from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from nicegui import ui

from unified_collector.coordinator import COORDINATOR
from unified_collector.platform_capabilities import PLATFORM_CAPABILITIES
from unified_collector.task_loader import load_task


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "data" / "store_registry.json"
TASK_DIR = ROOT / "unified_collector" / "tasks"
EXPORT_DIR = ROOT / "exports"

CARD = "background:#141414; border:1px solid #222; border-radius:10px; padding:20px"
CARD2 = "background:#0e0e0e; border:1px solid #1a1a1a; border-radius:8px; padding:12px 16px"
BTN_P = "background:#fff; color:#000; border:none; border-radius:7px; padding:9px 18px; font-size:13px; font-weight:600"
BTN_G = "background:transparent; color:#888; border:1px solid #333; border-radius:7px; padding:8px 14px; font-size:13px"


def render() -> None:
    with ui.column().classes("w-full gap-4"):
        with ui.row().classes("items-center justify-between w-full").style("margin-bottom:8px"):
            with ui.column().classes("gap-0"):
                ui.label("大一统采集控制台").style("font-size:26px; font-weight:700; color:#fff; letter-spacing:-0.5px")
                ui.label("Unified Review Collection Console").style("font-size:12px; color:#555")
            with ui.row().classes("gap-2"):
                ui.button("打开 Stitch 原型", on_click=lambda: ui.navigate.to("/prototype")).style(BTN_G)
                ui.button("静态模板", on_click=lambda: ui.navigate.to("/stitch-static/index.html", new_tab=True)).style(BTN_G)

        _render_safety_strip()
        _render_execution_logic()

        summary = _load_registry_summary()
        with ui.row().classes("w-full gap-3 flex-wrap"):
            _metric_card("门店注册表", str(summary["store_count"]), "114 家海外门店基准库", "#fff")
            _metric_card("Google Maps URL", str(summary["platform_url_counts"].get("google_maps", 0)), "可按 JDE/国家定位", "#4ade80")
            _metric_card("任务模板", str(len(_task_files())), "unified_collector/tasks", "#fff")
            _metric_card("导出文件", str(len(_export_files())), "exports 目录", "#fff")
            _metric_card("只读安全", "ON", "禁止回复/保存/删除/提交", "#4ade80")

        with ui.grid(columns=2).classes("w-full gap-4"):
            _render_task_runner()
            _render_platform_capabilities()

        with ui.grid(columns=2).classes("w-full gap-4"):
            _render_store_registry(summary)
            _render_exports()

        _render_task_activity()


def _render_safety_strip() -> None:
    with ui.element("div").style(CARD2 + "; border-left:3px solid #fff"):
        with ui.row().classes("items-center gap-2 flex-wrap"):
            ui.icon("verified_user").style("font-size:16px; color:#4ade80")
            ui.label("当前控制台默认只读：允许登录、导航、筛选、打开详情、导出；禁止回复、保存、删除、提交、支付、修改门店配置。").style(
                "font-size:12px; color:#aaa"
            )


def _render_execution_logic() -> None:
    snapshot = COORDINATOR.snapshot()
    steps = [
        ("1 校验", "检查 JSON DSL、平台执行器、安全策略和输出字段。"),
        ("2 Dry Run", "生成将要执行的命令，不启动浏览器，用于确认范围和参数。"),
        ("3 真实采集", "按平台/账号互斥执行；默认只允许 1 个真实浏览器任务运行。"),
        ("4 标准化", "导出 JSON/CSV/Excel，并保留质量标记、订单详情、图片 URL。"),
    ]
    with ui.element("div").style(CARD2):
        with ui.row().classes("items-start justify-between gap-4 flex-wrap"):
            with ui.column().classes("gap-1"):
                ui.label("按钮执行逻辑").style("font-size:13px; color:#fff; font-weight:700")
                ui.label("所有采集动作走统一协调器：先校验、再 Dry Run、最后真实采集；真实任务有互斥锁，避免账号和浏览器会话冲突。").style(
                    "font-size:12px; color:#777"
                )
            ui.label(
                f"当前活动任务 {snapshot['active_count']} · 真实并发 {snapshot['real_concurrency']} · Dry Run 并发 {snapshot['dry_run_concurrency']}"
            ).style("font-size:12px; color:#4ade80")
        with ui.row().classes("gap-2 flex-wrap").style("margin-top:10px"):
            for title, desc in steps:
                with ui.element("div").style("background:#111; border:1px solid #222; border-radius:8px; padding:10px 12px; min-width:190px; flex:1"):
                    ui.label(title).style("font-size:12px; color:#fff; font-weight:700")
                    ui.label(desc).style("font-size:11px; color:#666")


