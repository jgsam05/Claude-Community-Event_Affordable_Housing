"""Build data/processed/parcels.json.

    python -m oc_housing.build                      # synthetic demo data
    python -m oc_housing.build --parcels FILE.geojson   # your real parcel export

Pipeline: parcels -> spatial join to OC jurisdictions -> configured overlays
(zoning polygons, hazards, ...) -> processed file. Scoring happens at API load
time so changing config/scoring.yaml never requires re-running this.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path

from .etl.boundaries import JurisdictionIndex, fetch_boundaries
from .etl.overlays import apply_configured_overlays
from .etl.parcels import load_mapping, load_parcels
from .etl.sample import assign_sample_zoning, generate
from .zoning.base import load_adapters

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "parcels.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parcels", type=Path, help="GeoJSON parcel export (EPSG:4326)")
    ap.add_argument("--mapping", type=Path, help="column mapping yaml")
    ap.add_argument("--refresh-boundaries", action="store_true")
    ap.add_argument("--profile", default="", choices=["", "real"], help="real = data/zoning_real + parcels_real.json")
    args = ap.parse_args(argv)

    bounds = fetch_boundaries(ROOT / "data" / "raw" / "oc_city_boundaries.geojson",
                              force=args.refresh_boundaries)
    index = JurisdictionIndex(bounds)
    adapters = load_adapters(ROOT / "data" / ("zoning_real" if args.profile == "real" else "zoning"))

    meta: dict = {"generated": dt.datetime.now(dt.timezone.utc).isoformat()}
    if args.parcels:
        parcels, rep = load_parcels(args.parcels, load_mapping(args.mapping))
        meta.update(source=str(args.parcels), synthetic=False, load_report=rep)
    else:
        parcels = generate()
        meta.update(source="synthetic demo generator", synthetic=True)

    matched = index.assign(parcels)
    meta["jurisdiction_join"] = {"matched": matched, "unmatched": len(parcels) - matched}

    meta["overlay_report"] = apply_configured_overlays(
        parcels, ROOT, "overlays_real.yaml" if args.profile == "real" else "overlays.yaml")
    if meta["synthetic"]:
        meta["sample_zoning_assigned"] = assign_sample_zoning(parcels, adapters)

    out = OUT.with_name("parcels_real.json") if args.profile == "real" else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"meta": meta, "parcels": [p.model_dump() for p in parcels]}))

    by_zip = Counter(p.zip_code for p in parcels)
    by_city = Counter(p.city or "(outside OC boundary layer)" for p in parcels)
    print(f"Wrote {len(parcels)} parcels -> {out}")
    print("By ZIP: ", dict(by_zip))
    print("By city:", dict(by_city))
    print("Cities with zoning adapters:", sorted(adapters) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
