from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CREDENTIALS_FILE = DATA / "grabfood_credentials.local.json"
EXPORTS = ROOT / "exports" / "grabfood"
LOGIN_URL = "https://merchant.grab.com/en-my"
PORTAL_URL = "https://merchant.grab.com/portal?source=mrc"


@dataclass(frozen=True)
class AccountConfig:
    key: str
    country_code: str
    country: str
    account_label: str
    profile_name: str
    market_label: str
    store_scope_label: str = "All stores"
    service_label: str = "GrabFood"
    type_label: str = "Delivery and pickup"

    @property
    def profile_dir(self) -> Path:
        return DATA / "browser_profiles" / self.profile_name

    @property
    def export_dir(self) -> Path:
        return EXPORTS / self.country_code / self.key


ACCOUNTS = {
    "my_auro": AccountConfig(
        key="my_auro",
        country_code="my",
        country="Malaysia",
        account_label="Malaysia Owner A",
        profile_name="grabfood_my_auro",
        market_label="Klang Valley",
    ),
    "my_puresips": AccountConfig(
        key="my_puresips",
        country_code="my",
        country="Malaysia",
        account_label="Malaysia Owner B",
        profile_name="grabfood_my_puresips",
        market_label="Klang Valley",
    ),
    "sg": AccountConfig(
        key="sg",
        country_code="sg",
        country="Singapore",
        account_label="Singapore Owner",
        profile_name="grabfood_sg",
        market_label="Singapore",
    ),
}


FIELDS = [
    "Platform",
    "Country",
    "Country Code",
    "Account",
    "Market",
    "Store",
    "Rating",
    "Review",
    "Customer",
    "Customer ID",
    "Type",
    "Review Date",
    "Review Time",
    "Image URLs",
    "Ordered Items",
    "Reply Drawer Text",
    "Source",
    "Raw JSON",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GrabFood merchant weekly review collector")
    parser.add_argument("--account", default="my_auro", choices=sorted(ACCOUNTS), help="Grab merchant account")
    parser.add_argument("--days", type=int, default=7, help="Only keep reviews in the last N days")
    parser.add_argument("--max-reviews", type=int, default=100, help="Maximum reviews to export")
    parser.add_argument("--limit-stores", type=int, default=0, help="Limit stores for smoke runs; 0 means all")
    parser.add_argument("--all-stores-only", action="store_true", help="Collect the All stores summary page only")
    parser.add_argument("--store-name", default="", help="Only crawl stores whose name contains this text")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--manual-login", action="store_true", help="Wait for manual login if captcha/OTP appears")
    parser.add_argument("--username", default="", help="Login username")
    parser.add_argument("--password", default="", help="Login password")
    parser.add_argument("--output-prefix", default="", help="Optional export filename prefix")
    return parser.parse_args()


def load_credentials(args: argparse.Namespace, config: AccountConfig) -> tuple[str, str]:
    if args.username and args.password:
        return args.username, args.password

    env_prefix = f"GRABFOOD_{config.key.upper()}"
    username = os.getenv(f"{env_prefix}_USERNAME") or os.getenv("GRABFOOD_USERNAME") or ""
    password = os.getenv(f"{env_prefix}_PASSWORD") or os.getenv("GRABFOOD_PASSWORD") or ""
    if username and password:
        return username, password

    if CREDENTIALS_FILE.exists():
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        account_data = data.get(config.key) or {}
        username = account_data.get("username") or data.get("username") or ""
        password = account_data.get("password") or data.get("password") or ""
    return username, password


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_grab_date(value: str) -> datetime | None:
    raw = clean_text(value)
    raw = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw, flags=re.I)
    raw = raw.replace("/", " ")
    raw = re.sub(r"\s+", " ", raw)
    candidates = [
        raw,
        raw.replace("\n", " "),
        raw[:17],
        raw[:11],
    ]
    formats = (
        "%d %b %Y %H:%M",
        "%d %B %Y %H:%M",
        "%d %b %Y",
        "%d %B %Y",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    )
    for candidate in candidates:
        for fmt in formats:
            try:
                return datetime.strptime(candidate.strip(), fmt)
            except ValueError:
                pass
    return None


