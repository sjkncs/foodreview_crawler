"""
爬虫基类 v3 - 支持多策略自动切换
策略优先级：API拦截 → DOM解析 → OCR截图（qwen3-vl-plus 两步法）

OCR 两步法：
  Step 1 - 区域定位：全页截图 → qwen3-vl-plus 识别评论区 bbox + 关键元素坐标
  Step 2 - 精细识别：裁剪评论区 → 逐条结构化提取（用户名/评分/内容/图片URL/商家回复/子评分/时间）
"""
from __future__ import annotations
import asyncio
import base64
import io
import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncGenerator, Optional

from core.models import OcrStrategy, Platform, Review, ReviewType

logger = logging.getLogger(__name__)

# ── 评论区定位关键词（跨平台通用）────────────────────────────────
_REVIEW_AREA_KEYWORDS = (
    "评论", "评价", "好评", "差评", "食评", "用户评价",
    "reviews", "ratings", "comments", "customer reviews",
    "レビュー", "口コミ", "리뷰",  # 日韩
)


class BaseCrawler(ABC):
    """
    爬虫基类：支持三种策略自动切换
    - api_intercept:  拦截 XHR/Fetch 网络请求（最快）
    - dom_parse:      Playwright CSS/XPath 解析 DOM（稳定）
    - ocr_screenshot: qwen3-vl-plus 两步 OCR（反爬最强，跨平台通用）
    - hybrid:         自动按优先级降级
    """

    platform: Platform  # 子类必须声明

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        strategy: str = OcrStrategy.HYBRID.value,
    ):
        self.headless = headless
        self.proxy = proxy
        self.strategy = strategy
        self._browser = None
        self._context = None

    # ── 公共爬取入口 ───────────────────────────────────────────────
    async def crawl(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int = 10,
        review_type: ReviewType = ReviewType.REVIEW,
        progress_callback=None,
    ) -> list[Review]:
        """
        爬取入口：自动选择策略，hybrid 模式失败时逐级降级。
        progress_callback(fetched: int, total: int)
        """
        results: list[Review] = []
        primary = self._resolve_strategy()
        logger.info("[%s] 主策略: %s", self.platform.value, primary)

        try:
            await self._start_browser()
            async for batch in self._dispatch_strategy(
                primary, shop_id, shop_name, max_pages, review_type
            ):
                results.extend(batch)
                if progress_callback:
                    progress_callback(len(results), -1)
                await asyncio.sleep(self._random_delay())

        except Exception as exc:
            logger.error("[%s] 策略 %s 失败: %s", self.platform.value, primary, exc)
            # 非 hybrid 模式：直接抛出，不降级
            if self.strategy != OcrStrategy.HYBRID.value:
                raise
            # hybrid 降级链：api_intercept → dom_parse → ocr_screenshot
            fallback = self._next_fallback(primary)
            fallback_succeeded = False
            while fallback:
                logger.warning("[%s] 降级到: %s", self.platform.value, fallback)
                try:
                    async for batch in self._dispatch_strategy(
                        fallback, shop_id, shop_name, max_pages, review_type
                    ):
                        results.extend(batch)
                        if progress_callback:
                            progress_callback(len(results), -1)
                    fallback_succeeded = True
                    break  # 降级成功，退出
                except Exception as fb_exc:
                    logger.warning("[%s] 降级 %s 也失败: %s", self.platform.value, fallback, fb_exc)
                    fallback = self._next_fallback(fallback)
            if not fallback_succeeded and not results:
                raise exc  # 所有策略均失败，重新抛出原始异常

        finally:
            await self._close_browser()

        return results

    def _resolve_strategy(self) -> str:
        """hybrid 默认先走 api_intercept"""
        return (
            OcrStrategy.API_INTERCEPT.value
            if self.strategy == OcrStrategy.HYBRID.value
            else self.strategy
        )

    @staticmethod
    def _next_fallback(current: str) -> Optional[str]:
        """返回降级链中下一个策略"""
        chain = [
            OcrStrategy.API_INTERCEPT.value,
            OcrStrategy.DOM_PARSE.value,
            OcrStrategy.OCR_SCREENSHOT.value,
        ]
        try:
            idx = chain.index(current)
            return chain[idx + 1] if idx + 1 < len(chain) else None
        except ValueError:
            return None

    async def _dispatch_strategy(
        self,
        strategy: str,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        if strategy == OcrStrategy.API_INTERCEPT.value:
            async for batch in self.fetch_reviews(shop_id, shop_name, max_pages, review_type):
                yield batch
        elif strategy == OcrStrategy.DOM_PARSE.value:
            async for batch in self.fetch_reviews_dom(shop_id, shop_name, max_pages, review_type):
                yield batch
        elif strategy == OcrStrategy.OCR_SCREENSHOT.value:
            async for batch in self.fetch_reviews_ocr(shop_id, shop_name, max_pages, review_type):
                yield batch
        else:
            async for batch in self.fetch_reviews(shop_id, shop_name, max_pages, review_type):
                yield batch

    # ── 子类实现的策略方法 ─────────────────────────────────────────
    @abstractmethod
    async def fetch_reviews(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        """API 拦截策略（主策略，子类必须实现）"""
        ...

    async def fetch_reviews_dom(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        """DOM 解析策略（默认降级到 API 拦截，子类可覆盖）"""
        async for batch in self.fetch_reviews(shop_id, shop_name, max_pages, review_type):
            yield batch

    # ══════════════════════════════════════════════════════════════
    # OCR 两步策略（qwen3-vl-plus 驱动，跨平台通用）
    # ══════════════════════════════════════════════════════════════

    async def fetch_reviews_ocr(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        """
        OCR 截图策略通用入口（两步法）：
          Step 1: 全页截图 → VLM 定位评论区 & 导航到评论 Tab
          Step 2: 逐屏滚动截图 → VLM 逐条结构化识别所有字段
        """
        page = await self._context.new_page()
        try:
            url = self._get_shop_url(shop_id)
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Step 1：定位评论区，自动点击对应 Tab
            await self._ocr_navigate_to_reviews(page)

            seen_contents: set[str] = set()

            for _ in range(max_pages):
                # Step 2：截图并结构化识别
                screenshot = await page.screenshot(full_page=False, type="png")
                reviews = await self._ocr_extract_reviews(
                    screenshot, page.url, shop_id, shop_name, review_type
                )

                # 去重
                new_reviews = [
                    r for r in reviews
                    if r.content not in seen_contents and r.content.strip()
                ]
                for r in new_reviews:
                    seen_contents.add(r.content)

                if new_reviews:
                    yield new_reviews

                # 滚动加载更多
                if not await self._scroll_load_more(page):
                    break
                await page.wait_for_timeout(1500)

        finally:
            await page.close()

    async def _ocr_navigate_to_reviews(self, page) -> None:
        """
        Step 1 - 定位评论区：
        全页截图 → qwen3-vl-plus 识别页面结构 →
        找到含「评论/评价/食评」字样的 Tab/标签 → 点击
        """
        try:
            screenshot = await page.screenshot(full_page=False, type="png")
            b64 = base64.standard_b64encode(screenshot).decode()

            keywords_str = "、".join(_REVIEW_AREA_KEYWORDS[:8])
            prompt = f"""这是一个外卖/餐饮点评网站的截图。
请找到页面中包含「{keywords_str}」相关字样的标签页(Tab)或按钮。

返回 JSON 格式：
{{
  "found": true,
  "tab_text": "标签文字",
  "click_selector": "CSS选择器或描述",
  "review_area_visible": true
}}

如果评论内容已经直接可见（无需点击Tab），则 found=false, review_area_visible=true。
只返回 JSON，不要其他内容。"""

            from processors.ai_client import vision_chat
            raw = await vision_chat(b64, prompt, max_tokens=300)
            m = re.search(r'\{[^{}]+\}', raw, re.DOTALL)
            if not m:
                return

            data = json.loads(m.group())
            if data.get("found") and data.get("tab_text"):
                tab_text = data["tab_text"]
                logger.info("[OCR] 发现评论Tab: %s，尝试点击", tab_text)
                # 尝试用文字定位点击
                try:
                    el = page.locator(f"text={tab_text}").first
                    if await el.is_visible(timeout=3000):
                        await el.click()
                        await page.wait_for_timeout(2000)
                        logger.info("[OCR] 已点击评论Tab: %s", tab_text)
                        return
                except Exception:
                    pass
                # 降级：用 CSS selector
                css = data.get("click_selector", "")
                if css:
                    try:
                        await page.click(css, timeout=3000)
                        await page.wait_for_timeout(2000)
                    except Exception:
                        pass

        except Exception as exc:
            logger.warning("[OCR] 评论区定位失败，直接识别当前页面: %s", exc)

    async def _ocr_extract_reviews(
        self,
        screenshot: bytes,
        page_url: str,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
    ) -> list[Review]:
        """
        Step 2 - 结构化识别：
        截图 → qwen3-vl-plus 识别所有评论条目，提取完整字段：
          用户名、评分、评论内容、图片URL、商家回复、子评分、发布日期
        然后将结果映射到 Review 对象
        """
        b64 = base64.standard_b64encode(screenshot).decode()

        prompt = """这是一个外卖/餐饮点评页面的截图，请识别其中所有可见的用户评论条目。

对每条评论，提取以下字段（没有则填 null）：
- reviewer: 用户名/昵称
- rating: 评分（数字，1-5，如只有星星图标请数星星数量）
- content: 评论正文完整内容
- image_urls: 评论中附带的图片URL列表（如可见）
- merchant_reply: 商家回复内容
- child_rating: 子评分对象，如 {"口味": 5, "配送": 4, "包装": 5}
- published_at: 发布日期（原始文字，如"3天前"、"2024-01-15"）

以 JSON 数组返回，格式如下（严格JSON，不要注释）：
[
  {
    "reviewer": "用户名",
    "rating": 5,
    "content": "评论内容",
    "image_urls": ["url1", "url2"],
    "merchant_reply": "商家回复或null",
    "child_rating": {"口味": 5},
    "published_at": "3天前"
  }
]

注意：
1. 只识别评论内容区域，忽略导航栏、广告等
2. image_urls 只填写能从截图中看到的真实URL，看不到则填 []
3. 如页面无评论内容可见，返回 []"""

        try:
            from processors.ai_client import vision_chat
            raw = await vision_chat(b64, prompt, max_tokens=4096)
            # 提取 JSON 数组
            m = re.search(r'\[[\s\S]*\]', raw)
            if not m:
                logger.warning("[OCR] qwen3-vl-plus 未返回有效JSON数组: %s", raw[:200])
                return []
            items = json.loads(m.group())
        except Exception as exc:
            logger.warning("[OCR] VLM 识别失败: %s", exc)
            return await self._fallback_local_ocr(
                screenshot, page_url, shop_id, shop_name, review_type
            )

        reviews: list[Review] = []
        for item in items:
            content = (item.get("content") or "").strip()
            if not content:
                continue

            # 图片 URL 列表
            img_raw = item.get("image_urls") or []
            img_urls = tuple(str(u) for u in img_raw if u)

            # 子评分 JSON 序列化
            child = item.get("child_rating")
            child_rating = json.dumps(child, ensure_ascii=False) if child else None

            # 商家回复
            merchant_reply = item.get("merchant_reply") or None
            if merchant_reply == "null":
                merchant_reply = None

            # 评分
            try:
                rating = float(item.get("rating") or 5)
            except (ValueError, TypeError):
                rating = 5.0

            reviews.append(self._make_review(
                platform=self.platform,
                shop_id=shop_id,
                shop_name=shop_name,
                reviewer_name=item.get("reviewer") or "匿名用户",
                content=content,
                rating=rating,
                published_at=None,           # 原始文字在 raw_data 里
                image_urls=img_urls,
                merchant_reply=merchant_reply,
                child_rating=child_rating,
                review_type=review_type,
                page_url=page_url,
                raw_data=json.dumps(item, ensure_ascii=False),
                ocr_strategy=OcrStrategy.OCR_SCREENSHOT.value,
            ))

        logger.info("[OCR] qwen3-vl-plus 识别到 %d 条评论", len(reviews))
        return reviews

    async def _fallback_local_ocr(
        self,
        screenshot: bytes,
        page_url: str,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
    ) -> list[Review]:
        """本地 OCR 降级（PaddleOCR → Tesseract）"""
        texts = await self._local_ocr(screenshot)
        reviews: list[Review] = []
        for text in texts:
            text = text.strip()
            if len(text) > 8:
                reviews.append(self._make_review(
                    platform=self.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name="本地OCR",
                    content=text,
                    rating=0.0,
                    published_at=None,
                    review_type=review_type,
                    page_url=page_url,
                    ocr_strategy="local_ocr",
                ))
        return reviews

    async def _local_ocr(self, screenshot: bytes) -> list[str]:
        """本地 OCR 降级：PaddleOCR → Tesseract"""
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            import cv2
            ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            nparr = np.frombuffer(screenshot, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            result = ocr.ocr(img, cls=True)
            return [word_info[1][0] for line in result if line for word_info in line]
        except ImportError:
            pass
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(screenshot))
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            return [l.strip() for l in text.splitlines() if l.strip()]
        except ImportError:
            logger.warning("未安装 PaddleOCR 或 pytesseract，本地OCR不可用")
            return []

    # ── 浏览器管理 ────────────────────────────────────────────────
    async def _start_browser(self) -> None:
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        launch_opts: dict = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--lang=zh-CN",
            ],
        }
        if self.proxy:
            launch_opts["proxy"] = {"server": self.proxy}
        self._browser = await self._pw.chromium.launch(**launch_opts)
        self._context = await self._browser.new_context(
            user_agent=self._random_ua(),
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            accept_downloads=True,
        )
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN','zh','en'] });
        """)

    async def _close_browser(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, "_pw"):
            await self._pw.stop()

    # ── 工具方法 ──────────────────────────────────────────────────
    @staticmethod
    def _make_review(
        platform: Platform,
        shop_id: str,
        shop_name: str,
        reviewer_name: str,
        content: str,
        rating: float,
        published_at: Optional[datetime],
        review_type: ReviewType = ReviewType.REVIEW,
        image_urls: tuple[str, ...] = (),
        merchant_reply: Optional[str] = None,
        child_rating: Optional[str] = None,
        page_url: Optional[str] = None,
        raw_data: Optional[str] = None,
        ocr_strategy: Optional[str] = None,
    ) -> Review:
        return Review(
            id=None,
            platform=platform,
            shop_name=shop_name,
            shop_id=shop_id,
            reviewer_name=reviewer_name,
            content=content,
            rating=rating,
            published_at=published_at,
            crawled_at=datetime.now(),
            image_urls=image_urls,
            merchant_reply=merchant_reply,
            child_rating=child_rating,
            page_url=page_url,
            review_type=review_type,
            raw_data=raw_data,
            ocr_strategy=ocr_strategy,
        )

    def _get_shop_url(self, shop_id: str) -> str:
        """子类覆盖返回商家页 URL"""
        return shop_id if shop_id.startswith("http") else f"https://example.com/{shop_id}"

    @staticmethod
    async def _scroll_load_more(page) -> bool:
        try:
            prev_h = await page.evaluate("document.body.scrollHeight")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            new_h = await page.evaluate("document.body.scrollHeight")
            return new_h > prev_h
        except Exception:
            return False

    @staticmethod
    def _random_delay() -> float:
        import random
        return random.uniform(1.5, 3.5)

    @staticmethod
    def _random_ua() -> str:
        import random
        return random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ])
