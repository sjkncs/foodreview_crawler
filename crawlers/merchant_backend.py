"""
Recipe-driven merchant backend crawler.

This module keeps the reusable "blocks" for merchant portals in one place:
login/cookie reuse, branch entry, review-page navigation, API interception,
DOM table extraction, pagination, and field normalization. Platform modules
only provide a MerchantReviewRecipe plus any truly custom overrides.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import re
from typing import AsyncGenerator, Mapping, Optional
from urllib.parse import urlparse

from core.models import OcrStrategy, Platform, Review, ReviewType
from .base import BaseCrawler

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MerchantReviewRecipe:
    name: str
    platform: Platform
    cookie_dir_name: str
    review_path: str
    login_path: str = "/master/login"
    login_check_path: str = ""
    management_path: str = ""
    persistent_profile_dir_name: str = ""
    browser_channel: str = ""
    login_timeout_ms: int = 180_000
    credential_env_prefix: str = ""
    credential_host_env_prefixes: Mapping[str, str] = field(default_factory=dict)
    login_username_selectors: tuple[str, ...] = (
        "input[name='username']",
        "input[name='account']",
        "input[name='phone']",
        "input[name='mobile']",
        "input[type='tel']",
        "input[autocomplete='username']",
        "input[placeholder*='账号']",
        "input[placeholder*='帳號']",
        "input[placeholder*='手机']",
        "input[placeholder*='手機']",
        "input[placeholder*='手机号']",
        "input[placeholder*='Phone']",
        "input[placeholder*='Account']",
        "input[placeholder*='Email']",
        "input[type='text']",
    )
    login_password_selectors: tuple[str, ...] = (
        "input[type='password']",
        "input[name='password']",
        "input[autocomplete='current-password']",
        "input[placeholder*='密码']",
        "input[placeholder*='密碼']",
        "input[placeholder*='Password']",
    )
    login_submit_selectors: tuple[str, ...] = (
        "button[type='submit']",
        "button:has-text('登录')",
        "button:has-text('登入')",
        "button:has-text('Login')",
        "button:has-text('Sign in')",
        "button:has-text('Log in')",
        "[role='button']:has-text('登录')",
        "[role='button']:has-text('Login')",
        "[role='button']:has-text('Sign in')",
    )
    api_host_keyword: str = ""
    api_required_paths: tuple[str, ...] = ()
    api_patterns: tuple[str, ...] = (
        "appraise", "review", "comment", "rating", "reply", "feedback",
    )
    logged_in_url_fragments: tuple[str, ...] = ()
    logged_in_texts: tuple[str, ...] = ()
    review_texts: tuple[str, ...] = ()
    all_review_texts: tuple[str, ...] = ()
    not_replied_texts: tuple[str, ...] = ()
    enter_store_texts: tuple[str, ...] = ()
    store_trigger_selectors: tuple[str, ...] = (
        "[class*='shop']",
        "[class*='store']",
        "[class*='merchant']",
        "[class*='dropdown']",
        "[class*='select']",
    )
    store_trigger_text_regex: str = (
        r"shop|store|merchant|branch|门店|店铺|分店|餐厅|매장|succursale"
    )
    row_selectors: tuple[str, ...] = (
        "tr",
        ".ant-table-row",
        "[class*='table-row']",
    )
    review_card_selectors: tuple[str, ...] = (
        ".review-item",
        "[class*='ReviewItem']",
        "[class*='review-card']",
        "[class*='appraise-item']",
        "[class*='comment-item']",
        "tr.ant-table-row",
    )
    content_selectors: tuple[str, ...] = (
        "[class*='review-content']",
        "[class*='comment-text']",
        "[class*='comment-content']",
        "[class*='content']",
        "[class*='desc']",
        "p",
    )
    reviewer_selectors: tuple[str, ...] = (
        "[class*='reviewer-name']",
        "[class*='user-name']",
        "[class*='nickname']",
        "[class*='author']",
        ".name",
    )
    date_selectors: tuple[str, ...] = (
        "[class*='review-date']",
        "[class*='review-time']",
        "[class*='date-time']",
        "[class*='date']",
        "time",
    )
    reply_selectors: tuple[str, ...] = (
        "[class*='reply-content']",
        "[class*='merchant-reply']",
        "[class*='owner-reply']",
        "[class*='reply']",
    )
    image_selectors: tuple[str, ...] = (
        "[class*='review-image'] img",
        "[class*='photo'] img",
        "img[src*='review']",
    )
    next_selectors: tuple[str, ...] = (
        ".ant-pagination-next:not(.ant-pagination-disabled)",
        "button:has-text('Next')",
        "button:has-text('下一页')",
        "a:has-text('Next')",
        "[class*='next']:not([disabled])",
    )
    table_content_col: int = 0
    table_order_col: int = 1
    table_date_col: int = 2
    sub_rating_labels: Mapping[str, str] = field(default_factory=dict)
    list_keys: tuple[str, ...] = (
        "list", "records", "items", "reviews", "appraises", "comments",
    )
    api_content_fields: tuple[str, ...] = (
        "content", "reviewContent", "commentContent", "comment",
        "review", "appraiseContent", "feedback", "text",
    )
    api_reviewer_fields: tuple[str, ...] = (
        "nickname", "reviewerName", "userName", "username",
    )
    api_reviewer_objects: tuple[str, ...] = ("reviewer", "user", "customer", "member")
    api_rating_fields: tuple[str, ...] = (
        "rating", "score", "overallScore", "star", "stars", "reviewScore",
    )
    api_date_fields: tuple[str, ...] = (
        "reviewTime", "commentTime", "createdAt", "created_at", "createTime", "time",
    )
    api_reply_fields: tuple[str, ...] = (
        "reply", "merchantReply", "replyInfo", "replyContent",
    )
    api_image_fields: tuple[str, ...] = ("images", "pics", "photos")
    api_sub_rating_fields: tuple[tuple[str, str], ...] = ()

    @property
    def review_state_texts(self) -> tuple[str, ...]:
        return self.review_texts + self.all_review_texts + self.not_replied_texts


class RecipeMerchantCrawler(BaseCrawler):
    recipe: MerchantReviewRecipe

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        strategy: str = OcrStrategy.HYBRID.value,
        shop_name: str = "Merchant",
        shop_hint: Optional[str] = None,
        login_url: Optional[str] = None,
        login_username: Optional[str] = None,
        login_password: Optional[str] = None,
    ):
        super().__init__(headless=headless, proxy=proxy, strategy=strategy)
        self._shop_name = shop_name
        self._shop_hint = (shop_hint or "").strip()
        self._login_url = self._normalize_login_url(login_url or "")
        self._login_username = (login_username or "").strip()
        self._login_password = login_password or ""

    async def _start_browser(self) -> None:
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()
        launch_opts: dict = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--lang=zh-CN",
            ],
        }
        if self.proxy:
            launch_opts["proxy"] = {"server": self.proxy}

        context_opts: dict = {
            "user_agent": self._random_ua(),
            "viewport": {"width": 1440, "height": 900},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "accept_downloads": True,
        }
        profile_dir = self._persistent_profile_dir()
        if profile_dir:
            profile_dir.mkdir(parents=True, exist_ok=True)
            if self.recipe.browser_channel:
                launch_opts["channel"] = self.recipe.browser_channel
            try:
                self._browser = None
                self._context = await self._pw.chromium.launch_persistent_context(
                    str(profile_dir),
                    **launch_opts,
                    **context_opts,
                )
            except Exception:
                launch_opts.pop("channel", None)
                self._context = await self._pw.chromium.launch_persistent_context(
                    str(profile_dir),
                    **launch_opts,
                    **context_opts,
                )
            await self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN','zh','en'] });
            """)
            return

        self._browser = await self._pw.chromium.launch(**launch_opts)
        storage_state = self._initial_storage_state_file()
        if storage_state and storage_state.exists():
            context_opts["storage_state"] = str(storage_state)
        self._context = await self._browser.new_context(**context_opts)
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN','zh','en'] });
        """)

    def _get_shop_url(self, shop_id: str) -> str:
        return self._review_url(shop_id)

    async def fetch_reviews(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        page = await self._context.new_page()
        api_queue: list[dict] = []
        yielded = 0

        async def on_response(resp):
            try:
                url_lower = resp.url.lower()
                if resp.status != 200:
                    return
                if self.recipe.api_host_keyword and self.recipe.api_host_keyword.lower() not in url_lower:
                    return
                if self.recipe.api_required_paths and not any(path.lower() in url_lower for path in self.recipe.api_required_paths):
                    return
                if not any(pattern.lower() in url_lower for pattern in self.recipe.api_patterns):
                    return
                content_type = (resp.headers.get("content-type") or "").lower()
                if "json" not in content_type:
                    return
                api_queue.append({"body": await resp.json(), "url": resp.url})
            except Exception:
                return

        try:
            page = await self._ensure_logged_in(page, shop_id)
            self._context.on("response", on_response)
            page = await self._prepare_review_page(page, shop_id, shop_name)

            for _ in range(max_pages):
                await page.wait_for_timeout(2500)
                while api_queue:
                    item = api_queue.pop(0)
                    batch = self._parse_api_response(
                        item["body"], shop_id, shop_name, review_type, item["url"]
                    )
                    if batch:
                        yielded += len(batch)
                        yield batch
                if not await self._go_next_page(page):
                    break

            await self._save_cookies(shop_id)
        finally:
            await page.close()

        if yielded == 0:
            raise RuntimeError(f"{self.recipe.name} 未捕获到评论 API，准备降级到 DOM 解析")

    async def fetch_reviews_dom(
        self,
        shop_id: str,
        shop_name: str,
        max_pages: int,
        review_type: ReviewType,
    ) -> AsyncGenerator[list[Review], None]:
        page = await self._context.new_page()
        seen: set[str] = set()
        yielded = 0
        try:
            page = await self._ensure_logged_in(page, shop_id)
            page = await self._prepare_review_page(page, shop_id, shop_name)

            for _ in range(max_pages):
                await page.wait_for_timeout(1800)
                batch = await self._parse_dom(page, shop_id, shop_name, review_type, seen)
                if batch:
                    yielded += len(batch)
                    yield batch
                if not await self._go_next_page(page):
                    break

            await self._save_cookies(shop_id)
        finally:
            await page.close()

        if yielded == 0:
            raise RuntimeError(f"{self.recipe.name} DOM 页面未解析到评论")

    async def _prepare_review_page(self, page, shop_id: str, shop_name: str):
        page = await self._ensure_store_selected(page, shop_name) or page
        await self._open_review_page(page, shop_id)
        selected_page = await self._ensure_store_selected(page, shop_name)
        if selected_page:
            page = selected_page
            await self._open_review_page(page, shop_id)
        await self._apply_filters(page)
        return page

    async def _ensure_logged_in(self, page, shop_id: str):
        cookies_file = self._cookies_file(shop_id)
        target_url = self._entry_url(shop_id)

        # First trust the current browser profile/session. Merchant portals often
        # store the real login token in localStorage rather than cookies, so a
        # persisted profile can be logged in even when no cookie file exists.
        try:
            await page.goto(self._login_check_url(shop_id), wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2500)
            if await self._is_logged_in(page):
                logger.info("[%s] 已检测到现有登录态，跳过登录表单", self.recipe.name)
                if page.url != target_url:
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(2500)
                return page
        except Exception as exc:
            logger.debug("[%s] 初始登录态检测失败: %s", self.recipe.name, exc)

        if cookies_file.exists():
            try:
                await self._context.add_cookies(json.loads(cookies_file.read_text(encoding="utf-8")))
                await page.goto(self._login_check_url(shop_id), wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                if await self._is_logged_in(page):
                    logger.info("[%s] 使用已保存 Cookie 登录成功", self.recipe.name)
                    if page.url != target_url:
                        await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(2500)
                    return page
            except Exception as exc:
                logger.warning("[%s] 注入 Cookie 失败: %s", self.recipe.name, exc)

        username, password = self._resolve_login_credentials(shop_id)
        has_credentials = bool(username and password)

        logger.info("[%s] 需要登录，等待最多 %.0f 秒...", self.recipe.name, self.recipe.login_timeout_ms / 1000)
        if self.headless and not has_credentials:
            await self._close_browser()
            self.headless = False
            await self._start_browser()
            page = await self._context.new_page()

        await page.goto(self._login_page(shop_id), timeout=30000)
        await page.wait_for_timeout(2000)
        if has_credentials and not await self._is_logged_in(page):
            await self._try_auto_login(page, shop_id, username, password)

        try:
            if not await self._is_logged_in(page):
                await page.wait_for_function(
                    self._logged_in_wait_js(),
                    timeout=self.recipe.login_timeout_ms,
                )
        except Exception:
            pass

        try:
            if self.recipe.review_path not in page.url:
                await page.goto(target_url, timeout=30000)
                await page.wait_for_timeout(2500)
        except Exception:
            pass

        if not await self._is_logged_in(page):
            logger.error("[%s] 登录超时或未进入后台", self.recipe.name)
            raise RuntimeError(f"{self.recipe.name} 登录超时或未进入后台")

        await self._save_cookies(shop_id)
        logger.info("[%s] 登录成功，Cookie 已保存", self.recipe.name)
        return page

    async def _is_logged_in(self, page) -> bool:
        try:
            url = page.url.lower()
            if "/login" in url or "/master/login" in url:
                return False
            if any(fragment.lower() in url for fragment in self.recipe.logged_in_url_fragments):
                return True
            for text in self.recipe.logged_in_texts + self.recipe.review_state_texts:
                loc = page.locator(f"text={text}").first
                if await loc.count() > 0 and await loc.is_visible(timeout=500):
                    return True
        except Exception:
            return False
        return False

    async def _open_review_page(self, page, shop_id: str) -> None:
        await page.goto(self._review_url(shop_id), wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        await page.wait_for_timeout(1500)
        await self._click_first_visible_text(page, self.recipe.review_texts, timeout=1000)

    async def _apply_filters(self, page) -> None:
        await self._click_first_visible_text(page, self.recipe.all_review_texts, timeout=800, wait_ms=500)

    async def _ensure_store_selected(self, page, shop_name: str):
        tokens = self._store_tokens(shop_name)
        selected_page = await self._enter_branch_from_management(page, tokens)
        if selected_page:
            return selected_page

        for token in tokens:
            for selector in self.recipe.store_trigger_selectors:
                try:
                    trigger = page.locator(selector).filter(
                        has_text=re.compile(self.recipe.store_trigger_text_regex, re.I)
                    ).first
                    if await trigger.is_visible(timeout=800):
                        await trigger.click()
                        await page.wait_for_timeout(500)
                        option = page.locator(f"text={token}").first
                        if await option.is_visible(timeout=1200):
                            await option.click()
                            await page.wait_for_timeout(1500)
                            logger.info("[%s] 已尝试切换门店: %s", self.recipe.name, token)
                            return page
                except Exception:
                    pass
        return None

    async def _enter_branch_from_management(self, page, tokens: list[str]):
        try:
            enter_links = None
            for label in self.recipe.enter_store_texts:
                candidate = page.locator(f"text={label}")
                if await candidate.count() > 0:
                    enter_links = candidate
                    break
            if enter_links is None or await enter_links.count() == 0:
                return False

            rows = page.locator(", ".join(self.recipe.row_selectors))
            row_count = await rows.count()
            for token in tokens:
                for index in range(row_count):
                    row = rows.nth(index)
                    try:
                        text = (await row.inner_text()).strip()
                        if token.lower() not in text.lower():
                            continue
                        link = await self._first_visible_text_locator(row, self.recipe.enter_store_texts)
                        if link:
                            page = await self._click_and_capture_page(page, link)
                            logger.info("[%s] 已进入分店: %s", self.recipe.name, token)
                            return page
                    except Exception:
                        pass

            first_link = enter_links.first
            if await first_link.is_visible(timeout=1000):
                page = await self._click_and_capture_page(page, first_link)
                logger.info("[%s] 已进入第一个可见分店", self.recipe.name)
                return page
        except Exception:
            return None
        return None

    async def _parse_dom(
        self,
        page,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        seen: set[str],
    ) -> list[Review]:
        items = None
        for selector in self.recipe.review_card_selectors:
            loc = page.locator(selector)
            if await loc.count() > 0:
                items = loc
                break
        if not items:
            return []

        results: list[Review] = []
        for index in range(await items.count()):
            item = items.nth(index)
            row_data = await self._parse_table_row(item)
            review_id = (
                await item.get_attribute("data-id")
                or await item.get_attribute("data-row-key")
                or row_data.get("order_id")
                or f"{self.recipe.name}_{index}"
            )
            if review_id in seen:
                continue

            content = row_data.get("content") or await self._extract_text(item, self.recipe.content_selectors)
            if not content:
                content = await self._extract_text(item, ("div", "span"))
            if not content:
                continue
            seen.add(review_id)

            date_text = row_data.get("date_text") or await self._extract_text(item, self.recipe.date_selectors) or ""
            child_rating = row_data.get("child_rating") or await self._extract_sub_ratings(item)
            image_urls = await self._extract_image_urls(item)

            results.append(
                self._make_review(
                    platform=self.recipe.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name=await self._extract_text(item, self.recipe.reviewer_selectors) or "匿名用户",
                    content=content,
                    rating=await self._extract_rating(item),
                    published_at=self._parse_time(date_text),
                    image_urls=image_urls,
                    merchant_reply=await self._extract_text(item, self.recipe.reply_selectors),
                    child_rating=child_rating,
                    review_type=review_type,
                    page_url=page.url,
                    raw_data=json.dumps(row_data, ensure_ascii=False) if row_data else None,
                    ocr_strategy=OcrStrategy.DOM_PARSE.value,
                )
            )
        return results

    async def _parse_table_row(self, item) -> dict[str, str]:
        try:
            cells = item.locator("td, [role='cell']")
            cell_count = await cells.count()
            if cell_count <= 0:
                return {}
            cell_texts = [
                self._normalize_cell_text(await cells.nth(index).inner_text())
                for index in range(cell_count)
            ]
            content_col, order_col, date_col, rating_col = self._resolve_table_columns(cell_texts)
            max_col = max(content_col, order_col, date_col)
            if cell_count <= max_col:
                return {}
        except Exception:
            return {}

        content_text = cell_texts[content_col]
        order_text = cell_texts[order_col]
        date_text = cell_texts[date_col]
        order_match = re.search(r"\d{10,}", order_text)
        date_match = re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", date_text)
        row_data = {
            "content": self._clean_review_content(content_text),
            "order_id": order_match.group(0) if order_match else order_text.strip(),
            "date_text": date_match.group(0) if date_match else date_text.strip(),
        }
        rating_text = cell_texts[rating_col] if 0 <= rating_col < cell_count else content_text
        child_rating = self._extract_child_rating_from_text(f"{rating_text}\n{content_text}")
        if not child_rating and 0 <= rating_col < cell_count:
            child_rating = await self._extract_child_rating_from_star_cell(cells.nth(rating_col))
        if child_rating:
            row_data["child_rating"] = child_rating
        return {key: value for key, value in row_data.items() if value}

    def _parse_api_response(
        self,
        data,
        shop_id: str,
        shop_name: str,
        review_type: ReviewType,
        api_url: str,
    ) -> list[Review]:
        reviews: list[Review] = []
        for item in self._extract_review_items(data):
            if not isinstance(item, dict):
                continue
            content = self._pick_first(item, *self.recipe.api_content_fields).strip()
            if not content:
                continue
            reviews.append(
                self._make_review(
                    platform=self.recipe.platform,
                    shop_id=shop_id,
                    shop_name=shop_name,
                    reviewer_name=self._resolve_reviewer(item),
                    content=content,
                    rating=self._coerce_rating(self._pick_first(item, *self.recipe.api_rating_fields)),
                    published_at=self._parse_time(self._pick_first(item, *self.recipe.api_date_fields)),
                    image_urls=self._resolve_image_urls(item),
                    merchant_reply=self._resolve_reply(item),
                    child_rating=self._resolve_sub_ratings(item),
                    review_type=review_type,
                    page_url=api_url,
                    raw_data=json.dumps(item, ensure_ascii=False),
                    ocr_strategy=OcrStrategy.API_INTERCEPT.value,
                )
            )
        return reviews

    def _extract_review_items(self, data) -> list:
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        nested = data.get("data")
        if isinstance(nested, list):
            return nested
        if isinstance(nested, dict):
            for key in self.recipe.list_keys:
                value = nested.get(key)
                if isinstance(value, list):
                    return value
        for key in self.recipe.list_keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
        for value in data.values():
            items = self._extract_review_items(value)
            if items:
                return items
        return []

    async def _go_next_page(self, page) -> bool:
        for selector in self.recipe.next_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1000) and await btn.is_enabled():
                    await btn.click()
                    await page.wait_for_timeout(1800)
                    return True
            except Exception:
                pass
        return await self._scroll_load_more(page)

    async def _save_cookies(self, shop_id: str) -> None:
        cookies_file = self._cookies_file(shop_id)
        cookies_file.parent.mkdir(parents=True, exist_ok=True)
        cookies_file.write_text(
            json.dumps(await self._context.cookies(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        storage_file = self._storage_state_file(shop_id)
        await self._context.storage_state(path=str(storage_file))

    async def _extract_text(self, item, selectors: tuple[str, ...]) -> Optional[str]:
        for selector in selectors:
            try:
                loc = item.locator(selector).first
                if await loc.is_visible(timeout=600):
                    text = re.sub(r"\s+", " ", (await loc.inner_text()).strip())
                    if len(text) >= 2:
                        return text
            except Exception:
                pass
        return None

    async def _extract_rating(self, item) -> float:
        for selector in (
            "[aria-label*='star']",
            "[aria-label*='Star']",
            "[class*='star-rating']",
            "[class*='rating']",
            "[class*='score']",
        ):
            try:
                loc = item.locator(selector).first
                if await loc.count() == 0:
                    continue
                label = (
                    await loc.get_attribute("aria-label")
                    or await loc.get_attribute("title")
                    or await loc.inner_text()
                    or ""
                )
                rating = self._coerce_rating(label)
                if rating > 0:
                    return rating
            except Exception:
                pass
        return 5.0

    async def _extract_sub_ratings(self, item) -> Optional[str]:
        try:
            raw_text = (await item.inner_text()).strip()
        except Exception:
            raw_text = ""
        return self._extract_child_rating_from_text(raw_text)

    async def _extract_image_urls(self, item) -> tuple[str, ...]:
        urls: list[str] = []
        try:
            imgs = item.locator(", ".join(self.recipe.image_selectors))
            for index in range(await imgs.count()):
                url = await imgs.nth(index).get_attribute("src") or ""
                if url and "avatar" not in url:
                    urls.append(url)
        except Exception:
            pass
        return tuple(urls)

    def _clean_review_content(self, raw_text: str) -> str:
        lines = [line.strip() for line in re.split(r"[\r\n]+", raw_text or "") if line.strip()]
        labels = "|".join(re.escape(label) for label in self.recipe.sub_rating_labels)
        label_pattern = re.compile(rf"^({labels})\s*[:：]?\s*[\d.\s★☆⭐]*$", re.I) if labels else None
        cleaned = [
            line for line in lines
            if not (label_pattern and label_pattern.match(line))
        ]
        return "\n".join(cleaned).strip()

    def _resolve_table_columns(self, cell_texts: list[str]) -> tuple[int, int, int, int]:
        content_col = self.recipe.table_content_col
        order_col = self.recipe.table_order_col
        date_col = self.recipe.table_date_col
        rating_col = content_col

        if len(cell_texts) >= 5 and self._looks_like_rating_cell(cell_texts[0]):
            return 1, 2, 3, 0
        return content_col, order_col, date_col, rating_col

    def _looks_like_rating_cell(self, text: str) -> bool:
        lowered = re.sub(r"\s+", " ", text or "").lower()
        return any(re.sub(r"\s+", " ", label).lower() in lowered for label in self.recipe.sub_rating_labels)

    @staticmethod
    def _normalize_cell_text(text: str) -> str:
        text = re.sub(r"[\r\n]+", "\n", text or "")
        text = re.sub(r"[ \t\f\v]+", " ", text)
        return text.strip()

    def _extract_child_rating_from_text(self, raw_text: str) -> Optional[str]:
        collected: dict[str, float] = {}
        for source_label, normalized in self.recipe.sub_rating_labels.items():
            escaped_label = r"\s+".join(re.escape(part) for part in re.split(r"\s+", source_label.strip()))
            pattern = re.compile(rf"{escaped_label}\s*[:：]?\s*(\d+(?:\.\d+)?)", re.I)
            match = pattern.search(raw_text or "")
            if match:
                collected[normalized] = float(match.group(1))
        return json.dumps(collected, ensure_ascii=False) if collected else None

    async def _extract_child_rating_from_star_cell(self, cell) -> Optional[str]:
        if not self.recipe.sub_rating_labels:
            return None
        try:
            result = await cell.evaluate(
                """
                (cell, labelMap) => {
                    const normalize = (value) => String(value || '')
                        .replace(/\\s+/g, ' ')
                        .trim()
                        .toLowerCase();
                    const selector = [
                        '.ant-rate-star-full',
                        '[class*="star-full"]',
                        '[class*="starFull"]',
                        '[class*="rate-star-full"]',
                        '[class*="RateStarFull"]'
                    ].join(',');
                    const halfSelector = [
                        '.ant-rate-star-half',
                        '[class*="star-half"]',
                        '[class*="starHalf"]',
                        '[class*="rate-star-half"]',
                        '[class*="RateStarHalf"]'
                    ].join(',');
                    const countStars = (root) => {
                        const full = root.querySelectorAll(selector).length;
                        const half = root.querySelectorAll(halfSelector).length;
                        if (full || half) return full + half * 0.5;
                        const glyphs = (root.textContent || '').match(/[★⭐]/g);
                        if (glyphs && glyphs.length) return glyphs.length;
                        const attrs = Array.from(root.querySelectorAll('[aria-label], [title]'))
                            .map((node) => `${node.getAttribute('aria-label') || ''} ${node.getAttribute('title') || ''}`)
                            .join(' ');
                        const match = attrs.match(/(\\d+(?:\\.\\d+)?)/);
                        return match ? Number(match[1]) : 0;
                    };

                    const nodes = [cell, ...Array.from(cell.querySelectorAll('*'))];
                    const output = {};
                    for (const [sourceLabel, normalizedLabel] of labelMap) {
                        const label = normalize(sourceLabel);
                        let best = null;
                        for (const node of nodes) {
                            const nodeText = normalize(node.innerText || node.textContent);
                            if (!nodeText.includes(label)) continue;
                            if (!best || nodeText.length < normalize(best.innerText || best.textContent).length) {
                                best = node;
                            }
                        }
                        if (!best) continue;
                        let root = best;
                        for (let depth = 0; root && depth < 4; depth += 1, root = root.parentElement) {
                            const stars = countStars(root);
                            if (stars) {
                                output[normalizedLabel] = Math.max(0, Math.min(5, stars));
                                break;
                            }
                        }
                    }
                    return output;
                }
                """,
                list(self.recipe.sub_rating_labels.items()),
            )
            if isinstance(result, dict) and result:
                return json.dumps(result, ensure_ascii=False)
        except Exception:
            return None
        return None

    def _cookies_file(self, shop_id: str) -> Path:
        host = urlparse(self._base_url(shop_id)).netloc.replace(":", "_") or "default"
        return Path(__file__).parent.parent / "data" / self.recipe.cookie_dir_name / f"{host}.json"

    def _storage_state_file(self, shop_id: str) -> Path:
        host = urlparse(self._base_url(shop_id)).netloc.replace(":", "_") or "default"
        return Path(__file__).parent.parent / "data" / self.recipe.cookie_dir_name / f"{host}.storage.json"

    def _persistent_profile_dir(self) -> Optional[Path]:
        if not self.recipe.persistent_profile_dir_name:
            return None
        return Path(__file__).parent.parent / "data" / "browser_profiles" / self.recipe.persistent_profile_dir_name

    def _initial_storage_state_file(self) -> Optional[Path]:
        if not self._login_url:
            return None
        parsed = urlparse(self._login_url)
        if not parsed.netloc:
            return None
        host = parsed.netloc.replace(":", "_")
        return Path(__file__).parent.parent / "data" / self.recipe.cookie_dir_name / f"{host}.storage.json"

    def _login_page(self, shop_id: str) -> str:
        return self._normalize_login_url(self._login_url or self._base_url(shop_id) + self.recipe.login_path)

    def _review_url(self, shop_id: str) -> str:
        return f"{self._base_url(shop_id)}{self.recipe.review_path}"

    def _entry_url(self, shop_id: str) -> str:
        if self.recipe.management_path:
            return f"{self._base_url(shop_id)}{self.recipe.management_path}"
        return self._review_url(shop_id)

    def _login_check_url(self, shop_id: str) -> str:
        if self.recipe.login_check_path:
            return f"{self._base_url(shop_id)}{self.recipe.login_check_path}"
        return self._entry_url(shop_id)

    def _base_url(self, shop_id: str) -> str:
        for candidate in (self._login_url, shop_id):
            candidate = (candidate or "").strip()
            if not candidate.startswith("http"):
                continue
            parsed = urlparse(candidate)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        raise ValueError(f"{self.recipe.name} 缺少可用的登录 URL，请在 Excel 中补充对应门店后台链接")

    def _resolve_login_credentials(self, shop_id: str) -> tuple[str, str]:
        username = self._login_username
        password = self._login_password
        for prefix in self._credential_env_prefixes(shop_id):
            if not username:
                username = (
                    os.getenv(f"{prefix}_USERNAME", "").strip()
                    or os.getenv(f"{prefix}_ACCOUNT", "").strip()
                    or os.getenv(f"{prefix}_PHONE", "").strip()
                )
            if not password:
                password = os.getenv(f"{prefix}_PASSWORD", "")
            if username and password:
                break
        return username, password

    def _credential_env_prefixes(self, shop_id: str) -> list[str]:
        prefixes: list[str] = []
        try:
            host = urlparse(self._base_url(shop_id)).netloc.lower()
        except Exception:
            host = ""
        for host_token, prefix in self.recipe.credential_host_env_prefixes.items():
            host_token = host_token.lower()
            if host_token and host_token in host:
                prefixes.append(prefix)
        if self.recipe.credential_env_prefix:
            prefixes.append(self.recipe.credential_env_prefix)
        prefixes.append("MERCHANT")

        normalized: list[str] = []
        seen: set[str] = set()
        for prefix in prefixes:
            env_prefix = re.sub(r"[^A-Za-z0-9_]", "_", prefix or "").upper().strip("_")
            if env_prefix and env_prefix not in seen:
                seen.add(env_prefix)
                normalized.append(env_prefix)
        return normalized

    def _normalize_login_url(self, login_url: str) -> str:
        login_url = (login_url or "").strip()
        if not login_url:
            return ""
        if self.recipe.login_path in login_url:
            return login_url
        parsed = urlparse(login_url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}{self.recipe.login_path}"
        return login_url

    def _store_tokens(self, shop_name: str) -> list[str]:
        candidates = [self._shop_hint, shop_name, self._shop_name]
        tokens: list[str] = []
        for candidate in candidates:
            value = (candidate or "").strip()
            if not value:
                continue
            tokens.append(value)
            tokens.extend(re.findall(r"[（(]([^）)]+)[）)]", value))
        normalized: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            token = token.strip()
            if len(token) >= 2 and token not in seen:
                seen.add(token)
                normalized.append(token)
        return normalized

    def _logged_in_wait_js(self) -> str:
        logged_in_pattern = "|".join(re.escape(text) for text in self.recipe.logged_in_texts)
        review_pattern = "|".join(re.escape(text) for text in self.recipe.review_state_texts)
        url_fragments = list(self.recipe.logged_in_url_fragments) + [self.recipe.review_path]
        return f"""
            () => {{
                const href = window.location.href.toLowerCase();
                const text = document.body && document.body.innerText ? document.body.innerText : '';
                if ({json.dumps(url_fragments)}.some(fragment => href.includes(fragment.toLowerCase()))) return true;
                if (href.includes('/login')) return false;
                return new RegExp({json.dumps(logged_in_pattern)}, 'i').test(text) ||
                    new RegExp({json.dumps(review_pattern)}, 'i').test(text);
            }}
        """

    @staticmethod
    async def _click_first_visible_text(page, labels: tuple[str, ...], timeout: int = 1000, wait_ms: int = 1200) -> bool:
        for label in labels:
            try:
                loc = page.locator(f"text={label}").first
                if await loc.is_visible(timeout=timeout):
                    await loc.click()
                    await page.wait_for_timeout(wait_ms)
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    async def _click_and_capture_page(page, locator, wait_ms: int = 2500):
        try:
            async with page.context.expect_page(timeout=2000) as page_info:
                await locator.click()
            new_page = await page_info.value
            try:
                await new_page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            await new_page.wait_for_timeout(wait_ms)
            return new_page
        except Exception:
            await locator.click()
            await page.wait_for_timeout(wait_ms)
            return page

    async def _try_auto_login(self, page, shop_id: str, username: str, password: str) -> bool:
        try:
            username_input = await self._first_visible_selector(page, self.recipe.login_username_selectors)
            password_input = await self._first_visible_selector(page, self.recipe.login_password_selectors)
            if not username_input or not password_input:
                logger.info("[%s] 未找到可自动填写的登录输入框，等待人工登录", self.recipe.name)
                return False

            await username_input.fill(username)
            await password_input.fill(password)

            clicked = False
            for selector in self.recipe.login_submit_selectors:
                try:
                    submit = page.locator(selector).first
                    if await submit.is_visible(timeout=800) and await submit.is_enabled():
                        await submit.click()
                        clicked = True
                        break
                except Exception:
                    pass
            if not clicked:
                await password_input.press("Enter")

            try:
                await page.wait_for_function(self._logged_in_wait_js(), timeout=30_000)
            except Exception:
                pass
            await page.wait_for_timeout(1500)
            return await self._is_logged_in(page)
        except Exception as exc:
            logger.warning("[%s] 自动登录失败: %s", self.recipe.name, exc)
            return False

    @staticmethod
    async def _first_visible_selector(scope, selectors: tuple[str, ...], timeout: int = 800):
        for selector in selectors:
            try:
                loc = scope.locator(selector).first
                if await loc.count() > 0 and await loc.is_visible(timeout=timeout):
                    return loc
            except Exception:
                pass
        return None

    @staticmethod
    async def _first_visible_text_locator(scope, labels: tuple[str, ...], timeout: int = 800):
        for label in labels:
            try:
                loc = scope.locator(f"text={label}").first
                if await loc.count() > 0 and await loc.is_visible(timeout=timeout):
                    return loc
            except Exception:
                pass
        return None

    @staticmethod
    def _pick_first(item: dict, *keys: str) -> str:
        for key in keys:
            value = item.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                if value.strip():
                    return value
                continue
            if isinstance(value, (int, float)):
                return str(value)
        return ""

    def _resolve_reviewer(self, item: dict) -> str:
        for key in self.recipe.api_reviewer_objects:
            value = item.get(key)
            if isinstance(value, dict):
                name = self._pick_first(value, "nickname", "name", "userName", "username")
                if name:
                    return name
            if isinstance(value, str) and value.strip():
                return value.strip()
        return self._pick_first(item, *self.recipe.api_reviewer_fields) or "匿名用户"

    @staticmethod
    def _coerce_rating(raw) -> float:
        if raw is None:
            return 5.0
        if isinstance(raw, (int, float)):
            value = float(raw)
        else:
            match = re.search(r"(\d+(?:\.\d+)?)", str(raw))
            value = float(match.group(1)) if match else 5.0
        if value > 10:
            value = value / 10
        elif value > 5:
            value = value / 2
        return max(0.0, min(5.0, value)) or 5.0

    def _resolve_image_urls(self, item: dict) -> tuple[str, ...]:
        urls: list[str] = []
        for field_name in self.recipe.api_image_fields:
            pics = item.get(field_name)
            if not isinstance(pics, list):
                continue
            for picture in pics:
                if isinstance(picture, dict):
                    for key in ("url", "src", "imageUrl", "imgUrl"):
                        if picture.get(key):
                            urls.append(str(picture[key]))
                            break
                elif picture:
                    urls.append(str(picture))
        return tuple(url for url in urls if url)

    def _resolve_reply(self, item: dict) -> Optional[str]:
        for field_name in self.recipe.api_reply_fields:
            reply = item.get(field_name)
            if isinstance(reply, dict):
                value = self._pick_first(reply, "content", "replyContent", "text")
                if value:
                    return value
            if isinstance(reply, str) and reply.strip():
                return reply.strip()
        return None

    def _resolve_sub_ratings(self, item: dict) -> Optional[str]:
        collected: dict[str, float] = {}
        for key, label in self.recipe.api_sub_rating_fields:
            if item.get(key) is not None:
                collected[label] = self._coerce_rating(item.get(key))
        for key in ("subScore", "subScores", "detailScore"):
            sub = item.get(key)
            if isinstance(sub, dict):
                for sub_key, value in sub.items():
                    label = self.recipe.sub_rating_labels.get(str(sub_key), str(sub_key))
                    collected[label] = self._coerce_rating(value)
        return json.dumps(collected, ensure_ascii=False) if collected else None

    @staticmethod
    def _parse_time(value: str) -> Optional[datetime]:
        value = (value or "").strip()
        if not value:
            return None
        if value.isdigit():
            try:
                timestamp = int(value)
                if timestamp > 10_000_000_000:
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp)
            except Exception:
                pass
        for fmt, sample_len in (
            ("%Y-%m-%d %H:%M:%S", 19),
            ("%Y-%m-%d", 10),
            ("%Y/%m/%d %H:%M:%S", 19),
            ("%Y/%m/%d", 10),
            ("%d/%m/%Y", 10),
        ):
            try:
                return datetime.strptime(value[:sample_len], fmt)
            except ValueError:
                pass
        now = datetime.now()
        patterns = [
            (r"(\d+)\s*minutes?\s*ago", timedelta(minutes=1)),
            (r"(\d+)\s*hours?\s*ago", timedelta(hours=1)),
            (r"(\d+)\s*days?\s*ago", timedelta(days=1)),
            (r"(\d+)\s*weeks?\s*ago", timedelta(weeks=1)),
            (r"(\d+)\s*months?\s*ago", timedelta(days=30)),
            (r"(\d+)\s*years?\s*ago", timedelta(days=365)),
            (r"(\d+)\s*分钟前", timedelta(minutes=1)),
            (r"(\d+)\s*小时前", timedelta(hours=1)),
            (r"(\d+)\s*天前", timedelta(days=1)),
            (r"(\d+)\s*周前", timedelta(weeks=1)),
            (r"(\d+)\s*个月前", timedelta(days=30)),
            (r"(\d+)\s*年前", timedelta(days=365)),
        ]
        lowered = value.lower()
        for pattern, delta in patterns:
            match = re.search(pattern, lowered)
            if match:
                return now - int(match.group(1)) * delta
        return None
