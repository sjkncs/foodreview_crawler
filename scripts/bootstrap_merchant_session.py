from __future__ import annotations

import argparse
import asyncio
import json
import platform
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unified_collector.account_registry import resolve_account  # noqa: E402


DATA = ROOT / "data"


PLATFORM_DEFAULTS = {
    "grabfood": {
        "login_url": "https://merchant.grab.com/en-my",
        "portal_url": "https://merchant.grab.com/portal?source=mrc",
        "success_texts": ("Feedback", "Ratings and reviews", "Ratings & reviews"),
    },
    "mfood": {
        "login_url": "https://merchant.o2o.mfoodapp.com/#/login",
        "portal_url": "https://merchant.o2o.mfoodapp.com/#/appraise/tackout",
        "success_texts": ("订单管理", "訂單管理", "评价管理", "評價管理", "外卖评价", "外賣評價"),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap a read-only merchant browser session and export storage_state.")
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORM_DEFAULTS), help="Platform key")
    parser.add_argument("--account", required=True, help="Account key, for example sg/my_auro/default/tianshenxiang")
    parser.add_argument("--country", default="", help="Optional country code for account-registry lookup")
    parser.add_argument("--headless", action="store_true", help="Run headless; visible mode is recommended for manual gates")
    parser.add_argument("--browser-channel", default="msedge", help="Browser channel on Windows; ignored on Linux if unavailable")
    parser.add_argument("--wait-seconds", type=int, default=0, help="Optional fixed wait before saving, useful with remote VNC")
    parser.add_argument("--storage-state", default="", help="Output Playwright storage_state JSON")
    parser.add_argument("--portal-url", default="", help="Override portal URL")
    parser.add_argument("--login-url", default="", help="Override login URL")
    return parser.parse_args()


def default_profile_name(platform_key: str, account_key: str) -> str:
    if platform_key == "grabfood":
        return f"grabfood_{account_key}"
    if platform_key == "mfood":
        return f"mfood_{account_key}"
    return f"{platform_key}_{account_key}"


def default_storage_state(platform_key: str, account_key: str) -> Path:
    return DATA / "browser_profiles" / f"{default_profile_name(platform_key, account_key)}_storage_state.json"


def default_browser_channel(value: str) -> str:
    if platform.system().lower() != "windows":
        return ""
    return value.strip()


async def visible_text(page) -> str:
    try:
        return await page.locator("body").inner_text(timeout=2000)
    except Exception:
        return ""


async def classify_ready(page, success_texts: tuple[str, ...]) -> dict[str, Any]:
    text = await visible_text(page)
    matched = [item for item in success_texts if item in text]
    url = page.url
    lower_text = text.lower()
    if matched:
        return {"ready": True, "matched": matched, "url": url}
    if "captcha" in lower_text or "otp" in lower_text or "verification" in lower_text or "验证码" in text or "驗證碼" in text:
        return {"ready": False, "manual_gate": "captcha_or_otp", "url": url}
    if "login" in url.lower() or "weblogin" in url.lower() or "password" in lower_text:
        return {"ready": False, "manual_gate": "login_incomplete", "url": url}
    return {"ready": False, "manual_gate": "unknown_page_state", "url": url}


async def main() -> None:
    args = parse_args()
    if not args.headless:
        # This helper is the only supported interactive path; background collectors set
        # GLOBALREVIEWOPS_NONINTERACTIVE=1 and must never wait for stdin.
        pass
    platform_key = args.platform.strip().lower()
    account_key = args.account.strip()
    defaults = PLATFORM_DEFAULTS[platform_key]
    account = resolve_account(
        platform=platform_key,
        account_ref=f"{platform_key}:{account_key}",
        account_key=account_key,
        country_code=args.country,
    )
    effective_account_key = account.account_key if account and account.account_key else account_key
    storage_state = Path(args.storage_state).expanduser() if args.storage_state else default_storage_state(platform_key, effective_account_key)
    storage_state = storage_state if storage_state.is_absolute() else ROOT / storage_state
    storage_state.parent.mkdir(parents=True, exist_ok=True)
    profile_dir = DATA / "browser_profiles" / default_profile_name(platform_key, effective_account_key)
    profile_dir.mkdir(parents=True, exist_ok=True)
    portal_url = args.portal_url or (account.portal_url if account and account.portal_url else defaults["portal_url"])
    login_url = args.login_url or defaults["login_url"]

    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        launch_options: dict[str, Any] = {
            "headless": args.headless,
            "viewport": {"width": 1600, "height": 1000},
        }
        channel = default_browser_channel(args.browser_channel)
        if channel:
            launch_options["channel"] = channel
        context = await playwright.chromium.launch_persistent_context(str(profile_dir), **launch_options)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(portal_url or login_url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(2500)
        if not args.headless and sys.stdin.isatty():
            print("Complete login/read-only navigation in the opened browser.")
            print("Stop when the review/feedback page is visible, then press Enter here.")
            await asyncio.to_thread(input)
        elif args.wait_seconds > 0:
            await page.wait_for_timeout(args.wait_seconds * 1000)
        state = await classify_ready(page, tuple(defaults["success_texts"]))
        await context.storage_state(path=str(storage_state))
        await context.close()

    print(
        json.dumps(
            {
                "ok": bool(state.get("ready")),
                "platform": platform_key,
                "account": effective_account_key,
                "storage_state": str(storage_state),
                "profile_dir": str(profile_dir),
                "state": state,
                "portal_url": portal_url,
            },
            ensure_ascii=False,
        )
    )
    if not state.get("ready"):
        raise SystemExit(2)


if __name__ == "__main__":
    asyncio.run(main())
