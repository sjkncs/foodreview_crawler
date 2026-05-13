"""
舆情监控页面 — NiceGUI UI  黑白配色
"""
from __future__ import annotations
import asyncio
import csv
import io
import logging
from datetime import datetime

from nicegui import ui, run

logger = logging.getLogger(__name__)

# ── 黑白色系常量 ────────────────────────────────────────────────
CARD  = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"
CARD2 = "background:#111; border:1px solid #1e1e1e; border-radius:10px; padding:16px"

SENT_STYLE = {
    "正面": "background:#1a2e1a; color:#4ade80; border:1px solid #166534; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600",
    "负面": "background:#2e1a1a; color:#f87171; border:1px solid #7f1d1d; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600",
    "中性": "background:#1e1e1a; color:#d4d4a8; border:1px solid #404020; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600",
}
SOURCE_ICONS = {
    "百度新闻": "📰", "微博": "🔥", "知乎": "💡",
    "36氪": "🚀", "虎嗅": "🐯", "科技媒体": "📡",
}

BTN_PRIMARY = "background:#fff; color:#000; border:none; border-radius:7px; padding:8px 20px; font-size:13px; font-weight:600; cursor:pointer"
BTN_GHOST   = "background:transparent; color:#888; border:1px solid #333; border-radius:7px; padding:8px 16px; font-size:13px; cursor:pointer"


