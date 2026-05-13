from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import CollectionTask, DEFAULT_FIELDS, OutputPolicy, SafetyPolicy, TimeRange


def _time_range(data: dict[str, Any]) -> TimeRange:
    raw = data.get("time_range") or {}
    if isinstance(raw, int):
        return TimeRange(type="last_days", days=raw)
    return TimeRange(
        type=raw.get("type", "last_days"),
        days=int(raw.get("days", 7)),
        start_date=str(raw.get("start_date", "")),
        end_date=str(raw.get("end_date", "")),
    )


def _safety(data: dict[str, Any]) -> SafetyPolicy:
    raw = dict(data.get("safety") or {})
    if isinstance(data.get("safe_mode"), bool):
        raw["safe_mode"] = data["safe_mode"]
    deny = raw.get("deny_write_actions")
    defaults = SafetyPolicy()
    return SafetyPolicy(
        safe_mode=bool(raw.get("safe_mode", defaults.safe_mode)),
        allow_login=bool(raw.get("allow_login", defaults.allow_login)),
        allow_search=bool(raw.get("allow_search", defaults.allow_search)),
        allow_open_detail=bool(raw.get("allow_open_detail", defaults.allow_open_detail)),
        allow_manual_gate=bool(raw.get("allow_manual_gate", defaults.allow_manual_gate)),
        deny_write_actions=tuple(deny) if deny else defaults.deny_write_actions,
    )


def _output(data: dict[str, Any]) -> OutputPolicy:
    raw = dict(data.get("output") or {})
    formats = raw.get("formats") or ("json", "csv")
    return OutputPolicy(
        output_dir=str(raw.get("output_dir", "")),
        output_prefix=str(raw.get("output_prefix", data.get("output_prefix", ""))),
        formats=tuple(formats),
    )


def load_task(path: str | Path) -> CollectionTask:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="utf-8-sig")
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    data = json.loads(text)
    fields = data.get("fields")
    task = CollectionTask(
        platform=str(data["platform"]),
        account=str(data.get("account", "")),
        country=str(data.get("country", "")),
        stores=data.get("stores", "all"),
        time_range=_time_range(data),
        fields=tuple(fields) if fields else DEFAULT_FIELDS,
        mode=data.get("mode", "auto"),
        max_reviews=int(data.get("max_reviews", 100)),
        safety=_safety(data),
        output=_output(data),
        options=dict(data.get("options") or {}),
        store_registry=str(data.get("store_registry", data.get("registry", ""))),
    )
    task.validate()
    return task
