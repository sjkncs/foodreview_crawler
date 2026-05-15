from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .account_registry import resolve_account
from .platform_capabilities import canonical_platform, get_capability
from .schema import CollectionTask, ExecutorResult
from .store_registry import DEFAULT_REGISTRY, resolve_stores


ROOT = Path(__file__).resolve().parents[1]


def _bool_option(task: CollectionTask, key: str, default: bool) -> bool:
    value = task.options.get(key, default)
    return bool(value)


def _output_prefix(task: CollectionTask, fallback: str) -> str:
    return task.output.output_prefix or str(task.options.get("output_prefix") or fallback)


def _registry_path(task: CollectionTask) -> str:
    configured = task.store_registry or str(task.options.get("store_registry") or task.options.get("registry") or "")
    if configured and Path(configured).exists():
        return configured
    return str(DEFAULT_REGISTRY)


def _browser_channel(task: CollectionTask, default: str = "msedge") -> str:
    channel = str(task.options.get("browser_channel", default) or "").strip()
    if channel.lower() == "msedge" and platform.system().lower() != "windows":
        return ""
    return channel


def _append_browser_channel(args: list[str], task: CollectionTask, default: str = "msedge") -> None:
    args.extend(["--browser-channel", _browser_channel(task, default)])


def _store_metrics(task: CollectionTask, platform: str, require_url: bool = False) -> dict[str, Any]:
    try:
        stores = resolve_stores(
            platform=platform,
            country=task.country,
            stores=task.stores,
            registry_path=_registry_path(task),
            require_url=require_url,
        )
    except FileNotFoundError:
        return {}
    return {
        "registry_store_count": len(stores),
        "registry_jdes": [store.jde for store in stores],
    }


def _append_headless(args: list[str], task: CollectionTask) -> None:
    if platform.system().lower() != "windows" or _bool_option(task, "headless", True):
        args.append("--headless")


def _maybe_account_ref(task: CollectionTask, prefix: str = "") -> str:
    account = str(task.account or "").strip()
    if not account:
        return ""
    if ":" in account:
        return account
    if prefix:
        return f"{prefix}:{account}"
    return account


def _tail(lines: list[str], size: int = 30) -> tuple[str, ...]:
    return tuple(lines[-size:])


def _parse_summary(stdout: str) -> dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    summary: dict[str, Any] = {}
    for line in lines:
        if line.startswith("[done] reviews="):
            summary["review_count"] = int(line.rsplit("=", 1)[-1])
        elif line.startswith("[done] json="):
            summary["json"] = line.split("=", 1)[1]
        elif line.startswith("[done] csv="):
            summary["csv"] = line.split("=", 1)[1]
        elif line.startswith("[stores]"):
            match = re.search(r"(\d+)", line)
            if match:
                summary["store_count"] = int(match.group(1))
        elif line.startswith("[done] excel="):
            summary["excel"] = line.split("=", 1)[1]
    return summary


def _redact_command(command: list[str]) -> list[str]:
    redacted: list[str] = []
    sensitive_next = False
    sensitive_flags = {
        "--password",
        "--username",
        "--api-key",
        "--token",
        "--access-token",
        "--secret",
    }
    for part in command:
        text = str(part)
        lowered = text.lower()
        if sensitive_next:
            redacted.append("[redacted]")
            sensitive_next = False
            continue
        if lowered in sensitive_flags:
            redacted.append(text)
            sensitive_next = True
            continue
        if any(lowered.startswith(f"{flag}=") for flag in sensitive_flags):
            redacted.append(f"{text.split('=', 1)[0]}=[redacted]")
            continue
        redacted.append(text)
    return redacted


