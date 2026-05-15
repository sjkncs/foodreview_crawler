from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


Strategy = Literal["api", "dom", "visual", "ocr", "hybrid"]


@dataclass(frozen=True)
class PlatformCapability:
    name: str
    canonical_name: str
    executor: str
    strategies: tuple[Strategy, ...]
    supports_login: bool
    supports_store_registry: bool
    supports_time_filter: bool
    supports_order_detail: bool
    supports_review_images: bool
    supports_translation_source: bool
    read_only_detail: bool = True
    human_gate_required: bool = False
    denied_actions: tuple[str, ...] = (
        "reply",
        "save",
        "submit",
        "delete",
        "confirm",
        "payment",
    )
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PLATFORM_CAPABILITIES: dict[str, PlatformCapability] = {
    "hungry_panda": PlatformCapability(
        name="Hungry Panda",
        canonical_name="hungry_panda",
        executor="scripts/hungry_panda_weekly_reviews.py",
        strategies=("dom", "api", "hybrid"),
        supports_login=True,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=True,
        supports_review_images=True,
        supports_translation_source=False,
        notes="Use dataCenter/branch flow, then Orders -> Ratings and reviews; order detail is read-only.",
    ),
    "fantuan": PlatformCapability(
        name="Fantuan",
        canonical_name="fantuan",
        executor="platforms/fantuan/fantuan_weekly_reviews.py",
        strategies=("dom", "api", "hybrid"),
        supports_login=True,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=True,
        supports_review_images=True,
        supports_translation_source=False,
        notes="Customer review list plus order detail expansion in read-only mode.",
    ),
    "grabfood": PlatformCapability(
        name="GrabFood",
        canonical_name="grabfood",
        executor="platforms/grabfood/grabfood_weekly_reviews.py",
        strategies=("dom", "hybrid"),
        supports_login=True,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=True,
        supports_review_images=True,
        supports_translation_source=False,
        notes="Feedback/Ratings page collection only; no reply submission.",
    ),
    "google_maps": PlatformCapability(
        name="Google Maps",
        canonical_name="google_maps",
        executor="platforms/google_maps/google_maps_weekly_reviews.py",
        strategies=("dom", "visual", "hybrid"),
        supports_login=False,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=False,
        supports_review_images=True,
        supports_translation_source=True,
        notes="Public page extraction with expand text and translated text capture.",
    ),
    "keeta": PlatformCapability(
        name="KeeTa",
        canonical_name="keeta",
        executor="platforms/keeta/keeta_weekly_reviews.py",
        strategies=("dom", "hybrid"),
        supports_login=True,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=True,
        supports_review_images=True,
        supports_translation_source=False,
        human_gate_required=True,
        notes="Login/captcha is sensitive; manual gate allowed for session recovery.",
    ),
    "openrice": PlatformCapability(
        name="OpenRice",
        canonical_name="openrice",
        executor="platforms/openrice/openrice_public_reviews.py",
        strategies=("dom", "visual", "hybrid"),
        supports_login=False,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=False,
        supports_review_images=True,
        supports_translation_source=False,
        notes="Public review page; skip pinned reviews and collect by latest date.",
    ),
    "dianping": PlatformCapability(
        name="Dianping",
        canonical_name="dianping",
        executor="platforms/dianping/dianping_weekly_reviews.py",
        strategies=("dom", "visual", "hybrid"),
        supports_login=False,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=False,
        supports_review_images=True,
        supports_translation_source=False,
        notes="Public review pages with anti-crawl variance; focus on latest review list and evidence images.",
    ),
    "mfood": PlatformCapability(
        name="Mfood",
        canonical_name="mfood",
        executor="platforms/mfood/mfood_weekly_reviews.py",
        strategies=("dom", "hybrid"),
        supports_login=True,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=True,
        supports_review_images=True,
        supports_translation_source=False,
        human_gate_required=True,
        notes="Read-only order review collection with order detail modal extraction.",
    ),
    "aomi": PlatformCapability(
        name="Aomi",
        canonical_name="aomi",
        executor="platforms/aomi/aomi_weekly_reviews.py",
        strategies=("api", "dom", "hybrid"),
        supports_login=True,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=True,
        supports_review_images=True,
        supports_translation_source=False,
        human_gate_required=True,
        notes="API-first read-only review list and review detail capture; blocks reply/save/delete endpoints.",
    ),
    "uber_eats": PlatformCapability(
        name="Uber Eats",
        canonical_name="uber_eats",
        executor="platforms/uber_eats/uber_eats_weekly_reviews.py",
        strategies=("dom", "api", "hybrid"),
        supports_login=True,
        supports_store_registry=True,
        supports_time_filter=True,
        supports_order_detail=True,
        supports_review_images=True,
        supports_translation_source=False,
        human_gate_required=True,
        notes="Merchant Manager read-only extraction. Requires valid account session and may need manual gate for re-login.",
    ),
}


ALIASES = {
    "hungrypanda": "hungry_panda",
    "hungry-panda": "hungry_panda",
    "grab_food": "grabfood",
    "grab-food": "grabfood",
    "googlemaps": "google_maps",
    "google-maps": "google_maps",
    "dian_ping": "dianping",
    "dian-ping": "dianping",
    "open_rice": "openrice",
    "open-rice": "openrice",
    "ao_mi": "aomi",
    "ao-mi": "aomi",
    "uber": "uber_eats",
    "ubereats": "uber_eats",
    "uber-eats": "uber_eats",
}


def canonical_platform(name: str) -> str:
    key = name.lower().strip().replace(" ", "_")
    return ALIASES.get(key, key)


def get_capability(name: str) -> PlatformCapability | None:
    return PLATFORM_CAPABILITIES.get(canonical_platform(name))
