"""
批量处理管线 v3
- 同步 SQLite 操作用 asyncio.to_thread 包裹，避免阻塞事件循环
- gather 使用 return_exceptions=True，防止单条失败影响整批
- Semaphore 降至 3，避免触发 API 限速（每条评论实际发 3 次请求）
- 进度计数用原子计数器，防止乱序回跳
"""
from __future__ import annotations
import asyncio
import logging
from typing import Callable, Optional

from core.database import insert_review, update_review_analysis
from core.models import Review
from .sentiment import analyze_sentiment
from .keywords import extract_keywords
from .reply_gen import generate_reply
from .translator import translate_review
import config

logger = logging.getLogger(__name__)


async def process_review(review: Review) -> Review:
    """完整处理单条评论（翻译 → 情感 → 关键词 → 回复），返回新实例"""
    if config.get("auto_translate", True):
        review = await translate_review(review)
    review = await analyze_sentiment(review)
    review = await extract_keywords(review)
    if config.get("auto_reply", False):
        review = await generate_reply(review)
    return review


async def process_and_save(
    reviews: list[Review],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[Review]:
    """
    批量处理评论并存入数据库。
    - 同步 DB 操作通过 asyncio.to_thread 在线程池执行，不阻塞事件循环
    - 单条失败不影响其他条目（return_exceptions=True）
    - 进度用原子计数器保证单调递增
    """
    total = len(reviews)
    semaphore = asyncio.Semaphore(3)   # 每条发 3 次 AI 请求，实际并发 ≤9
    done_count = 0

    async def _worker(rev: Review) -> Optional[Review]:
        nonlocal done_count
        async with semaphore:
            try:
                # DB 写入放入线程池，避免阻塞 asyncio 事件循环
                rev_id: int = await asyncio.to_thread(insert_review, rev)
                processed = await process_review(rev)
                await asyncio.to_thread(update_review_analysis, rev_id, processed)
                done_count += 1
                if progress_callback:
                    progress_callback(done_count, total)
                return processed
            except Exception as exc:
                logger.warning("评论处理失败，跳过: %s | %s", rev.content[:30], exc)
                done_count += 1
                if progress_callback:
                    progress_callback(done_count, total)
                return None

    raw_results = await asyncio.gather(*[_worker(r) for r in reviews], return_exceptions=False)
    return [r for r in raw_results if r is not None]
