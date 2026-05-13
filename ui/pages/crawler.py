"""
爬取管理页面 — 深色主题
"""
from __future__ import annotations
import asyncio
from nicegui import ui
from core.database import insert_task, update_task_status, get_tasks
from core.models import Platform, ReviewType, CrawlTask, OcrStrategy
from crawlers import get_crawler
from processors import process_and_save
import config

CARD  = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"
CARD2 = "background:#0e0e0e; border:1px solid #1a1a1a; border-radius:8px; padding:12px 16px"
BTN_P = "background:#fff; color:#000; border:none; border-radius:7px; padding:9px 24px; font-size:13px; font-weight:600; cursor:pointer"
BTN_G = "background:transparent; color:#888; border:1px solid #333; border-radius:7px; padding:8px 14px; font-size:13px; cursor:pointer"
LABEL = "font-size:11px; color:#555; font-weight:500; letter-spacing:0.5px"

STATUS_STYLE = {
    "running": "color:#f59e0b; background:#1c1400; border:1px solid #422f00; border-radius:4px; padding:1px 8px; font-size:11px",
    "done":    "color:#4ade80; background:#0d1f0d; border:1px solid #14532d; border-radius:4px; padding:1px 8px; font-size:11px",
    "failed":  "color:#f87171; background:#1f0d0d; border:1px solid #7f1d1d; border-radius:4px; padding:1px 8px; font-size:11px",
    "pending": "color:#888;    background:#1a1a1a;  border:1px solid #333;   border-radius:4px; padding:1px 8px; font-size:11px",
}


