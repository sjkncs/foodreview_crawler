"""
Google Maps 评论爬虫 v2
新增：图片URLs、商家回复、子评分（各维度）、页面URL
主策略：DOM 解析（滚动加载）
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


class GoogleMapsCrawler(BaseCrawler):
    platform = Platform.GOOGLE_MAPS

    PLACE_URL = "https://www.google.com/maps/place/?q=place_id:{shop_id}"

    def _get_shop_url(self, shop_id: str) -> str:
        if shop_id.startswith("http"):
            return shop_id
        return self.PLACE_URL.format(shop_id=shop_id)

    async def fetch_reviews(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        page = await self._context.new_page()
        url = self._get_shop_url(shop_id)

        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # 点击"评论" Tab（中/英文自适应）
            for tab_label in ['[data-tab-index="1"]', 'button[aria-label*="评论"]',
                               'button[aria-label*="Reviews"]']:
                try:
                    await page.click(tab_label, timeout=4000)
                    await page.wait_for_timeout(1500)
                    break
                except Exception:
                    pass

            # 按最新排序
            for sort_label in ['[aria-label="排序评论"]', '[aria-label="Sort reviews"]',
                                'button[jsaction*="sortReviews"]']:
                try:
                    await page.click(sort_label, timeout=3000)
                    await page.wait_for_timeout(800)
                    for newest in ["最新", "Newest", "最近"]:
                        try:
                            await page.click(f"text={newest}", timeout=2000)
                            await page.wait_for_timeout(1500)
                            break
                        except Exception:
                            pass
                    break
                except Exception:
                    pass

            seen: set[str] = set()

            for _ in range(max_pages):
                batch = await self._parse_dom(page, shop_id, shop_name, review_type, seen)
                if batch:
                    yield batch

                # 滚动评论面板
                scrolled = False
                for scroll_sel in ['[data-section-id="reviews"]', '.m6QErb', '.section-scrollbox']:
                    try:
                        panel = page.locator(scroll_sel).first
                        if await panel.is_visible(timeout=2000):
                            await panel.evaluate("el => el.scrollBy(0, 3000)")
                            await page.wait_for_timeout(2000)
                            scrolled = True
                            break
                    except Exception:
                        pass

                if not scrolled:
                    if not await self._scroll_load_more(page):
                        break

        finally:
            await page.close()

    async def _parse_dom(
        self,
        page,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        seen: set[str],
    ) -> list[Review]:
        reviews: list[Review] = []
        try:
            # Google Maps 评论卡片
            items = page.locator('[data-review-id], .jftiEf, [class*="review"]')
            count = await items.count()

            for i in range(count):
                item = items.nth(i)
                review_id = await item.get_attribute("data-review-id") or f"gm_{i}"
                if review_id in seen:
                    continue
                seen.add(review_id)

                # 展开"更多"
                try:
                    more = item.locator("button.w8nwRe, button[aria-label*='更多'], button[aria-label*='More']").first
                    if await more.is_visible(timeout=1000):
                        await more.click()
                        await page.wait_for_timeout(300)
                except Exception:
                    pass

                # 评论内容
                content = ""
                for sel in [".MyEned span", ".wiI7pd", "[class*='review-text']", ".review-full-text"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            content = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass
                if not content:
                    continue

                # 用户名
                reviewer = ""
                for sel in [".d4r55", ".WNxjEc", "[class*='author']"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            reviewer = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass

                # 评分
                rating = 0.0
                for sel in ["[aria-label*='颗星']", "[aria-label*='star']", "[aria-label*='Star']"]:
                    try:
                        el = item.locator(sel).first
                        label = await el.get_attribute("aria-label") or ""
                        rating = self._parse_star_label(label)
                        if rating:
                            break
                    except Exception:
                        pass

                # 发布时间（Google Maps 显示相对时间，尝试解析为近似绝对时间）
                date_text = ""
                for sel in [".rsqaWe", ".DU9Pgb", "[class*='date']"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            date_text = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass
                published_at = self._parse_relative_time(date_text) or datetime.now()

                # 图片
                img_urls: tuple[str, ...] = ()
                try:
                    imgs = item.locator("img.KtCyie, .review-photo img, [class*='photo'] img")
                    n = await imgs.count()
                    raw = [await imgs.nth(j).get_attribute("src") or "" for j in range(n)]
                    img_urls = tuple(u for u in raw if u and "googleusercontent" in u)
                except Exception:
                    pass

                # 商家回复
                merchant_reply = None
                for sel in [".CDe7pd", ".IFVkKe", "[class*='owner-response']", "[class*='reply']"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            merchant_reply = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass

                # 子评分（各维度 aspect rating）
                child_rating = None
                sub = {}
                try:
                    aspects = item.locator(".r7HvHe, [class*='aspect']")
                    a_count = await aspects.count()
                    for j in range(a_count):
                        a = aspects.nth(j)
                        lbl = (await a.inner_text()).strip()
                        if lbl:
                            sub[lbl] = True
                    if sub:
                        child_rating = json.dumps(sub, ensure_ascii=False)
                except Exception:
                    pass

                reviews.append(self._make_review(
                    platform=self.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name=reviewer or "匿名",
                    content=content,
                    rating=rating or 5.0,
                    published_at=published_at,
                    image_urls=img_urls,
                    merchant_reply=merchant_reply,
                    child_rating=child_rating,
                    review_type=review_type,
                    page_url=page.url,
                    ocr_strategy=OcrStrategy.DOM_PARSE.value,
                ))

        except Exception as exc:
            logger.warning("[Google Maps] 解析失败: %s", exc)
        return reviews

    @staticmethod
    def _parse_star_label(label: str) -> float:
        m = re.search(r"(\d+(?:\.\d+)?)", label)
        return float(m.group(1)) if m else 5.0

    @staticmethod
    def _parse_relative_time(text: str) -> Optional[datetime]:
        """
        将 Google Maps 相对时间转换为近似绝对时间。
        支持中英文：'3天前' / '2 weeks ago' / '1个月前' / 'a year ago' 等
        """
        if not text:
            return None
        now = datetime.now()
        text = text.strip().lower()

        # 中文模式
        patterns_zh = [
            (r"(\d+)\s*分钟前", "minutes"),
            (r"(\d+)\s*小时前", "hours"),
            (r"(\d+)\s*天前",   "days"),
            (r"(\d+)\s*周前",   "weeks"),
            (r"(\d+)\s*个月前", "months"),
            (r"(\d+)\s*年前",   "years"),
            (r"刚刚",           "just"),
        ]
        # 英文模式
        patterns_en = [
            (r"(\d+)\s*minute",  "minutes"),
            (r"(\d+)\s*hour",    "hours"),
            (r"(\d+)\s*day",     "days"),
            (r"(\d+)\s*week",    "weeks"),
            (r"(\d+)\s*month",   "months"),
            (r"(\d+)\s*year",    "years"),
            (r"a\s+minute",      "minutes"),
            (r"an?\s+hour",      "hours"),
            (r"a\s+day",         "days"),
            (r"a\s+week",        "weeks"),
            (r"a\s+month",       "months"),
            (r"a\s+year",        "years"),
            (r"just\s+now",      "just"),
        ]

        from datetime import timedelta
        for pattern, unit in patterns_zh + patterns_en:
            m = re.search(pattern, text)
            if m:
                n = 1 if unit == "just" or not m.lastindex else int(m.group(1))
                if unit == "just" or unit == "minutes":
                    return now - timedelta(minutes=n)
                if unit == "hours":
                    return now - timedelta(hours=n)
                if unit == "days":
                    return now - timedelta(days=n)
                if unit == "weeks":
                    return now - timedelta(weeks=n)
                if unit == "months":
                    return now - timedelta(days=n * 30)
                if unit == "years":
                    return now - timedelta(days=n * 365)
        return None
