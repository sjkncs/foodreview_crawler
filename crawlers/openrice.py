"""
OpenRice 爬虫 v1
目标：https://www.openrice.com/zh/hongkong/restaurants?chainId=10006678

DOM 结构（来自页面截图分析）：
  搜索结果卡片：div[class*="poi-info"] / div[class*="restaurant-cell"]
  店铺名称：    div[class*="poi-name"] / h2[class*="name"]
  食评Tab：     a/button:has-text("食評")
  评论列表：    div.poi-detail-review-list / div.poi-review-list-desktop
  评论卡片：    article.review-post-desktop.poi-detail-review
  评论正文：    div.review-post-body > div.review-post-extract
  展开更多：    span.more:has-text("查看更多")
  图片附件：    div.review-extract-attachments a.ratio-box.attachment-item
  用户名：      div.review-post-header [class*="nickname"] / [class*="username"]
  发布时间：    div.review-post-header [class*="date"] / span[class*="time"]
  浏览量：      [class*="view"] / [class*="browse"]
  点赞量：      div.review-like-btn / [class*="like"]
  子评分：      div[class*="score"] (味道/環境/服務/衛生/抵食)
"""
from __future__ import annotations
import json
import logging
import re
from datetime import datetime
from typing import AsyncGenerator, Optional

from core.models import OcrStrategy, Platform, Review, ReviewType
from .base import BaseCrawler

logger = logging.getLogger(__name__)

CHAIN_URL = "https://www.openrice.com/zh/hongkong/restaurants?chainId=10006678&tabIndex=0"
BASE_URL   = "https://www.openrice.com"


