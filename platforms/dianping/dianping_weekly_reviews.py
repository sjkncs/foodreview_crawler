from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXPORT_DIR = ROOT / "exports" / "dianping"
PROFILE_DIR = ROOT / "data" / "browser_profiles" / "dianping_public"
DEFAULT_REGISTRY = ROOT / "data" / "store_registry.json"

FIELDS = [
    "Platform",
    "Country",
    "Store",
    "Store ID",
    "Store URL",
    "Review ID",
    "Review time",
    "Rating",
    "Reviewer Name",
    "Review contents",
    "Image URLs",
    "Order ID",
    "Order Detail",
    "Order Items JSON",
    "Raw Text",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dianping weekly review collector (read-only)")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Store registry JSON path")
    parser.add_argument("--country", default="", help="Country / region filter")
    parser.add_argument("--store-filter", default="", help="Store keyword or JDE filter")
    parser.add_argument("--max-stores", type=int, default=0, help="Max store count (0 means all)")
    parser.add_argument("--days", type=int, default=7, help="Collect reviews in recent N days")
    parser.add_argument("--max-reviews-per-store", type=int, default=120, help="Maximum reviews per store")
    parser.add_argument("--max-pages-per-store", type=int, default=6, help="Maximum pages per store")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--browser-channel", default="msedge", help="Playwright browser channel")
    parser.add_argument("--output-prefix", default="dianping_weekly_reviews", help="Output file prefix")
    return parser.parse_args()


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_review_date(value: str) -> datetime | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}", text)
    if not match:
        return None
    token = match.group(0).replace(".", "-").replace("/", "-")
    try:
        return datetime.strptime(token, "%Y-%m-%d")
    except ValueError:
        return None


def store_id_from_url(url: str) -> str:
    match = re.search(r"/shop/([^/?#]+)", url or "")
    return match.group(1) if match else ""


def normalized_review_url(url: str) -> str:
    if not url:
        return url
    if "/review_all" in url:
        return url
    return url.rstrip("/") + "/review_all"


def load_targets(args: argparse.Namespace) -> list[dict[str, str]]:
    from unified_collector.store_registry import resolve_stores

    selectors: str | list[str] = "all"
    if args.store_filter:
        selectors = [args.store_filter]
    stores = resolve_stores(
        platform="dianping",
        country=args.country,
        stores=selectors,
        registry_path=args.registry,
        require_url=True,
    )
    rows = []
    for store in stores:
        url = normalized_review_url(store.url)
        rows.append(
            {
                "jde": store.jde,
                "store_name": store.store_name,
                "country": store.country or args.country,
                "url": url,
                "store_id": store_id_from_url(url) or store.jde,
            }
        )
    if args.max_stores > 0:
        rows = rows[: args.max_stores]
    return rows


async def parse_rows_on_page(page, store: dict[str, str]) -> list[dict[str, Any]]:
    rows = await page.evaluate(
        """
        (store) => {
          const pickCards = () => {
            const candidates = [
              ...document.querySelectorAll('li.comment-item'),
              ...document.querySelectorAll('div.review-item'),
              ...document.querySelectorAll('[class*="comment-list"] li'),
            ];
            if (candidates.length) return candidates;
            return [...document.querySelectorAll('li, article, div')].filter(node => {
              const text = (node.innerText || '').trim();
              return text.length > 40 && /(评价|评论|口味|环境|服务)/.test(text);
            }).slice(0, 60);
          };

          const toText = (node, selectors) => {
            for (const sel of selectors) {
              const found = node.querySelector(sel);
              if (!found) continue;
              const value = (found.innerText || found.textContent || '').trim();
              if (value) return value;
            }
            return '';
          };

          const parseStar = (node) => {
            const starNode = node.querySelector('.star, [class*="star"], [class*="sml-rank-stars"]');
            if (!starNode) return '';
            const cls = `${starNode.className || ''} ${starNode.getAttribute('class') || ''}`;
            const m = cls.match(/star-?(\\d+)/i) || cls.match(/sml-rank-stars\\s+sml-str(\\d+)/i);
            if (m) {
              const v = Number(m[1] || 0);
              if (Number.isFinite(v) && v > 0) return v > 5 ? String(v / 10) : String(v);
            }
            const title = starNode.getAttribute('title') || starNode.getAttribute('aria-label') || '';
            const n = title.match(/(\\d(?:\\.\\d)?)/);
            return n ? n[1] : '';
          };

          const parseDate = (text) => {
            const m = String(text || '').match(/\\d{4}[./-]\\d{1,2}[./-]\\d{1,2}/);
            return m ? m[0].replace(/[./]/g, '-') : '';
          };

          const cards = pickCards();
          return cards.map((card, idx) => {
            const reviewer = toText(card, ['.name', '.user-name', '.username', '.user', '.reviewer-name']) || '匿名';
            let content = toText(card, ['.review-words', '.content', 'p.desc', '.J_brief_cont', '.desc.J-desc']);
            if (!content) {
              content = (card.innerText || '').split('\\n').map(x => x.trim()).filter(Boolean).slice(0, 6).join(' ');
            }
            const timeText = toText(card, ['.time', '.date', '.review-time', '.misc-info']) || '';
            const reviewTime = parseDate(timeText);
            const rating = parseStar(card);
            const imageUrls = [...card.querySelectorAll('img')]
              .map(img => img.currentSrc || img.src || '')
              .filter(url => url && !url.startsWith('data:') && !/avatar|profile/i.test(url));
            const reviewLink = card.querySelector('a[href*="review"]')?.href || '';
            const reviewId = (reviewLink.match(/review[_/-]?(\\d+)/i)?.[1]) || `${store.store_id}-${idx + 1}`;
            return {
              Platform: 'Dianping',
              Country: store.country || '',
              Store: store.store_name || '',
              'Store ID': store.store_id || '',
              'Store URL': store.url || location.href,
              'Review ID': reviewId,
              'Review time': reviewTime || timeText,
              Rating: rating,
              'Reviewer Name': reviewer,
              'Review contents': content,
              'Image URLs': [...new Set(imageUrls)].join('|'),
              'Order ID': '',
              'Order Detail': '',
              'Order Items JSON': '[]',
              'Raw Text': (card.innerText || '').trim(),
            };
          }).filter(row => row['Review contents']);
        }
        """,
        store,
    )
    return rows or []