def _metric_card(title: str, value: str, subtitle: str, color: str) -> None:
    with ui.element("div").style(
        "background:#111; border:1px solid #1e1e1e; border-radius:10px; padding:16px 18px;"
        "flex:1; min-width:170px"
    ):
        ui.label(title).style("font-size:11px; color:#555; font-weight:600; letter-spacing:.5px")
        ui.label(value).style(f"font-size:28px; font-weight:700; color:{color}; line-height:1.2")
        ui.label(subtitle).style("font-size:11px; color:#555")


def _render_task_runner() -> None:
    with ui.element("div").style(CARD):
        ui.label("统一任务运行器").style("font-size:15px; font-weight:700; color:#fff; margin-bottom:12px")
        task_paths = _task_files()
        options = {path.name: path.name for path in task_paths}
        task_select = ui.select(options=options, value=task_paths[0].name if task_paths else None, label="任务模板").classes("w-full").props(
            "dark dense outlined color=white label-color=grey-6"
        )
        ui.label("推荐流程：先点“校验任务”，再点“Dry Run”，确认无误后点“真实采集”。").style("font-size:12px; color:#777; margin-top:8px")
        dry_run = ui.checkbox("真实采集前强制 Dry Run 保护：不启动浏览器，只验证命令、门店定位和能力矩阵", value=True).props("dark color=white")
        result = ui.textarea(label="运行结果").classes("w-full").props("dark outlined autogrow readonly").style(
            "font-family:JetBrains Mono, monospace; font-size:12px; margin-top:10px"
        )
        status = ui.label("").style("font-size:12px; color:#777; margin-top:6px")

        def selected_task():
            if not task_select.value:
                raise ValueError("未找到任务模板")
            return load_task(TASK_DIR / task_select.value)

        def show_output(output: Any) -> None:
            result.value = json.dumps(output.to_dict() if hasattr(output, "to_dict") else output, ensure_ascii=False, indent=2)
            result.update()

        async def run_action(action: str) -> None:
            status.set_text(f"{action} 执行中...")
            result.value = ""
            result.update()
            try:
                task = selected_task()
                if action == "校验任务":
                    output = await asyncio.to_thread(COORDINATOR.validate, task)
                elif action == "Dry Run":
                    output = await asyncio.to_thread(COORDINATOR.dry_run, task)
                else:
                    if dry_run.value:
                        output = await asyncio.to_thread(COORDINATOR.dry_run, task)
                    else:
                        output = await asyncio.to_thread(COORDINATOR.run, task, "real_run")
                show_output(output)
                ui.notify(f"{action}完成" if output.ok else f"{action}失败", type="positive" if output.ok else "negative")
            except Exception as exc:
                result.value = str(exc)
                result.update()
                ui.notify(f"任务异常: {exc}", type="negative")
            finally:
                status.set_text("")

        async def validate_click() -> None:
            await run_action("校验任务")

        async def dry_run_click() -> None:
            await run_action("Dry Run")

        async def real_run_click() -> None:
            await run_action("真实采集")

        with ui.row().classes("gap-2").style("margin-top:12px"):
            ui.button("校验任务", on_click=validate_click).style(BTN_G)
            ui.button("Dry Run", on_click=dry_run_click).style(BTN_G)
            ui.button("真实采集", on_click=real_run_click).style(BTN_P)
            ui.button("刷新页面", on_click=lambda: ui.navigate.reload()).style(BTN_G)
        ui.label("说明：勾选 Dry Run 保护时，“真实采集”按钮仍只做 Dry Run；取消勾选才会启动平台采集脚本。").style(
            "font-size:11px; color:#555; margin-top:8px"
        )


def _render_platform_capabilities() -> None:
    with ui.element("div").style(CARD):
        ui.label("平台能力矩阵").style("font-size:15px; font-weight:700; color:#fff; margin-bottom:12px")
        rows = []
        for capability in PLATFORM_CAPABILITIES.values():
            rows.append(
                {
                    "平台": capability.name,
                    "策略": " / ".join(capability.strategies),
                    "订单详情": "YES" if capability.supports_order_detail else "NO",
                    "图片": "YES" if capability.supports_review_images else "NO",
                    "人工门": "YES" if capability.human_gate_required else "NO",
                    "执行器": capability.executor,
                }
            )
        ui.table(
            columns=[
                {"name": "平台", "label": "平台", "field": "平台", "align": "left"},
                {"name": "策略", "label": "策略", "field": "策略", "align": "left"},
                {"name": "订单详情", "label": "订单详情", "field": "订单详情"},
                {"name": "图片", "label": "图片", "field": "图片"},
                {"name": "人工门", "label": "人工门", "field": "人工门"},
            ],
            rows=rows,
            row_key="平台",
        ).classes("w-full").props("dark dense flat")


