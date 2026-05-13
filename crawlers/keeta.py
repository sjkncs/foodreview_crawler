"""
KeeTa 商户后台评论爬虫
目标：https://merchant.mykeeta.com/m/web/app/shop#/evaluate

登录流程：
  1. 首次运行 → 自动打开浏览器 → 用户手动登录
  2. 登录后自动保存 cookies 到 data/keeta_cookies.json
  3. 后续运行直接注入已保存 cookies，无需重复登录

采集字段（与全表头对齐）：
  店铺名称 | 平台 | 用户名 | 评分 | 评论内容 | 翻译内容
  发布日期 | 采集时间 | 图片URLs | 商家回复 | 子评分 | 页面URL

筛选支持：
  - 全量 / 最近N天 / 按评分（1-5星）
  - 默认按"最新"排序

DOM 结构（来自页面分析）：
  评论卡片：article / div[class*="evaluate"] / div[class*="review"]
  策略：API 拦截（XHR /evaluate） → DOM 解析 → OCR 降级
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, Optional

from core.models import OcrStrategy, Platform, Review, ReviewType
from .base import BaseCrawler

logger = logging.getLogger(__name__)

# ── 常量 ─────────────────────────────────────────────────────────
EVALUATE_URL  = "https://merchant.mykeeta.com/m/web/app/shop#/evaluate"
BASE_URL      = "https://merchant.mykeeta.com"
COOKIES_FILE  = Path(__file__).parent.parent / "data" / "keeta_cookies.json"
LOGIN_TIMEOUT = 120_000   # 2 分钟手动登录超时

# API 路径关键词（拦截 XHR 评论接口）
_API_PATTERNS = ("evaluate", "review", "comment", "rating", "feedback")


class KeetaCrawler(BaseCrawler):
    """
    KeeTa 商户后台评论爬虫。
    支持三级策略：API 拦截 → DOM 解析 → OCR 截图（qwen3-vl-plus）。
    """
    platform = Platform.KEETA

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        strategy: str = OcrStrategy.HYBRID.value,
        # 筛选参数
        days: Optional[int] = None,          # 最近 N 天，None 表示全量
        rating_filter: Optional[int] = None,  # 1-5 星筛选，None 表示全部
        shop_name: str = "KeeTa商户",
        shop_hint: Optional[str] = None,
    ):
        super().__init__(headless=headless, proxy=proxy, strategy=strategy)
        self.days = days
        self.rating_filter = rating_filter
        self._shop_name = shop_name
        self._shop_hint = shop_hint or ""

    def _get_shop_url(self, shop_id: str) -> str:
        return EVALUATE_URL

    # ══════════════════════════════════════════════════════════════
    # 登录管理
    # ══════════════════════════════════════════════════════════════

    async def _ensure_logged_in(self, page) -> bool:
        """
        确保已登录状态：
        1. 注入保存的 cookies → 检测是否仍有效
        2. 若无效 → 切换有头模式，等待用户手动登录 → 保存 cookies
        返回 True=登录成功，False=失败
        """
        # 尝试注入已有 cookies
        if COOKIES_FILE.exists():
            try:
                cookies = json.loads(COOKIES_FILE.read_text(encoding="utf-8"))
                await self._context.add_cookies(cookies)
                await page.goto(EVALUATE_URL, timeout=20000)
                await page.wait_for_timeout(3000)
                if await self._is_logged_in(page):
                    logger.info("[KeeTa] 使用已保存 Cookie 登录成功")
                    return True
                logger.warning("[KeeTa] 已保存 Cookie 已过期，需要重新登录")
            except Exception as exc:
                logger.warning("[KeeTa] 注入 Cookie 失败: %s", exc)

        # 需要手动登录：切换到有头模式
        logger.info("[KeeTa] 请在浏览器中手动登录，等待最多 2 分钟...")
        if self.headless:
            # 强制重启一个有头浏览器页面
            await self._close_browser()
            self.headless = False
            await self._start_browser()
            page = await self._context.new_page()

        await page.goto(BASE_URL, timeout=20000)
        await page.wait_for_timeout(2000)

        # 等待用户手动登录（检测到评论页面加载为止）
        try:
            await page.wait_for_function(
                "() => window.location.href.includes('/evaluate') || "
                "document.querySelector('[class*=\"evaluate\"], [class*=\"review\"]')",
                timeout=LOGIN_TIMEOUT,
            )
        except Exception:
            # 也接受手动导航到评论页
            if not await self._is_logged_in(page):
                logger.error("[KeeTa] 登录超时或失败")
                return False

        # 保存 cookies
        await self._save_cookies()
        logger.info("[KeeTa] 登录成功，已保存 Cookie 到 %s", COOKIES_FILE)
        return True

    async def _is_logged_in(self, page) -> bool:
        """检测是否已在评论页且已登录（不是登录页/错误页）"""
        try:
            url = page.url
            if "login" in url or "signin" in url or "auth" in url:
                return False
            # 检测评论相关 DOM 元素存在
            evaluate_el = page.locator(
                '[class*="evaluate"], [class*="review"], [class*="rating"]'
            )
            count = await evaluate_el.count()
            return count > 0
        except Exception:
            return False

    async def _save_cookies(self) -> None:
        """将当前 context cookies 保存到文件"""
        COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        cookies = await self._context.cookies()
        COOKIES_FILE.write_text(
            json.dumps(cookies, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ══════════════════════════════════════════════════════════════
    # 主策略：API 拦截
    # ══════════════════════════════════════════════════════════════

    async def fetch_reviews(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        """API 拦截策略：拦截 KeeTa 后台 XHR 评论接口"""
        page = await self._context.new_page()
        api_queue: list[dict] = []

        async def on_response(resp):
            if (
                any(k in resp.url for k in _API_PATTERNS)
                and resp.status == 200
                and "merchant.mykeeta.com" in resp.url
            ):
                try:
                    body = await resp.json()
                    api_queue.append({"body": body, "url": resp.url})
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            # 登录检查
            if not await self._ensure_logged_in(page):
                raise RuntimeError("KeeTa 登录失败，请检查账号或 Cookie")

            # 导航到评论页
            await page.goto(EVALUATE_URL, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            await self._ensure_store_selected(page, shop_name)

            # 应用筛选器
            await self._apply_filters(page)

            for _ in range(max_pages):
                await page.wait_for_timeout(2500)

                while api_queue:
                    item = api_queue.pop(0)
                    batch = self._parse_api_response(
                        item["body"], shop_id, shop_name, review_type, item["url"]
                    )
                    if batch:
                        yield batch

                # 翻页（下一页按钮 或 滚动加载）
                has_more = await self._go_next_page(page)
                if not has_more:
                    break

            # 保存最新 cookies（续期）
            await self._save_cookies()

        finally:
            await page.close()

    # ══════════════════════════════════════════════════════════════
    # 备用策略：DOM 解析
    # ══════════════════════════════════════════════════════════════

    async def fetch_reviews_dom(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        """DOM 解析策略：直接从页面 HTML 提取评论"""
        page = await self._context.new_page()
        try:
            if not await self._ensure_logged_in(page):
                raise RuntimeError("KeeTa 登录失败")

            await page.goto(EVALUATE_URL, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            await self._ensure_store_selected(page, shop_name)
            await self._apply_filters(page)

            seen: set[str] = set()
            for _ in range(max_pages):
                await page.wait_for_timeout(2000)
                batch = await self._parse_dom(page, shop_id, shop_name, review_type, seen)
                if batch:
                    yield batch
                if not await self._go_next_page(page):
                    break

            await self._save_cookies()
        finally:
            await page.close()

    # ══════════════════════════════════════════════════════════════
    # 筛选器操作
    # ══════════════════════════════════════════════════════════════

    async def _apply_filters(self, page) -> None:
        """
        在 KeeTa 评论页应用筛选：
        1. 点击「筛选」按钮
        2. 按评分筛选（若设置了 rating_filter）
        3. 按最新排序
        """
        await page.wait_for_timeout(1500)

        # ── 1. 点击筛选/排序按钮 ──────────────────────────────────
        filter_selectors = [
            "text=筛选", "text=篩選", "text=Filter",
            "[class*='filter']", "[class*='sort']",
            "button:has-text('最新')", "button:has-text('排序')",
        ]
        for sel in filter_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    await page.wait_for_timeout(800)
                    break
            except Exception:
                pass

        # ── 2. 选择"最新"排序 ────────────────────────────────────
        sort_options = ["text=最新", "text=最新優先", "text=Newest", "text=最近"]
        for sel in sort_options:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500):
                    await el.click()
                    await page.wait_for_timeout(800)
                    logger.info("[KeeTa] 已选择最新排序")
                    break
            except Exception:
                pass

        # ── 3. 按评分筛选 ─────────────────────────────────────────
        if self.rating_filter and 1 <= self.rating_filter <= 5:
            star_text_map = {1: "1星", 2: "2星", 3: "3星", 4: "4星", 5: "5星"}
            star_text = star_text_map[self.rating_filter]
            for sel in [f"text={star_text}", f"[data-rating='{self.rating_filter}']"]:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=1500):
                        await el.click()
                        await page.wait_for_timeout(800)
                        logger.info("[KeeTa] 已筛选 %d 星评论", self.rating_filter)
                        break
                except Exception:
                    pass

        # ── 4. 确认/应用筛选 ─────────────────────────────────────
        for confirm_sel in ["text=確認", "text=确认", "text=Apply", "text=完成"]:
            try:
                el = page.locator(confirm_sel).first
                if await el.is_visible(timeout=1000):
                    await el.click()
                    await page.wait_for_timeout(1000)
                    break
            except Exception:
                pass

        await page.wait_for_load_state("networkidle", timeout=8000)

    async def _ensure_store_selected(self, page, shop_name: str) -> None:
        """
        尝试在多门店商户后台里切换到目标门店。
        这是 best-effort 行为：找不到则继续当前门店，避免阻塞。
        """
        candidates = [self._shop_hint, shop_name, self._shop_name]
        tokens: list[str] = []
        for candidate in candidates:
            candidate = (candidate or "").strip()
            if not candidate:
                continue
            tokens.append(candidate)
            tokens.extend(re.findall(r"[（(]([^）)]+)[）)]", candidate))
        seen: set[str] = set()
        normalized_tokens = []
        for token in tokens:
            token = token.strip()
            if len(token) < 2 or token in seen:
                continue
            seen.add(token)
            normalized_tokens.append(token)
        if not normalized_tokens:
            return

        dropdown_selectors = [
            "[class*='shop']",
            "[class*='store']",
            "[class*='merchant']",
            "[class*='select']",
        ]
        for token in normalized_tokens:
            try:
                if await page.locator(f"text={token}").count() > 1:
                    return
            except Exception:
                pass

            for selector in dropdown_selectors:
                try:
                    trigger = page.locator(selector).filter(has_text=re.compile(r"门店|店铺|商户|shop|store", re.I)).first
                    if await trigger.is_visible(timeout=800):
                        await trigger.click()
                        await page.wait_for_timeout(500)
                        option = page.locator(f"text={token}").first
                        if await option.is_visible(timeout=1000):
                            await option.click()
                            await page.wait_for_timeout(1200)
                            logger.info("[KeeTa] 已尝试切换门店: %s", token)
                            return
                except Exception:
                    pass

    # ══════════════════════════════════════════════════════════════
    # DOM 解析
    # ══════════════════════════════════════════════════════════════

    async def _parse_dom(
        self,
        page,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        seen: set[str],
    ) -> list[Review]:
        """从 KeeTa 评论页 DOM 提取评论"""
        reviews: list[Review] = []

        # 评论卡片选择器（根据页面截图分析）
        card_selectors = [
            "article[class*='evaluate']",
            "article[class*='review']",
            "div[class*='evaluate-item']",
            "div[class*='review-item']",
            "li[class*='evaluate']",
            # 通用后备
            "article",
        ]

        items_loc = None
        for sel in card_selectors:
            loc = page.locator(sel)
            cnt = await loc.count()
            if cnt > 0:
                items_loc = loc
                logger.debug("[KeeTa DOM] 使用选择器 %s，找到 %d 条", sel, cnt)
                break

        if not items_loc:
            logger.warning("[KeeTa DOM] 未找到评论卡片，尝试 OCR 降级")
            return reviews

        count = await items_loc.count()
        for i in range(count):
            item = items_loc.nth(i)

            # ── 唯一标识（用于去重）──────────────────────────────
            uid = await item.get_attribute("data-id") or f"keeta_{i}"
            if uid in seen:
                continue
            seen.add(uid)

            # ── 评论内容 ─────────────────────────────────────────
            content = ""
            for sel in [
                "[class*='review-content']", "[class*='comment-text']",
                "[class*='body']", "p", "span[class*='content']",
            ]:
                try:
                    el = item.locator(sel).first
                    if await el.is_visible(timeout=1000):
                        content = (await el.inner_text()).strip()
                        if len(content) > 3:
                            break
                except Exception:
                    pass

            if not content:
                continue

            # ── 用户名 ───────────────────────────────────────────
            reviewer = await self._extract_text(item, [
                "[class*='username']", "[class*='nickname']",
                "[class*='user-name']", "[class*='author']",
            ]) or "匿名用户"

            # ── 评分 ─────────────────────────────────────────────
            rating = await self._extract_rating(item)

            # ── 发布时间 ─────────────────────────────────────────
            date_str = await self._extract_text(item, [
                "[class*='date']", "[class*='time']", "[class*='created']",
                "time", "span[class*='ago']",
            ]) or ""
            published_at = self._parse_time(date_str)

            # ── 图片 URLs ────────────────────────────────────────
            img_urls: tuple[str, ...] = ()
            try:
                imgs = item.locator("img[src]:not([src*='avatar']):not([src*='icon'])")
                n = await imgs.count()
                raw = [await imgs.nth(j).get_attribute("src") or "" for j in range(n)]
                img_urls = tuple(u for u in raw if u and len(u) > 10)
            except Exception:
                pass

            # ── 商家回复 ─────────────────────────────────────────
            merchant_reply = await self._extract_text(item, [
                "[class*='merchant-reply']", "[class*='owner-reply']",
                "[class*='reply-content']", "[class*='response']",
            ])

            # ── 子评分（口味/配送/包装等）────────────────────────
            child_rating = await self._extract_sub_ratings(item)

            reviews.append(self._make_review(
                platform=self.platform,
                shop_id=shop_id,
                shop_name=shop_name,
                reviewer_name=reviewer,
                content=content,
                rating=rating,
                published_at=published_at,
                image_urls=img_urls,
                merchant_reply=merchant_reply,
                child_rating=child_rating,
                review_type=review_type,
                page_url=page.url,
                ocr_strategy=OcrStrategy.DOM_PARSE.value,
            ))

        return reviews

    # ══════════════════════════════════════════════════════════════
    # API 响应解析
    # ══════════════════════════════════════════════════════════════

    def _parse_api_response(
        self,
        data: dict,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        api_url: str,
    ) -> list[Review]:
        """解析 KeeTa 后台 XHR 评论接口响应"""
        reviews: list[Review] = []
        try:
            # 尝试多种常见响应格式
            items = (
                data.get("data", {}).get("list", [])
                or data.get("data", {}).get("items", [])
                or data.get("data", {}).get("reviews", [])
                or data.get("list", [])
                or data.get("items", [])
                or data.get("reviews", [])
                or (data.get("data", []) if isinstance(data.get("data"), list) else [])
            )

            if not items:
                logger.debug("[KeeTa API] 响应中未找到评论列表，raw keys: %s", list(data.keys()))
                return reviews

            for item in items:
                content = (
                    item.get("content") or item.get("comment")
                    or item.get("review") or item.get("text") or ""
                ).strip()
                if not content:
                    continue

                # 评分
                raw_rating = item.get("rating") or item.get("star") or item.get("score") or 5
                try:
                    rating = float(raw_rating)
                    if rating > 5:
                        rating = rating / 10 if rating > 10 else rating / 2
                    rating = max(1.0, min(5.0, rating))
                except (ValueError, TypeError):
                    rating = 5.0

                # 时间
                published_at = self._parse_time(
                    str(item.get("createdAt") or item.get("created_at")
                        or item.get("createTime") or item.get("time") or "")
                )

                # 图片
                pics = item.get("images") or item.get("pics") or item.get("photos") or []
                img_urls = tuple(
                    (p.get("url") or p.get("src") or str(p)) if isinstance(p, dict) else str(p)
                    for p in pics if p
                )

                # 商家回复
                reply_raw = item.get("reply") or item.get("merchantReply") or item.get("merchant_reply") or {}
                if isinstance(reply_raw, dict):
                    merchant_reply = reply_raw.get("content") or reply_raw.get("text")
                elif isinstance(reply_raw, str):
                    merchant_reply = reply_raw or None
                else:
                    merchant_reply = None

                # 子评分
                sub = {}
                for k in ["foodScore", "food_score", "deliveryScore", "delivery_score",
                          "packScore", "pack_score", "serviceScore"]:
                    if item.get(k) is not None:
                        label = {"foodScore": "口味", "food_score": "口味",
                                 "deliveryScore": "配送", "delivery_score": "配送",
                                 "packScore": "包装", "pack_score": "包装",
                                 "serviceScore": "服务"}.get(k, k)
                        sub[label] = item[k]
                child_rating = json.dumps(sub, ensure_ascii=False) if sub else None

                # 用户名（可能有隐私脱敏）
                user_info = item.get("user") or item.get("reviewer") or {}
                if isinstance(user_info, dict):
                    reviewer = user_info.get("name") or user_info.get("nickname") or "匿名用户"
                else:
                    reviewer = str(user_info) if user_info else "匿名用户"

                reviews.append(self._make_review(
                    platform=self.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name=reviewer,
                    content=content,
                    rating=rating,
                    published_at=published_at,
                    image_urls=img_urls,
                    merchant_reply=merchant_reply,
                    child_rating=child_rating,
                    review_type=review_type,
                    page_url=api_url,
                    raw_data=json.dumps(item, ensure_ascii=False),
                    ocr_strategy=OcrStrategy.API_INTERCEPT.value,
                ))

            logger.info("[KeeTa API] 解析到 %d 条评论", len(reviews))
        except Exception as exc:
            logger.warning("[KeeTa API] 解析失败: %s", exc)
        return reviews

    # ══════════════════════════════════════════════════════════════
    # 翻页
    # ══════════════════════════════════════════════════════════════

    async def _go_next_page(self, page) -> bool:
        """点击下一页 或 滚动加载更多"""
        # 优先点击"下一页"按钮
        next_selectors = [
            "text=下一页", "text=下一頁", "text=Next",
            "[class*='next']:not([disabled])",
            "button[class*='next']:not([disabled])",
            "[aria-label='下一页']",
        ]
        for sel in next_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500) and await el.is_enabled():
                    await el.click()
                    await page.wait_for_timeout(2000)
                    return True
            except Exception:
                pass

        # 降级：滚动加载
        return await self._scroll_load_more(page)

    # ══════════════════════════════════════════════════════════════
    # DOM 辅助方法
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    async def _extract_text(item, selectors: list[str]) -> Optional[str]:
        """从多个选择器中尝试提取文字"""
        for sel in selectors:
            try:
                el = item.locator(sel).first
                if await el.is_visible(timeout=800):
                    text = (await el.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                pass
        return None

    @staticmethod
    async def _extract_rating(item) -> float:
        """从多种方式提取评分"""
        # 1. data-rating 属性
        try:
            val = await item.get_attribute("data-rating")
            if val:
                return max(1.0, min(5.0, float(val)))
        except Exception:
            pass
        # 2. aria-label 包含星级
        try:
            label = await item.locator("[aria-label*='星']").first.get_attribute("aria-label") or ""
            m = re.search(r"(\d+(?:\.\d+)?)", label)
            if m:
                return max(1.0, min(5.0, float(m.group(1))))
        except Exception:
            pass
        # 3. 数星星图标（filled star count）
        try:
            filled = item.locator("[class*='star-filled'], [class*='star_filled'], svg.star-on")
            n = await filled.count()
            if n > 0:
                return max(1.0, min(5.0, float(n)))
        except Exception:
            pass
        return 5.0   # 默认满分

    @staticmethod
    async def _extract_sub_ratings(item) -> Optional[str]:
        """提取子评分（口味/配送/包装等）"""
        try:
            sub: dict[str, float] = {}
            labels = ["口味", "配送", "包裝", "包装", "服務", "服务", "衛生", "卫生"]
            for label in labels:
                try:
                    el = item.locator(f"text={label}").first
                    if await el.count() > 0:
                        # 找到标签后，读取同级/父级的评分数值
                        parent = el.locator("xpath=..")
                        score_el = parent.locator("[class*='score'], [class*='star'], span").last
                        score_text = (await score_el.inner_text()).strip()
                        m = re.search(r"(\d+(?:\.\d+)?)", score_text)
                        if m:
                            sub[label] = float(m.group(1))
                except Exception:
                    pass
            return json.dumps(sub, ensure_ascii=False) if sub else None
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════
    # 时间解析
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _parse_time(s: str) -> Optional[datetime]:
        if not s:
            return None
        # 时间戳（毫秒）
        if s.isdigit() and len(s) >= 10:
            try:
                ts = int(s) / 1000 if len(s) > 10 else int(s)
                return datetime.fromtimestamp(ts)
            except Exception:
                pass
        # 标准格式
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
                    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
            try:
                return datetime.strptime(s[:len(fmt)], fmt)
            except ValueError:
                pass
        # 相对时间（复用 Google Maps 的解析）
        now = datetime.now()
        patterns = [
            (r"(\d+)\s*分鐘前", "minutes"), (r"(\d+)\s*分钟前", "minutes"),
            (r"(\d+)\s*小時前", "hours"),   (r"(\d+)\s*小时前", "hours"),
            (r"(\d+)\s*天前",   "days"),
            (r"(\d+)\s*週前",   "weeks"),   (r"(\d+)\s*周前", "weeks"),
            (r"(\d+)\s*個月前", "months"),  (r"(\d+)\s*个月前", "months"),
            (r"(\d+)\s*年前",   "years"),
        ]
        for pattern, unit in patterns:
            m = re.search(pattern, s)
            if m:
                n = int(m.group(1))
                delta_map = {
                    "minutes": timedelta(minutes=n),
                    "hours":   timedelta(hours=n),
                    "days":    timedelta(days=n),
                    "weeks":   timedelta(weeks=n),
                    "months":  timedelta(days=n * 30),
                    "years":   timedelta(days=n * 365),
                }
                return now - delta_map[unit]
        return None
