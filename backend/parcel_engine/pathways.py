"""State-law pathways: which California housing laws may help, or be blocked, on a parcel.

This is a screening aid, not a legal determination. Zoning is not in the data, so every
pathway says what it was based on. Each pathway has one status:

  applies   the data shows the law's main trigger is met
  likely    the trigger is met, but a condition we cannot see in public data still has to be confirmed
  possible  a proxy suggests it may apply (for example commercial land use standing in for zoning)
  blocked   a known exclusion (hazard, historic status) is present, so the pathway probably does not apply

Pathways that could not be evaluated because their dataset is not loaded are listed separately
(`pathways_unchecked`) with the dataset they need, so a missing dataset is never silent.
"""
from __future__ import annotations

import math
import re

import pandas as pd

TRANSIT_HALF_MILE_FT = 2640
CLEANUP_ON_SITE_FT = 50
COMMERCIAL_CODES = {"1460"}  # SCAG 12xx = commercial and services; 1460 = parking / transport facility (verify)


def _isnull(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA


def _true(v) -> bool:
    return (not _isnull(v)) and bool(v)


def _num(v):
    return None if _isnull(v) else float(v)


def _exclusions(g) -> list[str]:
    """Hazards and designations that commonly take a site out of streamlined pathways."""
    out = []
    if _true(g("flood_sfha")):
        out.append("in a FEMA flood hazard area")
    fire = " ".join(str(g(c)) for c in ("fhsz_lra", "fhsz_sra") if not _isnull(g(c))).lower()
    if "very high" in fire:
        out.append("in a Very High fire hazard zone")
    if _true(g("fault_zone")):
        out.append("in an earthquake fault zone")
    if _true(g("nrhp")):
        out.append("a National Register historic property")
    d = _num(g("dist_envirostor_ft"))
    if d is not None and d <= CLEANUP_ON_SITE_FT:
        out.append("on or beside a hazardous-waste cleanup site")
    return out


def _entry(pid, law, name, status, why, basis, caveat):
    return {"id": pid, "law": law, "name": name, "status": status, "why": why, "basis": basis, "caveat": caveat}


def analyze(g, a) -> tuple[list[dict], list[dict]]:
    """g(column) -> parcel value or None; a(dataset_id) -> True when the dataset loaded.

    Returns (pathways, unchecked)."""
    paths: list[dict] = []
    unchecked: list[dict] = []
    excl = _exclusions(g)
    city = g("jurisdiction") or "This city"

    # 1. Streamlined ministerial approval: SB 35 / SB 423 (Gov. Code 65913.4)
    name = "Streamlined ministerial approval"
    law = "SB 35 / SB 423 (Gov. Code 65913.4)"
    if not a("hcd_sb35"):
        unchecked.append({"id": "sb35", "law": law, "name": name,
                          "needs": "HCD's statewide determination of which cities are subject (hcd_sb35)"})
    else:
        s = str(g("sb35_status") or "").lower()
        subject = bool(s) and not ("not subject" in s or s.startswith("exempt") or s.startswith("not "))
        if subject:
            pct = re.search(r"(\d+)\s*%", s)
            share = f"at least {pct.group(1)}% affordable homes" if pct else "a share of affordable homes"
            if excl:
                paths.append(_entry("sb35", law, name, "blocked",
                                    f"{city} is subject to streamlining, but the parcel is {excl[0]}.",
                                    "HCD determination plus hazard layers",
                                    "Streamlining has site exclusions; a qualified review is needed."))
            else:
                paths.append(_entry("sb35", law, name, "likely",
                                    f"{city} is subject to streamlining for projects with {share}. No exclusion found in the hazard layers.",
                                    "HCD determination plus hazard layers",
                                    "Also requires zoning that allows residential use, prevailing wages and other conditions."))

    # 2. Housing on commercial land: AB 2011 and SB 6 (Gov. Code 65912.100 and 65852.24)
    code = str(g("land_use_code") or "").strip()
    if code and (code.startswith("12") or code in COMMERCIAL_CODES):
        law = "AB 2011 and SB 6"
        name = "Housing on commercial, office or parking land"
        if excl:
            paths.append(_entry("commercial", law, name, "blocked",
                                f"Land use {code} looks commercial, but the parcel is {excl[0]}.",
                                "SCAG existing land use (not zoning)", "Both laws exclude hazardous sites."))
        else:
            paths.append(_entry("commercial", law, name, "possible",
                                f"Land use {code} suggests commercial, retail, office or parking use. These laws allow housing on land zoned for those uses.",
                                "SCAG existing land use, a stand-in for zoning",
                                "Zoning must be confirmed. AB 2011 needs affordable homes and prevailing wages; SB 6 has its own rules."))

    # 3. Faith-based land: SB 4 (Gov. Code 65913.16)
    law, name = "SB 4 (Gov. Code 65913.16)", "Housing on faith-based land"
    if not a("osm_worship"):
        unchecked.append({"id": "sb4", "law": law, "name": name, "needs": "places of worship (osm_worship)"})
    elif _true(g("faith_based")):
        if excl:
            paths.append(_entry("sb4", law, name, "blocked", f"Looks like faith-based land, but the parcel is {excl[0]}.",
                                "OpenStreetMap place of worship", "Ownership is not confirmed."))
        else:
            paths.append(_entry("sb4", law, name, "possible",
                                "Looks like land owned by a religious organization. SB 4 allows affordable housing on such land.",
                                "OpenStreetMap place of worship (low confidence)",
                                "Ownership by a religious institution must be confirmed. Homes must be affordable to lower-income households."))

    # 4. Public and surplus land: Surplus Land Act (Gov. Code 54220 and following)
    law, name = "Surplus Land Act (Gov. Code 54220)", "Public and surplus land"
    if not (a("hcd_sla_notices") or a("apr_table_h") or a("dgs_state_land")):
        unchecked.append({"id": "sla", "law": law, "name": name,
                          "needs": "surplus-land notices, APR Table H or state property (hcd_sla_notices, apr_table_h, dgs_state_land)"})
    elif _true(g("sla_notice")):
        paths.append(_entry("sla", law, name, "applies",
                            "An agency has filed a surplus-land notice for this parcel. Affordable housing developers get the first chance to buy or lease it.",
                            "HCD surplus-land notices", "Check the notice for deadlines and the agency's process."))
    elif _true(g("public_surplus")) or _true(g("state_owned")):
        paths.append(_entry("sla", law, name, "likely",
                            "Publicly owned land. Before an agency sells or leases surplus land it must first offer it for affordable housing.",
                            "APR Table H or state property inventory", "The agency has to declare the land surplus first."))

    # 5. Parking reform: AB 2097 (Gov. Code 65863.2)
    rail = _num(g("dist_rail_ft"))
    if _true(g("in_hqta")) or (rail is not None and rail <= TRANSIT_HALF_MILE_FT):
        paths.append(_entry("parking", "AB 2097 (Gov. Code 65863.2)", "No parking minimums near transit", "likely",
                            "Within about half a mile of high-quality transit. Cities cannot require minimum parking for housing here.",
                            "SCAG transit corridors, buffered half a mile",
                            "The law uses a legal definition of major transit stop. The corridor data is an approximation."))

    # 6. State Density Bonus Law (Gov. Code 65915): any project that includes affordable homes
    if not _isnull(g("lot_sqft")):
        paths.append(_entry("density", "State Density Bonus Law (Gov. Code 65915)", "Density bonus", "applies",
                            "A project that sets aside affordable homes can ask for more homes than the zoning allows, plus fewer parking spaces and waivers of some standards.",
                            "Applies to any housing project with affordable homes", "The size of the bonus depends on the share and depth of affordability."))

    # 7. Housing Element site or rezone site
    if not a("scag_he_sites"):
        unchecked.append({"id": "he", "law": "Housing Element law (Gov. Code 65583.2)", "name": "Listed in the city's Housing Element",
                          "needs": "SCAG Housing Element sites (scag_he_sites)"})
    elif _true(g("he_site")) or _true(g("he_rezone")):
        rez = _true(g("he_rezone"))
        paths.append(_entry("he", "Housing Element law (Gov. Code 65583.2)", "Listed in the city's Housing Element",
                            "applies",
                            f"{city} has listed this parcel as a " + ("rezone site, which the city has committed to rezone for housing." if rez
                                                                    else "site where housing can be built to meet its state housing target."),
                            "SCAG compilation of HCD Housing Element site inventories",
                            "Rezone sites are not usable until the city completes the rezoning."))

    # 8. Builder's remedy (Housing Accountability Act, Gov. Code 65589.5)
    law, name = "Housing Accountability Act (Gov. Code 65589.5)", "Builder's remedy"
    if not a("hcd_compliance"):
        unchecked.append({"id": "builders_remedy", "law": law, "name": name,
                          "needs": "HCD Housing Element compliance status (hcd_compliance)"})
    else:
        he = str(g("he_status") or "").lower()
        if he and ("out of compliance" in he or "not in compliance" in he or "due" in he):
            paths.append(_entry("builders_remedy", law, name, "likely",
                                f"{city}'s Housing Element is not in compliance. Qualifying affordable projects can proceed even where zoning doesn't allow them.",
                                "HCD compliance report", "Requires a qualifying project and a pending application."))

    # 9. Notice and first-offer rules for expiring affordable housing (Gov. Code 65863.10 and following)
    law, name = "Preservation notice rules (Gov. Code 65863.10)", "Existing affordable housing at risk"
    if not (a("hud_lihtc") or a("hud_mf_s8") or a("hcd_mobilehome_parks")):
        unchecked.append({"id": "preservation", "law": law, "name": name,
                          "needs": "HUD tax-credit and Section 8 lists, HCD mobile home parks (hud_lihtc, hud_mf_s8, hcd_mobilehome_parks)"})
    near = [k for k, lab in (("dist_lihtc_ft", "tax-credit housing"), ("dist_s8_ft", "Section 8 housing"),
                             ("dist_mhp_ft", "a mobile home park")) if (_num(g(k)) is not None and _num(g(k)) <= CLEANUP_ON_SITE_FT)]
    if near:
        label = {"dist_lihtc_ft": "tax-credit housing", "dist_s8_ft": "Section 8 housing", "dist_mhp_ft": "a mobile home park"}[near[0]]
        paths.append(_entry("preservation", law, name, "possible",
                            f"The parcel has or touches {label}. Owners must give notice before affordability ends, and qualified buyers can get a first chance to buy.",
                            "HUD and HCD property lists", "Affordability end dates are not in the data yet."))
    return paths, unchecked