def render() -> None:
    from core.sentiment_db import (
        init_sentiment_db, search_articles, count_articles,
        get_sentiment_distribution, get_source_distribution,
        get_daily_trend, get_top_tags,
    )
    init_sentiment_db()

    state = {
        "keyword": "喜茶",
        "source": "",
        "sentiment": "",
        "days": 7,
        "page": 0,
        "page_size": 20,
        "crawling": False,
    }

    # ── 顶部 ─────────────────────────────────────────────────────
    with ui.row().classes("w-full items-center justify-between").style("margin-bottom:24px"):
        with ui.column().classes("gap-1"):
            ui.label("舆情监控").style("font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px")
            ui.label("Brand Sentiment Intelligence").style("font-size:12px; color:#444")
        with ui.row().classes("items-center gap-2"):
            ui.label("").style("width:8px;height:8px;border-radius:50%;background:#4ade80")
            ui.label("实时监控").style("font-size:12px; color:#555")

    # ── 搜索栏 ───────────────────────────────────────────────────
    with ui.element("div").style(CARD + "; margin-bottom:16px"):
        with ui.row().classes("w-full items-end gap-4 flex-wrap"):
            kw_input = (
                ui.input(label="关键词", placeholder="喜茶 / 奈雪 / 霸王茶姬", value=state["keyword"])
                .style("flex:1; min-width:180px")
                .props('dark dense outlined color=white label-color=grey-6')
            )
            source_sel = (
                ui.select(["全部", "百度新闻", "微博", "知乎", "36氪", "虎嗅"], label="来源", value="全部")
                .style("width:130px")
                .props('dark dense outlined color=white label-color=grey-6')
            )
            snt_sel = (
                ui.select(["全部", "正面", "负面", "中性"], label="情感", value="全部")
                .style("width:110px")
                .props('dark dense outlined color=white label-color=grey-6')
            )
            days_sel = (
                ui.select({"1": "近1天", "3": "近3天", "7": "近7天", "30": "近30天"}, label="时间", value="7")
                .style("width:110px")
                .props('dark dense outlined color=white label-color=grey-6')
            )

            def do_search():
                state["keyword"]   = kw_input.value or "喜茶"
                state["source"]    = "" if source_sel.value == "全部" else source_sel.value
                state["sentiment"] = "" if snt_sel.value == "全部" else snt_sel.value
                state["days"]      = int(days_sel.value)
                state["page"]      = 0
                _refresh_all()

            ui.button("搜索", on_click=do_search).style(BTN_PRIMARY)
            ui.button("导出 CSV", on_click=lambda: _export_csv(state)).style(BTN_GHOST)

    # ── 采集控制栏 ───────────────────────────────────────────────
    with ui.element("div").style(
        CARD + "; margin-bottom:16px; border-left:3px solid #fff"
    ):
        with ui.row().classes("items-center gap-4 flex-wrap"):
            with ui.column().classes("gap-0"):
                ui.label("立即采集").style("font-size:14px; font-weight:600; color:#fff")
                ui.label("触发后台爬虫从各平台拉取最新数据").style("font-size:11px; color:#555")

            crawl_kw = (
                ui.input(label="采集关键词", placeholder="喜茶", value="喜茶")
                .style("width:140px")
                .props('dark dense outlined color=white label-color=grey-6')
            )
            crawl_days = (
                ui.select({"7": "近7天", "3": "近3天", "1": "近1天"}, label="范围", value="7")
                .style("width:110px")
                .props('dark dense outlined color=white label-color=grey-6')
            )
            status_label = ui.label("").style("font-size:12px; color:#666")
            spinner = ui.spinner("dots", size="sm").style("color:#fff").bind_visibility_from(state, "crawling")

            async def do_crawl():
                if state["crawling"]:
                    return
                state["crawling"] = True
                status_label.set_text("⏳ 正在采集…")
                try:
                    from sentiment_monitor import run_once
                    new = await run.io_bound(
                        lambda: asyncio.run(
                            run_once(crawl_kw.value or "喜茶", int(crawl_days.value), headless=False)
                        )
                    )
                    status_label.set_text(f"✅ 新增 {len(new)} 条")
                    _refresh_all()
                except Exception as e:
                    status_label.set_text(f"❌ {str(e)[:60]}")
                    logger.error("采集失败: %s", e)
                finally:
                    state["crawling"] = False

            ui.button("▶ 开始采集", on_click=do_crawl).style(BTN_PRIMARY)

    # ── 图表区 ───────────────────────────────────────────────────
    charts_row = ui.row().classes("w-full gap-4 flex-wrap").style("margin-bottom:16px")

    # ── 标签云 ───────────────────────────────────────────────────
    tags_card = ui.element("div").style(CARD + "; margin-bottom:16px")

    # ── 文章列表 ─────────────────────────────────────────────────
    list_col = ui.column().classes("w-full gap-2")

    # ── 分页 ─────────────────────────────────────────────────────
    pager_row = ui.row().classes("w-full justify-center items-center gap-2").style("margin-top:16px")

    # ═══════════════════════════════════════════════════════════
    def _refresh_all():
        kw  = state["keyword"]
        src = state["source"]
        snt = state["sentiment"]
        d   = state["days"]

        # 图表
        charts_row.clear()
        with charts_row:
            snt_dist = get_sentiment_distribution(kw)
            src_dist = get_source_distribution(kw)
            trend    = get_daily_trend(kw, d)
            _render_charts(snt_dist, src_dist, trend, d)

        # 标签云
        tags_card.clear()
        with tags_card:
            tags = get_top_tags(kw, limit=30)
            with ui.row().classes("items-center gap-2").style("margin-bottom:12px"):
                ui.label("# 高频标签").style("font-size:13px; font-weight:600; color:#888; letter-spacing:1px")
            if tags:
                max_cnt = tags[0][1] if tags else 1
                with ui.row().classes("flex-wrap gap-2"):
                    for tag, cnt in tags:
                        ratio = cnt / max_cnt
                        sz = "14px" if ratio > 0.6 else ("12px" if ratio > 0.3 else "11px")
                        opacity = "1" if ratio > 0.6 else ("0.75" if ratio > 0.3 else "0.5")
                        ui.label(f"{tag}  {cnt}").style(
                            f"font-size:{sz}; color:#fff; opacity:{opacity};"
                            "background:#1f1f1f; border:1px solid #2a2a2a;"
                            "border-radius:20px; padding:3px 12px; cursor:default"
                        )
            else:
                ui.label("暂无标签，先触发一次采集").style("font-size:12px; color:#444")

        # 列表
        _refresh_list(kw, src, snt, d)

    def _refresh_list(kw, src, snt, d):
        list_col.clear()
        pager_row.clear()

        articles = search_articles(
            keyword=kw, source=src, sentiment=snt, days=d,
            limit=state["page_size"], offset=state["page"] * state["page_size"]
        )
        total = count_articles(kw, src, snt)
        total_pages = max(1, (total + state["page_size"] - 1) // state["page_size"])

        with list_col:
            # 结果小计
            with ui.row().classes("items-center gap-3").style("margin-bottom:8px"):
                ui.label(f"共 {total} 条").style("font-size:12px; color:#555")
                if snt:
                    ui.label(snt).style(SENT_STYLE.get(snt, ""))
                if src:
                    ui.label(SOURCE_ICONS.get(src, "") + " " + src).style(
                        "font-size:11px; color:#666; background:#1a1a1a;"
                        "border:1px solid #2a2a2a; border-radius:4px; padding:2px 8px"
                    )

            if not articles:
                with ui.element("div").style(CARD + "; text-align:center; padding:48px"):
                    ui.label("暂无数据").style("font-size:14px; color:#444")
                    ui.label("请调整筛选条件或先触发采集").style("font-size:12px; color:#333; margin-top:4px")
            else:
                for art in articles:
                    _render_card(art)

        with pager_row:
            cur = state["page"]
            ui.button("«", on_click=lambda: _go(0)).props("flat dense").style("color:#555").set_enabled(cur > 0)
            ui.button("‹", on_click=lambda: _go(cur - 1)).props("flat dense").style("color:#888").set_enabled(cur > 0)
            ui.label(f"{cur + 1} / {total_pages}").style("font-size:12px; color:#555; min-width:60px; text-align:center")
            ui.button("›", on_click=lambda: _go(cur + 1)).props("flat dense").style("color:#888").set_enabled(cur < total_pages - 1)
            ui.button("»", on_click=lambda: _go(total_pages - 1)).props("flat dense").style("color:#555").set_enabled(cur < total_pages - 1)

    def _go(p: int):
        state["page"] = max(0, p)
        _refresh_list(state["keyword"], state["source"], state["sentiment"], state["days"])

    _refresh_all()


# ── 图表渲染（黑白 ECharts 主题）────────────────────────────────
def _render_charts(snt_dist: dict, src_dist: dict, trend: list, days: int):
    DARK_CHART = {
        "backgroundColor": "transparent",
        "textStyle": {"color": "#666"},
    }

    total = sum(snt_dist.values()) or 1

    # 情感饼图
    with ui.element("div").style(
        "background:#111; border:1px solid #1e1e1e; border-radius:10px; padding:16px; flex:1; min-width:220px"
    ):
        ui.label("情感分布").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:8px")
        if snt_dist:
            pie_data = [
                {"value": snt_dist.get("正面", 0), "name": "正面", "itemStyle": {"color": "#4ade80"}},
                {"value": snt_dist.get("负面", 0), "name": "负面", "itemStyle": {"color": "#f87171"}},
                {"value": snt_dist.get("中性", 0), "name": "中性", "itemStyle": {"color": "#555"}},
            ]
            ui.echart({
                **DARK_CHART,
                "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)",
                            "backgroundColor": "#1a1a1a", "borderColor": "#333", "textStyle": {"color": "#ddd"}},
                "legend": {"bottom": 0, "textStyle": {"color": "#555"}, "itemWidth": 10, "itemHeight": 10},
                "series": [{"type": "pie", "radius": ["45%", "68%"], "center": ["50%", "45%"],
                             "data": pie_data,
                             "label": {"show": True, "formatter": "{d}%", "color": "#555", "fontSize": 11},
                             "emphasis": {"itemStyle": {"shadowBlur": 6, "shadowColor": "rgba(255,255,255,0.1)"}}}],
            }).classes("w-full").style("height:180px")

            # 数字行
            with ui.row().classes("justify-around w-full").style("margin-top:4px"):
                for key, color in [("正面", "#4ade80"), ("负面", "#f87171"), ("中性", "#666")]:
                    cnt = snt_dist.get(key, 0)
                    pct = round(cnt / total * 100)
                    with ui.column().classes("items-center gap-0"):
                        ui.label(str(cnt)).style(f"font-size:18px; font-weight:700; color:{color}")
                        ui.label(f"{key} {pct}%").style("font-size:10px; color:#444")
        else:
            ui.label("暂无数据").style("font-size:12px; color:#333; padding:40px 0; text-align:center")

    # 来源分布
    with ui.element("div").style(
        "background:#111; border:1px solid #1e1e1e; border-radius:10px; padding:16px; flex:1; min-width:220px"
    ):
        ui.label("来源分布").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:8px")
        if src_dist:
            sources = list(src_dist.keys())
            counts  = [src_dist[s] for s in sources]
            ui.echart({
                **DARK_CHART,
                "tooltip": {"trigger": "axis", "backgroundColor": "#1a1a1a", "borderColor": "#333",
                            "textStyle": {"color": "#ddd"}},
                "grid": {"left": "2%", "right": "8%", "bottom": "2%", "top": "2%", "containLabel": True},
                "xAxis": {"type": "value", "axisLabel": {"color": "#444", "fontSize": 10},
                           "splitLine": {"lineStyle": {"color": "#1a1a1a"}}},
                "yAxis": {"type": "category", "data": sources,
                           "axisLabel": {"color": "#555", "fontSize": 11}},
                "series": [{
                    "type": "bar", "data": counts, "barMaxWidth": 18,
                    "itemStyle": {"color": "#333", "borderRadius": [0, 3, 3, 0]},
                    "emphasis": {"itemStyle": {"color": "#555"}},
                    "label": {"show": True, "position": "right", "color": "#555", "fontSize": 10},
                }],
            }).classes("w-full").style("height:180px")
        else:
            ui.label("暂无数据").style("font-size:12px; color:#333; padding:40px 0; text-align:center")

    # 趋势折线（全宽）
    with ui.element("div").style(
        "background:#111; border:1px solid #1e1e1e; border-radius:10px; padding:16px; width:100%"
    ):
        ui.label(f"近 {days} 天趋势").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:8px")
        if trend:
            days_list = [t["day"] for t in trend]
            cnt_list  = [t["cnt"] for t in trend]
            ui.echart({
                **DARK_CHART,
                "tooltip": {"trigger": "axis", "backgroundColor": "#1a1a1a", "borderColor": "#333",
                            "textStyle": {"color": "#ddd"}},
                "grid": {"left": "2%", "right": "2%", "bottom": "12%", "top": "8%", "containLabel": True},
                "xAxis": {"type": "category", "data": days_list,
                           "axisLabel": {"color": "#444", "fontSize": 10, "rotate": 30},
                           "axisLine": {"lineStyle": {"color": "#222"}}},
                "yAxis": {"type": "value", "axisLabel": {"color": "#444", "fontSize": 10},
                           "splitLine": {"lineStyle": {"color": "#1a1a1a"}}},
                "series": [{
                    "type": "line", "data": cnt_list, "smooth": True,
                    "symbol": "circle", "symbolSize": 5,
                    "lineStyle": {"color": "#fff", "width": 1.5},
                    "itemStyle": {"color": "#fff"},
                    "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                             "colorStops": [
                                                 {"offset": 0, "color": "rgba(255,255,255,0.08)"},
                                                 {"offset": 1, "color": "rgba(255,255,255,0)"},
                                             ]}},
                }],
            }).classes("w-full").style("height:120px")
        else:
            ui.label("暂无趋势数据").style("font-size:12px; color:#333; padding:24px 0; text-align:center")


