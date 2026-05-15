from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
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
EXPORT_DIR = ROOT / "exports" / "uber_eats"
PROFILE_DIR = ROOT / "data" / "browser_profiles" / "uber_eats"
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
    parser = argparse.ArgumentParser(description="Uber Eats merchant review collector (read-only)")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Store registry path")
    parser.add_argument("--country", default="", help="Country filter")
    parser.add_argument("--store-filter", default="", help="Store/JDE filter")
    parser.add_argument("--max-stores", type=int, default=0, help="Max stores; 0 means all")
    parser.add_argument("--days", type=int, default=7, help="Recent N days")
    parser.add_argument("--max-reviews", type=int, default=120, help="Maximum reviews per run")
    parser.add_argument("--account", default="default", help="Account label")
    parser.add_argument("--username", default="", help="Login username/email")
    parser.add_argument("--password", default="", help="Login password")
    parser.add_argument("--manual-login", action="store_true", help="Allow manual login wait loop")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--browser-channel", default="msedge", help="Playwright browser channel")
    parser.add_argument("--output-prefix", default="uber_eats_weekly_reviews", help="Output prefix")
    return parser.parse_args()


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    username = args.username or os.getenv("UBER_EATS_USERNAME", "")
    password = args.password or os.getenv("UBER_EATS_PASSWORD", "")
    return str(username or ""), str(password or "")


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


def load_targets(args: argparse.Namespace) -> list[dict[str, str]]:
    from unified_collector.store_registry import resolve_stores

    selectors: str | list[str] = "all"
    if args.store_filter:
        selectors = [args.store_filter]
    stores = resolve_stores(
        platform="uber_eats",
        country=args.country,
        stores=selectors,
        registry_path=args.registry,
        require_url=True,
    )
    rows: list[dict[str, str]] = []
    for store in stores:
        rows.append(
            {
                "jde": store.jde,
                "store_name": store.store_name,
                "country": store.country or args.country,
                "url": store.url,
                "store_id": store.jde,
            }
        )
    if args.max_stores > 0:
        rows = rows[: args.max_stores]
    return rows


async def attempt_login(page, username: str, password: str) -> bool:
    if not username or not password:
        return False
    login_selectors = ("input[type='email']", "input[name='email']", "input#PHONE_NUMBER_or_EMAIL_ADDRESS")
    password_selectors = ("input[type='password']", "input[name='password']")
    email_input = None
    for selector in login_selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible(timeout=600):
                email_input = locator
                break
        except Exception:
            continue
    if not email_input:
        return False
    try:
        await email_input.fill(username)
    except Exception:
        return False
    for selector in ("button:has-text('Next')", "button:has-text('Continue')", "button[type='submit']"):
        try:
            locator = page.locator(selector).first
            if await locator.count():
                await locator.click()
                await page.wait_for_timeout(1200)
                break
        except Exception:
            continue
    password_input = None
    for selector in password_selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible(timeout=1200):
                password_input = locator
                break
        except Exception:
            continue
    if not password_input:
        return False
    try:
        await password_input.fill(password)
        submit = page.locator("button[type='submit'], button:has-text('Sign in'), button:has-text('登录')").first
        if await submit.count():
            await submit.click()
        await page.wait_for_timeout(3000)
        return True
    except Exception:
        return False


async def wait_manual_login(page, timeout_seconds: int = 180) -> bool:
    deadline = datetime.now().timestamp() + timeout_seconds
    while datetime.now().timestamp() < deadline:
        url = (page.url or "").lower()
        if "auth.uber.com" not in url and "login" not in url:
            return True
        await page.wait_for_timeout(2000)
    return False


