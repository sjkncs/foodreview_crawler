"""
评论列表页面 — 深色主题
"""
from __future__ import annotations
from nicegui import ui
from core.database import get_reviews, count_reviews
from core.models import Platform, ReviewType, SentimentLabel, Review

_PAGE_SIZE = 20

CARD  = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"
CARD2 = "background:#0e0e0e; border:1px solid #1a1a1a; border-radius:8px; padding:14px 16px"

SENT_STYLE = {
    "正面": "background:#1a2e1a; color:#4ade80; border:1px solid #166534; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600",
    "负面": "background:#2e1a1a; color:#f87171; border:1px solid #7f1d1d; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600",
    "中性": "background:#1e1e1a; color:#a3a380; border:1px solid #404020; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600",
}
SENT_LEFT = {"正面": "#4ade80", "负面": "#f87171", "中性": "#404040"}
BTN_PRIMARY = "background:#fff; color:#000; border:none; border-radius:7px; padding:8px 20px; font-size:13px; font-weight:600; cursor:pointer"
BTN_GHOST   = "background:transparent; color:#888; border:1px solid #333; border-radius:7px; padding:7px 14px; font-size:13px; cursor:pointer"


def render() -> None:
    state = {"page": 0, "platform": None, "sentiment": None, "review_type": None}

    # ── 顶部标题 ─────────────────────────────────────────────────
    with ui.row().classes("w-full items-center justify-between").style("margin-bottom:20px"):
        with ui.column().classes("gap-0"):
            ui.label("评论列表").style("font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px")
            ui.label("Review Explorer").style("font-size:12px; color:#444")

    # ── 筛选栏 ───────────────────────────────────────────────────
    with ui.element("div").style(CARD + "; margin-bottom:16px"):
        with ui.row().classes("w-full items-end gap-4 flex-wrap"):
            platform_sel = ui.select(
                options={"": "全部平台", **{p.value: p.value for p in Platform}},
                label="平台", value=""
            ).style("min-width:130px").props("dark dense outlined color=white label-color=grey-6")

            sentiment_sel = ui.select(
                options={"": "全部情感", **{s.value: s.value for s in SentimentLabel}},
                label="情感", value=""
            ).style("width:120px").props("dark dense outlined color=white label-color=grey-6")

            type_sel = ui.select(
                options={"": "全部类型", **{t.value: t.value for t in ReviewType}},
                label="类型", value=""
            ).style("width:120px").props("dark dense outlined color=white label-color=grey-6")

            def do_filter():
                state["page"] = 0
                state["platform"] = platform_sel.value or None
                state["sentiment"] = sentiment_sel.value or None
                state["review_type"] = type_sel.value or None
                refresh()

            ui.button("筛选", on_click=do_filter).style(BTN_PRIMARY)

            with ui.row().classes("gap-2"):
                ui.button("CSV",   on_click=lambda: _export("csv")).style(BTN_GHOST)
                ui.button("EXCEL", on_click=lambda: _export("excel")).style(BTN_GHOST)
                ui.button("JSON",  on_click=lambda: _export("json")).style(BTN_GHOST)

    # ── 列表区 ───────────────────────────────────────────────────
    list_col = ui.column().classes("w-full gap-3")

    # ── 分页 ─────────────────────────────────────────────────────
    pager = ui.row().classes("w-full justify-center items-center gap-3").style("margin-top:16px")

    def refresh():
        list_col.clear()
        pager.clear()
        platform = Platform(state["platform"]) if state["platform"] else None
        sentiment = SentimentLabel(state["sentiment"]) if state["sentiment"] else None
        review_type = ReviewType(state["review_type"]) if state["review_type"] else None

        reviews = get_reviews(
            platform=platform, sentiment=sentiment, review_type=review_type,
            limit=_PAGE_SIZE, offset=state["page"] * _PAGE_SIZE,
        )
        total = count_reviews(platform=platform, sentiment=sentiment, review_type=review_type)
        total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
        cur = state["page"]

        with list_col:
            ui.label(f"共 {total} 条").style("font-size:12px; color:#444; margin-bottom:4px")
            if not reviews:
                with ui.element("div").style(CARD + "; text-align:center; padding:48px"):
                    ui.label("暂无数据，请先爬取评论").style("font-size:14px; color:#333")
            else:
                for rev in reviews:
                    _render_card(rev)

        with pager:
            ui.button("«", on_click=lambda: _go(0)).props("flat dense").style("color:#555").set_enabled(cur > 0)
            ui.button("‹", on_click=lambda: _go(cur - 1)).props("flat dense").style("color:#888").set_enabled(cur > 0)
            ui.label(f"{cur + 1} / {total_pages}").style("font-size:12px; color:#444; min-width:64px; text-align:center")
            ui.button("›", on_click=lambda: _go(cur + 1)).props("flat dense").style("color:#888").set_enabled(cur < total_pages - 1)
            ui.button("»", on_click=lambda: _go(total_pages - 1)).props("flat dense").style("color:#555").set_enabled(cur < total_pages - 1)

    def _go(p: int):
        state["page"] = max(0, p)
        refresh()

    def _export(fmt: str):
        from processors.reporter import export_csv, export_excel, export_json
        platform = Platform(state["platform"]) if state["platform"] else None
        sentiment = SentimentLabel(state["sentiment"]) if state["sentiment"] else None
        reviews = get_reviews(platform=platform, sentiment=sentiment, limit=100000)
        path = {"csv": export_csv, "excel": export_excel, "json": export_json}[fmt](reviews)
        ui.notify(f"✅ 已导出: {path}", type="positive")

    refresh()


