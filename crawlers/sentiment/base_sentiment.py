"""
舆情爬虫基类 — 复用 BaseCrawler 的 Playwright 启动/关闭逻辑
"""
from __future__ import annotations
import asyncio
import logging
import random
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# ── 情感分析词典 ──────────────────────────────────────────────────
POSITIVE_WORDS = [
    "好评", "推荐", "好喝", "创新", "上新", "联名", "爆款", "排队", "火爆",
    "美味", "惊艳", "回购", "必喝", "打卡", "种草", "好评如潮", "口感好",
    "新品", "限定", "热销", "受欢迎", "高颜值", "值得", "满意",
]
NEGATIVE_WORDS = [
    "投诉", "差评", "食品安全", "问题", "下架", "罚款", "虚假", "塌房", "翻车",
    "变质", "异物", "退款", "维权", "曝光", "质疑", "争议", "负面", "危机",
    "涨价", "缩水", "失望", "难喝", "踩雷", "不推荐", "避雷",
]


def classify_sentiment(text: str) -> str:
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)
    if pos > neg:
        return "正面"
    if neg > pos:
        return "负面"
    return "中性"


def extract_tags(text: str, keyword: str) -> str:
    """从文本中提取相关标签"""
    all_words = POSITIVE_WORDS + NEGATIVE_WORDS + [
        "新品", "联名", "门店", "价格", "服务", "品质", "营销", "活动",
    ]
    found = [w for w in all_words if w in text and w != keyword]
    return ",".join(found[:8])


def parse_relative_time(text: str, now: Optional[datetime] = None) -> Optional[str]:
    """
    解析中文相对时间为 ISO8601 字符串
    支持: "1小时前", "3天前", "昨天", "今天", "2天前", "刚刚", "1分钟前"
    """
    if now is None:
        now = datetime.now()
    text = text.strip()

    if "刚刚" in text or "刚才" in text:
        return now.isoformat()
    m = re.search(r"(\d+)\s*分钟前", text)
    if m:
        return (now - timedelta(minutes=int(m.group(1)))).isoformat()
    m = re.search(r"(\d+)\s*小时前", text)
    if m:
        return (now - timedelta(hours=int(m.group(1)))).isoformat()
    if "昨天" in text:
        return (now - timedelta(days=1)).isoformat()
    if "今天" in text:
        return now.isoformat()
    m = re.search(r"(\d+)\s*天前", text)
    if m:
        return (now - timedelta(days=int(m.group(1)))).isoformat()
    m = re.search(r"(\d+)\s*周前", text)
    if m:
        return (now - timedelta(weeks=int(m.group(1)))).isoformat()
    # 尝试直接解析日期格式 "2026-04-01" 或 "04-01"
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T00:00:00"
    m = re.search(r"(\d{2})-(\d{2})", text)
    if m:
        return f"{now.year}-{m.group(1)}-{m.group(2)}T00:00:00"
    return None


class BaseSentimentCrawler(ABC):
    """舆情爬虫基类，管理 Playwright 生命周期"""

    source_name: str  # 子类声明，如 "百度新闻"

    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        self.headless = headless
        self.proxy = proxy
        self._pw = None
        self._browser = None
        self._context = None

    async def _start_browser(self):
        self._pw = await async_playwright().start()
        launch_opts = {"headless": self.headless, "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled"]}
        if self.proxy:
            launch_opts["proxy"] = {"server": self.proxy}
        self._browser = await self._pw.chromium.launch(**launch_opts)
        self._context = await self._browser.new_context(
            user_agent=self._random_ua(),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            viewport={"width": 1280, "height": 800},
        )
        # 隐藏 webdriver 特征
        await self._context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    async def _close_browser(self):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    @abstractmethod
    async def search(self, keyword: str, days: int = 7) -> list:
        """子类实现：搜索关键词，返回 SentimentArticle 列表"""
        ...

    def _is_within_days(self, publish_time_iso: Optional[str], days: int) -> bool:
        """判断文章是否在 days 天内"""
        if not publish_time_iso:
            return True  # 无法判断时间则保留
        try:
            dt = datetime.fromisoformat(publish_time_iso)
            return dt >= datetime.now() - timedelta(days=days)
        except Exception:
            return True

    @staticmethod
    def _random_ua() -> str:
        return random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ])

    @staticmethod
    async def _random_sleep(min_s: float = 1.0, max_s: float = 3.0):
        await asyncio.sleep(random.uniform(min_s, max_s))
