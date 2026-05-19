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
CREDENTIALS_FILE = DATA / "mfood_credentials.local.json"
EXPORTS = ROOT / "exports" / "mfood"
LOGIN_URL = "https://merchant.o2o.mfoodapp.com/#/login"
APPRAISE_URL = "https://merchant.o2o.mfoodapp.com/#/appraise/tackout"


@dataclass(frozen=True)
class AccountConfig:
    key: str
    label: str
    country_code: str
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
        label="Mfood Main",
        country_code="mo",
        profile_name="mfood_default",
    ),
    "tianshenxiang": AccountConfig(
        key="tianshenxiang",
        label="Mfood TianShenXiang",
        country_code="mo",
        profile_name="mfood_tianshenxiang",
    ),
}


FIELDS = [
    "Platform",
    "Country",
    "Country Code",
    "Account",
    "Store",
    "Review Time",
    "Reviewer Name",
    "Rating",
    "Taste Rating",
    "Package Rating",
    "Reply Status",
    "Review Content",
    "Top Status",
    "Order ID",
    "Image URLs",
    "Order Items JSON",
    "Order Items Text",
    "Expanded Order Detail",
    "Order Detail JSON",
    "Source",
    "Raw JSON",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mfood weekly review collector")
    parser.add_argument("--account", default="default", choices=sorted(ACCOUNTS), help="Mfood account key")
    parser.add_argument("--days", type=int, default=7, help="Only keep reviews in the last N days")
    parser.add_argument("--max-reviews", type=int, default=100, help="Maximum reviews to export")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum pages to iterate")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--manual-login", action="store_true", help="Allow manual login if automatic login fails")
    parser.add_argument("--username", default="", help="Override username")
    parser.add_argument("--password", default="", help="Override password")
    parser.add_argument("--output-prefix", default="", help="Optional output file prefix")
    parser.add_argument("--portal-url", default=APPRAISE_URL, help="Review page URL")
    parser.add_argument("--login-url", default=LOGIN_URL, help="Login page URL")
    parser.add_argument("--platform-label", default="Mfood", help="Platform label in exported rows")
    parser.add_argument("--country-label", default="China Macau", help="Country label in exported rows")
    parser.add_argument("--country-code", default="", help="Country code in exported rows")
    parser.add_argument("--file-tag", default="mfood", help="File name tag for output")
    parser.add_argument("--export-dir", default="", help="Override export directory")
    parser.add_argument("--profile-name", default="", help="Override Playwright persistent profile name")
    parser.add_argument("--storage-state", default="", help="Optional Playwright storage_state JSON path for restored login sessions")
    return parser.parse_args()


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def can_wait_for_manual_input() -> bool:
    if os.getenv("GLOBALREVIEWOPS_NONINTERACTIVE") == "1":
        return False
    return bool(getattr(sys.stdin, "isatty", lambda: False)())


def default_storage_state_path(profile_name: str) -> Path:
    return DATA / "browser_profiles" / f"{profile_name}_storage_state.json"


def _safe_excerpt(text: str, limit: int = 3000) -> str:
    cleaned = clean_text(text)
    cleaned = re.sub(r"[\w.+-]+@[\w.-]+", "[email]", cleaned)
    cleaned = re.sub(r"\b\d{6,}\b", "[number]", cleaned)
    return cleaned[:limit]


async def classify_page_state(page) -> dict[str, str]:
    try:
        body = await page.locator("body").inner_text(timeout=2_000)
    except Exception:
        body = ""
    try:
        title = await page.title()
    except Exception:
        title = ""
    blocker = classify_blocker_text(body)
    if blocker:
        if "permission gate" in blocker:
            return {"type": "permission", "message": blocker}
        if "captcha" in blocker.lower() or "otp" in blocker.lower():
            return {"type": "captcha_or_otp", "message": blocker}
        if "initial-password" in blocker:
            return {"type": "password_change_prompt", "message": blocker}
        return {"type": "manual_gate", "message": blocker}
    text = clean_text(f"{title} {body}")
    if "/login" in page.url or "#/login" in page.url:
        return {"type": "login_required", "message": "Mfood login has not completed in this browser session."}
    if any(token in text for token in ("訂單管理", "订单管理", "評價管理", "评价管理", "外賣評價", "外卖评价")):
        return {"type": "review_menu_visible", "message": "Mfood order/evaluation menu is visible."}
    return {"type": "unknown_page_state", "message": "Mfood page state could not be classified from the visible page."}