def render() -> None:
    with ui.column().classes("w-full gap-4"):
        # ── 标题 ─────────────────────────────────────────────────
        with ui.row().classes("items-center justify-between w-full").style("margin-bottom:8px"):
            with ui.column().classes("gap-0"):
                ui.label("爬取管理").style("font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px")
                ui.label("Crawl Manager").style("font-size:12px; color:#444")

        # ── 采集字段说明 ──────────────────────────────────────────
        with ui.element("div").style(CARD2 + "; border-left:3px solid #fff; margin-bottom:4px"):
            with ui.row().classes("items-center gap-2 flex-wrap"):
                ui.icon("check_circle").style("font-size:14px; color:#4ade80")
                ui.label(
                    "采集字段：店铺名称 · 平台 · 用户名 · 评分 · 评论内容 · 翻译 · "
                    "发布日期 · 采集时间 · 图片 · 商家回复 · 子评分 · 页面URL"
                ).style("font-size:12px; color:#555")

        # ── 新建爬取任务 ──────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("新建爬取任务").style("font-size:14px; font-weight:600; color:#fff; margin-bottom:16px")

            with ui.grid(columns=2).classes("w-full gap-4"):
                platform_select = ui.select(
                    options={p.value: p.value for p in Platform},
                    label="目标平台",
                    value=Platform.MEITUAN.value,
                ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

                shop_id_input = ui.input(
                    label="商家ID / URL",
                    placeholder="输入平台商家ID 或 完整 URL",
                ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

                shop_name_input = ui.input(
                    label="店铺名称",
                    placeholder="用于标识和导出",
                ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

                max_pages_input = ui.number(
                    label="最大爬取页数",
                    value=config.get("max_pages", 10),
                    min=1, max=200,
                ).classes("w-full").props("dark dense outlined color=white label-color=grey-6")

            with ui.row().classes("gap-4 flex-wrap").style("margin-top:12px"):
                review_type_toggle = ui.toggle(
                    {ReviewType.REVIEW.value: "📝 用户评论",
                     ReviewType.COMPLAINT.value: "⚠️ 客诉"},
                    value=ReviewType.REVIEW.value,
                ).props("flat dense")

                strategy_select = ui.select(
                    options={
                        "hybrid":         "🔀 Hybrid 自动降级",
                        "api_intercept":  "⚡ API 拦截",
                        "dom_parse":      "🌐 DOM 解析",
                        "ocr_screenshot": "📷 OCR 截图",
                    },
                    label="爬取策略",
                    value=config.get("ocr_strategy", "hybrid"),
                ).style("min-width:180px").props("dark dense outlined color=white label-color=grey-6")

                headless_check = ui.checkbox(
                    "无头模式", value=config.get("headless", True)
                ).props("dark color=white")

            # 进度
            progress_label = ui.label("").style("font-size:12px; color:#555; margin-top:10px")
            progress_bar = ui.linear_progress(value=0).classes("w-full").style("margin-top:4px")
            progress_bar.visible = False

            async def start_crawl():
                shop_id   = shop_id_input.value.strip()
                shop_name = shop_name_input.value.strip()
                max_pages = int(max_pages_input.value or 10)

                if not shop_id or not shop_name:
                    ui.notify("请填写商家ID和店铺名称", type="warning")
                    return

                platform  = Platform(platform_select.value)
                rev_type  = ReviewType(review_type_toggle.value)
                strategy  = strategy_select.value

                task = CrawlTask(
                    id=None, platform=platform, shop_id=shop_id,
                    shop_name=shop_name, status="running",
                    started_at=None, finished_at=None,
                    ocr_strategy=strategy,
                )
                task_id = insert_task(task)
                progress_bar.visible = True
                progress_bar.value = 0
                progress_label.set_text("⏳ 正在启动浏览器...")

                def on_crawl_progress(fetched: int, _total: int):
                    progress_label.set_text(f"📥 已爬取 {fetched} 条评论...")

                def on_process_progress(current: int, total: int):
                    if total > 0:
                        progress_bar.value = current / total
                    progress_label.set_text(f"🤖 AI 处理中... {current}/{total}")

                try:
                    cr = get_crawler(
                        platform,
                        headless=headless_check.value,
                        proxy=config.get("proxy") or None,
                        strategy=strategy,
                    )
                    reviews = await cr.crawl(
                        shop_id=shop_id,
                        shop_name=shop_name,
                        max_pages=max_pages,
                        review_type=rev_type,
                        progress_callback=on_crawl_progress,
                    )
                    progress_label.set_text(
                        f"✅ 爬取完成 {len(reviews)} 条，开始 AI 分析..."
                    )

                    if reviews and config.get("auto_analyze", True):
                        await process_and_save(reviews, progress_callback=on_process_progress)

                    update_task_status(task_id, "done", len(reviews))
                    ui.notify(f"✅ 完成！共处理 {len(reviews)} 条评论", type="positive")
                    refresh_tasks()

                except Exception as exc:
                    update_task_status(task_id, "failed", error_msg=str(exc))
                    ui.notify(f"❌ 失败: {exc}", type="negative")
                finally:
                    progress_bar.visible = False
                    progress_label.set_text("")

            ui.button("▶ 开始爬取", on_click=start_crawl).style(BTN_P + "; margin-top:16px")

        # ── 任务历史 ──────────────────────────────────────────────
        with ui.element("div").style(CARD):
            with ui.row().classes("items-center justify-between").style("margin-bottom:14px"):
                ui.label("任务历史").style("font-size:14px; font-weight:600; color:#fff")
                ui.button("刷新", on_click=lambda: refresh_tasks()).style(BTN_G)

            task_col = ui.column().classes("w-full gap-2")

            def refresh_tasks():
                task_col.clear()
                tasks = get_tasks(50)
                with task_col:
                    if not tasks:
                        ui.label("暂无任务记录").style("font-size:13px; color:#333; text-align:center; padding:24px 0")
                        return
                    for t in tasks:
                        _render_task_row(t)

            refresh_tasks()


def _render_task_row(t: dict) -> None:
    status = t.get("status", "pending")
    with ui.element("div").style(
        "background:#111; border:1px solid #1e1e1e; border-radius:8px; padding:12px 16px"
    ):
        with ui.row().classes("w-full items-center gap-4 flex-wrap"):
            ui.label(f"#{t.get('id', '?')}").style("font-size:12px; color:#333; min-width:28px")
            ui.label(t.get("platform", "")).style("font-size:12px; color:#666; min-width:80px")
            ui.label(t.get("shop_name", "")).style("font-size:13px; color:#bbb; flex:1; font-weight:500")
            ui.label(t.get("ocr_strategy", "")).style("font-size:11px; color:#444; min-width:80px")
            ui.label(status).style(STATUS_STYLE.get(status, STATUS_STYLE["pending"]))
            ui.label(str(t.get("total_fetched", 0)) + " 条").style("font-size:12px; color:#555; min-width:44px")
            if t.get("started_at"):
                ui.label(str(t["started_at"])[:16]).style("font-size:11px; color:#333")
            if t.get("error_msg"):
                ui.label(str(t["error_msg"])[:60]).style("font-size:11px; color:#f87171")