def _run_python(
    args: list[str],
    task: CollectionTask,
    timeout: int | None = None,
    extra_env: dict[str, str] | None = None,
) -> ExecutorResult:
    command = [sys.executable, *args]
    if task.options.get("dry_run"):
        return ExecutorResult(
            ok=True,
            platform=task.platform,
            account=task.account or task.country,
            metrics={"dry_run": True, "command": _redact_command(command)},
        )
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if extra_env:
        env.update({str(key): str(value) for key, value in extra_env.items() if str(value)})
    timeout_seconds = int(timeout or task.options.get("timeout", 900))
    try:
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return ExecutorResult(
            ok=False,
            platform=task.platform,
            account=task.account or task.country,
            errors=(f"collector timeout after {timeout_seconds}s", stderr.strip() or stdout.strip()),
            metrics={"timeout_seconds": timeout_seconds, "command": _redact_command(command)},
            stdout_tail=_tail([line for line in stdout.splitlines() if line.strip()]),
        )
    stdout_lines = [line for line in process.stdout.splitlines() if line.strip()]
    summary = _parse_summary(process.stdout)
    errors: list[str] = []
    if process.returncode != 0:
        errors.append(process.stderr.strip() or process.stdout.strip() or f"exit code {process.returncode}")
    if summary.get("errors"):
        errors.extend(str(item) for item in summary["errors"])
    return ExecutorResult(
        ok=process.returncode == 0 and not errors,
        platform=task.platform,
        account=task.account or task.country,
        json_path=str(summary.get("json", summary.get("json_path", ""))),
        csv_path=str(summary.get("csv", summary.get("csv_path", ""))),
        excel_path=str(summary.get("excel", summary.get("excel_path", ""))),
        review_count=int(summary.get("review_count", summary.get("reviews", 0) or 0)),
        store_count=int(summary.get("store_count", summary.get("branch_count", 0) or 0)),
        errors=tuple(errors),
        metrics={k: v for k, v in summary.items() if k not in {"json", "csv", "excel", "errors"}},
        stdout_tail=_tail(stdout_lines),
    )


def run_grabfood(task: CollectionTask) -> ExecutorResult:
    account = task.account or task.country or "my_auro"
    account_ref = _maybe_account_ref(task, "grabfood")
    account_record = resolve_account(
        platform="grabfood",
        account_ref=account_ref,
        account_key=account if ":" not in account else "",
        country_code=task.country,
    )
    if account_record and account_record.account_key:
        account = account_record.account_key
    args = [
        "platforms/grabfood/grabfood_weekly_reviews.py",
        "--account",
        account,
        "--days",
        str(task.time_range.days),
        "--max-reviews",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, f"unified_grabfood_{account}"),
    ]
    _append_headless(args, task)
    if task.options.get("manual_login"):
        args.append("--manual-login")
    if task.options.get("all_stores_only"):
        args.append("--all-stores-only")
    if task.options.get("limit_stores"):
        args.extend(["--limit-stores", str(task.options["limit_stores"])])
    if task.options.get("store_name"):
        args.extend(["--store-name", str(task.options["store_name"])])
    credential_env = {}
    if account_record and account_record.username and account_record.password:
        env_prefix = f"GRABFOOD_{account.upper()}"
        credential_env = {
            "GRABFOOD_USERNAME": account_record.username,
            "GRABFOOD_PASSWORD": account_record.password,
            f"{env_prefix}_USERNAME": account_record.username,
            f"{env_prefix}_PASSWORD": account_record.password,
        }
    result = _run_python(args, task, extra_env=credential_env)
    metrics = {
        **result.metrics,
        "account_ref": account_record.account_ref if account_record else "",
        "account_key": account_record.account_key if account_record else account,
    }
    return ExecutorResult(**{**result.to_dict(), "platform": "grabfood", "account": account, "metrics": metrics})


