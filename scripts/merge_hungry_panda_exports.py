from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
FIELDS = [
    "Platform",
    "Country",
    "Region",
    "City",
    "Branch ID",
    "Branch",
    "Review",
    "Review contents",
    "Image URLs",
    "Order ID",
    "Review time",
    "Operation",
    "Child ratings",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge Hungry Panda segmented review exports")
    parser.add_argument("--region", default="", help="Optional region code, e.g. ca/uk/au/kr/usa")
    parser.add_argument("--prefix", default="", help="Optional source filename prefix, e.g. seg_")
    parser.add_argument("--output-prefix", default="", help="Optional merged output filename prefix")
    parser.add_argument("--exports-dir", default=str(EXPORTS), help="Exports directory")
    return parser.parse_args()


def find_exports(exports_dir: Path, region: str, prefix: str) -> list[Path]:
    pattern = re.compile(r"hungry_panda_(?P<region>[a-z0-9]+)_weekly_reviews_\d{8}_\d{6}\.json$")
    files: list[Path] = []
    for path in exports_dir.glob("*.json"):
        match = pattern.search(path.name)
        if not match:
            continue
        if region and match.group("region") != region:
            continue
        if prefix and not path.name.startswith(prefix):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.stat().st_mtime)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def merge_payloads(paths: list[Path]) -> dict[str, Any]:
    reviews: list[dict[str, Any]] = []
    branches: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen_orders: set[str] = set()
    regions: set[str] = set()
    countries: set[str] = set()

    for path in paths:
        payload = load_payload(path)
        if payload.get("region"):
            regions.add(payload["region"])
        if payload.get("country"):
            countries.add(payload["country"])
        branches.extend(payload.get("branches", []))
        errors.extend(payload.get("errors", []))
        for row in payload.get("reviews", []):
            key = row.get("Order ID") or json.dumps(row, ensure_ascii=False, sort_keys=True)
            if key in seen_orders:
                continue
            seen_orders.add(key)
            reviews.append(row)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_files": [str(path) for path in paths],
        "regions": sorted(regions),
        "countries": sorted(countries),
        "branch_count": len(branches),
        "review_count": len(reviews),
        "branches": branches,
        "reviews": reviews,
        "errors": errors,
    }


def write_outputs(exports_dir: Path, output_prefix: str, payload: dict[str, Any]) -> tuple[Path, Path]:
    exports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{output_prefix}_" if output_prefix else ""
    region_part = "_".join(payload["regions"]) if payload["regions"] else "all"
    json_path = exports_dir / f"{prefix}hungry_panda_{region_part}_weekly_reviews_merged_{stamp}.json"
    csv_path = exports_dir / f"{prefix}hungry_panda_{region_part}_weekly_reviews_merged_{stamp}.csv"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in payload["reviews"]:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    return json_path, csv_path


def main() -> None:
    args = parse_args()
    exports_dir = Path(args.exports_dir)
    paths = find_exports(exports_dir, args.region, args.prefix)
    if not paths:
        raise SystemExit(f"No Hungry Panda exports found in {exports_dir}")

    payload = merge_payloads(paths)
    json_path, csv_path = write_outputs(exports_dir, args.output_prefix, payload)
    print(
        json.dumps(
            {
                "json": str(json_path),
                "csv": str(csv_path),
                "source_count": len(paths),
                "branch_count": payload["branch_count"],
                "review_count": payload["review_count"],
                "errors": payload["errors"][:5],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
