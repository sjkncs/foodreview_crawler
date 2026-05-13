"""
知乎搜索舆情爬虫
URL: https://www.zhihu.com/search?q=<keyword>&type=content
策略: DOM parse，采集问答和文章
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from urllib.parse import quote

from core.sentiment_models import SentimentArticle
from crawlers.sentiment.base_sentiment import (
    BaseSentimentCrawler, classify_sentiment, extract_tags, parse_relative_time
)

logger = logging.getLogger(__name__)

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "../../data/zhihu_cookies.json")


class ZhihuCrawler(BaseSentimentCrawler):
    source_name = "知乎"

    async def search(self, keyword: str, days: int = 7) -> list[SentimentArticle]:
        articles: list[SentimentArticle] = []
        headless = self.headless and os.path.exists(COOKIE_FILE)
        self.headless = headless

        try:
            await self._start_browser()
            page = await self._context.new_page()

            # 加载 cookie
            if os.path.exists(COOKIE_FILE):
                with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                await self._context.add_cookies(cookies)
                logger.info("知乎: 已加载保存的 cookie")

            url = f"https://www.zhihu.com/search?q={quote(keyword)}&type=content"
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await self._random_sleep(2.0, 3.0)

            # 检查登录状态
            if "signin" in page.url or await page.query_selector(".SignContainer"):
                logger.warning("知乎需要登录！请在浏览器中手动登录...")
                try:
                    await page.wait_for_url("**/zhihu.com/search**", timeout=120000)
                except Exception:
                    logger.error("知乎登录超时，跳过知乎采集")
                    await page.close()
                    return articles

                cookies = await self._context.cookies()
                os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
                with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, ensure_ascii=False)
                logger.info("知乎 cookie 已保存")

            seen_ids: set[str] = set()

            for scroll_round in range(6):
                # 知乎搜索结果卡片
                cards = await page.query_selector_all(
                    ".SearchResult-Card, [class*='SearchResult'], .Card"
                )

                for card in cards:
                    try:
                        # 标题
                        title_el = await card.query_selector(
                            "h2 a, .ContentItem-title a, [class*='title'] a"
                        )
                        if not title_el:
                            continue
                        title = (await title_el.inner_text()).strip()
                        href = await title_el.get_attribute("href") or ""
                        if not href:
                            continue
                        if href.startswith("/"):
                            href = "https://www.zhihu.com" + href

                        art_id = SentimentArticle.make_id(href)
                        if art_id in seen_ids:
                            continue
                        seen_ids.add(art_id)

                        # 摘要
                        snippet_el = await card.query_selector(
                            ".RichContent-inner, .ContentItem-excerpt, [class*='excerpt']"
                        )
                        snippet = (await snippet_el.inner_text()).strip()[:200] if snippet_el else ""

                        # 作者
                        author_el = await card.query_selector(
                            ".AuthorInfo-name, [class*='author'] .UserLink-link"
                        )
                        author = (await author_el.inner_text()).strip() if author_el else ""

                        # 时间
                        time_el = await card.query_selector(
                            ".ContentItem-time, [class*='time'], time"
                        )
                        time_text = (await time_el.inner_text()).strip() if time_el else ""
                        publish_time = parse_relative_time(time_text) or datetime.now().isoformat()

                        if not self._is_within_days(publish_time, days):
                            continue

                        full_text = title + " " + snippet
                        art = SentimentArticle(
                            id=art_id,
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
                        articles.append(art)
                    except Exception as e:
                        logger.debug("解析知乎条目失败: %s", e)
                        continue

                # 滚动
                prev_count = len(articles)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_sleep(2.0, 3.0)
                if scroll_round > 2 and len(articles) == prev_count:
                    break

            await page.close()
        except Exception as e:
            logger.error("知乎爬虫异常: %s", e)
        finally:
            await self._close_browser()

        logger.info("知乎共采集 %d 条", len(articles))
        return articles
