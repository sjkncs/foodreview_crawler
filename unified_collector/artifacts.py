from __future__ import annotations

import json
import difflib
import re
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
    "order_total",
    "image_urls",
    "source",
    "raw_json",
    "quality_flags",
    "review_id",
    "review_type",
    "reply_status",
    "review_quality",
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
    "order_total": ("order_total", "Order Total", "Total", "Subtotal", "订单金额", "訂單金額"),
    "image_urls": ("image_urls", "Image URLs", "Review Image URLs", "Photo URLs", "photos", "Product Image URLs"),
    "source": ("source", "Source"),
    "quality_flags": ("quality_flags", "Quality Flags"),
    "review_id": ("review_id", "Review ID", "id"),
    "review_type": ("review_type", "Review Type", "type"),
    "reply_status": ("reply_status", "Reply Status"),
    "review_quality": ("review_quality", "Review Quality", "quality"),
}
ORDER_ID_PATTERNS = (
    re.compile(r"(?:订单号|訂單號|order\s*(?:id|no\.?|number|#))\s*[:：#]?\s*([A-Z]{0,6}\d{6,})", re.IGNORECASE),
    re.compile(r"\b([A-Z]{1,6}\d{7,})\b"),
)


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
    excluded_key_tokens = (
        "reviewitemdetail",
        "reviewdetail",
        "subrating",
        "subratings",
        "ratingdetail",
        "scoreitem",
    )
    order_container_tokens = (
        "orderdetail",
        "orderdetails",
        "orderitems",
        "orderitemlist",
        "ordereditems",
        "productview",
        "products",
        "productlist",
        "goods",
        "goodslist",
        "itemlist",
        "items",
    )
    order_text_tokens = (
        "orderdetail",
        "orderdetails",
        "orderitems",
        "productview",
        "products",
        "goods",
        "goodslist",
        "itemlist",
        "items",
        "name",
        "spec",
        "qty",
        "quantity",
        "price",
        "amount",
        "subtotal",
        "total",
        "remark",
    )

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
                if any(token in key_l for token in excluded_key_tokens):
                    continue
                if any(token in key_l for token in order_container_tokens) and not isinstance(value, str):
                    item_containers.append(value)
                if isinstance(value, (dict, list, tuple)):
                    walk(value, depth + 1)
                elif isinstance(value, str):
                    text = value.strip()
                    if text and any(token in key_l for token in order_text_tokens):
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
    record["order_detail"] = _clean_order_detail_text(record.get("order_detail"))
    if _is_noise_order_detail(record.get("order_detail")):
        record["order_detail"] = ""
    record["review"] = _valid_review_text(record.get("review"))
    if not record["review"]:
        label_text = _valid_review_text(_label_review_text(raw))
        if label_text:
            record["review"] = label_text
            record["review_type"] = record.get("review_type") or "tag_only"
            flags = _as_list(record.get("quality_flags"))
            if "tag_only_review" not in flags:
                flags.append("tag_only_review")
            record["quality_flags"] = flags
        elif _clean_identity(record.get("rating")):
            record["review_type"] = record.get("review_type") or "rating_only"
            flags = _as_list(record.get("quality_flags"))
            if "rating_only_review" not in flags:
                flags.append("rating_only_review")
            record["quality_flags"] = flags
    record["translated_review"] = _valid_review_text(record.get("translated_review"))
    record["customer"] = _clean_customer_display(record.get("customer"))
    if not _clean_identity(record.get("order_total")):
        record["order_total"] = _extract_order_total_from_text(record.get("order_detail"))
    if not _clean_identity(record.get("order_id")):
        source_text = f"{record.get('order_detail') or ''}\n{json.dumps(raw, ensure_ascii=False)[:6000]}"
        for pattern in ORDER_ID_PATTERNS:
            match = pattern.search(source_text)
            if match:
                record["order_id"] = match.group(1).strip()
                break
    record["quality_flags"] = _as_list(record["quality_flags"])
    record["raw_json"] = raw
    return record