async def parse_reviews_on_page(page, store: dict[str, str]) -> list[dict[str, Any]]:
    rows = await page.evaluate(
        """
        (store) => {
          const blocks = [...document.querySelectorAll('tr, article, [data-testid*="review"], [class*="review"]')];
          const reviewBlocks = blocks.filter(node => {
            const text = (node.innerText || '').trim();
            if (!text || text.length < 18) return false;
            return /(review|rating|customer|order|反馈|评价|评论|star)/i.test(text);
          }).slice(0, 240);

          const parseDate = (text) => {
            const m = String(text || '').match(/\\d{4}[./-]\\d{1,2}[./-]\\d{1,2}/);
            return m ? m[0].replace(/[./]/g, '-') : '';
          };
          const parseRating = (text) => {
            const t = String(text || '');
            const m = t.match(/(\\d(?:\\.\\d)?)\\s*\\/\\s*5/) || t.match(/(\\d(?:\\.\\d)?)\\s*star/i);
            return m ? m[1] : '';
          };
          const parseOrderId = (text) => {
            const m = String(text || '').match(/(?:order\\s*id|订单号|訂單號)[:：\\s#-]*([A-Za-z0-9-]{6,})/i);
            return m ? m[1] : '';
          };
          const parseName = (text) => {
            const lines = String(text || '').split(/\\n+/).map(x => x.trim()).filter(Boolean);
            return lines.find(line => /[A-Za-z\\u4e00-\\u9fff]/.test(line) && line.length <= 32) || '';
          };

          return reviewBlocks.map((node, idx) => {
            const text = (node.innerText || '').trim();
            const rowText = text.replace(/\\s+/g, ' ');
            const reviewDate = parseDate(rowText);
            const rating = parseRating(rowText);
            const orderId = parseOrderId(rowText);
            const reviewer = parseName(rowText);
            const content = rowText;
            const images = [...node.querySelectorAll('img')]
              .map(img => img.currentSrc || img.src || '')
              .filter(url => url && !url.startsWith('data:') && !/avatar|profile/i.test(url));
            const reviewId = `${store.store_id}-${idx + 1}-${reviewDate || 'na'}`;
            return {
              Platform: 'Uber Eats',
              Country: store.country || '',
              Store: store.store_name || '',
              'Store ID': store.store_id || '',
              'Store URL': store.url || location.href,
              'Review ID': reviewId,
              'Review time': reviewDate,
              Rating: rating,
              'Reviewer Name': reviewer || 'Anonymous',
              'Review contents': content,
              'Image URLs': [...new Set(images)].join('|'),
              'Order ID': orderId,
              'Order Detail': '',
              'Order Items JSON': '[]',
              'Raw Text': rowText,
            };
          });
        }
        """,
        store,
    )
    return [row for row in (rows or []) if clean_text(row.get("Review contents"))]


async def crawl_store(page, store: dict[str, str], args: argparse.Namespace, since: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    try:
        await page.goto(store["url"], wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(2500)
    except Exception as error:
        return [], [f"open store failed: {store['store_name']} -> {error}"]

    page_url = (page.url or "").lower()
    if "auth.uber.com" in page_url or "login" in page_url:
        username, password = resolve_credentials(args)
        logged = await attempt_login(page, username, password)
        if not logged and args.manual_login:
            logged = await wait_manual_login(page)
        if not logged:
            errors.append(f"login required: {store['store_name']} ({store['url']})")
            return [], errors
        await page.wait_for_timeout(2000)

    rows = await parse_reviews_on_page(page, store)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        review_date = parse_review_date(str(row.get("Review time") or ""))
        if review_date and review_date < since:
            continue
        filtered.append(row)
        if len(filtered) >= args.max_reviews:
            break
    return filtered, errors


def export_rows(rows: list[dict[str, Any]], stores: list[dict[str, str]], args: argparse.Namespace, errors: list[str]) -> tuple[Path, Path]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = EXPORT_DIR / f"{args.output_prefix}_{stamp}.json"
    csv_path = EXPORT_DIR / f"{args.output_prefix}_{stamp}.csv"
    payload = {
        "platform": "Uber Eats",
        "country": args.country,
        "account": args.account,
        "days": args.days,
        "store_count": len(stores),
        "review_count": len(rows),
        "errors": errors,
        "stores": stores,
        "reviews": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return json_path, csv_path


async def run(args: argparse.Namespace) -> tuple[Path, Path, int, list[str]]:
    from playwright.async_api import async_playwright

    stores = load_targets(args)
    print(f"[stores] {len(stores)}")
    since = datetime.now() - timedelta(days=max(1, args.days))
    if not stores:
        json_path, csv_path = export_rows([], [], args, ["no stores found in registry"])
        return json_path, csv_path, 0, ["no stores found in registry"]

    all_rows: list[dict[str, Any]] = []
    all_errors: list[str] = []
    async with async_playwright() as p:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        launch_options: dict[str, Any] = {
            "headless": args.headless,
            "viewport": {"width": 1440, "height": 900},
            "locale": "en-US",
        }
        if args.browser_channel:
            launch_options["channel"] = args.browser_channel
        context = await p.chromium.launch_persistent_context(str(PROFILE_DIR), **launch_options)
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            for store in stores:
                rows, errors = await crawl_store(page, store, args, since)
                all_rows.extend(rows)
                all_errors.extend(errors)
                print(f"[store] {store['store_name']} reviews={len(rows)} errors={len(errors)}")
                if len(all_rows) >= args.max_reviews:
                    break
        finally:
            await context.close()
    all_rows = all_rows[: args.max_reviews]
    json_path, csv_path = export_rows(all_rows, stores, args, all_errors)
    return json_path, csv_path, len(all_rows), all_errors


def main() -> None:
    args = parse_args()
    json_path, csv_path, count, errors = asyncio.run(run(args))
    print(f"[done] reviews={count}")
    print(f"[done] json={json_path}")
    print(f"[done] csv={csv_path}")
    if errors:
        print(json.dumps({"errors": errors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
