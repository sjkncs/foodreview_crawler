from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import dataclass
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CREDENTIALS_FILE = DATA / "fantuan_credentials.local.json"
EXPORTS = ROOT / "exports" / "fantuan"
LOGIN_URL = "https://merchant.fantuan.ca/#/login"
BASE_URL = "https://merchant.fantuan.ca"
LIST_REVIEW_API = "/api/merchantadmin/pc/merchant/v1/review/listReview"
ORDER_INFO_API = "/api/merchantadmin/pc/merchantApi/v1/order/info/forReview"


@dataclass(frozen=True)
class CountryConfig:
    code: str
    route_suffix: str
    label: str
    profile_name: str
    display_name: str

    @property
    def profile_dir(self) -> Path:
        return DATA / "browser_profiles" / self.profile_name


COUNTRIES = {
    "ca": CountryConfig("ca", "CA", "加拿大", "fantuan_ca", "Canada"),
    "us": CountryConfig("us", "US", "美国", "fantuan_us", "United States"),
    "au": CountryConfig("au", "AU", "澳大利亚", "fantuan_au", "Australia"),
}

FIELDS = [
    "Platform",
    "Country",
    "Country Code",
    "Restaurant ID",
    "Restaurant Route",
    "Restaurant",
    "Area Name",
    "Reviewer Name",
    "Author Avatar URL",
    "Rating",
    "Rating Comment",
    "Package Rating",
    "Package Rating Comment",
    "Taste Rating",
    "Taste Rating Comment",
    "Review Content",
    "Recommended Items",
    "Image URLs",
    "Review Time",
    "Order SN",
    "POS Order ID",
    "Order Take No",
    "Order Customer Name",
    "Order Customer Mobile",
    "Order Items JSON",
    "Order Items Text",
    "Expanded Order Detail",
    "Order Detail JSON",
    "Product Subtotal",
    "Net Sales",
    "GST",
    "Commission",
    "Commission Tax",
    "Promotion Fee",
    "Settlement Amount",
    "Settlement JSON",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fantuan weekly review collector")
    parser.add_argument("--country", default="ca", choices=sorted(COUNTRIES), help="Fantuan country account")
    parser.add_argument("--days", type=int, default=7, help="Only keep reviews in the last N days")
    parser.add_argument("--max-reviews", type=int, default=100, help="Maximum reviews to export")
    parser.add_argument("--limit-stores", type=int, default=0, help="Limit number of stores to crawl; 0 means all")
    parser.add_argument("--restaurant-id", default="", help="Only crawl one restaurant ID")
    parser.add_argument("--store-name", default="", help="Only crawl stores whose name contains this text")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--username", default="", help="Fantuan username")
    parser.add_argument("--password", default="", help="Fantuan password")
    parser.add_argument("--output-prefix", default="", help="Optional export filename prefix")
    return parser.parse_args()


def normalize_country(country: str) -> CountryConfig:
    return COUNTRIES[country.lower()]


def load_credentials(args: argparse.Namespace, config: CountryConfig) -> tuple[str, str]:
    if args.username and args.password:
        return args.username, args.password

    country_prefix = f"FANTUAN_{config.code.upper()}"
    username = os.getenv(f"{country_prefix}_USERNAME") or os.getenv("FANTUAN_USERNAME") or ""
    password = os.getenv(f"{country_prefix}_PASSWORD") or os.getenv("FANTUAN_PASSWORD") or ""
    if username and password:
        return username, password

    if CREDENTIALS_FILE.exists():
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        country_data = data.get(config.code) or {}
        aliases = {
            "ca": ("canada",),
            "us": ("usa", "united_states", "united-states"),
            "au": ("australia",),
        }
        for alias in aliases.get(config.code, ()):
            country_data = country_data or data.get(alias) or {}
        username = country_data.get("username") or data.get("username") or ""
        password = country_data.get("password") or data.get("password") or ""
    else:
        username = password = ""
    return username, password


def parse_review_time(value: str) -> datetime | None:
    raw = str(value or "").strip()
    candidates = [raw, raw[:16], raw[:10]]
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        for candidate in candidates:
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                pass
    return None


async def click_if_visible(page, labels: tuple[str, ...], timeout: int = 1500) -> str:
    for label in labels:
        try:
            locator = page.get_by_text(label, exact=True).first
            if await locator.count() > 0 and await locator.is_visible(timeout=timeout):
                await locator.click(force=True)
                await page.wait_for_timeout(600)
                return label
        except Exception:
            pass
    return ""


async def fill_first_visible(page, selectors: tuple[str, ...], value: str, timeout: int = 1_500) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=timeout):
                await locator.fill(value)
                return True
        except Exception:
            pass
    return False


