"""
翻译处理器 v2 - 使用统一 ai_client
将非中文评论/商家回复翻译为中文
"""
from __future__ import annotations
import logging
import re
from typing import Optional

from core.models import Review
from .ai_client import chat

logger = logging.getLogger(__name__)


def needs_translation(text: str) -> bool:
    """判断文本是否需要翻译（中文字符比例 < 30%）"""
    if not text or len(text.strip()) < 3:
        return False
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese / max(len(text), 1) < 0.3


async def translate_review(review: Review) -> Review:
    """
    翻译评论内容和商家回复。
    只在判断为非中文时翻译，返回新 Review 实例。
    """
    content_tr: Optional[str] = None
    reply_tr: Optional[str] = None

    need_content = needs_translation(review.content)
    need_reply = bool(review.merchant_reply and needs_translation(review.merchant_reply))

    if not need_content and not need_reply:
        return review  # 已是中文，跳过

    try:
        # 批量翻译（一次 API 调用）
        import json
        items: dict[str, str] = {}
        if need_content:
            items["content"] = review.content[:600]
        if need_reply and review.merchant_reply:
            items["reply"] = review.merchant_reply[:300]

        prompt = f"""请将以下 JSON 中的文本翻译成中文，保持 JSON 格式和 key 不变，只翻译 value：
{json.dumps(items, ensure_ascii=False)}
只返回 JSON，不要其他说明。"""

        raw = await chat(prompt, max_tokens=800)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            result = json.loads(m.group())
            content_tr = result.get("content")
            reply_tr = result.get("reply")

    except Exception as exc:
        logger.warning("翻译失败，跳过: %s", exc)
        return review

    # 只在翻译实际有内容时才写入，避免空字符串覆盖原有数据
    if not content_tr and not reply_tr:
        return review

    return review.with_translation(
        content_tr=content_tr or "",
        reply_tr=reply_tr,
    )
