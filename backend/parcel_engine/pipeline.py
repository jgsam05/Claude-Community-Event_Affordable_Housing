"""ZIP -> scored GeoJSON FeatureCollection."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

import geopandas as gpd
import numpy as np
import pandas as pd

from . import geometry, joins, registry, scoring, selection, validation
from .config import OUT_CRS, SCORING_VERSION
from .sources import Sources, make_sources

SCORED = registry.DATA_DIR / "scored"

PROPERTIES = [
    "apn", "address", "zip", "jurisdiction", "straddles_city_line",
    "opp", "development_potential", "feasibility_risk", "level", "sig", "signals_total",
    "opp_reason", "dev_reason", "risk_reason", "reasons", "missing", "low_confidence_inputs", "confidence_cap",
    "pathways", "pathways_unchecked", "risk_unchecked", "evidence", "opp_raw",
    "lot_sqft", "lot_acres", "frontage_ft", "frontage_method", "buildable_sqft", "building_sqft",
    "building_coverage", "coverage_source", "vacant", "year_built", "land_use_code",
    "he_site", "he_rezone", "he_status", "sb35_status", "public_surplus", "sla_notice", "state_owned",
    "faith_based", "tax_defaulted", "in_hqta", "dist_bus_stop_ft", "dist_rail_ft", "tract_geoid", "tract_jobs",
    "dist_school_ft", "dist_grocery_ft", "tcac_category", "median_hh_income", "rent_burden_share",
    "ces_percentile", "in_oz", "flood_sfha", "fhsz_lra", "fhsz_sra", "liquefaction", "fault_zone",
    "coastal_zone", "dist_oil_well_ft", "dist_envirostor_ft", "dist_geotracker_ft", "nrhp",
    "dist_mhp_ft", "dist_lihtc_ft", "dist_s8_ft",
]


def _clean(v):
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if v is None or v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return None if math.isnan(v) else float(v)
    return v


def build_zip(zip_code: str, src: Sources | None = None, write: bool = True) -> dict:
    src = src or make_sources()
    parcels, meta, zcta = selection.select_parcels(zip_code, src)
    area = zcta.to_crs(4326).geometry.iloc[0]
    parcels = geometry.add_geometry_signals(parcels, src, area, zip_code)
    parcels, avail = joins.join_all(parcels, src, area, zip_code)
    scored = scoring.score(parcels, avail)
    scored = gpd.GeoDataFrame(scored.drop(columns="geometry", errors="ignore"),
                              geometry=parcels.geometry.values, crs=parcels.crs)
    out = scored.to_crs(OUT_CRS)
    out = out.sort_values("opp", ascending=False, na_position="last").reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    out.loc[out["opp"].isna(), "rank"] = None

    features = []
    for _, r in out.iterrows():
        props = {k: _clean(r.get(k)) for k in ["rank"] + PROPERTIES}
        features.append({"type": "Feature", "id": props["apn"],
                         "geometry": json.loads(json.dumps(r.geometry.__geo_interface__)), "properties": props})

    counts = out["level"].value_counts().reindex(["High", "Medium", "Low", "Insufficient"], fill_value=0).to_dict()
    used = sorted(k for k, v in src.status.items() if v == "loaded")
    recs = {r["id"]: r for r in registry.records()}
    fc = {
        "type": "FeatureCollection",
        "metadata": {
            **meta, "mode": src.mode, "scoring_version": SCORING_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "signals": scoring.SIGNALS, "confidence_rules": {"High": "9-10", "Medium": "7-8", "Low": "5-6", "Insufficient": "0-4"},
            "level_counts": {k: int(v) for k, v in counts.items()},
            "scored_count": int(out["opp"].notna().sum()),
            "datasets": {k: {"status": v, "ingest_date": recs.get(k, {}).get("ingest_date")}
                         for k, v in sorted(src.status.items())},
            "datasets_used": used,
            "data_as_of": min([recs[k]["ingest_date"] for k in used if recs.get(k, {}).get("ingest_date")] or [None]),
            "validation": validation.validate(out, validation.load_a2()) if src.mode == "live" else
            {"status": "not_run", "reason": "fixture mode"},
            "disclaimer": "Screening tool, not a feasibility study. Zoning is not included.",
        },
        "features": features,
    }
    if src.mode == "fixture":
        fc["metadata"]["data_as_of"] = "synthetic fixture"
    if write and src.mode == "live":
        SCORED.mkdir(parents=True, exist_ok=True)
        (SCORED / f"{zip_code}.geojson").write_text(json.dumps(fc))
    return fc
