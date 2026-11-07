"""Registry-driven joins of signal datasets onto parcels.

A dataset that is not available leaves its columns as NaN/None, which scoring
reads as "missing" (lowers confidence). A dataset that loaded but has no
feature touching a parcel gives a real False / far distance, which is data.
"""
from __future__ import annotations

import re

import geopandas as gpd
import numpy as np
import pandas as pd

from . import registry
from .sources import Sources, norm_apn, pick

FAR_FT = 15840.0  # point layers are clipped ~3 mi around the ZIP; "nothing found" reads as >= 3 mi
SKIP = {"ocgis_parcels", "ocgis_city_boundaries", "ocgis_unincorporated", "census_zcta", "census_tracts",
        "ocgis_building_footprints", "overture_buildings", "ocgis_centerlines", "apr_table_a2",
        "hud_income_limits"}


def _norm_juris(name) -> str:
    s = str(name or "").lower().strip()
    s = re.sub(r"^(city of|town of)\s+", "", s)
    s = re.sub(r"\s+(city|county)$", "", s)
    return "orange" if s in ("unincorporated", "orange co", "orange county") else s


def join_all(p: gpd.GeoDataFrame, src: Sources, area_4326, zip_code: str) -> tuple[gpd.GeoDataFrame, dict]:
    p = p.copy()
    rep = gpd.GeoDataFrame({"apn": p["apn"].values}, geometry=p.geometry.representative_point().values, crs=p.crs)
    shrunk = gpd.GeoDataFrame({"apn": p["apn"].values}, geometry=p.geometry.buffer(-1.0).values, crs=p.crs)
    avail: dict[str, bool] = {}

    # Tract key for tract-level tables.
    tracts = src.get("census_tracts", area_4326, cache_key=zip_code)
    if tracts is not None and not tracts.empty:
        gcol = pick(tracts, ["GEOID", "geoid"])
        t = tracts[[gcol, "geometry"]].rename(columns={gcol: "tract_geoid"}).to_crs(p.crs)
        hit = gpd.sjoin(rep, t, predicate="within", how="left")
        p["tract_geoid"] = hit[~hit.index.duplicated()]["tract_geoid"].astype("object").values
    else:
        p["tract_geoid"] = None

    for spec in registry.DATASETS:
        join = spec.get("join")
        if not join or spec["id"] in SKIP:
            continue
        data = src.get(spec["id"], area_4326, cache_key=zip_code)
        ok = data is not None
        if ok and join["type"] == "tract_table":
            ok = p["tract_geoid"].notna().any()
        avail[spec["id"]] = ok
        handler = HANDLERS[join["type"]]
        try:
            handler(p, data if ok else None, join, rep=rep, shrunk=shrunk)
        except KeyError as e:  # a schema mismatch is a missing signal, not a crash
            src.status[spec["id"]] = f"schema: {e}"
            avail[spec["id"]] = False
            handler(p, None, join, rep=rep, shrunk=shrunk)
    return p, avail


def _flag_intersects(p, data, join, shrunk, **_):
    col = join["column"]
    if data is None:
        p[col] = None
        return
    if data.empty:
        p[col] = False
        return
    hit = gpd.sjoin(shrunk, data[["geometry"]].to_crs(p.crs), predicate="intersects", how="inner")
    p[col] = p["apn"].isin(set(hit["apn"]))


def _attr_at_point(p, data, join, rep, **_):
    if data is None:
        for out in join["fields"]:
            p[out] = None
        return
    cols = {out: pick(data, cands) for out, cands in join["fields"].items()}
    d = data[list(cols.values()) + ["geometry"]].rename(columns={v: k for k, v in cols.items()}).to_crs(p.crs)
    hit = gpd.sjoin(rep, d, predicate="within", how="left")
    hit = hit[~hit.index.duplicated()]
    for out in cols:
        p[out] = hit[out].astype("object").where(hit[out].notna(), None).values


def _nearest_distance(p, data, join, rep, **_):
    col = join["column"]
    if data is None:
        p[col] = np.nan
        return
    if data.empty:
        p[col] = FAR_FT
        return
    d = data[["geometry"]].to_crs(p.crs)
    hit = gpd.sjoin_nearest(rep, d, how="left", distance_col="_d")
    dist = hit.groupby(level=0)["_d"].min().reindex(range(len(p)))
    p[col] = dist.clip(upper=FAR_FT).round(0).values


def _tract_table(p, data, join, **_):
    source = join["source"]
    if source == "acs":
        cols = ["median_hh_income", "rent_burden_share"]
        if data is None:
            for c in cols:
                p[c] = np.nan
            return
        m = p[["tract_geoid"]].merge(data, on="tract_geoid", how="left")
        for c in cols:
            p[c] = m[c].values
    elif source == "lodes":
        if data is None:
            p["tract_jobs"] = np.nan
            return
        m = p[["tract_geoid"]].merge(data, on="tract_geoid", how="left")
        p["tract_jobs"] = m["tract_jobs"].values
    elif source == "oz":
        if data is None:
            p["in_oz"] = None
            return
        key = pick(data, join.get("key", ["GEOID"]))
        geoids = set(data[key].astype(str).str.replace(r"\D", "", regex=True).str.zfill(11))
        p["in_oz"] = p["tract_geoid"].map(lambda g: (g in geoids) if g else None)


def _apn_list(p, data, join, **_):
    col = join["column"]
    if data is None:
        p[col] = None
        return
    key = pick(data, join["key"])
    apns = set(data[key].map(norm_apn).dropna())
    p[col] = p["apn_norm"].isin(apns)


def _jurisdiction_table(p, data, join, **_):
    if data is None:
        for out in join["fields"]:
            p[out] = None
        return
    key = pick(data, join["key"])
    lookup = data.assign(_j=data[key].map(_norm_juris)).drop_duplicates("_j").set_index("_j")
    for out, cands in join["fields"].items():
        c = pick(data, cands)
        p[out] = p["jurisdiction"].map(lambda j: lookup[c].get(_norm_juris(j)) if j else None)


HANDLERS = {"flag_intersects": _flag_intersects, "attr_at_point": _attr_at_point,
            "nearest_distance": _nearest_distance, "tract_table": _tract_table,
            "apn_list": _apn_list, "jurisdiction_table": _jurisdiction_table}