async def close_blocking_dialog(page) -> str:
    labels = (
        "暂不处理",
        "知道了",
        "关闭",
        "现在填写",
        "稍后处理",
    )
    labels = (
        "暂不处理",
        "稍后处理",
        "知道了",
        "我知道了",
        "关闭",
        "取消",
        "Close",
        "Cancel",
    )
    clicked = await click_if_visible(page, labels)
    if clicked:
        return clicked
    for selector in (
        ".ant-modal button[aria-label='Close']",
        ".ant-modal .ant-modal-close",
        ".ant-modal-confirm-btns button",
        ".ant-drawer button[aria-label='Close']",
        ".ant-drawer .anticon-close",
    ):
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=500):
                await locator.click(force=True)
                await page.wait_for_timeout(500)
                return selector
        except Exception:
            pass
    return ""


async def select_login_country(page, config: CountryConfig) -> None:
    selector = page.locator("#configName").locator("xpath=ancestor::div[contains(@class, 'ant-select')][1]").first
    if await selector.count() == 0:
        return
    current = ""
    try:
        current = await selector.inner_text(timeout=1000)
    except Exception:
        pass
    if config.label in current or config.route_suffix in current.upper():
        return
    await selector.click(force=True)
    await page.wait_for_timeout(500)
    option = page.locator(".ant-select-item-option-content", has_text=config.label).first
    if await option.count() == 0:
        options = page.locator(".ant-select-item-option-content")
        option_count = await options.count()
        route_hint = config.route_suffix.upper()
        for index in range(option_count):
            text = (await options.nth(index).inner_text()).strip().upper()
            if route_hint and route_hint in text:
                option = options.nth(index)
                break
    if await option.count() == 0:
        return
    await option.click(timeout=5_000)
    await page.wait_for_timeout(800)


async def switch_to_password_login(page) -> None:
    try:
        password_input = page.locator("#password").first
        if await password_input.count() > 0 and await password_input.is_visible(timeout=800):
            return
    except Exception:
        pass

    link_candidates = (
        "label.ant-checkbox-wrapper + a",
        "div[style*='justify-content: space-between'] a",
        "form a",
    )
    keywords = ("账号密码", "密碼登錄", "密码登录", "Password")
    for selector in link_candidates:
        try:
            links = page.locator(selector)
            count = await links.count()
            for index in range(count):
                link = links.nth(index)
                text = (await link.inner_text(timeout=800)).strip()
                if text and any(key in text for key in keywords):
                    await link.click(force=True)
                    await page.wait_for_timeout(900)
                    return
        except Exception:
            pass


async def ensure_logged_in(page, config: CountryConfig, username: str, password: str) -> None:
    await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(2_000)
    if "login" not in page.url:
        return

    if not username or not password:
        raise RuntimeError(f"Fantuan credentials missing. Provide env vars or {CREDENTIALS_FILE}.")

    await close_blocking_dialog(page)
    await select_login_country(page, config)
    await switch_to_password_login(page)
    await page.wait_for_timeout(400)
    await select_login_country(page, config)

    user_filled = await fill_first_visible(
        page,
        (
            "#username",
            "input[name='username']",
            "input[autocomplete='username']",
            "input[placeholder*='账号']",
            "input[placeholder*='用户名']",
            "input[placeholder*='邮箱']",
            "form input[type='text']",
        ),
        username,
    )
    password_filled = await fill_first_visible(
        page,
        (
            "#password",
            "input[name='password']",
            "input[autocomplete='current-password']",
            "input[placeholder*='密码']",
            "form input[type='password']",
        ),
        password,
    )
    if not user_filled or not password_filled:
        raise RuntimeError(
            f"Fantuan {config.display_name} login form not ready: username={user_filled}, password={password_filled}."
        )

    clicked = False
    for selector in (
        "button.ant-btn-primary:has-text('登录')",
        "button:has-text('登录')",
        "button.ant-btn-primary:has-text('Log in')",
        "button:has-text('Log in')",
        "form button[type='submit']",
    ):
        try:
            button = page.locator(selector).first
            if await button.count() > 0 and await button.is_visible(timeout=1_000):
                await button.click(timeout=5_000)
                clicked = True
                break
        except Exception:
            pass
    if not clicked:
        try:
            await page.keyboard.press("Enter")
            clicked = True
        except Exception:
            pass
    if not clicked:
        raise RuntimeError(f"Fantuan {config.display_name} login button was not found.")

    await page.wait_for_timeout(6_000)
    body = await page.locator("body").inner_text(timeout=5_000)
    if any(token in body for token in ("登录失败", "Login failed", "账号或密码错误", "Invalid username or password")):
        raise RuntimeError(f"Fantuan {config.display_name} login failed; country selection or credentials may be incorrect.")
    if "login" in page.url:
        raise RuntimeError("Fantuan login did not complete.")


