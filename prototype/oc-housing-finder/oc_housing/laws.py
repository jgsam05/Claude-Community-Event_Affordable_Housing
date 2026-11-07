"""State-law unit estimation (screening level).

Each pathway returns units, applies / does_not_apply / unknown, and a note
saying what was NOT checked. Parameters live in config/laws.yaml, which ships
with verified: false until a human reviews it against current statute text.
"""

from __future__ import annotations

import math
from typing import Optional

from .schema import Parcel, PathwayEstimate, UnitEstimate, ZoneRule

SQFT_PER_ACRE = 43560.0


def _floor(x: float) -> int:
    return int(math.floor(x + 1e-9))


def estimate_units(parcel: Parcel, rule: Optional[ZoneRule], laws: dict) -> UnitEstimate:
    est = UnitEstimate(laws_verified=bool(laws.get("verified", False)))
    acres = (parcel.lot_sqft / SQFT_PER_ACRE) if parcel.lot_sqft else None

    # --- Base zoning ------------------------------------------------------
    base: Optional[int] = None
    if rule is None:
        est.pathways.append(PathwayEstimate(
            name="base_zoning", status="unknown",
            note="Zoning not ingested for this parcel's jurisdiction or zone code."))
    elif acres is None:
        est.pathways.append(PathwayEstimate(
            name="base_zoning", status="unknown", note="Lot size unknown."))
    elif rule.max_density_du_ac is None or rule.max_density_du_ac <= 0:
        base = 0
        est.pathways.append(PathwayEstimate(
            name="base_zoning", units=0, status="does_not_apply",
            note=f"Zone {rule.zone_code} allows no residential density in the loaded table."))
    else:
        base = _floor(acres * rule.max_density_du_ac)
        est.pathways.append(PathwayEstimate(
            name="base_zoning", units=base, status="applies",
            note=f"{rule.max_density_du_ac:g} du/ac x {acres:.2f} ac, before setbacks/parking/height limits."))
    est.base_units = base

    # --- Density bonus ----------------------------------------------------
    db = laws["density_bonus"]
    if base is None:
        est.pathways.append(PathwayEstimate(
            name="density_bonus", status="unknown", note="Needs base zoning."))
    elif base >= db["min_base_units"]:
        bonus = _floor(base * (1 + db["max_bonus_pct"] / 100.0))
        est.pathways.append(PathwayEstimate(
            name="density_bonus", units=bonus, status="applies",
            note=f"Up to +{db['max_bonus_pct']}% for a qualifying affordable set-aside; "
                 "actual bonus depends on affordability mix."))
    else:
        est.pathways.append(PathwayEstimate(
            name="density_bonus", units=base, status="does_not_apply",
            note=f"Base project under {db['min_base_units']} units."))

    # --- SB 9 (single-family lots) ---------------------------------------
    s9 = laws["sb9"]
    if rule is None or parcel.lot_sqft is None:
        est.pathways.append(PathwayEstimate(
            name="sb9", status="unknown", note="Needs zone category and lot size."))
    elif rule.category == "residential_low" and parcel.land_use in ("single_family", "vacant"):
        if parcel.lot_sqft >= s9["min_lot_sqft_split"]:
            est.pathways.append(PathwayEstimate(
                name="sb9", units=s9["units_after_split"], status="applies",
                note="Lot split plus duplexes. Owner-occupancy and other SB 9 conditions not checked."))
        elif parcel.lot_sqft >= s9["min_lot_sqft_duplex"]:
            est.pathways.append(PathwayEstimate(
                name="sb9", units=s9["units_duplex"], status="applies",
                note="Duplex only; lot too small to split."))
        else:
            est.pathways.append(PathwayEstimate(
                name="sb9", units=0, status="does_not_apply", note="Lot below SB 9 minimum."))
    else:
        est.pathways.append(PathwayEstimate(
            name="sb9", units=0, status="does_not_apply", note="Not a single-family-zoned lot."))

    # --- AB 2011 / SB 6 (commercial corridors) ---------------------------
    a2 = laws["ab2011"]
    if rule is None or acres is None:
        est.pathways.append(PathwayEstimate(
            name="ab2011", status="unknown", note="Needs zone category and lot size."))
    elif rule.category in a2["eligible_categories"] and parcel.lot_sqft >= a2["min_lot_sqft"]:
        units = _floor(acres * a2["min_density_du_ac"])
        est.pathways.append(PathwayEstimate(
            name="ab2011", units=units, status="applies",
            note=f"At least {a2['min_density_du_ac']} du/ac on commercially zoned land. "
                 "Corridor adjacency/width and other eligibility NOT checked."))
    else:
        est.pathways.append(PathwayEstimate(
            name="ab2011", units=0, status="does_not_apply",
            note="Not commercially zoned or lot below minimum."))

    # --- ADUs -------------------------------------------------------------
    if parcel.land_use == "single_family":
        est.pathways.append(PathwayEstimate(
            name="adu", units=laws["adu"]["added_units"], status="applies",
            note="Added units on an existing single-family lot."))

    applicable = [p for p in est.pathways if p.status == "applies" and p.units is not None]
    if applicable:
        best = max(applicable, key=lambda p: p.units)
        est.best_units, est.best_pathway = best.units, best.name
    elif base is not None:
        # Zoning and lot size are both KNOWN and no pathway yields housing:
        # that is a real answer (zero units), not missing data. Leaving it None
        # would let non-residential parcels rank high by being "unknown".
        est.best_units, est.best_pathway = 0, None
    return est
