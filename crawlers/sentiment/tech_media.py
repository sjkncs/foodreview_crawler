"""
科技媒体舆情爬虫 — 36氪 + 虎嗅
36氪: https://36kr.com/search/articles/<keyword>
虎嗅: https://www.huxiu.com/search.html?q=<keyword>
策略: DOM parse
"""
from __future__ import annotations
import logging
from datetime import datetime
from urllib.parse import quote

from core.sentiment_models import SentimentArticle
from crawlers.sentiment.base_sentiment import (
    BaseSentimentCrawler, classify_sentiment, extract_tags, parse_relative_time
)

logger = logging.getLogger(__name__)


class TechMediaCrawler(BaseSentimentCrawler):
    source_name = "科技媒体"

    async def search(self, keyword: str, days: int = 7) -> list[SentimentArticle]:
        articles: list[SentimentArticle] = []
        try:
            await self._start_browser()
            articles += await self._crawl_36kr(keyword, days)
            articles += await self._crawl_huxiu(keyword, days)
        except Exception as e:
            logger.error("科技媒体爬虫异常: %s", e)
        finally:
            await self._close_browser()

        logger.info("科技媒体共采集 %d 条", len(articles))
        return articles

    async def _crawl_36kr(self, keyword: str, days: int) -> list[SentimentArticle]:
        articles: list[SentimentArticle] = []
        try:
            page = await self._context.new_page()
            url = f"https://36kr.com/search/articles/{quote(keyword)}"
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            await self._random_sleep(1.5, 2.5)

            items = await page.query_selector_all(
                ".article-item, .search-article-item, [class*='article-item']"
            )
            for item in items:
                try:
                    title_el = await item.query_selector(
                        "a.article-item-title, h3 a, [class*='title'] a, a"
                    )
                    if not title_el:
                        continue
                    title = (await title_el.inner_text()).strip()
                    href = await title_el.get_attribute("href") or ""
                    if not href or not title:
                        continue
                    if href.startswith("/"):
                        href = "https://36kr.com" + href

                    snippet_el = await item.query_selector(
                        ".article-item-description, [class*='description'], p"
                    )
                    snippet = (await snippet_el.inner_text()).strip()[:200] if snippet_el else ""

                    author_el = await item.query_selector(
                        ".article-item-author, [class*='author']"
                    )
                    author = (await author_el.inner_text()).strip() if author_el else "36氪"

                    time_el = await item.query_selector(
                        ".article-item-time, [class*='time'], time"
                    )
                    time_text = (await time_el.inner_text()).strip() if time_el else ""
                    publish_time = parse_relative_time(time_text) or datetime.now().isoformat()

                    if not self._is_within_days(publish_time, days):
                        continue

                    full_text = title + " " + snippet
                    art = SentimentArticle(
                        id=SentimentArticle.make_id(href),
                        keyword=keyword,
                        source="36氪",
                        title=title,
                        url=href,
                        snippet=snippet,
                        author=author,
                        publish_time=publish_time,
                        crawl_time=datetime.now().isoformat(),
                        sentiment=classify_sentiment(full_text),
                        tags=extract_tags(full_text, keyword),
                    )
                    articles.append(art)
                except Exception as e:
                    logger.debug("解析36氪条目失败: %s", e)
                    continue

            await page.close()
            logger.info("36氪采集 %d 条", len(articles))
        except Exception as e:
            logger.warning("36氪爬取失败: %s", e)
        return articles

    async def _crawl_huxiu(self, keyword: str, days: int) -> list[SentimentArticle]:
        articles: list[SentimentArticle] = []
        try:
            page = await self._context.new_page()
            url = f"https://www.huxiu.com/search.html?q={quote(keyword)}"
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            await self._random_sleep(1.5, 2.5)

            items = await page.query_selector_all(
                ".article-item, .search-item, [class*='article-item']"
            )
            for item in items:
                try:
                    title_el = await item.query_selector(
                        "a.article-item-title, h2 a, h3 a, [class*='title'] a"
                    )
                    if not title_el:
                        continue
                    title = (await title_el.inner_text()).strip()
                    href = await title_el.get_attribute("href") or ""
                    if not href or not title:
                        continue
                    if href.startswith("/"):
                        href = "https://www.huxiu.com" + href

                    snippet_el = await item.query_selector(
                        "[class*='description'], [class*='summary'], p"
                    )
                    snippet = (await snippet_el.inner_text()).strip()[:200] if snippet_el else ""

                    author_el = await item.query_selector("[class*='author'], .author")
                    author = (await author_el.inner_text()).strip() if author_el else "虎嗅"

                    time_el = await item.query_selector("[class*='time'], time, .time")
                    time_text = (await time_el.inner_text()).strip() if time_el else ""
                    publish_time = parse_relative_time(time_text) or datetime.now().isoformat()

                    if not self._is_within_days(publish_time, days):
                        continue

                    full_text = title + " " + snippet
                    art = SentimentArticle(
                        id=SentimentArticle.make_id(href),
                        keyword=keyword,
                        source="虎嗅",
                        title=title,
                        url=href,
                        snippet=snippet,
                        author=author,
                        publish_time=publish_time,
                        crawl_time=datetime.now().isoformat(),
                        sentiment=classify_sentiment(full_text),
                        tags=extract_tags(full_text, keyword),
                    )
                    articles.append(art)
                except Exception as e:
                    logger.debug("解析虎嗅条目失败: %s", e)
                    continue

            await page.close()
            logger.info("虎嗅采集 %d 条", len(articles))
        except Exception as e:
            logger.warning("虎嗅爬取失败: %s", e)
        return articles
