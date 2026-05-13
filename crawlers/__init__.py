"""
爬虫工厂 v4 - 支持 strategy 参数传递，支持 8 个平台
"""
from core.models import Platform
from .base import BaseCrawler
from .meituan import MeituanCrawler
from .eleme import ElemeCrawler
from .douyin import DouyinCrawler
from .dianping import DianpingCrawler
from .google_maps import GoogleMapsCrawler
from .keeta import KeetaCrawler
from .openrice import OpenRiceCrawler
from .hungry_panda import HungryPandaCrawler

_REGISTRY: dict[Platform, type[BaseCrawler]] = {
    Platform.MEITUAN:     MeituanCrawler,
    Platform.ELEME:       ElemeCrawler,
    Platform.DOUYIN:      DouyinCrawler,
    Platform.DIANPING:    DianpingCrawler,
    Platform.GOOGLE_MAPS: GoogleMapsCrawler,
    Platform.KEETA:       KeetaCrawler,
    Platform.OPENRICE:    OpenRiceCrawler,
    Platform.HUNGRY_PANDA: HungryPandaCrawler,
}


def get_crawler(
    platform: Platform,
    headless: bool = True,
    proxy: str | None = None,
    strategy: str = "hybrid",
    **kwargs,
) -> BaseCrawler:
    """
    获取平台爬虫实例。
    kwargs 传递给具体爬虫（如 KeetaCrawler 的 days/rating_filter）。
    """
    cls = _REGISTRY.get(platform)
    if not cls:
        raise ValueError(f"不支持的平台: {platform}，可用: {list(_REGISTRY.keys())}")
    return cls(headless=headless, proxy=proxy, strategy=strategy, **kwargs)


__all__ = ["get_crawler", "BaseCrawler", "_REGISTRY"]
