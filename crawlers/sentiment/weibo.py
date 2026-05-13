"""
微博搜索舆情爬虫
URL: https://s.weibo.com/weibo?q=<keyword>&timescope=custom:7d
策略: DOM parse + 模拟滚动
注意: 微博需要登录，首次运行会弹出登录页，手动登录后 cookie 自动保存
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

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "../../data/weibo_cookies.json")


class WeiboCrawler(BaseSentimentCrawler):
    source_name = "微博"

    async def search(self, keyword: str, days: int = 7) -> list[SentimentArticle]:
        articles: list[SentimentArticle] = []
        # 微博需要登录，首次运行用 headful 模式
        headless = self.headless and os.path.exists(COOKIE_FILE)
        self.headless = headless

        try:
            await self._start_browser()
            page = await self._context.new_page()

            # 加载已保存的 cookie
            if os.path.exists(COOKIE_FILE):
                with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                await self._context.add_cookies(cookies)
                logger.info("微博: 已加载保存的 cookie")

            # 构造搜索 URL（近7天）
            url = f"https://s.weibo.com/weibo?q={quote(keyword)}&typeall=1&suball=1&timescope=custom:{days}d&Refer=g"
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            await self._random_sleep(2.0, 3.0)

            # 检查是否需要登录
            if "passport.weibo.com" in page.url or await page.query_selector("#loginAction"):
                logger.warning("微博需要登录！请在浏览器中手动登录，完成后程序将自动继续...")
                # 等待用户登录（最多等 120 秒）
                try:
                    await page.wait_for_url("**/s.weibo.com/**", timeout=120000)
                except Exception:
                    logger.error("微博登录超时，跳过微博采集")
                    await page.close()
                    return articles

                # 保存 cookie 供下次使用
                cookies = await self._context.cookies()
                os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
                with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, ensure_ascii=False)
                logger.info("微博 cookie 已保存到 %s", COOKIE_FILE)

            seen_ids: set[str] = set()

            for scroll_round in range(8):  # 最多滚动 8 次
                cards = await page.query_selector_all(".card-wrap, [action-type='feed_list_item']")

                for card in cards:
                    try:
                        # 微博正文
                        content_el = await card.query_selector(
                            ".txt, p.txt, [node-type='feed_list_content']"
                        )
                        if not content_el:
                            continue
                        content = (await content_el.inner_text()).strip()
                        if not content or len(content) < 5:
                            continue

                        # 链接
                        link_el = await card.query_selector("a.from, .from a")
                        href = await link_el.get_attribute("href") if link_el else ""
                        if not href:
                            href = page.url
                        if href.startswith("//"):
                            href = "https:" + href

                        art_id = SentimentArticle.make_id(href + content[:20])
                        if art_id in seen_ids:
                            continue
                        seen_ids.add(art_id)

                        # 作者
                        author_el = await card.query_selector(".name, a.name")
                        author = (await author_el.inner_text()).strip() if author_el else ""

                        # 时间
                        time_el = await card.query_selector(".from a, .time")
                        time_text = (await time_el.inner_text()).strip() if time_el else ""
                        publish_time = parse_relative_time(time_text) or datetime.now().isoformat()

                        if not self._is_within_days(publish_time, days):
                            continue

                        art = SentimentArticle(
                            id=art_id,
                            keyword=keyword,
                            source=self.source_name,
                            title=content[:50] + ("..." if len(content) > 50 else ""),
                            url=href,
                            snippet=content[:200],
                            author=author,
                            publish_time=publish_time,
                            crawl_time=datetime.now().isoformat(),
                            sentiment=classify_sentiment(content),
                            tags=extract_tags(content, keyword),
                        )
                        articles.append(art)
                    except Exception as e:
                        logger.debug("解析微博条目失败: %s", e)
                        continue

                # 滚动加载更多
                prev_count = len(articles)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_sleep(2.0, 3.5)
                new_count = len(articles)
                if scroll_round > 2 and new_count == prev_count:
                    break  # 无新内容，停止滚动

            await page.close()
        except Exception as e:
            logger.error("微博爬虫异常: %s", e)
        finally:
            await self._close_browser()

        logger.info("微博共采集 %d 条", len(articles))
        return articles
