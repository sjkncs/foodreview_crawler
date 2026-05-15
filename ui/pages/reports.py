"""
统计报表页面 — 深色主题
支持平台筛选，所有图表/关键词/情感数据随平台联动刷新
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from nicegui import ui

from core.database import (
    get_sentiment_stats_by_platform,
    get_top_keywords,
    get_trend_data,
)
from core.models import Platform

CARD = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"
DARK_CHART = {
    "backgroundColor": "transparent",
    "textStyle": {"color": "#555"},
}

# 平台选项：空字符串 = 全部
_PLATFORM_OPTIONS: dict[str, str] = {"": "全部平台"}
_PLATFORM_OPTIONS.update({p.value: p.value for p in Platform})


def render() -> None:
    # ── 顶部标题 + 平台筛选 ─────────────────────────────────────
    state: dict = {"platform": None}

    with ui.column().classes("w-full gap-4"):
        with ui.row().classes("items-center justify-between w-full").style("margin-bottom:8px"):
            with ui.column().classes("gap-0"):
                ui.label("统计报表").style(
                    "font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px"
                )
                ui.label("Analytics").style("font-size:12px; color:#444")

            # 平台筛选下拉
            platform_sel = (
                ui.select(
                    options=_PLATFORM_OPTIONS,
                    value="",
                    label="筛选平台",
                )
                .props("outlined dense dark")
                .style(
                    "min-width:140px; background:#141414; border-radius:8px;"
                    "font-size:13px; color:#ccc"
                )
            )

        # ── 图表容器（用 ui.refreshable 实现联动刷新）──────────────

        @ui.refreshable
        def charts_area() -> None:
            plat_val = state["platform"]
            plat_enum: Optional[Platform] = Platform(plat_val) if plat_val else None

            stats = get_sentiment_stats_by_platform(plat_enum)

            # ── 平台评分对比 ─────────────────────────────────────
            with ui.element("div").style(CARD):
                ui.label("平台评分 & 评论量对比").style(
                    "font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px"
                )
                if stats:
                    platforms   = [s["platform"] for s in stats]
                    avg_ratings = [round(s.get("avg_rating") or 0, 2) for s in stats]
                    totals      = [s["total"] for s in stats]
                    ui.echart({
                        **DARK_CHART,
                        "tooltip": {
                            "trigger": "axis",
                            "backgroundColor": "#1a1a1a",
                            "borderColor": "#333",
                            "textStyle": {"color": "#ddd"},
                        },
                        "legend": {
                            "data": ["平均评分", "评论数"],
                            "textStyle": {"color": "#555"},
                            "itemWidth": 10,
                        },
                        "grid": {"left": "2%", "right": "4%", "bottom": "3%", "containLabel": True},
                        "xAxis": {
                            "type": "category",
                            "data": platforms,
                            "axisLabel": {"color": "#444"},
                            "axisLine": {"lineStyle": {"color": "#222"}},
                        },
                        "yAxis": [
                            {
                                "type": "value",
                                "name": "评分",
                                "min": 0,
                                "max": 5,
                                "axisLabel": {"color": "#444"},
                                "splitLine": {"lineStyle": {"color": "#1a1a1a"}},
                            },
                            {
                                "type": "value",
                                "name": "数量",
                                "axisLabel": {"color": "#444"},
                                "splitLine": {"show": False},
                            },
                        ],
                        "series": [
                            {
                                "name": "平均评分",
                                "type": "bar",
                                "data": avg_ratings,
                                "itemStyle": {"color": "#fff", "borderRadius": [3, 3, 0, 0]},
                            },
                            {
                                "name": "评论数",
                                "type": "line",
                                "yAxisIndex": 1,
                                "data": totals,
                                "smooth": True,
                                "lineStyle": {"color": "#555"},
                                "itemStyle": {"color": "#555"},
                                "symbol": "circle",
                                "symbolSize": 5,
                            },
                        ],
                    }).classes("w-full").style("height:260px")
                else:
                    ui.label("暂无数据，请先爬取评论").style(
                        "font-size:13px; color:#333; text-align:center; padding:40px 0"
                    )

            # ── 情感饼图 + 关键词 ─────────────────────────────────
            with ui.row().classes("w-full gap-4 flex-wrap"):
                # 情感分布
                with ui.element("div").style(CARD + "; flex:1; min-width:280px"):
                    ui.label("整体情感分布").style(
                        "font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px"
                    )
                    if stats:
                        total_pos = sum(s["positive"] for s in stats)
                        total_neg = sum(s["negative"] for s in stats)
                        total_neu = sum(s["neutral"]  for s in stats)
                        ui.echart({
                            **DARK_CHART,
                            "tooltip": {
                                "trigger": "item",
                                "formatter": "{b}: {c} ({d}%)",
                                "backgroundColor": "#1a1a1a",
                                "borderColor": "#333",
                                "textStyle": {"color": "#ddd"},
                            },
                            "legend": {
                                "bottom": 0,
                                "textStyle": {"color": "#555"},
                                "itemWidth": 10,
                                "itemHeight": 10,
                            },
                            "series": [{
                                "type": "pie",
                                "radius": ["42%", "65%"],
                                "data": [
                                    {"value": total_pos, "name": "正面", "itemStyle": {"color": "#4ade80"}},
                                    {"value": total_neg, "name": "负面", "itemStyle": {"color": "#f87171"}},
                                    {"value": total_neu, "name": "中性", "itemStyle": {"color": "#404040"}},
                                ],
                                "label": {"color": "#555", "fontSize": 11},
                                "emphasis": {
                                    "itemStyle": {"shadowBlur": 6, "shadowColor": "rgba(255,255,255,0.1)"}
                                },
                            }],
                        }).classes("w-full").style("height:200px")
                    else:
                        ui.label("暂无数据").style(
                            "font-size:13px; color:#333; text-align:center; padding:40px 0"
                        )

                # 关键词云
                with ui.element("div").style(CARD + "; flex:1; min-width:280px"):
                    label_suffix = f"（{plat_val}）" if plat_val else "（全部平台）"
                    ui.label(f"高频关键词 {label_suffix}").style(
                        "font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px"
                    )
                    keywords = get_top_keywords(limit=40, platform=plat_enum)
                    if keywords:
                        max_cnt = keywords[0][1]
                        with ui.element("div").style("max-height:200px; overflow-y:auto"):
                            with ui.row().classes("flex-wrap gap-2"):
                                for word, count in keywords:
                                    ratio = count / max_cnt
                                    size    = "15px" if ratio > 0.6 else ("12px" if ratio > 0.3 else "11px")
                                    opacity = "1"    if ratio > 0.6 else ("0.7"  if ratio > 0.3 else "0.45")
                                    ui.label(f"{word}  {count}").style(
                                        f"font-size:{size}; color:#fff; opacity:{opacity};"
                                        "background:#1a1a1a; border:1px solid #2a2a2a;"
                                        "border-radius:20px; padding:3px 12px; cursor:default"
                                    )
                    else:
                        ui.label("暂无关键词数据").style("font-size:13px; color:#333")

            # ── 近7天趋势 ─────────────────────────────────────────
            with ui.element("div").style(CARD):
                ui.label("近7天评论趋势").style(
                    "font-size:12px; font-weight:600; color:#555; letter-spacing:1px; margin-bottom:12px"
                )
                _render_trend_chart(plat_enum)

        charts_area()

        # 平台切换时联动刷新
        def _on_platform_change(e) -> None:
            state["platform"] = e.value or None
            charts_area.refresh()

        platform_sel.on("update:model-value", _on_platform_change)


# ── 趋势图（按平台过滤） ────────────────────────────────────────────

def _render_trend_chart(platform: Optional[Platform] = None) -> None:
    now  = datetime.now()
    days = [(now - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)]
    day_data: dict[str, dict[str, int]] = {
        d: {"正面": 0, "负面": 0, "中性": 0} for d in days
    }

    rows = get_trend_data(platform=platform, days=7)
    for row in rows:
        raw_day = row.get("day", "")
        # DATE() 返回 YYYY-MM-DD，转换为 MM-DD
        try:
            label = datetime.strptime(raw_day, "%Y-%m-%d").strftime("%m-%d")
        except (ValueError, TypeError):
            continue
        if label in day_data:
            day_data[label]["正面"] = row.get("positive", 0) or 0
            day_data[label]["负面"] = row.get("negative", 0) or 0
            day_data[label]["中性"] = row.get("neutral",  0) or 0

    has_data = any(
        v for d in day_data.values() for v in d.values()
    )
    if not has_data:
        ui.label("暂无数据").style("font-size:13px; color:#333; text-align:center; padding:24px 0")
        return

    ui.echart({
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "#1a1a1a",
            "borderColor": "#333",
            "textStyle": {"color": "#ddd"},
        },
        "legend": {
            "data": ["正面", "负面", "中性"],
            "textStyle": {"color": "#555"},
            "itemWidth": 10,
        },
        "grid": {"left": "2%", "right": "2%", "bottom": "10%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": days,
            "axisLabel": {"color": "#444"},
            "axisLine": {"lineStyle": {"color": "#222"}},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"color": "#444"},
            "splitLine": {"lineStyle": {"color": "#1a1a1a"}},
        },
        "series": [
            {
                "name": "正面",
                "type": "line",
                "smooth": True,
                "data": [day_data[d]["正面"] for d in days],
                "lineStyle": {"color": "#4ade80"},
                "itemStyle": {"color": "#4ade80"},
                "areaStyle": {"opacity": 0.06},
            },
            {
                "name": "负面",
                "type": "line",
                "smooth": True,
                "data": [day_data[d]["负面"] for d in days],
                "lineStyle": {"color": "#f87171"},
                "itemStyle": {"color": "#f87171"},
                "areaStyle": {"opacity": 0.06},
            },
            {
                "name": "中性",
                "type": "line",
                "smooth": True,
                "data": [day_data[d]["中性"] for d in days],
                "lineStyle": {"color": "#555"},
                "itemStyle": {"color": "#555"},
            },
        ],
    }).classes("w-full").style("height:220px")
