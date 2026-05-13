"""
AI 客户端工厂 v4
多 Agent 架构：
  文字任务（情感/翻译/关键词/回复）→ qwen3-235b-a22b-thinking-2507
  OCR/Vision 任务                  → qwen3-vl-plus

两套 SDK 自动适配：
  OpenAI 兼容端点（iflow 等）→ openai.AsyncOpenAI
  Anthropic 官方端点          → anthropic.AsyncAnthropic

Thinking 模型特殊处理：
  返回的 content 可能在 choices[0].message.content（普通）
  或 choices[0].message.reasoning_content（思考过程）
  优先取 content，content 为空时取 reasoning_content
"""
from __future__ import annotations
import logging
import os
from typing import Optional

import config as cfg_module

logger = logging.getLogger(__name__)

# OCR/Vision 专用模型（固定不受全局 model 影响）
OCR_MODEL = "qwen3-vl-plus"


def _is_openai_compat(base_url: str) -> bool:
    """判断是否为 OpenAI 兼容端点"""
    anthropic_hosts = ("api.anthropic.com",)
    return not any(h in base_url for h in anthropic_hosts)


def _load_params(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[str, str, str]:
    cfg = cfg_module.load()
    _key = api_key or cfg.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
    _url = base_url or cfg.get("anthropic_base_url", "http://apis.iflow.cn/v1")
    _model = model or cfg.get("model", "qwen3-235b-a22b-thinking-2507")
    if not _key:
        raise ValueError("未配置 API Key，请在⚙️设置页面填写")
    return _key, _url, _model


def _extract_content(resp_obj) -> str:
    """
    从 OpenAI 响应中提取文字内容。
    Thinking 模型特殊处理：
      - 普通模式：choices[0].message.content
      - thinking 模式：choices[0].message.reasoning_content（content 为空时）
    """
    choices = resp_obj.choices or []
    if not choices:
        return ""
    msg = choices[0].message
    # 优先取 content（非 thinking 文字）
    content = getattr(msg, "content", None)
    if content:
        return content.strip()
    # thinking 模型回退：取思考内容
    reasoning = getattr(msg, "reasoning_content", None)
    if reasoning:
        return reasoning.strip()
    return ""


# ──────────────────────── 文字对话接口 ────────────────────────────

async def chat(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 512,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    统一文字对话接口。
    默认使用 qwen3-235b-a22b-thinking-2507。
    """
    _key, _url, _model = _load_params(api_key, base_url, model)
    if _is_openai_compat(_url):
        return await _openai_chat(_key, _url, _model, prompt, system, max_tokens)
    return await _anthropic_chat(_key, _url, _model, prompt, system, max_tokens)


async def _openai_chat(
    api_key: str, base_url: str, model: str,
    prompt: str, system: Optional[str], max_tokens: int,
) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    # thinking 模型关闭内置思考，只取回答部分（更快更省 token）
    extra_kwargs: dict = {}
    if "thinking" in model:
        extra_kwargs["extra_body"] = {"enable_thinking": False}

    resp = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
        **extra_kwargs,
    )
    return _extract_content(resp)


async def _anthropic_chat(
    api_key: str, base_url: str, model: str,
    prompt: str, system: Optional[str], max_tokens: int,
) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    msg = await client.messages.create(**kwargs)
    return msg.content[0].text.strip()


# ──────────────────────── Vision / OCR 专用接口 ───────────────────

async def vision_chat(
    image_b64: str,
    prompt: str,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Vision 多模态接口（截图 OCR 专用）。
    固定使用 qwen3-vl-plus，config 中 ocr_model 可覆盖。
    """
    cfg = cfg_module.load()
    _key = api_key or cfg.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
    _url = base_url or cfg.get("anthropic_base_url", "http://apis.iflow.cn/v1")
    # OCR 模型优先级：参数 > config.ocr_model > 固定默认值
    _model = model or cfg.get("ocr_model", OCR_MODEL)

    if not _key:
        raise ValueError("未配置 API Key")

    logger.debug("vision_chat: model=%s url=%s", _model, _url)

    if _is_openai_compat(_url):
        return await _openai_vision(_key, _url, _model, image_b64, prompt, max_tokens)
    return await _anthropic_vision(_key, _url, _model, image_b64, prompt, max_tokens)


async def _openai_vision(
    api_key: str, base_url: str, model: str,
    image_b64: str, prompt: str, max_tokens: int,
) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    resp = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return _extract_content(resp)


async def _anthropic_vision(
    api_key: str, base_url: str, model: str,
    image_b64: str, prompt: str, max_tokens: int,
) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
    msg = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return msg.content[0].text.strip()
