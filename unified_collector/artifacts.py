from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "exports" / "runs"

NORMALIZED_FIELDS = (
    "run_id",
    "platform",
    "country",
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
    "raw_json",
    "quality_flags",
)

FIELD_ALIASES = {
    "platform": ("platform", "Platform"),
    "country": ("country", "Country", "region", "Region"),
    "account": ("account", "Account"),
    "store": ("store", "Store", "shop", "Shop", "Branch", "branch", "store_name", "Store Name", "Restaurant"),
    "store_id": ("store_id", "Store ID", "Branch ID", "branch_id", "jde", "JDE"),
    "rating": ("rating", "Rating", "综合评价", "score"),
    "sub_ratings": ("sub_ratings", "Child ratings", "child_ratings", "Sub Ratings"),
    "review": ("review", "Review contents", "Review Content", "Review", "content", "Content", "Comment", "Raw Text", "评价", "评价内容"),
    "review_language": ("review_language", "language", "Language"),
    "translated_review": ("translated_review", "Translated Review", "translated_content", "Google translation", "Chinese Translation", "CN Translation"),
    "customer": ("customer", "Customer", "reviewer", "Reviewer", "Reviewer Name", "user_name", "User Name"),
    "review_time": ("review_time", "Review time", "Review Time", "Approx Review Date", "Review Date", "time", "Date", "评价时间"),
    "order_id": ("order_id", "Order ID", "Order SN", "POS Order ID", "Order View ID", "订单号"),
    "ordered_items": ("ordered_items", "Ordered Items", "Order Items JSON", "Order Items Text", "items", "Products", "Order Items", "Order Detail JSON"),
    "order_detail": ("order_detail", "Order Detail", "Order Details", "Expanded Order Detail", "order_details", "Order Detail JSON"),
    "image_urls": ("image_urls", "Image URLs", "Review Image URLs", "Photo URLs", "photos", "Product Image URLs"),
    "source": ("source", "Source"),
    "quality_flags": ("quality_flags", "Quality Flags"),
}


def run_dir(run_id: str) -> Path:
    path = RUNS_DIR / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_checkpoint(run_id: str, stage: str, payload: dict[str, Any]) -> Path:
    path = run_dir(run_id) / "checkpoint.json"
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    checkpoints = list(existing.get("checkpoints") or [])
    checkpoints.append({"stage": stage, "at": datetime.now().isoformat(timespec="seconds"), "payload": payload})
    existing.update(
        {
            "run_id": run_id,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "last_stage": stage,
            "checkpoints": checkpoints[-50:],
        }
    )
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _get(raw: dict[str, Any], field: str, default: Any = "") -> Any:
    for key in FIELD_ALIASES.get(field, (field,)):
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return default


def _as_list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [part.strip() for part in value.split("|") if part.strip()] or [value]
    return [value]


def _parse_ordered_items(value: Any) -> list[dict[str, Any]]:
    parsed_value = value
    if isinstance(parsed_value, str):
        stripped = parsed_value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                parsed_value = json.loads(stripped)
            except json.JSONDecodeError:
                parsed_value = value
    if isinstance(parsed_value, dict):
        for key in ("details", "items", "order_items", "orderItemList"):
            nested = parsed_value.get(key)
            if isinstance(nested, list):
                parsed_value = nested
                break
    items = _as_list(parsed_value)
    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        elif item not in (None, ""):
            normalized.append({"text": str(item)})
    return normalized


