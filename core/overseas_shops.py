"""
海外喜茶门店与平台目标解析。

用途：
1. 读取内置海外/港澳门店清单（Google Maps URL）
2. 合并 Excel 中已有的平台 ID（如美团 / 大众点评）
3. 按地区、JDE、门店关键字筛选，生成可直接爬取的平台目标列表
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import re
from typing import Iterable, Optional

from core.models import Platform
from excel_reader import read_shop_list


_BUILTIN_SHOPS_PATH = (
    Path(__file__).parent.parent
    / "review-collector-extension"
    / "python-server"
    / "builtin_shops.py"
)


@dataclass(frozen=True)
class ShopTarget:
    platform: Platform
    shop_id: str
    shop_name: str
    region: str
    store_code: str = ""
    address: str = ""
    source: str = ""
    platform_hint: str = ""
    platform_rating: str = ""
    platform_url: str = ""


@dataclass(frozen=True)
class ShopProfile:
    shop_name: str
    region: str
    store_code: str = ""
    address: str = ""
    openrice_hint: str = ""


@dataclass(frozen=True)
class PlatformManifest:
    platform_name: str
    shop_name: str
    region: str
    store_code: str = ""
    address: str = ""
    login_url: str = ""
    hint: str = ""
    rating: str = ""
    source: str = "excel_weekly_report"


_HUNGRY_PANDA_REGION_LOGIN_URLS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("美国", "usa", "united states", "new york", "california", "washington", "boston", "seattle", "sunnyvale", "san jose", "daly city", "bellevue"), "https://merchant-usa.hungrypanda.co/master/login"),
    (("加拿大", "canada", "vancouver", "burnaby", "richmond", "toronto"), "https://merchant-ca.hungrypanda.co/master/login"),
    (("英国", "uk", "united kingdom", "london", "glasgow", "manchester", "canary wharf", "oxford"), "https://merchant-uk.hungrypanda.co/master/login"),
    (("澳大利亚", "australia", "sydney", "melbourne", "burwood", "box hill", "clayton", "nsw", "victoria", "adelaide"), "https://merchant-aus.hungrypanda.co/master/login"),
    (("新西兰", "new zealand", "auckland"), "https://merchant-nzd.hungrypanda.co/master/login"),
    (("韩国", "korea", "seoul", "hongdae", "gangnam", "myeong", "konkuk"), "https://merchant-kr.hungrypanda.co/master/login"),
    (("日本", "japan", "tokyo", "osaka"), "https://merchant-jp.hungrypanda.co/master/login"),
    (("新加坡", "singapore"), "https://merchant-sg.hungrypanda.co/master/login"),
    (("欧洲", "europe", "france", "germany", "italy", "spain", "paris"), "https://merchant-eur.hungrypanda.co/master/login"),
)


def _normalize_name(name: str) -> str:
    return re.sub(r"[\s()（）·\-.]", "", name or "").lower()


def _normalize_region(region: str) -> str:
    return (region or "").strip().replace("中国", "")


def _infer_hungry_panda_login_url(shop: dict) -> str:
    explicit = str(shop.get("hungry_panda_url") or "").strip()
    if explicit.startswith("http"):
        return explicit
    haystacks = [
        str(shop.get("region") or ""),
        str(shop.get("province") or ""),
        str(shop.get("city") or ""),
        str(shop.get("sub_zone") or ""),
        str(shop.get("address") or ""),
        str(shop.get("hungry_panda_note") or ""),
    ]
    combined = " ".join(part.lower() for part in haystacks if part)
    for tokens, login_url in _HUNGRY_PANDA_REGION_LOGIN_URLS:
        if any(token.lower() in combined for token in tokens):
            return login_url
    return ""


def _load_builtin_shops() -> list[dict]:
    if not _BUILTIN_SHOPS_PATH.exists():
        return []
    spec = importlib.util.spec_from_file_location("builtin_shops", _BUILTIN_SHOPS_PATH)
    if not spec or not spec.loader:
        return []
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(getattr(module, "BUILTIN_SHOPS", []))


def _matches_text(value: str, keywords: Iterable[str]) -> bool:
    normalized = _normalize_name(value)
    return any(_normalize_name(keyword) in normalized for keyword in keywords if keyword)


def similarity_score(left: str, right: str) -> float:
    left_set = set(_normalize_name(left))
    right_set = set(_normalize_name(right))
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def load_overseas_shop_profiles(
    *,
    region: Optional[str] = None,
    shop_keywords: Optional[Iterable[str]] = None,
    store_codes: Optional[Iterable[str]] = None,
) -> list[ShopProfile]:
    keyword_list = [keyword.strip() for keyword in (shop_keywords or []) if keyword and keyword.strip()]
    code_set = {str(code).strip() for code in (store_codes or []) if str(code).strip()}
    region_text = _normalize_region(region or "")

    profiles: dict[str, ShopProfile] = {}

    def add_profile(
        *,
        shop_name: str,
        shop_region: str,
        store_code: str = "",
        address: str = "",
        openrice_hint: str = "",
    ) -> None:
        effective_region = _normalize_region(shop_region)
        if region_text and region_text not in effective_region:
            return
        if code_set and store_code not in code_set:
            return
        if keyword_list and not _matches_text(shop_name, keyword_list):
            return
        dedupe_key = store_code or _normalize_name(shop_name)
        candidate = ShopProfile(
            shop_name=shop_name,
            region=effective_region,
            store_code=store_code,
            address=address,
            openrice_hint=openrice_hint,
        )
        existing = profiles.get(dedupe_key)
        if not existing:
            profiles[dedupe_key] = candidate
            return
        if candidate.openrice_hint and not existing.openrice_hint:
            profiles[dedupe_key] = candidate
            return
        if candidate.address and not existing.address:
            profiles[dedupe_key] = candidate

    try:
        excel_shops = read_shop_list(region_filter=region if region else None)
    except Exception:
        excel_shops = []

    for shop in excel_shops:
        add_profile(
            shop_name=str(shop.get("shop_name", "")).strip(),
            shop_region=str(shop.get("region", "")).strip(),
            store_code=str(shop.get("store_code", "")).strip(),
            address=str(shop.get("address", "")).strip(),
            openrice_hint=str(shop.get("openrice_note", "")).strip(),
        )

    for shop in _load_builtin_shops():
        add_profile(
            shop_name=str(shop.get("name", "")).strip(),
            shop_region=str(shop.get("region", "")).strip(),
            store_code=str(shop.get("jde", "")).strip(),
        )
    return sorted(profiles.values(), key=lambda item: (item.region, item.shop_name))


def load_overseas_shop_targets(
    *,
    region: Optional[str] = None,
    shop_keywords: Optional[Iterable[str]] = None,
    store_codes: Optional[Iterable[str]] = None,
    platforms: Optional[Iterable[Platform]] = None,
) -> list[ShopTarget]:
    """
    返回海外门店的平台目标列表。

    优先级：
    - 内置门店清单：提供 Google Maps 目标
    - Excel 门店清单：补充 美团 / 大众点评 等平台 ID
    """
    requested_platforms = set(platforms or [])
    keyword_list = [keyword.strip() for keyword in (shop_keywords or []) if keyword and keyword.strip()]
    code_set = {str(code).strip() for code in (store_codes or []) if str(code).strip()}
    region_text = _normalize_region(region or "")

    metadata_by_code: dict[str, dict] = {}
    metadata_by_name: dict[str, dict] = {}
    targets: list[ShopTarget] = []
    seen: set[tuple[str, str]] = set()

    builtin_shops = _load_builtin_shops()
    for shop in builtin_shops:
        name = str(shop.get("name", "")).strip()
        code = str(shop.get("jde", "")).strip()
        shop_region = _normalize_region(str(shop.get("region", "")).strip())
        google_url = str(shop.get("googleUrl", "")).strip()
        meta = {
            "shop_name": name,
            "region": shop_region,
            "store_code": code,
            "address": "",
        }
        if code:
            metadata_by_code[code] = meta
        if name:
            metadata_by_name[_normalize_name(name)] = meta
        if google_url:
            targets.append(
                ShopTarget(
                    platform=Platform.GOOGLE_MAPS,
                    shop_id=google_url,
                    shop_name=name,
                    region=shop_region,
                    store_code=code,
                    source="builtin_google_maps",
                )
            )

    try:
        excel_shops = read_shop_list(region_filter=region if region else None)
    except Exception:
        excel_shops = []

    for shop in excel_shops:
        name = str(shop.get("shop_name", "")).strip()
        code = str(shop.get("store_code", "")).strip()
        region_value = _normalize_region(str(shop.get("region", "")).strip())
        address = str(shop.get("address", "")).strip()
        meta = {
            "shop_name": name,
            "region": region_value,
            "store_code": code,
            "address": address,
            "google_maps_url": str(shop.get("google_maps_url", "")).strip(),
            "openrice_hint": str(shop.get("openrice_note", "")).strip(),
            "keeta_hint": str(shop.get("keeta_note", "")).strip(),
        }
        if code and code not in metadata_by_code:
            metadata_by_code[code] = meta
        if name:
            metadata_by_name.setdefault(_normalize_name(name), meta)

        platform_ids = {
            Platform.GOOGLE_MAPS: str(shop.get("google_maps_url") or "").strip(),
            Platform.MEITUAN: str(shop.get("meituan_id") or shop.get("meituan_poi_id") or "").strip(),
            Platform.DIANPING: str(shop.get("dianping_url") or shop.get("dianping_id") or "").strip(),
        }
        for platform, shop_id in platform_ids.items():
            if not shop_id:
                continue
            platform_hint = ""
            platform_rating = ""
            if platform == Platform.GOOGLE_MAPS:
                platform_rating = str(shop.get("google_maps_rating") or "").strip()
            elif platform == Platform.DIANPING:
                platform_rating = str(shop.get("dianping_rating") or "").strip()
            targets.append(
                ShopTarget(
                    platform=platform,
                    shop_id=shop_id,
                    shop_name=name,
                    region=region_value,
                    store_code=code,
                    address=address,
                    source="excel_shop_list",
                    platform_hint=platform_hint,
                    platform_rating=platform_rating,
                )
            )
        keeta_hint = str(shop.get("keeta_note") or "").strip()
        keeta_rating = str(shop.get("keeta_rating") or "").strip()
        if keeta_hint or keeta_rating:
            targets.append(
                ShopTarget(
                    platform=Platform.KEETA,
                    shop_id=code or name,
                    shop_name=name,
                    region=region_value,
                    store_code=code,
                    address=address,
                    source="excel_keeta_hint",
                    platform_hint=keeta_hint,
                    platform_rating=keeta_rating,
                )
            )
        hungry_panda_hint = str(shop.get("hungry_panda_note") or "").strip()
        hungry_panda_rating = str(shop.get("hungry_panda_rating") or "").strip()
        hungry_panda_url = _infer_hungry_panda_login_url(shop)
        if hungry_panda_hint or hungry_panda_rating or hungry_panda_url:
            targets.append(
                ShopTarget(
                    platform=Platform.HUNGRY_PANDA,
                    shop_id=code or name,
                    shop_name=name,
                    region=region_value,
                    store_code=code,
                    address=address,
                    source="excel_hungry_panda",
                    platform_hint=hungry_panda_hint,
                    platform_rating=hungry_panda_rating,
                    platform_url=hungry_panda_url,
                )
            )

    source_priority = {
        "excel_shop_list": 3,
        "excel_hungry_panda": 3,
        "openrice_discovery": 3,
        "builtin_google_maps": 1,
        "": 0,
    }
    selected: dict[tuple[str, str], ShopTarget] = {}
    for target in targets:
        meta = metadata_by_code.get(target.store_code) or metadata_by_name.get(_normalize_name(target.shop_name))
        effective = target
        if meta:
            effective = ShopTarget(
                platform=target.platform,
                shop_id=target.shop_id,
                shop_name=meta.get("shop_name") or target.shop_name,
                region=meta.get("region") or target.region,
                store_code=meta.get("store_code") or target.store_code,
                address=meta.get("address") or target.address,
                source=target.source,
                platform_hint=target.platform_hint,
                platform_rating=target.platform_rating,
                platform_url=target.platform_url,
            )

        if requested_platforms and effective.platform not in requested_platforms:
            continue
        if region_text and region_text not in _normalize_region(effective.region):
            continue
        if code_set and effective.store_code not in code_set:
            continue
        if keyword_list and not _matches_text(effective.shop_name, keyword_list):
            continue

        dedupe_key = (effective.platform.value, effective.store_code or _normalize_name(effective.shop_name))
        existing = selected.get(dedupe_key)
        if not existing:
            selected[dedupe_key] = effective
            continue
        if source_priority.get(effective.source, 0) >= source_priority.get(existing.source, 0):
            selected[dedupe_key] = effective

    return sorted(selected.values(), key=lambda item: (item.region, item.shop_name, item.platform.value))


def load_platform_manifests(
    *,
    region: Optional[str] = None,
    shop_keywords: Optional[Iterable[str]] = None,
    store_codes: Optional[Iterable[str]] = None,
    platform_names: Optional[Iterable[str]] = None,
) -> list[PlatformManifest]:
    requested = {name.strip().lower() for name in (platform_names or []) if name and name.strip()}
    keyword_list = [keyword.strip() for keyword in (shop_keywords or []) if keyword and keyword.strip()]
    code_set = {str(code).strip() for code in (store_codes or []) if str(code).strip()}
    region_text = _normalize_region(region or "")

    field_map = {
        "hungry panda": ("hungry_panda_url", "hungry_panda_note", "hungry_panda_rating"),
        "uber eats": ("uber_eats_url", "uber_eats_note", "uber_eats_rating"),
        "fantuan": ("fantuan_url", "fantuan_note", "fantuan_rating"),
        "grabfood": ("grabfood_url", "grabfood_note", "grabfood_rating"),
        "foodpanda": ("foodpanda_url", "foodpanda_note", "foodpanda_rating"),
        "mfood": ("mfood_url", "mfood_note", "mfood_rating"),
        "澳觅": ("aomi_url", "aomi_note", "aomi_rating"),
        "baedal minjok": ("baedal_minjok_url", "baedal_minjok_note", "baedal_minjok_rating"),
        "keeta": ("keeta_url", "keeta_note", "keeta_rating"),
        "openrice": ("openrice_url", "openrice_note", "openrice_rating"),
    }

    manifests: list[PlatformManifest] = []
    for shop in read_shop_list(region_filter=region if region else None):
        shop_name = str(shop.get("shop_name", "")).strip()
        shop_region = _normalize_region(str(shop.get("region", "")).strip())
        shop_province = _normalize_region(str(shop.get("province", "")).strip())
        shop_city = _normalize_region(str(shop.get("city", "")).strip())
        shop_sub_zone = _normalize_region(str(shop.get("sub_zone", "")).strip())
        store_code = str(shop.get("store_code", "")).strip()
        address = str(shop.get("address", "")).strip()

        if region_text and all(region_text not in value for value in (shop_region, shop_province, shop_city, shop_sub_zone)):
            continue
        if code_set and store_code not in code_set:
            continue
        if keyword_list and not _matches_text(shop_name, keyword_list):
            continue

        for platform_name, (url_field, note_field, rating_field) in field_map.items():
            if requested and platform_name not in requested:
                continue
            login_url = str(shop.get(url_field) or "").strip()
            hint = str(shop.get(note_field) or "").strip()
            rating = str(shop.get(rating_field) or "").strip()
            if not login_url and not hint and not rating:
                continue
            manifests.append(
                PlatformManifest(
                    platform_name=platform_name.title() if platform_name.isascii() else platform_name,
                    shop_name=shop_name,
                    region=shop_region,
                    store_code=store_code,
                    address=address,
                    login_url=login_url,
                    hint=hint,
                    rating=rating,
                )
            )
    return manifests
