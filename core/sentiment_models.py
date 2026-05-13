"""
舆情监控数据模型
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SentimentArticle:
    id: str              # sha256(url)[:12]
    keyword: str         # 监控关键词，如 "喜茶"
    source: str          # "百度新闻" | "微博" | "知乎" | "36氪" | "虎嗅"
    title: str
    url: str
    snippet: str         # 摘要/正文前200字
    author: str
    publish_time: str    # ISO8601 字符串
    crawl_time: str      # ISO8601 字符串
    sentiment: str       # "正面" | "负面" | "中性"
    tags: str            # 逗号分隔关键词

    @staticmethod
    def make_id(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "keyword": self.keyword,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "author": self.author,
            "publish_time": self.publish_time,
            "crawl_time": self.crawl_time,
            "sentiment": self.sentiment,
            "tags": self.tags,
        }
