"""
决策块：AI 介入的关键节点判断
包括：验证码检测、登录墙检测、异常页面识别
"""
from __future__ import annotations
import base64
import json
import logging
import re
from typing import Optional

from .base_block import BaseBlock, BlockResult

logger = logging.getLogger(__name__)


class DeciderBlock(BaseBlock):
    """
    AI 决策块：截图 → VLM 分析当前页面状态 → 决定下一步行动
    关键节点：每次执行前调用，判断是否需要人工介入
    """
    name = "Decider"
    timeout_s = 20.0

    async def execute(self, ctx: dict) -> BlockResult:
        page = ctx.get("page")
        if not page:
            return BlockResult.fail("ctx 中缺少 page 对象")

        try:
            screenshot = await page.screenshot(type="png")
            b64 = base64.standard_b64encode(screenshot).decode()
            decision = await self._ask_vlm(b64)
            return self._handle_decision(decision, ctx)
        except Exception as exc:
            logger.warning("[Decider] VLM 判断失败，假设页面正常: %s", exc)
            return BlockResult.success("normal", "VLM不可用，跳过检测")

    async def _ask_vlm(self, b64: str) -> dict:
        from processors.ai_client import vision_chat
        prompt = """分析当前页面截图，判断页面状态：

返回 JSON（严格格式）：
{
  "status": "normal | captcha | login | blocked | error | empty",
  "confidence": 0.0到1.0,
  "action": "continue | pause | skip | retry",
  "reason": "原因说明"
}

状态说明：
- normal: 页面正常，可以继续操作
- captcha: 出现验证码（滑动/图片/短信）
- login: 出现登录弹窗或被重定向到登录页
- blocked: 被限流或IP封禁（出现"访问频繁"等提示）
- error: 页面错误（404/500/加载失败）
- empty: 页面空白或无评论内容"""

        raw = await vision_chat(b64, prompt, max_tokens=300)
        m = re.search(r'\{[\s\S]*?\}', raw)
        if m:
            return json.loads(m.group())
        return {"status": "normal", "confidence": 0.5, "action": "continue", "reason": "解析失败"}

    def _handle_decision(self, decision: dict, ctx: dict) -> BlockResult:
        status = decision.get("status", "normal")
        action = decision.get("action", "continue")
        reason = decision.get("reason", "")
        conf   = decision.get("confidence", 1.0)

        ctx["page_status"] = status
        logger.info("[Decider] 页面状态: %s (置信度:%.2f) → 动作: %s", status, conf, action)

        if status == "normal":
            return BlockResult.success(status, "页面正常")
        if status in ("captcha", "login"):
            return BlockResult.pause(f"需要人工处理: {status} - {reason}")
        if status == "blocked":
            return BlockResult.fail(f"被限流/封禁: {reason}")
        if status == "error":
            return BlockResult.fail(f"页面错误: {reason}")
        if status == "empty":
            return BlockResult.skip(f"页面无内容: {reason}")
        return BlockResult.success(status, reason)


class HumanGateBlock(BaseBlock):
    """
    人机协同门：暂停并等待人工操作完成。
    适用场景：登录、验证码、二维码扫描等。

    在 NiceGUI Web 界面中：弹出提示，用户点击"已完成"按钮后继续。
    在 CLI 模式中：打印提示，等待用户按 Enter 键。
    """
    name = "HumanGate"
    timeout_s = 300.0   # 最多等待5分钟

    def __init__(self, prompt_msg: str = "请完成人工操作后按 Enter 继续"):
        self.prompt_msg = prompt_msg

    async def execute(self, ctx: dict) -> BlockResult:
        import asyncio

        mode = ctx.get("ui_mode", "cli")  # "cli" 或 "gui"
        logger.info("[HumanGate] ⏸ %s", self.prompt_msg)

        if mode == "gui":
            # GUI 模式：设置标志，等待前端确认
            ctx["human_gate_waiting"] = True
            ctx["human_gate_message"] = self.prompt_msg
            for _ in range(int(self.timeout_s)):
                if ctx.get("human_gate_done"):
                    ctx["human_gate_waiting"] = False
                    ctx["human_gate_done"] = False
                    return BlockResult.success(None, "人工操作已完成")
                await asyncio.sleep(1)
            return BlockResult.fail("人工等待超时")
        else:
            # CLI 模式：阻塞等待 Enter
            import sys
            print(f"\n⏸  [{self.name}] {self.prompt_msg}")
            print("   完成后请按 Enter 键继续...", end="", flush=True)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, sys.stdin.readline)
            return BlockResult.success(None, "人工操作已完成")
