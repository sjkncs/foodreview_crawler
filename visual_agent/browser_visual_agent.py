from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPORTS = ROOT / "exports" / "visual_agent"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from processors.ai_client import vision_chat


SAFE_DENY_PATTERNS = (
    r"\bsubmit\b",
    r"\bsend\b",
    r"\bsave\b",
    r"\bpublish\b",
    r"\breply\b",
    r"\bdelete\b",
    r"\bremove\b",
    r"\bconfirm\b",
    r"\b支付\b",
    r"\b提交\b",
    r"\b发送\b",
    r"\b保存\b",
    r"\b回复\b",
    r"\b删除\b",
    r"\b确认\b",
)


@dataclass
class VisualTask:
    name: str
    start_url: str
    goal: str
    profile_name: str = "visual_agent"
    max_steps: int = 20
    headless: bool = False
    allowed_domains: list[str] = field(default_factory=list)
    deny_actions: list[str] = field(default_factory=lambda: list(SAFE_DENY_PATTERNS))
    extraction_schema: dict[str, Any] = field(default_factory=dict)


def load_task(path: Path) -> VisualTask:
    data = json.loads(path.read_text(encoding="utf-8"))
    return VisualTask(
        name=data["name"],
        start_url=data["start_url"],
        goal=data["goal"],
        profile_name=data.get("profile_name", "visual_agent"),
        max_steps=int(data.get("max_steps", 20)),
        headless=bool(data.get("headless", False)),
        allowed_domains=list(data.get("allowed_domains", [])),
        deny_actions=list(data.get("deny_actions", SAFE_DENY_PATTERNS)),
        extraction_schema=dict(data.get("extraction_schema", {})),
    )


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def is_denied(action: dict[str, Any], patterns: list[str]) -> tuple[bool, str]:
    action_text = json.dumps(action, ensure_ascii=False)
    for pattern in patterns:
        if re.search(pattern, action_text, flags=re.I):
            return True, pattern
    return False, ""


async def screenshot_b64(page) -> str:
    raw = await page.screenshot(full_page=False, type="png")
    return base64.b64encode(raw).decode("ascii")


def build_prompt(task: VisualTask, step: int, history: list[dict[str, Any]]) -> str:
    schema_text = json.dumps(task.extraction_schema, ensure_ascii=False, indent=2) if task.extraction_schema else "{}"
    history_tail = json.dumps(history[-6:], ensure_ascii=False, indent=2)
    deny_text = "\n".join(f"- {item}" for item in task.deny_actions)
    return f"""
你是一个只通过截图操作网页的视觉浏览器 Agent。你不能修改商户后台数据。

任务名称：{task.name}
目标：{task.goal}
当前步数：{step}/{task.max_steps}

硬性安全规则：
1. 允许：导航、点击菜单/筛选/日期/分页、滚动、打开详情弹窗、读取页面。
2. 禁止：提交、保存、发送、回复客户、删除、确认付款、修改任何配置。
3. 如果目标按钮可能触发提交/回复/保存，必须返回 action="stop"。
4. 只返回 JSON，不要解释。

禁止动作关键词/正则：
{deny_text}

需要抽取的数据 schema：
{schema_text}

最近动作历史：
{history_tail}

请根据截图决定下一步。返回以下 JSON 之一：

点击：
{{"action":"click","x":123,"y":456,"reason":"点击左侧 Feedback 菜单"}}

输入：
{{"action":"type","text":"要输入的文本","reason":"输入搜索关键词"}}

按键：
{{"action":"key","key":"Enter","reason":"确认搜索"}}

滚动：
{{"action":"scroll","dx":0,"dy":700,"reason":"向下查看更多评论"}}

等待：
{{"action":"wait","ms":2000,"reason":"等待页面加载"}}

抽取结构化数据：
{{"action":"extract","records":[{{"字段":"值"}}],"reason":"当前页评论已读完"}}

完成：
{{"action":"done","reason":"任务完成"}}

停止：
{{"action":"stop","reason":"需要人工处理或存在修改数据风险"}}
""".strip()


async def run_action(page, action: dict[str, Any]) -> None:
    kind = str(action.get("action", "")).lower()
    if kind == "click":
        await page.mouse.click(float(action["x"]), float(action["y"]))
    elif kind == "type":
        await page.keyboard.type(str(action.get("text", "")), delay=20)
    elif kind == "key":
        await page.keyboard.press(str(action.get("key", "Enter")))
    elif kind == "scroll":
        await page.mouse.wheel(float(action.get("dx", 0)), float(action.get("dy", 600)))
    elif kind == "wait":
        await page.wait_for_timeout(int(action.get("ms", 1500)))
    else:
        raise ValueError(f"Unsupported action: {kind}")
    await page.wait_for_timeout(800)


async def run_task(task: VisualTask) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    profile_dir = DATA / "browser_profiles" / task.profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    EXPORTS.mkdir(parents=True, exist_ok=True)

    history: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    stopped_reason = ""

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            str(profile_dir),
            channel="msedge",
            headless=task.headless,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(task.start_url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(3_000)

        for step in range(1, task.max_steps + 1):
            image = await screenshot_b64(page)
            prompt = build_prompt(task, step, history)
            raw = await vision_chat(image, prompt, max_tokens=2048)
            try:
                action = extract_json(raw)
            except Exception as exc:
                action = {
                    "action": "stop",
                    "reason": f"model_output_not_json: {exc}",
                    "raw_preview": raw[:500],
                }
            denied, pattern = is_denied(action, task.deny_actions)
            action_log = {
                "step": step,
                "url": page.url,
                "action": action,
                "model_raw": raw,
                "denied": denied,
                "denied_pattern": pattern,
            }
            history.append(action_log)

            if denied:
                stopped_reason = f"Denied by safety rule: {pattern}"
                break

            kind = str(action.get("action", "")).lower()
            if kind == "extract":
                batch = action.get("records") or []
                if isinstance(batch, list):
                    records.extend(item for item in batch if isinstance(item, dict))
                continue
            if kind == "done":
                stopped_reason = str(action.get("reason") or "done")
                break
            if kind == "stop":
                stopped_reason = str(action.get("reason") or "stopped")
                break
            await run_action(page, action)

        await context.close()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": task.__dict__,
        "record_count": len(records),
        "records": records,
        "stopped_reason": stopped_reason,
        "history": history,
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = EXPORTS / f"{task.name}_{stamp}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["output_path"] = str(output)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vision-only browser agent PoC")
    parser.add_argument("task", type=Path, help="JSON task file")
    parser.add_argument("--headless", action="store_true", help="Override task to run headless")
    parser.add_argument("--max-steps", type=int, default=0, help="Override max steps")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    task = load_task(args.task)
    if args.headless:
        task.headless = True
    if args.max_steps:
        task.max_steps = args.max_steps
    result = await run_task(task)
    print(
        json.dumps(
            {
                "output": result["output_path"],
                "record_count": result["record_count"],
                "stopped_reason": result["stopped_reason"],
                "steps": len(result["history"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