def run_hungry_panda(task: CollectionTask) -> ExecutorResult:
    region = (task.country or task.account or "usa").strip().lower()
    explicit_ref = _maybe_account_ref(task, "hungry_panda")
    implied_account_ref = "hungry_panda:kr" if region in {"kr", "korea", "south_korea"} else "hungry_panda:default"
    account_record = resolve_account(
        platform="hungry_panda",
        account_ref=explicit_ref,
        country_code=region,
    )
    if not account_record:
        account_record = resolve_account(platform="hungry_panda", account_ref=implied_account_ref, country_code=region)
    phone_code = str(task.options.get("phone_code") or (account_record.phone_code if account_record and account_record.phone_code else "+86"))
    args = [
        "scripts/hungry_panda_weekly_reviews.py",
        "--region",
        region,
        "--days",
        str(task.time_range.days),
        "--max-reviews",
        str(task.max_reviews),
        "--phone-code",
        phone_code,
        "--output-prefix",
        _output_prefix(task, f"unified_hungry_panda_{region}"),
    ]
    _append_headless(args, task)
    if task.options.get("manual_login"):
        args.append("--manual-login")
    if task.options.get("start_index") is not None:
        args.extend(["--start-index", str(task.options["start_index"])])
    if task.options.get("limit"):
        args.extend(["--limit", str(task.options["limit"])])
    credential_env = {}
    if account_record and account_record.username and account_record.password:
        env_prefix = f"HUNGRY_PANDA_{region.upper()}"
        credential_env = {
            "HUNGRY_PANDA_USERNAME": account_record.username,
            "HUNGRY_PANDA_PASSWORD": account_record.password,
            f"{env_prefix}_USERNAME": account_record.username,
            f"{env_prefix}_PASSWORD": account_record.password,
        }
    result = _run_python(args, task, extra_env=credential_env)
    metrics = {
        **result.metrics,
        "account_ref": account_record.account_ref if account_record else implied_account_ref,
        "account_key": account_record.account_key if account_record else "default",
    }
    return ExecutorResult(**{**result.to_dict(), "platform": "hungry_panda", "account": region, "metrics": metrics})


def run_fantuan(task: CollectionTask) -> ExecutorResult:
    country = task.country or task.account or "ca"
    args = [
        "platforms/fantuan/fantuan_weekly_reviews.py",
        "--country",
        country,
        "--days",
        str(task.time_range.days),
        "--max-reviews",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, f"unified_fantuan_{country}"),
    ]
    _append_headless(args, task)
    if task.options.get("limit_stores"):
        args.extend(["--limit-stores", str(task.options["limit_stores"])])
    if task.options.get("restaurant_id"):
        args.extend(["--restaurant-id", str(task.options["restaurant_id"])])
    if task.options.get("store_name"):
        args.extend(["--store-name", str(task.options["store_name"])])
    result = _run_python(args, task)
    return ExecutorResult(**{**result.to_dict(), "platform": "fantuan", "account": country})


def run_google_maps(task: CollectionTask) -> ExecutorResult:
    args = [
        "platforms/google_maps/google_maps_weekly_reviews.py",
        "--days",
        str(task.time_range.days),
        "--max-reviews-per-store",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, f"unified_google_maps_{task.country or 'all'}"),
    ]
    _append_browser_channel(args, task)
    _append_headless(args, task)
    if task.country:
        args.extend(["--country", task.country])
    if task.options.get("excel"):
        args.extend(["--excel", str(task.options["excel"])])
    registry = _registry_path(task)
    if Path(registry).exists():
        args.extend(["--registry", registry])
    if task.options.get("sheet"):
        args.extend(["--sheet", str(task.options["sheet"])])
    if task.options.get("shop_name"):
        args.extend(["--shop-name", str(task.options["shop_name"])])
    elif isinstance(task.stores, str) and task.stores != "all":
        args.extend(["--shop-name", task.stores])
    elif isinstance(task.stores, list) and task.stores and task.stores != ["all"]:
        args.extend(["--shop-name", str(task.stores[0])])
    if task.options.get("limit_stores"):
        args.extend(["--limit-stores", str(task.options["limit_stores"])])
    if task.options.get("max_scrolls"):
        args.extend(["--max-scrolls", str(task.options["max_scrolls"])])
    result = _run_python(args, task, timeout=int(task.options.get("timeout", 900)))
    metrics = {**result.metrics, **_store_metrics(task, "google_maps", require_url=True)}
    return ExecutorResult(**{**result.to_dict(), "platform": "google_maps", "account": task.country, "metrics": metrics})


