"""
OpenRice 批量爬取主脚本
用法：
  python run_openrice.py                    # 爬取所有香港喜茶店铺
  python run_openrice.py --headless false   # 显示浏览器（调试）
  python run_openrice.py --max-pages 3      # 每店最多3页
  python run_openrice.py --shop "荃新天地"  # 只爬指定店铺

流程：
  1. 读取 Excel 获取香港喜茶店铺名称
  2. 打开 OpenRice 品牌页，获取所有店铺 URL
  3. 按名称匹配（模糊匹配）
  4. 逐店爬取：食評Tab → 最新排序 → 展开全文 → 提取所有字段
  5. AI 处理（翻译+情感+关键词）
  6. 导出 Excel
"""
from __future__ import annotations
import asyncio
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.database import init_db
from core.models import Platform, ReviewType
from crawlers.openrice import OpenRiceCrawler, CHAIN_URL
from processors.pipeline import process_and_save
from processors.reporter import export_excel, export_csv
from excel_reader import read_shop_list, get_hk_shop_names

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/openrice_crawl.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

Path("logs").mkdir(exist_ok=True)


def _similarity(a: str, b: str) -> float:
    """字符重叠相似度（用于店铺名匹配）"""
    a_set = set(a.lower().replace(" ", ""))
    b_set = set(b.lower().replace(" ", ""))
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / len(a_set | b_set)


def match_shop(excel_name: str, openrice_shops: list[dict], threshold: float = 0.4) -> list[dict]:
    """
    将 Excel 店铺名与 OpenRice 店铺列表匹配。
    返回相似度超过阈值的所有候选（通常只有1个）。
    """
    # 提取括号内的关键词（如「荃新天地」）
    import re
    keywords = re.findall(r'[（(]([^）)]+)[）)]', excel_name)
    core_name = re.sub(r'香港|喜茶|HEYTEA', '', excel_name).strip()

    candidates = []
    for shop in openrice_shops:
        or_name = shop["name"]
        score = _similarity(core_name, or_name)
        # 关键词精确匹配加分
        for kw in keywords:
            if kw in or_name:
                score = max(score, 0.8)
        if score >= threshold:
            candidates.append({**shop, "match_score": score})

    return sorted(candidates, key=lambda x: x["match_score"], reverse=True)


async def crawl_all(args: argparse.Namespace) -> None:
    init_db()

    # ── 1. 读取 Excel 店铺名 ──────────────────────────────────────
    excel_shops = read_shop_list(region_filter="中国香港")
    if args.shop:
        excel_shops = [s for s in excel_shops if args.shop in s["shop_name"]]
    logger.info("Excel 中香港喜茶门店: %d 家", len(excel_shops))
    for s in excel_shops:
        logger.info("  - %s", s["shop_name"])

    # ── 2. 获取 OpenRice 品牌页所有店铺 ──────────────────────────
    logger.info("正在获取 OpenRice 品牌页店铺列表...")
    crawler = OpenRiceCrawler(
        headless=args.headless,
        strategy="dom_parse",
    )
    openrice_shops = await crawler.get_all_shops()
    logger.info("OpenRice 品牌页共 %d 家店铺:", len(openrice_shops))
    for s in openrice_shops:
        logger.info("  - %s  %s", s["name"], s["url"])

    if not openrice_shops:
        logger.error("OpenRice 品牌页未获取到店铺，请检查网络或 URL")
        return

    # ── 3. 匹配 + 爬取 ───────────────────────────────────────────
    all_reviews = []
    skipped = []
    matched_count = 0

    for excel_shop in excel_shops:
        shop_name = excel_shop["shop_name"]
        candidates = match_shop(shop_name, openrice_shops, threshold=0.35)

        if not candidates:
            logger.warning("  [跳过] %s → OpenRice 未找到匹配店铺", shop_name)
            skipped.append(shop_name)
            continue

        best = candidates[0]
        logger.info("  [匹配] %s → %s (相似度:%.2f) %s",
                    shop_name, best["name"], best["match_score"], best["url"])
        matched_count += 1

        # 爬取该店铺评论
        try:
            crawler = OpenRiceCrawler(
                headless=args.headless,
                strategy="dom_parse",
            )
            await crawler._start_browser()
            reviews = []

            async for batch in crawler.fetch_reviews(
                shop_id=best["url"],
                shop_name=shop_name,
                max_pages=args.max_pages,
                review_type=ReviewType.REVIEW,
            ):
                reviews.extend(batch)
                logger.info("    已爬取 %d 条...", len(reviews))

            await crawler._close_browser()
            logger.info("  [完成] %s: %d 条评论", shop_name, len(reviews))
            all_reviews.extend(reviews)

        except Exception as exc:
            logger.error("  [失败] %s: %s", shop_name, exc)
            try:
                await crawler._close_browser()
            except Exception:
                pass

    # ── 4. AI 处理 ────────────────────────────────────────────────
    if all_reviews and not args.no_analyze:
        logger.info("开始 AI 处理 %d 条评论（翻译+情感+关键词）...", len(all_reviews))
        processed = await process_and_save(
            all_reviews,
            progress_callback=lambda cur, total: logger.info("  AI处理: %d/%d", cur, total),
        )
        logger.info("AI 处理完成: %d 条", len(processed))
        final_reviews = processed
    else:
        from core.database import insert_review
        for r in all_reviews:
            insert_review(r)
        final_reviews = all_reviews

    # ── 5. 导出 ───────────────────────────────────────────────────
    if final_reviews:
        path_excel = export_excel(final_reviews)
        path_csv   = export_csv(final_reviews)
        logger.info("导出完成:")
        logger.info("  Excel: %s", path_excel)
        logger.info("  CSV:   %s", path_csv)
    else:
        logger.warning("未获取到任何评论")

    # ── 6. 汇总报告 ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("OpenRice 爬取汇总")
    print("=" * 60)
    print(f"  Excel 门店数:    {len(excel_shops)}")
    print(f"  OpenRice 店铺数: {len(openrice_shops)}")
    print(f"  成功匹配:        {matched_count}")
    print(f"  跳过(未找到):    {len(skipped)}")
    print(f"  总评论数:        {len(final_reviews)}")
    if skipped:
        print(f"\n  未匹配店铺:")
        for s in skipped:
            print(f"    - {s}")
    if final_reviews:
        print(f"\n  导出文件: {path_excel}")


def main():
    parser = argparse.ArgumentParser(description="OpenRice 喜茶评论批量爬取")
    parser.add_argument("--headless", type=lambda x: x.lower() != "false",
                        default=True, help="无头模式（默认True，调试用False）")
    parser.add_argument("--max-pages", type=int, default=10,
                        help="每家店最多爬取页数（默认10）")
    parser.add_argument("--shop", type=str, default="",
                        help="只爬取包含此关键词的店铺（如：荃新天地）")
    parser.add_argument("--no-analyze", action="store_true",
                        help="跳过 AI 分析，只爬取原始数据")
    args = parser.parse_args()

    asyncio.run(crawl_all(args))


if __name__ == "__main__":
    main()
