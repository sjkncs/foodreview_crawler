from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PROFILE_DIR = DATA / "browser_profiles" / "openrice_public"
EXPORTS = ROOT / "exports" / "openrice"

CHAIN_URL = "https://www.openrice.com/zh/hongkong/restaurants?chainId=10006678&tabIndex=0"
BASE_URL = "https://www.openrice.com"

FIELDS = [
    "Platform",
    "Region",
    "Store",
    "Store URL",
    "Restaurant ID",
    "Address",
    "Area",
    "Review ID",
    "Review URL",
    "Position",
    "Reviewer",
    "Reviewer Level",
    "Review Date",
    "Views",
    "Title",
    "Content",
    "Rating",
    "Taste",
    "Environment",
    "Service",
    "Hygiene",
    "Value",
    "Recommended Items",
    "Meal Date",
    "Meal Type",
    "Wait Time",
    "Average Spend",
    "Dining Method",
    "Image URLs",
    "Raw Text",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenRice public HEYTEA HK review collector")
    parser.add_argument("--chain-url", default=CHAIN_URL, help="OpenRice chain listing URL")
    parser.add_argument("--max-shops", type=int, default=0, help="Limit shops; 0 means all")
    parser.add_argument("--shop-name", default="", help="Only crawl stores containing this text")
    parser.add_argument("--max-reviews-per-shop", type=int, default=30, help="Maximum reviews per store")
    parser.add_argument("--max-pages-per-shop", type=int, default=3, help="Maximum review pages per store")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--browser-channel", default="msedge", help="Playwright browser channel")
    parser.add_argument("--output-prefix", default="openrice_hk_reviews", help="Export filename prefix")
    return parser.parse_args()


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def restaurant_id_from_url(url: str) -> str:
    match = re.search(r"-r(\d+)(?:/|$)", url)
    return match.group(1) if match else ""


def review_id_from_url(url: str) -> str:
    match = re.search(r"-e(\d+)(?:[/?#]|$)", url)
    return match.group(1) if match else ""


def parse_date(value: str) -> datetime | None:
    match = re.search(r"\d{4}-\d{2}-\d{2}", value or "")
    if not match:
        return None
    try:
        return datetime.strptime(match.group(), "%Y-%m-%d")
    except ValueError:
        return None


async def close_cookie_banner(page) -> None:
    for selector in ("button:has-text('同意')", "text=同意", ".cookie-accept"):
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=500):
                await locator.click(force=True)
                await page.wait_for_timeout(300)
                return
        except Exception:
            pass


async def collect_shops(page, chain_url: str) -> list[dict[str, str]]:
    await page.goto(chain_url, wait_until="domcontentloaded", timeout=60_000)
    await page.wait_for_timeout(6000)
    await close_cookie_banner(page)

    shops = await page.evaluate(
        """
        () => [...document.querySelectorAll('.poi-list-cell-wrapper')].map((card, index) => {
          const name = (card.querySelector('.poi-name')?.innerText || '').trim();
          const overlay = card.querySelector('a.poi-list-cell-desktop-right-link-overlay');
          const photo = card.querySelector('a.rms-photo-list-photo-count');
          const href = overlay?.href || (photo?.href || '').replace(/\\/photos\\/all\\/?$/, '/');
          const text = (card.innerText || '').trim();
          const lines = text.split(/\\n+/).map(x => x.trim()).filter(Boolean);
          const address = lines.find(line => !line.startsWith('+') && !/^\\d/.test(line) && line !== name && !line.includes('|')) || '';
          const infoLine = lines.find(line => line.includes('|')) || '';
          const area = infoLine.split('|').map(x => x.trim()).find(x => x && !x.includes('$') && !x.includes('港式') && !x.includes('果汁') && !x.includes('台式')) || '';
          return { index, name, url: href, address, area, rawText: text };
        }).filter(x => x.name && x.url && x.name.includes('喜茶'));
        """
    )
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for shop in shops:
        url = str(shop["url"]).rstrip("/")
        if url in seen:
            continue
        seen.add(url)
        shop["url"] = url
        shop["restaurant_id"] = restaurant_id_from_url(url)
        unique.append(shop)
    return unique


