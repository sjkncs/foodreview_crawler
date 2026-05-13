from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "store_registry.json"


@dataclass(frozen=True)
class StoreLocator:
    jde: str
    store_name: str
    country: str
    country_code: str
    city: str
    source_row: int
    platform: str = ""
    url: str = ""
    meta: str = ""
    note: str = ""
    account_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "jde": self.jde,
            "store_name": self.store_name,
            "country": self.country,
            "country_code": self.country_code,
            "city": self.city,
            "source_row": self.source_row,
            "platform": self.platform,
            "url": self.url,
            "meta": self.meta,
            "note": self.note,
            "account_ref": self.account_ref,
        }


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"store registry not found: {registry_path}")
    return json.loads(registry_path.read_text(encoding="utf-8"))


def _match_store_selector(store: dict[str, Any], selector: str) -> bool:
    query = selector.strip().lower()
    if not query:
        return True
    fields = [
        str(store.get("jde", "")),
        str(store.get("store_name", "")),
        str(store.get("country", "")),
        str(store.get("city", "")),
    ]
    return any(query in field.lower() for field in fields)


def _store_selectors(stores: str | list[str]) -> list[str]:
    if stores == "all" or stores == ["all"]:
        return []
    if isinstance(stores, str):
        return [stores]
    return [str(item) for item in stores]


def resolve_stores(
    *,
    platform: str = "",
    country: str = "",
    stores: str | list[str] = "all",
    registry_path: str | Path = DEFAULT_REGISTRY,
    require_url: bool = False,
) -> list[StoreLocator]:
    registry = load_registry(registry_path)
    selectors = _store_selectors(stores)
    platform_key = platform.lower().replace("-", "_").replace(" ", "_")
    country_query = country.strip().lower()
    matches: list[StoreLocator] = []
    for store in registry.get("stores", []):
        if country_query and country_query not in f"{store.get('country', '')} {store.get('country_code', '')} {store.get('city', '')}".lower():
            continue
        if selectors and not any(_match_store_selector(store, selector) for selector in selectors):
            continue
        platform_data = (store.get("platforms") or {}).get(platform_key, {}) if platform_key else {}
        if require_url and not platform_data.get("url"):
            continue
        matches.append(
            StoreLocator(
                jde=str(store.get("jde", "")),
                store_name=str(store.get("store_name", "")),
                country=str(store.get("country", "")),
                country_code=str(store.get("country_code", "")),
                city=str(store.get("city", "")),
                source_row=int(store.get("source_row", 0) or 0),
                platform=platform_key,
                url=str(platform_data.get("url", "")),
                meta=str(platform_data.get("meta", "")),
                note=str(platform_data.get("note", "")),
                account_ref=str(platform_data.get("account_ref", "")),
            )
        )
    return matches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Locate stores from unified registry")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--platform", default="")
    parser.add_argument("--country", default="")
    parser.add_argument("--store", action="append", default=[])
    parser.add_argument("--require-url", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stores = resolve_stores(
        platform=args.platform,
        country=args.country,
        stores=args.store or "all",
        registry_path=args.registry,
        require_url=args.require_url,
    )
    payload = {
        "count": len(stores),
        "stores": [store.to_dict() for store in stores],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
