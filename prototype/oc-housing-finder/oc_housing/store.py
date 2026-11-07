"""In-memory store: loads processed parcels, scores them, indexes by ZIP.

Scoring runs at load time, so editing config/scoring.yaml or config/laws.yaml
and restarting (or POST /api/reload) re-scores everything without re-running ETL.
"""

from __future__ import annotations

import os

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from .etl.boundaries import JurisdictionIndex, load_jurisdiction_config
from .schema import Parcel, ParcelScore
from .scoring import ROOT, load_yaml, score_parcel
from .zoning.base import ZoningAdapter, load_adapters


class Store:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self.meta: dict = {}
        self.parcels: dict[str, Parcel] = {}
        self.scores: dict[str, ParcelScore] = {}
        self.by_zip: dict[str, list[str]] = defaultdict(list)
        self.adapters: dict[str, ZoningAdapter] = {}
        self.cities_in_layer: list[str] = []
        self.laws_verified = False
        self.load()

    def load(self) -> None:
        self.parcels, self.scores = {}, {}
        self.by_zip = defaultdict(list)
        scoring_cfg = load_yaml("scoring.yaml")
        laws_cfg = load_yaml("laws.yaml")
        self.laws_verified = bool(laws_cfg.get("verified"))
        self.profile = os.environ.get("OC_PROFILE", "")
        self.adapters = load_adapters(self.root / "data" / ("zoning_real" if self.profile == "real" else "zoning"))

        bpath = self.root / "data" / "raw" / "oc_city_boundaries.geojson"
        if bpath.exists():
            idx = JurisdictionIndex(json.loads(bpath.read_text()), load_jurisdiction_config())
            self.cities_in_layer = idx.cities
        else:
            self.cities_in_layer = []

        path = self.root / "data" / "processed" / ("parcels_real.json" if self.profile == "real" else "parcels.json")
        if not path.exists():
            self.meta = {"error": "No processed data. Run: python -m oc_housing.build"}
            return
        blob = json.loads(path.read_text())
        self.meta = blob["meta"]
        for raw in blob["parcels"]:
            p = Parcel(**raw)
            self.parcels[p.parcel_id] = p
            self.scores[p.parcel_id] = score_parcel(p, self.adapters, scoring_cfg, laws_cfg)
            self.by_zip[p.zip_code].append(p.parcel_id)

    # ---- queries ------------------------------------------------------
    def zips(self) -> list[dict]:
        out = []
        for z, ids in sorted(self.by_zip.items()):
            cities = Counter(self.parcels[i].city or "(unmatched)" for i in ids)
            out.append({"zip": z, "parcels": len(ids), "cities": dict(cities)})
        return out

    def query(
        self, zip_code: str, *, min_score: float = 0.0, city: Optional[str] = None,
        land_use: Optional[str] = None, min_lot: float = 0.0,
        result_type: Optional[str] = None, max_risk: float = 100.0,
        min_confidence: float = 0.0,
    ) -> list[tuple[Parcel, ParcelScore]]:
        rows = []
        for pid in self.by_zip.get(zip_code, []):
            p, s = self.parcels[pid], self.scores[pid]
            if s.overall < min_score or s.risk > max_risk or s.confidence < min_confidence:
                continue
            if city and p.city != city:
                continue
            if land_use and p.land_use != land_use:
                continue
            if min_lot and (p.lot_sqft or 0) < min_lot:
                continue
            if result_type and s.result_type != result_type:
                continue
            rows.append((p, s))
        rows.sort(key=lambda r: r[1].overall, reverse=True)
        return rows

    def zoning_coverage(self) -> list[dict]:
        """Per jurisdiction: is zoning ingested, and are the values samples?"""
        names = list(self.cities_in_layer) + ["Unincorporated Orange County"]
        out = []
        for name in names:
            a = self.adapters.get(name)
            out.append({
                "jurisdiction": name,
                "zoning": "none" if a is None else ("sample" if a.is_sample else "ingested"),
                "zone_codes": 0 if a is None else len(a.rules()),
            })
        return out

    def gap_report(self, zip_code: str) -> dict:
        ids = self.by_zip.get(zip_code, [])
        by_city: dict[str, Counter] = defaultdict(Counter)
        unknown_fields: Counter = Counter()
        for pid in ids:
            p, s = self.parcels[pid], self.scores[pid]
            by_city[p.city or "(unmatched)"][s.zoning_status] += 1
            for g in s.data_gaps:
                if g.endswith(": unknown"):
                    unknown_fields[g.removesuffix(": unknown")] += 1
        return {
            "zip": zip_code,
            "parcels": len(ids),
            "zoning_status_by_jurisdiction": {c: dict(v) for c, v in by_city.items()},
            "unknown_field_counts": dict(unknown_fields.most_common()),
        }
