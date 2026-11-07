"""Write the dataset catalog (docs/DATASETS.md + docs/datasets.csv) from the registry.

Run: python -m parcel_engine.cli catalog
"""
from __future__ import annotations

import csv
from pathlib import Path

from . import registry

REPO = Path(__file__).resolve().parents[2]
RAW = registry.DATA_DIR / "raw"


def _in_repo(d: dict) -> bool:
    return d["access"] == "file" and (RAW / d.get("local_file", "")).is_file()

CATEGORIES = [
    ("Base geography", ["ocgis_parcels", "ocgis_city_boundaries", "ocgis_unincorporated", "census_zcta",
                        "census_tracts", "ocgis_building_footprints", "overture_buildings", "ocgis_centerlines", "ocgis_address_points",
                        "scag_land_use"]),
    ("Housing policy", ["scag_he_sites", "scag_he_rezone", "hcd_compliance", "hcd_sb35", "apr_table_h",
                        "hcd_sla_notices", "dgs_state_land", "osm_worship", "oc_tax_defaulted"]),
    ("Access", ["scag_hqta", "octa_gtfs", "metrolink_gtfs", "lodes_wac", "cde_schools", "osm_grocery"]),
    ("Opportunity and need", ["tcac_opportunity", "acs5", "hud_income_limits", "calenviroscreen4", "cdfi_oz"]),
    ("Hazards and constraints", ["fema_nfhl", "calfire_fhsz_lra", "calfire_fhsz_sra", "cgs_liquefaction",
                                 "cgs_fault_zones", "coastal_zone", "calgem_wells", "dtsc_envirostor",
                                 "geotracker", "nrhp"]),
    ("Preservation", ["hcd_mobilehome_parks", "hud_lihtc", "hud_mf_s8"]),
    ("Validation", ["apr_table_a2"]),
]

ACCESS = {
    "arcgis_rest": "Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.",
    "census_api": "Pulled live from the Census Data API for Orange County tracts and cached.",
    "file": "Manual download. Save as `backend/data/raw/{local_file}`.",
    "pdf_dir": "Manual download. Put the PDFs in `backend/data/raw/{local_file}/`, then run "
               "`python -m parcel_engine.cli parse-tax-pdfs`.",
}

USE = {
    "flag_intersects": "Parcel gets `{column}` = true if it overlaps any feature{where}.",
    "attr_at_point": "Parcel takes {fields} from the polygon containing its interior point.",
    "nearest_distance": "Parcel gets `{column}`: feet to the nearest feature (capped at 3 miles).",
    "tract_table": "Joined by Census tract to give {what}.",
    "apn_list": "Parcel gets `{column}` = true if its APN is on the list.",
    "jurisdiction_table": "Joined by city / unincorporated to give {fields}.",
}
TRACT_WHAT = {"acs": "`median_hh_income` and `rent_burden_share`", "lodes": "`tract_jobs`", "oz": "`in_oz`"}
SPECIAL_USE = {
    "ocgis_parcels": "Defines the parcels. APN, address and year built come from here; lot size, frontage and "
                     "buildable area are computed from the polygon.",
    "ocgis_city_boundaries": "Tags each parcel with the city containing its interior point; flags parcels split by a city line.",
    "ocgis_unincorporated": "With city boundaries, defines the county footprint used to reject non-OC ZIPs.",
    "census_zcta": "The ZIP polygon. A parcel belongs to the ZIP containing its interior point.",
    "census_tracts": "Gives each parcel a tract GEOID for the ACS, LODES and Opportunity Zone joins.",
    "ocgis_building_footprints": "Footprint area inside the parcel ÷ lot area = building coverage; no footprint = vacant.",
    "overture_buildings": "Alternative footprint source (set FOOTPRINT_SOURCE=overture_buildings).",
    "ocgis_address_points": "Fills blank parcel addresses from the address point inside the parcel, else the nearest within 150 ft.",
    "ocgis_centerlines": "Frontage = parcel edge within 60 ft of a centerline.",
    "lodes_wac": "Block-level jobs (C000) summed to tract to give `tract_jobs`.",
    "hud_income_limits": "Not joined yet. Reserved for expressing tract income as % of AMI.",
    "apr_table_a2": "Not a scoring input. Permitted APNs are compared with scores (lift, AUC).",
}


def _use(d: dict) -> str:
    if d["id"] in SPECIAL_USE:
        return SPECIAL_USE[d["id"]]
    j = d.get("join") or {}
    t = j.get("type")
    if not t:
        return "-"
    fields = ", ".join(f"`{f}`" for f in j.get("fields", {}))
    where = f" where {j['where']}" if j.get("where") else ""
    return USE[t].format(column=j.get("column", ""), fields=fields, where=where,
                         what=TRACT_WHAT.get(j.get("source"), ""))


def _yes(b) -> str:
    return "yes" if b else "**no**"