async def expand_more(page) -> None:
    for _ in range(8):
        clicked = await page.evaluate(
            """
            () => {
              const items = [...document.querySelectorAll('.review-post-extract .more, span.more')];
              const target = items.find(e => e.offsetParent !== null);
              if (!target) return false;
              target.click();
              return true;
            }
            """
        )
        if not clicked:
            break
        await page.wait_for_timeout(350)


async def parse_reviews_on_page(page, shop: dict[str, str], position_offset: int) -> list[dict[str, Any]]:
    await expand_more(page)
    rows = await page.evaluate(
        """
        ({shop, positionOffset}) => [...document.querySelectorAll('article.review-post-desktop.poi-detail-review')].map((article, index) => {
          const pick = (sel) => (article.querySelector(sel)?.innerText || '').trim();
          const header = article.querySelector('.review-post-header');
          const reviewer = (header?.querySelector('.info-top span')?.innerText || '').trim();
          const info = [...(header?.querySelectorAll('.info-bottom .with-dot') || [])].map(e => (e.innerText || '').trim()).filter(Boolean);
          const level = info.find(x => x.includes('等級')) || '';
          const date = info.find(x => /\\d{4}-\\d{2}-\\d{2}/.test(x)) || '';
          const views = info.find(x => x.includes('瀏覽')) || '';
          const titleLink = article.querySelector('.review-post-info-wrapper a.wrapper-left, .review-post-title-box a.wrapper-left');
          const reviewUrl = titleLink ? new URL(titleLink.getAttribute('href'), location.origin).href : '';
          const title = (article.querySelector('.review-post-title')?.innerText || article.querySelector('.review-post-info-wrapper')?.innerText || '').trim().split('\\n')[0];
          let content = pick('.review-post-body') || pick('.review-post-extract');
          content = content.replace(/查看更多/g, '').trim();
          const images = [...article.querySelectorAll('.review-extract-attachments img, .review-body-attachment img')].map(img => img.currentSrc || img.src).filter(src => src && !src.startsWith('data:'));
          const scores = {};
          article.querySelectorAll('.pdsd-item').forEach(item => {
            const label = (item.querySelector('.pdsd-item-label')?.innerText || '').trim();
            const value = (item.querySelector('.pdsd-item-value')?.innerText || '').trim();
            if (label) scores[label] = value;
          });
          const infoRows = {};
          article.querySelectorAll('.review-post-info-row').forEach(row => {
            const parts = [...row.children].map(x => (x.innerText || '').trim()).filter(Boolean);
            if (parts.length >= 2) infoRows[parts[0]] = parts.slice(1).join(' ');
          });
          const raw = (article.innerText || '').trim();
          return {
            Platform: 'OpenRice',
            Region: 'HK',
            Store: shop.name || '',
            'Store URL': shop.url || '',
            'Restaurant ID': shop.restaurant_id || '',
            Address: shop.address || '',
            Area: shop.area || '',
            'Review ID': reviewUrl.match(/-e(\\d+)/)?.[1] || '',
            'Review URL': reviewUrl,
            Position: positionOffset + index + 1,
            Reviewer: reviewer,
            'Reviewer Level': level,
            'Review Date': date,
            Views: views,
            Title: title,
            Content: content.startsWith(title) ? content.slice(title.length).trim() : content,
            Rating: pick('.review-post-rating-title + .review-detail-scores-desktop') ? '' : '',
            Taste: scores['味道'] || '',
            Environment: scores['環境'] || '',
            Service: scores['服務'] || '',
            Hygiene: scores['衛生'] || '',
            Value: scores['抵食'] || '',
            'Recommended Items': infoRows['推介美食'] || '',
            'Meal Date': infoRows['用餐日期'] || '',
            'Meal Type': infoRows['用餐途徑'] || '',
            'Wait Time': infoRows['等候時間'] || '',
            'Average Spend': infoRows['人均消費'] || '',
            'Dining Method': infoRows['用餐途徑'] || '',
            'Image URLs': images.join('|'),
            'Raw Text': raw,
          };
        })
        """,
        {"shop": shop, "positionOffset": position_offset},
    )
    for row in rows:
        score_values = [row.get("Taste"), row.get("Environment"), row.get("Service"), row.get("Hygiene"), row.get("Value")]
        numeric = [float(v) for v in score_values if str(v).replace(".", "", 1).isdigit()]
        row["Rating"] = round(sum(numeric) / len(numeric), 2) if numeric else ""
    return rows