def contains_review_shape(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    keys = {str(key).lower() for key in data}
    has_rating = any("rating" in key or "star" in key for key in keys)
    has_review = any(key in keys or "review" in key or "comment" in key for key in ("review", "comment", "content", "message"))
    has_store = any("store" in key or "merchant" in key for key in keys)
    return has_rating and (has_review or has_store)


def walk_review_objects(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(data, dict):
        if contains_review_shape(data):
            found.append(data)
        for value in data.values():
            found.extend(walk_review_objects(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(walk_review_objects(item))
    return found


def deep_get(data: dict[str, Any], names: tuple[str, ...]) -> Any:
    lowered = {str(key).lower(): value for key, value in data.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    for value in data.values():
        if isinstance(value, dict):
            nested = deep_get(value, names)
            if nested not in (None, ""):
                return nested
    return ""


def collect_image_urls(value: Any) -> list[str]:
    urls: list[str] = []

    def add(raw: Any) -> None:
        text = str(raw or "").strip()
        if not text or text.startswith("data:") or text.startswith("blob:"):
            return
        if not re.match(r"https?://", text, flags=re.I):
            return
        if not re.search(r"\.(?:jpe?g|png|webp|gif)(?:[?#].*)?$", text, flags=re.I):
            return
        if text not in urls:
            urls.append(text)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, item in node.items():
                if any(token in str(key).lower() for token in ("image", "photo", "picture", "media", "url")):
                    if isinstance(item, str):
                        add(item)
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            for match in re.finditer(r"https?://[^\s\"'<>]+", node):
                add(match.group(0))

    walk(value)
    return urls


def network_review_to_row(record: dict[str, Any], config: AccountConfig, since_date: datetime.date) -> dict[str, Any] | None:
    rating = deep_get(record, ("rating", "star", "score"))
    review = deep_get(record, ("review", "reviewText", "comment", "content", "message"))
    customer = deep_get(record, ("customerName", "customer", "userName", "name"))
    customer_id = deep_get(record, ("customerId", "consumerId", "userId", "id"))
    store = deep_get(record, ("storeName", "merchantName", "restaurantName", "store"))
    review_type = deep_get(record, ("type", "reviewType", "visibility"))
    date_value = deep_get(record, ("date", "createdAt", "submittedAt", "reviewDate", "orderDate"))
    parsed = parse_grab_date(str(date_value))
    if parsed and parsed.date() < since_date:
        return None
    if not any((review, customer, store, rating)):
        return None
    return {
        "Platform": "GrabFood",
        "Country": config.country,
        "Country Code": config.country_code.upper(),
        "Account": config.account_label,
        "Market": config.market_label,
        "Store": clean_text(store),
        "Rating": clean_text(rating),
        "Review": clean_text(review),
        "Customer": clean_text(customer),
        "Customer ID": clean_text(customer_id),
        "Type": clean_text(review_type),
        "Review Date": parsed.date().isoformat() if parsed else clean_text(date_value),
        "Review Time": parsed.strftime("%H:%M") if parsed else "",
        "Image URLs": "|".join(collect_image_urls(record)),
        "Ordered Items": clean_text(deep_get(record, ("orderedItems", "ordered", "items", "orderItems"))),
        "Reply Drawer Text": "",
        "Source": "network",
        "Raw JSON": json.dumps(record, ensure_ascii=False),
    }


async def click_first_text(page, labels: tuple[str, ...], exact: bool = True, timeout: int = 1_000) -> str:
    for label in labels:
        try:
            locator = page.get_by_text(label, exact=exact).first
            if await locator.count() > 0 and await locator.is_visible(timeout=timeout):
                await locator.click(force=True)
                await page.wait_for_timeout(700)
                return label
        except Exception:
            pass
    return ""


async def click_first_selector(page, selectors: tuple[str, ...], timeout: int = 1_000) -> str:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=timeout):
                await locator.click(force=True)
                await page.wait_for_timeout(700)
                return selector
        except Exception:
            pass
    return ""


async def fill_first_visible(page, selectors: tuple[str, ...], value: str, timeout: int = 1_000) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=timeout):
                await locator.fill(value)
                return True
        except Exception:
            pass
    return False


async def accept_cookie_banner(page) -> None:
    await click_first_text(page, ("Accept All Cookies", "Allow All"), exact=True, timeout=1_500)


async def ensure_logged_in(page, config: AccountConfig, username: str, password: str, manual_login: bool):
    await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)
    await page.wait_for_timeout(2_000)
    await accept_cookie_banner(page)

    try:
        async with page.context.expect_page(timeout=5_000) as popup_info:
            await page.get_by_text("Go to Portal", exact=True).click(force=True)
        page = await popup_info.value
        await page.wait_for_load_state("domcontentloaded", timeout=60_000)
    except Exception:
        clicked = await click_first_text(page, ("Go to portal", "Go to Portal"), exact=False, timeout=2_000)
        if clicked:
            await page.wait_for_timeout(3_000)
        if "portal" not in page.url and "weblogin.grab.com" not in page.url:
            await page.goto(PORTAL_URL, wait_until="domcontentloaded", timeout=60_000)

    await page.wait_for_timeout(4_000)
    await accept_cookie_banner(page)

    if "saved-accounts" in page.url or await page.get_by_text("Welcome back", exact=False).count() > 0:
        await click_first_selector(
            page,
            (
                "button:has-text('Continue')",
                "button[type='button']",
            ),
            timeout=3_000,
        )
        await page.wait_for_timeout(5_000)

    if await page.get_by_text("Feedback", exact=True).count() > 0:
        return page

    if username and password:
        if await page.locator("input[type='password'], input[autocomplete='current-password']").count() == 0:
            await click_first_text(page, ("Username",), exact=True, timeout=1_000)
            await fill_first_visible(
                page,
                (
                    "#Username",
                    "input[placeholder='Enter your username']",
                    "input[name='username']",
                    "input[name='email']",
                    "input[type='email']",
                    "input[type='text']",
                    "input[autocomplete='username']",
                ),
                username,
                timeout=2_000,
            )
            await click_first_selector(
                page,
                (
                    "button[type='submit']",
                    "button:has-text('Continue')",
                    "button:has-text('Next')",
                ),
                timeout=2_000,
            )
            await page.wait_for_timeout(6_000)
        if "challenge/password" in page.url or await page.get_by_text("Enter password", exact=False).count() > 0:
            await fill_first_visible(
                page,
                (
                    "#password",
                    "input[placeholder='Password']",
                    "input[name='password']",
                    "input[type='password']",
                ),
                password,
                timeout=3_000,
            )
            await click_first_selector(
                page,
                (
                    "button:has-text('Continue')",
                    "button[type='submit']",
                ),
                timeout=3_000,
            )
            await page.wait_for_timeout(12_000)
        elif await page.locator("input[type='password'], input[autocomplete='current-password']").count() > 0:
            await fill_first_visible(
                page,
                (
                    "#password",
                    "input[placeholder='Password']",
                    "input[name='password']",
                    "input[type='password']",
                    "input[autocomplete='current-password']",
                ),
                password,
                timeout=3_000,
            )
            await click_first_selector(
                page,
                (
                    "button:has-text('Continue')",
                    "button[type='submit']",
                ),
                timeout=3_000,
            )
            await page.wait_for_timeout(12_000)

    if "weblogin.grab.com" not in page.url and "portal" not in page.url:
        try:
            await page.goto(PORTAL_URL, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(5_000)
        except Exception:
            pass

    if manual_login and await page.get_by_text("Feedback", exact=True).count() == 0:
        print("Manual login required. Complete login in the opened browser, then press Enter here.")
        await asyncio.to_thread(input)

    if await page.get_by_text("Feedback", exact=True).count() == 0:
        await page.wait_for_load_state("domcontentloaded", timeout=30_000)
    if "weblogin.grab.com" in page.url and not manual_login:
        raise RuntimeError("GrabFood login did not complete; saved account, captcha, or OTP may require manual login.")
    return page


async def open_feedback_page(page) -> None:
    clicked = await click_first_text(page, ("Feedback",), exact=True, timeout=5_000)
    if not clicked:
        await click_first_text(page, ("Feedback",), exact=False, timeout=5_000)
    await page.wait_for_timeout(3_000)
    await click_first_text(page, ("Ratings and reviews", "Ratings & reviews"), exact=False, timeout=2_000)
    await page.wait_for_timeout(2_000)


async def choose_dropdown_option(page, current_labels: tuple[str, ...], option_label: str) -> bool:
    if not option_label:
        return True
    for current_label in current_labels:
        try:
            locator = page.get_by_text(current_label, exact=False).first
            if await locator.count() > 0 and await locator.is_visible(timeout=1_000):
                await locator.click(force=True)
                await page.wait_for_timeout(700)
                option = page.get_by_text(option_label, exact=False).last
                if await option.count() > 0 and await option.is_visible(timeout=2_000):
                    await option.click(force=True)
                    await page.wait_for_timeout(2_000)
                    return True
        except Exception:
            pass
    return False


async def apply_base_filters(page, config: AccountConfig) -> None:
    await choose_dropdown_option(page, ("Klang Valley", "Singapore", "Region", "City"), config.market_label)
    await choose_dropdown_option(page, ("GrabFood", "Service"), config.service_label)
    await choose_dropdown_option(page, ("Delivery and pickup", "Type"), config.type_label)
    await click_first_text(page, ("Written reviews",), exact=False, timeout=1_500)
    await page.wait_for_timeout(2_000)


async def list_store_options(page, config: AccountConfig) -> list[str]:
    has_store_dropdown = False
    try:
        dropdown = page.locator(".dui-select").filter(has_text=config.store_scope_label).first
        if await dropdown.count() > 0 and await dropdown.is_visible(timeout=2_000):
            has_store_dropdown = True
            await dropdown.click(force=True)
            await page.wait_for_timeout(1_000)
    except Exception:
        pass
    if not has_store_dropdown:
        return []
    options: list[str] = []
    try:
        texts = await page.locator(
            ".dui-select-dropdown:not(.dui-select-dropdown-hidden) .dui-select-item-option:not(.dui-select-item-option-disabled)"
        ).evaluate_all("""nodes => nodes.map(node => (node.innerText || node.textContent || '').trim()).filter(Boolean)""")
        for text in texts:
            label = clean_text(text)
            if not label or label.upper() == "ALL" or label.lower() == config.store_scope_label.lower():
                continue
            if len(label) > 120 or "download" in label.lower():
                continue
            if label not in options:
                options.append(label)
    except Exception:
        pass
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    return options


async def select_store(page, store_name: str) -> bool:
    if not store_name:
        return True
    try:
        dropdown = page.locator(".dui-select").filter(has_text=re.compile(r"All stores|heytea", re.I)).last
        if await dropdown.count() > 0 and await dropdown.is_visible(timeout=2_000):
            await dropdown.click(force=True)
            await page.wait_for_timeout(700)
            option = page.locator(".dui-select-dropdown:not(.dui-select-dropdown-hidden) .dui-select-item-option").filter(
                has_text=store_name
            ).first
            if await option.count() > 0 and await option.is_visible(timeout=2_000):
                await option.click(force=True)
                await page.wait_for_timeout(2_000)
                return True
    except Exception:
        pass
    return await choose_dropdown_option(page, ("All stores", "Store", store_name), store_name)


async def collect_network_rows(page, config: AccountConfig, since_date: datetime.date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for payload in getattr(page, "_grab_json_payloads", []):
        for record in walk_review_objects(payload):
            row = network_review_to_row(record, config, since_date)
            if not row:
                continue
            key = "|".join([row.get("Store", ""), row.get("Customer ID", ""), row.get("Review", ""), row.get("Review Date", "")])
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


async def extract_node_image_urls(locator) -> list[str]:
    try:
        return await locator.evaluate(
            r"""
            (root) => {
              const urls = [];
              const add = (raw) => {
                const text = String(raw || '').trim();
                if (!text || text.startsWith('data:') || text.startsWith('blob:')) return;
                let url = text;
                try { url = new URL(text, window.location.href).href; } catch (_) {}
                if (!/^https?:\/\//i.test(url)) return;
                if (!/\.(jpe?g|png|webp|gif)([?#].*)?$/i.test(url)) return;
                if (!urls.includes(url)) urls.push(url);
              };
              root.querySelectorAll('img').forEach((img) => {
                add(img.currentSrc);
                add(img.getAttribute('src'));
                add(img.getAttribute('data-src'));
                add(img.getAttribute('data-original'));
                String(img.getAttribute('srcset') || '').split(',').forEach((part) => add(part.trim().split(/\s+/)[0]));
              });
              root.querySelectorAll('[style*="background"]').forEach((node) => {
                const style = node.getAttribute('style') || '';
                for (const match of style.matchAll(/url\((['"]?)(.*?)\1\)/g)) add(match[2]);
              });
              return urls;
            }
            """
        )
    except Exception:
        return []


async def extract_reply_drawer(page) -> tuple[str, str, str]:
    await page.wait_for_timeout(1_000)
    drawer_text = ""
    image_urls: list[str] = []
    found_drawer = False
    for selector in (
        "aside:has-text('REPLY TO CUSTOMER')",
        "[role='dialog']:has-text('REPLY TO CUSTOMER')",
        "div:has-text('REPLY TO CUSTOMER')",
    ):
        try:
            locator = page.locator(selector).last
            if await locator.count() > 0 and await locator.is_visible(timeout=1_000):
                drawer_text = clean_text(await locator.inner_text(timeout=2_000))
                image_urls = await extract_node_image_urls(locator)
                found_drawer = True
                break
        except Exception:
            pass
    if not found_drawer:
        return "", "", ""
    ordered = ""
    match = re.search(r"Ordered:\s*(.+?)(?:What would you like|Your reply|Submit|$)", drawer_text, flags=re.I)
    if match:
        ordered = clean_text(match.group(1))
    await click_first_selector(
        page,
        (
            "button[aria-label='Close']",
            "[aria-label='Close']",
            "button:has-text('×')",
            "svg:near(:text('REPLY TO CUSTOMER'))",
        ),
        timeout=700,
    )
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    return drawer_text, ordered, "|".join(image_urls)


async def scrape_dom_table(page, config: AccountConfig, since_date: datetime.date, max_reviews: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_locator = page.locator(".dui-table-tbody tr.dui-table-row, tbody tr")
    if await row_locator.count() == 0:
        row_locator = page.locator("[role='row']").filter(has_text=re.compile(r"Public|Private|Reply|[0-9]{2} [A-Z][a-z]{2}", re.I))
    count = await row_locator.count()
    for index in range(count):
        if len(rows) >= max_reviews:
            break
        row = row_locator.nth(index)
        try:
            text = clean_text(await row.inner_text(timeout=2_000))
        except Exception:
            continue
        if not text or text.lower() == "no data" or "Rating Review Customer Store Type Date" in text:
            continue
        date_match = re.search(r"(\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4}(?:\s+\d{1,2}:\d{2})?)", text)
        parsed = parse_grab_date(date_match.group(1) if date_match else text)
        if parsed and parsed.date() < since_date:
            continue

        raw_cells: list[str] = []
        cells: list[str] = []
        try:
            raw_cells = await row.locator("td").evaluate_all("nodes => nodes.map(n => n.innerText || n.textContent || '')")
            cells = [clean_text(cell) for cell in raw_cells]
        except Exception:
            pass
        rating = ""
        review = ""
        customer = ""
        customer_id = ""
        store = ""
        review_type = ""
        date_text = clean_text(date_match.group(1) if date_match else "")
        if len(cells) >= 6:
            rating = clean_text(re.search(r"\d+", cells[0]).group(0) if re.search(r"\d+", cells[0]) else cells[0])
            review = cells[1].replace("Reply", "").strip()
            customer_lines = [part.strip() for part in raw_cells[2].splitlines() if part.strip()] if len(raw_cells) > 2 else []
            customer = customer_lines[0] if customer_lines else cells[2]
            customer_id = customer_lines[1] if len(customer_lines) > 1 else ""
            store = cells[3]
            review_type = cells[4]
            date_text = cells[5] or date_text
        else:
            rating_match = re.search(r"\b([1-5])\s*★?", text)
            rating = rating_match.group(1) if rating_match else ""
            review = text
        if clean_text(review).lower() == "no data":
            continue

        drawer_text = ""
        ordered_items = ""
        image_urls = await extract_node_image_urls(row)
        try:
            reply = row.get_by_text("Reply", exact=True).first
            more = row.locator("button").last
            if await reply.count() > 0 and await reply.is_visible(timeout=500):
                await reply.click(force=True)
                drawer_text, ordered_items, drawer_image_urls = await extract_reply_drawer(page)
                image_urls = "|".join(url for url in [image_urls, drawer_image_urls] if url)
            elif await more.count() > 0 and await more.is_visible(timeout=500):
                await more.click(force=True)
                drawer_text, ordered_items, drawer_image_urls = await extract_reply_drawer(page)
                image_urls = "|".join(url for url in [image_urls, drawer_image_urls] if url)
        except Exception:
            pass

        parsed = parse_grab_date(date_text) or parsed
        rows.append(
            {
                "Platform": "GrabFood",
                "Country": config.country,
                "Country Code": config.country_code.upper(),
                "Account": config.account_label,
                "Market": config.market_label,
                "Store": store,
                "Rating": rating,
                "Review": clean_text(review),
                "Customer": customer,
                "Customer ID": customer_id,
                "Type": review_type,
                "Review Date": parsed.date().isoformat() if parsed else date_text,
                "Review Time": parsed.strftime("%H:%M") if parsed else "",
                "Image URLs": image_urls,
                "Ordered Items": ordered_items,
                "Reply Drawer Text": drawer_text,
                "Source": "dom",
                "Raw JSON": "",
            }
        )
    return rows


async def click_next_page(page) -> bool:
    selectors = (
        "button[aria-label='Next page']:not([disabled])",
        "button[aria-label='Next']:not([disabled])",
        "button:has-text('Next'):not([disabled])",
        "[data-testid*='next']:not([disabled])",
    )
    clicked = await click_first_selector(page, selectors, timeout=700)
    if clicked:
        await page.wait_for_timeout(2_000)
        return True
    return False


async def collect_current_store(page, config: AccountConfig, since_date: datetime.date, max_reviews: int) -> list[dict[str, Any]]:
    getattr(page, "_grab_json_payloads", []).clear()
    await page.wait_for_timeout(3_000)
    rows = await scrape_dom_table(page, config, since_date, max_reviews)
    if len(rows) < max_reviews:
        network_rows = await collect_network_rows(page, config, since_date)
        existing = {"|".join([row.get("Store", ""), row.get("Customer ID", ""), row.get("Review", ""), row.get("Review Date", "")]) for row in rows}
        for row in network_rows:
            key = "|".join([row.get("Store", ""), row.get("Customer ID", ""), row.get("Review", ""), row.get("Review Date", "")])
            if key not in existing:
                rows.append(row)
                existing.add(key)
            if len(rows) >= max_reviews:
                break
    return rows[:max_reviews]


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = "|".join([row.get("Account", ""), row.get("Store", ""), row.get("Customer ID", ""), row.get("Review", ""), row.get("Review Date", "")])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def export_results(prefix: str, config: AccountConfig, payload: dict[str, Any]) -> tuple[Path, Path]:
    config.export_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_prefix = f"{prefix}_" if prefix else ""
    json_path = config.export_dir / f"{name_prefix}grabfood_{config.key}_weekly_reviews_{stamp}.json"
    csv_path = config.export_dir / f"{name_prefix}grabfood_{config.key}_weekly_reviews_{stamp}.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in payload["reviews"]:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    return json_path, csv_path


async def collect_reviews(args: argparse.Namespace) -> tuple[AccountConfig, dict[str, Any]]:
    config = ACCOUNTS[args.account]
    username, password = load_credentials(args, config)
    since_date = datetime.now().date() - timedelta(days=args.days)
    reviews: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    stores: list[str] = []

    from playwright.async_api import async_playwright

    config.profile_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            str(config.profile_dir),
            channel="msedge",
            headless=args.headless,
            viewport={"width": 1920, "height": 1080},
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page._grab_json_payloads = []

        async def on_response(response) -> None:
            try:
                if response.status != 200:
                    return
                url = response.url.lower()
                if not any(token in url for token in ("review", "feedback", "rating")):
                    return
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type.lower():
                    return
                page._grab_json_payloads.append(json.loads(await response.text()))
            except Exception:
                pass

        context.on("response", on_response)
        page = await ensure_logged_in(page, config, username, password, args.manual_login)
        await open_feedback_page(page)
        await apply_base_filters(page, config)
        if args.all_stores_only:
            stores = [config.store_scope_label]
        else:
            stores = await list_store_options(page, config)
            if args.store_name:
                stores = [store for store in stores if args.store_name.lower() in store.lower()]
            if args.limit_stores:
                stores = stores[: args.limit_stores]
            if not stores:
                stores = [config.store_scope_label]

        for store in stores:
            if len(reviews) >= args.max_reviews:
                break
            try:
                if store != config.store_scope_label:
                    await select_store(page, store)
                remaining = args.max_reviews - len(reviews)
                page_rows = await collect_current_store(page, config, since_date, remaining)
                for row in page_rows:
                    if store != config.store_scope_label and not row.get("Store"):
                        row["Store"] = store
                    reviews.append(row)
                while len(reviews) < args.max_reviews and await click_next_page(page):
                    remaining = args.max_reviews - len(reviews)
                    reviews.extend(await collect_current_store(page, config, since_date, remaining))
            except Exception as exc:
                errors.append({"store": store, "error": str(exc)})

        await context.close()

    reviews = dedupe_rows(reviews)[: args.max_reviews]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "platform": "GrabFood",
        "country": config.country,
        "country_code": config.country_code,
        "account": config.account_label,
        "account_key": config.key,
        "login_url": LOGIN_URL,
        "since_date": since_date.isoformat(),
        "store_count": len(stores),
        "stores": stores,
        "review_count": len(reviews),
        "reviews": reviews,
        "errors": errors,
    }
    return config, payload


async def main() -> None:
    args = parse_args()
    config, payload = await collect_reviews(args)
    json_path, csv_path = export_results(args.output_prefix, config, payload)
    print(
        json.dumps(
            {
                "json": str(json_path),
                "csv": str(csv_path),
                "country": config.country,
                "account": config.account_label,
                "store_count": payload["store_count"],
                "review_count": payload["review_count"],
                "errors": payload["errors"][:5],
                "stores": payload["stores"][:10],
                "sample": payload["reviews"][:3],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
