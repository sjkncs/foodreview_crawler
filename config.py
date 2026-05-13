"""
配置管理 v3 - 多 Agent API 支持
  - iflow_new:  http://apis.iflow.cn/v1  (当前可用✅)
                文字: qwen3-235b-a22b-thinking-2507
                OCR:  qwen3-vl-plus
  - anthropic:  https://api.anthropic.com
  - custom:     用户自定义
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent / "config.json"

# ── 内置 API 端点预设 ─────────────────────────────────────────────
API_PRESETS: dict[str, dict[str, str]] = {
    "iflow_new": {
        "label":      "iflow 多Agent（当前可用✅）",
        "api_key":    "",
        "base_url":   "http://apis.iflow.cn/v1",
        "model":      "qwen3-235b-a22b-thinking-2507",
        "ocr_model":  "qwen3-vl-plus",
        "note":       "OpenAI 兼容，文字+OCR双模型",
    },
    "iflow_old": {
        "label":      "iflow 旧Key（已过期）",
        "api_key":    "",
        "base_url":   "http://apis.iflow.cn/v1",
        "model":      "deepseek-v3",
        "ocr_model":  "qwen3-vl-plus",
        "note":       "Key已过期，请切换到 iflow_new",
    },
    "anthropic": {
        "label":      "Anthropic 官方",
        "api_key":    "",
        "base_url":   "https://api.anthropic.com",
        "model":      "claude-sonnet-4-6",
        "ocr_model":  "claude-sonnet-4-6",
        "note":       "官方 API，需自备 Key",
    },
    "custom": {
        "label":      "自定义",
        "api_key":    "",
        "base_url":   "",
        "model":      "",
        "ocr_model":  "",
        "note":       "手动填写",
    },
}

_DEFAULTS: dict[str, Any] = {
    # API 配置
    "api_preset":         "iflow_new",
    "anthropic_api_key":  API_PRESETS["iflow_new"]["api_key"],
    "anthropic_base_url": API_PRESETS["iflow_new"]["base_url"],
    "model":              API_PRESETS["iflow_new"]["model"],
    "ocr_model":          API_PRESETS["iflow_new"]["ocr_model"],

    # 爬虫配置
    "headless":           True,
    "proxy":              "",
    "max_pages":          10,
    "ocr_strategy":       "hybrid",

    # 处理配置
    "auto_analyze":       True,
    "auto_reply":         False,
    "auto_translate":     True,
    "translate_lang":     "zh",
    "language":           "zh",
}


def load() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open(encoding="utf-8") as f:
                data = json.load(f)
            return {**_DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def save(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def get(key: str, default: Any = None) -> Any:
    return load().get(key, default)


def switch_api_preset(preset_key: str, custom_key: str = "", custom_url: str = "") -> None:
    """切换 API 端点预设（Claude Code Switch）"""
    cfg = load()
    if preset_key == "custom":
        cfg.update({
            "api_preset":         "custom",
            "anthropic_api_key":  custom_key,
            "anthropic_base_url": custom_url,
        })
    elif preset_key in API_PRESETS:
        preset = API_PRESETS[preset_key]
        cfg.update({
            "api_preset":         preset_key,
            "anthropic_base_url": preset["base_url"],
        })
        if preset["api_key"]:
            cfg["anthropic_api_key"] = preset["api_key"]
        if preset.get("model"):
            cfg["model"] = preset["model"]
        if preset.get("ocr_model"):
            cfg["ocr_model"] = preset["ocr_model"]
    save(cfg)


def get_active_api_info() -> dict[str, str]:
    """返回当前激活的 API 配置摘要"""
    cfg = load()
    preset = cfg.get("api_preset", "custom")
    return {
        "preset":    preset,
        "label":     API_PRESETS.get(preset, {}).get("label", "自定义"),
        "base_url":  cfg.get("anthropic_base_url", ""),
        "api_key":   (cfg.get("anthropic_api_key") or "")[:8] + "****",
        "model":     cfg.get("model", ""),
        "ocr_model": cfg.get("ocr_model", "qwen3-vl-plus"),
    }
