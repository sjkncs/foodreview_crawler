"""
CLI 命令行入口 - 无需浏览器，适合自动化/脚本集成
用法:
  python cli.py crawl --platform 美团外卖 --shop-id 12345 --shop-name "某餐厅" --max-pages 5
  python cli.py list --platform 美团外卖 --sentiment 负面
  python cli.py export --format excel
  python cli.py stats
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import argparse
import logging
from core.database import init_db, get_reviews, get_sentiment_stats, get_top_keywords
from core.models import Platform, ReviewType, SentimentLabel
from crawlers import get_crawler
from overseas_pipeline import crawl_overseas_reviews
from processors import process_and_save, export_csv, export_excel, export_json
from processors.review_filters import ReviewFilter, parse_keywords
from core.overseas_shops import load_platform_manifests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ──────────────────────── 子命令实现 ────────────────────────────────

async def cmd_crawl(args: argparse.Namespace) -> None:
    """爬取评论"""
    try:
        platform = Platform(args.platform)
    except ValueError:
        print(f"❌ 不支持的平台: {args.platform}")
        print(f"   支持平台: {', '.join(p.value for p in Platform)}")
        sys.exit(1)

    rev_type = ReviewType.COMPLAINT if args.complaint else ReviewType.REVIEW
    print(f"🕷️  开始爬取 [{platform.value}] {args.shop_name} (ID: {args.shop_id})")
    print(f"   最大页数: {args.max_pages} | 类型: {rev_type.value} | 无头: {not args.show}")

    crawler_kwargs = {}
    if platform == Platform.HUNGRY_PANDA:
        if args.shop_hint:
            crawler_kwargs["shop_hint"] = args.shop_hint
        if args.login_url:
            crawler_kwargs["login_url"] = args.login_url

    crawler = get_crawler(
        platform,
        headless=not args.show,
        proxy=args.proxy or None,
        strategy=getattr(args, "strategy", "hybrid"),
        **crawler_kwargs,
    )

    def on_progress(fetched: int, total: int):
        print(f"\r  已爬取 {fetched} 条...", end="", flush=True)

    reviews = await crawler.crawl(
        shop_id=args.shop_id,
        shop_name=args.shop_name,
        max_pages=args.max_pages,
        review_type=rev_type,
        progress_callback=on_progress,
    )
    print(f"\n✅ 爬取完成，共 {len(reviews)} 条")

    if not reviews:
        print("⚠️  未获取到任何评论，请检查商家ID或平台是否可访问")
        return

    if not args.no_analyze:
        print("🤖 开始 AI 分析...")

        def on_analyze(cur, total):
            bar_width = 40
            filled = int(bar_width * cur / total)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"\r  [{bar}] {cur}/{total}", end="", flush=True)

        processed = await process_and_save(reviews, progress_callback=on_analyze)
        print(f"\n✅ AI 分析完成！{len(processed)} 条评论已入库")
    else:
        from core.database import insert_review
        for r in reviews:
            insert_review(r)
        print(f"✅ {len(reviews)} 条评论已存入数据库（跳过 AI 分析）")


async def cmd_crawl_overseas(args: argparse.Namespace) -> None:
    """批量采集海外喜茶多门店评论"""
    try:
        platforms = tuple(Platform(name) for name in args.platforms) if args.platforms else ()
    except ValueError:
        print(f"❌ 存在不支持的平台: {args.platforms}")
        print(f"   支持平台: {', '.join(p.value for p in Platform)}")
        return
    rules = ReviewFilter(
        since_days=args.since_days,
        min_rating=args.min_rating,
        max_rating=args.max_rating,
        include_keywords=parse_keywords(args.include),
        exclude_keywords=parse_keywords(args.exclude),
        foreign_only=args.foreign_only,
        dedupe=not args.no_dedupe,
    )
    print("🌍 开始批量采集海外喜茶评论")
    if args.region:
        print(f"   地区: {args.region}")
    if args.shop_keyword:
        print(f"   门店关键词: {args.shop_keyword}")
    if args.platforms:
        print(f"   平台: {', '.join(args.platforms)}")
    summary = await crawl_overseas_reviews(
        region=args.region,
        shop_keywords=parse_keywords(args.shop_keyword),
        store_codes=tuple(args.store_codes or ()),
        platforms=platforms,
        max_shops=args.max_shops,
        max_pages=args.max_pages,
        show_browser=args.show,
        proxy=args.proxy or None,
        strategy=args.strategy,
        filters=rules,
        no_analyze=args.no_analyze,
        export_format=args.export_format,
    )
    print(f"\n✅ 批量任务完成，共 {len(summary.targets)} 个目标")
    print(f"   原始评论: {summary.fetched_total} | 筛选后: {summary.kept_total} | 入库: {summary.saved_total}")
    if summary.export_path:
        print(f"   导出文件: {summary.export_path}")
    for item in summary.targets:
        extra = f" | 错误: {item.error}" if item.error else ""
        print(
            f"   [{item.status.upper():6}] {item.target.region} | "
            f"{item.target.shop_name} | {item.target.platform.value} | "
            f"{item.fetched_count}->{item.kept_count}->{item.saved_count}{extra}"
        )


def cmd_export_manifests(args: argparse.Namespace) -> None:
    manifests = load_platform_manifests(
        region=args.region,
        shop_keywords=parse_keywords(args.shop_keyword),
        store_codes=tuple(args.store_codes or ()),
        platform_names=args.platforms or (),
    )
    if not manifests:
        print("⚠️  未找到匹配的平台清单")
        return
    import json
    from pathlib import Path

    output = Path(args.output) if args.output else Path("exports") / "platform_manifests.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = [manifest.__dict__ for manifest in manifests]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已导出 {len(manifests)} 条平台清单到: {output}")


def cmd_list(args: argparse.Namespace) -> None:
    """列出评论"""
    platform = Platform(args.platform) if args.platform else None
    sentiment = SentimentLabel(args.sentiment) if args.sentiment else None
    reviews = get_reviews(platform=platform, sentiment=sentiment, limit=args.limit)
    print(f"\n📝 共找到 {len(reviews)} 条评论：\n")
    for r in reviews:
        sentiment_icon = {"正面": "😊", "负面": "😞", "中性": "😐"}.get(
            r.sentiment.value if r.sentiment else "", "❓"
        )
        print(f"[{r.platform.value}] {r.shop_name} | {r.reviewer_name} | ⭐{r.rating}")
        print(f"  {sentiment_icon} {r.content[:100]}{'...' if len(r.content) > 100 else ''}")
        if r.keywords:
            print(f"  🏷️  {' | '.join(r.keywords)}")
        print()


def cmd_export(args: argparse.Namespace) -> None:
    """导出数据"""
    reviews = get_reviews(limit=100000)
    if not reviews:
        print("⚠️  数据库为空，请先爬取数据")
        return

    fmt = args.format.lower()
    if fmt == "csv":
        path = export_csv(reviews)
    elif fmt == "excel":
        path = export_excel(reviews)
    elif fmt == "json":
        path = export_json(reviews)
    else:
        print(f"❌ 不支持的格式: {fmt}，请使用 csv / excel / json")
        return

    print(f"✅ 已导出 {len(reviews)} 条评论到: {path}")


def cmd_stats(args: argparse.Namespace) -> None:
    """统计概览"""
    stats = get_sentiment_stats()
    keywords = get_top_keywords(10)

    print("\n📊 评论统计概览")
    print("=" * 60)
    if not stats:
        print("  暂无数据")
    else:
        for s in stats:
            print(f"\n  平台: {s['platform']}")
            print(f"    总数: {s['total']} | 平均评分: {s.get('avg_rating', 0):.2f}")
            print(f"    😊 正面: {s['positive']} | 😞 负面: {s['negative']} | 😐 中性: {s['neutral']}")

    print("\n🏷️  高频关键词 Top 10:")
    for word, count in keywords:
        bar = "█" * min(count, 20)
        print(f"  {word:<10} {bar} ({count})")


# ──────────────────────── CLI 入口 ────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="外卖评论爬虫系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # crawl
    crawl_p = sub.add_parser("crawl", help="爬取评论")
    crawl_p.add_argument("--platform", "-p", required=True,
                         help="平台名称: 美团外卖 / 饿了么 / 抖音外卖 / 大众点评 / Google Maps / KeeTa / OpenRice / Hungry Panda")
    crawl_p.add_argument("--shop-id", "-i", required=True, help="商家ID或URL")
    crawl_p.add_argument("--shop-name", "-n", required=True, help="商家名称")
    crawl_p.add_argument("--max-pages", "-m", type=int, default=10, help="最大爬取页数")
    crawl_p.add_argument("--complaint", action="store_true", help="爬取客诉（默认爬用户评论）")
    crawl_p.add_argument("--show", action="store_true", help="显示浏览器窗口（调试用）")
    crawl_p.add_argument("--proxy", help="代理地址，如 http://127.0.0.1:7890")
    crawl_p.add_argument("--no-analyze", action="store_true", help="跳过 AI 分析")
    crawl_p.add_argument("--login-url", help="商家后台登录链接（Hungry Panda 等后台型平台使用）")
    crawl_p.add_argument("--shop-hint", help="后台分店名称/关键词提示（用于进入正确分店）")
    crawl_p.add_argument(
        "--strategy", "-s",
        choices=["hybrid", "api_intercept", "dom_parse", "ocr_screenshot"],
        default="hybrid",
        help="爬取策略（默认 hybrid 自动降级）",
    )

    overseas_p = sub.add_parser("crawl-overseas", help="批量采集海外喜茶评论")
    overseas_p.add_argument("--region", help="地区筛选，如 香港 / 美国 / 英国")
    overseas_p.add_argument("--shop-keyword", help="门店名称关键字，支持逗号分隔多个")
    overseas_p.add_argument("--store-code", dest="store_codes", action="append", help="按 JDE / 经营单位代码筛选，可重复传入")
    overseas_p.add_argument("--platform", dest="platforms", action="append", help="平台名称，可重复传入，如 Google Maps")
    overseas_p.add_argument("--max-shops", type=int, help="最多处理多少个目标店铺")
    overseas_p.add_argument("--max-pages", "-m", type=int, default=5, help="每个目标最多爬取页数")
    overseas_p.add_argument("--show", action="store_true", help="显示浏览器窗口（调试用）")
    overseas_p.add_argument("--proxy", help="代理地址，如 http://127.0.0.1:7890")
    overseas_p.add_argument("--no-analyze", action="store_true", help="跳过 AI 翻译/情感/关键词处理")
    overseas_p.add_argument(
        "--strategy", "-s",
        choices=["hybrid", "api_intercept", "dom_parse", "ocr_screenshot"],
        default="hybrid",
        help="爬取策略（默认 hybrid 自动降级）",
    )
    overseas_p.add_argument("--since-days", type=int, help="仅保留最近 N 天评论")
    overseas_p.add_argument("--min-rating", type=float, help="最低评分")
    overseas_p.add_argument("--max-rating", type=float, help="最高评分")
    overseas_p.add_argument("--include", help="仅保留包含这些关键词的评论，逗号分隔")
    overseas_p.add_argument("--exclude", help="排除包含这些关键词的评论，逗号分隔")
    overseas_p.add_argument("--foreign-only", action="store_true", help="仅保留需要翻译的外文评论")
    overseas_p.add_argument("--no-dedupe", action="store_true", help="关闭去重")
    overseas_p.add_argument("--export-format", choices=["excel", "csv", "json"], help="导出本次批量结果")

    manifest_p = sub.add_parser("export-manifests", help="导出无 Python 爬虫平台的门店清单")
    manifest_p.add_argument("--region", help="地区筛选，如 香港 / 美国 / 英国")
    manifest_p.add_argument("--shop-keyword", help="门店名称关键字，支持逗号分隔多个")
    manifest_p.add_argument("--store-code", dest="store_codes", action="append", help="按 JDE / 经营单位代码筛选，可重复传入")
    manifest_p.add_argument("--platform", dest="platforms", action="append", help="平台名称，可重复传入，如 Hungry Panda")
    manifest_p.add_argument("--output", help="输出 JSON 文件路径")

    # list
    list_p = sub.add_parser("list", help="列出评论")
    list_p.add_argument("--platform", "-p", help="按平台筛选")
    list_p.add_argument("--sentiment", "-s", help="按情感筛选: 正面 / 负面 / 中性")
    list_p.add_argument("--limit", "-l", type=int, default=20, help="显示条数")

    # export
    export_p = sub.add_parser("export", help="导出数据")
    export_p.add_argument("--format", "-f", default="excel",
                          help="导出格式: csv / excel / json（默认 excel）")

    # stats
    sub.add_parser("stats", help="统计概览")

    # gui - 启动 Web 界面
    sub.add_parser("gui", help="启动 Web GUI 界面（http://localhost:8080）")

    return parser


def main() -> None:
    init_db()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "crawl":
        asyncio.run(cmd_crawl(args))
    elif args.command == "crawl-overseas":
        asyncio.run(cmd_crawl_overseas(args))
    elif args.command == "export-manifests":
        cmd_export_manifests(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "gui":
        import subprocess
        subprocess.run([sys.executable, "main.py"], check=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