async def next_page(page) -> bool:
    selectors = (
        "a.next",
        "a[data-page='next']",
        ".page a.next",
        ".Pages a.NextPage",
    )
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=800):
                before = page.url
                await locator.click(force=True)
                await page.wait_for_timeout(1800)
                return page.url != before or True
        except Exception:
            continue
    return False


async def crawl_store(page, store: dict[str, str], args: argparse.Namespace, since: datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        await page.goto(store["url"], wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(2800)
    except Exception as error:
        print(f"[warn] open store failed {store['store_name']}: {error}")
        return rows

    for page_no in range(max(1, args.max_pages_per_store)):
        batch = await parse_rows_on_page(page, store)
        added = 0
        stale = 0
        for row in batch:
            key = f"{row.get('Store ID')}|{row.get('Review ID')}|{row.get('Review time')}|{row.get('Review contents')}"
            if key in seen:
                continue
            seen.add(key)
            review_date = parse_review_date(str(row.get("Review time") or ""))
            if review_date and review_date < since:
                stale += 1
                continue
            rows.append(row)
            added += 1
            if len(rows) >= args.max_reviews_per_store:
                break
        print(f"[store] {store['store_name']} page={page_no + 1} added={added} stale={stale} total={len(rows)}")
        if len(rows) >= args.max_reviews_per_store:
            break
        if not await next_page(page):
            break
        await page.wait_for_timeout(1200)
    return rows[: args.max_reviews_per_store]


def export_rows(rows: list[dict[str, Any]], stores: list[dict[str, str]], args: argparse.Namespace) -> tuple[Path, Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = EXPORT_DIR / f"{args.output_prefix}_{stamp}.json"
    csv_path = EXPORT_DIR / f"{args.output_prefix}_{stamp}.csv"
    payload = {
        "platform": "Dianping",
        "country": args.country,
        "days": args.days,
        "store_count": len(stores),
        "review_count": len(rows),
        "stores": stores,
        "reviews": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return json_path, csv_path


async def run(args: argparse.Namespace) -> tuple[Path, Path, int]:
    from playwright.async_api import async_playwright

    stores = load_targets(args)
    print(f"[stores] {len(stores)}")
    if not stores:
        empty_json, empty_csv = export_rows([], [], args)
        return empty_json, empty_csv, 0
    since = datetime.now() - timedelta(days=max(1, args.days))

    async with async_playwright() as p:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        launch_options: dict[str, Any] = {
            "headless": args.headless,
            "viewport": {"width": 1440, "height": 900},
            "locale": "zh-CN",
        }
        if args.browser_channel:
            launch_options["channel"] = args.browser_channel
        context = await p.chromium.launch_persistent_context(str(PROFILE_DIR), **launch_options)
        page = context.pages[0] if context.pages else await context.new_page()
        all_rows: list[dict[str, Any]] = []
        try:
            for store in stores:
                all_rows.extend(await crawl_store(page, store, args, since))
        finally:
            await context.close()
    all_rows.sort(key=lambda row: str(row.get("Review time") or ""), reverse=True)
    json_path, csv_path = export_rows(all_rows, stores, args)
    return json_path, csv_path, len(all_rows)


def main() -> None:
    args = parse_args()
    json_path, csv_path, count = asyncio.run(run(args))
    print(f"[done] reviews={count}")
    print(f"[done] json={json_path}")
    print(f"[done] csv={csv_path}")


if __name__ == "__main__":
    main()