def _render_store_registry(summary: dict[str, Any]) -> None:
    with ui.element("div").style(CARD):
        ui.label("门店注册表覆盖").style("font-size:15px; font-weight:700; color:#fff; margin-bottom:12px")
        rows = [{"平台": key, "URL 数": value} for key, value in sorted(summary["platform_url_counts"].items())]
        if not rows:
            ui.label("未生成 data/store_registry.json").style("font-size:13px; color:#777")
            return
        ui.table(
            columns=[
                {"name": "平台", "label": "平台", "field": "平台", "align": "left"},
                {"name": "URL 数", "label": "URL 数", "field": "URL 数"},
            ],
            rows=rows,
            row_key="平台",
        ).classes("w-full").props("dark dense flat")
        ui.label(f"来源：{REGISTRY_PATH}").style("font-size:11px; color:#555; margin-top:8px")


def _render_exports() -> None:
    with ui.element("div").style(CARD):
        ui.label("最近导出文件").style("font-size:15px; font-weight:700; color:#fff; margin-bottom:12px")
        files = _export_files()[:12]
        if not files:
            ui.label("暂无导出文件").style("font-size:13px; color:#777")
            return
        rows = [
            {
                "文件": path.name,
                "目录": str(path.parent.relative_to(ROOT)),
                "大小KB": round(path.stat().st_size / 1024, 1),
                "时间": path.stat().st_mtime,
            }
            for path in files
        ]
        ui.table(
            columns=[
                {"name": "文件", "label": "文件", "field": "文件", "align": "left"},
                {"name": "目录", "label": "目录", "field": "目录", "align": "left"},
                {"name": "大小KB", "label": "KB", "field": "大小KB"},
            ],
            rows=rows,
            row_key="文件",
        ).classes("w-full").props("dark dense flat")


def _render_task_activity() -> None:
    snapshot = COORDINATOR.snapshot()
    with ui.element("div").style(CARD):
        ui.label("任务活动与互斥状态").style("font-size:15px; font-weight:700; color:#fff; margin-bottom:12px")
        if snapshot["active"]:
            ui.table(
                columns=[
                    {"name": "run_id", "label": "Run ID", "field": "run_id", "align": "left"},
                    {"name": "key", "label": "互斥键", "field": "key", "align": "left"},
                    {"name": "action", "label": "动作", "field": "action"},
                    {"name": "started_at", "label": "开始时间", "field": "started_at"},
                ],
                rows=snapshot["active"],
                row_key="run_id",
            ).classes("w-full").props("dark dense flat")
        else:
            ui.label("当前没有活动采集任务。").style("font-size:13px; color:#777")

        history = snapshot["history"][:10]
        ui.label("最近任务").style("font-size:13px; color:#fff; font-weight:700; margin-top:14px")
        if not history:
            ui.label("暂无任务历史。").style("font-size:12px; color:#555")
            return
        ui.table(
            columns=[
                {"name": "run_id", "label": "Run ID", "field": "run_id", "align": "left"},
                {"name": "key", "label": "平台/账号", "field": "key", "align": "left"},
                {"name": "action", "label": "动作", "field": "action"},
                {"name": "ok", "label": "成功", "field": "ok"},
                {"name": "reviews", "label": "评论", "field": "reviews"},
                {"name": "finished_at", "label": "完成时间", "field": "finished_at"},
            ],
            rows=history,
            row_key="run_id",
        ).classes("w-full").props("dark dense flat")


def _load_registry_summary() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"store_count": 0, "platform_url_counts": {}}
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for store in data.get("stores", []):
        for platform, platform_data in (store.get("platforms") or {}).items():
            if platform_data.get("url"):
                counts[platform] = counts.get(platform, 0) + 1
    return {"store_count": int(data.get("store_count", 0)), "platform_url_counts": counts}


def _task_files() -> list[Path]:
    if not TASK_DIR.exists():
        return []
    return sorted(path for path in TASK_DIR.glob("*.json") if path.is_file())


def _export_files() -> list[Path]:
    if not EXPORT_DIR.exists():
        return []
    files = [
        path
        for path in EXPORT_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".csv", ".xlsx"}
    ]
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)
