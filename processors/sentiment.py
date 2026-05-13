"""
情感分析处理器 v2 - 使用统一 ai_client
优先 AI API，降级到本地规则引擎
"""
from __future__ import annotations
import logging
import re
from typing import Optional

from core.models import Review, SentimentLabel
from .ai_client import chat

logger = logging.getLogger(__name__)

# ── 本地规则字典（API 不可用时降级）───────────────────────────────
_POSITIVE = {
    "好吃", "美味", "新鲜", "满意", "推荐", "棒", "赞", "不错", "超级", "好评",
    "喜欢", "香", "实惠", "速度快", "准时", "热乎", "份量足", "物超所值",
    "服务好", "打包好", "包装好", "干净", "卫生", "超赞", "完美", "正宗",
}
_NEGATIVE = {
    "难吃", "差", "冷", "凉", "慢", "超时", "少菜", "缺菜", "漏单", "不新鲜",
    "油腻", "咸", "淡", "硬", "臭", "变质", "投诉", "退款", "差评", "失望",
    "脏", "不卫生", "头发", "异物", "蟑螂", "态度差", "骗人", "恶心",
}


def _local_sentiment(content: str) -> tuple[SentimentLabel, float]:
    pos = sum(1 for w in _POSITIVE if w in content)
    neg = sum(1 for w in _NEGATIVE if w in content)
    if pos == 0 and neg == 0:
        return SentimentLabel.NEUTRAL, 0.0
    score = (pos - neg) / (pos + neg)
    if score > 0.15:
        return SentimentLabel.POSITIVE, score
    if score < -0.15:
        return SentimentLabel.NEGATIVE, score
    return SentimentLabel.NEUTRAL, score


async def analyze_sentiment(review: Review) -> Review:
    """情感分析：AI 优先，降级本地规则。返回新实例。"""
    try:
        prompt = f"""分析以下外卖评论的情感倾向，只返回 JSON 格式，不要任何说明：
{{"label": "正面|负面|中性", "score": 0到1之间的浮点数}}

评论：{review.content[:500]}"""
        raw = await chat(prompt, max_tokens=80)
        m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if m:
            import json
            data = json.loads(m.group())
            label_map = {
                "正面": SentimentLabel.POSITIVE,
                "负面": SentimentLabel.NEGATIVE,
                "中性": SentimentLabel.NEUTRAL,
            }
            label = label_map.get(data.get("label", "中性"), SentimentLabel.NEUTRAL)
            score_raw = max(0.0, min(1.0, float(data.get("score", 0.5))))  # 裁剪到 [0,1]
            score = score_raw if label == SentimentLabel.POSITIVE else (
                -score_raw if label == SentimentLabel.NEGATIVE else 0.0
            )
            return review.with_sentiment(label, score)
    except Exception as exc:
        logger.warning("AI 情感分析失败，降级本地规则: %s", exc)

    label, score = _local_sentiment(review.content)
    return review.with_sentiment(label, score)
