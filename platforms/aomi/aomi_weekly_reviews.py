from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
EXPORTS = ROOT / "exports" / "aomi"
CREDENTIALS_FILE = DATA / "aomi_credentials.local.json"
MFOOD_SCRIPT = ROOT / "platforms" / "mfood" / "mfood_weekly_reviews.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aomi weekly review collector (read-only)")
    parser.add_argument("--account", default="default", help="Account key in aomi credential file")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--max-reviews", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--manual-login", action="store_true")
    parser.add_argument("--portal-url", default="", help="Aomi review page URL (required)")
    parser.add_argument("--login-url", default="", help="Aomi login page URL")
    parser.add_argument("--username", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--country-label", default="China Macau")
    parser.add_argument("--country-code", default="mo")
    parser.add_argument("--output-prefix", default="")
    return parser.parse_args()


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


def infer_login_url(portal_url: str) -> str:
    parsed = urlparse(portal_url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    if "/#/" in parsed.path:
        path = parsed.path.split("/#/")[0] + "/#/login"
    else:
        path = "/#/login"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def main() -> None:
    args = parse_args()
    if not args.portal_url:
        print(
            json.dumps(
                {
                    "ok": False,
                    "platform": "Aomi",
                    "errors": ["Aomi portal URL is required. Provide --portal-url or task.options.portal_url."],
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)

    if not MFOOD_SCRIPT.exists():
        print(
            json.dumps(
                {
                    "ok": False,
                    "platform": "Aomi",
                    "errors": ["shared collector missing: platforms/mfood/mfood_weekly_reviews.py"],
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)

    username, password = load_credentials(args)
    command = [
        sys.executable,
        str(MFOOD_SCRIPT),
        "--account",
        "default",
        "--days",
        str(args.days),
        "--max-reviews",
        str(args.max_reviews),
        "--max-pages",
        str(args.max_pages),
        "--portal-url",
        args.portal_url,
        "--login-url",
        (args.login_url or infer_login_url(args.portal_url)),
        "--platform-label",
        "Aomi",
        "--country-label",
        args.country_label,
        "--country-code",
        args.country_code,
        "--file-tag",
        "aomi",
        "--export-dir",
        str(EXPORTS),
        "--output-prefix",
        args.output_prefix,
    ]
    if args.headless:
        command.append("--headless")
    if args.manual_login:
        command.append("--manual-login")
    if username and password:
        command.extend(["--username", username, "--password", password])

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if process.stdout:
        print(process.stdout.strip())
    if process.returncode != 0:
        if process.stderr:
            print(process.stderr.strip(), file=sys.stderr)
        raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
