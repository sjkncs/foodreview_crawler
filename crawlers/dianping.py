"""
大众点评爬虫 v2
新增：图片URLs、商家回复、子评分（口味/环境/服务）、页面URL
主策略：DOM 解析（大众点评反爬较强，无稳定 API）
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

from core.models import OcrStrategy, Platform, Review, ReviewType
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class DianpingCrawler(BaseCrawler):
    platform = Platform.DIANPING

    SHOP_URL = "https://www.dianping.com/shop/{shop_id}/review_all"

    def _get_shop_url(self, shop_id: str) -> str:
        if shop_id.startswith("http"):
            return shop_id
        return self.SHOP_URL.format(shop_id=shop_id)

    async def fetch_reviews(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        """大众点评使用 DOM 解析（无稳定 JSON API）"""
        page = await self._context.new_page()
        page_url = self._get_shop_url(shop_id)
        try:
            await page.goto(page_url, timeout=30000)

            for _ in range(max_pages):
                await page.wait_for_load_state("networkidle", timeout=10000)
                batch = await self._parse_dom(page, shop_id, shop_name, review_type)
                if batch:
                    yield batch

                # 翻页按钮
                try:
                    next_btn = page.locator("a.next, a[data-page='next'], .page-next").first
                    if await next_btn.is_visible(timeout=3000):
                        await next_btn.click()
                        await page.wait_for_timeout(2000)
                    else:
                        break
                except Exception:
                    break
        finally:
            await page.close()

    async def _parse_dom(
        self,
        page,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
    ) -> list[Review]:
        reviews: list[Review] = []
        try:
            # 大众点评评论区选择器（可能随版本变化）
            selectors = ["li.comment-item", "div.review-item", "[class*='comment-list'] li"]
            items_loc = None
            for sel in selectors:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    items_loc = loc
                    break

            if not items_loc:
                return reviews

            count = await items_loc.count()
            for i in range(count):
                item = items_loc.nth(i)

                # 评论内容
                content = ""
                for sel in [".review-words", ".content", "p.desc", ".J_brief_cont"]:
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
                for sel in [".name", ".username", ".user-name"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            reviewer = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass

                # 评分（从 CSS class 提取）
                rating = 0.0
                for sel in [".star", "[class*='star']"]:
                    try:
                        el = item.locator(sel).first
                        cls = await el.get_attribute("class") or ""
                        rating = self._extract_star(cls)
                        if rating:
                            break
                    except Exception:
                        pass

                # 子评分（口味/环境/服务）
                child_rating = None
                sub = {}
                for label_text in ["口味", "环境", "服务"]:
                    try:
                        label_el = item.locator(f"text={label_text}")
                        if await label_el.count() > 0:
                            parent = label_el.first.locator("xpath=..")
                            score_el = parent.locator("[class*='star'], .score")
                            score_cls = await score_el.first.get_attribute("class") or ""
                            sub[label_text] = self._extract_star(score_cls)
                    except Exception:
                        pass
                if sub:
                    child_rating = json.dumps(sub, ensure_ascii=False)

                # 发布时间
                date_str = ""
                for sel in [".time", ".date", ".review-time"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            date_str = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass
                published_at = self._parse_time(date_str)

                # 图片
                img_urls: tuple[str, ...] = ()
                try:
                    imgs = item.locator("img.pic, .photo img, [class*='photo'] img")
                    n = await imgs.count()
                    raw_imgs = [await imgs.nth(j).get_attribute("src") or "" for j in range(n)]
                    img_urls = tuple(u for u in raw_imgs if u and "avatar" not in u)
                except Exception:
                    pass

                # 商家回复
                merchant_reply = None
                for sel in [".reply-content", ".merchant-reply", "[class*='reply']"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            merchant_reply = (await el.inner_text()).strip()
                            break
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
            logger.warning("[大众点评 DOM] 解析失败: %s", exc)
        return reviews

    @staticmethod
    def _extract_star(css_class: str) -> float:
        import re
        m = re.search(r"star-?(\d+)", css_class)
        if m:
            v = int(m.group(1))
            return v / 10 if v > 5 else float(v)
        return 0.0

    @staticmethod
    def _parse_time(s: str) -> Optional[datetime]:
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%Y年%m月%d日", "%Y/%m/%d"):
            try:
                return datetime.strptime(s.strip()[:10], fmt)
            except ValueError:
                pass
        return None