# ── 文章卡片 ────────────────────────────────────────────────────
def _render_card(art: dict):
    snt      = art.get("sentiment", "中性")
    src      = art.get("source", "")
    src_icon = SOURCE_ICONS.get(src, "📄")

    with ui.element("div").style(
        "background:#111; border:1px solid #1e1e1e; border-radius:10px; padding:14px 16px;"
        "transition:border-color 0.15s; cursor:default"
    ):
        with ui.row().classes("w-full items-start gap-3"):
            # 情感标签
            ui.label(snt).style(SENT_STYLE.get(snt, SENT_STYLE["中性"]))

            with ui.column().classes("flex-1 gap-1"):
                # 标题行
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.label(f"{src_icon} {src}").style(
                        "font-size:10px; color:#444; background:#1a1a1a;"
                        "border:1px solid #222; border-radius:4px; padding:1px 6px"
                    )
                    ui.link(art.get("title", "（无标题）"), art.get("url", "#"), new_tab=True).style(
                        "font-size:14px; font-weight:500; color:#e5e5e5; text-decoration:none;"
                        "flex:1; line-height:1.4"
                    )

                # 摘要
                snippet = art.get("snippet", "")
                if snippet:
                    ui.label(snippet[:140] + ("…" if len(snippet) > 140 else "")).style(
                        "font-size:12px; color:#555; line-height:1.6"
                    )

                # 元信息行
                with ui.row().classes("items-center gap-4 flex-wrap").style("margin-top:4px"):
                    if art.get("author"):
                        ui.label(f"👤 {art['author']}").style("font-size:11px; color:#3a3a3a")
                    pt = (art.get("publish_time") or "")[:10]
                    if pt:
                        ui.label(f"📅 {pt}").style("font-size:11px; color:#3a3a3a")
                    ct = (art.get("crawl_time") or "")[:16].replace("T", " ")
                    if ct:
                        ui.label(f"采集 {ct}").style("font-size:10px; color:#2a2a2a")
                    tags = art.get("tags", "")
                    if tags:
                        for tag in tags.split(",")[:5]:
                            tag = tag.strip()
                            if tag:
                                ui.label(f"#{tag}").style(
                                    "font-size:10px; color:#3a3a3a; background:#1a1a1a;"
                                    "border-radius:3px; padding:1px 5px"
                                )


def _export_csv(state: dict):
    from core.sentiment_db import search_articles
    articles = search_articles(
        keyword=state["keyword"],
        source=state["source"],
        sentiment=state["sentiment"],
        days=state["days"],
        limit=5000, offset=0,
    )
    if not articles:
        ui.notify("无数据可导出", type="warning")
        return
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=articles[0].keys())
    writer.writeheader()
    writer.writerows(articles)
    filename = f"sentiment_{state['keyword']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    ui.download(buf.getvalue().encode("utf-8-sig"), filename)
    ui.notify(f"已导出 {len(articles)} 条", type="positive")
