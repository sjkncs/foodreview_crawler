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


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPORTS = ROOT / "exports"
CREDENTIALS_FILE = DATA / "hungry_panda_credentials.local.json"
ORDER_DETAIL_API = "/api/merchant/order/detail"


@dataclass(frozen=True)
class RegionConfig:
    code: str
    country: str
    host: str
    profile_name: str

    @property
    def base_url(self) -> str:
        return f"https://{self.host}"

    @property
    def branch_url(self) -> str:
        return f"{self.base_url}/master/branchStore/storeList"


REGIONS = {
    "usa": RegionConfig("usa", "United States", "merchant-usa.hungrypanda.co", "hungry_panda_usa"),
    "us": RegionConfig("usa", "United States", "merchant-usa.hungrypanda.co", "hungry_panda_usa"),
    "ca": RegionConfig("ca", "Canada", "merchant-ca.hungrypanda.co", "hungry_panda_ca"),
    "canada": RegionConfig("ca", "Canada", "merchant-ca.hungrypanda.co", "hungry_panda_ca"),
    "au": RegionConfig("au", "Australia", "merchant-aus.hungrypanda.co", "hungry_panda_au"),
    "australia": RegionConfig("au", "Australia", "merchant-aus.hungrypanda.co", "hungry_panda_au"),
    "uk": RegionConfig("uk", "United Kingdom", "merchant-uk.hungrypanda.co", "hungry_panda_uk"),
    "gb": RegionConfig("uk", "United Kingdom", "merchant-uk.hungrypanda.co", "hungry_panda_uk"),
    "united-kingdom": RegionConfig("uk", "United Kingdom", "merchant-uk.hungrypanda.co", "hungry_panda_uk"),
    "kr": RegionConfig("kr", "South Korea", "merchant-kr.hungrypanda.co", "hungry_panda_kr"),
    "korea": RegionConfig("kr", "South Korea", "merchant-kr.hungrypanda.co", "hungry_panda_kr"),
}

DEFAULT_REGION = REGIONS["usa"]
PROFILE = DATA / "browser_profiles" / DEFAULT_REGION.profile_name
BRANCH_URL = DEFAULT_REGION.branch_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hungry Panda merchant weekly review collector")
    parser.add_argument(
        "--region",
        default="usa",
        choices=sorted(REGIONS),
        help="Hungry Panda merchant region: usa/us, ca/canada, au/australia, uk/gb, kr/korea",
    )
    parser.add_argument("--days", type=int, default=7, help="Only keep reviews in the last N days")
    parser.add_argument("--max-reviews", type=int, default=100, help="Stop after this many reviews")
    parser.add_argument("--start-index", type=int, default=0, help="Branch start index for segmented runs")
    parser.add_argument("--limit", type=int, default=0, help="Max branches to process in this segment; 0 means all")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--output-prefix", default="", help="Optional export filename prefix")
    parser.add_argument("--username", default="", help="Login username; prefer env/file for regular use")
    parser.add_argument("--password", default="", help="Login password; prefer env/file for regular use")
    parser.add_argument("--phone-code", default="+86", help="Phone country code for login account")
    parser.add_argument(
        "--manual-login",
        action="store_true",
        help="Open the browser and wait for manual login/captcha completion when needed",
    )
    return parser.parse_args()


def normalize_region(region: str) -> RegionConfig:
    return REGIONS[region.lower()]


def load_credentials(region: RegionConfig, args: argparse.Namespace) -> tuple[str, str]:
    if args.username and args.password:
        return args.username, args.password

    region_prefix = f"HUNGRY_PANDA_{region.code.upper()}"
    username = os.getenv(f"{region_prefix}_USERNAME") or os.getenv("HUNGRY_PANDA_USERNAME") or ""
    password = os.getenv(f"{region_prefix}_PASSWORD") or os.getenv("HUNGRY_PANDA_PASSWORD") or ""
    if username and password:
        return username, password

    if CREDENTIALS_FILE.exists():
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        region_data = data.get(region.code) or data.get(region.country) or {}
        default_data = data.get("default") or {}
        username = region_data.get("username") or default_data.get("username") or ""
        password = region_data.get("password") or default_data.get("password") or ""
    return username, password


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


async def click_first_visible(page, selectors: tuple[str, ...], timeout: int = 1_500) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=timeout):
                await locator.click()
                return True
        except Exception:
            pass
    return False


