"""Synthetic world for tests and offline demos. NOT real county data.

Three fixture ZIPs mirror the Phase 1 samples:
  92618  mostly Irvine with an unincorporated strip
  92620  Irvine, thin data (no year built, missing tract tables / land use / TCAC)
  92705  crosses Santa Ana, an unincorporated strip, and Tustin (cross-city case)
  10001  a ZCTA outside the county (must be rejected)
"""
from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.affinity import scale
from shapely.geometry import LineString, Point, box

from .config import WORK_CRS

X0, Y0 = 6_080_000.0, 2_190_000.0
W, H = 3600.0, 2400.0
ZIPS = {"92618": (X0, Y0), "92620": (X0, Y0 + 8000), "92705": (X0 + 10000, Y0), "10001": (X0 + 300000, Y0)}
STREETS = ["Alder Way", "Birch Ct", "Cedar Ln", "Dove St", "Elm Pl", "Fern Ave", "Gull Rd", "Hawk Ter",
           "Iris Ln", "Juniper Way", "Kestrel Ct", "Laurel St"]
WIDTHS = [60, 75, 90, 120, 160, 220, 300]
DEPTH, GAP = 150.0, 40.0


def _gdf(rows, geom="geometry"):
    if not rows:
        return gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs=WORK_CRS)
    return gpd.GeoDataFrame(rows, geometry=geom, crs=WORK_CRS)


@lru_cache(maxsize=1)
def _base():
    rng = np.random.default_rng(42)
    parcels, lines, zcta = [], [], []
    for z, (x0, y0) in ZIPS.items():
        zcta.append({"GEOID": z, "geometry": box(x0, y0, x0 + W, y0 + H)})
        if z == "10001":
            continue
        row = 0
        y = y0 + GAP
        while y + DEPTH <= y0 + H - GAP / 2:
            lines.append({"geometry": LineString([(x0, y - GAP / 2), (x0 + W, y - GAP / 2)])})
            x, col = x0 + 5, 0
            while True:
                w = WIDTHS[int(rng.integers(len(WIDTHS)))]
                if x + w > x0 + W - 5:
                    break
                yb = int(rng.integers(1950, 2016))
                parcels.append({
                    "ASSESSMENT_NO": f"{z[2:]}-{row:03d}-{col:02d}",
                    "SITE_ADDRESS": f"{100 + col * 12} {STREETS[(row + int(z)) % len(STREETS)]}",
                    "YEAR_BUILT": "" if (z == "92620" or rng.random() < 0.15) else str(yb),
                    "NBR_BEDROOMS": 0, "zip": z, "geometry": box(x, y, x + w, y + DEPTH)})
                x += w
                col += 1
            y += DEPTH + GAP
            row += 1
    return _gdf(parcels), _gdf(lines), _gdf(zcta), rng


