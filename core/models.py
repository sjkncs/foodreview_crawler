"""
数据模型定义 - 使用 dataclass 保持不可变性
表头字段对齐：店铺名称 平台 用户名 评分 评论内容 翻译内容 发布日期 采集时间 图片URLs 商家回复 子评分 页面URL
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    MEITUAN     = "美团外卖"
    ELEME       = "饿了么"
    DOUYIN      = "抖音外卖"
    DIANPING    = "大众点评"
    GOOGLE_MAPS = "Google Maps"
    KEETA       = "KeeTa"
    OPENRICE    = "OpenRice"
    HUNGRY_PANDA = "Hungry Panda"


class SentimentLabel(str, Enum):
    POSITIVE = "正面"
    NEGATIVE = "负面"
    NEUTRAL  = "中性"


class ReviewType(str, Enum):
    REVIEW    = "评论"
    COMPLAINT = "客诉"


class OcrStrategy(str, Enum):
    """OCR / 爬虫策略，可在设置页切换"""
    API_INTERCEPT  = "api_intercept"   # 拦截 XHR/Fetch（速度最快）
    DOM_PARSE      = "dom_parse"       # Playwright CSS 选择器解析 DOM
    OCR_SCREENSHOT = "ocr_screenshot"  # 截图 + OCR（反爬最强备用）
    HYBRID         = "hybrid"          # 先尝试 API 拦截，失败回退 OCR


@dataclass(frozen=True)
class Review:
    """
    评论/客诉完整数据模型（不可变）
    字段与表单表头一一对应：
      店铺名称 | 平台 | 用户名 | 评分 | 评论内容 | 翻译内容
      发布日期 | 采集时间 | 图片URLs | 商家回复 | 子评分 | 页面URL
    """
    # ── 核心标识 ──────────────────────────────────────────────
    id:             Optional[int]
    platform:       Platform
    shop_name:      str          # 店铺名称
    shop_id:        str

    # ── 表单主字段 ────────────────────────────────────────────
    reviewer_name:  str          # 用户名
    content:        str          # 评论内容
    rating:         float        # 评分（1-5）
    translated_content: Optional[str] = None   # 翻译内容（中文翻译）
    published_at:   Optional[datetime] = None  # 发布日期（原始平台时间）
    crawled_at:     Optional[datetime] = None  # 采集时间
    image_urls:     tuple[str, ...] = field(default_factory=tuple)  # 图片URLs
    merchant_reply: Optional[str] = None       # 商家回复原文
    reply_translation: Optional[str] = None   # 商家回复翻译
    child_rating:   Optional[str] = None       # 子评分（口味/配送/包装等，JSON）
    page_url:       Optional[str] = None       # 页面URL

    # ── 类型与分析 ────────────────────────────────────────────
    review_type:    ReviewType = ReviewType.REVIEW
    sentiment:      Optional[SentimentLabel] = None
    sentiment_score: Optional[float] = None    # -1.0 ~ 1.0
    keywords:       tuple[str, ...] = field(default_factory=tuple)
    suggested_reply: Optional[str] = None
    is_replied:     bool = False

    # ── 爬取元数据 ────────────────────────────────────────────
    raw_data:       Optional[str] = None       # JSON 原始数据备份
    ocr_strategy:   Optional[str] = None       # 实际使用的爬取策略

    # ── 不可变更新方法 ────────────────────────────────────────
    def _evolve(self, **kwargs) -> "Review":
        """通用不可变更新，返回新实例"""
        d = {f.name: getattr(self, f.name) for f in self.__dataclass_fields__.values()}
        d.update(kwargs)
        return Review(**d)

    def with_sentiment(self, label: SentimentLabel, score: float) -> "Review":
        return self._evolve(sentiment=label, sentiment_score=score)

    def with_keywords(self, keywords: tuple[str, ...]) -> "Review":
        return self._evolve(keywords=keywords)

    def with_reply(self, reply: str) -> "Review":
        return self._evolve(suggested_reply=reply)

    def with_translation(self, content_tr: str, reply_tr: Optional[str] = None) -> "Review":
        return self._evolve(translated_content=content_tr, reply_translation=reply_tr)

    # ── 兼容旧字段 ────────────────────────────────────────────
    @property
    def created_at(self) -> datetime:
        """向后兼容旧代码，等同于 published_at 或 crawled_at"""
        return self.published_at or self.crawled_at or datetime.now()


@dataclass(frozen=True)
class Shop:
    """商家信息"""
    id:             Optional[int]
    platform:       Platform
    shop_id:        str
    name:           str
    category:       str
    address:        str
    rating:         float
    review_count:   int
    registered_at:  Optional[datetime] = None
    extra:          Optional[str] = None


@dataclass(frozen=True)
class CrawlTask:
    """爬取任务"""
    id:            Optional[int]
    platform:      Platform
    shop_id:       str
    shop_name:     str
    status:        str            # pending / running / done / failed
    started_at:    Optional[datetime]
    finished_at:   Optional[datetime]
    total_fetched: int = 0
    error_msg:     Optional[str] = None
    ocr_strategy:  str = OcrStrategy.HYBRID.value


@dataclass(frozen=True)
class ReportSummary:
    """报表摘要"""
    platform:       Platform
    shop_name:      str
    total_reviews:  int
    avg_rating:     float
    positive_count: int
    negative_count: int
    neutral_count:  int
    top_keywords:   tuple[str, ...]
    generated_at:   datetime
