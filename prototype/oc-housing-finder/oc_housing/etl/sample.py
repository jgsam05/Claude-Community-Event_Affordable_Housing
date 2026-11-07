"""SYNTHETIC demo parcels so the whole system runs before real data is loaded.

Nothing here is a real property. IDs are 'SYN-...', every record carries
is_synthetic=True, and the UI shows a banner whenever synthetic data is loaded.
Parcel geometry is placed near each ZIP's approximate center; the jurisdiction
is still assigned by the REAL spatial join against the OC boundary layer, so a
synthetic parcel can land in whichever city that point actually falls in.
"""

from __future__ import annotations

import random

from shapely.geometry import Polygon, mapping

from ..schema import Parcel

# Approximate ZIP centers. The 92627 demo grid is centered ON the Costa Mesa /
# Newport Beach border (computed from the real boundary layer) so that one demo
# ZIP spans two cities, the situation real OC ZIPs create all the time.
SAMPLE_ZIPS = {
    "92701": (33.7455, -117.8678),
    "92805": (33.8366, -117.9143),
    "92627": (33.64696, -117.89877),
}

M_PER_DEG_LAT = 111_000.0
M_PER_DEG_LON = 92_500.0  # at ~33.8 N
SQM_TO_SQFT = 10.7639

USE_WEIGHTS = [
    ("single_family", 45), ("multifamily", 10), ("commercial_1story", 12),
    ("commercial_other", 5), ("vacant", 8), ("surface_parking", 7),
    ("industrial", 5), ("public", 3), ("institutional_faith", 3),
    ("mobile_home_park", 2),
]

OWNER_BY_USE = {
    "public": "public", "institutional_faith": "faith",
    "mobile_home_park": "corporate",
}

SAMPLE_ZONE_BY_USE = {
    "single_family": ["SAMPLE-R1"],
    "multifamily": ["SAMPLE-R3"],
    "mobile_home_park": ["SAMPLE-R3"],
    "commercial_1story": ["SAMPLE-C1"],
    "commercial_other": ["SAMPLE-C1", "SAMPLE-MU"],
    "surface_parking": ["SAMPLE-C1", "SAMPLE-MU"],
    "industrial": ["SAMPLE-I"],
    "public": ["SAMPLE-PF"],
    "institutional_faith": ["SAMPLE-PF", "SAMPLE-R3"],
    "vacant": ["SAMPLE-R1", "SAMPLE-R3", "SAMPLE-C1", "SAMPLE-MU"],
}


def _maybe(rng: random.Random, value, p_known: float):
    """Return value with probability p_known, else None (unknown)."""
    return value if rng.random() < p_known else None


def generate(seed: int = 42, per_zip: int = 70) -> list[Parcel]:
    rng = random.Random(seed)
    uses, weights = zip(*USE_WEIGHTS)
    parcels: list[Parcel] = []

    for zip_code, (clat, clon) in SAMPLE_ZIPS.items():
        cols = 10
        rows = (per_zip + cols - 1) // cols
        for n in range(per_zip):
            r, c = divmod(n, cols)
            w = rng.uniform(18, 70)   # meters
            d = rng.uniform(25, 80)
            x0 = (c - cols / 2) * 85 + rng.uniform(0, 10)
            y0 = (r - rows / 2) * 95 + rng.uniform(0, 10)
            ring = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + d), (x0, y0 + d)]
            poly = Polygon([(clon + x / M_PER_DEG_LON, clat + y / M_PER_DEG_LAT) for x, y in ring])
            cen = poly.centroid
            lot_sqft = round(w * d * SQM_TO_SQFT)

            use = rng.choices(uses, weights)[0]
            if use == "vacant":
                bldg, impr = 0, 0
            elif use in ("commercial_1story", "surface_parking"):
                cov = rng.uniform(0.05, 0.25) if use == "surface_parking" else rng.uniform(0.15, 0.45)
                bldg, impr = round(lot_sqft * cov), None
            else:
                bldg, impr = round(lot_sqft * rng.uniform(0.2, 0.7)), None
            land_value = round(lot_sqft * rng.uniform(25, 95))
            if impr is None:
                impr = round(bldg * rng.uniform(45, 130))

            sold_recent = rng.random() < 0.35
            sale_year = rng.randint(2020, 2026) if sold_recent else rng.randint(1985, 2015)
            sale_price = round(lot_sqft * rng.uniform(120, 260) + bldg * rng.uniform(80, 200))

            distress_prone = use in ("vacant", "commercial_1story", "commercial_other", "surface_parking")
            parcels.append(Parcel(
                parcel_id=f"SYN-{zip_code}-{n:04d}",
                apn=f"SYN-{zip_code}-{n:04d}",
                address=f"{100 + n * 7} Demo St (synthetic)",
                zip_code=zip_code,
                lat=cen.y, lon=cen.x,
                geometry=mapping(poly),
                lot_sqft=lot_sqft,
                land_use=use,
                year_built=None if use == "vacant" else rng.randint(1948, 2012),
                building_sqft=bldg,
                land_value=land_value,
                improvement_value=impr,
                last_sale_price=sale_price,
                last_sale_year=sale_year,
                owner_type=OWNER_BY_USE.get(use, rng.choice(["individual", "corporate", "individual"])),
                tax_default=_maybe(rng, rng.random() < (0.12 if distress_prone else 0.03), 0.7),
                code_violations=_maybe(rng, rng.choice([0, 0, 0, 1, 2, 4]) if distress_prone else 0, 0.5),
                vacant_registry=_maybe(rng, use == "vacant" and rng.random() < 0.25, 0.4),
                housing_element_site=_maybe(rng, True, 0.05) if use in ("vacant", "surface_parking") else None,
                transit_distance_m=_maybe(rng, round(rng.uniform(100, 2500)), 0.8),
                opportunity_level=_maybe(
                    rng, rng.choice(["highest", "high", "moderate", "low", "very_low"]), 0.7),
                coastal_zone=_maybe(rng, zip_code == "92627" and rng.random() < 0.3, 0.6),
                fire_hazard=_maybe(rng, False, 0.5),
                flood_zone=_maybe(rng, rng.random() < 0.1, 0.7),
                airport_zone=_maybe(rng, rng.random() < 0.08, 0.7),
                contamination=_maybe(rng, use == "industrial" and rng.random() < 0.4, 0.6),
                historic=_maybe(rng, rng.random() < 0.03, 0.8),
                mobile_home=True if use == "mobile_home_park" else None,
                is_synthetic=True,
            ))
    return parcels


def assign_sample_zoning(parcels: list[Parcel], adapters: dict, seed: int = 43) -> int:
    """Give synthetic parcels a SAMPLE zone code, only where the (real) joined
    city has a sample adapter. Other cities stay 'not ingested' on purpose."""
    rng = random.Random(seed)
    n = 0
    for p in parcels:
        if p.city in adapters and p.land_use:
            p.zoning_code = rng.choice(SAMPLE_ZONE_BY_USE[p.land_use])
            n += 1
    return n