class OpenRiceCrawler(BaseCrawler):
    """
    OpenRice 开饭喇爬虫
    流程：
      1. 打开品牌页，获取所有喜茶店铺列表
      2. 按店铺名称匹配（来自 Excel）
      3. 进入店铺页 → 点击「食評」Tab
      4. 筛选「最新」排序
      5. 逐条展开「查看更多」→ 提取完整评论
    """
    platform = Platform.OPENRICE

    def _get_shop_url(self, shop_id: str) -> str:
        if shop_id.startswith("http"):
            return shop_id
        return f"{BASE_URL}/zh/hongkong/r-{shop_id}"

    # ══════════════════════════════════════════════════════════════
    # 主策略：DOM 解析（OpenRice 无稳定 JSON API）
    # ══════════════════════════════════════════════════════════════

    async def fetch_reviews(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        """
        shop_id: OpenRice 店铺 URL 或 ID（如 heytea-city-walk-r738767）
        shop_name: 用于标记数据
        """
        page = await self._context.new_page()
        try:
            url = self._get_shop_url(shop_id)
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # 点击「食評」Tab
            await self._click_review_tab(page)

            # 筛选最新
            await self._filter_newest(page)

            seen: set[str] = set()
            for page_num in range(max_pages):
                await page.wait_for_timeout(2000)

                # 展开所有「查看更多」
                await self._expand_all_reviews(page)

                batch = await self._parse_reviews(page, shop_id, shop_name, review_type, seen)
                if batch:
                    yield batch

                # 翻页
                if not await self._next_page(page):
                    break

        finally:
            await page.close()

    # ══════════════════════════════════════════════════════════════
    # 品牌页：获取所有店铺列表
    # ══════════════════════════════════════════════════════════════

    async def get_all_shops(self) -> list[dict]:
        """
        打开品牌页，返回所有喜茶店铺列表：
        [{"name": "喜茶 (荃新天地)", "url": "https://...", "shop_id": "r738767"}]
        """
        await self._start_browser()
        page = await self._context.new_page()
        shops = []
        try:
            await page.goto(CHAIN_URL, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(2000)

            # 滚动加载所有店铺
            for _ in range(10):
                await self._scroll_load_more(page)
                await page.wait_for_timeout(1000)

            shops = await self._parse_shop_list(page)
            logger.info("[OpenRice] 品牌页共找到 %d 家店铺", len(shops))
        finally:
            await page.close()
            await self._close_browser()
        return shops

    async def _parse_shop_list(self, page) -> list[dict]:
        """解析品牌页店铺列表"""
        shops = []
        # 店铺卡片选择器（根据页面结构）
        card_selectors = [
            "[class*='restaurant-cell']",
            "[class*='poi-info']",
            "[class*='search-result'] li",
            "li[class*='restaurant']",
        ]
        items_loc = None
        for sel in card_selectors:
            loc = page.locator(sel)
            if await loc.count() > 0:
                items_loc = loc
                break

        if not items_loc:
            logger.warning("[OpenRice] 未找到店铺列表，尝试 VLM")
            return await self._vlm_parse_shop_list(page)

        count = await items_loc.count()
        for i in range(count):
            item = items_loc.nth(i)
            try:
                # 店铺名
                name = ""
                for sel in ["[class*='poi-name']", "h2", "h3", "[class*='name']"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            name = (await el.inner_text()).strip()
                            if name:
                                break
                    except Exception:
                        pass

                # 店铺链接
                href = ""
                try:
                    link = item.locator("a[href*='/r-'], a[href*='/restaurant']").first
                    href = await link.get_attribute("href") or ""
                    if href and not href.startswith("http"):
                        href = BASE_URL + href
                except Exception:
                    pass

                # 提取 shop_id（URL 中的 r-xxxxx 部分）
                shop_id = ""
                m = re.search(r'/r-([^/?#]+)', href)
                if m:
                    shop_id = m.group(1)

                if name and href:
                    shops.append({
                        "name":    name,
                        "url":     href,
                        "shop_id": shop_id,
                    })
            except Exception as exc:
                logger.debug("[OpenRice] 解析店铺卡片失败: %s", exc)

        return shops

    async def _vlm_parse_shop_list(self, page) -> list[dict]:
        """VLM 截图识别店铺列表（降级）"""
        try:
            import base64
            from processors.ai_client import vision_chat
            screenshot = await page.screenshot(type="png")
            b64 = base64.standard_b64encode(screenshot).decode()
            prompt = """这是 OpenRice 喜茶品牌页截图，请识别所有店铺名称和对应链接。
返回 JSON 数组：[{"name": "店铺名", "url": "链接或空"}]
只返回 JSON，不要其他内容。"""
            raw = await vision_chat(b64, prompt, max_tokens=1000)
            m = re.search(r'\[[\s\S]*\]', raw)
            if m:
                return json.loads(m.group())
        except Exception as e:
            logger.warning("[OpenRice] VLM 解析店铺列表失败: %s", e)
        return []

    # ══════════════════════════════════════════════════════════════
    # 评论页操作
    # ══════════════════════════════════════════════════════════════

    async def _click_review_tab(self, page) -> None:
        """点击「食評」Tab"""
        tab_kws = ["食評", "食评", "Reviews", "評論"]
        for kw in tab_kws:
            try:
                # 匹配含数字的 Tab，如「食評 (97)」
                el = page.locator(f"a:has-text('{kw}'), button:has-text('{kw}')").first
                if await el.is_visible(timeout=3000):
                    await el.click()
                    await page.wait_for_timeout(2000)
                    logger.info("[OpenRice] 已点击食評Tab")
                    return
            except Exception:
                pass
        logger.warning("[OpenRice] 未找到食評Tab，继续当前页面")

    async def _filter_newest(self, page) -> None:
        """筛选最新评论"""
        # 点击筛选入口
        for kw in ["篩選食評", "筛选", "篩選", "Filter"]:
            try:
                el = page.locator(f"text={kw}").first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    await page.wait_for_timeout(800)
                    break
            except Exception:
                pass

        # 选最新
        for kw in ["最新", "最新優先", "Newest", "Most Recent"]:
            try:
                el = page.locator(f"text={kw}").first
                if await el.is_visible(timeout=1500):
                    await el.click()
                    await page.wait_for_timeout(1000)
                    logger.info("[OpenRice] 已选择最新排序")
                    return
            except Exception:
                pass

    async def _expand_all_reviews(self, page) -> None:
        """展开所有「查看更多」"""
        for _ in range(20):
            try:
                # OpenRice 的展开按钮：span.more 或 a:has-text("查看更多")
                more_btns = page.locator(
                    "span.more, a:has-text('查看更多'), span:has-text('查看更多'), "
                    "[class*='more']:has-text('查看'), a:has-text('...more')"
                )
                count = await more_btns.count()
                if count == 0:
                    break
                # 点击第一个可见的
                for i in range(count):
                    btn = more_btns.nth(i)
                    if await btn.is_visible(timeout=500):
                        await btn.click()
                        await page.wait_for_timeout(500)
                        break
                else:
                    break
            except Exception:
                break

    async def _next_page(self, page) -> bool:
        """翻到下一页"""
        next_selectors = [
            "a[class*='next']:not([class*='disabled'])",
            "button[class*='next']:not([disabled])",
            "a:has-text('下一頁')",
            "a:has-text('Next')",
            "[aria-label='下一頁']",
        ]
        for sel in next_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500) and await el.is_enabled():
                    await el.click()
                    await page.wait_for_timeout(2500)
                    return True
            except Exception:
                pass
        return False

    # ══════════════════════════════════════════════════════════════
    # 评论解析（核心）
    # ══════════════════════════════════════════════════════════════

    async def _parse_reviews(
        self,
        page,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        seen: set[str],
    ) -> list[Review]:
        reviews: list[Review] = []
        try:
            # 评论卡片：article.review-post-desktop.poi-detail-review
            items = page.locator(
                "article.review-post-desktop, "
                "article[class*='poi-detail-review'], "
                "article[class*='review-post']"
            )
            count = await items.count()
            logger.info("[OpenRice] 当前页找到 %d 条评论卡片", count)

            for i in range(count):
                item = items.nth(i)
                try:
                    review = await self._parse_single_review(
                        item, page, shop_id, shop_name, review_type, seen
                    )
                    if review:
                        reviews.append(review)
                except Exception as exc:
                    logger.debug("[OpenRice] 解析第%d条失败: %s", i, exc)

        except Exception as exc:
            logger.warning("[OpenRice] 评论列表解析失败: %s", exc)
        return reviews

    async def _parse_single_review(
        self,
        item,
        page,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        seen: set[str],
    ) -> Optional[Review]:
        """解析单条评论，提取所有字段"""

        # ── 去重 ID ──────────────────────────────────────────────
        uid = await item.get_attribute("data-review-id") or ""
        if not uid:
            # 用评论链接作为 ID
            try:
                link = item.locator("a[href*='/review']").first
                uid = await link.get_attribute("href") or ""
            except Exception:
                pass
        if uid and uid in seen:
            return None
        if uid:
            seen.add(uid)

        # ── 评论正文（section.review-post-main > div.review-post-body）──
        content = ""
        # 先尝试展开后的完整内容
        for sel in [
            "div.review-post-body",
            "div.review-post-extract",
            "[class*='review-body']",
            "[class*='review-content']",
        ]:
            try:
                el = item.locator(sel).first
                if await el.is_visible(timeout=1000):
                    raw = (await el.inner_text()).strip()
                    # 去掉「查看更多」文字
                    raw = re.sub(r'查看更多|\.\.\.more|See More', '', raw).strip()
                    if len(raw) > 3:
                        content = raw
                        break
            except Exception:
                pass

        if not content:
            return None

        # ── 用户名 ───────────────────────────────────────────────
        reviewer = ""
        for sel in [
            "[class*='nickname']", "[class*='username']",
            "[class*='user-name']", "[class*='author']",
            "div.review-post-header [class*='name']",
        ]:
            try:
                el = item.locator(sel).first
                if await el.is_visible(timeout=800):
                    reviewer = (await el.inner_text()).strip()
                    if reviewer:
                        break
            except Exception:
                pass

        # ── 发布时间 ─────────────────────────────────────────────
        date_str = ""
        for sel in [
            "[class*='date']", "[class*='time']",
            "span[class*='ago']", "time",
            "div.review-post-header span",
        ]:
            try:
                el = item.locator(sel).first
                if await el.is_visible(timeout=800):
                    t = (await el.inner_text()).strip()
                    # 过滤掉纯数字（浏览量）
                    if t and not t.isdigit() and len(t) > 3:
                        date_str = t
                        break
            except Exception:
                pass
        published_at = self._parse_openrice_time(date_str)

        # ── 浏览量 ───────────────────────────────────────────────
        view_count = ""
        for sel in ["[class*='view']", "[class*='browse']", "[class*='read']"]:
            try:
                el = item.locator(sel).first
                if await el.is_visible(timeout=800):
                    t = (await el.inner_text()).strip()
                    if t and re.search(r'\d', t):
                        view_count = t
                        break
            except Exception:
                pass

        # ── 点赞量 ───────────────────────────────────────────────
        like_count = ""
        for sel in [
            "div.review-like-btn", "[class*='like-btn']",
            "[class*='like-count']", "[class*='helpful']",
        ]:
            try:
                el = item.locator(sel).first
                if await el.is_visible(timeout=800):
                    t = (await el.inner_text()).strip()
                    if t:
                        like_count = t
                        break
            except Exception:
                pass

        # ── 图片 URLs（div.review-extract-attachments a.ratio-box）──
        img_urls: tuple[str, ...] = ()
        try:
            # 图片链接（指向评论详情页，包含图片）
            attachments = item.locator(
                "div.review-extract-attachments a.ratio-box, "
                "div[class*='attachment'] a, "
                "[class*='review-image'] img, "
                "[class*='photo'] img",
            )
            n = await attachments.count()
            imgs = []
            for j in range(n):
                att = attachments.nth(j)
                # 优先取 href（链接到图片详情）
                href = await att.get_attribute("href") or ""
                if href:
                    full = href if href.startswith("http") else BASE_URL + href
                    imgs.append(full)
                else:
                    # 取 img src
                    img_el = att.locator("img").first
                    src = await img_el.get_attribute("src") or ""
                    if src:
                        imgs.append(src)
            img_urls = tuple(imgs)
        except Exception:
            pass

        # ── 子评分（味道/環境/服務/衛生/抵食）────────────────────
        child_rating = None
        try:
            score_labels = ["味道", "環境", "服務", "衛生", "抵食"]
            sub: dict[str, str] = {}
            for label in score_labels:
                try:
                    label_el = item.locator(f"text={label}").first
                    if await label_el.count() > 0:
                        # 找同级的评分数字
                        parent = label_el.locator("xpath=..")
                        score_el = parent.locator("[class*='score'], span").last
                        score_text = (await score_el.inner_text()).strip()
                        if score_text and re.search(r'\d', score_text):
                            sub[label] = score_text
                except Exception:
                    pass
            if sub:
                child_rating = json.dumps(sub, ensure_ascii=False)
        except Exception:
            pass

        # ── 评分（整体星级）─────────────────────────────────────
        rating = 0.0
        try:
            # OpenRice 用 emoji 表情：😊(好) OK(一般) 😞(差)
            # 或者数字评分
            for sel in ["[class*='score']", "[class*='rating']", "[class*='star']"]:
                el = item.locator(sel).first
                try:
                    if await el.is_visible(timeout=800):
                        t = (await el.inner_text()).strip()
                        m = re.search(r'(\d+(?:\.\d+)?)', t)
                        if m:
                            rating = float(m.group(1))
                            break
                except Exception:
                    pass
        except Exception:
            pass

        # ── 组装 child_rating（含浏览量和点赞量）────────────────
        extra_info: dict = {}
        if view_count:
            extra_info["浏览量"] = view_count
        if like_count:
            extra_info["点赞量"] = like_count
        if extra_info:
            existing = json.loads(child_rating) if child_rating else {}
            existing.update(extra_info)
            child_rating = json.dumps(existing, ensure_ascii=False)

        return self._make_review(
            platform=self.platform,
            shop_id=shop_id,
            shop_name=shop_name,
            reviewer_name=reviewer or "匿名用户",
            content=content,
            rating=rating or 5.0,
            published_at=published_at,
            image_urls=img_urls,
            merchant_reply=None,   # OpenRice 商家回复在 div.review-post-comments
            child_rating=child_rating,
            review_type=review_type,
            page_url=page.url,
            ocr_strategy=OcrStrategy.DOM_PARSE.value,
        )

    # ══════════════════════════════════════════════════════════════
    # 时间解析
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _parse_openrice_time(s: str) -> Optional[datetime]:
        if not s:
            return None
        # 标准格式：2025-08-28
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s.strip()[:10], fmt)
            except ValueError:
                pass
        # 相对时间
        now = datetime.now()
        from datetime import timedelta
        patterns = [
            (r"(\d+)\s*分鐘前", "minutes"), (r"(\d+)\s*小時前", "hours"),
            (r"(\d+)\s*天前", "days"),       (r"(\d+)\s*週前", "weeks"),
            (r"(\d+)\s*個月前", "months"),   (r"(\d+)\s*年前", "years"),
        ]
        for pattern, unit in patterns:
            m = re.search(pattern, s)
            if m:
                n = int(m.group(1))
                delta = {
                    "minutes": timedelta(minutes=n), "hours": timedelta(hours=n),
                    "days": timedelta(days=n),        "weeks": timedelta(weeks=n),
                    "months": timedelta(days=n*30),   "years": timedelta(days=n*365),
                }[unit]
                return now - delta
        return None