def _extract_nested_order_fields(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    item_containers: list[Any] = []
    detail_texts: list[str] = []
    seen_refs: set[int] = set()

    def walk(node: Any, depth: int = 0) -> None:
        if depth > 6:
            return
        ref_id = id(node)
        if ref_id in seen_refs:
            return
        seen_refs.add(ref_id)
        if isinstance(node, dict):
            for key, value in node.items():
                key_l = str(key or "").lower().replace(" ", "").replace("-", "").replace("_", "")
                if any(token in key_l for token in ("orderdetail", "orderdetails", "items", "products", "goods", "detail")):
                    item_containers.append(value)
                if isinstance(value, (dict, list, tuple)):
                    walk(value, depth + 1)
                elif isinstance(value, str):
                    text = value.strip()
                    if text and any(token in key_l for token in ("name", "spec", "qty", "price", "remark", "detail")):
                        detail_texts.append(text)
        elif isinstance(node, (list, tuple)):
            for value in node:
                walk(value, depth + 1)

    walk(raw)
    extracted_items: list[dict[str, Any]] = []
    for candidate in item_containers:
        for item in _parse_ordered_items(candidate):
            if item not in extracted_items:
                extracted_items.append(item)
    detail = "\n".join(text for text in detail_texts if text)[:12000]
    return extracted_items, detail


def _normalized_record(raw: dict[str, Any], payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    record = {field: _get(raw, field) for field in NORMALIZED_FIELDS}
    record["run_id"] = run_id
    record["platform"] = record["platform"] or payload.get("platform", "")
    record["country"] = record["country"] or payload.get("country", "") or payload.get("region", "")
    record["account"] = record["account"] or payload.get("account", "")
    record["image_urls"] = _as_list(record["image_urls"])
    record["ordered_items"] = _parse_ordered_items(record.get("ordered_items"))
    nested_items, nested_detail = _extract_nested_order_fields(raw)
    if not record["ordered_items"] and nested_items:
        record["ordered_items"] = nested_items
    if str(record.get("order_detail") or "").strip() in {"", "-", "None", "null"} and nested_detail:
        record["order_detail"] = nested_detail
    record["quality_flags"] = _as_list(record["quality_flags"])
    record["raw_json"] = raw
    return record


def load_reviews(json_path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = Path(json_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {}, [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return {}, []
    for key in ("reviews", "data", "items", "rows"):
        value = payload.get(key)
        if isinstance(value, list):
            return payload, [item for item in value if isinstance(item, dict)]
    return payload, []


def normalize_json_to_jsonl(json_path: str | Path, run_id: str) -> dict[str, Any]:
    payload, reviews = load_reviews(json_path)
    records = [_normalized_record(raw, payload, run_id) for raw in reviews]
    output = run_dir(run_id) / "normalized_reviews.jsonl"
    with output.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    report = build_quality_report(records, payload, source_json=str(json_path))
    report_path = run_dir(run_id) / "quality_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "normalized_jsonl": str(output),
        "quality_report": str(report_path),
        "normalized_review_count": len(records),
        "quality": report,
    }


def build_quality_report(records: list[dict[str, Any]], payload: dict[str, Any], source_json: str = "") -> dict[str, Any]:
    core_fields = ("platform", "store", "rating", "review", "review_time")
    total = len(records)
    non_empty = 0
    for record in records:
        non_empty += sum(1 for field in core_fields if record.get(field) not in (None, "", []))
    completeness = round(non_empty / max(1, total * len(core_fields)), 4)
    order_rows = [record for record in records if record.get("order_id")]
    detail_rows = [record for record in order_rows if record.get("order_detail") or record.get("ordered_items")]
    identity_counts = Counter(
        f"{record.get('platform')}|{record.get('store_id')}|{record.get('order_id')}|{record.get('review_time')}|{record.get('review')}"
        for record in records
    )
    duplicates = sum(count - 1 for count in identity_counts.values() if count > 1)
    missing_core = [
        {"index": index, "missing": [field for field in core_fields if record.get(field) in (None, "", [])]}
        for index, record in enumerate(records, start=1)
        if any(record.get(field) in (None, "", []) for field in core_fields)
    ][:100]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_json": source_json,
        "platform": payload.get("platform", "") or (records[0].get("platform") if records else ""),
        "review_count": total,
        "field_completeness": completeness,
        "detail_coverage": round(len(detail_rows) / max(1, len(order_rows)), 4),
        "image_url_count": sum(len(_as_list(record.get("image_urls"))) for record in records),
        "duplicate_count": duplicates,
        "out_of_range_count": 0,
        "manual_gate_count": 0,
        "error_count": len(payload.get("errors") or []),
        "errors": payload.get("errors") or [],
        "missing_core_samples": missing_core,
        "retry_candidates": [
            {
                "store": record.get("store"),
                "store_id": record.get("store_id"),
                "order_id": record.get("order_id"),
                "reason": "missing_order_detail",
            }
            for record in order_rows
            if not (record.get("order_detail") or record.get("ordered_items"))
        ][:100],
    }
