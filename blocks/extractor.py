"""
提取块：评论数据提取（对接现有爬虫）
人机协同门（GUI 等待确认）
"""
from __future__ import annotations
import logging
from typing import Optional

from .base_block import BaseBlock, BlockResult
# 重用现有爬虫的 _make_review 和数据库层
from core.models import Platform, ReviewType

logger = logging.getLogger(__name__)


class ExtractReviewsBlock(BaseBlock):
    """
    积木块：从当前页面提取评论。
    直接复用现有爬虫的 fetch_reviews_dom / fetch_reviews_ocr，
    不重复实现，只做调度和结果聚合。
    """
    name = "ExtractReviews"
    timeout_s = 120.0

    def __init__(
        self,
        platform: Platform,
        shop_id: str,
        shop_name: str,
        max_pages: int = 10,
        review_type: ReviewType = ReviewType.REVIEW,
        strategy: str = "hybrid",
    ):
        self.platform = platform
        self.shop_id = shop_id
        self.shop_name = shop_name
        self.max_pages = max_pages
        self.review_type = review_type
        self.strategy = strategy

    async def execute(self, ctx: dict) -> BlockResult:
        from crawlers import get_crawler
        # 复用已有爬虫（不重启浏览器，共享 context）
        crawler = get_crawler(
            self.platform,
            headless=ctx.get("headless", True),
            strategy=self.strategy,
        )
        crawler._context = ctx.get("browser_context")  # 共享已登录的 context

        reviews = []
        try:
            async for batch in crawler._dispatch_strategy(
                crawler._resolve_strategy(),
                self.shop_id,
                self.shop_name,
                self.max_pages,
                self.review_type,
            ):
                reviews.extend(batch)
                if ctx.get("progress_cb"):
                    ctx["progress_cb"](len(reviews), -1)
        except Exception as exc:
            if not reviews:
                return BlockResult.fail(f"提取失败: {exc}")
            logger.warning("[ExtractReviews] 部分失败，已获取 %d 条: %s", len(reviews), exc)

        if not reviews:
            return BlockResult.skip(f"{self.shop_name} 无评论数据")

        ctx["reviews"] = ctx.get("reviews", []) + reviews
        return BlockResult.success(reviews, f"提取 {len(reviews)} 条评论")


class AIProcessBlock(BaseBlock):
    """
    积木块：AI 批量处理（翻译 + 情感 + 关键词 + 回复建议）
    复用 processors.pipeline
    """
    name = "AIProcess"
    timeout_s = 300.0

    async def execute(self, ctx: dict) -> BlockResult:
        reviews = ctx.get("reviews", [])
        if not reviews:
            return BlockResult.skip("没有评论可处理")

        from processors.pipeline import process_and_save
        processed = await process_and_save(
            reviews,
            progress_callback=ctx.get("progress_cb"),
        )
        ctx["processed_reviews"] = processed
        return BlockResult.success(processed, f"AI 处理完成: {len(processed)} 条")


class ExportBlock(BaseBlock):
    """积木块：导出结果"""
    name = "Export"

    def __init__(self, fmt: str = "excel"):
        self.fmt = fmt.lower()

    async def execute(self, ctx: dict) -> BlockResult:
        reviews = ctx.get("processed_reviews") or ctx.get("reviews", [])
        if not reviews:
            return BlockResult.skip("没有数据可导出")

        from processors.reporter import export_csv, export_excel, export_json
        fn = {"excel": export_excel, "csv": export_csv, "json": export_json}.get(
            self.fmt, export_excel
        )
        path = fn(reviews)
        ctx["export_path"] = str(path)
        return BlockResult.success(str(path), f"已导出到: {path}")