def write(md_path: Path | None = None, csv_path: Path | None = None) -> tuple[Path, Path]:
    md_path = md_path or REPO / "docs" / "DATASETS.md"
    csv_path = csv_path or REPO / "docs" / "datasets.csv"
    by_id = registry.BY_ID
    listed = [i for _, ids in CATEGORIES for i in ids]
    missing = set(by_id) - set(listed)
    assert not missing, f"datasets missing from catalog categories: {missing}"

    n = len(registry.DATASETS)
    lic_ok = sum(bool(d["license_verified"]) for d in registry.DATASETS)
    ref_ok = sum(bool(d["refresh_verified"]) for d in registry.DATASETS)
    live = sum(d["access"] in ("arcgis_rest", "census_api") for d in registry.DATASETS)
    stored = [d for d in registry.DATASETS if _in_repo(d)]

    lines = [
        "# Dataset catalog",
        "",
        "Every input to the parcel screener, one entry per source. Generated from "
        "`backend/parcel_engine/registry.py` by `python -m parcel_engine.cli catalog`; edit the registry, "
        "not this file. A machine-readable copy is in [`datasets.csv`](datasets.csv).",
        "",
        "Most data files are not stored in this repo. They are either queried live by the backend or downloaded "
        "into `backend/data/raw/`. Files already committed there are marked *In repo* below.",
        "",
        "## Status",
        "",
        f"- {n} datasets: {live} pulled live by the backend, {len(stored)} committed in `backend/data/raw/` "
        f"({', '.join(d['id'] for d in stored) or 'none'}), {n - live - len(stored)} still need a manual download.",
        f"- License checked against the publisher: {lic_ok} of {n}.",
        f"- Refresh date checked against the publisher: {ref_ok} of {n}.",
        f"- Source (publisher, URL, vintage) checked on {registry.SOURCE_CHECKED_ON}: "
        f"{sum(bool(d['source_checked_on']) for d in registry.DATASETS)} of {n}.",
        "- Authority: **original** = the agency responsible for the data, serving it itself; **compiler** = a public "
        "agency compiling other governments' records (SCAG); **community** = OpenStreetMap, used only where the "
        "project plan calls for it and always low confidence; **consortium** = Overture, alternative only. "
        "No dataset is read from a third-party mirror.",
        "- Phase 1 requires every source documented with source, license and refresh date. Rows marked "
        "**no** under *Verified* still need someone to open the publisher's page and confirm.",
        "- Ingest date is recorded per run in `backend/data/registry_state.json` and served by `GET /registry`.",
        "",
        "## Summary",
        "",
        "| Dataset | Publisher (authority) | Signal(s) | Access | License | Refresh | Verified (license / refresh) |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, ids in CATEGORIES:
        for i in ids:
            d = by_id[i]
            lines.append(f"| [{d['name']}](#{i.replace('_', '-')}) | {d['publisher']} ({d['authority']}) | "
                         f"{', '.join(d['signals'])} | {'in repo' if _in_repo(d) else d['access']} | "
                         f"{d['license']} | {d['refresh_date']} | {_yes(d['license_verified'])} / {_yes(d['refresh_verified'])} |")
    for cat, ids in CATEGORIES:
        lines += ["", f"## {cat}"]
        for i in ids:
            d = by_id[i]
            access = ACCESS[d["access"]].format(local_file=d.get("local_file", ""))
            if _in_repo(d):
                access = f"**In repo:** `backend/data/raw/{d['local_file']}`."
            lines += [
                "", f"### {i.replace('_', '-')}", "", f"**{d['name']}**", "",
                f"- **Publisher:** {d['publisher']} (authority: {d['authority']})",
                f"- **Source checked against publisher:** {d['source_checked_on'] or '**not yet**'}",
                f"- **Signals:** {', '.join(d['signals'])}",
                f"- **Source URL:** {d['url']}",
                f"- **Publisher page:** {d['landing_url']}",
                f"- **License:** {d['license']} (verified: {_yes(d['license_verified'])})",
                f"- **Refresh date:** {d['refresh_date']} (verified: {_yes(d['refresh_verified'])})",
                f"- **How to get it:** {access}",
                f"- **How it's used:** {_use(d)}",
            ]
            if d.get("low_confidence"):
                lines.append("- **Low confidence:** a parcel flagged by this source loses half a signal of confidence.")
            if d.get("notes"):
                lines.append(f"- **Notes:** {d['notes']}")
    lines += [
        "", "## Removed signals (no free, legal, county-wide dataset)", "",
        "Code enforcement and vacant/foreclosure registries; long-term vacancy (HUD/USPS, restricted); absentee "
        "owners (needs owner mailing addresses); frequent transfers and sale prices (paid data); methane zones; "
        "local historic designations; displacement risk index; state at-risk housing list (CHPC, by request).",
        "", "## Conditional signals cut after describe_layer", "",
        "The OCGIS parcel layer has no use code, assessed values or owner name "
        "(see [`backend/docs/describe_layer_report.md`](../backend/docs/describe_layer_report.md)). Land use comes "
        "from SCAG instead; improvement-to-land ratio and land cost per unit are removed; owner type is limited to "
        "public ownership from Table H, SLA notices and DGS. Airport compatibility zones and city zoning are not ingested.",
        "",
    ]
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines))

    cols = ["id", "category", "name", "publisher", "authority", "source_checked_on", "signals", "access", "url", "landing_url", "local_file", "license",
            "license_verified", "refresh_date", "refresh_verified", "low_confidence", "how_used", "notes"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for cat, ids in CATEGORIES:
            for i in ids:
                d = by_id[i]
                w.writerow({"id": i, "category": cat, "name": d["name"], "publisher": d["publisher"],
                            "authority": d["authority"], "source_checked_on": d["source_checked_on"] or "",
                            "signals": "; ".join(d["signals"]),
                            "access": "in_repo" if _in_repo(d) else d["access"], "url": d["url"], "landing_url": d["landing_url"],
                            "local_file": d.get("local_file", ""), "license": d["license"],
                            "license_verified": d["license_verified"], "refresh_date": d["refresh_date"],
                            "refresh_verified": d["refresh_verified"], "low_confidence": bool(d.get("low_confidence")),
                            "how_used": _use(d), "notes": d.get("notes", "")})
    return md_path, csv_path
