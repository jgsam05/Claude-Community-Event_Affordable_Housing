"""Geometry signals computed in EPSG:2230 (US feet)."""
from __future__ import annotations

import geopandas as gpd
import numpy as np
from shapely.ops import unary_union

from .config import FOOTPRINT_SOURCE, FRONTAGE_BUFFER_FT, MIN_FOOTPRINT_SQFT, SETBACK_FT

SQFT_PER_ACRE = 43560.0


def _mrr_short_side(geom) -> float:
    rect = geom.minimum_rotated_rectangle
    if rect.geom_type != "Polygon":
        return 0.0
    xs, ys = rect.exterior.coords.xy
    sides = [np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(4)]
    return float(min(sides))


def add_geometry_signals(parcels: gpd.GeoDataFrame, src, area_4326, zip_code) -> gpd.GeoDataFrame:
    p = parcels.copy()
    p["lot_sqft"] = p.geometry.area.round(0)
    p["lot_acres"] = (p["lot_sqft"] / SQFT_PER_ACRE).round(3)
    p["buildable_sqft"] = p.geometry.buffer(-SETBACK_FT).area.round(0)

    # Frontage: parcel boundary length within FRONTAGE_BUFFER_FT of a street centerline.
    streets = src.get("ocgis_centerlines", area_4326, cache_key=zip_code)
    if streets is not None and not streets.empty:
        corridor = unary_union(streets.geometry.buffer(FRONTAGE_BUFFER_FT).values)
        p["frontage_ft"] = p.geometry.boundary.intersection(corridor).length.round(0)
        p["frontage_method"] = "centerline_buffer"
    else:
        p["frontage_ft"] = p.geometry.map(_mrr_short_side).round(0)
        p["frontage_method"] = "mrr_estimate"

    # Building coverage = footprint area inside parcel / lot area.
    fp = src.get(FOOTPRINT_SOURCE, area_4326, cache_key=zip_code)
    p["coverage_source"] = FOOTPRINT_SOURCE
    if fp is None:
        p["building_coverage"] = np.nan
        p["building_sqft"] = np.nan
        p["vacant"] = None
        return p
    fp = fp[["geometry"]].to_crs(p.crs)
    fp = fp[fp.geometry.notna()]
    fp["geometry"] = fp.geometry.make_valid()
    if fp.empty:
        inter_area = {}
    else:
        ov = gpd.overlay(p[["apn", "geometry"]], fp, how="intersection", keep_geom_type=True)
        inter_area = ov.assign(a=ov.area).groupby("apn")["a"].sum().to_dict()
    p["building_sqft"] = p["apn"].map(inter_area).fillna(0.0).round(0)
    p["building_coverage"] = (p["building_sqft"] / p["lot_sqft"]).clip(upper=1.0).round(3)
    p["vacant"] = p["building_sqft"] < MIN_FOOTPRINT_SQFT
    return p