def run_keeta(task: CollectionTask) -> ExecutorResult:
    args = [
        "platforms/keeta/keeta_weekly_reviews.py",
        "--max-reviews",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, "unified_keeta_hk"),
    ]
    _append_browser_channel(args, task)
    _append_headless(args, task)
    if task.time_range.type == "fixed":
        args.extend(["--start-date", task.time_range.start_date, "--end-date", task.time_range.end_date])
    else:
        today = datetime.now().date()
        start_date = today - timedelta(days=task.time_range.days - 1)
        args.extend(
            [
                "--start-date",
                str(task.options.get("start_date", start_date.isoformat())),
                "--end-date",
                str(task.options.get("end_date", today.isoformat())),
            ]
        )
    if task.options.get("max_pages"):
        args.extend(["--max-pages", str(task.options["max_pages"])])
    if task.options.get("no_login"):
        args.append("--no-login")
    result = _run_python(args, task)
    return ExecutorResult(**{**result.to_dict(), "platform": "keeta", "account": task.account or "hk"})


def run_openrice(task: CollectionTask) -> ExecutorResult:
    args = [
        "platforms/openrice/openrice_public_reviews.py",
        "--max-reviews-per-shop",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, "unified_openrice_hk"),
    ]
    _append_browser_channel(args, task)
    _append_headless(args, task)
    if task.options.get("chain_url"):
        args.extend(["--chain-url", str(task.options["chain_url"])])
    if task.options.get("max_shops"):
        args.extend(["--max-shops", str(task.options["max_shops"])])
    if task.options.get("shop_name"):
        args.extend(["--shop-name", str(task.options["shop_name"])])
    if task.options.get("max_pages_per_shop"):
        args.extend(["--max-pages-per-shop", str(task.options["max_pages_per_shop"])])
    result = _run_python(args, task)
    return ExecutorResult(**{**result.to_dict(), "platform": "openrice", "account": "public"})


def run_dianping(task: CollectionTask) -> ExecutorResult:
    script = ROOT / "platforms" / "dianping" / "dianping_weekly_reviews.py"
    if not script.exists():
        return ExecutorResult(
            ok=False,
            platform="dianping",
            account=task.account or task.country,
            errors=("dianping executor is not implemented yet: platforms/dianping/dianping_weekly_reviews.py",),
        )
    args = [
        str(script.relative_to(ROOT)),
        "--days",
        str(task.time_range.days),
        "--max-reviews-per-store",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, f"unified_dianping_{task.country or 'all'}"),
    ]
    _append_browser_channel(args, task)
    _append_headless(args, task)
    if task.country:
        args.extend(["--country", task.country])
    if isinstance(task.stores, str) and task.stores != "all":
        args.extend(["--store-filter", task.stores])
    if task.options.get("store_filter"):
        args.extend(["--store-filter", str(task.options["store_filter"])])
    if task.options.get("max_stores"):
        args.extend(["--max-stores", str(task.options["max_stores"])])
    if task.options.get("max_pages_per_store"):
        args.extend(["--max-pages-per-store", str(task.options["max_pages_per_store"])])
    registry = _registry_path(task)
    if Path(registry).exists():
        args.extend(["--registry", registry])
    result = _run_python(args, task, timeout=int(task.options.get("timeout", 900)))
    metrics = {**result.metrics, **_store_metrics(task, "dianping", require_url=True)}
    return ExecutorResult(**{**result.to_dict(), "platform": "dianping", "account": task.country, "metrics": metrics})


