"""
抖音外卖评论爬虫 v2
新增：图片URLs、商家回复、子评分、页面URL
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

from core.models import OcrStrategy, Platform, Review, ReviewType
from .base import BaseCrawler

logger = logging.getLogger(__name__)

_API_KEYWORDS = ("comment", "review", "rating", "evaluate", "poi_detail")


class DouyinCrawler(BaseCrawler):
    platform = Platform.DOUYIN

    SHOP_URL = "https://www.douyin.com/store/poi/{shop_id}"

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

            for _ in range(max_pages):
                await page.wait_for_timeout(2500)
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
                data.get("comment_list", [])
                or data.get("data", {}).get("list", [])
                or data.get("list", [])
                or []
            )
            for item in items:
                content = (
                    item.get("content") or item.get("text") or
                    item.get("comment_text") or ""
                ).strip()
                if not content:
                    continue

                rating = float(item.get("star") or item.get("rating") or 5)

                # 时间戳转换
                ts = item.get("create_time") or item.get("timestamp") or 0
                try:
                    published_at = datetime.fromtimestamp(int(ts)) if ts else None
                except Exception:
                    published_at = None

                # 图片
                pics = item.get("images") or item.get("pic_list") or []
                img_urls = tuple(
                    (p.get("url") or p.get("uri") or str(p))
                    for p in pics if p
                )

                # 商家回复
                reply = item.get("reply") or item.get("merchant_reply") or {}
                merchant_reply = None
                if isinstance(reply, dict):
                    merchant_reply = reply.get("content") or reply.get("text")
                elif isinstance(reply, str):
                    merchant_reply = reply or None

                # 子评分
                sub = {
                    k: item.get(k)
                    for k in ["taste_score", "pack_score", "speed_score", "service_score"]
                    if item.get(k) is not None
                }
                child_rating = json.dumps(sub, ensure_ascii=False) if sub else None

                reviews.append(self._make_review(
                    platform=self.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name=item.get("nickname") or item.get("user_name") or "匿名用户",
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
            logger.warning("[抖音] 解析失败: %s", exc)
        return reviews
