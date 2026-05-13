"""
导航块：负责浏览器导航、搜索店铺、点击 Tab、筛选排序
"""
from __future__ import annotations
import logging
import re
from typing import Optional

from .base_block import BaseBlock, BlockResult

logger = logging.getLogger(__name__)


class OpenPageBlock(BaseBlock):
    """积木块：打开指定 URL"""
    name = "OpenPage"

    def __init__(self, url: str, wait_for: str = "networkidle"):
        self.url = url
        self.wait_for = wait_for

    async def execute(self, ctx: dict) -> BlockResult:
        page = ctx.get("page")
        if not page:
            return BlockResult.fail("ctx 中缺少 page 对象")
        await page.goto(self.url, timeout=30000)
        await page.wait_for_load_state(self.wait_for, timeout=15000)
        ctx["current_url"] = page.url
        return BlockResult.success(page.url, f"已打开 {self.url}")


class ShopSearchBlock(BaseBlock):
    """
    积木块：在平台搜索框中搜索店铺名称。
    搜索不到时返回 SKIPPED，不阻断整个流程。
    使用 VLM 辅助识别搜索结果，匹配最相似店铺。
    """
    name = "ShopSearch"
    timeout_s = 45.0

    def __init__(
        self,
        shop_name: str,
        search_selectors: Optional[list[str]] = None,
        similarity_threshold: float = 0.6,
    ):
        self.shop_name = shop_name
        self.search_selectors = search_selectors or [
            "input[placeholder*='搜']",
            "input[placeholder*='Search']",
            "input[type='search']",
            ".search-input input",
            "[class*='search'] input",
        ]
        self.similarity_threshold = similarity_threshold

    async def execute(self, ctx: dict) -> BlockResult:
        page = ctx.get("page")
        if not page:
            return BlockResult.fail("ctx 中缺少 page 对象")

        # ── 找到搜索框 ─────────────────────────────────────────
        search_input = None
        for sel in self.search_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    search_input = el
                    break
            except Exception:
                pass

        if not search_input:
            logger.warning("[ShopSearch] 未找到搜索框，尝试 VLM 定位")
            search_input = await self._vlm_find_search_box(page)

        if not search_input:
            return BlockResult.skip(f"页面无搜索框，跳过店铺: {self.shop_name}")

        # ── 输入店铺名搜索 ──────────────────────────────────────
        await search_input.clear()
        await search_input.type(self.shop_name, delay=80)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2000)

        # ── 从结果中匹配最相似店铺 ──────────────────────────────
        matched = await self._find_best_match(page)
        if not matched:
            logger.info("[ShopSearch] '%s' 搜索无结果，跳过", self.shop_name)
            return BlockResult.skip(f"平台搜索不到: {self.shop_name}")

        await matched.click()
        await page.wait_for_load_state("networkidle", timeout=15000)
        ctx["shop_page_url"] = page.url
        ctx["matched_shop_name"] = self.shop_name
        return BlockResult.success(page.url, f"已进入店铺页: {self.shop_name}")

    async def _find_best_match(self, page) -> Optional[object]:
        """从搜索结果中找最相似店铺"""
        result_selectors = [
            "[class*='result-item']",
            "[class*='search-result'] li",
            "[class*='poi-item']",
            "ul[class*='list'] li",
        ]
        for sel in result_selectors:
            try:
                items = page.locator(sel)
                n = await items.count()
                if n == 0:
                    continue
                # 找文字匹配度最高的
                best_item = None
                best_score = 0.0
                for i in range(min(n, 10)):
                    item = items.nth(i)
                    text = (await item.inner_text()).strip()
                    score = self._similarity(text, self.shop_name)
                    if score > best_score:
                        best_score = score
                        best_item = item
                if best_item and best_score >= self.similarity_threshold:
                    logger.info("[ShopSearch] 匹配结果相似度=%.2f", best_score)
                    return best_item
            except Exception:
                pass
        return None

    async def _vlm_find_search_box(self, page) -> Optional[object]:
        """VLM 截图识别搜索框位置"""
        try:
            import base64
            from processors.ai_client import vision_chat
            screenshot = await page.screenshot(type="png")
            b64 = base64.standard_b64encode(screenshot).decode()
            prompt = """图中是否有搜索框？如有，请返回 JSON：
{"found": true, "selector": "CSS选择器或描述", "x": 像素x, "y": 像素y}
如无：{"found": false}"""
            raw = await vision_chat(b64, prompt, max_tokens=200)
            import json, re as _re
            m = _re.search(r'\{[^}]+\}', raw)
            if m:
                data = json.loads(m.group())
                if data.get("found") and data.get("x"):
                    await page.mouse.click(data["x"], data["y"])
                    return page.locator(":focus")
        except Exception as e:
            logger.warning("[ShopSearch] VLM 定位搜索框失败: %s", e)
        return None

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """简单字符重叠相似度"""
        a_set = set(a.lower())
        b_set = set(b.lower())
        if not a_set or not b_set:
            return 0.0
        return len(a_set & b_set) / len(a_set | b_set)


