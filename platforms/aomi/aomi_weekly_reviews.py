from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
EXPORTS = ROOT / "exports" / "aomi"
CREDENTIALS_FILE = DATA / "aomi_credentials.local.json"

LOGIN_URL = "https://merchant.aomiapp.com/#/login"
BUSINESS_STORES_URL = "https://merchant.aomiapp.com/#/businessDaily/stores"
REVIEW_URL = "https://merchant.aomiapp.com/#/customer/evaluation"

DANGEROUS_URL_TOKENS = (
    "_merchant-replied",
    "_delete-merchant-replied",
    "_selected",
    "_cancel-selected",
    "review-coupon",
    "resetAccountPassword",
    "saveStoreMerchantAdminAccount",
    "auth2Store",
)


@dataclass(frozen=True)
class AccountConfig:
    key: str
    label: str
    country_code: str
    country_label: str
    profile_name: str

    @property
    def profile_dir(self) -> Path:
        return DATA / "browser_profiles" / self.profile_name

    @property
    def export_dir(self) -> Path:
        return EXPORTS / self.country_code / self.key


ACCOUNTS = {
    "default": AccountConfig(
        key="default",
        label="Aomi Macau",
        country_code="mo",
        country_label="中国澳门",
        profile_name="aomi_default",
    )
}


