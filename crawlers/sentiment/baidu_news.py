"""
百度新闻舆情爬虫
URL: https://news.baidu.com/search?word=<keyword>
策略: DOM parse，最多爬取 5 页
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


class BaiduNewsCrawler(BaseSentimentCrawler):
    source_name = "百度新闻"

    async def search(self, keyword: str, days: int = 7) -> list[SentimentArticle]:
        articles: list[SentimentArticle] = []
        # 百度对无头浏览器有反爬，强制有头模式
        self.headless = False
        try:
            await self._start_browser()
            page = await self._context.new_page()

            for page_num in range(3):  # 最多 3 页
                pn = page_num * 10
                url = f"https://www.baidu.com/s?tn=news&rtt=1&bsst=1&cl=2&wd={quote(keyword)}&pn={pn}"
                try:
                    await page.goto(url, timeout=20000)
                    await page.wait_for_load_state("domcontentloaded", timeout=10000)
                    await self._random_sleep(1.5, 2.5)
                except Exception as e:
                    logger.warning("百度新闻第%d页加载失败: %s", page_num + 1, e)
                    break

                # 提取新闻条目，百度新闻结果选择器（兼容多种页面结构）
                items = await page.query_selector_all(
                    ".result.c-container, .result-op.c-container, "
                    "[tpl='news_single'], [tpl='news_multi_hot'], "
                    ".c-container[srcid]"
                )
                if not items:
                    items = await page.query_selector_all(".result, .c-container")

                if not items:
                    logger.info("百度新闻第%d页无结果，停止翻页", page_num + 1)
                    break

                page_articles = []
                for item in items:
                    try:
                        # 标题和链接（百度新闻多种选择器）
                        title_el = await item.query_selector(
                            "h3 a, h3.c-title a, .c-title a, "
                            "a.news-title, a[data-click], "
                            "[class*='title'] a"
                        )
                        if not title_el:
                            continue
                        title = (await title_el.inner_text()).strip()
                        href = (
                            await title_el.get_attribute("href")
                            or await title_el.get_attribute("data-href")
                            or ""
                        )
                        if not title or not href:
                            continue
                        # 百度跳转链接尝试获取真实 URL
                        if "baidu.com/link" in href or href.startswith("/"):
                            href = await title_el.get_attribute("data-href") or href

                        # 摘要
                        snippet_el = await item.query_selector(
                            ".c-summary, .c-span-last, .news-summary, p"
                        )
                        snippet = (await snippet_el.inner_text()).strip()[:200] if snippet_el else ""

                        # 来源和时间
                        meta_el = await item.query_selector(
                            ".c-color-gray2, .c-author, .news-from, .c-font-normal"
                        )
                        meta_text = (await meta_el.inner_text()).strip() if meta_el else ""

                        # 解析时间（meta_text 可能包含 "来源 · 1小时前"）
                        publish_time = parse_relative_time(meta_text) or datetime.now().isoformat()
                        author = meta_text.split("·")[0].strip() if "·" in meta_text else meta_text[:20]

                        if not self._is_within_days(publish_time, days):
                            continue

                        full_text = title + " " + snippet
                        art = SentimentArticle(
                            id=SentimentArticle.make_id(href),
                            keyword=keyword,
                            source=self.source_name,
                            title=title,
                            url=href,
                            snippet=snippet,
                            author=author,
                            publish_time=publish_time,
                            crawl_time=datetime.now().isoformat(),
                            sentiment=classify_sentiment(full_text),
                            tags=extract_tags(full_text, keyword),
                        )
                        page_articles.append(art)
                    except Exception as e:
                        logger.debug("解析百度新闻条目失败: %s", e)
                        continue

                articles.extend(page_articles)
                logger.info("百度新闻第%d页: 采集 %d 条", page_num + 1, len(page_articles))

                if len(page_articles) == 0:
                    break

            await page.close()
        except Exception as e:
            logger.error("百度新闻爬虫异常: %s", e)
        finally:
            await self._close_browser()

        logger.info("百度新闻共采集 %d 条", len(articles))
        return articles
