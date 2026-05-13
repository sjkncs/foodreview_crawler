"""
统计报表页面 — 深色主题
"""
from nicegui import ui
from core.database import get_sentiment_stats, get_top_keywords, get_reviews
from core.models import Platform, SentimentLabel
from datetime import datetime, timedelta

CARD  = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"
DARK_CHART = {
    "backgroundColor": "transparent",
    "textStyle": {"color": "#555"},
}


def render() -> None:
    with ui.column().classes("w-full gap-4"):
        with ui.row().classes("items-center justify-between w-full").style("margin-bottom:8px"):
            with ui.column().classes("gap-0"):
                ui.label("统计报表").style("font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px")
                ui.label("Analytics").style("font-size:12px; color:#444")

        stats = get_sentiment_stats()

        # ── 平台评分对比 ─────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("平台评分 & 评论量对比").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px")
            if stats:
                platforms  = [s["platform"] for s in stats]
                avg_ratings = [round(s.get("avg_rating") or 0, 2) for s in stats]
                totals      = [s["total"] for s in stats]
                ui.echart({
                    **DARK_CHART,
                    "tooltip": {"trigger": "axis", "backgroundColor": "#1a1a1a",
                                "borderColor": "#333", "textStyle": {"color": "#ddd"}},
                    "legend": {"data": ["平均评分", "评论数"],
                               "textStyle": {"color": "#555"}, "itemWidth": 10},
                    "grid": {"left": "2%", "right": "4%", "bottom": "3%", "containLabel": True},
                    "xAxis": {"type": "category", "data": platforms,
                              "axisLabel": {"color": "#444"},
                              "axisLine": {"lineStyle": {"color": "#222"}}},
                    "yAxis": [
                        {"type": "value", "name": "评分", "min": 0, "max": 5,
                         "axisLabel": {"color": "#444"},
                         "splitLine": {"lineStyle": {"color": "#1a1a1a"}}},
                        {"type": "value", "name": "数量",
                         "axisLabel": {"color": "#444"},
                         "splitLine": {"show": False}},
                    ],
                    "series": [
                        {"name": "平均评分", "type": "bar", "data": avg_ratings,
                         "itemStyle": {"color": "#fff", "borderRadius": [3, 3, 0, 0]}},
                        {"name": "评论数", "type": "line", "yAxisIndex": 1,
                         "data": totals, "smooth": True,
                         "lineStyle": {"color": "#555"}, "itemStyle": {"color": "#555"},
                         "symbol": "circle", "symbolSize": 5},
                    ],
                }).classes("w-full").style("height:260px")
            else:
                ui.label("暂无数据，请先爬取评论").style("font-size:13px; color:#333; text-align:center; padding:40px 0")

        # ── 情感饼图 + 关键词 ─────────────────────────────────────
        with ui.row().classes("w-full gap-4 flex-wrap"):
            with ui.element("div").style(CARD + "; flex:1; min-width:280px"):
                ui.label("整体情感分布").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px")
                if stats:
                    total_pos = sum(s["positive"] for s in stats)
                    total_neg = sum(s["negative"] for s in stats)
                    total_neu = sum(s["neutral"]  for s in stats)
                    ui.echart({
                        **DARK_CHART,
                        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)",
                                    "backgroundColor": "#1a1a1a", "borderColor": "#333",
                                    "textStyle": {"color": "#ddd"}},
                        "legend": {"bottom": 0, "textStyle": {"color": "#555"},
                                   "itemWidth": 10, "itemHeight": 10},
                        "series": [{
                            "type": "pie", "radius": ["42%", "65%"],
                            "data": [
                                {"value": total_pos, "name": "正面", "itemStyle": {"color": "#4ade80"}},
                                {"value": total_neg, "name": "负面", "itemStyle": {"color": "#f87171"}},
                                {"value": total_neu, "name": "中性", "itemStyle": {"color": "#404040"}},
                            ],
                            "label": {"color": "#555", "fontSize": 11},
                            "emphasis": {"itemStyle": {"shadowBlur": 6, "shadowColor": "rgba(255,255,255,0.1)"}},
                        }],
                    }).classes("w-full").style("height:200px")
                else:
                    ui.label("暂无数据").style("font-size:13px; color:#333; text-align:center; padding:40px 0")

            with ui.element("div").style(CARD + "; flex:1; min-width:280px"):
                ui.label("高频关键词").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px")
                keywords = get_top_keywords(30)
                if keywords:
                    max_cnt = keywords[0][1]
                    with ui.element("div").style("max-height:200px; overflow-y:auto"):
                        with ui.row().classes("flex-wrap gap-2"):
                            for word, count in keywords:
                                ratio = count / max_cnt
                                size = "15px" if ratio > 0.6 else ("12px" if ratio > 0.3 else "11px")
                                opacity = "1" if ratio > 0.6 else ("0.7" if ratio > 0.3 else "0.45")
                                ui.label(f"{word} {count}").style(
                                    f"font-size:{size}; color:#fff; opacity:{opacity};"
                                    "background:#1a1a1a; border:1px solid #2a2a2a;"
                                    "border-radius:20px; padding:3px 12px; cursor:default"
                                )
                else:
                    ui.label("暂无关键词数据").style("font-size:13px; color:#333")

        # ── 近7天趋势 ─────────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("近7天评论趋势").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px")
            _render_trend_chart()


def _render_trend_chart() -> None:
    reviews = get_reviews(limit=5000)
    if not reviews:
        ui.label("暂无数据").style("font-size:13px; color:#333; text-align:center; padding:24px 0")
        return

    now  = datetime.now()
    days = [(now - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)]
    day_data = {d: {"正面": 0, "负面": 0, "中性": 0} for d in days}

    for r in reviews:
        ts = r.published_at or r.crawled_at
        if ts is None:
            continue
        d = ts.strftime("%m-%d")
        if d in day_data and r.sentiment:
            day_data[d][r.sentiment.value] += 1

    ui.echart({
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis", "backgroundColor": "#1a1a1a",
                    "borderColor": "#333", "textStyle": {"color": "#ddd"}},
        "legend": {"data": ["正面", "负面", "中性"],
                   "textStyle": {"color": "#555"}, "itemWidth": 10},
        "grid": {"left": "2%", "right": "2%", "bottom": "10%", "containLabel": True},
        "xAxis": {"type": "category", "data": days,
                  "axisLabel": {"color": "#444"},
                  "axisLine": {"lineStyle": {"color": "#222"}}},
        "yAxis": {"type": "value",
                  "axisLabel": {"color": "#444"},
                  "splitLine": {"lineStyle": {"color": "#1a1a1a"}}},
        "series": [
            {"name": "正面", "type": "line", "smooth": True,
             "data": [day_data[d]["正面"] for d in days],
             "lineStyle": {"color": "#4ade80"}, "itemStyle": {"color": "#4ade80"},
             "areaStyle": {"opacity": 0.06}},
            {"name": "负面", "type": "line", "smooth": True,
             "data": [day_data[d]["负面"] for d in days],
             "lineStyle": {"color": "#f87171"}, "itemStyle": {"color": "#f87171"},
             "areaStyle": {"opacity": 0.06}},
            {"name": "中性", "type": "line", "smooth": True,
             "data": [day_data[d]["中性"] for d in days],
             "lineStyle": {"color": "#555"}, "itemStyle": {"color": "#555"}},
        ],
    }).classes("w-full").style("height:220px")
