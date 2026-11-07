"""Transparent opportunity scoring.

Development Potential and Feasibility Risk are separate numbers. Both come with
a per-component breakdown so a user can see exactly why a parcel ranked where
it did. Unknown data is excluded from the weighted average (it does not count
as zero) and instead reduces `confidence`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from .laws import estimate_units
from .schema import Component, Parcel, ParcelScore, ZoneRule
from .zoning.base import ZoningAdapter

ROOT = Path(__file__).resolve().parent.parent


def load_yaml(name: str) -> dict:
    with (ROOT / "config" / name).open() as fh:
        return yaml.safe_load(fh)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


LAND_USE_FIT = {
    "vacant": 1.0,
    "surface_parking": 0.95,
    "commercial_1story": 0.8,
    "institutional_faith": 0.7,
    "public": 0.5,
    "industrial": 0.4,
    "commercial_other": 0.4,
    "single_family": 0.2,
    "other": 0.2,
    "multifamily": 0.15,
    "mobile_home_park": 0.0,
}

OWNER_FIT = {
    "public": 1.0,
    "faith": 0.9,
    "nonprofit": 0.7,
    "corporate": 0.5,
    "individual": 0.4,
}

OPPORTUNITY_FIT = {"highest": 1.0, "high": 0.9, "moderate": 0.6, "low": 0.35, "very_low": 0.2}


# --- individual components: each returns (score or None, explanation) --------

def c_land_use(p: Parcel, **_) -> tuple[Optional[float], str]:
    if p.land_use is None:
        return None, "Land use unknown."
    s = LAND_USE_FIT[p.land_use]
    return s, f"Land use '{p.land_use}' scores {s:.2f} for redevelopment fit."


def c_underbuilt(p: Parcel, cfg: dict, **_) -> tuple[Optional[float], str]:
    parts, notes = [], []
    if p.land_use == "vacant":
        return 1.0, "Vacant: no existing improvements."
    if p.lot_sqft and p.building_sqft is not None:
        coverage = p.building_sqft / p.lot_sqft
        parts.append(1 - _clamp(coverage / 0.8))
        notes.append(f"building/lot ratio {coverage:.2f}")
    if p.land_value and p.improvement_value is not None:
        ratio = p.improvement_value / p.land_value
        parts.append(1 - _clamp(ratio / 2.0))
        recent = (
            p.last_sale_year is not None
            and cfg["current_year"] - p.last_sale_year <= cfg["recent_sale_years"]
        )
        caveat = "" if recent else " (Prop 13 caveat: no recent sale, assessed values may understate market value)"
        notes.append(f"improvement/land value {ratio:.2f}{caveat}")
    if not parts:
        return None, "No building size or assessed value data."
    s = sum(parts) / len(parts)
    return s, "Underbuilt signals: " + "; ".join(notes) + "."


def c_lot_size(p: Parcel, cfg: dict, **_) -> tuple[Optional[float], str]:
    if p.lot_sqft is None:
        return None, "Lot size unknown."
    ls = cfg["lot_size_sqft"]
    a = p.lot_sqft
    if a < ls["too_small"]:
        s = 0.1
    elif a < ls["workable"]:
        s = 0.1 + 0.5 * (a - ls["too_small"]) / (ls["workable"] - ls["too_small"])
    elif a <= ls["sweet_spot_max"]:
        s = 1.0
    else:
        s = 0.7
    return s, f"Lot of {a:,.0f} sq ft."


def c_legal_upside(p: Parcel, units=None, **_) -> tuple[Optional[float], str]:
    if units is None or units.best_units is None:
        return None, "Unit potential cannot be computed (zoning or lot data missing)."
    best = units.best_units
    size_part = _clamp(best / 80.0)
    if units.base_units is None:
        # Base zoning unknown: uplift cannot be measured, so score on size alone.
        s = size_part
        return s, (f"Pathway '{units.best_pathway}' allows ~{best} units; base zoning "
                   "unknown, so unlock-vs-base uplift is not scored.")
    base = units.base_units
    uplift_part = _clamp((best - base) / max(base, 1))
    s = 0.6 * size_part + 0.4 * uplift_part
    if best == 0:
        return 0.0, "No residential units possible under loaded zoning or state-law pathways."
    return s, (f"Best pathway '{units.best_pathway}' allows ~{best} units "
               f"vs {base} under base zoning.")


def c_distress(p: Parcel, **_) -> tuple[Optional[float], str]:
    known = [v for v in (p.tax_default, p.code_violations, p.vacant_registry) if v is not None]
    if not known:
        return None, "No distress data for this parcel."
    s, notes = 0.0, []
    if p.tax_default:
        s += 0.5
        notes.append("tax-defaulted")
    if p.code_violations:
        s += 0.4 if p.code_violations >= 3 else 0.25
        notes.append(f"{p.code_violations} code violation(s)")
    if p.vacant_registry:
        s += 0.35
        notes.append("on vacant-building registry")
    s = _clamp(s)
    return s, ("Distress: " + ", ".join(notes) + ".") if notes else "No distress flags among known data."


def c_ownership(p: Parcel, **_) -> tuple[Optional[float], str]:
    s = OWNER_FIT.get(p.owner_type)
    notes = []
    if s is not None:
        notes.append(f"owner type '{p.owner_type}'")
    if p.housing_element_site:
        s = max(s or 0.0, 0.9)
        notes.append("on Housing Element sites inventory")
    if s is None:
        return None, "Owner type unknown."
    return s, "Ownership signals: " + ", ".join(notes) + "."


def c_location(p: Parcel, cfg: dict, **_) -> tuple[Optional[float], str]:
    parts, notes = [], []
    if p.transit_distance_m is not None:
        for limit, val in cfg["transit_distance_m"]:
            if p.transit_distance_m <= limit:
                parts.append(val)
                break
        notes.append(f"{p.transit_distance_m:,.0f} m to high-quality transit")
    if p.opportunity_level is not None:
        parts.append(OPPORTUNITY_FIT[p.opportunity_level])
        notes.append(f"{p.opportunity_level} opportunity area")
    if not parts:
        return None, "No transit or opportunity-area data."
    return sum(parts) / len(parts), "Location: " + ", ".join(notes) + "."


COMPONENT_FUNCS = {
    "land_use_fit": c_land_use,
    "underbuilt": c_underbuilt,
    "lot_size": c_lot_size,
    "legal_upside": c_legal_upside,
    "distress": c_distress,
    "ownership": c_ownership,
    "location": c_location,
}

RISK_LABELS = {
    "coastal_zone": "In Coastal Zone (Coastal Commission permitting)",
    "fire_hazard": "Very high fire hazard severity zone",
    "flood_zone": "In FEMA flood zone",
    "airport_zone": "In airport land-use compatibility zone",
    "contamination": "Near/at known contamination site",
    "historic": "Historic designation",
    "mobile_home": "Mobile home park (preserve, do not demolish)",
    "fragmented_ownership": "Condo/shared-lot stack (many owners; assembly needed)",
}


def resolve_zone(
    parcel: Parcel, adapters: dict[str, ZoningAdapter]
) -> tuple[Optional[ZoneRule], str]:
    adapter = adapters.get(parcel.city or "")
    if adapter is None:
        return None, "not_ingested"
    rule = adapter.lookup(parcel.zoning_code)
    if rule is None:
        return None, "code_not_in_table"
    return rule, ("sample" if rule.is_sample else "ingested")


def build_reason(parcel, units, comps, rcomps, potential, risk, confidence, result_type, zoning_status) -> str:
    """One plain-language paragraph: top drivers, top risk, units, and what is unknown."""
    where = parcel.city or "an unmatched jurisdiction"
    if result_type == "preservation_watch":
        return (f"Mobile home park in {where}: flagged to PRESERVE existing affordable homes, "
                "not as a redevelopment target.")
    label = lambda n: n.replace("_", " ")
    known = sorted((c for c in comps if c.score is not None), key=lambda c: c.score * c.weight, reverse=True)
    pos = [label(c.name) for c in known if c.score >= 0.6][:2]
    weak = [label(c.name) for c in known if c.score <= 0.2][:1]
    parts = [f"Development potential {potential:.0f}/100 in {where}"]
    parts.append("driven by " + " and ".join(pos) if pos else "with no strong positive signal")
    if weak:
        parts.append(f"held back by {weak[0]}")
    txt = ", ".join(parts) + "."
    if units.best_units:
        txt += f" Estimated {units.best_units} units via {units.best_pathway.replace('_', ' ')}."
    elif units.best_units == 0:
        txt += " Zoning is known and no pathway yields housing here."
    else:
        txt += " Unit count unavailable (zoning not ingested or code unmatched)."
    hot = [label(c.name) for c in rcomps if c.score and c.score > 0][:2]
    txt += f" Feasibility risk {risk:.0f}/100" + (f" ({', '.join(hot)})." if hot else " (no flagged constraints).")
    unknown = sum(1 for c in comps if c.score is None)
    txt += f" Confidence {confidence:.0%}" + (f"; {unknown} potential factor(s) unknown." if unknown else ".")
    return txt


def score_parcel(
    parcel: Parcel,
    adapters: dict[str, ZoningAdapter],
    scoring_cfg: dict,
    laws_cfg: dict,
) -> ParcelScore:
    rule, zoning_status = resolve_zone(parcel, adapters)
    units = estimate_units(parcel, rule, laws_cfg)

    # Potential ---------------------------------------------------------
    weights = scoring_cfg["potential_weights"]
    comps: list[Component] = []
    known_w = total_w = weighted = 0.0
    for name, weight in weights.items():
        score, why = COMPONENT_FUNCS[name](parcel, cfg=scoring_cfg, units=units)
        comps.append(Component(name=name, score=score, weight=weight, explanation=why))
        total_w += weight
        if score is not None:
            known_w += weight
            weighted += weight * score
    potential = 100.0 * weighted / known_w if known_w else 0.0
    confidence = known_w / total_w if total_w else 0.0

    # Risk --------------------------------------------------------------
    rw = scoring_cfg["risk_weights"]
    rcomps: list[Component] = []
    risk_total = risk_known = risk_hit = 0.0
    # mobile_home is derivable from land use: leaving it None on every non-park
    # parcel would flood the data-gap report with a field that is not really missing.
    derived_mobile_home = (
        parcel.mobile_home if parcel.mobile_home is not None
        else (None if parcel.land_use is None else parcel.land_use == "mobile_home_park")
    )
    for name, weight in rw.items():
        if name == "fragmented_ownership":
            flag = None if parcel.stack_units is None else parcel.stack_units > 1
        elif name == "mobile_home":
            flag = derived_mobile_home
        else:
            flag = getattr(parcel, name)
        risk_total += weight
        if flag is None:
            rcomps.append(Component(name=name, score=None, weight=weight,
                                    explanation=f"{RISK_LABELS[name]}: unknown."))
            continue
        risk_known += weight
        if flag:
            risk_hit += weight
        rcomps.append(Component(name=name, score=1.0 if flag else 0.0, weight=weight,
                                explanation=f"{RISK_LABELS[name]}: {'YES' if flag else 'no'}."))
    risk = 100.0 * risk_hit / risk_total if risk_total else 0.0
    risk_conf = risk_known / risk_total if risk_total else 0.0

    overall = potential * (1 - scoring_cfg["overall"]["risk_penalty"] * risk / 100.0)

    # Cost per unit (approximate) --------------------------------------
    cost = basis = None
    if units.best_units:
        recent = (parcel.last_sale_year is not None and parcel.last_sale_price
                  and scoring_cfg["current_year"] - parcel.last_sale_year
                  <= scoring_cfg["recent_sale_years"])
        if recent:
            cost, basis = parcel.last_sale_price / units.best_units, \
                f"recent sale ({parcel.last_sale_year})"
        elif parcel.land_value:
            cost, basis = parcel.land_value / units.best_units, \
                "assessed land value (likely below market due to Prop 13)"

    # Caveats and gaps --------------------------------------------------
    caveats, gaps = [], []
    if zoning_status == "not_ingested":
        gaps.append(f"Zoning not yet ingested for {parcel.city or 'unknown jurisdiction'}")
        caveats.append("Zoning not ingested: unit estimates and legal upside are unavailable.")
    elif zoning_status == "code_not_in_table":
        gaps.append(f"Zone code '{parcel.zoning_code}' missing from {parcel.city} rules table")
    elif zoning_status == "sample":
        caveats.append("Zoning rules are SAMPLE values, not real municipal code.")
    if rule is not None and rule.description.startswith("DERIVED"):
        caveats.append("Zone limits are DERIVED from SCAG general-plan density, not the city's municipal code.")
    if parcel.stack_units and parcel.stack_units > 1:
        caveats.append(f"{parcel.stack_units} condo/unit records share this site; redevelopment needs many owners.")
    if not units.laws_verified:
        caveats.append("State-law parameters in config/laws.yaml are unverified.")
    if parcel.is_synthetic:
        caveats.append("SYNTHETIC DEMO PARCEL: not a real property.")
    for c in comps + rcomps:
        if c.score is None:
            gaps.append(f"{c.name}: unknown")

    result_type = "preservation_watch" if (
        parcel.land_use == "mobile_home_park" or parcel.mobile_home) else "development"

    return ParcelScore(
        parcel_id=parcel.parcel_id, result_type=result_type,
        potential=round(potential, 1), risk=round(risk, 1), overall=round(overall, 1),
        confidence=round(confidence, 2), risk_confidence=round(risk_conf, 2),
        components=comps, risk_components=rcomps, units=units,
        land_cost_per_unit=round(cost) if cost else None, price_basis=basis,
        zoning_status=zoning_status, caveats=caveats, data_gaps=gaps,
        reason=build_reason(parcel, units, comps, rcomps, round(potential, 1), round(risk, 1),
                            round(confidence, 2), result_type, zoning_status),
    )