def _clean_identity(value: Any, max_len: int = 220) -> str:
    text = str(value or "").strip()
    if text in {"", "-", "None", "none", "null", "NULL", "No data", "no data", "N/A", "n/a"}:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()[:max_len]


def _is_noise_order_detail(value: Any) -> bool:
    text = str(value or "").strip()
    if not _clean_identity(text):
        return True
    text = _clean_order_detail_text(text)
    if not _clean_identity(text):
        return True
    signal_markers = (
        "order",
        "item",
        "qty",
        "quantity",
        "price",
        "subtotal",
        "total",
        "product",
        "goods",
        "订单",
        "訂單",
        "商品",
        "产品",
        "產品",
        "数量",
        "數量",
        "单价",
        "單價",
        "价格",
        "價格",
        "小计",
        "小計",
        "合计",
        "合計",
        "结算",
        "結算",
        "配送",
        "外卖",
        "外賣",
    )
    lower = text.lower()
    if any(marker.lower() in lower for marker in signal_markers):
        return False
    if re.search(r"(?:[$€£¥￥]|HK\$|MOP|RM|SGD|USD|AUD|CAD)\s*\d", text, flags=re.IGNORECASE):
        return False
    if re.search(r"(?:^|\s)(?:x\s*)?\d+\s*(?:件|杯|份|个|個|pcs?|items?)\b", text, flags=re.IGNORECASE):
        return False
    markers = (
        "order",
        "item",
        "qty",
        "quantity",
        "price",
        "subtotal",
        "total",
        "product",
        "goods",
        "订单",
        "商品",
        "数量",
        "单价",
        "价格",
        "小计",
        "结算",
    )
    lower = text.lower()
    has_marker = any(marker.lower() in lower for marker in markers)
    has_money = bool(re.search(r"(?:[$€£¥]|HK\$|MOP|RM|SGD|USD|AUD|CAD)\s*\d", text, flags=re.IGNORECASE))
    has_quantity = bool(re.search(r"(?:^|\s)(?:x\s*)?\d+\s*(?:份|杯|件|pcs?|items?)\b", text, flags=re.IGNORECASE))
    return not (has_marker or has_money or has_quantity)


