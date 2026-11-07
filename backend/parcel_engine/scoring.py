"""Development Potential, Feasibility Risk, Opportunity Score, confidence, reasons.

See docs/scoring.md for the method in prose. All weights live here.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

# ---------------- Confidence ----------------
# Ten signals, matching the front end's "N of 10 signals" display.
SIGNALS = ["Lot size", "Building coverage", "Year built", "Land use code", "Housing Element status",
           "Transit access", "Jobs access", "Opportunity area", "Rent burden / income", "Hazard layers"]
LEVEL_RULES = [(9, "High"), (7, "Medium"), (5, "Low"), (0, "Insufficient")]
LOW_CONFIDENCE_PENALTY = 0.5  # each low-confidence input that is true for the parcel costs half a signal

# ---------------- Development Potential ----------------
CORE_WEIGHTS = {"lot": 25, "coverage": 25, "transit": 15, "jobs": 10, "opportunity": 10,
                "land_use": 8, "age": 4, "amenities": 3}
BONUS_POINTS = {"he": 15, "public": 10, "faith": 5, "sb35": 3, "he_noncompliant": 2, "tax_defaulted": 2}

# SCAG existing land use codes treated as underused for housing. VERIFY against the
# SCAG land use code book before relying on them.
LAND_USE_UNDERUSED = {
    "1200": "commercial and services", "1210": "retail / commercial services", "1220": "other commercial",
    "1460": "surface parking / transportation facility", "1500": "commercial and industrial mixed",
    "1900": "urban vacant", "3000": "vacant",
}

# ---------------- Feasibility Risk ----------------
RISK_POINTS = {"flood": 20, "fire_very_high": 20, "fire_high": 12, "fire_moderate": 5, "liquefaction": 10,
               "fault": 15, "coastal": 10, "oil_on": 15, "oil_near": 8, "contam_on": 15, "contam_near": 6,
               "nrhp": 15, "small_lot": 10, "narrow": 5, "preservation": 20, "env_burden": 5}
RISK_DAMPING = 0.7  # Opportunity = DP x (1 - 0.7 x Risk/100)
# A Low-confidence score stands on thin data, so it is discounted. 0.66 keeps the result at or below 66,
# i.e. never in the High band (67+), while preserving the order of parcels. Keep in sync with the front end.
LOW_CONFIDENCE_OPP_FACTOR = 0.66


def level_for(effective: float) -> str:
    for n, lvl in LEVEL_RULES:
        if effective >= n:
            return lvl
    return "Insufficient"


def band(x: float, kind: str = "dp") -> str:
    if kind == "risk":
        return "High risk" if x >= 50 else "Moderate risk" if x >= 20 else "Low risk"
    return "High" if x >= 67 else "Medium" if x >= 34 else "Low"


def _isnull(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA


def _true(v) -> bool:
    return (not _isnull(v)) and bool(v)


def _pct_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True, method="average")


def _fmt_acres(acres: float, sqft: float) -> str:
    return f"{acres:.2f} acres ({sqft:,.0f} sq ft)"


def _fire_class(*vals) -> str | None:
    s = " ".join(str(v).lower() for v in vals if not _isnull(v))
    if not s:
        return None
    if "very high" in s or s.strip() in ("3", "vh"):
        return "very_high"
    if "high" in s or s.strip() == "2":
        return "high"
    if "moderate" in s or s.strip() == "1":
        return "moderate"
    return None


def score(p: pd.DataFrame, avail: dict[str, bool]) -> pd.DataFrame:
    p = p.copy()
    a = lambda k: bool(avail.get(k))
    lot_pr = _pct_rank(p["lot_sqft"])
    cov_pr = _pct_rank(p["building_coverage"]) if p["building_coverage"].notna().any() else pd.Series(np.nan, index=p.index)
    jobs_pr = _pct_rank(p["tract_jobs"]) if "tract_jobs" in p and p["tract_jobs"].notna().any() else pd.Series(np.nan, index=p.index)
    hazards_ok = a("fema_nfhl") and (a("calfire_fhsz_lra") or a("calfire_fhsz_sra")) and a("cgs_liquefaction")

    rows = []
    for i, r in p.iterrows():
        g = r.get
        # ---- confidence ----
        found = {
            "Lot size": not _isnull(g("lot_sqft")) and g("lot_sqft") > 0,
            "Building coverage": not _isnull(g("building_coverage")),
            "Year built": not _isnull(g("year_built")) or _true(g("vacant")),
            "Land use code": not _isnull(g("land_use_code")),
            "Housing Element status": a("scag_he_sites"),
            "Transit access": a("scag_hqta") or not _isnull(g("dist_bus_stop_ft")) or not _isnull(g("dist_rail_ft")),
            "Jobs access": not _isnull(g("tract_jobs")),
            "Opportunity area": not _isnull(g("tcac_category")),
            "Rent burden / income": not _isnull(g("rent_burden_share")) or not _isnull(g("median_hh_income")),
            "Hazard layers": hazards_ok,
        }
        missing = [s for s in SIGNALS if not found[s]]
        n_found = len(SIGNALS) - len(missing)
        low_inputs = []
        if _true(g("faith_based")):
            low_inputs.append("Faith-based parcel (OSM place of worship; ownership not confirmed)")
        if _true(g("tax_defaulted")):
            low_inputs.append("Tax-defaulted status (parsed from Treasurer PDF)")
        effective = n_found - LOW_CONFIDENCE_PENALTY * len(low_inputs)
        level = level_for(effective)
        cap_reason = None
        if _true(g("faith_based")) and level in ("High", "Medium"):
            level, cap_reason = "Low", "Capped at Low: SB 4 faith-based parcel identified from OSM, not ownership records."

        # ---- development potential ----
        core, contrib = {}, []  # contrib: (points, dir, short phrase, long sentence)
        if found["Lot size"]:
            acres = g("lot_acres")
            f = min(max((math.log10(max(acres, 1e-4)) - math.log10(0.1)) / (math.log10(2) - math.log10(0.1)), 0), 1)
            core["lot"] = f
            cmp = "larger" if lot_pr[i] >= 0.5 else "smaller"
            share = lot_pr[i] if cmp == "larger" else 1 - lot_pr[i]
            contrib.append(("lot", f, "up" if f >= 0.4 else "down", f"{acres:.2f} acre lot",
                            f"Lot size {_fmt_acres(acres, g('lot_sqft'))} — {cmp} than {share:.0%} of lots in this ZIP."))
        if found["Building coverage"]:
            cov = g("building_coverage")
            f = 1.0 if _true(g("vacant")) else 1 - min(cov / 0.5, 1)
            core["coverage"] = f
            if _true(g("vacant")):
                contrib.append(("coverage", f, "up", "vacant (no building footprint)",
                                "Vacant — no building footprint on the parcel."))
            else:
                cmp = "lower" if cov_pr[i] <= 0.5 else "higher"
                share = 1 - cov_pr[i] if cmp == "lower" else cov_pr[i]
                contrib.append(("coverage", f, "up" if f >= 0.5 else "down", f"{cov:.0%} building coverage",
                                f"Building coverage {cov:.0%} — {cmp} than {share:.0%} of parcels in this ZIP."))
        if found["Transit access"]:
            if _true(g("in_hqta")):
                f, ph = 1.0, "inside HQTA"
                txt = "Inside a High Quality Transit Area — frequent transit nearby."
            elif not _isnull(g("dist_rail_ft")) and g("dist_rail_ft") <= 2640:
                f, ph = 0.8, f"{g('dist_rail_ft') / 5280:.1f} mi to rail"
                txt = f"Rail station {g('dist_rail_ft') / 5280:.1f} mi away — within a half mile."
            elif not _isnull(g("dist_bus_stop_ft")) and g("dist_bus_stop_ft") <= 1320:
                f, ph = 0.5, "bus stop within 1/4 mi"
                txt = f"Bus stop {g('dist_bus_stop_ft'):,.0f} ft away — within a quarter mile."
            else:
                f, ph = 0.0, "no frequent transit"
                txt = "Outside HQTA and no stop within a quarter mile — weak transit access."
            core["transit"] = f
            contrib.append(("transit", f, "up" if f >= 0.5 else "down", ph, txt))
        if found["Jobs access"] and not _isnull(jobs_pr[i]):
            f = float(jobs_pr[i])
            core["jobs"] = f
            contrib.append(("jobs", f, "up" if f >= 0.5 else "down", f"{g('tract_jobs'):,.0f} jobs in tract",
                            f"Jobs in tract {g('tract_jobs'):,.0f} — {'more' if f >= 0.5 else 'fewer'} than most parcels in this ZIP."))
        if found["Opportunity area"]:
            cat = str(g("tcac_category"))
            f = 1.0 if "high" in cat.lower() else 0.5 if "moderate" in cat.lower() else 0.0
            core["opportunity"] = f
            contrib.append(("opportunity", f, "up" if f >= 0.5 else "down", f"TCAC {cat}",
                            f"TCAC/HCD opportunity area: {cat}."))
        if found["Land use code"]:
            code = str(g("land_use_code")).split(".")[0]
            label = LAND_USE_UNDERUSED.get(code)
            core["land_use"] = 1.0 if label else 0.0
            if label:
                contrib.append(("land_use", 1.0, "up", label, f"Land use {code} ({label}) — common redevelopment candidate."))
        if not _isnull(g("year_built")):
            yb = int(g("year_built"))
            core["age"] = 1.0 if yb < 1980 else 0.0
            contrib.append(("age", core["age"], "up" if yb < 1980 else "down", f"built {yb}",
                            f"Built {yb} — {'older than 1980' if yb < 1980 else 'built 1980 or later'}."))
        amen = []
        for col, nm in (("dist_grocery_ft", "grocery"), ("dist_school_ft", "school")):
            if not _isnull(g(col)):
                amen.append(1.0 if g(col) <= 2640 else 0.0)
        if amen:
            core["amenities"] = sum(amen) / len(amen)

        wsum = sum(CORE_WEIGHTS[k] for k in core)
        dp_core = 100 * sum(CORE_WEIGHTS[k] * v for k, v in core.items()) / wsum if wsum else None
        bonus = []
        if _true(g("he_site")) or _true(g("he_rezone")):
            bonus.append(("he", "Housing Element " + ("rezone site" if _true(g("he_rezone")) else "site")))
        if _true(g("public_surplus")) or _true(g("sla_notice")) or _true(g("state_owned")):
            bonus.append(("public", "publicly owned / surplus land"))
        if _true(g("faith_based")):
            bonus.append(("faith", "faith-based parcel (SB 4, low confidence)"))
        sb35 = str(g("sb35_status") or "").lower()
        if "subject" in sb35 or "10%" in sb35 or "50%" in sb35:
            bonus.append(("sb35", "jurisdiction subject to SB 35"))
        he_status = str(g("he_status") or "").lower()
        if he_status and ("out of compliance" in he_status or "not in compliance" in he_status or "due" in he_status):
            bonus.append(("he_noncompliant", "jurisdiction out of HE compliance (builder's remedy watch)"))
        if _true(g("tax_defaulted")):
            bonus.append(("tax_defaulted", "tax-defaulted (low confidence)"))
        dp = None if dp_core is None else min(100.0, dp_core + sum(BONUS_POINTS[k] for k, _ in bonus))

        # ---- feasibility risk ----
        risk_items = []  # (points, phrase)
        if _true(g("flood_sfha")):
            risk_items.append((RISK_POINTS["flood"], "FEMA Special Flood Hazard Area"))
        fire = _fire_class(g("fhsz_lra"), g("fhsz_sra"))
        if fire:
            risk_items.append((RISK_POINTS[f"fire_{fire}"], f"{fire.replace('_', ' ').title()} fire hazard zone"))
        if _true(g("liquefaction")):
            risk_items.append((RISK_POINTS["liquefaction"], "liquefaction zone"))
        if _true(g("fault_zone")):
            risk_items.append((RISK_POINTS["fault"], "Alquist-Priolo fault zone"))
        if _true(g("coastal_zone")):
            risk_items.append((RISK_POINTS["coastal"], "Coastal Zone (CDP required)"))
        w = g("dist_oil_well_ft")
        if not _isnull(w) and w <= 100:
            risk_items.append((RISK_POINTS["oil_on"], "oil/gas well on or at parcel"))
        elif not _isnull(w) and w <= 500:
            risk_items.append((RISK_POINTS["oil_near"], f"oil/gas well {w:,.0f} ft away"))
        cd = np.nanmin([v for v in (g("dist_envirostor_ft"), g("dist_geotracker_ft")) if not _isnull(v)] or [np.nan])
        if not _isnull(cd) and cd <= 250:
            risk_items.append((RISK_POINTS["contam_on"], "cleanup site on or next to parcel"))
        elif not _isnull(cd) and cd <= 1000:
            risk_items.append((RISK_POINTS["contam_near"], f"cleanup site {cd:,.0f} ft away"))
        if _true(g("nrhp")):
            risk_items.append((RISK_POINTS["nrhp"], "National Register historic property"))
        if found["Lot size"] and g("lot_sqft") < 5000:
            risk_items.append((RISK_POINTS["small_lot"], f"small lot ({g('lot_sqft'):,.0f} sq ft)"))
        if not _isnull(g("frontage_ft")) and 0 < g("frontage_ft") < 40:
            risk_items.append((RISK_POINTS["narrow"], f"narrow frontage (~{g('frontage_ft'):.0f} ft)"))
        pres = [nm for col, nm in (("dist_mhp_ft", "mobile home park"), ("dist_lihtc_ft", "LIHTC property"),
                                   ("dist_s8_ft", "Section 8 property")) if not _isnull(g(col)) and g(col) <= 50]
        if pres:
            risk_items.append((RISK_POINTS["preservation"], f"existing {pres[0]} — preservation, not redevelopment"))
        if not _isnull(g("ces_percentile")) and float(g("ces_percentile")) >= 75:
            risk_items.append((RISK_POINTS["env_burden"], f"CalEnviroScreen {float(g('ces_percentile')):.0f}th percentile"))
        risk = min(100.0, float(sum(pts for pts, _ in risk_items))) if found["Lot size"] else None
        risk_items.sort(key=lambda x: -x[0])

        # ---- opportunity ----
        scored = level != "Insufficient" and dp is not None
        opp = round(dp * (1 - RISK_DAMPING * risk / 100)) if scored else None
        discounted = scored and level == "Low"
        if discounted:
            opp = round(opp * LOW_CONFIDENCE_OPP_FACTOR)

        # ---- reasons ----
        ups = sorted([c for c in contrib if c[2] == "up"], key=lambda c: -CORE_WEIGHTS[c[0]] * c[1])
        downs = sorted([c for c in contrib if c[2] == "down"], key=lambda c: -CORE_WEIGHTS[c[0]] * (1 - c[1]))
        dp_phrases = [b[1] for b in bonus] + [c[3] for c in ups]
        dp_reason = None if dp is None else (
            f"{band(dp)}: " + (", ".join(dp_phrases[:3]) if dp_phrases else
                               ", ".join(c[3] for c in downs[:3]) or "few positive signals") + ".")
        risk_phrases = [ph for _, ph in risk_items]
        missing_hazard = [n for ok, n in ((a("fema_nfhl"), "flood"),
                                          (a("calfire_fhsz_lra") or a("calfire_fhsz_sra"), "fire"),
                                          (a("cgs_liquefaction"), "liquefaction")) if not ok]
        risk_reason = None if risk is None else (
            f"{band(risk, 'risk')}: " + (", ".join(risk_phrases[:3]) if risk_phrases else "no hazard or constraint flags found")
            + (f" ({', '.join(missing_hazard)} data unavailable)" if missing_hazard else "") + ".")
        opp_reason = (f"{band(opp)}: development potential {dp:.0f}"
                      + (f", reduced by feasibility risk {risk:.0f}" if risk else ", no risk deductions")
                      + (", then discounted because confidence is Low" if discounted else "") + "."
                      ) if scored else f"Not scored: {n_found} of {len(SIGNALS)} signals found."

        reasons = [{"dir": "up", "score": "development_potential", "text": f"{ph[0].upper()}{ph[1:]} — adds to development potential."}
                   for _, ph in bonus]
        reasons += [{"dir": "up", "score": "development_potential", "text": c[4]} for c in ups]
        reasons += [{"dir": "down", "score": "feasibility_risk", "text": f"{ph[0].upper()}{ph[1:]} — raises feasibility risk (+{pts})."}
                    for pts, ph in risk_items]
        reasons += [{"dir": "down", "score": "development_potential", "text": c[4]} for c in downs]

        rows.append({
            "sig": n_found, "signals_total": len(SIGNALS), "level": level, "confidence_cap": cap_reason,
            "missing": missing, "low_confidence_inputs": low_inputs,
            "development_potential": None if dp is None or not scored else round(dp),
            "feasibility_risk": None if risk is None or not scored else round(risk),
            "opp": opp,
            "dev_reason": dp_reason if scored else None, "risk_reason": risk_reason if scored else None,
            "opp_reason": opp_reason, "reasons": reasons[:5],
        })
    return pd.concat([p.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
