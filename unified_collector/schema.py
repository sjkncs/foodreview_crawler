from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


TimeRangeType = Literal["last_days", "fixed"]
ExecutionMode = Literal["auto", "api", "dom", "visual", "ocr"]
OutputFormat = Literal["json", "csv", "excel"]


DEFAULT_FIELDS: tuple[str, ...] = (
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
    "review_id",
    "review_type",
    "reply_status",
    "review_quality",
)


@dataclass(frozen=True)
class TimeRange:
    type: TimeRangeType = "last_days"
    days: int = 7
    start_date: str = ""
    end_date: str = ""

    def validate(self) -> None:
        if self.type not in ("last_days", "fixed"):
            raise ValueError(f"unsupported time range type: {self.type}")
        if self.type == "last_days" and self.days <= 0:
            raise ValueError("time_range.days must be positive")
        if self.type == "fixed" and (not self.start_date or not self.end_date):
            raise ValueError("fixed time range requires start_date and end_date")


@dataclass(frozen=True)
class SafetyPolicy:
    safe_mode: bool = True
    allow_login: bool = True
    allow_search: bool = True
    allow_open_detail: bool = True
    allow_manual_gate: bool = True
    deny_write_actions: tuple[str, ...] = (
        "submit",
        "send",
        "save",
        "reply",
        "delete",
        "remove",
        "confirm",
        "publish",
        "支付",
        "提交",
        "发送",
        "發送",
        "保存",
        "儲存",
        "回复",
        "回覆",
        "删除",
        "刪除",
        "确认",
        "確認",
        "置顶",
        "置頂",
        "屏蔽",
        "拉黑",
    )


@dataclass(frozen=True)
class OutputPolicy:
    output_dir: str = ""
    output_prefix: str = ""
    formats: tuple[OutputFormat, ...] = ("json", "csv")


@dataclass(frozen=True)
class CollectionTask:
    platform: str
    account: str = ""
    country: str = ""
    stores: str | list[str] = "all"
    time_range: TimeRange = field(default_factory=TimeRange)
    fields: tuple[str, ...] = DEFAULT_FIELDS
    mode: ExecutionMode = "auto"
    max_reviews: int = 100
    safety: SafetyPolicy = field(default_factory=SafetyPolicy)
    output: OutputPolicy = field(default_factory=OutputPolicy)
    options: dict[str, Any] = field(default_factory=dict)
    store_registry: str = ""

    def validate(self) -> None:
        if not self.platform:
            raise ValueError("platform is required")
        if self.mode not in ("auto", "api", "dom", "visual", "ocr"):
            raise ValueError(f"unsupported execution mode: {self.mode}")
        if self.max_reviews <= 0:
            raise ValueError("max_reviews must be positive")
        self.time_range.validate()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QualityReport:
    field_completeness: float = 0.0
    detail_coverage: float = 0.0
    image_url_count: int = 0
    duplicate_count: int = 0
    out_of_range_count: int = 0
    manual_gate_count: int = 0
    error_count: int = 0


@dataclass(frozen=True)
class ExecutorResult:
    ok: bool
    platform: str
    account: str
    json_path: str = ""
    csv_path: str = ""
    excel_path: str = ""
    review_count: int = 0
    store_count: int = 0
    errors: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)
    stdout_tail: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
