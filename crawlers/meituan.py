"""
美团外卖评论爬虫 v2
新增字段：图片URLs、商家回复、子评分（口味/配送/包装）、页面URL
策略：API 拦截（主）→ DOM 解析（备）
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

from core.models import OcrStrategy, Platform, Review, ReviewType
from .base import BaseCrawler

logger = logging.getLogger(__name__)

# 美团评论 API 路径特征
_API_KEYWORDS = ("comment", "review", "evaluate", "rating")


class MeituanCrawler(BaseCrawler):
    platform = Platform.MEITUAN

    SHOP_URL  = "https://h5.waimai.meituan.com/waimai/mindex/menu?wmPoiId={shop_id}"
    # PC版商家主页（更易爬）
    PC_URL    = "https://www.meituan.com/meishi/{shop_id}/"

    def _get_shop_url(self, shop_id: str) -> str:
        return self.SHOP_URL.format(shop_id=shop_id)

    # ── 主策略：API 拦截 ────────────────────────────────────────
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

            # 切换到评价 Tab
            for tab_text in ["评价", "好评", "全部评价"]:
                try:
                    tab = page.locator(f"text={tab_text}").first
                    if await tab.is_visible(timeout=3000):
                        await tab.click()
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

    # ── 备用策略：DOM 解析 ──────────────────────────────────────
    async def fetch_reviews_dom(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        page = await self._context.new_page()
        page_url = self.SHOP_URL.format(shop_id=shop_id)
        try:
            await page.goto(page_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            for _ in range(max_pages):
                batch = await self._parse_dom(page, shop_id, shop_name, review_type)
                if batch:
                    yield batch
                if not await self._scroll_load_more(page):
                    break
        finally:
            await page.close()

    async def _parse_dom(self, page, shop_id, shop_name, review_type) -> list[Review]:
        reviews: list[Review] = []
        try:
            items = page.locator(".comment-item, .review-item, [class*='comment'], [class*='review']")
            count = await items.count()
            for i in range(count):
                item = items.nth(i)
                content = ""
                for sel in [".comment-content", ".review-text", "p.content", ".text"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            content = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass
                if not content:
                    continue

                reviewer = ""
                for sel in [".username", ".nickname", ".user-name", ".name"]:
                    try:
                        el = item.locator(sel).first
                        if await el.is_visible(timeout=1000):
                            reviewer = (await el.inner_text()).strip()
                            break
                    except Exception:
                        pass

                # 图片
                img_els = item.locator("img[src*='img'], img[src*='photo']")
                img_count = await img_els.count()
                imgs = tuple([await img_els.nth(j).get_attribute("src") or "" for j in range(img_count)])
                imgs = tuple(u for u in imgs if u)

                # 商家回复
                merchant_reply = None
                for sel in [".merchant-reply", ".reply-content", ".owner-reply", "[class*='reply']"]:
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
                    rating=5.0,
                    published_at=datetime.now(),
                    image_urls=imgs,
                    merchant_reply=merchant_reply,
                    review_type=review_type,
                    page_url=page.url,
                    ocr_strategy=OcrStrategy.DOM_PARSE.value,
                ))
        except Exception as exc:
            logger.warning("[美团 DOM] 解析失败: %s", exc)
        return reviews

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
            comment_list = (
                data.get("data", {}).get("commentList", [])
                or data.get("data", {}).get("list", [])
                or data.get("commentList", [])
                or data.get("list", [])
            )
            for item in comment_list:
                content = (item.get("comment") or item.get("content") or "").strip()
                if not content:
                    continue

                # 评分处理（美团用 10/20/.../50 表示 1-5 星，需统一到 1-5 浮点）
                raw_star = float(item.get("starType") or item.get("star") or 50)
                if raw_star > 10:
                    rating = raw_star / 10   # 50 → 5.0, 40 → 4.0
                elif raw_star > 5:
                    rating = raw_star / 2    # 10-制：10 → 5.0
                else:
                    rating = raw_star        # 已是 1-5 直接使用
                rating = max(1.0, min(5.0, rating))   # 强制裁剪到合法范围

                # 发布时间
                published_at = self._parse_time(
                    item.get("publishTime") or item.get("time") or ""
                )

                # 图片 URLs
                pics = item.get("pictures") or item.get("imgs") or []
                if isinstance(pics, list):
                    img_urls = tuple(
                        (p.get("url") or p.get("src") or p) for p in pics
                        if isinstance(p, (dict, str))
                    )
                else:
                    img_urls = ()
                img_urls = tuple(str(u) for u in img_urls if u)

                # 商家回复
                reply_info = item.get("reply") or item.get("merchantReply") or {}
                merchant_reply = None
                if isinstance(reply_info, dict):
                    merchant_reply = reply_info.get("content") or reply_info.get("text")
                elif isinstance(reply_info, str) and reply_info:
                    merchant_reply = reply_info

                # 子评分（口味/配送/包装）
                sub_ratings = item.get("subRatings") or item.get("tagScores") or {}
                child_rating = json.dumps(sub_ratings, ensure_ascii=False) if sub_ratings else None

                reviews.append(self._make_review(
                    platform=self.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name=item.get("userNick") or item.get("username") or "匿名用户",
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
            logger.warning("[美团 API] 解析失败: %s", exc)
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
