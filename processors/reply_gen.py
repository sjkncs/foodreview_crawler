"""
自动回复生成处理器 v2 - 使用统一 ai_client
"""
from __future__ import annotations
import logging

from core.models import Review, SentimentLabel
from .ai_client import chat

logger = logging.getLogger(__name__)

_TEMPLATES = {
    SentimentLabel.POSITIVE: "感谢您的好评！您的认可是我们最大的动力，期待您的再次光临！😊",
    SentimentLabel.NEGATIVE: (
        "非常抱歉给您带来了不好的体验！我们已记录您的问题并将认真改进，"
        "如需进一步处理请联系我们客服，感谢您的反馈！"
    ),
    SentimentLabel.NEUTRAL: (
        "感谢您的评价！我们会继续努力提升服务质量，期待下次为您带来更好的体验！"
    ),
}


async def generate_reply(review: Review) -> Review:
    """生成建议回复，返回新 Review 实例。"""
    try:
        sentiment_str = review.sentiment.value if review.sentiment else "中性"
        prompt = (
            f"你是{review.shop_name}的客服专员，正在回复一条"
            f"{review.platform.value}上的{sentiment_str}评论。\n"
            f"请生成一条专业、真诚、简洁的回复（50字以内），不要格式标记。\n\n"
            f"顾客评论：{review.content[:300]}\n"
            f"评分：{review.rating}星"
        )
        reply = await chat(prompt, max_tokens=150)
        return review.with_reply(reply)
    except Exception as exc:
        logger.warning("AI 回复生成失败，使用模板: %s", exc)

    sentiment = review.sentiment or SentimentLabel.NEUTRAL
    return review.with_reply(_TEMPLATES[sentiment])
