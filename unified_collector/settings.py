from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS_PATH = ROOT / "data" / "unified_settings.local.json"


DEFAULT_SETTINGS: dict[str, Any] = {
    "schema_version": 1,
    "api": {
        "active_provider": "deepseek",
        "mode": "single",
        "providers": {
            "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "model": "deepseek-reasoner", "api_key": ""},
            "qwen": {"label": "Qwen", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-turbo", "api_key": ""},
            "kimi": {"label": "Kimi / Moonshot", "base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-32k", "api_key": ""},
            "glm": {"label": "GLM / Zhipu", "base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-plus", "api_key": ""},
            "minimax": {"label": "MiniMax", "base_url": "https://api.minimax.chat/v1", "model": "abab6.5s-chat", "api_key": ""},
            "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1", "model": "gpt-4o", "api_key": ""},
            "grok": {"label": "Grok / xAI", "base_url": "https://api.x.ai/v1", "model": "grok-3", "api_key": ""},
            "claude": {"label": "Claude", "base_url": "https://api.anthropic.com/v1", "model": "claude-3-5-sonnet-latest", "api_key": ""},
            "gemini": {"label": "Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-1.5-pro", "api_key": ""},
            "nvidia": {"label": "NVIDIA NIM", "base_url": "https://integrate.api.nvidia.com/v1", "model": "meta/llama-3.1-70b-instruct", "api_key": ""},
            "longcat": {"label": "LongCat", "base_url": "https://api.longcat.chat/openai", "model": "LongCat-Flash-Thinking-2601", "api_key": "", "api_format": "openai"},
            "aigate_deepseek": {"label": "AIGate DeepSeek", "base_url": "https://llm.chudian.site/v1", "model": "deepseek-v4-pro", "api_key": "", "api_format": "openai"},
            "aigate_qwen": {"label": "AIGate Qwen", "base_url": "https://llm.chudian.site/v1", "model": "qwen3.6-plus", "api_key": "", "api_format": "openai"},
        },
        "temperature": 0.2,
        "max_tokens": 2000,
        "timeout_seconds": 60,
    },
    "appearance": {
        "theme": "light",
        "font_family": "Microsoft YaHei",
        "font_size": 13,
        "language": "en",
        "timezone": "Asia/Shanghai",
    },
    "processing": {
        "manual_gate_enabled": True,
        "manual_gate_threshold": 0.5,
        "conversation_preprocess": True,
        "auto_dialogue_role_split": True,
        "classification_prompt": "Analyze the review and identify product, service, delivery, safety, and quality issues. Return evidence-grounded labels only.",
        "batch_size": 10,
        "parallel_workers": 1,
        "api_interval_seconds": 0.1,
        "sync_interval_seconds": 3600,
        "checkpoint_resume": True,
        "checkpoint_path": "exports/runs",
        "autosave_interval_minutes": 5,
        "retry_count": 3,
        "retry_interval_seconds": 2,
        "max_collection_days": 30,
        "real_concurrency": 1,
        "dry_run_concurrency": 8,
    },
    "export": {
        "default_output_dir": "exports",
        "default_format": "xlsx",
        "append_timestamp": True,
        "include_raw_api": False,
        "include_analysis": True,
        "include_charts": True,
        "include_images": True,
        "normalized_jsonl": True,
    },
    "quality": {
        "min_field_completeness": 0.95,
        "min_detail_coverage": 0.9,
        "max_duplicate_rate": 0.01,
        "report_reward_weights": {
            "evidence": 0.25,
            "charts": 0.2,
            "sentiment": 0.2,
            "root_cause": 0.2,
            "actionability": 0.15,
        },
        "loss_weights": {
            "unsupported_claim": 0.35,
            "missing_evidence": 0.25,
            "missing_chart": 0.15,
            "weak_action": 0.15,
            "format_error": 0.1,
        },
    },
}


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_settings(path: str | Path = DEFAULT_SETTINGS_PATH, include_secrets: bool = False) -> dict[str, Any]:
    settings_path = Path(path)
    data = copy.deepcopy(DEFAULT_SETTINGS)
    if settings_path.exists():
        loaded = json.loads(settings_path.read_text(encoding="utf-8-sig"))
        if isinstance(loaded, dict):
            data = _deep_merge(data, loaded)
    providers = ((data.get("api") or {}).get("providers") or {})
    if isinstance(providers, dict):
        for provider_name, provider in list(providers.items()):
            if isinstance(provider, dict):
                providers[provider_name] = _normalize_provider_settings(provider)
    if include_secrets:
        return data
    safe = copy.deepcopy(data)
    for provider in safe.get("api", {}).get("providers", {}).values():
        key = str(provider.get("api_key", ""))
        provider["api_key_set"] = bool(key)
        provider["api_key_masked"] = mask_secret(key)
        provider["api_key"] = ""
    return safe


