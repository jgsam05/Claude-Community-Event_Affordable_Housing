"""HTTP API.

GET /zip/{zip}              GeoJSON FeatureCollection of scored parcels (cached per ZIP)
GET /zip/{zip}?refresh=1    rebuild from sources
GET /zip/{zip}/validation   APR Table A2 comparison for the ZIP
GET /registry               dataset registry + Phase 1 gaps
GET /describe-layer         conditional-field report for the OCGIS parcel layer
GET /health
Run: uvicorn parcel_engine.api:app --reload   (from backend/)
"""
from __future__ import annotations

import json
import threading

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import arcgis, pipeline, registry
from .config import MODE, SAMPLE_ZIPS
from .selection import ZipError

app = FastAPI(title="Parcel Screener API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])
_mem: dict[str, dict] = {}
_lock = threading.Lock()


def _get_zip(zip_code: str, refresh: bool) -> dict:
    with _lock:
        if not refresh and zip_code in _mem:
            return _mem[zip_code]
        disk = pipeline.SCORED / f"{zip_code}.geojson"
        if not refresh and MODE == "live" and disk.exists():
            fc = json.loads(disk.read_text())
        else:
            fc = pipeline.build_zip(zip_code)
        _mem[zip_code] = fc
        return fc


@app.get("/health")
def health():
    return {"ok": True, "mode": MODE, "sample_zips": SAMPLE_ZIPS}


@app.get("/zip/{zip_code}")
def get_zip(zip_code: str, refresh: bool = Query(False)):
    try:
        return _get_zip(zip_code, refresh)
    except ZipError as e:
        raise HTTPException(status_code=e.status, detail=str(e))


@app.get("/zip/{zip_code}/validation")
def get_validation(zip_code: str):
    try:
        return _get_zip(zip_code, False)["metadata"]["validation"]
    except ZipError as e:
        raise HTTPException(status_code=e.status, detail=str(e))


@app.get("/registry")
def get_registry():
    gaps = registry.phase1_gaps()
    return {"datasets": registry.records(), "phase1_gaps": gaps, "phase1_documented": not gaps}


@app.get("/describe-layer")
def get_describe_layer(url: str = Query(registry.BY_ID["ocgis_parcels"]["url"])):
    if MODE == "fixture":
        raise HTTPException(status_code=503, detail="describe-layer needs live mode")
    return arcgis.describe_layer(url)