def _render_card(rev: Review) -> None:
    snt_val = rev.sentiment.value if rev.sentiment else "中性"
    left_color = SENT_LEFT.get(snt_val, "#333")

    with ui.element("div").style(
        f"background:#111; border:1px solid #1e1e1e; border-left:3px solid {left_color};"
        "border-radius:10px; padding:16px 20px; transition:border-color 0.15s"
    ):
        # ── 头部：平台 + 店名 + 评分 ──────────────────────────────
        with ui.row().classes("w-full items-start justify-between gap-2 flex-wrap"):
            with ui.row().classes("items-center gap-2 flex-wrap"):
                ui.label(rev.platform.value).style(
                    "font-size:10px; color:#555; background:#1a1a1a;"
                    "border:1px solid #2a2a2a; border-radius:4px; padding:1px 8px"
                )
                ui.label(rev.shop_name).style("font-size:13px; color:#888; font-weight:500")
                if rev.review_type.value == "客诉":
                    ui.label("⚠ 客诉").style(
                        "font-size:10px; color:#f87171; background:#2e1a1a;"
                        "border:1px solid #7f1d1d; border-radius:4px; padding:1px 8px"
                    )
                if rev.sentiment:
                    ui.label(snt_val).style(SENT_STYLE.get(snt_val, ""))
                if rev.ocr_strategy:
                    icons = {"api_intercept": "⚡", "dom_parse": "🌐", "ocr_screenshot": "📷"}
                    ui.label(f"{icons.get(rev.ocr_strategy, '')}{rev.ocr_strategy}").style(
                        "font-size:10px; color:#555; background:#1a1a1a;"
                        "border:1px solid #2a2a2a; border-radius:4px; padding:1px 6px"
                    )

            with ui.column().classes("items-end gap-0"):
                stars = "★" * int(rev.rating) + "☆" * max(0, 5 - int(rev.rating))
                ui.label(stars).style("color:#f59e0b; font-size:14px; letter-spacing:1px")
                if rev.published_at:
                    ui.label(rev.published_at.strftime("%Y-%m-%d %H:%M")).style("font-size:10px; color:#333; margin-top:2px")

        # ── 用户名 ───────────────────────────────────────────────
        ui.label(f"👤 {rev.reviewer_name}").style("font-size:12px; color:#444; margin-top:8px")

        # ── 评论正文 ─────────────────────────────────────────────
        ui.label(rev.content).style("font-size:14px; color:#bbb; line-height:1.6; margin:6px 0")

        if rev.translated_content:
            ui.label(f"🌐 {rev.translated_content}").style("font-size:12px; color:#4a7fa8; font-style:italic")

        # ── 子评分 ───────────────────────────────────────────────
        if rev.child_rating:
            import json as _j
            try:
                sub = _j.loads(rev.child_rating)
                with ui.row().classes("gap-2 flex-wrap").style("margin-top:6px"):
                    for k, v in sub.items():
                        ui.label(f"{k}: {v}").style(
                            "font-size:10px; color:#6366f1; background:#1e1e30;"
                            "border:1px solid #2a2a40; border-radius:4px; padding:1px 8px"
                        )
            except Exception:
                pass

        # ── 图片 ─────────────────────────────────────────────────
        if rev.image_urls:
            with ui.row().classes("gap-2 flex-wrap").style("margin-top:6px"):
                for url in rev.image_urls[:6]:
                    ui.image(url).style("width:72px; height:72px; object-fit:cover; border-radius:6px; border:1px solid #222; cursor:pointer").on(
                        "click", lambda u=url: ui.open(u)
                    )

        # ── 商家回复 ─────────────────────────────────────────────
        if rev.merchant_reply:
            with ui.element("div").style(
                "background:#0e0e0e; border:1px solid #1a1a1a; border-radius:8px;"
                "padding:10px 14px; margin-top:8px"
            ):
                with ui.row().classes("items-start gap-2"):
                    ui.label("🏪").style("font-size:14px")
                    with ui.column().classes("gap-1"):
                        ui.label("商家回复").style("font-size:10px; color:#555; font-weight:600")
                        ui.label(rev.merchant_reply).style("font-size:12px; color:#666")
                        if rev.reply_translation:
                            ui.label(f"🌐 {rev.reply_translation}").style("font-size:11px; color:#4a7fa8; font-style:italic")

        # ── 关键词 ───────────────────────────────────────────────
        if rev.keywords:
            with ui.row().classes("gap-1 flex-wrap").style("margin-top:6px"):
                for kw in rev.keywords:
                    ui.label(f"#{kw}").style(
                        "font-size:10px; color:#555; background:#1a1a1a;"
                        "border-radius:3px; padding:1px 6px"
                    )

        # ── 建议回复 ─────────────────────────────────────────────
        if rev.suggested_reply:
            with ui.expansion("建议回复").classes("w-full").style("margin-top:6px; color:#555"):
                ui.label(rev.suggested_reply).style(
                    "font-size:12px; color:#666; background:#0e0e0e;"
                    "border-left:2px solid #4ade80; padding:10px 14px; border-radius:0 6px 6px 0"
                )

        # ── 底部元信息 ───────────────────────────────────────────
        with ui.row().classes("items-center gap-4 flex-wrap").style("margin-top:8px; padding-top:8px; border-top:1px solid #1a1a1a"):
            if rev.page_url:
                display = rev.page_url[:60] + ("…" if len(rev.page_url) > 60 else "")
                ui.link(f"🔗 {display}", rev.page_url, new_tab=True).style("font-size:11px; color:#444; text-decoration:none")
            if rev.crawled_at:
                ui.label(f"🕐 采集 {rev.crawled_at.strftime('%Y-%m-%d %H:%M:%S')}").style("font-size:10px; color:#2a2a2a; margin-left:auto")