async def write_diagnostics(page, config: AccountConfig, reason: str, export_dir: Path, output_prefix: str = "") -> dict[str, str]:
    diag_dir = export_dir / "_diagnostics" / config.key
    diag_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{output_prefix}_" if output_prefix else ""
    base = diag_dir / f"{prefix}mfood_{config.key}_{stamp}"
    try:
        body = await page.locator("body").inner_text(timeout=2_000)
    except Exception:
        body = ""
    try:
        title = await page.title()
    except Exception:
        title = ""
    screenshot_path = base.with_suffix(".png")
    screenshot_value = str(screenshot_path)
    try:
        await page.screenshot(path=str(screenshot_path), full_page=True)
    except Exception:
        screenshot_value = ""
    state = await classify_page_state(page)
    json_path = base.with_suffix(".json")
    payload = {
        "platform": "Mfood",
        "account_key": config.key,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reason": reason,
        "state": state,
        "url": page.url,
        "title": title,
        "text_excerpt": _safe_excerpt(body),
        "screenshot": screenshot_value,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"diagnostics_json": str(json_path), "diagnostics_screenshot": screenshot_value}


def classify_blocker_text(body: str) -> str:
    text = clean_text(body)
    if not text:
        return ""
    if any(token in text for token in ("初始密碼", "初始密码", "修改密碼", "修改密码")):
        return "Mfood manual gate required: initial-password change prompt blocks read-only navigation; do not modify password in automation."
    if any(token in text for token in ("驗證碼", "验证码", "OTP", "captcha", "Captcha")):
        return "Mfood manual gate required: captcha/OTP verification blocks server-side collection."
    if any(token in text for token in ("門店管理", "门店管理", "權限管理", "权限管理")) and not any(
        token in text for token in ("訂單管理", "订单管理", "評價管理", "评价管理", "外賣評價", "外卖评价")
    ):
        return "Mfood account permission gate: order/evaluation menu is not visible for this account after login."
    return ""


