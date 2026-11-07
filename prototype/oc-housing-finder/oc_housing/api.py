"""FastAPI app. Run:  uvicorn oc_housing.api:app --reload"""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .schema import Parcel, ParcelScore
from .store import Store

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="OC Affordable Housing Opportunity Finder", version="0.1.0")
store = Store()

ZIP_RE = re.compile(r"^\d{5}$")
DISCLAIMER = ("Screening-level results only. Not legal, zoning, or investment advice; "
              "verify with the city and a qualified professional.")


def _feature(p: Parcel, s: ParcelScore) -> dict:
    return {
        "type": "Feature",
        "id": p.parcel_id,
        "geometry": p.geometry,
        "properties": {
            "parcel_id": p.parcel_id, "address": p.address, "zip": p.zip_code,
            "city": p.city, "community": p.community,
            "land_use": p.land_use, "lot_sqft": p.lot_sqft,
            "zoning_code": p.zoning_code, "owner_type": p.owner_type,
            "overall": s.overall, "potential": s.potential, "risk": s.risk,
            "confidence": s.confidence, "risk_confidence": s.risk_confidence,
            "best_units": s.units.best_units, "best_pathway": s.units.best_pathway,
            "base_units": s.units.base_units,
            "land_cost_per_unit": s.land_cost_per_unit, "price_basis": s.price_basis,
            "zoning_status": s.zoning_status, "result_type": s.result_type,
            "is_synthetic": p.is_synthetic, "reason": s.reason,
        },
    }


def _validated_zip(zip_code: str) -> str:
    if not ZIP_RE.match(zip_code):
        raise HTTPException(400, "ZIP must be exactly 5 digits.")
    if zip_code not in store.by_zip:
        loaded = sorted(store.by_zip)
        raise HTTPException(404, {
            "message": f"No parcel data is loaded for ZIP {zip_code}. This is either "
                       "not an Orange County ZIP or its parcels have not been ingested yet.",
            "loaded_zips": loaded,
        })
    return zip_code


def _filtered(zip_code, min_score, city, land_use, min_lot, result_type, max_risk,
              min_confidence):
    return store.query(
        _validated_zip(zip_code), min_score=min_score, city=city, land_use=land_use,
        min_lot=min_lot, result_type=result_type, max_risk=max_risk,
        min_confidence=min_confidence)


FILTERS = dict(
    min_score=Query(0.0, ge=0, le=100), city=Query(None), land_use=Query(None),
    min_lot=Query(0.0, ge=0), result_type=Query(None), max_risk=Query(100.0, ge=0, le=100),
    min_confidence=Query(0.0, ge=0, le=1))


@app.get("/api/health")
def health():
    return {
        "status": "ok" if "error" not in store.meta else "no_data",
        "parcels": len(store.parcels),
        "zips": len(store.by_zip),
        "synthetic_data": bool(store.meta.get("synthetic")),
        "laws_verified": store.laws_verified,
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/meta")
def meta():
    return {**store.meta, "zoning_coverage": store.zoning_coverage(),
            "laws_verified": store.laws_verified, "disclaimer": DISCLAIMER}


@app.get("/api/datasets")
def datasets():
    """Registry of every input dataset: source, license, refresh, verification status."""
    import yaml
    from pathlib import Path
    return yaml.safe_load((Path(__file__).resolve().parent.parent / "config" / "datasets.yaml").read_text())


@app.get("/api/zips")
def zips():
    return store.zips()


@app.get("/api/coverage")
def coverage():
    return store.zoning_coverage()


@app.post("/api/reload")
def reload():
    store.load()
    return {"parcels": len(store.parcels), "zips": len(store.by_zip)}


@app.get("/api/zip/{zip_code}")
def zip_lookup(
    zip_code: str,
    min_score: float = FILTERS["min_score"], city: Optional[str] = FILTERS["city"],
    land_use: Optional[str] = FILTERS["land_use"], min_lot: float = FILTERS["min_lot"],
    result_type: Optional[str] = FILTERS["result_type"], max_risk: float = FILTERS["max_risk"],
    min_confidence: float = FILTERS["min_confidence"],
):
    rows = _filtered(zip_code, min_score, city, land_use, min_lot, result_type, max_risk,
                     min_confidence)
    all_rows = store.query(zip_code)
    return {
        "type": "FeatureCollection",
        "features": [_feature(p, s) for p, s in rows],
        "summary": {
            "zip": zip_code,
            "matched": len(rows),
            "total_in_zip": len(all_rows),
            "cities": sorted({p.city or "(unmatched)" for p, _ in all_rows}),
            "synthetic_data": bool(store.meta.get("synthetic")),
            "disclaimer": DISCLAIMER,
        },
    }


@app.get("/api/zip/{zip_code}/gaps")
def zip_gaps(zip_code: str):
    return store.gap_report(_validated_zip(zip_code))


@app.get("/api/zip/{zip_code}/export.geojson")
def export_geojson(
    zip_code: str,
    min_score: float = FILTERS["min_score"], city: Optional[str] = FILTERS["city"],
    land_use: Optional[str] = FILTERS["land_use"], min_lot: float = FILTERS["min_lot"],
    result_type: Optional[str] = FILTERS["result_type"], max_risk: float = FILTERS["max_risk"],
    min_confidence: float = FILTERS["min_confidence"],
):
    rows = _filtered(zip_code, min_score, city, land_use, min_lot, result_type, max_risk,
                     min_confidence)
    body = {"type": "FeatureCollection", "disclaimer": DISCLAIMER,
            "features": [_feature(p, s) for p, s in rows]}
    return Response(json.dumps(body), media_type="application/geo+json", headers={
        "Content-Disposition": f'attachment; filename="oc_{zip_code}_opportunities.geojson"'})


CSV_FIELDS = [
    "parcel_id", "address", "zip", "city", "land_use", "lot_sqft", "zoning_code",
    "overall", "potential", "risk", "confidence", "best_units", "best_pathway",
    "land_cost_per_unit", "price_basis", "zoning_status", "result_type", "is_synthetic",
]


@app.get("/api/zip/{zip_code}/export.csv")
def export_csv(
    zip_code: str,
    min_score: float = FILTERS["min_score"], city: Optional[str] = FILTERS["city"],
    land_use: Optional[str] = FILTERS["land_use"], min_lot: float = FILTERS["min_lot"],
    result_type: Optional[str] = FILTERS["result_type"], max_risk: float = FILTERS["max_risk"],
    min_confidence: float = FILTERS["min_confidence"],
):
    rows = _filtered(zip_code, min_score, city, land_use, min_lot, result_type, max_risk,
                     min_confidence)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    w.writeheader()
    for p, s in rows:
        props = _feature(p, s)["properties"]
        w.writerow({k: props.get(k) for k in CSV_FIELDS})
    return Response(buf.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="oc_{zip_code}_opportunities.csv"'})


@app.get("/api/parcel/{parcel_id}")
def parcel_detail(parcel_id: str):
    p = store.parcels.get(parcel_id)
    if p is None:
        raise HTTPException(404, f"Unknown parcel {parcel_id}")
    return {"parcel": p.model_dump(exclude={"geometry"}),
            "score": store.scores[parcel_id].model_dump(),
            "disclaimer": DISCLAIMER}


@app.exception_handler(HTTPException)
async def http_error(_, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail}
    return JSONResponse(status_code=exc.status_code, content=detail)


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")