async def next_review_page(page) -> bool:
    for selector in (
        "a[rel='next']",
        "a:has-text('下一頁')",
        "button:has-text('下一頁')",
        ".pagination a:has-text('>')",
        "[class*='pagination'] a:has-text('>')",
    ):
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1000):
                before = page.url
                await locator.click(force=True)
                await page.wait_for_timeout(3000)
                return page.url != before or True
        except Exception:
            pass

    current = page.url
    parsed = urlparse(current)
    params = parse_qs(parsed.query)
    current_page = int(params.get("page", ["1"])[0] or "1")
    params["page"] = [str(current_page + 1)]
    next_url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
    await page.goto(next_url, wait_until="domcontentloaded", timeout=60_000)
    await page.wait_for_timeout(3000)
    has_reviews = await page.locator("article.review-post-desktop.poi-detail-review").count()
    return has_reviews > 0


async def crawl_shop(page, shop: dict[str, str], args: argparse.Namespace) -> list[dict[str, Any]]:
    review_url = shop["url"].rstrip("/") + "/reviews"
    await page.goto(review_url, wait_until="domcontentloaded", timeout=60_000)
    await page.wait_for_timeout(5000)
    await close_cookie_banner(page)

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page_no in range(args.max_pages_per_shop):
        await page.wait_for_timeout(1500)
        batch = await parse_reviews_on_page(page, shop, len(rows))
        added = 0
        for row in batch:
            key = row.get("Review ID") or f"{row.get('Store')}:{row.get('Reviewer')}:{row.get('Review Date')}:{row.get('Title')}"
            if key in seen:
                continue
            seen.add(str(key))
            rows.append(row)
            added += 1
            if len(rows) >= args.max_reviews_per_shop:
                break
        print(f"[shop] {shop['name']} page={page_no + 1} added={added} total={len(rows)}")
        if len(rows) >= args.max_reviews_per_shop:
            break
        if not await next_review_page(page):
            break

    rows.sort(key=lambda row: parse_date(str(row.get("Review Date") or "")) or datetime.min, reverse=True)
    return rows[: args.max_reviews_per_shop]


def export_rows(rows: list[dict[str, Any]], shops: list[dict[str, str]], args: argparse.Namespace) -> tuple[Path, Path]:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = EXPORTS / f"{args.output_prefix}_{stamp}.json"
    csv_path = EXPORTS / f"{args.output_prefix}_{stamp}.csv"
    payload = {
        "platform": "OpenRice",
        "region": "HK",
        "chain_url": args.chain_url,
        "shop_count": len(shops),
        "review_count": len(rows),
        "shops": shops,
        "reviews": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return json_path, csv_path


async def run(args: argparse.Namespace) -> tuple[Path, Path, int]:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        launch_options: dict[str, Any] = {
            "headless": args.headless,
            "viewport": {"width": 1280, "height": 900},
            "locale": "zh-HK",
        }
        if args.browser_channel:
            launch_options["channel"] = args.browser_channel
        context = await p.chromium.launch_persistent_context(str(PROFILE_DIR), **launch_options)
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            shops = await collect_shops(page, args.chain_url)
            if args.shop_name:
                shops = [shop for shop in shops if args.shop_name.lower() in shop["name"].lower()]
            if args.max_shops:
                shops = shops[: args.max_shops]
            print(f"[shops] {len(shops)}")
            for shop in shops:
                print(f"[shops] {shop['name']} {shop['url']}")

            all_rows: list[dict[str, Any]] = []
            for shop in shops:
                all_rows.extend(await crawl_shop(page, shop, args))
            all_rows.sort(key=lambda row: parse_date(str(row.get("Review Date") or "")) or datetime.min, reverse=True)
            json_path, csv_path = export_rows(all_rows, shops, args)
            return json_path, csv_path, len(all_rows)
        finally:
            await context.close()


def main() -> None:
    args = parse_args()
    json_path, csv_path, count = asyncio.run(run(args))
    print(f"[done] reviews={count}")
    print(f"[done] json={json_path}")
    print(f"[done] csv={csv_path}")


if __name__ == "__main__":
    main()