async def read_session_payload(page) -> dict[str, Any]:
    raw = await page.evaluate("() => sessionStorage.getItem('SESSIONKEY')")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def build_store_records(config: CountryConfig, session_payload: dict[str, Any], args: argparse.Namespace) -> list[dict[str, str]]:
    store_name_filter = (args.store_name or "").strip().lower()
    restaurant_id_filter = (args.restaurant_id or "").strip()
    group_stores = session_payload.get("groupStores") or []
    stores: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    def append_store(item: dict[str, Any]) -> None:
        restaurant_id = str(item.get("restaurantId") or "").strip()
        if not restaurant_id or restaurant_id in seen_ids:
            return
        restaurant_name = str(item.get("restaurantName") or item.get("enRestaurantName") or "").strip()
        if restaurant_id_filter and restaurant_id != restaurant_id_filter:
            return
        if store_name_filter and store_name_filter not in restaurant_name.lower():
            return
        seen_ids.add(restaurant_id)
        stores.append(
            {
                "restaurant_id": restaurant_id,
                "restaurant_name": restaurant_name,
                "route": f"{restaurant_id}-{config.route_suffix}",
                "area_name": str(item.get("wechatName") or "").strip(),
            }
        )

    for store in group_stores:
        if isinstance(store, dict):
            append_store(store)

    if not stores and session_payload.get("restaurantId"):
        append_store(session_payload)

    if args.limit_stores > 0:
        stores = stores[: args.limit_stores]
    return stores


async def wait_for_review_page(page, route: str) -> dict[str, Any]:
    review_url = f"{BASE_URL}/#/{route}/evaluate/custom"
    payload = await wait_for_json_response(
        page,
        lambda response: LIST_REVIEW_API in response.url and response.status == 200,
        lambda: page.goto(review_url, wait_until="domcontentloaded", timeout=45_000),
        timeout=45_000,
    )
    await page.wait_for_timeout(2_000)
    await close_blocking_dialog(page)
    return payload


async def wait_for_json_response(page, matcher, action, timeout: int = 30_000) -> dict[str, Any]:
    captured: dict[str, Any] = {"errors": []}

    async def on_response(response) -> None:
        if "payload" in captured:
            return
        try:
            if not matcher(response):
                return
            text = await response.text()
            captured["payload"] = json.loads(text)
        except Exception as exc:
            captured["errors"].append(str(exc))

    page.context.on("response", on_response)
    try:
        await action()
        deadline = asyncio.get_running_loop().time() + timeout / 1000
        while "payload" not in captured and asyncio.get_running_loop().time() < deadline:
            await page.wait_for_timeout(200)
        if "payload" in captured:
            return captured["payload"]
        last_error = captured["errors"][-1] if captured["errors"] else ""
        raise RuntimeError(last_error or "Timed out waiting for JSON response")
    finally:
        page.context.remove_listener("response", on_response)


