"""Turn raw pulls (tools/pull_real_zip.py) into scoreable SITES.

Why this exists (found by inspecting real data, 2026-11-07):
  ~30% of OC parcel rows are condo units / shared-lot stacks. They repeat ONE polygon many
  times (e.g. 521 S LYON ST units 1..N). SCAG does not match them by APN. Scoring each row as
  a separate "parcel" would put dozens of identical dots on the map and rank condo buildings
  as redevelopment targets. So we collapse rows with identical geometry into one SITE,
  sum the values, keep the unit count (stack_units), and let scoring treat it as fragmented
  ownership risk.

Also derives per-city zone rules from SCAG general-plan max density (clearly marked DERIVED).

  python tools/build_real_sites.py 92701 92805 92627 92780
"""
import csv, hashlib, json, re, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]

# SCAG LU24 -> this tool's land_use. Only codes whose meaning was confirmed from SCAG's published
# description or is a hundred-level family are mapped. Everything else is reported, not guessed.
# VERIFY against SCAG's "Land Use Code Description" document before relying on these.
LU_MAP = {
    "1110": "single_family", "1111": "single_family", "1112": "single_family", "1113": "single_family",
    "1150": "single_family",
    "1120": "multifamily", "1121": "multifamily", "1122": "multifamily", "1123": "multifamily", "1124": "multifamily",
    "1130": "mobile_home_park",   # UNVERIFIED: recalled as mobile home & trailer parks
    "1200": "commercial_other", "1210": "commercial_other", "1211": "commercial_other",
    "1220": "commercial_other", "1222": "commercial_other", "1223": "commercial_other",
    "1620": "commercial_other",   # commercial-oriented residential / mixed use
    "1272": "vacant", "1275": "vacant", "1900": "vacant",
    "1300": "industrial", "1310": "industrial", "1311": "industrial",
}
MIN_LOT_SQFT = 1500   # smaller pieces are slivers / ROW remnants, not buildable sites


def num(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def geom_key(g):
    return hashlib.md5(json.dumps(g["coordinates"], separators=(",", ":")).encode()).hexdigest()


def main(zips):
    sites, report = [], {}
    for z in zips:
        feats = json.load(open(ROOT / f"data/parcels_in/real_{z}.geojson"))["features"]
        groups = defaultdict(list)
        for f in feats:
            groups[geom_key(f["geometry"])].append(f)
        r = Counter(rows_in=len(feats), sites_formed=len(groups))
        unmapped = Counter()
        for rows in groups.values():
            props = [x["properties"] for x in rows]
            lot_type = props[0]["LotType"]
            area = props[0]["Shape__Area"]          # sq ft (state plane)
            if lot_type != "Lot":
                r["dropped_row_or_rail"] += 1; continue
            addr = (props[0]["SiteAddress"] or "").upper()
            if re.search(r"\b(FWY|FREEWAY|HWY|HIGHWAY)\b", addr):
                r["dropped_freeway_row"] += 1; continue   # Caltrans right-of-way posing as vacant land
            if area < MIN_LOT_SQFT:
                r["dropped_sliver"] += 1; continue
            rep = next((p for p in props if p["zoning_code"]), props[0])   # row that SCAG matched
            lu = rep["lu24"]
            land_use = LU_MAP.get(lu) if lu else None
            if lu and not land_use:
                unmapped[lu] += 1
            lv = [num(p["LandVal"]) for p in props]; iv = [num(p["ImprovedVal"]) for p in props]
            sites.append({"type": "Feature", "geometry": rows[0]["geometry"], "properties": {
                "apn": rep["AssessmentNo"], "address": rep["SiteAddress"], "zip": z,
                "lot_sqft": round(area), "use_code": lu, "land_use": land_use,
                "land_value": sum(x for x in lv if x is not None) if any(x is not None for x in lv) else None,
                "improvement_value": sum(x for x in iv if x is not None) if any(x is not None for x in iv) else None,
                "zoning_code": rep["zoning_code"], "city_scag": rep["city_scag"],
                "gp_den_max": rep["gp_den_max"], "gp_far_max": rep["gp_far_max"],
                "housing_element_site": True if any(p["he_site"] for p in props) else None,
                "stack_units": len(props)}})
            r["sites_kept"] += 1
        report[z] = {**r, "unmapped_lu24": dict(unmapped.most_common(8))}
    out = ROOT / "data/parcels_in/real_sites.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": sites}))

    # derived zone rules: per (city, zone): median positive GP max density + majority category
    by = defaultdict(list)
    for s in sites:
        p = s["properties"]
        if p["city_scag"] and p["zoning_code"]:
            by[(p["city_scag"], p["zoning_code"])].append(p)
    rows = []
    for (city, zone), ps in sorted(by.items()):
        dens = [p["gp_den_max"] for p in ps if (p["gp_den_max"] or 0) > 0]
        d = round(st.median(dens), 1) if len(dens) >= max(3, len(ps) * 0.5) else None
        lus = Counter(p["land_use"] for p in ps if p["land_use"]).most_common(1)
        top = lus[0][0] if lus else None
        cat = {"single_family": "residential_low", "multifamily": "residential_multi",
               "commercial_other": "commercial", "industrial": "industrial"}.get(top, "other")
        if cat == "residential_low" and d and d > 14:
            cat = "residential_multi"
        rows.append([("Unincorporated Orange County" if city == "Unincorporated" else city), zone,
                     f"DERIVED from SCAG GP max density; n={len(ps)} sites", cat, d, "", "", "",
                     "https://maps.scag.ca.gov/scaggis/rest/services/LDX/GeneralPlan_poly_OR/MapServer/0",
                     "2026-11-07", ""])
    (ROOT / "data/zoning_real").mkdir(exist_ok=True)
    hdr = ["city", "zone_code", "description", "category", "max_density_du_ac", "max_height_ft",
           "min_lot_sqft", "parking_per_unit", "source_url", "retrieved", "is_sample"]
    with open(ROOT / "data/zoning_real/derived_scag_gp.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(hdr); w.writerows(rows)
    report["derived_zone_rules"] = len(rows)
    report["derived_rules_with_density"] = sum(1 for r in rows if r[4] != "")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:] or ["92701", "92805", "92627", "92780"])
