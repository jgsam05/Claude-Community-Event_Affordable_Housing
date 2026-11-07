"""ZIP -> parcels, each tagged with its city or 'Unincorporated'."""
from __future__ import annotations

import re

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

from .config import MIN_OC_SHARE, WORK_CRS
from .sources import Sources, norm_apn, pick


class ZipError(Exception):
    status = 400


class ZipNotFound(ZipError):
    status = 404


class ZipNotInOC(ZipError):
    status = 404


def zcta_polygon(zip_code: str, src: Sources) -> gpd.GeoDataFrame:
    if not re.fullmatch(r"\d{5}", zip_code or ""):
        raise ZipError("ZIP must be 5 digits")
    if src.mode == "fixture":
        z = src.get("census_zcta")
        z = z[z["GEOID"] == zip_code] if z is not None else None
    else:
        from . import arcgis, registry
        z = arcgis.query(registry.BY_ID["census_zcta"]["url"], where=f"GEOID = '{zip_code}'")
        src.status["census_zcta"] = "loaded"
        registry.stamp_ingest("census_zcta", extra={"method": "arcgis_rest query"})
    if z is None or z.empty:
        raise ZipNotFound(f"{zip_code} is not a Census ZCTA")
    return z.dissolve()[["geometry"]]


def _city_name_col(cities: gpd.GeoDataFrame) -> str:
    return pick(cities, ["CITY", "JURISDICTI", "NAME", "city"])


def select_parcels(zip_code: str, src: Sources) -> tuple[gpd.GeoDataFrame, dict, gpd.GeoDataFrame]:
    zcta = zcta_polygon(zip_code, src)
    zgeom = zcta.geometry.iloc[0]
    area_4326 = zcta.to_crs(4326).geometry.iloc[0]

    cities = src.get("ocgis_city_boundaries", area_4326, cache_key=zip_code)
    uninc = src.get("ocgis_unincorporated", area_4326, cache_key=zip_code)

    # Valid OC ZIP: enough of the ZCTA falls inside the county (cities + unincorporated).
    loaded = [g for g in (cities, uninc) if g is not None]
    oc_share = None
    if loaded:
        parts = [unary_union(g.to_crs(WORK_CRS).geometry.values) for g in loaded if not g.empty]
        oc_share = zgeom.intersection(unary_union(parts)).area / zgeom.area if parts else 0.0
        if oc_share < MIN_OC_SHARE:
            raise ZipNotInOC(f"{zip_code} is not an Orange County ZIP ({oc_share:.1%} inside county)")

    parcels = src.get("ocgis_parcels", area_4326, cache_key=zip_code)
    if parcels is None:
        raise RuntimeError("Parcel layer unavailable; cannot screen ZIP")
    if parcels.empty:
        raise ZipNotInOC(f"No OCGIS parcels in {zip_code}")

    parcels = parcels.to_crs(WORK_CRS)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].copy()
    parcels["geometry"] = parcels.geometry.make_valid()
    rep = parcels.geometry.representative_point()
    parcels = parcels[rep.within(zgeom)].copy()          # parcel belongs to the ZIP its interior point is in
    rep = parcels.geometry.representative_point()

    apn_col = pick(parcels, ["ASSESSMENT_NO", "APN"])
    addr_col = pick(parcels, ["SITE_ADDRESS", "ADDRESS"], required=False)
    yb_col = pick(parcels, ["YEAR_BUILT"], required=False)
    out = gpd.GeoDataFrame({
        "apn": parcels[apn_col].astype(str).str.strip(),
        "apn_norm": parcels[apn_col].map(norm_apn),
        "address": parcels[addr_col].fillna("").astype(str).str.strip() if addr_col else "",
        "year_built": pd.to_numeric(parcels[yb_col], errors="coerce") if yb_col else pd.NA,
        "zip": zip_code,
    }, geometry=parcels.geometry.values, crs=WORK_CRS)
    out.loc[(out["year_built"] < 1800) | (out["year_built"] > 2100), "year_built"] = pd.NA
    # Stacked condo/duplicate records: keep one row per APN.
    out = out.drop_duplicates("apn").reset_index(drop=True)
    rep = out.geometry.representative_point()

    # Jurisdiction tagging.
    out["jurisdiction"] = "Unincorporated"
    out["straddles_city_line"] = False
    if cities is not None and not cities.empty:
        name_col = _city_name_col(cities)
        c = cities[[name_col, "geometry"]].rename(columns={name_col: "city"}).to_crs(WORK_CRS)
        c["city"] = c["city"].astype(str).str.strip().str.title()
        hit = gpd.sjoin(gpd.GeoDataFrame(geometry=rep, crs=WORK_CRS), c, predicate="within", how="left")
        hit = hit[~hit.index.duplicated()]
        out.loc[hit["city"].notna(), "jurisdiction"] = hit.loc[hit["city"].notna(), "city"]
        # Parcels whose polygon is split by a city line (>1% of area on the other side).
        ov = gpd.overlay(out[["apn", "geometry"]], c, how="intersection", keep_geom_type=True)
        ov["share"] = ov.area / ov["apn"].map(out.set_index("apn").area)
        by = ov.groupby(["apn", "city"])["share"].sum()
        n_cities = (by > 0.01).groupby(level=0).sum()
        inside = by.groupby(level=0).sum()
        straddle = set(n_cities[n_cities > 1].index) | set(inside[(inside > 0.01) & (inside < 0.99)].index)
        out["straddles_city_line"] = out["apn"].isin(straddle)
    elif src.status.get("ocgis_city_boundaries") != "loaded":
        out["jurisdiction"] = None  # unknown, not unincorporated

    counts = out["jurisdiction"].fillna("Unknown").value_counts().to_dict()
    meta = {"zip": zip_code, "oc_share": None if oc_share is None else round(oc_share, 4),
            "jurisdictions": counts, "crosses_city_lines": len(counts) > 1,
            "parcel_count": int(len(out))}
    return out, meta, zcta