def run_uber_eats(task: CollectionTask) -> ExecutorResult:
    script = ROOT / "platforms" / "uber_eats" / "uber_eats_weekly_reviews.py"
    if not script.exists():
        return ExecutorResult(
            ok=False,
            platform="uber_eats",
            account=task.account or task.country,
            errors=("uber_eats executor is not implemented yet: platforms/uber_eats/uber_eats_weekly_reviews.py",),
        )
    account_record = resolve_account(
        platform="uber_eats",
        account_ref=_maybe_account_ref(task, "uber_eats"),
        account_key=task.account if task.account and ":" not in task.account else "",
        country_code=task.country,
    )
    account_key = account_record.account_key if account_record and account_record.account_key else (task.account or "default")
    args = [
        str(script.relative_to(ROOT)),
        "--days",
        str(task.time_range.days),
        "--max-reviews",
        str(task.max_reviews),
        "--account",
        account_key,
        "--output-prefix",
        _output_prefix(task, f"unified_uber_eats_{task.country or account_key}"),
    ]
    _append_browser_channel(args, task)
    _append_headless(args, task)
    if task.country:
        args.extend(["--country", task.country])
    if isinstance(task.stores, str) and task.stores != "all":
        args.extend(["--store-filter", task.stores])
    if task.options.get("store_filter"):
        args.extend(["--store-filter", str(task.options["store_filter"])])
    if task.options.get("max_stores"):
        args.extend(["--max-stores", str(task.options["max_stores"])])
    if task.options.get("manual_login"):
        args.append("--manual-login")
    credential_env = {}
    if account_record and account_record.username and account_record.password:
        credential_env = {
            "UBER_EATS_USERNAME": account_record.username,
            "UBER_EATS_PASSWORD": account_record.password,
        }
    registry = _registry_path(task)
    if Path(registry).exists():
        args.extend(["--registry", registry])
    result = _run_python(args, task, timeout=int(task.options.get("timeout", 900)), extra_env=credential_env)
    metrics = {
        **result.metrics,
        **_store_metrics(task, "uber_eats", require_url=True),
        "account_ref": account_record.account_ref if account_record else "",
        "account_key": account_key,
    }
    return ExecutorResult(**{**result.to_dict(), "platform": "uber_eats", "account": account_key, "metrics": metrics})


def run_mfood(task: CollectionTask) -> ExecutorResult:
    script = ROOT / "platforms" / "mfood" / "mfood_weekly_reviews.py"
    if not script.exists():
        return ExecutorResult(
            ok=False,
            platform="mfood",
            account=task.account,
            errors=("mfood executor is not implemented yet: platforms/mfood/mfood_weekly_reviews.py",),
        )
    account_record = resolve_account(
        platform="mfood",
        account_ref=_maybe_account_ref(task, "mfood"),
        account_key=task.account if task.account and ":" not in task.account else "",
        country_code=task.country,
    )
    account_key = account_record.account_key if account_record and account_record.account_key else (task.account or "default")
    args = [
        str(script.relative_to(ROOT)),
        "--account",
        account_key,
        "--days",
        str(task.time_range.days),
        "--max-reviews",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, "unified_mfood"),
    ]
    _append_headless(args, task)
    if task.options.get("manual_login"):
        args.append("--manual-login")
    if task.options.get("max_pages"):
        args.extend(["--max-pages", str(task.options["max_pages"])])
    credential_env = {}
    if account_record and account_record.username and account_record.password:
        env_prefix = f"MFOOD_{account_key.upper()}"
        credential_env = {
            "MFOOD_USERNAME": account_record.username,
            "MFOOD_PASSWORD": account_record.password,
            f"{env_prefix}_USERNAME": account_record.username,
            f"{env_prefix}_PASSWORD": account_record.password,
        }
    if account_record and account_record.portal_url and not task.options.get("portal_url"):
        args.extend(["--portal-url", account_record.portal_url])
    if task.options.get("portal_url"):
        args.extend(["--portal-url", str(task.options["portal_url"])])
    if task.options.get("login_url"):
        args.extend(["--login-url", str(task.options["login_url"])])
    result = _run_python(args, task, extra_env=credential_env)
    metrics = {
        **result.metrics,
        "account_ref": account_record.account_ref if account_record else "",
        "account_key": account_key,
        "portal_url": (task.options.get("portal_url") or (account_record.portal_url if account_record else "")),
    }
    return ExecutorResult(**{**result.to_dict(), "platform": "mfood", "account": account_key, "metrics": metrics})