async def click_next_page(page) -> dict[str, Any] | None:
    await close_blocking_dialog(page)
    next_button = page.locator(".ant-pagination-next:not(.ant-pagination-disabled)").first
    try:
        if await next_button.count() == 0 or not await next_button.is_visible(timeout=1_000):
            return None
        payload = await wait_for_json_response(
            page,
            lambda response: LIST_REVIEW_API in response.url and response.status == 200,
            lambda: next_button.click(),
            timeout=30_000,
        )
        await page.wait_for_timeout(1_500)
        return payload
    except Exception:
        return None


async def click_order_detail(page, row_index: int) -> dict[str, Any]:
    await close_blocking_dialog(page)
    detail_buttons = page.get_by_text("订单详情", exact=True)
    if await detail_buttons.count() == 0:
        detail_buttons = page.get_by_text("订单详情", exact=True)
    if await detail_buttons.count() == 0:
        detail_buttons = page.get_by_text("Order details", exact=True)
    payload = await wait_for_json_response(
        page,
        lambda response: ORDER_INFO_API in response.url and response.status == 200,
        lambda: detail_buttons.nth(row_index).click(timeout=8_000, force=True),
        timeout=30_000,
    )
    await page.wait_for_timeout(500)
    await close_order_drawer(page)
    return payload


async def close_order_drawer(page) -> None:
    for selector in (
        ".ant-drawer .ant-drawer-extra",
        ".ant-drawer .anticon-close",
        ".ant-drawer button[aria-label='Close']",
        ".ant-modal .ant-modal-close",
        ".ant-modal button[aria-label='Close']",
    ):
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=700):
                await locator.click(force=True)
                await page.wait_for_timeout(400)
                return
        except Exception:
            pass
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(400)
    except Exception:
        pass