def save_settings(patch: dict[str, Any], path: str | Path = DEFAULT_SETTINGS_PATH) -> dict[str, Any]:
    settings_path = Path(path)
    current = load_settings(settings_path, include_secrets=True)
    providers_patch = ((patch.get("api") or {}).get("providers") or {}) if isinstance(patch.get("api"), dict) else {}
    for name, provider_patch in providers_patch.items():
        if isinstance(provider_patch, dict) and provider_patch.get("api_key", None) == "":
            provider_patch.pop("api_key", None)
            existing_key = current.get("api", {}).get("providers", {}).get(name, {}).get("api_key", "")
            if existing_key:
                current.setdefault("api", {}).setdefault("providers", {}).setdefault(name, {})["api_key"] = existing_key
    merged = _deep_merge(current, patch)
    providers = ((merged.get("api") or {}).get("providers") or {})
    if isinstance(providers, dict):
        for provider_name, provider in list(providers.items()):
            if isinstance(provider, dict):
                providers[provider_name] = _normalize_provider_settings(provider)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return load_settings(settings_path, include_secrets=False)


def reset_settings(path: str | Path = DEFAULT_SETTINGS_PATH) -> dict[str, Any]:
    settings_path = Path(path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(DEFAULT_SETTINGS, ensure_ascii=False, indent=2), encoding="utf-8")
    return load_settings(settings_path, include_secrets=False)


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return value[:1] + "***" + value[-1:]
    return value[:4] + "***" + value[-4:]


def _sanitize_base_url(value: Any) -> str:
    raw = str(value or "").strip().strip("'").strip('"')
    if not raw:
        return ""
    normalized = raw.replace("：", ":").replace("／", "/").replace("\\", "/")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", normalized):
        normalized = "https://" + normalized.lstrip("/")
    return normalized.rstrip("/")


