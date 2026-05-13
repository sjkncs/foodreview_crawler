"""
喜茶舆情监控主程序
- 每小时自动采集百度新闻、微博、知乎、36氪、虎嗅
- 结果去重后追加写入 CSV（每天一个文件）
- 运行: python sentiment_monitor.py [--keyword 喜茶] [--days 7] [--once]
"""
from __future__ import annotations
import argparse
import asyncio
import csv
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sentiment_monitor")

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "exports")
CSV_FIELDNAMES = [
    "id", "keyword", "source", "title", "url",
    "snippet", "author", "publish_time", "crawl_time",
    "sentiment", "tags",
]


def get_csv_path(keyword: str) -> str:
    today = datetime.now().strftime("%Y%m%d")
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    return os.path.join(EXPORTS_DIR, f"sentiment_{keyword}_{today}.csv")


def load_existing_ids(csv_path: str) -> set[str]:
    """读取已有 CSV 中的 id，用于去重"""
    if not os.path.exists(csv_path):
        return set()
    ids: set[str] = set()
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("id"):
                ids.add(row["id"])
    return ids


def append_to_csv(articles: list, csv_path: str):
    """追加写入 CSV，首次创建时写入表头"""
    is_new = not os.path.exists(csv_path)
    with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if is_new:
            writer.writeheader()
        for art in articles:
            writer.writerow(art.to_dict())


async def run_once(keyword: str = "喜茶", days: int = 7, headless: bool = True):
    from crawlers.sentiment import (
        BaiduNewsCrawler, WeiboCrawler, ZhihuCrawler, TechMediaCrawler
    )

    logger.info("===== 开始采集 [%s] 舆情 =====", keyword)
    csv_path = get_csv_path(keyword)
    existing_ids = load_existing_ids(csv_path)
    logger.info("已有记录 %d 条（去重用）", len(existing_ids))

    all_articles = []

    # 各平台顺序采集（避免并发触发反爬）
    crawlers = [
        ("百度新闻", BaiduNewsCrawler(headless=headless)),
        ("微博",     WeiboCrawler(headless=headless)),
        ("知乎",     ZhihuCrawler(headless=headless)),
        ("科技媒体", TechMediaCrawler(headless=headless)),
    ]

    for name, crawler in crawlers:
        try:
            logger.info("正在采集: %s ...", name)
            results = await crawler.search(keyword, days=days)
            all_articles.extend(results)
            logger.info("%s 采集完成: %d 条", name, len(results))
        except Exception as e:
            logger.error("%s 采集失败: %s", name, e)

    # 去重（跨平台 + 跨历史）
    seen: set[str] = set(existing_ids)
    new_articles = []
    for art in all_articles:
        if art.id not in seen:
            seen.add(art.id)
            new_articles.append(art)

    if new_articles:
        # 写入 CSV
        append_to_csv(new_articles, csv_path)
        # 写入 SQLite（供 Web UI 使用）
        try:
            from core.sentiment_db import init_sentiment_db, upsert_articles
            init_sentiment_db()
            db_inserted = upsert_articles(new_articles)
            logger.info("新增 %d 条 → CSV: %s | SQLite: %d 条入库", len(new_articles), csv_path, db_inserted)
        except Exception as e:
            logger.warning("写入 SQLite 失败（不影响 CSV）: %s", e)
    else:
        logger.info("无新增内容")

    logger.info("===== 采集完成，本次共 %d 条新数据 =====", len(new_articles))
    return new_articles


def main():
    parser = argparse.ArgumentParser(description="茶饮品牌舆情监控")
    parser.add_argument("--keyword", default="喜茶", help="监控关键词（默认: 喜茶）")
    parser.add_argument("--days", type=int, default=7, help="采集最近N天（默认: 7）")
    parser.add_argument("--once", action="store_true", help="只执行一次，不循环")
    parser.add_argument("--headless", action="store_true", default=False,
                        help="无头模式（微博/知乎首次需要登录，建议不加此参数）")
    parser.add_argument("--interval", type=int, default=60,
                        help="定时间隔（分钟，默认60）")
    args = parser.parse_args()

    if args.once:
        asyncio.run(run_once(args.keyword, args.days, args.headless))
        return

    # 定时循环
    import schedule
    import time

    def job():
        asyncio.run(run_once(args.keyword, args.days, args.headless))

    # 立即执行一次
    job()

    # 每 N 分钟执行一次
    schedule.every(args.interval).minutes.do(job)
    logger.info("定时任务已启动，每 %d 分钟采集一次，按 Ctrl+C 停止", args.interval)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
