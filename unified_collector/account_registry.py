from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACCOUNT_REGISTRY = ROOT / "data" / "account_registry.local.json"


@dataclass(frozen=True)
class AccountRecord:
    account_ref: str
    platform: str
    account_key: str
    username: str
    password: str
    portal_url: str = ""
    country_codes: tuple[str, ...] = ()
    phone_code: str = ""

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "account_ref": self.account_ref,
            "platform": self.platform,
            "account_key": self.account_key,
            "portal_url": self.portal_url,
            "country_codes": list(self.country_codes),
            "phone_code": self.phone_code,
        }


def load_account_registry(path: str | Path = DEFAULT_ACCOUNT_REGISTRY) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {"schema_version": 1, "accounts": {}}
    text = file_path.read_text(encoding="utf-8-sig")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        return {"schema_version": 1, "accounts": {}}
    return payload


def _normalize_country(value: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    aliases = {
        "united_states": "usa",
        "us": "usa",
        "united_kingdom": "uk",
        "gb": "uk",
        "korea": "kr",
        "south_korea": "kr",
        "australia": "au",
        "canada": "ca",
        "singapore": "sg",
    }
    return aliases.get(text, text)


def _build_record(account_ref: str, data: dict[str, Any]) -> AccountRecord:
    country_codes = tuple(str(item).strip().lower() for item in (data.get("country_codes") or []) if str(item).strip())
    return AccountRecord(
        account_ref=account_ref,
        platform=str(data.get("platform", "")).strip(),
        account_key=str(data.get("account_key", "")).strip(),
        username=str(data.get("username", "")).strip(),
        password=str(data.get("password", "")).strip(),
        portal_url=str(data.get("portal_url", "")).strip(),
        country_codes=country_codes,
        phone_code=str(data.get("phone_code", "")).strip(),
    )


def resolve_account(
    *,
    platform: str,
    account_ref: str = "",
    country_code: str = "",
    account_key: str = "",
    registry_path: str | Path = DEFAULT_ACCOUNT_REGISTRY,
) -> AccountRecord | None:
    payload = load_account_registry(registry_path)
    accounts = payload.get("accounts")
    if not isinstance(accounts, dict):
        return None

    if account_ref and account_ref in accounts and isinstance(accounts[account_ref], dict):
        return _build_record(account_ref, accounts[account_ref])

    normalized_platform = str(platform or "").strip().lower()
    normalized_country = _normalize_country(country_code)
    normalized_key = str(account_key or "").strip().lower()

    candidates: list[AccountRecord] = []
    for ref, raw in accounts.items():
        if not isinstance(raw, dict):
            continue
        record = _build_record(str(ref), raw)
        if record.platform.lower() != normalized_platform:
            continue
        candidates.append(record)

    if not candidates:
        return None

    if normalized_key:
        for item in candidates:
            if item.account_key.lower() == normalized_key:
                return item

    if normalized_country:
        for item in candidates:
            if normalized_country in item.country_codes:
                return item

    # fallback: exact default first, otherwise first candidate
    for item in candidates:
        if item.account_key.lower() in {"default", "main"}:
            return item
    return candidates[0]