def _normalize_provider_settings(provider: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(provider)
    normalized["base_url"] = _sanitize_base_url(normalized.get("base_url"))
    normalized["model"] = str(normalized.get("model") or "").strip()
    if "api_key" in normalized and isinstance(normalized.get("api_key"), str):
        normalized["api_key"] = normalized["api_key"].strip()
    api_format = str(normalized.get("api_format") or "").strip().lower()
    if api_format in {"openai", "anthropic"}:
        normalized["api_format"] = api_format
    elif "api_format" in normalized:
        normalized.pop("api_format", None)
    return normalized


def smoke_check_settings(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    data = settings or load_settings()
    processing = data.get("processing") or {}
    export = data.get("export") or {}
    api = data.get("api") or {}
    providers = api.get("providers") or {}
    active_provider = str(api.get("active_provider") or "")
    active_provider_data = providers.get(active_provider) or {}
    keyed_providers = [
        name for name, provider in providers.items()
        if provider.get("api_key_set") or provider.get("api_key")
    ]
    checks = [
        {
            "id": "real_concurrency",
            "severity": "high" if int(processing.get("real_concurrency", 1)) > 1 else "low",
            "ok": int(processing.get("real_concurrency", 1)) <= 1,
            "message": "Real browser collectors should default to single concurrency to avoid merchant session collision.",
        },
        {
            "id": "checkpoint_resume",
            "severity": "high",
            "ok": bool(processing.get("checkpoint_resume")),
            "message": "Checkpoint resume must stay enabled for long country/platform batches.",
        },
        {
            "id": "max_collection_days",
            "severity": "medium",
            "ok": 1 <= int(processing.get("max_collection_days", 30)) <= 30,
            "message": "Collection window must be capped at 30 days.",
        },
        {
            "id": "export_path",
            "severity": "medium",
            "ok": bool(export.get("default_output_dir")),
            "message": "Default export path must be configured.",
        },
        {
            "id": "model_provider",
            "severity": "medium",
            "ok": bool(providers),
            "message": "At least one model provider must be configured for translation and quality reports.",
        },
        {
            "id": "active_model_key",
            "severity": "medium",
            "ok": bool(active_provider_data.get("api_key_set") or active_provider_data.get("api_key")),
            "message": "The active model provider should have an API key before production translation or quality-report generation.",
        },
    ]
    return {
        "ok": all(item["ok"] or item["severity"] == "low" for item in checks),
        "checks": checks,
        "model_distribution": {
            "active_provider": active_provider,
            "provider_count": len(providers),
            "keyed_provider_count": len(keyed_providers),
            "keyed_providers": keyed_providers,
            "mode": api.get("mode", "single"),
        },
        "risk_counts": {
            "high": sum(1 for item in checks if item["severity"] == "high" and not item["ok"]),
            "medium": sum(1 for item in checks if item["severity"] == "medium" and not item["ok"]),
            "low": sum(1 for item in checks if item["severity"] == "low" and not item["ok"]),
        },
    }


def _provider_format(provider: dict[str, Any]) -> str:
    explicit = str(provider.get("api_format") or "").lower()
    if explicit in {"openai", "anthropic"}:
        return explicit
    base_url = _sanitize_base_url(provider.get("base_url")).lower()
    label = str(provider.get("label") or "").lower()
    if "anthropic" in base_url or "anthropic" in label or "claude" in label:
        return "anthropic"
    return "openai"


async def smoke_test_provider(provider_name: str | None = None, prompt: str = "只回复：OK", max_tokens: int = 8) -> dict[str, Any]:
    settings = load_settings(include_secrets=True)
    api = settings.get("api") or {}
    providers = api.get("providers") or {}
    name = provider_name or str(api.get("active_provider") or "")
    provider = providers.get(name)
    if not provider:
        return {"ok": False, "provider": name, "error": "provider_not_found"}
    api_key = str(provider.get("api_key") or "")
    if not api_key:
        return {"ok": False, "provider": name, "label": provider.get("label", name), "error": "api_key_missing"}
    base_url = _sanitize_base_url(provider.get("base_url"))
    model = str(provider.get("model") or "").strip()
    if not base_url:
        return {"ok": False, "provider": name, "label": provider.get("label", name), "error": "base_url_missing"}
    if not model:
        return {"ok": False, "provider": name, "label": provider.get("label", name), "error": "model_missing"}
    timeout = max(5, int(api.get("timeout_seconds") or 30))
    started = time.perf_counter()
    try:
        import httpx

        if _provider_format(provider) == "anthropic":
            url = f"{base_url}/messages" if base_url.endswith("/v1") else f"{base_url}/v1/messages"
            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            payload = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        else:
            url = f"{base_url}/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "content-type": "application/json"}
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "stream": False}

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            return {
                "ok": False,
                "provider": name,
                "label": provider.get("label", name),
                "model": model,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "error": response.text[:500],
            }
        body = response.json()
        if _provider_format(provider) == "anthropic":
            content_items = body.get("content") or []
            content = content_items[0].get("text", "") if content_items and isinstance(content_items[0], dict) else ""
        else:
            choice = (body.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            content = message.get("content") or message.get("reasoning_content") or ""
        return {
            "ok": bool(content),
            "provider": name,
            "label": provider.get("label", name),
            "model": model,
            "elapsed_ms": elapsed_ms,
            "response_chars": len(content),
            "response_preview": str(content)[:80],
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": name,
            "label": provider.get("label", name),
            "model": model,
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
            "error": str(exc)[:500],
        }


async def chat_with_configured_provider(
    prompt: str,
    max_tokens: int = 800,
    provider_name: str | None = None,
) -> str:
    settings = load_settings(include_secrets=True)
    api = settings.get("api") or {}
    providers = api.get("providers") or {}
    name = provider_name or str(api.get("active_provider") or "")
    provider = providers.get(name)
    if not provider:
        raise ValueError("provider_not_found")

    api_key = str(provider.get("api_key") or "").strip()
    if not api_key:
        raise ValueError("api_key_missing")

    base_url = _sanitize_base_url(provider.get("base_url"))
    model = str(provider.get("model") or "").strip()
    if not base_url:
        raise ValueError("base_url_missing")
    if not model:
        raise ValueError("model_missing")

    timeout = max(5, int(api.get("timeout_seconds") or 30))
    import httpx

    if _provider_format(provider) == "anthropic":
        url = f"{base_url}/messages" if base_url.endswith("/v1") else f"{base_url}/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    else:
        url = f"{base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "content-type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "stream": False}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code >= 400:
        raise ValueError(response.text[:500] or f"http_{response.status_code}")

    body = response.json()
    if _provider_format(provider) == "anthropic":
        content_items = body.get("content") or []
        content = content_items[0].get("text", "") if content_items and isinstance(content_items[0], dict) else ""
    else:
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or message.get("reasoning_content") or ""

    text = str(content or "").strip()
    if not text:
        raise ValueError("empty_response")
    return text
