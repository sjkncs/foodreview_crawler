"""
海外喜茶评论批量采集管线。

能力：
1. 根据地区 / 门店关键词 / JDE 批量选择目标店铺
2. 自动按平台逐店采集评论
3. 对评论执行自动筛选、翻译、情感与关键词分析
4. 支持导出本次运行结果
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from core.database import init_db, insert_review, insert_task, update_task_status
from core.models import CrawlTask, Platform, Review
from core.overseas_shops import (
    ShopProfile,
    ShopTarget,
    load_overseas_shop_profiles,
    load_overseas_shop_targets,
    similarity_score,
)
from crawlers import get_crawler
from crawlers.openrice import OpenRiceCrawler
from processors import export_csv, export_excel, export_json, process_and_save
from processors.review_filters import ReviewFilter, filter_reviews


@dataclass(frozen=True)
class BatchTargetResult:
    target: ShopTarget
    fetched_count: int
    kept_count: int
    saved_count: int
    status: str
    error: str | None = None


@dataclass(frozen=True)
class BatchCrawlSummary:
    started_at: datetime
    finished_at: datetime
    targets: tuple[BatchTargetResult, ...]
    export_path: str | None = None

    @property
    def fetched_total(self) -> int:
        return sum(item.fetched_count for item in self.targets)

    @property
    def kept_total(self) -> int:
        return sum(item.kept_count for item in self.targets)

    @property
    def saved_total(self) -> int:
        return sum(item.saved_count for item in self.targets)


async def crawl_overseas_reviews(
    *,
    region: str | None = None,
    shop_keywords: tuple[str, ...] = (),
    store_codes: tuple[str, ...] = (),
    platforms: tuple[Platform, ...] = (),
    max_shops: int | None = None,
    max_pages: int = 5,
    show_browser: bool = False,
    proxy: str | None = None,
    strategy: str = "hybrid",
    filters: ReviewFilter | None = None,
    no_analyze: bool = False,
    export_format: str | None = None,
) -> BatchCrawlSummary:
    init_db()
    started_at = datetime.now()
    selected_targets = await _resolve_targets(
        region=region,
        shop_keywords=shop_keywords,
        store_codes=store_codes,
        platforms=platforms,
        show_browser=show_browser,
        proxy=proxy,
    )
    if max_shops is not None:
        selected_targets = selected_targets[:max_shops]

    if not selected_targets:
        return BatchCrawlSummary(started_at=started_at, finished_at=datetime.now(), targets=tuple())

    rules = filters or ReviewFilter()
    results: list[BatchTargetResult] = []
    exported_reviews: list[Review] = []

    for target in selected_targets:
        task_id = insert_task(
            CrawlTask(
                id=None,
                platform=target.platform,
                shop_id=target.shop_id,
                shop_name=target.shop_name,
                status="running",
                started_at=datetime.now(),
                finished_at=None,
                ocr_strategy=strategy,
            )
        )
        try:
            crawler_kwargs = {}
            if target.platform == Platform.KEETA and target.platform_hint:
                crawler_kwargs["shop_hint"] = target.platform_hint
            if target.platform == Platform.HUNGRY_PANDA:
                if target.platform_hint:
                    crawler_kwargs["shop_hint"] = target.platform_hint
                if target.platform_url:
                    crawler_kwargs["login_url"] = target.platform_url
            crawler = get_crawler(
                target.platform,
                headless=not show_browser,
                proxy=proxy,
                strategy=strategy,
                **crawler_kwargs,
            )
            fetched_reviews = await crawler.crawl(
                shop_id=target.shop_id,
                shop_name=target.shop_name,
                max_pages=max_pages,
            )
            filtered_reviews = filter_reviews(fetched_reviews, rules)
            saved_reviews = await _save_reviews(filtered_reviews, no_analyze=no_analyze)
            exported_reviews.extend(saved_reviews)
            update_task_status(task_id, "done", total_fetched=len(fetched_reviews))
            results.append(
                BatchTargetResult(
                    target=target,
                    fetched_count=len(fetched_reviews),
                    kept_count=len(filtered_reviews),
                    saved_count=len(saved_reviews),
                    status="done",
                )
            )
        except Exception as exc:
            update_task_status(task_id, "failed", error_msg=str(exc))
            results.append(
                BatchTargetResult(
                    target=target,
                    fetched_count=0,
                    kept_count=0,
                    saved_count=0,
                    status="failed",
                    error=str(exc),
                )
            )

    export_path = _export_reviews(exported_reviews, export_format)
    return BatchCrawlSummary(
        started_at=started_at,
        finished_at=datetime.now(),
        targets=tuple(results),
        export_path=export_path,
    )


async def _save_reviews(reviews: list[Review], *, no_analyze: bool) -> list[Review]:
    if not reviews:
        return []
    if not no_analyze:
        return await process_and_save(reviews)
    await asyncio.to_thread(_insert_reviews_sync, reviews)
    return reviews


def _insert_reviews_sync(reviews: list[Review]) -> None:
    for review in reviews:
        insert_review(review)


def _export_reviews(reviews: list[Review], export_format: Optional[str]) -> str | None:
    if not reviews or not export_format:
        return None
    fmt = export_format.lower()
    if fmt == "excel":
        return str(export_excel(reviews))
    if fmt == "csv":
        return str(export_csv(reviews))
    if fmt == "json":
        return str(export_json(reviews))
    raise ValueError(f"不支持的导出格式: {export_format}")


async def _resolve_targets(
    *,
    region: str | None,
    shop_keywords: tuple[str, ...],
    store_codes: tuple[str, ...],
    platforms: tuple[Platform, ...],
    show_browser: bool,
    proxy: str | None,
) -> list[ShopTarget]:
    requested_platforms = set(platforms or [])
    static_targets = load_overseas_shop_targets(
        region=region,
        shop_keywords=shop_keywords,
        store_codes=store_codes,
        platforms=platforms,
    )
    if requested_platforms and Platform.OPENRICE not in requested_platforms:
        return static_targets
    if not requested_platforms and not _needs_openrice_discovery(region):
        return static_targets

    openrice_targets = await _discover_openrice_targets(
        region=region,
        shop_keywords=shop_keywords,
        store_codes=store_codes,
        show_browser=show_browser,
        proxy=proxy,
    )
    merged = static_targets + openrice_targets
    deduped: list[ShopTarget] = []
    seen: set[tuple[str, str]] = set()
    for target in merged:
        key = (target.platform.value, target.shop_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(target)
    return deduped


def _needs_openrice_discovery(region: str | None) -> bool:
    if not region:
        return True
    normalized = region.replace("中国", "").strip()
    return any(token in normalized for token in ("香港", "hk", "hong"))


async def _discover_openrice_targets(
    *,
    region: str | None,
    shop_keywords: tuple[str, ...],
    store_codes: tuple[str, ...],
    show_browser: bool,
    proxy: str | None,
) -> list[ShopTarget]:
    if not _needs_openrice_discovery(region):
        return []
    profiles = load_overseas_shop_profiles(
        region=region or "香港",
        shop_keywords=shop_keywords,
        store_codes=store_codes,
    )
    hk_profiles = [profile for profile in profiles if "香港" in profile.region]
    if not hk_profiles:
        return []

    crawler = OpenRiceCrawler(headless=not show_browser, proxy=proxy, strategy="dom_parse")
    try:
        discovered_shops = await crawler.get_all_shops()
    except Exception:
        return []

    targets: list[ShopTarget] = []
    seen_ids: set[str] = set()
    for profile in hk_profiles:
        match = match_openrice_shop(profile, discovered_shops)
        if not match:
            continue
        shop_url = str(match.get("url", "")).strip()
        if not shop_url or shop_url in seen_ids:
            continue
        seen_ids.add(shop_url)
        targets.append(
            ShopTarget(
                platform=Platform.OPENRICE,
                shop_id=shop_url,
                shop_name=profile.shop_name,
                region=profile.region,
                store_code=profile.store_code,
                address=profile.address,
                source="openrice_discovery",
            )
        )
    return targets


def match_openrice_shop(profile: ShopProfile, discovered_shops: list[dict], threshold: float = 0.35) -> dict | None:
    best: dict | None = None
    best_score = 0.0
    keywords = _extract_shop_keywords(profile.shop_name)
    if profile.openrice_hint:
        keywords += (profile.openrice_hint,)
    for shop in discovered_shops:
        candidate_name = str(shop.get("name", "")).strip()
        score = similarity_score(profile.shop_name, candidate_name)
        for keyword in keywords:
            if keyword and keyword in candidate_name:
                score = max(score, 0.8)
        if score >= threshold and score > best_score:
            best = shop
            best_score = score
    return best


def _extract_shop_keywords(shop_name: str) -> tuple[str, ...]:
    import re

    keywords = re.findall(r"[（(]([^）)]+)[）)]", shop_name or "")
    return tuple(keyword.strip() for keyword in keywords if keyword.strip())