def parse_review_time(value: str) -> datetime | None:
    raw = clean_text(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def load_credentials(args: argparse.Namespace, config: AccountConfig) -> tuple[str, str]:
    if args.username and args.password:
        return args.username, args.password

    env_prefix = f"MFOOD_{config.key.upper()}"
    username = os.getenv(f"{env_prefix}_USERNAME") or os.getenv("MFOOD_USERNAME") or ""
    password = os.getenv(f"{env_prefix}_PASSWORD") or os.getenv("MFOOD_PASSWORD") or ""
    if username and password:
        return username, password

    if CREDENTIALS_FILE.exists():
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8-sig"))
        account_data = data.get(config.key) or {}
        username = account_data.get("username") or data.get("username") or ""
        password = account_data.get("password") or data.get("password") or ""
    return str(username or ""), str(password or "")


def _match_col(headers: list[str], candidates: tuple[str, ...], default: int) -> int:
    normalized_headers = [clean_text(item).lower() for item in headers]
    for idx, header in enumerate(normalized_headers):
        if any(token.lower() in header for token in candidates):
            return idx
    return default


async def _optional_click(page, texts: tuple[str, ...], timeout: int = 1200) -> bool:
    for text in texts:
        try:
            locator = page.get_by_text(text, exact=True).first
            if await locator.count() > 0 and await locator.is_visible(timeout=timeout):
                await locator.click(force=True)
                await page.wait_for_timeout(500)
                return True
        except Exception:
            continue
    return False


async def close_startup_dialogs(page) -> None:
    async def click_visible_in_dialog(texts: tuple[str, ...]) -> bool:
        clicked = await page.evaluate(
            """targets => {
                const isVisible = el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                };
                for (const button of Array.from(document.querySelectorAll('.el-dialog button'))) {
                    const text = (button.innerText || '').replace(/\\s+/g, ' ').trim();
                    if (isVisible(button) && targets.includes(text)) {
                        button.click();
                        return true;
                    }
                }
                return false;
            }""",
            list(texts),
        )
        if clicked:
            await page.wait_for_timeout(800)
            return True
        return False

    for _ in range(3):
        body = ""
        try:
            body = await page.locator("body").inner_text(timeout=1500)
        except Exception:
            body = ""
        if any(token in body for token in ("初始密碼", "初始密码", "修改密碼", "修改密码")):
            if await click_visible_in_dialog(("取消", "稍後", "稍后", "Cancel")):
                continue
            try:
                button = page.locator(".el-dialog:visible .el-dialog__headerbtn").first
                if await button.count() > 0 and await button.is_visible(timeout=500):
                    await button.click(force=True)
                    await page.wait_for_timeout(800)
                    continue
            except Exception:
                pass
        if "選擇店鋪" in body or "选择店铺" in body:
            try:
                clicked_store = await page.evaluate(
                    """() => {
                        const isVisible = el => {
                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);
                            return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                        };
                        for (const el of Array.from(document.querySelectorAll('.el-dialog *'))) {
                            const text = (el.innerText || '').replace(/\\s+/g, ' ').trim();
                            if (isVisible(el) && text.includes('喜茶')) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }"""
                )
                if clicked_store:
                    await page.wait_for_timeout(1500)
                    return
            except Exception:
                pass
        break


async def ensure_logged_in(page, username: str, password: str, manual_login: bool, portal_url: str, login_url: str) -> None:
    await page.goto(portal_url, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(2_000)

    if "/login" not in page.url and "#/login" not in page.url:
        return

    await page.goto(login_url, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(1_500)

    if not username or not password:
        if manual_login:
            if can_wait_for_manual_input():
                print("[login] waiting for manual login...")
                await asyncio.to_thread(input)
                return
            raise RuntimeError("Mfood manual gate required: credentials are missing in non-interactive server mode.")
        raise RuntimeError(f"Mfood credentials missing; provide args/env/or {CREDENTIALS_FILE}")

    username_candidates = (
        "#username",
        "input[name='username']",
        "input[placeholder*='账号']",
        "input[placeholder*='帳號']",
        "input[placeholder*='Account']",
        "input[type='text']",
    )
    password_candidates = (
        "#password",
        "input[name='password']",
        "input[placeholder*='密码']",
        "input[placeholder*='密碼']",
        "input[placeholder*='Password']",
        "input[type='password']",
    )

    username_filled = False
    for selector in username_candidates:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=800):
                await locator.fill(username)
                username_filled = True
                break
        except Exception:
            continue
    if not username_filled:
        raise RuntimeError("Mfood login username input not found.")

    password_filled = False
    for selector in password_candidates:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=800):
                await locator.fill(password)
                password_filled = True
                break
        except Exception:
            continue
    if not password_filled:
        raise RuntimeError("Mfood login password input not found.")

    submitted = await _optional_click(page, ("登录", "登錄", "登 录", "登 錄", "登\xa0錄", "登入", "Sign in", "Login"), timeout=1_200)
    if not submitted:
        try:
            primary = page.locator("button.el-button--primary").first
            if await primary.count() > 0 and await primary.is_visible(timeout=1_000):
                await primary.click(force=True)
                submitted = True
        except Exception:
            submitted = False
    if not submitted:
        try:
            await page.keyboard.press("Enter")
        except Exception:
            pass

    await page.wait_for_timeout(5_000)
    try:
        body = await page.locator("body").inner_text(timeout=2000)
    except Exception:
        body = ""
    if any(token in body for token in ("登錄信息有誤", "登录信息有误", "重新登錄", "重新登录", "incorrect", "invalid")):
        raise RuntimeError("Mfood login rejected by platform; verify account/password or account region.")
    if "/login" in page.url or "#/login" in page.url:
        if manual_login:
            if can_wait_for_manual_input():
                print("[login] auto-login not completed, waiting for manual login...")
                await asyncio.to_thread(input)
                await page.wait_for_timeout(1_000)
                if "/login" not in page.url and "#/login" not in page.url:
                    return
            raise RuntimeError("Mfood manual gate required: login did not complete in non-interactive server mode.")
        raise RuntimeError("Mfood login did not complete; maybe captcha/OTP/manual confirmation required.")
    await close_startup_dialogs(page)


async def open_review_page(page, portal_url: str) -> None:
    await close_startup_dialogs(page)
    await page.goto(portal_url, wait_until="domcontentloaded", timeout=45_000)
    await page.wait_for_timeout(1_500)
    await close_startup_dialogs(page)
    await _optional_click(page, ("订单管理", "訂單管理", "Order Management"))
    await _optional_click(page, ("评价管理", "評價管理", "外卖评价", "外賣評價", "Ratings", "Reviews"))
    await page.wait_for_timeout(1_200)
    table = page.locator("table tbody tr").first
    try:
        await table.wait_for(timeout=20_000)
    except Exception as exc:
        try:
            body = await page.locator("body").inner_text(timeout=2000)
        except Exception:
            body = ""
        blocker = classify_blocker_text(body)
        if blocker:
            raise RuntimeError(blocker) from exc
        login_like = False
        for selector in (
            "#username",
            "#password",
            "input[type='password']",
            "input[placeholder*='账号']",
            "input[placeholder*='帳號']",
            "input[placeholder*='password']",
        ):
            try:
                node = page.locator(selector).first
                if await node.count() > 0 and await node.is_visible(timeout=500):
                    login_like = True
                    break
            except Exception:
                continue
        if login_like:
            raise RuntimeError("Mfood page remains on login state; retry with --manual-login or refresh stored session.") from exc
        raise


async def parse_table_headers(page) -> list[str]:
    headers: list[str] = []
    ths = page.locator("table thead th")
    count = await ths.count()
    for idx in range(count):
        try:
            headers.append(clean_text(await ths.nth(idx).inner_text()))
        except Exception:
            headers.append("")
    return headers


async def extract_image_urls_from_dialog(page) -> list[str]:
    urls = await page.evaluate(
        """() => {
            const overlays = Array.from(document.querySelectorAll('.el-dialog__wrapper,.el-drawer__wrapper,.ant-modal,.ant-drawer,.ivu-modal-wrap'))
                .filter(el => getComputedStyle(el).display !== 'none');
            const target = overlays.length ? overlays[overlays.length - 1] : document.body;
            const srcs = Array.from(target.querySelectorAll('img'))
                .map(img => (img.currentSrc || img.src || '').trim())
                .filter(Boolean)
                .filter(url => /^https?:\\/\\//.test(url));
            return Array.from(new Set(srcs));
        }"""
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls or []:
        lowered = str(url).lower()
        if "avatar" in lowered or "profile" in lowered:
            continue
        if url in seen:
            continue
        seen.add(url)
        deduped.append(str(url))
    return deduped


async def close_overlay(page) -> None:
    clicked = await _optional_click(page, ("关闭", "關閉", "Close", "X"), timeout=800)
    if clicked:
        return
    for selector in (
        ".el-dialog__wrapper .el-dialog__close",
        ".el-drawer__wrapper .el-icon-close",
        ".ant-modal-close",
        ".ant-drawer-close",
    ):
        try:
            node = page.locator(selector).first
            if await node.count() > 0 and await node.is_visible(timeout=600):
                await node.click(force=True)
                await page.wait_for_timeout(300)
                return
        except Exception:
            continue
    try:
        await page.keyboard.press("Escape")
    except Exception:
        pass
    await page.wait_for_timeout(250)


async def open_image_dialog_and_extract(row, page) -> list[str]:
    link = row.get_by_text(re.compile("查看图片|查看圖片|图片|圖片|Image|Photo", re.IGNORECASE)).first
    try:
        if await link.count() == 0:
            return []
        await link.click(force=True, timeout=1_500)
        await page.wait_for_timeout(400)
        urls = await extract_image_urls_from_dialog(page)
        await close_overlay(page)
        return urls
    except Exception:
        return []


def _extract_order_items_from_text(detail_text: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in str(detail_text or "").splitlines()]
    lines = [line for line in lines if line]
    items: list[dict[str, Any]] = []
    price_pattern = re.compile(r"[¥$₩]?\s*\d+(?:\.\d+)?")
    for idx, line in enumerate(lines):
        if any(token in line for token in ("商品信息", "商品名稱", "商品名称")):
            continue
        if "规格" in line or "規格" in line or "属性" in line or "屬性" in line:
            continue
        if len(line) < 2:
            continue
        if line.isdigit():
            continue
        if line.startswith(("收货人信息", "收貨人信息", "联系电话", "聯繫電話", "买家备注", "買家備註", "餐具数量", "餐具數量")):
            continue
        if not re.search(r"[\u4e00-\u9fffA-Za-z]", line):
            continue
        quantity = ""
        price = ""
        if idx + 1 < len(lines) and lines[idx + 1].isdigit():
            quantity = lines[idx + 1]
        if idx + 1 < len(lines) and price_pattern.search(lines[idx + 1]):
            price = price_pattern.search(lines[idx + 1]).group(0)
        if idx + 2 < len(lines) and not quantity and lines[idx + 2].isdigit():
            quantity = lines[idx + 2]
        if idx + 2 < len(lines) and not price and price_pattern.search(lines[idx + 2]):
            price = price_pattern.search(lines[idx + 2]).group(0)
        if quantity or price:
            items.append({"name": line, "quantity": quantity, "price": price})
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        key = f"{item.get('name')}|{item.get('quantity')}|{item.get('price')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _extract_order_id(detail_text: str) -> str:
    text = str(detail_text or "")
    match = re.search(r"(订单号|訂單號|Order\\s*ID)[:：\\s]*([0-9A-Za-z-]{6,})", text, re.IGNORECASE)
    if match:
        return clean_text(match.group(2))
    fallback = re.search(r"\b\d{8,}\b", text)
    return clean_text(fallback.group(0)) if fallback else ""


async def open_order_detail_and_extract(row, page) -> tuple[str, list[dict[str, Any]], str]:
    link = row.get_by_text(re.compile("订单详情|訂單詳情|Order\\s*Detail", re.IGNORECASE)).first
    if await link.count() == 0:
        return "", [], ""
    try:
        await link.click(force=True, timeout=2_000)
        await page.wait_for_timeout(500)
    except Exception:
        return "", [], ""

    detail_text = await page.evaluate(
        """() => {
            const overlays = Array.from(document.querySelectorAll('.el-dialog__wrapper,.el-drawer__wrapper,.ant-modal,.ant-drawer,.ivu-modal-wrap'))
                .filter(el => getComputedStyle(el).display !== 'none');
            const target = overlays.length ? overlays[overlays.length - 1] : document.body;
            return (target.innerText || '').trim();
        }"""
    )
    items = _extract_order_items_from_text(detail_text)
    order_id = _extract_order_id(detail_text)
    await close_overlay(page)
    return order_id, items, detail_text


async def goto_next_page(page) -> bool:
    selectors = (
        ".el-pagination button.btn-next:not([disabled])",
        ".el-pagination .btn-next:not(.is-disabled)",
        ".ant-pagination-next:not(.ant-pagination-disabled)",
        ".ivu-page-next",
    )
    for selector in selectors:
        try:
            node = page.locator(selector).first
            if await node.count() > 0 and await node.is_visible(timeout=700):
                await node.click(force=True)
                await page.wait_for_timeout(1_000)
                return True
        except Exception:
            continue
    return False


async def collect_reviews(page, config: AccountConfig, args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[str]]:
    cutoff = datetime.now() - timedelta(days=max(1, args.days))
    reviews: list[dict[str, Any]] = []
    errors: list[str] = []
    page_no = 1

    for _ in range(max(1, args.max_pages)):
        headers = await parse_table_headers(page)
        rows = page.locator("table tbody tr")
        row_count = await rows.count()
        if row_count == 0:
            break

        idx_time = _match_col(headers, ("评", "評論", "review time", "time"), 0)
        idx_name = _match_col(headers, ("用户", "用戶", "customer", "name"), 1)
        idx_rating = _match_col(headers, ("总评", "總體", "overall", "rating"), 2)
        idx_taste = _match_col(headers, ("口味", "taste"), 3)
        idx_reply = _match_col(headers, ("回复", "回覆", "reply"), 4)
        idx_pkg = _match_col(headers, ("包装", "包裝", "package"), 5)
        idx_content = _match_col(headers, ("详情", "詳情", "content", "review"), 6)
        idx_top = _match_col(headers, ("置顶", "置頂", "top"), 7)

        oldest_on_page: datetime | None = None
        for row_index in range(row_count):
            if len(reviews) >= args.max_reviews:
                return reviews, errors

            row = rows.nth(row_index)
            cells = row.locator("td")
            cell_count = await cells.count()
            cell_values: list[str] = []
            for col in range(cell_count):
                try:
                    cell_values.append(clean_text(await cells.nth(col).inner_text()))
                except Exception:
                    cell_values.append("")
            if not cell_values:
                continue

            review_time = cell_values[idx_time] if idx_time < len(cell_values) else ""
            parsed_time = parse_review_time(review_time)
            if parsed_time:
                oldest_on_page = parsed_time if oldest_on_page is None else min(oldest_on_page, parsed_time)
                if parsed_time < cutoff:
                    continue

            reviewer = cell_values[idx_name] if idx_name < len(cell_values) else ""
            overall = cell_values[idx_rating] if idx_rating < len(cell_values) else ""
            taste = cell_values[idx_taste] if idx_taste < len(cell_values) else ""
            reply_status = cell_values[idx_reply] if idx_reply < len(cell_values) else ""
            package = cell_values[idx_pkg] if idx_pkg < len(cell_values) else ""
            review_content = cell_values[idx_content] if idx_content < len(cell_values) else ""
            top_status = cell_values[idx_top] if idx_top < len(cell_values) else ""

            image_urls = await open_image_dialog_and_extract(row, page)
            order_id, order_items, detail_text = await open_order_detail_and_extract(row, page)

            review_record = {
                "Platform": args.platform_label,
                "Country": args.country_label,
                "Country Code": args.country_code or config.country_code,
                "Account": config.key,
                "Store": "",
                "Review Time": review_time,
                "Reviewer Name": reviewer,
                "Rating": overall,
                "Taste Rating": taste,
                "Package Rating": package,
                "Reply Status": reply_status,
                "Review Content": review_content,
                "Top Status": top_status,
                "Order ID": order_id,
                "Image URLs": "|".join(image_urls),
                "Order Items JSON": json.dumps(order_items, ensure_ascii=False),
                "Order Items Text": "\n".join(
                    f"{item.get('name','')} x{item.get('quantity','')} {item.get('price','')}".strip()
                    for item in order_items
                ),
                "Expanded Order Detail": detail_text,
                "Order Detail JSON": json.dumps({"order_id": order_id, "items": order_items}, ensure_ascii=False),
                "Source": args.portal_url,
                "Raw JSON": json.dumps(
                    {
                        "headers": headers,
                        "row_values": cell_values,
                    },
                    ensure_ascii=False,
                ),
            }
            reviews.append(review_record)

        if len(reviews) >= args.max_reviews:
            break

        if oldest_on_page and oldest_on_page < cutoff:
            break

        has_next = await goto_next_page(page)
        if not has_next:
            break
        page_no += 1
        await page.wait_for_timeout(700)

    return reviews, errors


def write_exports(config: AccountConfig, reviews: list[dict[str, Any]], output_prefix: str, args: argparse.Namespace) -> tuple[Path, Path]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{output_prefix}_" if output_prefix else ""
    export_dir = Path(args.export_dir).expanduser() if args.export_dir else config.export_dir
    export_dir = export_dir if export_dir.is_absolute() else (ROOT / export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    file_tag = clean_text(args.file_tag).lower().replace(" ", "_") or "mfood"
    json_path = export_dir / f"{prefix}{file_tag}_{config.key}_weekly_reviews_{stamp}.json"
    csv_path = export_dir / f"{prefix}{file_tag}_{config.key}_weekly_reviews_{stamp}.csv"

    payload = {
        "platform": args.platform_label,
        "country": args.country_label,
        "country_code": args.country_code or config.country_code,
        "account": config.key,
        "review_count": len(reviews),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reviews": reviews,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in reviews:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    return json_path, csv_path


async def run() -> dict[str, Any]:
    from playwright.async_api import async_playwright

    args = parse_args()
    config = ACCOUNTS[args.account]
    username, password = load_credentials(args, config)
    errors: list[str] = []
    reviews: list[dict[str, Any]] = []
    diagnostics: dict[str, str] = {}
    manual_gate_type = ""

    profile_name = clean_text(args.profile_name)
    if not profile_name and clean_text(args.file_tag).lower() not in {"", "mfood"}:
        profile_name = f"{clean_text(args.file_tag).lower()}_{config.key}"
    profile_dir = DATA / "browser_profiles" / profile_name if profile_name else config.profile_dir
    resolved_profile_name = profile_name or config.profile_name
    storage_state = Path(args.storage_state).expanduser() if args.storage_state else default_storage_state_path(resolved_profile_name)
    storage_state = storage_state if storage_state.is_absolute() else (ROOT / storage_state)
    profile_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = None
        try:
            if storage_state.exists():
                browser = await pw.chromium.launch(headless=args.headless)
                context = await browser.new_context(
                    storage_state=str(storage_state),
                    viewport={"width": 1600, "height": 1000},
                    locale="zh-CN",
                    ignore_https_errors=True,
                )
            else:
                context = await pw.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=args.headless,
                    viewport={"width": 1600, "height": 1000},
                    locale="zh-CN",
                    ignore_https_errors=True,
                )
        except Exception as exc:
            fallback_profile = DATA / "browser_profiles" / f"{profile_dir.name}_retry_{os.getpid()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            fallback_profile.mkdir(parents=True, exist_ok=True)
            errors.append(f"persistent profile launch failed, retried with isolated profile: {exc}")
            context = await pw.chromium.launch_persistent_context(
                user_data_dir=str(fallback_profile),
                headless=args.headless,
                viewport={"width": 1600, "height": 1000},
                locale="zh-CN",
                ignore_https_errors=True,
            )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await ensure_logged_in(page, username, password, args.manual_login, args.portal_url, args.login_url)
            await open_review_page(page, args.portal_url)
            reviews, crawl_errors = await collect_reviews(page, config, args)
            errors.extend(crawl_errors)
        except Exception as exc:
            message = str(exc)
            errors.append(message)
            state = await classify_page_state(page)
            manual_gate_type = state.get("type", "")
            export_dir = Path(args.export_dir).expanduser() if args.export_dir else config.export_dir
            export_dir = export_dir if export_dir.is_absolute() else (ROOT / export_dir)
            diagnostics = await write_diagnostics(page, config, message, export_dir, args.output_prefix)
        finally:
            try:
                storage_state.parent.mkdir(parents=True, exist_ok=True)
                await context.storage_state(path=str(storage_state))
            except Exception:
                pass
            await context.close()
            if browser:
                await browser.close()

    if reviews:
        json_path, csv_path = write_exports(config, reviews, args.output_prefix, args)
    else:
        export_dir = Path(args.export_dir).expanduser() if args.export_dir else config.export_dir
        export_dir = export_dir if export_dir.is_absolute() else (ROOT / export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        json_path = export_dir / "mfood_empty.json"
        csv_path = export_dir / "mfood_empty.csv"
        empty_payload = {
            "platform": args.platform_label,
            "country": args.country_label,
            "country_code": args.country_code or config.country_code,
            "account": config.key,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "review_count": 0,
            "store_count": 0,
            "errors": errors,
            "manual_gate_required": any("manual gate" in error.lower() or "permission gate" in error.lower() for error in errors),
            "manual_gate_type": manual_gate_type,
            "diagnostics": diagnostics,
            "storage_state": str(storage_state),
            "retry_suggestions": [
                "先在可视浏览器完成 Mfood 登录，确认订单管理/外卖评价可见后再重跑。",
                "如果只看到门店管理/权限管理，说明账号缺少评价读取权限，需要平台后台授权。",
                "如果出现初始密码修改/验证码/OTP，脚本必须暂停，不能自动修改密码或绕过验证。",
            ],
            "reviews": [],
        }
        json_path.write_text(json.dumps(empty_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            csv.DictWriter(file, fieldnames=FIELDS).writeheader()

    summary = {
        "json": str(json_path),
        "csv": str(csv_path),
        "review_count": len(reviews),
        "store_count": 0,
        "errors": errors,
        "manual_gate_required": any("manual gate" in error.lower() or "permission gate" in error.lower() for error in errors),
        "manual_gate_type": manual_gate_type,
        "diagnostics": diagnostics,
        "storage_state": str(storage_state),
        "sample": reviews[:3],
    }
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> None:
    summary = asyncio.run(run())
    if summary.get("errors"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