@lru_cache(maxsize=1)
def world() -> dict:
    parcels, lines, zcta, rng = _base()
    x18, y18 = ZIPS["92618"]
    x20, y20 = ZIPS["92620"]
    x05, y05 = ZIPS["92705"]
    county = box(X0 - 5000, Y0 - 5000, X0 + 20000, Y0 + 15000)

    cities = _gdf([
        {"JURISDICTI": "IRVINE", "CITY": "IRVINE", "geometry": box(x18 - 5000, y18 - 5000, x18 + W - 400, y20 + H + 2000)},
        # Santa Ana / unincorporated line at x05+1500 cuts through parcels on purpose.
        {"JURISDICTI": "SANTA ANA", "CITY": "SANTA ANA", "geometry": box(x05 - 1000, y05 - 2000, x05 + 1500, y05 + H + 2000)},
        {"JURISDICTI": "TUSTIN", "CITY": "TUSTIN", "geometry": box(x05 + 2300, y05 - 2000, x05 + W + 3000, y05 + H + 2000)},
    ])
    uninc = _gdf([{"NAME": "Unincorporated", "geometry": county.difference(cities.union_all())}])

    p = parcels.reset_index(drop=True)
    rep = p.geometry.representative_point()
    n = len(p)

    # Footprints: ~12% vacant, rest 5-60% coverage.
    fps = []
    for i, g in enumerate(p.geometry):
        if rng.random() < 0.12:
            continue
        cov = float(rng.uniform(0.05, 0.6))
        fps.append({"Height": 15.0, "geometry": scale(g, np.sqrt(cov), np.sqrt(cov))})
    footprints = _gdf(fps)

    pick = lambda frac: p.sample(frac=frac, random_state=int(rng.integers(1e6)))
    he = _gdf([{"geometry": g} for g in pick(0.05).geometry])
    rezone = _gdf([{"geometry": g} for g in pick(0.03).geometry])
    hqta = _gdf([{"geometry": box(x18 + 1800, y18 - 500, x18 + W + 500, y18 + H + 500)},
                 {"geometry": box(x05 - 500, y05 - 500, x05 + 1800, y05 + H + 500)}])
    bus = _gdf([{"stop_id": f"b{i}", "geometry": Point(x, ln.coords[0][1])}
                for i, ln in enumerate(lines.geometry) for x in np.arange(ln.coords[0][0] + 200, ln.coords[1][0], 900)])
    rail = _gdf([{"stop_id": "r1", "geometry": Point(x05 + 600, y05 + 1200)}])

    # Tracts: each ZIP split east/west.
    tracts, acs, lodes, tcac, ces = [], [], [], [], []
    for k, (z, (x0, y0)) in enumerate(ZIPS.items()):
        for half in (0, 1):
            geoid = f"06059{(k * 10 + half + 1) * 100:06d}"
            geom = box(x0 + half * W / 2, y0, x0 + (half + 1) * W / 2, y0 + H)
            tracts.append({"GEOID": geoid, "geometry": geom})
            thin = z == "92620" and half == 1
            if not thin:
                acs.append({"tract_geoid": geoid, "median_hh_income": 60000 + 25000 * k + 10000 * half,
                            "rent_burden_share": 0.35 + 0.08 * half})
                lodes.append({"tract_geoid": geoid, "tract_jobs": 1500 + 4000 * half + 2500 * k})
            if z != "92620":
                tcac.append({"oppcat": ["Highest Resource", "High Resource", "Moderate Resource", "Low Resource"][(k + half) % 4],
                             "geometry": geom})
            ces.append({"CIscoreP": 30 + 25 * half + 10 * k, "geometry": geom})

    lu_rows = []
    codes = ["1110", "1120", "1210", "1220", "1460", "1230", "1900"]
    for g, z in zip(p.geometry, p["zip"]):
        if z != "92620":
            lu_rows.append({"LU19": codes[int(rng.integers(len(codes)))], "geometry": g})

    worship_idx = [5, 40]
    tax_idx = [12, 77]
    nrhp_idx = [30]

    return {
        "census_zcta": zcta,
        "ocgis_parcels": p.drop(columns=["zip"]),
        "ocgis_city_boundaries": cities,
        "ocgis_unincorporated": uninc,
        "ocgis_building_footprints": footprints,
        "ocgis_centerlines": lines,
        "census_tracts": _gdf(tracts),
        "scag_land_use": _gdf(lu_rows),
        "scag_he_sites": he,
        "scag_he_rezone": rezone,
        "hcd_compliance": pd.DataFrame({"Jurisdiction": ["Irvine", "Santa Ana", "Tustin", "Orange County"],
                                        "Status": ["In compliance", "In compliance", "Out of compliance", "In compliance"]}),
        "hcd_sb35": pd.DataFrame({"Jurisdiction": ["Irvine", "Santa Ana", "Tustin", "Orange County"],
                                  "Determination": ["Subject to SB 35 (50% affordability)", "Exempt",
                                                    "Subject to SB 35 (10% affordability)",
                                                    "Subject to SB 35 (10% affordability)"]}),
        "apr_table_h": pd.DataFrame({"APN": [p.loc[60, "ASSESSMENT_NO"]]}),
        "hcd_sla_notices": pd.DataFrame({"APN": pd.Series([], dtype=str)}),
        "dgs_state_land": _gdf([]),
        "osm_worship": _gdf([{"name": "Synthetic chapel", "geometry": rep.iloc[i].buffer(5)} for i in worship_idx]),
        "oc_tax_defaulted": pd.DataFrame({"apn": [p.loc[i, "ASSESSMENT_NO"] for i in tax_idx]}),
        "scag_hqta": hqta,
        "octa_gtfs": bus,
        "metrolink_gtfs": rail,
        "lodes_wac": pd.DataFrame(lodes),
        "cde_schools": _gdf([{"geometry": Point(x18 + 900, y18 + 1200)}, {"geometry": Point(x05 + 2800, y05 + 600)}]),
        "osm_grocery": _gdf([{"geometry": Point(x18 + 2500, y18 + 300)}, {"geometry": Point(x05 + 1000, y05 + 2000)}]),
        "tcac_opportunity": _gdf(tcac),
        "acs5": pd.DataFrame(acs),
        "calenviroscreen4": _gdf(ces),
        "cdfi_oz": pd.DataFrame({"GEOID": [tracts[5]["GEOID"]]}),
        "fema_nfhl": _gdf([{"SFHA_TF": "T", "geometry": box(x05, y05, x05 + W, y05 + 400)}]),
        "calfire_fhsz_lra": _gdf([{"HAZ_CLASS": "Very High", "geometry": box(x20, y20 + H - 500, x20 + W, y20 + H)}]),
        "calfire_fhsz_sra": _gdf([]),
        "cgs_liquefaction": _gdf([{"geometry": box(x05 + 2000, y05, x05 + W, y05 + H)}]),
        "cgs_fault_zones": _gdf([]),
        "coastal_zone": _gdf([]),
        "calgem_wells": _gdf([{"geometry": rep.iloc[100]}]),
        "dtsc_envirostor": _gdf([{"geometry": Point(x18 + 300, y18 + 300)}]),
        "geotracker": _gdf([]),
        "nrhp": _gdf([{"geometry": p.geometry.iloc[i]} for i in nrhp_idx]),
        "hcd_mobilehome_parks": _gdf([{"geometry": rep.iloc[150]}]),
        "hud_lihtc": _gdf([{"geometry": rep.iloc[200]}]),
        "hud_mf_s8": _gdf([]),
        "_meta": {"worship_apns": [p.loc[i, "ASSESSMENT_NO"] for i in worship_idx],
                  "tax_apns": [p.loc[i, "ASSESSMENT_NO"] for i in tax_idx], "n_parcels": n},
    }
