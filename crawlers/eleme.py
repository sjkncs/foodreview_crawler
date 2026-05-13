"""
饿了么评论爬虫 v2
新增：图片URLs、商家回复、子评分（口味/配送/包装）、页面URL
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

from core.models import OcrStrategy, Platform, Review, ReviewType
from .base import BaseCrawler

logger = logging.getLogger(__name__)

_API_KEYWORDS = ("ratings", "reviews", "comments", "evaluations")


class ElemeCrawler(BaseCrawler):
    platform = Platform.ELEME

    SHOP_URL = "https://h5.ele.me/shop/{shop_id}/"
    PC_URL   = "https://www.ele.me/shop/{shop_id}"

    def _get_shop_url(self, shop_id: str) -> str:
        return self.SHOP_URL.format(shop_id=shop_id)

    async def fetch_reviews(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        page = await self._context.new_page()
        api_queue: list[dict] = []

        async def on_response(resp):
            if any(k in resp.url for k in _API_KEYWORDS) and resp.status == 200:
                try:
                    body = await resp.json()
                    api_queue.append(body)
                except Exception:
                    pass

        page.on("response", on_response)
        page_url = self.SHOP_URL.format(shop_id=shop_id)

        try:
            await page.goto(page_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # 点击评价 Tab
            for tab in ["评价", "评论", "好评"]:
                try:
                    el = page.locator(f"text={tab}").first
                    if await el.is_visible(timeout=3000):
                        await el.click()
                        await page.wait_for_timeout(1500)
                        break
                except Exception:
                    pass

            for _ in range(max_pages):
                await page.wait_for_timeout(2000)
                while api_queue:
                    body = api_queue.pop(0)
                    batch = self._parse_api(body, shop_id, shop_name, review_type, page.url)
                    if batch:
                        yield batch
                if not await self._scroll_load_more(page):
                    break

        finally:
            await page.close()

    def _parse_api(
        self,
        data: dict,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        page_url: str,
    ) -> list[Review]:
        reviews: list[Review] = []
        try:
            items = (
                data.get("ratings", [])
                or data.get("data", {}).get("ratings", [])
                or data.get("reviews", [])
                or []
            )
            for item in items:
                content = (
                    item.get("body") or item.get("content") or item.get("comment") or ""
                ).strip()
                if not content:
                    continue

                rating = float(item.get("rating_star") or item.get("star") or 5)
                published_at = self._parse_time(
                    item.get("rated_at") or item.get("time") or item.get("created_at") or ""
                )

                # 图片（防御 pics 元素为字符串的情况）
                pics = item.get("images") or item.get("pics") or []
                img_urls = tuple(
                    (p.get("url") or p.get("image_url") if isinstance(p, dict) else str(p))
                    for p in pics if p
                )

                # 商家回复
                reply = item.get("reply") or item.get("merchant_reply") or {}
                merchant_reply = None
                if isinstance(reply, dict):
                    merchant_reply = reply.get("content") or reply.get("body")
                elif isinstance(reply, str):
                    merchant_reply = reply or None

                # 子评分（口味/配送/包装）
                sub = item.get("food_score") or {}
                if not sub:
                    sub = {
                        k: item.get(k)
                        for k in ["food_score", "pkg_score", "deliver_score"]
                        if item.get(k) is not None
                    }
                child_rating = json.dumps(sub, ensure_ascii=False) if sub else None

                reviews.append(self._make_review(
                    platform=self.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name=item.get("username") or item.get("nickname") or "匿名用户",
                    content=content,
                    rating=rating,
                    published_at=published_at,
                    image_urls=img_urls,
                    merchant_reply=merchant_reply,
                    child_rating=child_rating,
                    review_type=review_type,
                    page_url=page_url,
                    raw_data=json.dumps(item, ensure_ascii=False),
                    ocr_strategy=OcrStrategy.API_INTERCEPT.value,
                ))
        except Exception as exc:
            logger.warning("[饿了么] 解析失败: %s", exc)
        return reviews

    @staticmethod
    def _parse_time(s: str) -> Optional[datetime]:
        if not s:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s[:19], fmt)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