async def select_phone_code(page, phone_code: str) -> bool:
    if not phone_code:
        return True

    current = ""
    try:
        current = await page.locator("#phonePrefix").locator(
            "xpath=ancestor::div[contains(@class, 'ant-select')][1]"
        ).inner_text(timeout=1_000)
    except Exception:
        pass
    if phone_code in current:
        return True

    try:
        prefix_select = page.locator("#phonePrefix").locator(
            "xpath=ancestor::div[contains(@class, 'ant-select')][1]"
        )
        if await prefix_select.count() == 0:
            return False
        await prefix_select.click(force=True)
        await page.wait_for_timeout(300)
        phone_input = page.locator("#phonePrefix").first
        await phone_input.fill(phone_code.lstrip("+"))
        await page.wait_for_timeout(500)
        option = page.locator(
            ".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option-content",
            has_text=phone_code,
        ).first
        if await option.count() > 0 and await option.is_visible(timeout=2_000):
            await option.click()
        else:
            await page.keyboard.press("Enter")
        await page.wait_for_timeout(500)
        selected = await prefix_select.inner_text(timeout=1_000)
        return phone_code in selected
    except Exception:
        pass

    try:
        return await page.evaluate(
            """
            (phoneCode) => {
              const input = document.querySelector('#phonePrefix');
              if (!input) return false;
              const select = input.closest('.ant-select');
              const selector = select && select.querySelector('.ant-select-selector');
              if (!selector) return false;
              selector.click();
              input.value = phoneCode;
              input.dispatchEvent(new Event('input', { bubbles: true }));
              input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
              return true;
            }
            """,
            phone_code,
        )
    except Exception:
        return False