FIELDS = [
    "platform",
    "country",
    "country_code",
    "account",
    "store",
    "store_id",
    "rating",
    "sub_ratings",
    "review",
    "review_language",
    "translated_review",
    "customer",
    "review_time",
    "order_id",
    "ordered_items",
    "order_detail",
    "image_urls",
    "source",
    "quality_flags",
    "raw_json",
    "review_id",
    "review_type",
    "reply_status",
    "review_quality",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aomi weekly review collector (read-only)")
    parser.add_argument("--account", default="default", choices=sorted(ACCOUNTS))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--max-reviews", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--manual-login", action="store_true")
    parser.add_argument("--portal-url", default=REVIEW_URL)
    parser.add_argument("--login-url", default=LOGIN_URL)
    parser.add_argument("--username", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--country-label", default="")
    parser.add_argument("--country-code", default="")
    parser.add_argument("--output-prefix", default="")
    parser.add_argument("--limit-stores", type=int, default=0)
    return parser.parse_args()


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_review_time(value: Any) -> datetime | None:
    raw = clean_text(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def load_credentials(args: argparse.Namespace) -> tuple[str, str]:
    if args.username and args.password:
        return args.username, args.password
    username = os.getenv("AOMI_USERNAME") or ""
    password = os.getenv("AOMI_PASSWORD") or ""
    if username and password:
        return username, password
    if CREDENTIALS_FILE.exists():
        payload = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8-sig"))
        account_data = payload.get(args.account) or {}
        username = account_data.get("username") or payload.get("username") or ""
        password = account_data.get("password") or payload.get("password") or ""
    return str(username or ""), str(password or "")


def unwrap_response(text: str) -> Any:
    payload = json.loads(text)
    if isinstance(payload, dict):
        if "detailMsg" in payload:
            return payload["detailMsg"]
        if "result" in payload:
            return payload["result"]
    return payload


async def install_readonly_guard(context) -> None:
    async def guard(route, request):
        lowered = request.url.lower()
        method = request.method.upper()
        if method != "GET" and any(token.lower() in lowered for token in DANGEROUS_URL_TOKENS):
            await route.abort()
            return
        await route.continue_()

    await context.route("**/*", guard)


async def fill_first_visible(locator, value: str) -> bool:
    count = await locator.count()
    for index in range(count):
        node = locator.nth(index)
        try:
            if await node.is_visible(timeout=500):
                await node.fill(value)
                return True
        except Exception:
            continue
    return False


async def ensure_logged_in(page, username: str, password: str, manual_login: bool, login_url: str) -> None:
    await page.goto(BUSINESS_STORES_URL, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(2_000)

    token = await page.evaluate("() => localStorage.getItem('token') || ''")
    if token and "#/login" not in page.url:
        return

    await page.goto(login_url or LOGIN_URL, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(1_500)
    if not username or not password:
        if manual_login:
            print("[login] waiting for manual login...")
            await page.wait_for_timeout(90_000)
            return
        raise RuntimeError(f"Aomi credentials missing; provide args/env/or {CREDENTIALS_FILE}")

    inputs = page.locator("input")
    filled_user = False
    count = await inputs.count()
    for index in range(count):
        node = inputs.nth(index)
        try:
            input_type = (await node.get_attribute("type") or "").lower()
            if input_type != "password" and await node.is_visible(timeout=500):
                await node.fill(username)
                filled_user = True
                break
        except Exception:
            continue
    if not filled_user:
        raise RuntimeError("Aomi login username input not found.")

    if not await fill_first_visible(page.locator("input[type='password']"), password):
        raise RuntimeError("Aomi login password input not found.")

    login_clicked = False
    buttons = page.locator("button")
    for index in range(await buttons.count()):
        button = buttons.nth(index)
        try:
            text = clean_text(await button.inner_text())
            if await button.is_visible(timeout=500) and any(token in text.lower() for token in ("登录", "登錄", "login", "進入", "进入")):
                await button.click(force=True)
                login_clicked = True
                break
        except Exception:
            continue
    if not login_clicked:
        await page.keyboard.press("Enter")

    await page.wait_for_timeout(5_000)
    token = await page.evaluate("() => localStorage.getItem('token') || ''")
    if not token:
        if manual_login:
            print("[login] auto-login not completed, waiting for manual login...")
            await page.wait_for_timeout(90_000)
            return
        raise RuntimeError("Aomi login did not complete; captcha/OTP/manual confirmation may be required.")


async def return_to_business_system(page) -> None:
    state = await page.evaluate(
        """() => ({
            systemType: localStorage.getItem('systemType') || '',
            storesId: localStorage.getItem('storesId') || ''
        })"""
    )
    if str(state.get("systemType")) == "0":
        return
    try:
        if "customer/evaluation" not in page.url and "dashboard" not in page.url:
            await page.goto(REVIEW_URL, wait_until="domcontentloaded", timeout=45_000)
            await page.wait_for_timeout(2_000)
        button = page.get_by_text("返回商戶管理系統", exact=True).first
        if await button.count() > 0 and await button.is_visible(timeout=1_000):
            await button.click(force=True)
            await page.wait_for_timeout(4_000)
            if await page.evaluate("() => localStorage.getItem('systemType')") == "0":
                return
    except Exception:
        pass
    await page.evaluate(
        """() => {
            localStorage.setItem('systemType', '0');
            localStorage.setItem('storesId', '');
            localStorage.removeItem('storeName');
        }"""
    )
    await page.goto("https://merchant.aomiapp.com/#/dashboard", wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(1_500)
    await page.goto(BUSINESS_STORES_URL, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(2_000)


async def response_detail(response) -> Any:
    text = await response.text()
    return unwrap_response(text)


async def open_store_list(page) -> list[dict[str, Any]]:
    await return_to_business_system(page)
    try:
        async with page.expect_response(lambda resp: "getBusinessAuthStores" in resp.url and resp.status == 200, timeout=30_000) as response_info:
            await page.goto(BUSINESS_STORES_URL, wait_until="domcontentloaded", timeout=45_000)
        detail = await response_detail(await response_info.value)
        if isinstance(detail, list):
            return [store for store in detail if isinstance(store, dict)]
    except Exception:
        pass

    await page.wait_for_timeout(2_000)
    stores = await page.evaluate(
        """() => {
            const rows = Array.from(document.querySelectorAll('table tbody tr'));
            return rows.map(row => {
                const cells = Array.from(row.querySelectorAll('td')).map(td => (td.innerText || '').trim());
                return {storeId: cells[0] || '', name: cells[1] || '', raw: cells.join('\\n')};
            }).filter(item => /^\\d{3,}$/.test(item.storeId));
        }"""
    )
    return [store for store in stores if isinstance(store, dict)]


async def enter_store_by_index(page, store: dict[str, Any], index: int) -> None:
    await return_to_business_system(page)
    await page.goto(BUSINESS_STORES_URL, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(2_000)
    enter_buttons = page.get_by_text("進入門店", exact=True)
    if await enter_buttons.count() <= index:
        raise RuntimeError(f"Aomi enter-store button not found for {store.get('storeId') or store.get('name')}")

    async with page.expect_response(lambda resp: "goToStores" in resp.url and resp.status == 200, timeout=30_000):
        await enter_buttons.nth(index).click(force=True)
    await page.wait_for_timeout(3_000)
    expected_store_id = clean_text(store.get("storeId"))
    current_store_id = await page.evaluate("() => localStorage.getItem('storesId') || ''")
    if expected_store_id and current_store_id != expected_store_id:
        raise RuntimeError(f"Aomi store switch mismatch: expected {expected_store_id}, got {current_store_id}")


async def load_review_list(page) -> dict[str, Any]:
    async with page.expect_response(lambda resp: "review-admin-view" in resp.url and resp.status == 200, timeout=35_000) as response_info:
        await page.goto(REVIEW_URL, wait_until="domcontentloaded", timeout=45_000)
    detail = await response_detail(await response_info.value)
    try:
        await page.get_by_text("查看", exact=True).first.wait_for(timeout=10_000)
        await page.wait_for_timeout(500)
    except Exception:
        pass
    return detail if isinstance(detail, dict) else {}


async def goto_next_review_page(page) -> dict[str, Any] | None:
    next_button = page.locator(".el-pagination button.btn-next:not([disabled])").first
    try:
        if await next_button.count() == 0 or not await next_button.is_visible(timeout=700):
            return None
        async with page.expect_response(lambda resp: "review-admin-view" in resp.url and resp.status == 200, timeout=25_000) as response_info:
            await next_button.click(force=True)
        detail = await response_detail(await response_info.value)
        return detail if isinstance(detail, dict) else None
    except Exception:
        return None


async def close_dialog(page) -> None:
    for selector in (".el-dialog__wrapper .el-dialog__close", ".el-dialog__headerbtn"):
        try:
            close = page.locator(selector).last
            if await close.count() > 0 and await close.is_visible(timeout=500):
                await close.click(force=True)
                await page.wait_for_timeout(300)
                return
        except Exception:
            continue
    try:
        await page.keyboard.press("Escape")
    except Exception:
        pass
    await page.wait_for_timeout(300)


async def open_detail_by_visible_order(page, visible_index: int, review_id: str) -> dict[str, Any]:
    detail_button_pattern = re.compile(r"^(查看|詳情|详情|view|detail)$", re.IGNORECASE)

    async def click_and_capture(locator) -> dict[str, Any]:
        async with page.expect_response(
            lambda resp: f"/aomi-comment-api-merchant/review/{review_id}" in resp.url and resp.status == 200,
            timeout=25_000,
        ) as response_info:
            await locator.click(force=True)
        detail = await response_detail(await response_info.value)
        await close_dialog(page)
        return detail if isinstance(detail, dict) else {}

    try:
        row = page.locator(".el-table__row").nth(visible_index)
        row_button = row.locator("button").filter(has_text=detail_button_pattern).first
        if await row_button.count() > 0 and await row_button.is_visible(timeout=800):
            return await click_and_capture(row_button)
    except Exception:
        await close_dialog(page)

    button_indices = await page.locator("button").evaluate_all(
        """buttons => buttons
            .map((button, index) => ({
                index,
                text: (button.innerText || '').trim(),
                visible: !!(button.offsetWidth || button.offsetHeight || button.getClientRects().length)
            }))
            .filter(item => item.visible && item.text === '查看')
            .map(item => item.index)
        """
    )
    if len(button_indices) <= visible_index:
        return {}
    button = page.locator("button").nth(int(button_indices[visible_index]))
    try:
        return await click_and_capture(button)
    except Exception:
        await close_dialog(page)
        if len(button_indices) > visible_index + 1:
            try:
                return await click_and_capture(page.locator("button").nth(int(button_indices[visible_index + 1])))
            except Exception:
                await close_dialog(page)
                return {}
        return {}


def parse_product_items(product_view: dict[str, Any]) -> list[dict[str, Any]]:
    name = clean_text(product_view.get("name"))
    if not name:
        return []
    items: list[dict[str, Any]] = []
    for part in re.split(r"[,，、]\s*", name):
        text = clean_text(part)
        if not text:
            continue
        match = re.match(r"(.+?)[xX×]\s*(\d+(?:\.\d+)?)$", text)
        if match:
            items.append({"name": clean_text(match.group(1)), "quantity": match.group(2), "unit_price": "", "price": ""})
        else:
            items.append({"name": text, "quantity": "", "unit_price": "", "price": ""})
    return items


def build_order_detail(detail: dict[str, Any]) -> tuple[str, list[dict[str, Any]], str]:
    product_view = detail.get("productView") if isinstance(detail.get("productView"), dict) else {}
    send_view = detail.get("sendView") if isinstance(detail.get("sendView"), dict) else {}
    order_id = clean_text(product_view.get("orderId"))
    items = parse_product_items(product_view)
    total = clean_text(product_view.get("showPrice") or product_view.get("price"))
    lines = []
    if product_view:
        lines.extend(
            [
                "产品详情：",
                f"产品类型：{clean_text(product_view.get('type'))}",
                f"产品名称：{clean_text(product_view.get('name'))}",
                f"订单金额：{total}",
                f"订单号：{order_id}",
            ]
        )
    if send_view:
        lines.extend(
            [
                "配送详情：",
                f"配送类型：{clean_text(send_view.get('type'))}",
                f"配送评价：{', '.join(clean_text(item) for item in send_view.get('tips') or [])}",
                f"配送进度：{clean_text(send_view.get('schedule'))}",
            ]
        )
    return order_id, items, "\n".join(line for line in lines if clean_text(line.split("：", 1)[-1]) or line.endswith("："))


def normalize_review(
    list_item: dict[str, Any],
    detail: dict[str, Any],
    store: dict[str, Any],
    config: AccountConfig,
    args: argparse.Namespace,
) -> dict[str, Any]:
    merged = {**list_item, **{k: v for k, v in detail.items() if v not in (None, "", [], {})}}
    order_id, ordered_items, order_detail = build_order_detail(merged)
    image_urls = [str(url) for url in (merged.get("medias") or []) if str(url).startswith(("http://", "https://"))]
    review_text = clean_text(merged.get("content"))
    flags: list[str] = []
    if not review_text:
        flags.append("empty_review_content")
    if not order_id:
        flags.append("missing_order_id")
    if not order_detail:
        flags.append("missing_order_detail")
    if not image_urls:
        flags.append("no_review_images")
    return {
        "platform": "Aomi",
        "country": args.country_label or config.country_label,
        "country_code": args.country_code or config.country_code,
        "account": config.key,
        "store": clean_text(merged.get("storeName") or store.get("name")),
        "store_id": clean_text(merged.get("storeId") or store.get("storeId")),
        "rating": clean_text(merged.get("score")),
        "sub_ratings": clean_text(merged.get("reviewItemDetail")),
        "review": review_text,
        "review_language": "",
        "translated_review": "",
        "customer": clean_text(merged.get("userName")),
        "review_time": clean_text(merged.get("createTime")),
        "order_id": order_id,
        "ordered_items": ordered_items,
        "order_detail": order_detail,
        "image_urls": image_urls,
        "source": REVIEW_URL,
        "quality_flags": flags,
        "raw_json": {"list": list_item, "detail": detail},
        "review_id": clean_text(merged.get("id")),
        "review_type": clean_text(merged.get("type")),
        "reply_status": "已回复" if merged.get("merchantReplied") else "未回复",
        "review_quality": clean_text(merged.get("quality")),
    }


async def collect_store_reviews(page, store: dict[str, Any], config: AccountConfig, args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[str]]:
    cutoff = datetime.now() - timedelta(days=max(1, args.days))
    reviews: list[dict[str, Any]] = []
    errors: list[str] = []
    current_page = await load_review_list(page)
    page_no = 1

    while current_page and page_no <= max(1, args.max_pages):
        list_items = [item for item in current_page.get("list") or [] if isinstance(item, dict)]
        if not list_items:
            break

        oldest_on_page: datetime | None = None
        visible_index = 0
        for item in list_items:
            if len(reviews) >= args.max_reviews:
                return reviews, errors
            parsed_time = parse_review_time(item.get("createTime"))
            if parsed_time:
                oldest_on_page = parsed_time if oldest_on_page is None else min(oldest_on_page, parsed_time)
                if parsed_time < cutoff:
                    visible_index += 1
                    continue
            review_id = clean_text(item.get("id"))
            detail: dict[str, Any] = {}
            if review_id:
                detail = await open_detail_by_visible_order(page, visible_index, review_id)
                if not detail:
                    errors.append(f"detail not captured: store={store.get('storeId')} review={review_id}")
            reviews.append(normalize_review(item, detail, store, config, args))
            visible_index += 1

        if len(reviews) >= args.max_reviews:
            break
        if oldest_on_page and oldest_on_page < cutoff:
            break
        page_no += 1
        current_page = await goto_next_review_page(page)
        if not current_page:
            break
    return reviews, errors


def write_exports(
    config: AccountConfig,
    reviews: list[dict[str, Any]],
    stores: list[dict[str, Any]],
    errors: list[str],
    warnings: list[str],
    args: argparse.Namespace,
) -> tuple[Path, Path]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{args.output_prefix}_" if args.output_prefix else ""
    export_dir = config.export_dir
    export_dir.mkdir(parents=True, exist_ok=True)
    json_path = export_dir / f"{prefix}aomi_{config.key}_weekly_reviews_{stamp}.json"
    csv_path = export_dir / f"{prefix}aomi_{config.key}_weekly_reviews_{stamp}.csv"
    end_at = datetime.now()
    start_at = end_at - timedelta(days=max(1, int(args.days or 7)))
    payload = {
        "platform": "Aomi",
        "country": args.country_label or config.country_label,
        "country_code": args.country_code or config.country_code,
        "account": config.key,
        "store_count": len(stores),
        "review_count": len(reviews),
        "time_range": {
            "type": "last_days",
            "days": max(1, int(args.days or 7)),
            "start_date": start_at.date().isoformat(),
            "end_date": end_at.date().isoformat(),
            "filter_mode": "client_side_after_read_only_api",
        },
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "errors": errors,
        "warnings": warnings,
        "stores": stores,
        "reviews": reviews,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in reviews:
            writer.writerow(
                {
                    field: json.dumps(row.get(field), ensure_ascii=False) if isinstance(row.get(field), (dict, list)) else row.get(field, "")
                    for field in FIELDS
                }
            )
    return json_path, csv_path


async def run() -> dict[str, Any]:
    from playwright.async_api import async_playwright

    args = parse_args()
    config = ACCOUNTS[args.account]
    username, password = load_credentials(args)
    errors: list[str] = []
    warnings: list[str] = []
    all_reviews: list[dict[str, Any]] = []
    stores: list[dict[str, Any]] = []
    profile_dir = config.profile_dir
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=args.headless,
            viewport={"width": 1600, "height": 1000},
            locale="zh-CN",
            ignore_https_errors=True,
        )
        await install_readonly_guard(context)
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await ensure_logged_in(page, username, password, args.manual_login, args.login_url)
            stores = await open_store_list(page)
            if args.limit_stores:
                stores = stores[: max(1, args.limit_stores)]
            if not stores:
                raise RuntimeError("Aomi store list is empty; account may lack store-management permission.")
            for index, store in enumerate(stores):
                if len(all_reviews) >= args.max_reviews:
                    break
                try:
                    await enter_store_by_index(page, store, index)
                    remaining = max(0, args.max_reviews - len(all_reviews))
                    store_args = argparse.Namespace(**{**vars(args), "max_reviews": remaining})
                    reviews, store_errors = await collect_store_reviews(page, store, config, store_args)
                    all_reviews.extend(reviews)
                    warnings.extend(store_errors)
                except Exception as exc:
                    errors.append(f"store failed: {store.get('storeId') or store.get('name')}: {exc}")
        except Exception as exc:
            errors.append(str(exc))
        finally:
            await context.close()

    json_path, csv_path = write_exports(config, all_reviews, stores, errors, warnings, args)
    summary = {
        "json": str(json_path),
        "csv": str(csv_path),
        "review_count": len(all_reviews),
        "store_count": len(stores),
        "time_range_days": max(1, int(args.days or 7)),
        "errors": errors,
        "warnings": warnings,
        "sample": all_reviews[:3],
    }
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> None:
    summary = asyncio.run(run())
    if summary.get("errors"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