def _clean_order_detail_text(value: Any) -> str:
    lines = []
    for line in str(value or "").replace("\r", "\n").split("\n"):
        text = line.strip()
        if not text:
            continue
        lower = text.lower()
        if re.fullmatch(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
            continue
        if ".owner" in lower or "owner a" in lower or "owner b" in lower:
            continue
        if re.fullmatch(r"[A-Za-z]:[\\/].+", text) or re.search(r"exports[\\/].+\.jsonl?$", text, flags=re.IGNORECASE):
            continue
        lines.append(text)
    return "\n".join(lines).strip()


def _valid_review_text(value: Any) -> str:
    text = str(value or "").strip()
    if not _clean_identity(text):
        return ""
    if re.fullmatch(r"[\d\s:：\-.,，。/]+", text):
        return ""
    return text


def _label_review_text(raw: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "Review Labels",
        "Shop Labels",
        "Rating Comment",
        "Package Rating Comment",
        "Taste Rating Comment",
        "Recommended Items",
    ):
        text = str(raw.get(key) or "").strip()
        if text and text not in {"-", "None", "null"}:
            parts.append(text)
    seen: set[str] = set()
    unique = []
    for part in parts:
        if part not in seen:
            unique.append(part)
            seen.add(part)
    return "；".join(unique)


def _extract_order_total_from_text(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    patterns = (
        r"(?:顾客支付|客戶支付|客户支付|Customer\s*paid|Customer\s*payment)\s*[:：]?\s*([A-Z$€£¥￥]*\s*\d+(?:[.,]\d{1,2})?)",
        r"(?:订单总额|訂單總額|合计|合計|Total)\s*[:：]?\s*([A-Z$€£¥￥]*\s*\d+(?:[.,]\d{1,2})?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", "", match.group(1)).strip()
    return ""


def _clean_customer_display(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\b[a-fA-F0-9]{16,64}\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _record_identity(record: dict[str, Any]) -> str:
    platform = _clean_identity(record.get("platform"), 120)
    order_id = _clean_identity(record.get("order_id"), 160)
    if order_id:
        return f"order|{platform}|{order_id}"
    store = _clean_identity(record.get("store") or record.get("store_id"), 160)
    customer = _clean_identity(record.get("customer"), 120)
    rating = _clean_identity(record.get("rating"), 20)
    if platform in {"google maps", "google_maps"} and store and customer:
        return f"google_user|{platform}|{store}|{customer}|{rating}"
    review = _clean_identity(record.get("review") or record.get("translated_review"), 260)
    if review:
        return f"text|{platform}|{store}|{customer}|{rating}|{review}"
    review_time = _clean_identity(str(record.get("review_time") or "")[:10], 40)
    if review_time or customer or store or rating:
        return f"rating_only|{platform}|{review_time}|{customer}|{rating}|{store}"
    return f"fallback|{platform}"


def _record_fuzzy_base_key(record: dict[str, Any]) -> str:
    platform = _clean_identity(record.get("platform"), 120)
    store = _clean_identity(record.get("store") or record.get("store_id"), 160)
    rating = _clean_identity(record.get("rating"), 20)
    review_time = _clean_identity(str(record.get("review_time") or "")[:16], 40)
    return f"{platform}|{store}|{rating}|{review_time}"


def _record_text_identity(record: dict[str, Any], max_len: int = 2000) -> str:
    text = str(record.get("review") or record.get("translated_review") or "")
    text = re.sub(r"[\ue000-\uf8ff]", " ", text)
    text = re.sub(r"(?:…|\.\.\.)\s*(?:更多|more|show\s+more).*$", "", text, flags=re.IGNORECASE | re.DOTALL)
    return _clean_identity(text, max_len)


def _same_record_text(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    shorter, longer = sorted((left, right), key=len)
    if len(shorter) < 40:
        return False
    if shorter in longer:
        return True
    if len(shorter) >= 80 and shorter[:96] == longer[:96]:
        return True
    return difflib.SequenceMatcher(None, shorter[:800], longer[:800]).ratio() >= 0.92


def _resolve_record_key(
    deduped: dict[str, dict[str, Any]],
    fuzzy_buckets: dict[str, list[str]],
    record: dict[str, Any],
) -> str:
    key = _record_identity(record)
    if key in deduped or not key.startswith("text|"):
        return key
    text = _record_text_identity(record)
    if not text:
        return key
    for candidate_key in fuzzy_buckets.get(_record_fuzzy_base_key(record), []):
        candidate = deduped.get(candidate_key)
        if candidate and _same_record_text(text, _record_text_identity(candidate)):
            return candidate_key
    return key


def _remember_record_key(fuzzy_buckets: dict[str, list[str]], record: dict[str, Any], key: str) -> None:
    if not key.startswith("text|") or not _record_text_identity(record):
        return
    bucket = fuzzy_buckets.setdefault(_record_fuzzy_base_key(record), [])
    if key not in bucket:
        bucket.append(key)


def _is_non_review_page_record(record: dict[str, Any]) -> bool:
    text = str(record.get("review") or record.get("translated_review") or "").strip()
    if not text:
        return False
    platform = _clean_identity(record.get("platform"), 120).replace(" ", "_")
    has_core_review_evidence = any(
        [
            _clean_identity(record.get("rating")),
            _clean_identity(record.get("review_time")),
            _clean_identity(record.get("order_id")),
        ]
    )
    if platform == "dianping" and not (
        _clean_identity(record.get("rating")) or _clean_identity(record.get("review_time"))
    ):
        return True
    site_chrome_patterns = (
        r"商户服务|关于我们|请登录|登录/注册|去\s*APP\s*查看更多内容|查看更多内容|美食",
        r"中国最贵的将军墓|上千瓶茅台|网红大滑梯|这个商场惊见",
        r"privacy policy|terms of use|sign in|log in|register|download app",
    )
    return (not has_core_review_evidence) and any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in site_chrome_patterns)


def _record_score(record: dict[str, Any]) -> int:
    score = 0
    for field in ("platform", "country", "account", "store", "store_id", "rating", "review", "translated_review", "customer", "review_time", "order_id", "order_total"):
        if _clean_identity(record.get(field)):
            score += 4
    items = record.get("ordered_items")
    if isinstance(items, list) and items:
        score += 18 + min(len(items), 8)
        score += sum(1 for item in items if isinstance(item, dict) and _clean_identity(item.get("price") or item.get("unit_price") or item.get("order_total")))
    if _clean_identity(record.get("order_detail")):
        score += 18 + min(len(str(record.get("order_detail"))), 300) // 30
    images = _as_list(record.get("image_urls"))
    if images:
        score += 10 + min(len(images), 6)
    return score


def _has_review_signal(record: dict[str, Any]) -> bool:
    if record.get("review") not in (None, "", []) or record.get("translated_review") not in (None, "", []):
        return True
    if record.get("review_type") in {"tag_only", "rating_only"}:
        return True
    return bool(_clean_identity(record.get("rating")))


def _looks_like_manual_gate(errors: list[Any]) -> bool:
    joined = "\n".join(str(error) for error in errors)
    return bool(
        re.search(
            r"manual gate|captcha|otp|mfa|two[-\s]?factor|saved account|login|password change|initial-password|permission gate|权限|權限|验证码|驗證碼|人工",
            joined,
            re.IGNORECASE,
        )
    )


def _merge_records(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    primary, secondary = (incoming, existing) if _record_score(incoming) > _record_score(existing) else (existing, incoming)
    merged = dict(primary)
    for key, value in secondary.items():
        if not merged.get(key) and value not in (None, "", [], {}):
            merged[key] = value
        elif key == "image_urls":
            urls: list[Any] = []
            for candidate in (_as_list(merged.get(key)), _as_list(value)):
                for url in candidate:
                    if url and url not in urls:
                        urls.append(url)
            merged[key] = urls
        elif key == "ordered_items" and isinstance(value, list):
            current = merged.get(key) if isinstance(merged.get(key), list) else []
            if len(value) > len(current):
                merged[key] = value
        elif key == "order_detail" and len(str(value or "")) > len(str(merged.get(key) or "")):
            merged[key] = value
    return merged


def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    fuzzy_buckets: dict[str, list[str]] = {}
    for record in records:
        if _is_non_review_page_record(record):
            continue
        key = _resolve_record_key(deduped, fuzzy_buckets, record)
        if key in deduped:
            deduped[key] = _merge_records(deduped[key], record)
        else:
            deduped[key] = record
            _remember_record_key(fuzzy_buckets, record, key)
    return list(deduped.values())


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
    records = _dedupe_records([_normalized_record(raw, payload, run_id) for raw in reviews])
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
        for field in core_fields:
            if field == "review" and _has_review_signal(record):
                non_empty += 1
            elif record.get(field) not in (None, "", []):
                non_empty += 1
    completeness = round(non_empty / max(1, total * len(core_fields)), 4)
    order_rows = [record for record in records if record.get("order_id")]
    detail_rows = [record for record in order_rows if record.get("order_detail") or record.get("ordered_items")]
    identity_counts = Counter(_record_identity(record) for record in records)
    duplicates = sum(count - 1 for count in identity_counts.values() if count > 1)
    payload_errors = payload.get("errors") or []
    if not isinstance(payload_errors, list):
        payload_errors = [str(payload_errors)]
    manual_gate_count = 1 if payload.get("manual_gate_required") or _looks_like_manual_gate(payload_errors) else 0
    missing_core = [
        {
            "index": index,
            "missing": [
                field
                for field in core_fields
                if not (field == "review" and _has_review_signal(record)) and record.get(field) in (None, "", [])
            ],
        }
        for index, record in enumerate(records, start=1)
        if any(
            not (field == "review" and _has_review_signal(record)) and record.get(field) in (None, "", [])
            for field in core_fields
        )
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
        "manual_gate_count": manual_gate_count,
        "error_count": len(payload_errors),
        "tag_only_count": sum(1 for record in records if record.get("review_type") == "tag_only"),
        "rating_only_count": sum(1 for record in records if record.get("review_type") == "rating_only"),
        "errors": payload_errors,
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