async def ensure_logged_in(
    page,
    region: RegionConfig,
    username: str,
    password: str,
    phone_code: str = "+86",
    manual_login: bool = False,
) -> None:
    if "master/login" not in page.url:
        return
    if not username or not password:
        raise RuntimeError(
            f"Hungry Panda {region.country} is not logged in. "
            f"Provide credentials via {CREDENTIALS_FILE}, env vars, or CLI args."
        )

    if not await select_phone_code(page, phone_code):
        raise RuntimeError(f"Could not switch Hungry Panda phone prefix to {phone_code}.")
    username_selectors = (
        'input[placeholder="Enter account number"]',
        'input[placeholder*="account number"]',
        'input[placeholder*="账号"]',
        'input[placeholder*="帳號"]',
        'input[placeholder*="계정"]',
        'input[type="tel"]',
        'input:not([type="password"])',
    )
    password_selectors = (
        'input[placeholder="Enter password"]',
        'input[placeholder*="password"]',
        'input[placeholder*="密码"]',
        'input[placeholder*="密碼"]',
        'input[placeholder*="비밀번호"]',
        'input[type="password"]',
    )
    submit_selectors = (
        'button:has-text("Login")',
        'button:has-text("登录")',
        'button:has-text("登入")',
        'button:has-text("로그인")',
        'button[type="submit"]',
    )

    if not await fill_first_visible(page, username_selectors, username):
        raise RuntimeError("Could not find Hungry Panda login username input.")
    if not await fill_first_visible(page, password_selectors, password):
        raise RuntimeError("Could not find Hungry Panda login password input.")
    if not await click_first_visible(page, submit_selectors):
        raise RuntimeError("Could not find Hungry Panda login button.")

    await page.wait_for_timeout(5_000)
    if "master/login" in page.url:
        if manual_login:
            print(
                json.dumps(
                    {
                        "status": "waiting_manual_login",
                        "region": region.code,
                        "message": "Complete captcha/login in the opened Edge window; crawler will continue after login succeeds.",
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            await page.wait_for_url(lambda url: "master/login" not in url, timeout=300_000)
            return
        raise RuntimeError(
            "Hungry Panda login did not complete; captcha or manual verification is required. "
            "Rerun with --manual-login once, then reuse the saved browser profile."
        )


async def collect_branch_rows(page) -> list[dict[str, Any]]:
    rows = page.locator("tr.ant-table-row, table tbody tr")
    branches: list[dict[str, Any]] = []
    for index in range(await rows.count()):
        row = rows.nth(index)
        text = (await row.inner_text()).replace("\n", "\t").strip()
        if "Enter the Branch Page" not in text:
            continue
        parts = [part.strip() for part in re.split(r"\t+", text) if part.strip()]
        if len(parts) >= 4:
            city, branch_id, branch_name = parts[0], parts[1], parts[2]
        else:
            match = re.search(r"\b(\d{6,})\b", text)
            branch_id = match.group(1) if match else ""
            city = text[: match.start()].strip() if match else ""
            branch_name = text[match.end() :].replace("Enter the Branch Page", "").strip() if match else text
        branches.append(
            {
                "row_index": index,
                "city": city,
                "branch_id": branch_id,
                "branch_name": branch_name,
                "source_text": text,
            }
        )
    return branches


async def enter_branch(master_page, branch: dict[str, Any]):
    rows = master_page.locator("tr.ant-table-row, table tbody tr")
    row = rows.nth(int(branch["row_index"]))
    button = row.get_by_text("Enter the Branch Page", exact=True).first
    try:
        async with master_page.context.expect_page(timeout=4_000) as page_info:
            await button.click()
        branch_page = await page_info.value
        await branch_page.wait_for_load_state("domcontentloaded", timeout=30_000)
        await branch_page.wait_for_timeout(2_000)
        return branch_page
    except Exception:
        await button.click()
        await master_page.wait_for_timeout(3_000)
        return master_page


async def open_ratings_page(branch_page) -> None:
    await close_order_detail_modal(branch_page)
    await branch_page.get_by_text("Orders", exact=True).click(timeout=10_000)
    await branch_page.wait_for_timeout(1_500)
    await close_order_detail_modal(branch_page)
    await branch_page.get_by_text("Ratings and reviews", exact=True).click(timeout=10_000)
    await branch_page.wait_for_timeout(2_500)
    try:
        await branch_page.get_by_text("All reviews", exact=True).click(timeout=1_500)
        await branch_page.wait_for_timeout(800)
    except Exception:
        pass


async def extract_reviews(page) -> list[dict[str, Any]]:
    return await page.evaluate(
        r"""
        () => {
          const norm = (s) => String(s || '').replace(/\s+/g, ' ').trim();
          const absolutize = (url) => {
            const value = String(url || '').trim();
            if (!value) return '';
            if (value.startsWith('data:') || value.startsWith('blob:')) return '';
            try {
              return new URL(value, window.location.href).href;
            } catch (_) {
              return value;
            }
          };
          const isReviewImageUrl = (url) => {
            if (!/^https?:\/\//i.test(url)) return false;
            if (/panda_logo|lan\.|captcha|verify|code|icon|avatar/i.test(url)) return false;
            if (/static\.hungrypanda\.co\/panda\//i.test(url)) return true;
            return /\.(jpe?g|png|webp|gif)(\?|#|$)/i.test(url);
          };
          const cleanText = (cell) => {
            const clone = cell.cloneNode(true);
            clone.querySelectorAll('img, svg, canvas, [class*="preview"], [class*="Preview"], [class*="image"], [class*="Image"]').forEach((node) => node.remove());
            return norm(clone.innerText || clone.textContent);
          };
          const extractImageUrls = (root) => {
            const urls = [];
            const push = (raw) => {
              const url = absolutize(raw);
              if (!url || urls.includes(url) || !isReviewImageUrl(url)) return;
              urls.push(url);
            };
            const pushSrcSet = (raw) => {
              String(raw || '').split(',').forEach((part) => push(part.trim().split(/\s+/)[0]));
            };
            root.querySelectorAll('img').forEach((img) => {
              push(img.currentSrc);
              push(img.getAttribute('src'));
              push(img.getAttribute('data-src'));
              push(img.getAttribute('data-original'));
              push(img.getAttribute('lazy-src'));
              pushSrcSet(img.getAttribute('srcset'));
              pushSrcSet(img.getAttribute('data-srcset'));
            });
            root.querySelectorAll('[style*="background"]').forEach((node) => {
              const style = node.getAttribute('style') || '';
              for (const match of style.matchAll(/url\((['"]?)(.*?)\1\)/g)) push(match[2]);
            });
            return urls.sort((left, right) => {
              const leftStatic = /static\.hungrypanda\.co\/panda\//i.test(left) ? 0 : 1;
              const rightStatic = /static\.hungrypanda\.co\/panda\//i.test(right) ? 0 : 1;
              return leftStatic - rightStatic || left.localeCompare(right);
            });
          };
          const countStars = (root) => {
            const fullSelectors = ['.ant-rate-star-full', '[class*="star-full"]', '[class*="starFull"]', '[class*="rate-star-full"]'];
            const halfSelectors = ['.ant-rate-star-half', '[class*="star-half"]', '[class*="starHalf"]', '[class*="rate-star-half"]'];
            let full = 0, half = 0;
            for (const sel of fullSelectors) full += root.querySelectorAll(sel).length;
            for (const sel of halfSelectors) half += root.querySelectorAll(sel).length;
            if (full || half) return Math.min(5, full + half * 0.5);
            const glyphs = (root.textContent || '').match(/[★⭐]/g);
            return glyphs ? Math.min(5, glyphs.length) : 0;
          };
          const labelMap = [
            ['Dish package', '包装'],
            ['Dish taste', '口味'],
            ['Overall review', '综合评价'],
            ['菜品包装', '包装'],
            ['菜品口味', '口味'],
            ['综合评价', '综合评价']
          ];
          const parseRatingCell = (cell) => {
            const result = {};
            const text = norm(cell.innerText || cell.textContent).toLowerCase();
            for (const [source, target] of labelMap) {
              if (!text.includes(source.toLowerCase())) continue;
              let best = null;
              const nodes = [cell, ...Array.from(cell.querySelectorAll('*'))];
              for (const node of nodes) {
                const nodeText = norm(node.innerText || node.textContent).toLowerCase();
                if (!nodeText.includes(source.toLowerCase())) continue;
                if (!best || nodeText.length < norm(best.innerText || best.textContent).length) best = node;
              }
              if (!best) continue;
              let root = best;
              for (let depth = 0; root && depth < 6; depth += 1, root = root.parentElement) {
                const stars = countStars(root);
                if (stars) {
                  result[target] = stars;
                  break;
                }
              }
            }
            return result;
          };
          const rows = Array.from(document.querySelectorAll('table tbody tr, tr.ant-table-row, .ant-table-row'));
          const out = [];
          for (const row of rows) {
            const cells = Array.from(row.querySelectorAll('td, [role="cell"]'));
            if (cells.length < 4) continue;
            const texts = cells.map((cell) => cleanText(cell));
            let ratingCol = 0, contentCol = 0, orderCol = 1, dateCol = 2, opCol = 3;
            if (/Dish package|Dish taste|Overall review|菜品包装|菜品口味|综合评价/i.test(texts[0]) && cells.length >= 5) {
              ratingCol = 0; contentCol = 1; orderCol = 2; dateCol = 3; opCol = 4;
            }
            const orderMatch = texts[orderCol].match(/\d{10,}/);
            const dateMatch = texts[dateCol].match(/\d{4}[-/]\d{1,2}[-/]\d{1,2}/);
            const content = texts[contentCol];
            const imageUrls = extractImageUrls(cells[contentCol] || row);
            if ((!content && !imageUrls.length) || !orderMatch || !dateMatch) continue;
            out.push({
              Review: texts[ratingCol],
              'Review contents': content,
              'Image URLs': imageUrls.join('|'),
              'Order ID': orderMatch[0],
              'Review time': dateMatch[0],
              Operation: texts[opCol] || '',
              child_rating: parseRatingCell(cells[ratingCol])
            });
          }
          return out;
        }
        """
    )


async def click_next_review_page(page) -> bool:
    selectors = (
        ".ant-pagination-next:not(.ant-pagination-disabled) button",
        ".ant-pagination-next:not(.ant-pagination-disabled)",
        "button:has-text('Next')",
    )
    for selector in selectors:
        try:
            button = page.locator(selector).first
            if await button.count() > 0 and await button.is_visible(timeout=800) and await button.is_enabled():
                await button.click()
                await page.wait_for_timeout(1_500)
                return True
        except Exception:
            pass
    return False


def parse_review_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return None


def export_results(prefix: str, payload: dict[str, Any]) -> tuple[Path, Path]:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_prefix = f"{prefix}_" if prefix else ""
    region = payload.get("region", "unknown")
    json_path = EXPORTS / f"{name_prefix}hungry_panda_{region}_weekly_reviews_{stamp}.json"
    csv_path = EXPORTS / f"{name_prefix}hungry_panda_{region}_weekly_reviews_{stamp}.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = [
        "Platform",
        "Country",
        "Region",
        "City",
        "Branch ID",
        "Branch",
        "Review",
        "Review contents",
        "Image URLs",
        "Order ID",
        "Review time",
        "Operation",
        "Child ratings",
        "Product Image URLs",
        "Order Status",
        "Order Created Time",
        "Expected Delivery Time",
        "Delivery Mode",
        "Courier Name",
        "Courier Phone",
        "Recipient Name",
        "Recipient Phone",
        "Recipient Address",
        "Doorplate Number",
        "Postal Code",
        "Notes",
        "Merchant Promotions",
        "Product Breakdown",
        "Consumer Tax",
        "Estimated Revenue",
        "Revenue Before Tax",
        "Delivery Fee",
        "Packing Charges",
        "Tableware Fee",
        "Fixed Price",
        "Order Items JSON",
        "Order Items Text",
        "Expanded Order Detail",
        "Fee Breakdown JSON",
        "Promotion Detail JSON",
        "Delivery Detail JSON",
        "Recipient Detail JSON",
        "Order Detail JSON",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in payload["reviews"]:
            writer.writerow({field: row.get(field, "") for field in fields})
    return json_path, csv_path


def format_price(value: Any, symbol: str = "$") -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ""
        if any(ch in text for ch in ("$", "£", "€", "¥")):
            return text
        try:
            value = float(text)
        except ValueError:
            return text
    if isinstance(value, (int, float)):
        return f"{symbol}{float(value):.2f}"
    return str(value)


def fee_price_map(fees: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for fee in fees:
        name = str(fee.get("feeName") or "").strip()
        if name:
            result[name] = format_price(fee.get("feePrice"))
    return result


def promotion_summary(promotion: dict[str, Any], symbol: str) -> tuple[str, list[dict[str, str]]]:
    items: list[dict[str, str]] = []
    pairs = (
        ("fullSubName", "fullSubPrice"),
        ("firstDiscountName", "firstDiscount"),
        ("redPacketName", "redPacketPrice"),
    )
    for name_key, price_key in pairs:
        name = str(promotion.get(name_key) or "").strip()
        raw_price = promotion.get(price_key)
        price = format_price(raw_price, symbol) if raw_price not in (None, "") else ""
        if name or price:
            items.append({"name": name, "price": price})
    summary = " | ".join(
        " ".join(part for part in (item["name"], item["price"]) if part).strip()
        for item in items
        if item["name"] or item["price"]
    )
    return summary, items


def build_order_items(details: list[dict[str, Any]], symbol: str) -> tuple[list[dict[str, Any]], str, str, str]:
    items: list[dict[str, Any]] = []
    text_blocks: list[str] = []
    expanded_blocks: list[str] = []
    image_urls: list[str] = []
    for detail in details:
        name = str(detail.get("productName") or "").strip()
        sku = str(detail.get("skuName") or "").strip()
        quantity = detail.get("productCount")
        price = format_price(detail.get("productPrice"), symbol)
        image_url = str(detail.get("productImg") or "").strip()
        if image_url and image_url not in image_urls:
            image_urls.append(image_url)
        item = {
            "product_name": name,
            "sku_name": sku,
            "quantity": quantity,
            "unit_price": price,
            "image_url": image_url,
        }
        items.append(item)

        summary_line = f"{quantity} x {name}".strip() if quantity not in (None, "") else name
        if price:
            summary_line = f"{summary_line}  {price}".strip()
        text_lines = [summary_line]
        expanded_lines = []
        if quantity not in (None, ""):
            expanded_lines.append(f"数量: {quantity}")
        if name:
            expanded_lines.append(f"商品: {name}")
        if sku:
            text_lines.append(f"规格: {sku}")
            expanded_lines.append(f"规格: {sku}")
        if price:
            expanded_lines.append(f"单价: {price}")
        if image_url:
            expanded_lines.append(f"商品图: {image_url}")
        text_blocks.append("\n".join(line for line in text_lines if line))
        expanded_blocks.append("\n".join(expanded_lines))

    return (
        items,
        "\n\n".join(block for block in text_blocks if block),
        "\n\n".join(block for block in expanded_blocks if block),
        "|".join(image_urls),
    )


def extract_order_detail(payload: dict[str, Any], modal_text: str = "") -> dict[str, Any]:
    data = payload.get("data") or {}
    symbol = str(data.get("symbol") or "$")
    details = data.get("details") if isinstance(data.get("details"), list) else []
    fees = data.get("feeInfoResqDTOList") if isinstance(data.get("feeInfoResqDTOList"), list) else []
    fee_map = fee_price_map(fees)
    promotion = data.get("fullSubRedRespDTO") if isinstance(data.get("fullSubRedRespDTO"), dict) else {}
    delivery = data.get("deliver") if isinstance(data.get("deliver"), dict) else {}
    recipient = data.get("merchantOrderAddressResVO") if isinstance(data.get("merchantOrderAddressResVO"), dict) else {}

    order_items, order_items_text, expanded_items_text, product_image_urls = build_order_items(details, symbol)
    promotion_text, promotion_items = promotion_summary(promotion, symbol)
    product_breakdown = next(
        (fee for fee in fees if str(fee.get("feeName") or "").strip() == "Product breakdown analysis(+)"),
        {},
    )
    product_breakdown_parts: list[str] = []
    if product_breakdown:
        root_price = format_price(product_breakdown.get("feePrice"), symbol)
        root_name = str(product_breakdown.get("feeName") or "").strip()
        if root_name or root_price:
            product_breakdown_parts.append(" ".join(part for part in (root_name, root_price) if part).strip())
        for sub_fee in product_breakdown.get("subFeeList") or []:
            sub_name = str(sub_fee.get("feeName") or "").strip()
            sub_price = format_price(sub_fee.get("feePrice"), symbol)
            if sub_name or sub_price:
                product_breakdown_parts.append(" ".join(part for part in (sub_name, sub_price) if part).strip())
    product_breakdown_text = "\n".join(product_breakdown_parts)

    expanded_lines = [
        f"Order ID: {data.get('orderSn') or ''}".strip(),
        f"Order Status: {data.get('orderStatusDesc') or ''}".strip(),
        f"Order Created Time: {data.get('createTimeStr') or ''}".strip(),
        f"Expected Delivery Time: {data.get('deliveryTime') or ''}".strip(),
        "",
        "Menu details",
        expanded_items_text,
        "",
        f"Product breakdown: {product_breakdown_parts[0]}".strip() if product_breakdown_parts else "",
        *product_breakdown_parts[1:],
        f"Consumer Tax: {fee_map.get('consumer tax(+)', '')}".strip() if fee_map.get("consumer tax(+)") else "",
        f"Estimated Revenue: {fee_map.get('Estimated revenue', '')}".strip() if fee_map.get("Estimated revenue") else "",
        f"Revenue Before Tax: {fee_map.get('revenue before tax', '')}".strip() if fee_map.get("revenue before tax") else "",
        f"Delivery Fee: {format_price(data.get('deliveryPrice'), symbol)}".strip() if data.get("deliveryPrice") is not None else "",
        f"Packing Charges: {format_price(data.get('packingCharges'), symbol)}".strip() if data.get("packingCharges") is not None else "",
        f"Tableware Fee: {format_price(data.get('tablewarePrice'), symbol)}".strip() if data.get("tablewarePrice") is not None else "",
        f"Fixed Price: {format_price(data.get('fixedPrice'), symbol)}".strip() if data.get("fixedPrice") is not None else "",
        f"Notes: {data.get('remark') or ''}".strip(),
        f"Merchant Promotions: {promotion_text}".strip() if promotion_text else "",
        "",
        "Delivery information",
        f"Delivery Mode: {'Third-party delivery' if delivery.get('deliveryType') == 1 else ''}".strip() if delivery.get("deliveryType") is not None else "",
        f"Courier Name: {delivery.get('deliveryName') or ''}".strip(),
        f"Courier Phone: {delivery.get('deliveryPhone') or ''}".strip(),
        "",
        "Recipient information",
        f"Recipient Name: {recipient.get('consigneeName') or ''}".strip(),
        f"Recipient Phone: {recipient.get('consigneeTelMask') or ''}".strip(),
        f"Recipient Address: {recipient.get('consigneeFullAddress') or ''}".strip(),
        f"Doorplate Number: {recipient.get('consigneeHouseNumber') or ''}".strip(),
        f"Postal Code: {recipient.get('consigneeZipCode') or ''}".strip(),
    ]
    expanded_detail = "\n".join(line for line in expanded_lines if line is not None).strip()
    modal_text = modal_text.strip()
    if modal_text:
        expanded_detail = f"{expanded_detail}\n\nModal Snapshot\n{modal_text}".strip()

    delivery_mode = ""
    if delivery.get("deliveryType") == 1:
        delivery_mode = "Third-party delivery"
    elif delivery.get("deliveryType") not in (None, ""):
        delivery_mode = str(delivery.get("deliveryType"))

    return {
        "Product Image URLs": product_image_urls,
        "Order Status": data.get("orderStatusDesc") or "",
        "Order Created Time": data.get("createTimeStr") or "",
        "Expected Delivery Time": data.get("deliveryTime") or "",
        "Delivery Mode": delivery_mode,
        "Courier Name": delivery.get("deliveryName") or "",
        "Courier Phone": delivery.get("deliveryPhone") or "",
        "Recipient Name": recipient.get("consigneeName") or "",
        "Recipient Phone": recipient.get("consigneeTelMask") or "",
        "Recipient Address": recipient.get("consigneeFullAddress") or "",
        "Doorplate Number": recipient.get("consigneeHouseNumber") or "",
        "Postal Code": recipient.get("consigneeZipCode") or "",
        "Notes": data.get("remark") or "",
        "Merchant Promotions": promotion_text,
        "Product Breakdown": product_breakdown_text,
        "Consumer Tax": fee_map.get("consumer tax(+)", ""),
        "Estimated Revenue": fee_map.get("Estimated revenue", ""),
        "Revenue Before Tax": fee_map.get("revenue before tax", ""),
        "Delivery Fee": format_price(data.get("deliveryPrice"), symbol),
        "Packing Charges": format_price(data.get("packingCharges"), symbol),
        "Tableware Fee": format_price(data.get("tablewarePrice"), symbol),
        "Fixed Price": format_price(data.get("fixedPrice"), symbol),
        "Order Items JSON": json.dumps(order_items, ensure_ascii=False),
        "Order Items Text": order_items_text,
        "Expanded Order Detail": expanded_detail,
        "Fee Breakdown JSON": json.dumps(fees, ensure_ascii=False),
        "Promotion Detail JSON": json.dumps(promotion_items, ensure_ascii=False),
        "Delivery Detail JSON": json.dumps(delivery, ensure_ascii=False),
        "Recipient Detail JSON": json.dumps(recipient, ensure_ascii=False),
        "Order Detail JSON": json.dumps(data, ensure_ascii=False),
    }


async def close_order_detail_modal(page) -> None:
    selectors = (
        ".ant-modal-close",
        ".ant-modal-wrap .ant-modal-close",
        "button[aria-label='Close']",
        "[aria-label='Close']",
        ".ant-modal button[aria-label='Close']",
        ".ant-modal-confirm-btns button",
    )
    for _ in range(3):
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible(timeout=600):
                    await locator.click(force=True, timeout=1_500)
                    await page.wait_for_timeout(500)
                    if await page.locator(".ant-modal-wrap, .ant-modal-mask").count() == 0:
                        return
            except Exception:
                pass
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)
        except Exception:
            pass
        try:
            still_visible = await page.locator(".ant-modal-wrap, .ant-modal-mask").first.is_visible(timeout=600)
        except Exception:
            still_visible = False
        if not still_visible:
            return

    try:
        await page.evaluate(
            """
            () => {
              document.querySelectorAll('.ant-modal-wrap, .ant-modal-mask').forEach((node) => {
                node.style.pointerEvents = 'none';
                node.style.display = 'none';
                node.setAttribute('aria-hidden', 'true');
              });
              document.body.classList.remove('ant-scrolling-effect');
              document.body.style.overflow = '';
              document.body.style.width = '';
            }
            """
        )
        await page.wait_for_timeout(300)
    except Exception:
        pass


async def click_order_detail(page, order_id: str) -> dict[str, Any]:
    await close_order_detail_modal(page)
    link = page.locator("table tbody tr a", has_text=order_id).first
    if await link.count() == 0:
        link = page.locator(f"text={order_id}").first
    async with page.expect_response(
        lambda response: ORDER_DETAIL_API in response.url and response.status == 200,
        timeout=30_000,
    ) as response_info:
        await link.click(force=True)
    response = await response_info.value
    payload = await response.json()

    modal_text = ""
    try:
        modal = page.locator(".ant-modal, [role='dialog']").filter(has_text="Order details").first
        if await modal.count() > 0 and await modal.is_visible(timeout=5_000):
            expanders = modal.locator(".ant-collapse-header")
            for index in range(await expanders.count()):
                try:
                    await expanders.nth(index).click(force=True)
                    await page.wait_for_timeout(300)
                except Exception:
                    pass
            modal_text = await modal.inner_text(timeout=5_000)
    except Exception:
        modal_text = ""
    await close_order_detail_modal(page)
    return extract_order_detail(payload, modal_text)


async def main() -> None:
    args = parse_args()
    region = normalize_region(args.region)
    credentials = load_credentials(region, args)
    since_date = datetime.now().date() - timedelta(days=args.days)
    profile = DATA / "browser_profiles" / region.profile_name
    profile.mkdir(parents=True, exist_ok=True)

    from playwright.async_api import async_playwright

    reviews: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    branch_stats: list[dict[str, Any]] = []

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            str(profile),
            channel="msedge",
            headless=args.headless,
            viewport={"width": 1920, "height": 1080},
        )
        master_page = context.pages[0] if context.pages else await context.new_page()
        await master_page.goto(region.branch_url, wait_until="domcontentloaded", timeout=45_000)
        await master_page.wait_for_timeout(3_500)
        await ensure_logged_in(
            master_page,
            region,
            *credentials,
            phone_code=args.phone_code,
            manual_login=args.manual_login,
        )
        if "master/login" in master_page.url or "/master/branchStore/storeList" not in master_page.url:
            await master_page.goto(region.branch_url, wait_until="domcontentloaded", timeout=45_000)
            await master_page.wait_for_timeout(3_500)

        branches = await collect_branch_rows(master_page)
        selected = branches[args.start_index :]
        if args.limit:
            selected = selected[: args.limit]
        print(
            json.dumps(
                {
                    "status": "branches_loaded",
                    "region": region.code,
                    "branch_count": len(branches),
                    "selected_count": len(selected),
                    "start_index": args.start_index,
                    "limit": args.limit,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

        for branch in selected:
            if len(reviews) >= args.max_reviews:
                break
            branch_page = None
            branch_review_count = 0
            print(
                json.dumps(
                    {
                        "status": "branch_start",
                        "region": region.code,
                        "branch_id": branch.get("branch_id"),
                        "branch": branch.get("branch_name"),
                        "total_reviews_so_far": len(reviews),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            try:
                await master_page.goto(region.branch_url, wait_until="domcontentloaded", timeout=45_000)
                await master_page.wait_for_timeout(1_000)
                branch_page = await enter_branch(master_page, branch)
                await open_ratings_page(branch_page)

                stop_branch = False
                seen_order_ids: set[str] = set()
                while len(reviews) < args.max_reviews:
                    rows = await extract_reviews(branch_page)
                    if not rows:
                        break
                    for row in rows:
                        order_id = row["Order ID"]
                        if order_id in seen_order_ids:
                            continue
                        seen_order_ids.add(order_id)
                        review_date = parse_review_date(row["Review time"])
                        if review_date and review_date.date() < since_date:
                            stop_branch = True
                            continue
                        enriched = {
                            "Platform": "Hungry Panda",
                            "Country": region.country,
                            "Region": region.code,
                            "City": branch["city"],
                            "Branch ID": branch["branch_id"],
                            "Branch": branch["branch_name"],
                            "Review": row["Review"],
                            "Review contents": row["Review contents"],
                            "Image URLs": row.get("Image URLs", ""),
                            "Order ID": order_id,
                            "Review time": row["Review time"],
                            "Operation": row["Operation"],
                            "Child ratings": json.dumps(row["child_rating"], ensure_ascii=False),
                        }
                        try:
                            enriched.update(await click_order_detail(branch_page, order_id))
                        except Exception as detail_exc:
                            enriched.update(
                                {
                                    "Product Image URLs": "",
                                    "Order Status": "",
                                    "Order Created Time": "",
                                    "Expected Delivery Time": "",
                                    "Delivery Mode": "",
                                    "Courier Name": "",
                                    "Courier Phone": "",
                                    "Recipient Name": "",
                                    "Recipient Phone": "",
                                    "Recipient Address": "",
                                    "Doorplate Number": "",
                                    "Postal Code": "",
                                    "Notes": "",
                                    "Merchant Promotions": "",
                                    "Product Breakdown": "",
                                    "Consumer Tax": "",
                                    "Estimated Revenue": "",
                                    "Revenue Before Tax": "",
                                    "Delivery Fee": "",
                                    "Packing Charges": "",
                                    "Tableware Fee": "",
                                    "Fixed Price": "",
                                    "Order Items JSON": "",
                                    "Order Items Text": "",
                                    "Expanded Order Detail": "",
                                    "Fee Breakdown JSON": "",
                                    "Promotion Detail JSON": "",
                                    "Delivery Detail JSON": "",
                                    "Recipient Detail JSON": "",
                                    "Order Detail JSON": "",
                                }
                            )
                            errors.append(
                                {
                                    "Branch ID": branch.get("branch_id"),
                                    "Branch": branch.get("branch_name"),
                                    "order_id": order_id,
                                    "error": f"order detail: {detail_exc}",
                                }
                            )
                        reviews.append(enriched)
                        branch_review_count += 1
                        if len(reviews) >= args.max_reviews:
                            break
                    if stop_branch or len(reviews) >= args.max_reviews:
                        break
                    if not await click_next_review_page(branch_page):
                        break
            except Exception as exc:
                errors.append(
                    {
                        "Branch ID": branch.get("branch_id"),
                        "Branch": branch.get("branch_name"),
                        "error": str(exc),
                    }
                )
            finally:
                branch_stats.append(
                    {
                        "Branch ID": branch.get("branch_id"),
                        "Branch": branch.get("branch_name"),
                        "Country": region.country,
                        "Region": region.code,
                        "City": branch.get("city"),
                        "review_count": branch_review_count,
                    }
                )
                print(
                    json.dumps(
                        {
                            "status": "branch_done",
                            "region": region.code,
                            "branch_id": branch.get("branch_id"),
                            "branch": branch.get("branch_name"),
                            "branch_review_count": branch_review_count,
                            "total_reviews_so_far": len(reviews),
                            "error_count": len(errors),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                if branch_page is not None and branch_page is not master_page:
                    await branch_page.close()

        await context.close()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "region": region.code,
        "country": region.country,
        "branch_url": region.branch_url,
        "since_date": since_date.isoformat(),
        "max_reviews": args.max_reviews,
        "start_index": args.start_index,
        "branch_limit": args.limit,
        "branch_count": len(branch_stats),
        "branches": branch_stats,
        "review_count": len(reviews),
        "reviews": reviews,
        "errors": errors,
    }
    json_path, csv_path = export_results(args.output_prefix, payload)
    print(
        json.dumps(
            {
                "json": str(json_path),
                "csv": str(csv_path),
                "review_count": len(reviews),
                "branch_count": len(branch_stats),
                "errors": errors[:5],
                "sample": reviews[:5],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