def first_list_with_goods(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        if data and all(isinstance(item, dict) for item in data) and any("goodsName" in item for item in data):
            return data
        for item in data:
            result = first_list_with_goods(item)
            if result:
                return result
    if isinstance(data, dict):
        for key in ("orderGoodsList", "goodsList", "orderGoodsVOList", "goodsInfoList"):
            value = data.get(key)
            result = first_list_with_goods(value)
            if result:
                return result
        for value in data.values():
            result = first_list_with_goods(value)
            if result:
                return result
    return []


def extract_settlement(data: dict[str, Any]) -> list[dict[str, Any]]:
    settlement = data.get("settlementInfo") or {}
    items = settlement.get("settlementItemList")
    if isinstance(items, list):
        return items
    return []


def format_order_items(goods_list: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str, str]:
    items: list[dict[str, Any]] = []
    text_blocks: list[str] = []
    expanded_blocks: list[str] = []
    for goods in goods_list:
        attrs: list[dict[str, Any]] = []
        attr_texts: list[str] = []
        expanded_lines: list[str] = []
        for attr in goods.get("attrList") or []:
            attr_name = attr.get("attrName") or attr.get("enAttrName") or ""
            details = []
            for detail in attr.get("attrDetailList") or []:
                detail_name = detail.get("attrDetailName") or detail.get("enAttrDetailName") or ""
                detail_count = detail.get("attrDetailCount")
                details.append(
                    {
                        "name": detail_name,
                        "count": detail_count,
                        "price": detail.get("attrDetailPrice") or detail.get("attrDetailPriceView") or "",
                    }
                )
                prefix = f"x{detail_count} " if detail_count not in (None, "") else ""
                attr_texts.append(f"[{attr_name}] {prefix}{detail_name}".strip())
                expanded_lines.extend([f"[{attr_name}]", f"{prefix}{detail_name}".strip()])
            attrs.append({"name": attr_name, "details": details})

        item = {
            "quantity": goods.get("goodsCount"),
            "product": goods.get("goodsName") or goods.get("enGoodsName") or "",
            "unit_price": goods.get("goodsPrice") or goods.get("goodsPriceView") or "",
            "attributes": attrs,
        }
        items.append(item)
        text_blocks.append(
            "\n".join(
                [
                    f"{item['quantity']} x {item['product']}  {item['unit_price']}".strip(),
                    *attr_texts,
                ]
            ).strip()
        )
        expanded_blocks.append(
            "\n".join(
                [
                    f"数量: {item['quantity']}",
                    f"商品: {item['product']}",
                    *expanded_lines,
                    f"单价: {item['unit_price']}",
                ]
            ).strip()
        )
    return items, "\n\n".join(block for block in text_blocks if block), "\n\n".join(block for block in expanded_blocks if block)


def settlement_value(items: list[dict[str, Any]], name: str, key: str | None = None) -> str:
    for item in items:
        if key and item.get("key") == key:
            return item.get("value") or ""
        if item.get("name") == name:
            return item.get("value") or ""
    return ""


def extract_order_detail(payload: dict[str, Any], order_sn: str = "") -> dict[str, Any]:
    data = payload.get("data") or {}
    goods_list = first_list_with_goods(data)
    order_items, order_items_text, expanded_order_items_text = format_order_items(goods_list)
    settlement_items = extract_settlement(data)
    subtotal = settlement_value(settlement_items, "商品小计")
    net_sales = settlement_value(settlement_items, "净销售额", "net_sale")
    gst = settlement_value(settlement_items, "GST")
    commission = settlement_value(settlement_items, "佣金", "commission")
    commission_tax = settlement_value(settlement_items, "佣金税", "commissionAddTax")
    promotion_fee = settlement_value(settlement_items, "推广费", "additional_merchant_fee")
    settlement_amount = settlement_value(settlement_items, "结算金额")
    expanded_detail = "\n".join(
        part
        for part in [
            f"订单号: {data.get('orderSn') or order_sn}".strip(),
            f"取餐号: {data.get('orderTakeNo') or data.get('takeNumber') or ''}".strip(),
            "",
            expanded_order_items_text,
            "",
            f"商品小计: {subtotal}" if subtotal else "",
            f"净销售额: {net_sales}" if net_sales else "",
            f"GST: {gst}" if gst else "",
            f"佣金: {commission}" if commission else "",
            f"佣金税: {commission_tax}" if commission_tax else "",
            f"推广费: {promotion_fee}" if promotion_fee else "",
            f"结算金额: {settlement_amount}" if settlement_amount else "",
        ]
        if part != ""
    )
    return {
        "Order Take No": data.get("orderTakeNo") or data.get("takeNumber") or "",
        "Order Customer Name": data.get("name") or "",
        "Order Customer Mobile": data.get("mobile") or "",
        "Order Items JSON": json.dumps(order_items, ensure_ascii=False),
        "Order Items Text": order_items_text,
        "Expanded Order Detail": expanded_detail,
        "Order Detail JSON": json.dumps(data, ensure_ascii=False),
        "Product Subtotal": subtotal,
        "Net Sales": net_sales,
        "GST": gst,
        "Commission": commission,
        "Commission Tax": commission_tax,
        "Promotion Fee": promotion_fee,
        "Settlement Amount": settlement_amount,
        "Settlement JSON": json.dumps(settlement_items, ensure_ascii=False),
    }


def review_to_row(
    review: dict[str, Any],
    config: CountryConfig,
    store: dict[str, str],
    restaurant_name: str,
    order_detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recommended = [item.get("goodsName", "") for item in review.get("likeGoodsList") or [] if item.get("goodsName")]
    attachments = [url for url in review.get("attachmentsList") or [] if isinstance(url, str)]
    row = {
        "Platform": "Fantuan",
        "Country": config.display_name,
        "Country Code": config.route_suffix,
        "Restaurant ID": str(review.get("restaurantId") or store["restaurant_id"]),
        "Restaurant Route": store["route"],
        "Restaurant": restaurant_name,
        "Area Name": store.get("area_name", ""),
        "Reviewer Name": review.get("authorName") or "",
        "Author Avatar URL": review.get("authorAvatar") or "",
        "Rating": review.get("rate"),
        "Rating Comment": review.get("rateComment") or "",
        "Package Rating": review.get("packageRate"),
        "Package Rating Comment": review.get("packageRateComment") or "",
        "Taste Rating": review.get("tasteRate"),
        "Taste Rating Comment": review.get("tasteRateComment") or "",
        "Review Content": review.get("content") or "",
        "Recommended Items": "、".join(recommended),
        "Image URLs": "|".join(attachments),
        "Review Time": review.get("createdAt") or "",
        "Order SN": review.get("orderSn") or "",
        "POS Order ID": review.get("posOrderId") or "",
        "Order Take No": "",
        "Order Customer Name": "",
        "Order Customer Mobile": "",
        "Order Items JSON": "",
        "Order Items Text": "",
        "Expanded Order Detail": "",
        "Order Detail JSON": "",
        "Product Subtotal": "",
        "Net Sales": "",
        "GST": "",
        "Commission": "",
        "Commission Tax": "",
        "Promotion Fee": "",
        "Settlement Amount": "",
        "Settlement JSON": "",
    }
    if order_detail:
        row.update(order_detail)
    return row


def export_results(prefix: str, config: CountryConfig, payload: dict[str, Any]) -> tuple[Path, Path]:
    export_dir = EXPORTS / config.code
    export_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_prefix = f"{prefix}_" if prefix else ""
    json_path = export_dir / f"{name_prefix}fantuan_{config.code}_weekly_reviews_{stamp}.json"
    csv_path = export_dir / f"{name_prefix}fantuan_{config.code}_weekly_reviews_{stamp}.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in payload["reviews"]:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    return json_path, csv_path


async def collect_reviews(args: argparse.Namespace) -> tuple[CountryConfig, dict[str, Any]]:
    config = normalize_country(args.country)
    username, password = load_credentials(args, config)
    since_date = datetime.now().date() - timedelta(days=args.days)
    reviews: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    source_pages = 0

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
        await ensure_logged_in(page, config, username, password)

        if "login" in page.url:
            raise RuntimeError(f"Fantuan {config.display_name} login did not complete.")

        await page.wait_for_timeout(1_500)
        session_payload = await read_session_payload(page)
        stores = build_store_records(config, session_payload, args)
        if not stores:
            raise RuntimeError(f"No Fantuan stores found for {config.display_name}.")

        for store in stores:
            if len(reviews) >= args.max_reviews:
                break
            try:
                list_payload = await wait_for_review_page(page, store["route"])
            except Exception as exc:
                errors.append(
                    {
                        "restaurant_id": store["restaurant_id"],
                        "restaurant": store["restaurant_name"],
                        "error": f"open review page: {exc}",
                    }
                )
                continue

            stop = False
            while list_payload and not stop and len(reviews) < args.max_reviews:
                source_pages += 1
                data = list_payload.get("data") or {}
                restaurant_name = data.get("restaurantName") or store["restaurant_name"]
                page_reviews = data.get("reviewInfoVos") or []
                recent_indices: list[tuple[int, dict[str, Any]]] = []
                for index, review in enumerate(page_reviews):
                    review_time = parse_review_time(review.get("createdAt") or "")
                    if review_time and review_time.date() < since_date:
                        stop = True
                        continue
                    recent_indices.append((index, review))

                for row_index, review in recent_indices:
                    if len(reviews) >= args.max_reviews:
                        break
                    detail = None
                    try:
                        detail_payload = await click_order_detail(page, row_index)
                        detail = extract_order_detail(detail_payload, review.get("orderSn") or "")
                    except Exception as exc:
                        errors.append(
                            {
                                "restaurant_id": store["restaurant_id"],
                                "restaurant": store["restaurant_name"],
                                "review_id": review.get("id"),
                                "order_sn": review.get("orderSn"),
                                "error": str(exc),
                            }
                        )
                    reviews.append(review_to_row(review, config, store, restaurant_name, detail))

                if stop or len(reviews) >= args.max_reviews:
                    break
                list_payload = await click_next_page(page)

        await context.close()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "platform": "Fantuan",
        "country": config.display_name,
        "country_code": config.code,
        "login_url": LOGIN_URL,
        "since_date": since_date.isoformat(),
        "source_pages": source_pages,
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
                "country": config.display_name,
                "store_count": payload["store_count"],
                "review_count": payload["review_count"],
                "source_pages": payload["source_pages"],
                "errors": payload["errors"][:5],
                "stores": payload["stores"][:10],
                "sample": [
                    {
                        "Restaurant": row.get("Restaurant"),
                        "Reviewer Name": row.get("Reviewer Name"),
                        "Review Content": row.get("Review Content"),
                        "Image URLs": row.get("Image URLs"),
                        "Review Time": row.get("Review Time"),
                        "Order SN": row.get("Order SN"),
                        "Order Items Text": row.get("Order Items Text"),
                        "Expanded Order Detail": row.get("Expanded Order Detail"),
                    }
                    for row in payload["reviews"][:3]
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