class ClickTabBlock(BaseBlock):
    """
    积木块：点击指定文字的 Tab（食评/评论/评价/Reviews）
    支持多语言：中文、繁体、英文
    """
    name = "ClickTab"

    def __init__(self, tab_keywords: Optional[list[str]] = None):
        self.tab_keywords = tab_keywords or [
            "食評", "食评", "评论", "評論", "评价", "評價",
            "Reviews", "Comments", "Ratings",
        ]

    async def execute(self, ctx: dict) -> BlockResult:
        page = ctx.get("page")
        if not page:
            return BlockResult.fail("ctx 中缺少 page 对象")

        for kw in self.tab_keywords:
            try:
                el = page.locator(f"text={kw}").first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    await page.wait_for_timeout(1500)
                    logger.info("[ClickTab] 已点击 Tab: %s", kw)
                    ctx["review_tab_clicked"] = kw
                    return BlockResult.success(kw, f"已点击评论Tab: {kw}")
            except Exception:
                pass

        # VLM 兜底
        return await self._vlm_click_tab(page, ctx)

    async def _vlm_click_tab(self, page, ctx) -> BlockResult:
        try:
            import base64
            from processors.ai_client import vision_chat
            screenshot = await page.screenshot(type="png")
            b64 = base64.standard_b64encode(screenshot).decode()
            kws = "、".join(self.tab_keywords[:5])
            prompt = f"""请找到页面中类似「{kws}」的导航标签，返回JSON：
{{"found": true, "text": "标签文字", "x": x坐标, "y": y坐标}}
若无：{{"found": false}}"""
            raw = await vision_chat(b64, prompt, max_tokens=200)
            import json, re as _re
            m = _re.search(r'\{[^}]+\}', raw)
            if m:
                data = json.loads(m.group())
                if data.get("found") and data.get("x"):
                    await page.mouse.click(data["x"], data["y"])
                    await page.wait_for_timeout(1500)
                    ctx["review_tab_clicked"] = data.get("text", "VLM")
                    return BlockResult.success(data.get("text"), "VLM点击评论Tab成功")
        except Exception as e:
            logger.warning("[ClickTab] VLM 失败: %s", e)
        return BlockResult.skip("未找到评论Tab，跳过")


class FilterNewestBlock(BaseBlock):
    """
    积木块：筛选最新评论（按时间降序）
    自动识别「筛选」「排序」按钮，选择最新
    """
    name = "FilterNewest"

    async def execute(self, ctx: dict) -> BlockResult:
        page = ctx.get("page")
        if not page:
            return BlockResult.fail("ctx 中缺少 page 对象")

        # 先点击筛选/排序入口
        filter_entry_kws = ["篩選食評", "筛选", "篩選", "排序", "Filter", "Sort"]
        for kw in filter_entry_kws:
            try:
                el = page.locator(f"text={kw}").first
                if await el.is_visible(timeout=1500):
                    await el.click()
                    await page.wait_for_timeout(800)
                    break
            except Exception:
                pass

        # 再选"最新"选项
        newest_kws = ["最新", "最新優先", "Newest", "Most Recent", "最近"]
        for kw in newest_kws:
            try:
                el = page.locator(f"text={kw}").first
                if await el.is_visible(timeout=1500):
                    await el.click()
                    await page.wait_for_timeout(1000)
                    logger.info("[FilterNewest] 已选择最新排序: %s", kw)
                    ctx["sort_by"] = "newest"
                    return BlockResult.success("newest", f"已选择: {kw}")
            except Exception:
                pass

        return BlockResult.skip("未找到最新排序选项，使用默认排序")


class ExpandMoreBlock(BaseBlock):
    """
    积木块：展开"更多"按钮，确保评论内容完整加载。
    四级策略：直接点击 → JS解除disabled → 调用loadMore函数 → VLM定位点击
    """
    name = "ExpandMore"

    async def execute(self, ctx: dict) -> BlockResult:
        page = ctx.get("page")
        if not page:
            return BlockResult.fail("ctx 中缺少 page 对象")

        total_expanded = 0
        max_attempts = 20  # 最多展开20次，防止无限循环

        for _ in range(max_attempts):
            expanded = await self._try_expand_once(page)
            if expanded == 0:
                break
            total_expanded += expanded
            await page.wait_for_timeout(1000)

        if total_expanded > 0:
            return BlockResult.success(total_expanded, f"共展开 {total_expanded} 次")
        return BlockResult.skip("无需展开或已全部展示")

    async def _try_expand_once(self, page) -> int:
        """尝试一次展开，返回成功次数"""
        # 策略1: 直接点击展开按钮
        expand_kws = ["展开更多", "更多评论", "查看更多", "Load More",
                      "Show More", "更多", "展开", "全部"]
        for kw in expand_kws:
            try:
                el = page.locator(f"button:has-text('{kw}'), a:has-text('{kw}')").first
                if await el.is_visible(timeout=1000) and await el.is_enabled():
                    await el.click()
                    return 1
            except Exception:
                pass

        # 策略2: JS 解除 disabled 属性后点击
        try:
            result = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll(
                        'button[disabled], button.disabled, [class*="load-more"]'
                    );
                    let clicked = 0;
                    btns.forEach(btn => {
                        const text = btn.textContent || '';
                        if (/更多|more|load|expand/i.test(text)) {
                            btn.removeAttribute('disabled');
                            btn.classList.remove('disabled');
                            btn.click();
                            clicked++;
                        }
                    });
                    return clicked;
                }
            """)
            if result > 0:
                return result
        except Exception:
            pass

        # 策略3: 调用页面内部 loadMore/fetchMore 函数
        try:
            result = await page.evaluate("""
                () => {
                    const fns = ['loadMore', 'fetchMore', 'loadNextPage', 'showMore'];
                    for (const fn of fns) {
                        if (typeof window[fn] === 'function') {
                            window[fn]();
                            return 1;
                        }
                    }
                    return 0;
                }
            """)
            if result > 0:
                return result
        except Exception:
            pass

        return 0
