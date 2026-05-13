"""
评论筛选器。

用于在批量采集场景下做自动过滤，避免将无关评论送入后续 AI 管线。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re

from core.models import Review
from .translator import needs_translation


@dataclass(frozen=True)
class ReviewFilter:
    since_days: int | None = None
    min_rating: float | None = None
    max_rating: float | None = None
    include_keywords: tuple[str, ...] = field(default_factory=tuple)
    exclude_keywords: tuple[str, ...] = field(default_factory=tuple)
    foreign_only: bool = False
    dedupe: bool = True


def parse_keywords(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(part.strip() for part in re.split(r"[,，|/]", raw) if part.strip())


def filter_reviews(reviews: list[Review], rules: ReviewFilter) -> list[Review]:
    seen: set[tuple[str, str, str, str]] = set()
    kept: list[Review] = []
    for review in reviews:
        if rules.foreign_only and not needs_translation(review.content):
            continue
        if rules.since_days is not None and not _within_days(review, rules.since_days):
            continue
        if rules.min_rating is not None and review.rating < rules.min_rating:
            continue
        if rules.max_rating is not None and review.rating > rules.max_rating:
            continue
        haystack = _build_haystack(review)
        if rules.include_keywords and not any(keyword.lower() in haystack for keyword in rules.include_keywords):
            continue
        if rules.exclude_keywords and any(keyword.lower() in haystack for keyword in rules.exclude_keywords):
            continue

        if rules.dedupe:
            key = (
                review.platform.value,
                review.shop_id,
                _normalize_text(review.reviewer_name),
                _normalize_text(review.content),
            )
            if key in seen:
                continue
            seen.add(key)

        kept.append(review)
    return kept


def _build_haystack(review: Review) -> str:
    parts = [
        review.shop_name,
        review.reviewer_name,
        review.content,
        review.translated_content or "",
        review.merchant_reply or "",
    ]
    return " ".join(parts).lower()


def _within_days(review: Review, since_days: int) -> bool:
    baseline = review.published_at or review.crawled_at
    if not baseline:
        return False
    return baseline >= datetime.now() - timedelta(days=since_days)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).lower()