def run_aomi(task: CollectionTask) -> ExecutorResult:
    script = ROOT / "platforms" / "aomi" / "aomi_weekly_reviews.py"
    if not script.exists():
        return ExecutorResult(
            ok=False,
            platform="aomi",
            account=task.account,
            errors=("aomi executor is not implemented yet: platforms/aomi/aomi_weekly_reviews.py",),
        )
    account_record = resolve_account(
        platform="aomi",
        account_ref=_maybe_account_ref(task, "aomi"),
        account_key=task.account if task.account and ":" not in task.account else "",
        country_code=task.country,
    )
    account_key = account_record.account_key if account_record and account_record.account_key else (task.account or "default")
    portal_url = str(task.options.get("portal_url") or (account_record.portal_url if account_record else "")).strip()
    if not portal_url:
        return ExecutorResult(
            ok=False,
            platform="aomi",
            account=account_key,
            errors=("Aomi portal URL is missing. Set task.options.portal_url first.",),
        )

    args = [
        str(script.relative_to(ROOT)),
        "--account",
        account_key,
        "--days",
        str(task.time_range.days),
        "--max-reviews",
        str(task.max_reviews),
        "--output-prefix",
        _output_prefix(task, "unified_aomi"),
        "--portal-url",
        portal_url,
    ]
    _append_headless(args, task)
    if task.options.get("manual_login"):
        args.append("--manual-login")
    if task.options.get("max_pages"):
        args.extend(["--max-pages", str(task.options["max_pages"])])
    if task.options.get("login_url"):
        args.extend(["--login-url", str(task.options["login_url"])])
    if task.options.get("country_label"):
        args.extend(["--country-label", str(task.options["country_label"])])
    if task.options.get("country_code"):
        args.extend(["--country-code", str(task.options["country_code"])])
    credential_env = {}
    if account_record and account_record.username and account_record.password:
        credential_env = {
            "AOMI_USERNAME": account_record.username,
            "AOMI_PASSWORD": account_record.password,
        }
    result = _run_python(args, task, extra_env=credential_env)
    metrics = {
        **result.metrics,
        "account_ref": account_record.account_ref if account_record else "",
        "account_key": account_key,
        "portal_url": portal_url,
    }
    return ExecutorResult(**{**result.to_dict(), "platform": "aomi", "account": account_key, "metrics": metrics})


EXECUTORS: dict[str, Callable[[CollectionTask], ExecutorResult]] = {
    "grabfood": run_grabfood,
    "grab_food": run_grabfood,
    "hungry_panda": run_hungry_panda,
    "hungrypanda": run_hungry_panda,
    "fantuan": run_fantuan,
    "fan_tuan": run_fantuan,
    "google_maps": run_google_maps,
    "googlemaps": run_google_maps,
    "keeta": run_keeta,
    "openrice": run_openrice,
    "open_rice": run_openrice,
    "dianping": run_dianping,
    "dian_ping": run_dianping,
    "mfood": run_mfood,
    "aomi": run_aomi,
    "ao_mi": run_aomi,
    "uber_eats": run_uber_eats,
    "uber": run_uber_eats,
    "ubereats": run_uber_eats,
}


def run_task(task: CollectionTask) -> ExecutorResult:
    task.validate()
    key = canonical_platform(task.platform)
    executor = EXECUTORS.get(key)
    if not executor:
        return ExecutorResult(
            ok=False,
            platform=task.platform,
            account=task.account,
            errors=(f"no executor registered for platform: {task.platform}",),
        )
    result = executor(task)
    capability = get_capability(key)
    if not capability:
        return result
    metrics = {
        **result.metrics,
        "capability": capability.to_dict(),
    }
    return ExecutorResult(**{**result.to_dict(), "metrics": metrics})
