from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import datetime, timezone, timedelta
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
CREDENTIALS_FILE = DATA / "keeta_credentials.local.json"
PROFILE_DIR = DATA / "browser_profiles" / "keeta_weekly"
FALLBACK_PROFILE_DIR = DATA / "browser_profiles" / "keeta_weekly_fallback"
EXPORTS = ROOT / "exports" / "keeta"

LOGIN_URL = "https://merchant.mykeeta.com/pc/login"
INDEX_URL = "https://merchant.mykeeta.com/m/web/order?locale=zh&cityId=810001#/index"
EVALUATE_URL = "https://merchant.mykeeta.com/m/web/app/shop#/evaluate"
COMMENT_API_TOKEN = "/api/order/getMerchantComments"
SHOP_LIST_API_TOKEN = "/api/account/query/getShopListByAccount"
ORDER_DETAIL_API_TOKEN = "/api/order/getOrderDtl"
ORDER_DETAIL_PAGE = "https://merchant.mykeeta.com/web/mach/b_pc_order_history_list?evaluateOrderViewId={order_id}&evaluateShopId={shop_id}"

HK_TZ = timezone(timedelta(hours=8))

DEFAULT_SHOPS = [
    {"id": "721536352", "name": "heytea喜茶(無限極廣場店)"},
    {"id": "584148", "name": "heytea喜茶 (K11 MUSEA店)"},
    {"id": "473019", "name": "heytea喜茶 (屯門V City店)"},
    {"id": "574293", "name": "heytea喜茶 (旺角豉油街店)"},
    {"id": "466486", "name": "heytea喜茶 (荃灣荃新天地店)"},
    {"id": "479626", "name": "heytea喜茶 (銅鑼灣駱克道店)"},
    {"id": "597251", "name": "heytea喜茶 (MOKO新世紀廣場店)"},
    {"id": "590537", "name": "heytea喜茶 (沙田連城廣場店)"},
    {"id": "491602", "name": "heytea喜茶 (旺角新之城店)"},
    {"id": "458197", "name": "heytea喜茶 (銅鑼灣時代廣場店)"},
    {"id": "487762", "name": "heytea喜茶 (K11 Art Mall店)"},
]

