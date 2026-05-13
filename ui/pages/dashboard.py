"""
仪表盘页面 - 数据概览（黑白配色）
"""
from nicegui import ui
from core.database import count_reviews, get_sentiment_stats, get_top_keywords
from core.models import Platform, SentimentLabel

CARD = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"


def render() -> None:
    with ui.column().classes("w-full gap-4"):
        with ui.row().classes("items-center justify-between w-full").style("margin-bottom:8px"):
            with ui.column().classes("gap-0"):
                ui.label("仪表盘").style("font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px")
                ui.label("Overview").style("font-size:12px; color:#444")

        # ── 统计卡片行 ──────────────────────────────────────────
        with ui.row().classes("w-full gap-3 flex-wrap"):
            _stat_card("总评论数",  str(count_reviews()),                                          "#fff",    "◈")
            _stat_card("正面评论",  str(count_reviews(sentiment=SentimentLabel.POSITIVE)), "#4ade80", "↑")
            _stat_card("负面评论",  str(count_reviews(sentiment=SentimentLabel.NEGATIVE)), "#f87171", "↓")
            _stat_card("中性评论",  str(count_reviews(sentiment=SentimentLabel.NEUTRAL)),  "#888",    "—")

        # ── 平台情感分布图 ──────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("各平台情感分布").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px")
            stats = get_sentiment_stats()
            if stats:
                _render_platform_chart(stats)
            else:
                ui.label("暂无数据，请先爬取评论").style("font-size:13px; color:#333; text-align:center; padding:40px 0")

        # ── 高频关键词 ──────────────────────────────────────────
        with ui.element("div").style(CARD):
            ui.label("高频关键词 Top 20").style("font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px")
            keywords = get_top_keywords(20)
            if keywords:
                max_cnt = keywords[0][1] if keywords else 1
                with ui.row().classes("flex-wrap gap-2"):
                    for word, count in keywords:
                        ratio = count / max_cnt
                        opacity = "1" if ratio > 0.6 else ("0.7" if ratio > 0.3 else "0.4")
                        ui.label(f"{word}  {count}").style(
                            f"font-size:12px; color:#fff; opacity:{opacity};"
                            "background:#1a1a1a; border:1px solid #2a2a2a;"
                            "border-radius:20px; padding:3px 12px"
                        )
            else:
                ui.label("暂无关键词数据").style("font-size:13px; color:#333")


def _stat_card(title: str, value: str, color: str, icon: str) -> None:
    with ui.element("div").style(
        "background:#111; border:1px solid #1e1e1e; border-radius:10px; padding:18px 20px;"
        "flex:1; min-width:140px"
    ):
        with ui.row().classes("items-center justify-between w-full").style("margin-bottom:8px"):
            ui.label(title).style("font-size:11px; color:#444; font-weight:500; letter-spacing:0.5px")
            ui.label(icon).style(f"font-size:16px; color:{color}; opacity:0.6")
        ui.label(value).style(f"font-size:28px; font-weight:700; color:{color}; letter-spacing:-1px")


def _render_platform_chart(stats: list[dict]) -> None:
    platforms = [s["platform"] for s in stats]
    positive  = [s["positive"] for s in stats]
    negative  = [s["negative"] for s in stats]
    neutral   = [s["neutral"]  for s in stats]

    options = {
        "backgroundColor": "transparent",
        "textStyle": {"color": "#555"},
        "tooltip": {"trigger": "axis", "backgroundColor": "#1a1a1a",
                    "borderColor": "#333", "textStyle": {"color": "#ddd"}},
        "legend": {"data": ["正面", "负面", "中性"], "textStyle": {"color": "#555"},
                   "itemWidth": 10, "itemHeight": 10},
        "grid": {"left": "2%", "right": "2%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": platforms,
                  "axisLabel": {"color": "#444"}, "axisLine": {"lineStyle": {"color": "#222"}}},
        "yAxis": {"type": "value", "axisLabel": {"color": "#444"},
                  "splitLine": {"lineStyle": {"color": "#1a1a1a"}}},
        "series": [
            {"name": "正面", "type": "bar", "stack": "total",
             "data": positive, "itemStyle": {"color": "#4ade80"}},
            {"name": "负面", "type": "bar", "stack": "total",
             "data": negative, "itemStyle": {"color": "#f87171"}},
            {"name": "中性", "type": "bar", "stack": "total",
             "data": neutral,  "itemStyle": {"color": "#333"}},
        ],
    }
    ui.echart(options).classes("w-full").style("height:240px")
