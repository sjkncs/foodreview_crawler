"""
关键词提取处理器 v2 - 使用统一 ai_client
优先 AI API，降级 jieba 分词
"""
from __future__ import annotations
import logging
import re

from core.models import Review
from .ai_client import chat

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都",
    "一", "上", "也", "很", "到", "说", "要", "去", "你", "会",
    "着", "没有", "看", "好", "自己", "这", "那", "还", "但",
    "外卖", "点", "买", "来", "次", "个", "下单", "一个",
}


def _jieba_keywords(content: str, top_k: int = 8) -> tuple[str, ...]:
    try:
        import jieba.analyse
        tags = jieba.analyse.extract_tags(content, topK=top_k, withWeight=False)
        return tuple(t for t in tags if t not in _STOPWORDS and len(t) > 1)
    except ImportError:
        words = re.findall(r'[\u4e00-\u9fa5]{2,5}', content)
        freq: dict[str, int] = {}
        for w in words:
            if w not in _STOPWORDS:
                freq[w] = freq.get(w, 0) + 1
        return tuple(sorted(freq, key=lambda x: freq[x], reverse=True)[:top_k])


async def extract_keywords(review: Review, top_k: int = 8) -> Review:
    """关键词提取：AI 优先，降级 jieba。返回新实例。"""
    try:
        prompt = f"""从以下外卖评论提取最多{top_k}个关键标签（如：配送慢、份量足、味道好），
只返回 JSON 数组，不要说明：["标签1","标签2",...]

评论：{review.content[:400]}"""
        raw = await chat(prompt, max_tokens=120)
        m = re.search(r'\[.*?\]', raw, re.DOTALL)
        if m:
            import json
            keywords = tuple(json.loads(m.group()))
            return review.with_keywords(keywords)
    except Exception as exc:
        logger.warning("AI 关键词提取失败，降级 jieba: %s", exc)

    return review.with_keywords(_jieba_keywords(review.content, top_k))