FIELDS = [
    "Platform",
    "Region",
    "Store ID",
    "Store",
    "Review ID",
    "Reviewer Name",
    "Rating",
    "Delivery Rating",
    "Review Content",
    "Review Labels",
    "Shop Labels",
    "Review Time",
    "Review Timestamp",
    "Order View ID",
    "Image URLs",
    "Order Items JSON",
    "Order Items Text",
    "Expanded Order Detail",
    "Order Detail JSON",
    "Raw Review JSON",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KeeTa HK weekly review collector")
    parser.add_argument("--start-date", default="2026-05-01", help="Inclusive HK date, YYYY-MM-DD")
    parser.add_argument("--end-date", default="2026-05-07", help="Inclusive HK date, YYYY-MM-DD")
    parser.add_argument("--max-reviews", type=int, default=100, help="Maximum reviews to export")
    parser.add_argument("--max-pages", type=int, default=12, help="Maximum UI pages to capture")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--profile-dir", default="", help="Override browser user data dir")
    parser.add_argument("--browser-channel", default="msedge", help="Playwright browser channel; empty uses bundled Chromium")
    parser.add_argument("--username", default="", help="KeeTa login email")
    parser.add_argument("--password", default="", help="KeeTa password")
    parser.add_argument("--output-prefix", default="", help="Optional export filename prefix")
    parser.add_argument("--no-login", action="store_true", help="Do not attempt login; require existing session")
    return parser.parse_args()


def load_credentials(args: argparse.Namespace) -> tuple[str, str]:
    if args.username and args.password:
        return args.username, args.password
    username = os.getenv("KEETA_USERNAME", "")
    password = os.getenv("KEETA_PASSWORD", "")
    if username and password:
        return username, password
    if CREDENTIALS_FILE.exists():
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        return data.get("username", ""), data.get("password", "")
    return "", ""


def hk_day_ms(date_text: str, end: bool = False) -> int:
    dt = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=HK_TZ)
    if end:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)
    return int(dt.timestamp() * 1000)


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def find_comment_items(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(data, dict):
        keys = {str(key) for key in data}
        if {"reviewId", "orderCommentScore", "ctime"}.issubset(keys):
            found.append(data)
        for value in data.values():
            found.extend(find_comment_items(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(find_comment_items(item))
    return found


def find_shop_items(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(data, dict):
        lowered = {str(k).lower(): v for k, v in data.items()}
        shop_id = lowered.get("shopid") or lowered.get("id")
        shop_name = lowered.get("shopname") or lowered.get("name")
        if shop_id and shop_name and "heytea" in str(shop_name).lower():
            found.append({"id": str(shop_id), "name": str(shop_name)})
        for value in data.values():
            found.extend(find_shop_items(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(find_shop_items(item))
    return found


def collect_image_urls(value: Any) -> list[str]:
    urls: list[str] = []

    def add(raw: Any) -> None:
        text = str(raw or "").strip()
        if not text or text.startswith(("data:", "blob:")):
            return
        if not re.match(r"https?://", text, flags=re.I):
            return
        if text not in urls:
            urls.append(text)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, item in node.items():
                if any(token in str(key).lower() for token in ("url", "pic", "image", "photo")):
                    if isinstance(item, str):
                        add(item)
                    else:
                        walk(item)
                else:
                    walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            add(node)

    walk(value)
    return urls


def _format_money(value: Any, currency: str = "") -> str:
    if isinstance(value, str):
        text = clean_text(value)
        if text:
            return text
    if isinstance(value, (int, float)):
        amount = float(value)
        if abs(amount) >= 100:
            amount = amount / 100.0
        prefix = "$" if str(currency).upper() in {"HKD", "USD", "CAD", "AUD", "SGD"} else ""
        return f"{prefix}{amount:.2f}"
    return ""


def _extract_order_detail(payload: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    order_info = data.get("orderInfo")
    if not isinstance(order_info, dict):
        return None
    base_order = order_info.get("baseOrder") if isinstance(order_info.get("baseOrder"), dict) else {}
    merchant_order = order_info.get("merchantOrder") if isinstance(order_info.get("merchantOrder"), dict) else {}
    currency = clean_text(base_order.get("currency") or merchant_order.get("currency") or "")
    order_view_id = str(
        base_order.get("orderViewId")
        or merchant_order.get("orderViewId")
        or merchant_order.get("orderViewIdStr")
        or ""
    )
    products = order_info.get("products")
    if not isinstance(products, list):
        products = []

    order_items: list[dict[str, Any]] = []
    detail_lines: list[str] = []
    image_urls: list[str] = []

    for product in products:
        if not isinstance(product, dict):
            continue
        count = product.get("count") or 1
        main_price = _format_money(
            product.get("priceStr")
            or product.get("originPriceStr")
            or product.get("price")
            or product.get("originPrice"),
            currency,
        )
        unit_price = ""
        price_without_group = product.get("priceWithoutGroup")
        if isinstance(price_without_group, dict):
            unit_price = _format_money(
                price_without_group.get("unitPriceStr")
                or price_without_group.get("unitPrice")
                or price_without_group.get("amountStr")
                or price_without_group.get("amount"),
                currency,
            )
        if not unit_price:
            unit_price = main_price

        pic_list = product.get("picList")
        if isinstance(pic_list, list):
            for url in pic_list:
                text = clean_text(url)
                if text and text.startswith(("http://", "https://")) and text not in image_urls:
                    image_urls.append(text)

        item = {
            "spuName": product.get("name") or product.get("spuName") or "",
            "count": count,
            "remark": product.get("remark") or "",
            "desc": product.get("desc") or "",
            "spec": product.get("spec") or "",
            "groupProductNames": product.get("desc") or "",
            "currency": currency,
            "price": main_price,
            "priceStr": main_price,
            "unit_price": unit_price,
            "origin_price": _format_money(product.get("originPriceStr") or product.get("originPrice"), currency),
        }
        order_items.append(item)

        line = " | ".join(
            part
            for part in (
                f"{count}x {clean_text(item['spuName'])}".strip(),
                clean_text(item.get("spec")),
                clean_text(item.get("desc")),
                clean_text(item.get("unit_price")),
            )
            if part
        )
        if line:
            detail_lines.append(line)

    if not order_view_id:
        return None

    fee_lines: list[str] = []
    fee_dtls = order_info.get("feeDtls")
    if isinstance(fee_dtls, list):
        for fee in fee_dtls:
            if not isinstance(fee, dict):
                continue
            name = clean_text(fee.get("name") or fee.get("nameI18nEnum") or fee.get("code"))
            value = clean_text(fee.get("value") or _format_money(fee.get("price"), fee.get("currency") or currency))
            if name and value:
                fee_lines.append(f"{name}: {value}")

    expanded_detail = "\n".join(detail_lines)
    if fee_lines:
        expanded_detail = (expanded_detail + ("\n" if expanded_detail else "") + "Fee Summary\n" + "\n".join(fee_lines)).strip()

    return {
        "order_view_id": order_view_id,
        "order_items": order_items,
        "expanded_detail": expanded_detail,
        "order_detail_json": payload,
        "image_urls": image_urls,
    }


async def fetch_order_details(context, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not rows:
        return {}
    detail_lookup: dict[str, dict[str, Any]] = {}
    detail_page = await context.new_page()
    try:
        for index, row in enumerate(rows, start=1):
            order_id = clean_text(row.get("Order View ID"))
            shop_id = clean_text(row.get("Store ID"))
            if not order_id or not shop_id or order_id in detail_lookup:
                continue
            url = ORDER_DETAIL_PAGE.format(order_id=order_id, shop_id=shop_id)
            try:
                async with detail_page.expect_response(
                    lambda response: ORDER_DETAIL_API_TOKEN in response.url and response.status == 200,
                    timeout=20_000,
                ) as response_info:
                    await detail_page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                response = await response_info.value
                payload = await response.json()
                detail = _extract_order_detail(payload)
                if detail:
                    detail_lookup[order_id] = detail
            except Exception:
                continue
            if index % 10 == 0:
                print(f"[detail] fetched={len(detail_lookup)} processed={index}/{len(rows)}")
    finally:
        await detail_page.close()
    return detail_lookup


def normalize_item(
    item: dict[str, Any],
    shop_lookup: dict[str, str],
    detail_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ts = int(item.get("ctime") or item.get("reviewTime") or 0)
    review_dt = datetime.fromtimestamp(ts / 1000, tz=HK_TZ) if ts else None
    sku_list = item.get("skuList") or []
    labels = item.get("commentLabelList") or []
    shop_labels = item.get("shopCommentLabelList") or []
    image_urls = collect_image_urls(item.get("reviewPicList") or item.get("commentPicList") or item)

    order_items = []
    for sku in sku_list if isinstance(sku_list, list) else []:
        if not isinstance(sku, dict):
            continue
        order_items.append(
            {
                "spuName": sku.get("spuName") or sku.get("name") or "",
                "count": sku.get("count") or sku.get("quantity") or "",
                "remark": sku.get("remark") or "",
                "desc": sku.get("desc") or "",
                "spec": sku.get("spec") or "",
                "groupProductNames": sku.get("groupProductNames") or "",
            }
        )

    def item_line(sku: dict[str, Any]) -> str:
        parts = [
            f"{sku.get('count') or ''}x {sku.get('spuName') or ''}".strip(),
            clean_text(sku.get("spec")),
            clean_text(sku.get("desc")),
            clean_text(sku.get("remark")),
        ]
        return " | ".join(part for part in parts if part)

    shop_id = str(item.get("shopId") or "")
    order_view_id = str(item.get("orderViewId") or "")
    detail = (detail_lookup or {}).get(order_view_id) if order_view_id else None
    if detail and detail.get("order_items"):
        order_items = detail["order_items"]
        detail_images = detail.get("image_urls") or []
        for url in detail_images:
            if url not in image_urls:
                image_urls.append(url)
    shop_name = item.get("shopName") or shop_lookup.get(shop_id, "")
    expanded_detail = "\n".join(item_line(sku) for sku in order_items)
    detail_json = ""
    if detail:
        detail_text = str(detail.get("expanded_detail") or "").strip()
        if detail_text:
            expanded_detail = detail_text
        detail_payload = detail.get("order_detail_json")
        if detail_payload:
            detail_json = json.dumps(detail_payload, ensure_ascii=False)

    return {
        "Platform": "KeeTa",
        "Region": "HK",
        "Store ID": shop_id,
        "Store": shop_name,
        "Review ID": str(item.get("reviewId") or ""),
        "Reviewer Name": item.get("userName") or item.get("nickName") or "",
        "Rating": item.get("orderCommentScore") or "",
        "Delivery Rating": item.get("deliveryCommentScore") or "",
        "Review Content": item.get("comment") or "",
        "Review Labels": "|".join(clean_text(label.get("name")) for label in labels if isinstance(label, dict)),
        "Shop Labels": "|".join(clean_text(label.get("name")) for label in shop_labels if isinstance(label, dict)),
        "Review Time": review_dt.strftime("%Y-%m-%d") if review_dt else "",
        "Review Timestamp": ts,
        "Order View ID": order_view_id,
        "Image URLs": "|".join(image_urls),
        "Order Items JSON": json.dumps(order_items, ensure_ascii=False),
        "Order Items Text": "; ".join(item_line(sku) for sku in order_items),
        "Expanded Order Detail": expanded_detail,
        "Order Detail JSON": detail_json,
        "Raw Review JSON": json.dumps(item, ensure_ascii=False),
    }


async def safe_click_text(page, text: str, exact: bool = True, timeout: int = 1200) -> bool:
    try:
        locator = page.get_by_text(text, exact=exact).first
        if await locator.count() and await locator.is_visible(timeout=timeout):
            await locator.click(force=True)
            await page.wait_for_timeout(700)
            return True
    except Exception:
        return False
    return False


async def close_dialogs(page) -> None:
    blocked_words = ("知道了", "我知道了", "暂不处理", "稍后再说", "关闭")
    for word in blocked_words:
        if await safe_click_text(page, word, exact=True, timeout=400):
            return
    for selector in (
        ".ant-modal-close",
        ".adm-modal-close",
        "button[aria-label='Close']",
        ".ant-drawer-close",
        ".guide-close",
    ):
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=400):
                await locator.click(force=True)
                await page.wait_for_timeout(500)
                return
        except Exception:
            pass
    try:
        await page.mouse.click(1165, 204)
        await page.wait_for_timeout(400)
    except Exception:
        pass


async def is_logged_in(page) -> bool:
    if "login" in page.url.lower():
        return False
    for selector in (
        "text=顾客评价",
        "text=订单管理",
        "text=门店",
        "text=评价",
        "text=Reviews",
        "text=Orders",
        "text=Home",
        "text=Manage my restaurant",
    ):
        try:
            if await page.locator(selector).first.count():
                return True
        except Exception:
            pass
    return False


async def safe_goto(page, url: str, timeout: int = 60_000) -> None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    except Exception as exc:
        message = str(exc)
        if "interrupted by another navigation" not in message:
            raise
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            pass
    await page.wait_for_timeout(500)


async def ensure_logged_in(page, username: str, password: str, no_login: bool = False) -> None:
    await safe_goto(page, INDEX_URL)
    await page.wait_for_timeout(2500)
    if await is_logged_in(page):
        return
    if no_login:
        raise RuntimeError("KeeTa session is not logged in and --no-login was set.")
    if not username or not password:
        raise RuntimeError(f"KeeTa credentials missing. Provide env vars or {CREDENTIALS_FILE}.")

    await safe_goto(page, LOGIN_URL)
    await page.wait_for_timeout(2500)
    inputs = page.locator("input")
    input_count = await inputs.count()
    if input_count < 1:
        raise RuntimeError("Login inputs not found.")
    await inputs.nth(0).fill(username)
    await page.wait_for_timeout(300)

    password_input = page.locator("input[type='password']").first
    if input_count < 2 and await password_input.count() == 0:
        clicked_continue = False
        for label in ("Continue", "继续", "繼續", "下一步", "Next"):
            clicked_continue = await safe_click_text(page, label, exact=False, timeout=900)
            if clicked_continue:
                break
        if not clicked_continue:
            await page.keyboard.press("Enter")
        for _ in range(15):
            await page.wait_for_timeout(1000)
            password_input = page.locator("input[type='password']").first
            if await password_input.count() > 0:
                break
    if await password_input.count() > 0:
        await password_input.fill(password)
    elif await page.locator("input").count() >= 2:
        await page.locator("input").nth(1).fill(password)
    else:
        raise RuntimeError("Password input not found after email step.")
    await page.wait_for_timeout(300)

    clicked = False
    for label in ("登录", "登入", "Sign in", "Log in", "Continue"):
        clicked = await safe_click_text(page, label, exact=False, timeout=700)
        if clicked:
            break
    if not clicked:
        await page.mouse.click(1175, 580)

    for _ in range(30):
        await page.wait_for_timeout(1000)
        if await is_logged_in(page):
            return
    raise RuntimeError("KeeTa login did not complete.")


async def goto_evaluate(page) -> None:
    await safe_goto(page, EVALUATE_URL)
    await page.wait_for_timeout(3500)
    if "login" in page.url.lower():
        return
    await close_dialogs(page)
    if "#/evaluate" not in page.url:
        clicked = await safe_click_text(page, "顾客评价", exact=True, timeout=2500)
        if not clicked:
            await safe_click_text(page, "Reviews", exact=True, timeout=2500)
        await page.wait_for_timeout(3000)
        await close_dialogs(page)
    if "#/evaluate" not in page.url:
        await safe_goto(page, EVALUATE_URL)
        await page.wait_for_timeout(3500)
        await close_dialogs(page)


def get_evaluate_frame(page):
    for frame in page.frames:
        if "merchant.mykeeta.com/web/app/shop#/evaluate" in frame.url:
            return frame
    return page.main_frame


async def click_next_page(page) -> bool:
    frame = get_evaluate_frame(page)
    try:
        await frame.evaluate(
            "() => { const se = document.scrollingElement || document.documentElement || document.body; se.scrollTop = se.scrollHeight; }"
        )
        await page.wait_for_timeout(700)
    except Exception:
        await page.mouse.move(1000, 900)
        for _ in range(7):
            await page.mouse.wheel(0, 900)
            await page.wait_for_timeout(120)

    selectors = (
        ".roo-pagination li.arrow:not(.disabled) a[aria-label='Next']",
        ".roo-pagination a[aria-label='Next']",
        ".ant-pagination-next:not(.ant-pagination-disabled) button",
        ".ant-pagination-next:not(.ant-pagination-disabled)",
        "li[title='下一页']:not(.ant-pagination-disabled)",
        "li[title='Next Page']:not(.ant-pagination-disabled)",
    )
    for selector in selectors:
        try:
            locator = frame.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1000):
                await locator.click(force=True)
                await page.wait_for_timeout(2500)
                return True
        except Exception:
            pass

    try:
        box = await frame.locator("body").bounding_box()
        if box:
            await page.mouse.click(box["x"] + box["width"] - 80, box["y"] + box["height"] - 40)
        else:
            await page.mouse.click(1360, 940)
        await page.wait_for_timeout(2500)
        return True
    except Exception:
        return False


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = row.get("Review ID") or f"{row.get('Order View ID')}:{row.get('Review Timestamp')}"
        if key in seen:
            continue
        seen.add(str(key))
        unique.append(row)
    unique.sort(key=lambda r: int(r.get("Review Timestamp") or 0), reverse=True)
    return unique


def export_rows(rows: list[dict[str, Any]], raw_seen_count: int, args: argparse.Namespace) -> tuple[Path, Path]:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = args.output_prefix or "keeta_hk_weekly_reviews"
    json_path = EXPORTS / f"{prefix}_{stamp}.json"
    csv_path = EXPORTS / f"{prefix}_{stamp}.csv"
    payload = {
        "platform": "KeeTa",
        "region": "HK",
        "date_start": args.start_date,
        "date_end": args.end_date,
        "review_count": len(rows),
        "raw_seen_count": raw_seen_count,
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

    username, password = load_credentials(args)
    start_ms = hk_day_ms(args.start_date, end=False)
    end_ms = hk_day_ms(args.end_date, end=True)

    captured_pages: set[int] = set()
    raw_items: list[dict[str, Any]] = []
    shop_lookup = {shop["id"]: shop["name"] for shop in DEFAULT_SHOPS}

    async with async_playwright() as p:
        profile_dir = Path(args.profile_dir) if args.profile_dir else PROFILE_DIR
        profile_dir.mkdir(parents=True, exist_ok=True)
        launch_options: dict[str, Any] = {
            "headless": args.headless,
            "viewport": {"width": 1440, "height": 1000},
            "locale": "zh-HK",
            "timezone_id": "Asia/Hong_Kong",
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        if args.browser_channel:
            launch_options["channel"] = args.browser_channel
        try:
            context = await p.chromium.launch_persistent_context(str(profile_dir), **launch_options)
        except Exception as exc:
            if args.profile_dir:
                raise
            print(f"[browser] primary profile failed: {exc.__class__.__name__}: {exc}")
            FALLBACK_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            launch_options.pop("channel", None)
            context = await p.chromium.launch_persistent_context(str(FALLBACK_PROFILE_DIR), **launch_options)
        page = context.pages[0] if context.pages else await context.new_page()

        async def on_response(response) -> None:
            nonlocal raw_items, shop_lookup
            if response.status != 200:
                return
            url = response.url
            if COMMENT_API_TOKEN in url:
                try:
                    body = await response.json()
                except Exception:
                    return
                items = find_comment_items(body)
                request = response.request
                page_no = 0
                try:
                    post = request.post_data_json
                    page_no = int((post or {}).get("pageNo") or 0)
                except Exception:
                    pass
                if page_no:
                    captured_pages.add(page_no)
                for item in items:
                    raw_items.append(item)
                print(f"[capture] page={page_no or '?'} items={len(items)} total_raw={len(raw_items)}")
            elif SHOP_LIST_API_TOKEN in url:
                try:
                    shops = find_shop_items(await response.json())
                except Exception:
                    return
                for shop in shops:
                    shop_lookup[str(shop["id"])] = shop["name"]

        page.on("response", on_response)

        try:
            await ensure_logged_in(page, username, password, args.no_login)
            await goto_evaluate(page)
            await page.wait_for_timeout(5000)

            stable_rounds = 0
            last_count = 0
            for index in range(args.max_pages):
                rows = [
                    normalize_item(item, shop_lookup)
                    for item in raw_items
                    if start_ms <= int(item.get("ctime") or 0) <= end_ms
                ]
                rows = dedupe_rows(rows)
                print(f"[page-loop] step={index + 1}/{args.max_pages} valid={len(rows)} pages={sorted(captured_pages)}")
                if len(rows) >= args.max_reviews:
                    break
                if len(rows) == last_count:
                    stable_rounds += 1
                else:
                    stable_rounds = 0
                    last_count = len(rows)
                if index > 0 and stable_rounds >= 3 and rows:
                    oldest = rows[-1].get("Review Time")
                    if oldest and oldest < args.start_date:
                        break
                if not await click_next_page(page):
                    break

            await page.wait_for_timeout(2000)
            filtered_items = [item for item in raw_items if start_ms <= int(item.get("ctime") or 0) <= end_ms]
            rows = [normalize_item(item, shop_lookup) for item in filtered_items]
            rows = dedupe_rows(rows)[: args.max_reviews]
            if rows:
                detail_lookup = await fetch_order_details(context, rows)
                if detail_lookup:
                    rows = [normalize_item(item, shop_lookup, detail_lookup) for item in filtered_items]
                    rows = dedupe_rows(rows)[: args.max_reviews]
            json_path, csv_path = export_rows(rows, len(raw_items), args)
            return json_path, csv_path, len(rows)
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
