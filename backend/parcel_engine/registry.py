"""Dataset registry: one record per source.

Each record documents source URL, license, publisher refresh date and (at run
time) ingest date. It also tells the loader how to fetch the data and the join
engine how to attach it to parcels, so adding a source is a registry edit.

`license_verified` / `refresh_verified` are False where the value has not been
checked against the publisher's page. Phase 1 exit requires every record to be
verified; `phase1_gaps()` lists what is left.

access:
  arcgis_rest  queried live from an ArcGIS REST layer (url is the layer)
  file         read from data/raw/<local_file>; download from landing_url
  census_api   Census Data API (url is the API base)
  pdf_dir      folder of PDFs under data/raw/<local_file>
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = DATA_DIR / "registry_state.json"

PUBLIC_DOMAIN = "Public domain (U.S. Government work)"
ODBL = "ODbL 1.0 (attribution + share-alike)"
OCGIS_TERMS = "OC Survey / OCGIS public data; terms of use on ocgis.com"
CA_PUBLIC = "California public record; state open-data terms"
SCAG_TERMS = "SCAG Open Data terms of use"

OCGIS = "https://www.ocgis.com/arcpub/rest/services/Map_Layers"
TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"

DATASETS: list[dict] = [
    # ---------------- Base geography ----------------
    dict(id="ocgis_parcels", name="OCGIS Parcels", signals=["Lot size", "Year built"],
         access="arcgis_rest", url=f"{OCGIS}/Parcels/FeatureServer/0",
         landing_url="https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer",
         license=OCGIS_TERMS, license_verified=False,
         refresh_date="Not published on layer (no editingInfo.lastEditDate)", refresh_verified=False,
         notes="Fields: OBJECTID, SITE_ADDRESS, ASSESSMENT_NO (APN), YEAR_BUILT, NBR_BEDROOMS. "
               "No use code, assessed value or owner name. See docs/describe_layer_report.md."),
    dict(id="ocgis_city_boundaries", name="OCGIS City Boundaries", signals=["Jurisdiction"],
         access="arcgis_rest", url=f"{OCGIS}/City_Boundaries/MapServer/0",
         landing_url=f"{OCGIS}/City_Boundaries/MapServer",
         license=OCGIS_TERMS, license_verified=False,
         refresh_date="verify at ingest", refresh_verified=False,
         notes="Fields JURISDICTI, CITY. Areas outside every polygon are tagged Unincorporated."),
    dict(id="ocgis_unincorporated", name="OCGIS Unincorporated Area", signals=["Jurisdiction", "Valid OC ZIP"],
         access="arcgis_rest", url=f"{OCGIS}/Unincorporated_Area/MapServer/0",
         landing_url=f"{OCGIS}/Unincorporated_Area/MapServer",
         license=OCGIS_TERMS, license_verified=False, refresh_date="verify at ingest", refresh_verified=False,
         notes="With city boundaries, defines the county footprint used to validate OC ZIPs."),
    dict(id="census_zcta", name="Census 2020 ZCTA (TIGERweb)", signals=["ZIP selection"],
         access="arcgis_rest", url=f"{TIGERWEB}/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7",
         landing_url="https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html",
         license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="2020 Census vintage", refresh_verified=True,
         notes="Layer 7 = Census 2020 ZCTAs. Field GEOID = 5-digit ZCTA."),
    dict(id="census_tracts", name="Census tracts (TIGERweb)", signals=["Tract join key"],
         access="arcgis_rest", url=f"{TIGERWEB}/Tracts_Blocks/MapServer/0",
         landing_url="https://tigerweb.geo.census.gov/tigerwebmain/TIGERweb_main.html",
         license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="Current TIGERweb vintage", refresh_verified=False,
         notes="Tract GEOID used to join ACS, LODES, Opportunity Zones. Confirm layer 0 is tracts."),
    dict(id="ocgis_building_footprints", name="OCGIS Building Footprints", signals=["Building coverage"],
         access="arcgis_rest", url=f"{OCGIS}/Building_Footprints/FeatureServer/0",
         landing_url=f"{OCGIS}/Building_Footprints/FeatureServer",
         license=OCGIS_TERMS, license_verified=False,
         refresh_date="verify at ingest", refresh_verified=False,
         notes="Default footprint source because it is bbox-queryable. Overture/Microsoft are file "
               "alternatives (set FOOTPRINT_SOURCE)."),
    dict(id="overture_buildings", name="Overture Maps buildings", signals=["Building coverage"],
         access="file", local_file="overture_buildings_oc.parquet",
         url="https://docs.overturemaps.org/guides/buildings/",
         landing_url="https://overturemaps.org/download/",
         license="ODbL 1.0 (buildings theme)", license_verified=False,
         refresh_date="Monthly Overture release; record release id at ingest", refresh_verified=False),
    dict(id="ocgis_centerlines", name="OCGIS Street Centerlines", signals=["Frontage"],
         access="arcgis_rest", url=f"{OCGIS}/Street_Centerlines_With_Labels/FeatureServer/0",
         landing_url=f"{OCGIS}/Street_Centerlines_With_Labels/FeatureServer",
         license=OCGIS_TERMS, license_verified=False, refresh_date="verify at ingest", refresh_verified=False,
         notes="Used for frontage. If unavailable, frontage falls back to the short side of the "
               "parcel's minimum rotated rectangle (flagged frontage_method=mrr_estimate)."),
    dict(id="scag_land_use", name="SCAG parcel land use", signals=["Land use code"],
         access="file", local_file="scag_land_use_oc.gpkg",
         url="https://gisdata-scag.opendata.arcgis.com/", landing_url="https://gisdata-scag.opendata.arcgis.com/",
         license=SCAG_TERMS, license_verified=False, refresh_date="2019 annual land use (verify)",
         refresh_verified=False,
         join=dict(type="attr_at_point", fields={"land_use_code": ["LU19", "LU_CODE", "SCAG_LU", "LU"]}),
         notes="Replaces the missing OCGIS use code. Code meanings in scoring.LAND_USE_UNDERUSED (verify)."),

    # ---------------- Housing policy ----------------
    dict(id="scag_he_sites", name="SCAG 6th Cycle Housing Element sites inventory", signals=["Housing Element site"],
         access="file", local_file="scag_he_sites_6th.gpkg",
         url="https://gisdata-scag.opendata.arcgis.com/", landing_url="https://scag.ca.gov/housing-element-parcel-tool",
         license=SCAG_TERMS, license_verified=False, refresh_date="6th Cycle (2021-2029); verify",
         refresh_verified=False, join=dict(type="flag_intersects", column="he_site")),
    dict(id="scag_he_rezone", name="SCAG 6th Cycle Housing Element rezone sites", signals=["Housing Element site"],
         access="file", local_file="scag_he_rezone_6th.gpkg",
         url="https://gisdata-scag.opendata.arcgis.com/", landing_url="https://scag.ca.gov/housing-element-parcel-tool",
         license=SCAG_TERMS, license_verified=False, refresh_date="6th Cycle; verify", refresh_verified=False,
         join=dict(type="flag_intersects", column="he_rezone")),
    dict(id="hcd_compliance", name="HCD Housing Element Compliance Report", signals=["HE compliance"],
         access="file", local_file="hcd_he_compliance.csv",
         url="https://www.hcd.ca.gov/planning-and-community-development/housing-elements",
         landing_url="https://www.hcd.ca.gov/planning-and-community-development/housing-elements",
         license=CA_PUBLIC, license_verified=False, refresh_date="Updated continuously; record pull date",
         refresh_verified=False,
         join=dict(type="jurisdiction_table", key=["Jurisdiction", "JURISDICTION", "jurisdiction"],
                   fields={"he_status": ["Status", "STATUS", "Compliance Status", "status"]})),
    dict(id="hcd_sb35", name="HCD SB 35 statewide determination", signals=["SB 35"],
         access="file", local_file="hcd_sb35_determination.csv",
         url="https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process",
         landing_url="https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process",
         license=CA_PUBLIC, license_verified=False, refresh_date="Annual determination; verify year",
         refresh_verified=False,
         join=dict(type="jurisdiction_table", key=["Jurisdiction", "JURISDICTION", "jurisdiction"],
                   fields={"sb35_status": ["Determination", "SB35", "Status", "sb35_status"]})),
    dict(id="apr_table_h", name="HCD APR Table H (locally owned surplus sites)", signals=["Public land"],
         access="file", local_file="apr_table_h.csv",
         url="https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
         landing_url="https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
         license=CA_PUBLIC, license_verified=False, refresh_date="Annual APR cycle; verify", refresh_verified=False,
         join=dict(type="apn_list", key=["APN", "apn", "PARCEL_ID"], column="public_surplus")),
    dict(id="hcd_sla_notices", name="HCD Surplus Land Act notices", signals=["Public land"],
         access="file", local_file="hcd_sla_notices.csv",
         url="https://www.hcd.ca.gov/planning-and-community-development/public-lands",
         landing_url="https://www.hcd.ca.gov/planning-and-community-development/public-lands",
         license=CA_PUBLIC, license_verified=False, refresh_date="verify", refresh_verified=False,
         join=dict(type="apn_list", key=["APN", "apn"], column="sla_notice")),
    dict(id="dgs_state_land", name="DGS state-owned land", signals=["Public land"],
         access="file", local_file="dgs_state_owned.gpkg",
         url="https://www.dgs.ca.gov/RESD", landing_url="https://www.dgs.ca.gov/RESD",
         license=CA_PUBLIC, license_verified=False, refresh_date="verify", refresh_verified=False,
         join=dict(type="flag_intersects", column="state_owned")),
    dict(id="osm_worship", name="OSM places of worship", signals=["Faith-based (SB 4)"],
         access="file", local_file="osm_places_of_worship_oc.geojson",
         url="https://download.geofabrik.de/north-america/us/california/socal.html",
         landing_url="https://www.openstreetmap.org/copyright",
         license=ODBL, license_verified=True, refresh_date="Geofabrik daily extract; record extract date",
         refresh_verified=False, low_confidence=True,
         join=dict(type="flag_intersects", column="faith_based"),
         notes="Low confidence: OSM tags the use, not the owner. Parcels flagged here are capped at Low."),
    dict(id="oc_tax_defaulted", name="OC Treasurer tax-defaulted parcels (PDF)", signals=["Tax-defaulted"],
         access="pdf_dir", local_file="oc_treasurer_pdfs",
         url="https://www.octreasurer.gov/", landing_url="https://www.octreasurer.gov/",
         license="County public record", license_verified=False, refresh_date="Per auction list; record PDF date",
         refresh_verified=False, low_confidence=True,
         join=dict(type="apn_list", key=["apn"], column="tax_defaulted"),
         notes="Parsed separately by parcel_engine.tax_default into data/cache/tax_defaulted_apns.csv."),

    # ---------------- Access ----------------
    dict(id="scag_hqta", name="SCAG High Quality Transit Areas", signals=["Transit (HQTA)"],
         access="file", local_file="scag_hqta.gpkg",
         url="https://gisdata-scag.opendata.arcgis.com/", landing_url="https://gisdata-scag.opendata.arcgis.com/",
         license=SCAG_TERMS, license_verified=False, refresh_date="Connect SoCal 2024 HQTA (verify)",
         refresh_verified=False, join=dict(type="flag_intersects", column="in_hqta")),
    dict(id="octa_gtfs", name="OCTA GTFS stops", signals=["Transit stops"],
         access="file", local_file="octa_gtfs.zip",
         url="https://www.octa.net/about/about-octa/doing-business-with-octa/gtfs/",
         landing_url="https://www.octa.net/", license="OCTA GTFS license (verify)", license_verified=False,
         refresh_date="Per service change; read feed_info.txt", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_bus_stop_ft", gtfs=True)),
    dict(id="metrolink_gtfs", name="Metrolink GTFS stops", signals=["Transit stops"],
         access="file", local_file="metrolink_gtfs.zip",
         url="https://metrolinktrains.com/about/gtfs/", landing_url="https://metrolinktrains.com/",
         license="Metrolink GTFS license (verify)", license_verified=False,
         refresh_date="Per service change; read feed_info.txt", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_rail_ft", gtfs=True)),
    dict(id="lodes_wac", name="Census LEHD LODES8 WAC (jobs by workplace)", signals=["Jobs access"],
         access="file", local_file="ca_wac_S000_JT00_2022.csv.gz",
         url="https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_2022.csv.gz",
         landing_url="https://lehd.ces.census.gov/data/", license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="LODES8, 2022 job year", refresh_verified=False,
         join=dict(type="tract_table", source="lodes", column="tract_jobs"),
         notes="Block-level C000 summed to tract (first 11 digits of w_geocode)."),
    dict(id="cde_schools", name="CDE public schools", signals=["Schools"],
         access="file", local_file="pubschls.txt",
         url="https://www.cde.ca.gov/ds/si/ds/pubschls.asp", landing_url="https://www.cde.ca.gov/ds/si/ds/pubschls.asp",
         license=CA_PUBLIC, license_verified=False, refresh_date="Updated daily; record download date",
         refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_school_ft", lat=["Latitude"], lon=["Longitude"])),
    dict(id="osm_grocery", name="OSM/Overture grocery stores", signals=["Grocery"],
         access="file", local_file="osm_grocery_oc.geojson",
         url="https://download.geofabrik.de/north-america/us/california/socal.html",
         landing_url="https://www.openstreetmap.org/copyright", license=ODBL, license_verified=True,
         refresh_date="Record extract date", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_grocery_ft")),

    # ---------------- Opportunity & need ----------------
    dict(id="tcac_opportunity", name="TCAC/HCD Opportunity Map", signals=["Opportunity area"],
         access="file", local_file="tcac_opportunity_map.gpkg",
         url="https://www.treasurer.ca.gov/ctcac/opportunity.asp", landing_url="https://www.treasurer.ca.gov/ctcac/opportunity.asp",
         license=CA_PUBLIC, license_verified=False, refresh_date="Annual map; record map year",
         refresh_verified=False,
         join=dict(type="attr_at_point", fields={"tcac_category": ["oppcat", "OPPCAT", "Category", "category"]})),
    dict(id="acs5", name="ACS 5-year (rent burden, median household income)", signals=["Rent burden / income"],
         access="census_api", url="https://api.census.gov/data/2023/acs/acs5",
         landing_url="https://www.census.gov/programs-surveys/acs", license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="2019-2023 ACS 5-year (released Dec 2024)", refresh_verified=False,
         join=dict(type="tract_table", source="acs", column="acs")),
    dict(id="hud_income_limits", name="HUD income limits (Orange County AMI)", signals=["AMI"],
         access="file", local_file="hud_income_limits.csv",
         url="https://www.huduser.gov/portal/datasets/il.html", landing_url="https://www.huduser.gov/portal/datasets/il.html",
         license=PUBLIC_DOMAIN, license_verified=True, refresh_date="FY income limits; record FY",
         refresh_verified=False, notes="County-level constant; used to express tract income as % AMI."),
    dict(id="calenviroscreen4", name="CalEnviroScreen 4.0", signals=["Environmental burden"],
         access="file", local_file="calenviroscreen40.gpkg",
         url="https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-40",
         landing_url="https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-40",
         license=CA_PUBLIC, license_verified=False, refresh_date="Oct 2021 (version 4.0)", refresh_verified=False,
         join=dict(type="attr_at_point", fields={"ces_percentile": ["CIscoreP", "CIscore_P", "ces_percentile"]})),
    dict(id="cdfi_oz", name="CDFI Fund Opportunity Zones tract list", signals=["Opportunity Zone"],
         access="file", local_file="opportunity_zones.csv",
         url="https://www.cdfifund.gov/opportunity-zones", landing_url="https://www.cdfifund.gov/opportunity-zones",
         license=PUBLIC_DOMAIN, license_verified=True, refresh_date="2018 designations", refresh_verified=False,
         join=dict(type="tract_table", source="oz", column="in_oz", key=["GEOID", "Census Tract Number", "geoid"])),

    # ---------------- Hazards ----------------
    dict(id="fema_nfhl", name="FEMA National Flood Hazard Layer (flood zones)", signals=["Hazards"],
         access="arcgis_rest", url="https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28",
         landing_url="https://www.fema.gov/flood-maps/national-flood-hazard-layer", license=PUBLIC_DOMAIN,
         license_verified=True, refresh_date="Continuously updated; record query date", refresh_verified=True,
         join=dict(type="flag_intersects", column="flood_sfha", where="SFHA_TF = 'T'")),
    dict(id="calfire_fhsz_lra", name="CAL FIRE FHSZ (LRA, OCGIS mirror)", signals=["Hazards"],
         access="arcgis_rest", url=f"{OCGIS}/Fire_Hazard_Severity_Zones_LRA/MapServer/0",
         landing_url="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones",
         license=CA_PUBLIC, license_verified=False, refresh_date="2025 LRA maps (verify mirror vintage)",
         refresh_verified=False,
         join=dict(type="attr_at_point", fields={"fhsz_lra": ["HAZ_CLASS", "FHSZ_Description", "HAZ_CODE", "FHSZ"]})),
    dict(id="calfire_fhsz_sra", name="CAL FIRE FHSZ (SRA, OCGIS mirror)", signals=["Hazards"],
         access="arcgis_rest", url=f"{OCGIS}/Fire_Hazard_Severity_Zones_SRA/MapServer/0",
         landing_url="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones",
         license=CA_PUBLIC, license_verified=False, refresh_date="2023 SRA maps (verify mirror vintage)",
         refresh_verified=False,
         join=dict(type="attr_at_point", fields={"fhsz_sra": ["HAZ_CLASS", "FHSZ_Description", "HAZ_CODE", "FHSZ"]})),
    dict(id="cgs_liquefaction", name="CGS liquefaction zones (OCGIS mirror)", signals=["Hazards"],
         access="arcgis_rest", url=f"{OCGIS}/Liquefaction/MapServer/0",
         landing_url="https://www.conservation.ca.gov/cgs/sh/program", license=CA_PUBLIC, license_verified=False,
         refresh_date="verify", refresh_verified=False, join=dict(type="flag_intersects", column="liquefaction")),
    dict(id="cgs_fault_zones", name="CGS Alquist-Priolo fault zones", signals=["Hazards"],
         access="file", local_file="cgs_ap_fault_zones.gpkg",
         url="https://www.conservation.ca.gov/cgs/alquist-priolo", landing_url="https://www.conservation.ca.gov/cgs/alquist-priolo",
         license=CA_PUBLIC, license_verified=False, refresh_date="verify", refresh_verified=False,
         join=dict(type="flag_intersects", column="fault_zone")),
    dict(id="coastal_zone", name="Coastal Zone boundary (OCGIS mirror of CCC)", signals=["Hazards"],
         access="arcgis_rest", url=f"{OCGIS}/Coastal_Zone/MapServer/0",
         landing_url="https://www.coastal.ca.gov/maps/czb/", license=CA_PUBLIC, license_verified=False,
         refresh_date="verify", refresh_verified=False, join=dict(type="flag_intersects", column="coastal_zone")),
    dict(id="calgem_wells", name="CalGEM oil and gas wells", signals=["Hazards"],
         access="file", local_file="calgem_wells.csv",
         url="https://www.conservation.ca.gov/calgem/maps", landing_url="https://www.conservation.ca.gov/calgem/maps",
         license=CA_PUBLIC, license_verified=False, refresh_date="Updated weekly; record download date",
         refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_oil_well_ft", lat=["Latitude", "LAT"], lon=["Longitude", "LON"])),
    dict(id="dtsc_envirostor", name="DTSC EnviroStor sites", signals=["Hazards"],
         access="file", local_file="envirostor_sites.csv",
         url="https://www.envirostor.dtsc.ca.gov/public/data_download", landing_url="https://www.envirostor.dtsc.ca.gov/public/",
         license=CA_PUBLIC, license_verified=False, refresh_date="Record download date", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_envirostor_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"])),
    dict(id="geotracker", name="Water Board GeoTracker cleanup sites", signals=["Hazards"],
         access="file", local_file="geotracker_sites.csv",
         url="https://geotracker.waterboards.ca.gov/data_download", landing_url="https://geotracker.waterboards.ca.gov/",
         license=CA_PUBLIC, license_verified=False, refresh_date="Record download date", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_geotracker_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"])),
    dict(id="nrhp", name="National Register of Historic Places", signals=["Hazards"],
         access="file", local_file="nrhp.gpkg",
         url="https://www.nps.gov/subjects/nationalregister/data-downloads.htm",
         landing_url="https://www.nps.gov/subjects/nationalregister/data-downloads.htm",
         license=PUBLIC_DOMAIN, license_verified=True, refresh_date="verify", refresh_verified=False,
         join=dict(type="flag_intersects", column="nrhp")),

    # ---------------- Preservation ----------------
    dict(id="hcd_mobilehome_parks", name="HCD mobilehome park list", signals=["Preservation"],
         access="file", local_file="hcd_mobilehome_parks.csv",
         url="https://www.hcd.ca.gov/manufactured-and-mobilehomes/mobilehome-parks",
         landing_url="https://www.hcd.ca.gov/manufactured-and-mobilehomes", license=CA_PUBLIC,
         license_verified=False, refresh_date="verify", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_mhp_ft", lat=["Latitude", "LATITUDE"], lon=["Longitude", "LONGITUDE"])),
    dict(id="hud_lihtc", name="HUD LIHTC database", signals=["Preservation"],
         access="file", local_file="LIHTCPUB.csv",
         url="https://www.huduser.gov/portal/datasets/lihtc.html", landing_url="https://www.huduser.gov/portal/datasets/lihtc.html",
         license=PUBLIC_DOMAIN, license_verified=True, refresh_date="Annual release; record placed-in-service year",
         refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_lihtc_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"])),
    dict(id="hud_mf_s8", name="HUD Multifamily Section 8 contracts", signals=["Preservation"],
         access="file", local_file="hud_mf_section8.csv",
         url="https://www.hud.gov/program_offices/housing/mfh/exp/mfhdiscl",
         landing_url="https://www.hud.gov/program_offices/housing/mfh/exp/mfhdiscl", license=PUBLIC_DOMAIN,
         license_verified=True, refresh_date="Monthly; record download date", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_s8_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"])),

    # ---------------- Validation ----------------
    dict(id="apr_table_a2", name="HCD APR Table A2 (building activity by APN)", signals=["Validation"],
         access="file", local_file="apr_table_a2.csv",
         url="https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
         landing_url="https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
         license=CA_PUBLIC, license_verified=False, refresh_date="Annual APR cycle; record report years",
         refresh_verified=False),
]

BY_ID = {d["id"]: d for d in DATASETS}


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def stamp_ingest(dataset_id: str, when: str | None = None, extra: dict | None = None) -> None:
    """Record that a dataset was ingested (REST query date or local file date)."""
    state = _load_state()
    rec = state.get(dataset_id, {})
    rec["ingest_date"] = when or date.today().isoformat()
    if extra:
        rec.update(extra)
    state[dataset_id] = rec
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def records() -> list[dict]:
    """Registry records merged with ingest state. One record per source."""
    state = _load_state()
    out = []
    for d in DATASETS:
        rec = {k: v for k, v in d.items() if k != "join"}
        rec["ingest_date"] = state.get(d["id"], {}).get("ingest_date")
        rec["ingest_detail"] = {k: v for k, v in state.get(d["id"], {}).items() if k != "ingest_date"} or None
        out.append(rec)
    return out


def phase1_gaps() -> list[dict]:
    """What blocks the Phase 1 'every dataset documented' requirement."""
    gaps = []
    for r in records():
        missing = [k for k in ("url", "license", "refresh_date") if not r.get(k)]
        unverified = [k for k in ("license", "refresh_date") if not r.get(f"{k.split('_')[0]}_verified")]
        if missing or unverified or not r["ingest_date"]:
            gaps.append(dict(id=r["id"], missing=missing, unverified=unverified,
                             never_ingested=not r["ingest_date"]))
    return gaps
