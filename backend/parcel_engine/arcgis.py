"""Minimal ArcGIS REST client: layer description + paged spatial queries."""
from __future__ import annotations

import json
import re
import time

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import MultiPolygon, Polygon

from .config import WORK_CRS

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "parcel-screener-backend/0.1"
TIMEOUT = 60


def _get(url: str, params: dict, method: str = "GET", retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            if method == "POST":
                r = SESSION.post(url, data=params, timeout=TIMEOUT)
            else:
                r = SESSION.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise RuntimeError(f"ArcGIS error from {url}: {data['error']}")
            return data
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def layer_info(layer_url: str) -> dict:
    return _get(layer_url, {"f": "json"})


# Patterns for the conditional-signal report. ASSESSMENT_NO is the APN, not a value,
# so value patterns exclude *_NO / *_NUM fields.
CONDITIONAL_PATTERNS = {
    "use_code": (r"(USE|LANDUSE|LAND_USE|LU_?CODE|USECODE|ZON)", None),
    "year_built": (r"(YEAR_?BUILT|YR_?BLT|AYB|EFF_?YR)", None),
    "assessed_values": (r"(ASSESS|LAND_?VAL|IMP_?VAL|IMPR|TOTAL_?VAL|NET_?VAL|VALUE)", r"(_NO|_NUM|NUMBER)$"),
    "owner_name": (r"(OWNER|OWN_?NAME|TAXPAYER)", None),
}

DECISIONS = {
    "use_code": ("Land use code signal kept from parcel layer",
                 "Use code absent: use SCAG parcel land use dataset (scag_land_use) or remove"),
    "year_built": ("Building age kept (missing values lower confidence)", "Building age removed"),
    "assessed_values": ("Improvement-to-land ratio and land cost per unit kept",
                        "Improvement-to-land ratio removed; land cost replaced by unit-count estimate only"),
    "owner_name": ("Owner type classified (public/corporate/individual), then name discarded",
                   "Owner type limited to public ownership from Keep sources (Table H, SLA, DGS)"),
}


def describe_layer(layer_url: str, fill_rates: bool = True) -> dict:
    """Report which conditional fields exist on a layer and what that decides."""
    info = layer_info(layer_url)
    fields = [dict(name=f["name"], type=f["type"], alias=f.get("alias")) for f in info.get("fields", [])]
    report = {"layer_url": layer_url, "name": info.get("name"), "geometry_type": info.get("geometryType"),
              "max_record_count": info.get("maxRecordCount"),
              "spatial_reference": (info.get("extent") or {}).get("spatialReference") or info.get("sourceSpatialReference"),
              "last_edit_date": (info.get("editingInfo") or {}).get("lastEditDate"),
              "fields": fields, "conditional": {}}
    total = None
    if fill_rates:
        try:
            total = _get(f"{layer_url}/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"})["count"]
        except Exception:  # count is a nice-to-have
            total = None
    report["feature_count"] = total
    for key, (pat, exclude) in CONDITIONAL_PATTERNS.items():
        matches = [f["name"] for f in fields
                   if re.search(pat, f["name"], re.I) and not (exclude and re.search(exclude, f["name"], re.I))
                   and f["type"] not in ("esriFieldTypeOID", "esriFieldTypeGeometry")]
        entry = {"present": bool(matches), "fields": matches,
                 "decision": DECISIONS[key][0] if matches else DECISIONS[key][1]}
        if matches and fill_rates and total:
            rates = {}
            for name in matches:
                try:
                    n = _get(f"{layer_url}/query", {"where": f"{name} IS NOT NULL AND {name} <> ''",
                                                    "returnCountOnly": "true", "f": "json"})["count"]
                    rates[name] = round(n / total, 4)
                except Exception:
                    rates[name] = None
            entry["fill_rate"] = rates
        report["conditional"][key] = entry
    return report


def _esri_polygon(geom) -> dict:
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    rings = []
    for p in polys:
        rings.append([list(c) for c in p.exterior.coords])
        rings.extend([list(c) for c in i.coords] for i in p.interiors)
    return {"rings": rings, "spatialReference": {"wkid": 4326}}


def query(layer_url: str, where: str = "1=1", geometry=None, out_fields: str = "*",
          chunk: int | None = None) -> gpd.GeoDataFrame:
    """Query a layer and return a GeoDataFrame in WORK_CRS.

    `geometry` is a shapely polygon in EPSG:4326 used as an intersects filter.
    Pages by object id (works on MapServer layers without pagination support).
    """
    base = {"where": where, "f": "json"}
    if geometry is not None:
        if not isinstance(geometry, (Polygon, MultiPolygon)):
            geometry = geometry.envelope
        base.update(geometry=json.dumps(_esri_polygon(geometry.simplify(0.00005))),
                    geometryType="esriGeometryPolygon", inSR="4326", spatialRel="esriSpatialRelIntersects")
    ids = _get(f"{layer_url}/query", {**base, "returnIdsOnly": "true"}, method="POST").get("objectIds") or []
    if not ids:
        return gpd.GeoDataFrame(geometry=[], crs=WORK_CRS)
    if chunk is None:
        chunk = min(int(layer_info(layer_url).get("maxRecordCount") or 1000), 1000)
    frames = []
    for i in range(0, len(ids), chunk):
        params = {"objectIds": ",".join(map(str, ids[i:i + chunk])), "outFields": out_fields,
                  "outSR": "4326", "f": "geojson", "returnGeometry": "true"}
        gj = _get(f"{layer_url}/query", params, method="POST")
        if gj.get("features"):
            frames.append(gpd.GeoDataFrame.from_features(gj["features"], crs=4326))
    if not frames:
        return gpd.GeoDataFrame(geometry=[], crs=WORK_CRS)
    gdf = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=4326)
    return gdf.to_crs(WORK_CRS)

