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
         access="arcgis_rest", url=f"{OCGIS}/Parcels/MapServer/0",
         landing_url="https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/MapServer",
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
         access="arcgis_rest", url=f"{OCGIS}/Building_Footprints/MapServer/0",
         landing_url=f"{OCGIS}/Building_Footprints/MapServer",
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
    dict(id="scag_land_use", name="SCAG 2024 Existing Land Use, Orange County", signals=["Land use code"],
         access="arcgis_rest", url="https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_OR/MapServer/0",
         landing_url="https://gisdata-scag.opendata.arcgis.com/",
         license=SCAG_TERMS, license_verified=False,
         refresh_date="2024 Annual Land Use, released June 2025 (on 2024 parcels, March 2025)", refresh_verified=True,
         join=dict(type="attr_at_point", fields={"land_use_code": ["LU24", "LU_24", "LU19", "LU_CODE", "LU"]}),
         notes="Replaces the missing OCGIS use code. Served by SCAG itself. Confirm the 2024 code field name on first "
               "live run; code meanings in scoring.LAND_USE_UNDERUSED still need checking against SCAG's code book."),
    dict(id="scag_he_sites", name="SCAG Region 6th Cycle Housing Element Sites (Table A)", signals=["Housing Element site"],
         access="arcgis_rest", url="https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer/0",
         landing_url="https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer",
         license=SCAG_TERMS, license_verified=False,
         refresh_date="HCD sites inventory forms retrieved by SCAG October 2025 (168 jurisdictions)", refresh_verified=True,
         join=dict(type="flag_intersects", column="he_site"),
         notes="Underlying data is HCD's Electronic Housing Element Sites Inventory Form (Table A), compiled by SCAG."),
    dict(id="scag_he_rezone", name="SCAG Region 6th Cycle Housing Element Rezone Sites (Table B)", signals=["Housing Element site"],
         access="arcgis_rest", url="https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementRezone_poly_scag/MapServer/0",
         landing_url="https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementRezone_poly_scag/MapServer",
         license=SCAG_TERMS, license_verified=False,
         refresh_date="HCD sites inventory forms retrieved by SCAG October 2025", refresh_verified=True,
         join=dict(type="flag_intersects", column="he_rezone"),
         notes="Underlying data is HCD's sites inventory form Table B (candidate sites to be rezoned)."),
    dict(id="hcd_compliance", name="HCD Housing Element Review and Compliance Report", signals=["HE compliance"],
         access="file", local_file="hcd_he_compliance.csv",
         url="https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/housing-element-review-and-compliance-report",
         landing_url="https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/housing-element-review-and-compliance-report",
         license=CA_PUBLIC, license_verified=False, refresh_date="Updated continuously; record pull date",
         refresh_verified=False,
         join=dict(type="jurisdiction_table", key=["Jurisdiction", "JURISDICTION", "jurisdiction"],
                   fields={"he_status": ["Status", "STATUS", "Compliance Status", "status"]})),
    dict(id="hcd_sb35", name="HCD SB 423 (formerly SB 35) Streamlined Ministerial Approval statewide determination",
         signals=["SB 35 / SB 423"],
         access="file", local_file="hcd_sb423_determination.csv",
         url="https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/sb423-determination-summary.pdf",
         landing_url="https://www.hcd.ca.gov/planning-and-community-development/statutory-determinations",
         license=CA_PUBLIC, license_verified=False,
         refresh_date="Annual HCD determination; record the determination date printed on the PDF", refresh_verified=False,
         join=dict(type="jurisdiction_table", key=["Jurisdiction", "JURISDICTION", "jurisdiction"],
                   fields={"sb35_status": ["Determination", "SB423", "SB35", "Status", "sb35_status"]}),
         notes="SB 423 (2023) replaced the SB 35 determination; HCD now publishes the SB 423 summary. It is a PDF: "
               "convert to CSV with columns Jurisdiction, Determination (Not subject / 10% / 50%)."),
    dict(id="apr_table_h", name="HCD APR Table H (locally owned surplus sites)", signals=["Public land"],
         access="file", local_file="apr_table_h.csv",
         url="https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
         landing_url="https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year",
         license=CA_PUBLIC, license_verified=False, refresh_date="Annual APR cycle (reports due April 1); record report years",
         refresh_verified=False,
         join=dict(type="apn_list", key=["APN", "apn", "PARCEL_ID"], column="public_surplus"),
         notes="Published by HCD (contact APR@hcd.ca.gov) on the state open data portal."),
    dict(id="hcd_sla_notices", name="HCD Surplus Land Act notices", signals=["Public land"],
         access="file", local_file="hcd_sla_notices.csv",
         url="https://www.hcd.ca.gov/planning-and-community-development/public-lands",
         landing_url="https://www.hcd.ca.gov/planning-and-community-development/public-lands",
         license=CA_PUBLIC, license_verified=False, refresh_date="verify", refresh_verified=False,
         join=dict(type="apn_list", key=["APN", "apn"], column="sla_notice")),
    dict(id="dgs_state_land", name="DGS Statewide Property Inventory (state-owned real property)", signals=["Public land"],
         access="file", local_file="dgs_state_owned.gpkg",
         url="https://catalog.data.gov/dataset/realproperty",
         landing_url="https://www.dgs.ca.gov/RESD/Resources/Page-Content/Real-Estate-Services-Division-Resources-List-Folder/Statewide-Property-Inventory",
         license="No license stated by DGS (state public record)", license_verified=True,
         refresh_date="Updated annually by agencies; RealProperty last modified 2025-10-22", refresh_verified=True,
         join=dict(type="flag_intersects", column="state_owned"),
         notes="Excludes Caltrans highway right of way and some security-sensitive sites (Gov Code 11011)."),
    dict(id="osm_worship", name="OSM places of worship", signals=["Faith-based (SB 4)"],
         access="file", local_file="osm_places_of_worship_oc.geojson",
         url="https://download.geofabrik.de/north-america/us/california/socal.html",
         landing_url="https://www.openstreetmap.org/copyright",
         license=ODBL, license_verified=True, refresh_date="Geofabrik daily extract; record extract date",
         refresh_verified=False, low_confidence=True,
         join=dict(type="flag_intersects", column="faith_based"),
         notes="Low confidence: OSM tags the use, not the owner. Parcels flagged here are capped at Low."),
    dict(id="oc_tax_defaulted", name="OC Treasurer-Tax Collector tax-defaulted property lists (PDF)", signals=["Tax-defaulted"],
         access="pdf_dir", local_file="oc_treasurer_pdfs",
         url="https://www.octreasurer.gov/taxdefaultedproperty", landing_url="https://www.octreasurer.gov/taxauction",
         license="County public notice (published under Rev. & Tax. Code 3371 / 3702)", license_verified=True,
         refresh_date="Delinquency list published each September (latest seen: executed Sept 2, 2025); "
                      "auction Exhibit I each spring", refresh_verified=True, low_confidence=True,
         join=dict(type="apn_list", key=["apn"], column="tax_defaulted"),
         notes="Parsed separately by parcel_engine.tax_default into data/cache/tax_defaulted_apns.csv. "
               "Lists change daily as parcels are redeemed; treat as a snapshot."),
    dict(id="scag_hqta", name="SCAG High Quality Transit Areas", signals=["Transit (HQTA)"],
         access="file", local_file="scag_hqta.gpkg",
         url="https://gisdata-scag.opendata.arcgis.com/", landing_url="https://gisdata-scag.opendata.arcgis.com/",
         license=SCAG_TERMS, license_verified=False,
         refresh_date="Use Connect SoCal 2024 base-year (2022) HQTA; SCAG updates every 4 years", refresh_verified=False,
         join=dict(type="flag_intersects", column="in_hqta"),
         notes="SCAG serves the 2024 base-year HQTC lines live (OpenData/HQTC_Year_2022) but I could not find the "
               "matching HQTA polygon service, so this stays a download from SCAG's portal. Do not use the RTP2020 layers."),
    dict(id="octa_gtfs", name="OCTA GTFS stops", signals=["Transit stops"],
         access="file", local_file="octa_gtfs.zip",
         url="https://www.octa.net/current/google_transit.zip",
         landing_url="https://octa.net/about/about-octa/open-data",
         license="OCTA open data terms: free use, OCTA retains ownership, no warranty", license_verified=True,
         refresh_date="Quarterly service changes; read feed_info.txt / calendar.txt", refresh_verified=True,
         join=dict(type="nearest_distance", column="dist_bus_stop_ft", gtfs=True)),
    dict(id="metrolink_gtfs", name="Metrolink GTFS stops", signals=["Transit stops"],
         access="file", local_file="metrolink_gtfs.zip",
         url="https://metrolinktrains.com/globalassets/about/gtfs/gtfs.zip",
         landing_url="https://metrolinktrains.com/about/gtfs/",
         license="Metrolink: provided as is, no liability", license_verified=True,
         refresh_date="Updated with schedule changes (about 5 times a year)", refresh_verified=True,
         join=dict(type="nearest_distance", column="dist_rail_ft", gtfs=True)),
    dict(id="lodes_wac", name="Census LEHD LODES8 WAC (jobs by workplace)", signals=["Jobs access"],
         access="file", local_file="ca_wac_S000_JT00_2022.csv.gz",
         url="https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_2022.csv.gz",
         landing_url="https://lehd.ces.census.gov/data/#lodes", license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="Committed file is job year 2022; LODES 8.4 (Dec 18, 2025) adds 2023", refresh_verified=True,
         join=dict(type="tract_table", source="lodes", column="tract_jobs"),
         notes="Block-level C000 summed to tract (first 11 digits of w_geocode). To move to 2023, download "
               "ca_wac_S000_JT00_2023.csv.gz and change local_file and url."),
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
    dict(id="tcac_opportunity", name="CTCAC/HCD Opportunity Map (2026)", signals=["Opportunity area"],
         access="file", local_file="tcac_opportunity_map_2026.gpkg",
         url="https://www.treasurer.ca.gov/ctcac/opportunity.asp", landing_url="https://www.treasurer.ca.gov/ctcac/opportunity.asp",
         license=CA_PUBLIC, license_verified=False, refresh_date="2026 map, adopted December 2025 (annual)",
         refresh_verified=True,
         join=dict(type="attr_at_point", fields={"tcac_category": ["oppcat", "OPPCAT", "Category", "category"]}),
         notes="Published by the State Treasurer's CTCAC with HCD. Shapefile is linked from the page above."),
    dict(id="acs5", name="ACS 5-year 2020-2024 (rent burden, median household income)", signals=["Rent burden / income"],
         access="census_api", url="https://api.census.gov/data/2024/acs/acs5",
         landing_url="https://www.census.gov/programs-surveys/acs/news/data-releases/2024/release.html",
         license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="2020-2024 ACS 5-year, released January 29, 2026", refresh_verified=True,
         join=dict(type="tract_table", source="acs", column="acs")),
    dict(id="hud_income_limits", name="HUD FY2026 income limits (Orange County AMI)", signals=["AMI"],
         access="file", local_file="hud_income_limits_fy2026.csv",
         url="https://www.huduser.gov/portal/datasets/il.html", landing_url="https://www.huduser.gov/portal/datasets/il.html",
         license=PUBLIC_DOMAIN, license_verified=True, refresh_date="FY2026, effective May 1, 2026",
         refresh_verified=True, notes="County-level constant; used to express tract income as % AMI."),
    dict(id="calenviroscreen4", name="CalEnviroScreen 5.0 (OEHHA)", signals=["Environmental burden"],
         access="file", local_file="calenviroscreen50.gpkg",
         url="https://gis.data.ca.gov/datasets/OEHHA::calenviroscreen-5-0",
         landing_url="https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-50",
         license="OEHHA conditions of use", license_verified=False,
         refresh_date="CalEnviroScreen 5.0, final released July 2026 (replaces 4.0, Oct 2021)", refresh_verified=True,
         join=dict(type="attr_at_point", fields={"ces_percentile": ["CIscoreP", "CIscore_Pctl", "CIscorePctl",
                                                                    "CES5_Pctl", "ces_percentile"]}),
         notes="Use the final 5.0 release, not the January 2026 draft. Confirm the percentile field name in the "
               "5.0 data dictionary."),
    dict(id="cdfi_oz", name="Treasury/CDFI Fund Qualified Opportunity Zones (2026 list)", signals=["Opportunity Zone"],
         access="file", local_file="opportunity_zones_2026.csv",
         url="https://www.cdfifund.gov/media/8018881/download?inline",
         landing_url="https://www.cdfifund.gov/opportunity-zones",
         license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="2026 designations announced Nov 5, 2026 (2018 list superseded)", refresh_verified=True,
         join=dict(type="tract_table", source="oz", column="in_oz", key=["GEOID", "Census Tract Number", "geoid"]),
         notes="Check the effective date of the 2026 designations against the 2018 list before relying on it."),
    dict(id="fema_nfhl", name="FEMA National Flood Hazard Layer (flood zones)", signals=["Hazards"],
         access="arcgis_rest", url="https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28",
         landing_url="https://www.fema.gov/flood-maps/national-flood-hazard-layer", license=PUBLIC_DOMAIN,
         license_verified=True, refresh_date="Continuously updated; record query date", refresh_verified=True,
         join=dict(type="flag_intersects", column="flood_sfha", where="SFHA_TF = 'T'"),
         notes="FEMA's own service. Its robots.txt blocked my automated metadata check, so confirm layer 28 is "
               "'Flood Hazard Zones' on first live run."),
    dict(id="calfire_fhsz_lra", name="CAL FIRE OSFM Fire Hazard Severity Zones, LRA (2025)", signals=["Hazards"],
         access="file", local_file="fhsz_lra_2025.zip",
         url="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones",
         landing_url="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones",
         license="CC BY (CAL FIRE listing on data.gov); data.ca.gov: no restrictions on public use", license_verified=True,
         refresh_date="LRA maps released in 4 phases, Feb 10 - Mar 24, 2025 (combined file, Phases 1-4)",
         refresh_verified=True,
         join=dict(type="attr_at_point", fields={"fhsz_lra": ["FHSZ_Description", "FHSZ_Descr", "HAZ_CLASS", "Haz_Class", "FHSZ"]}),
         notes="Download 'LRA FHSZ Combined Data as Recommended by the Office of the State Fire Marshal - Phases 1 "
               "through 4' (file geodatabase zip) from the OSFM page. Cities adopt these by local ordinance."),
    dict(id="calfire_fhsz_sra", name="CAL FIRE OSFM Fire Hazard Severity Zones, SRA (effective April 1, 2024)", signals=["Hazards"],
         access="file", local_file="fhsz_sra_2024.zip",
         url="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones",
         landing_url="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones",
         license="CC BY (CAL FIRE listing on data.gov); data.ca.gov: no restrictions on public use", license_verified=True,
         refresh_date="Effective April 1, 2024; a 2026 SRA update was open for public comment (Nov 2026)",
         refresh_verified=True,
         join=dict(type="attr_at_point", fields={"fhsz_sra": ["FHSZ_Description", "FHSZ_Descr", "HAZ_CLASS", "Haz_Class", "FHSZ"]}),
         notes="Download 'SRA FHSZ Data Effective April 1, 2024' from the OSFM page. Replace when the 2026 SRA "
               "maps are adopted."),
    dict(id="cgs_liquefaction", name="CGS Seismic Hazards Program: Liquefaction Zones", signals=["Hazards"],
         access="arcgis_rest",
         url="https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Liquefaction_Zones/FeatureServer/0",
         landing_url="https://catalog.data.gov/dataset/cgs-liquefaction-zones",
         license="CC BY (California Department of Conservation)", license_verified=True,
         refresh_date="Last modified 2025-11-19 (publisher metadata)", refresh_verified=True,
         join=dict(type="flag_intersects", column="liquefaction"),
         notes="Service published by the California Department of Conservation, CGS. Zones of Required "
               "Investigation; not an official natural hazard disclosure determination."),
    dict(id="cgs_fault_zones", name="CGS Alquist-Priolo Earthquake Fault Zones", signals=["Hazards"],
         access="arcgis_rest",
         url="https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Alquist_Priolo_Fault_Zones/FeatureServer/0",
         landing_url="https://catalog.data.gov/dataset/cgs-alquist-priolo-fault-zones",
         license="CC BY (California Department of Conservation)", license_verified=True,
         refresh_date="Last modified 2025-11-19 (publisher metadata)", refresh_verified=True,
         join=dict(type="flag_intersects", column="fault_zone")),
    dict(id="coastal_zone", name="California Coastal Commission Coastal Zone Boundary", signals=["Hazards"],
         access="file", local_file="ccc_coastal_zone_boundary.gpkg",
         url="https://experience.arcgis.com/experience/61840fda04474fab9d1b5778740ad1b5",
         landing_url="https://www.coastal.ca.gov/maps/czb/",
         license="CCC disclaimer: no warranty; users indemnify the Commission; not survey accuracy",
         license_verified=True,
         refresh_date="Digital CZB from CCC GIS/Mapping Unit (2014-2016 vintages); official boundary adopted 1977 "
                      "and amended since", refresh_verified=True,
         join=dict(type="flag_intersects", column="coastal_zone"),
         notes="Download from the Commission's own GIS Data app. The digital boundary is not adopted and does not "
               "supersede the official maps; parcels near the line need a CCC boundary determination."),
    dict(id="calgem_wells", name="CalGEM WellSTAR oil and gas wells", signals=["Hazards"],
         access="arcgis_rest", url="https://gis.conservation.ca.gov/server/rest/services/WellSTAR/Wells/MapServer/0",
         landing_url="https://catalog.data.gov/dataset/wellstar-oil-and-gas-wells",
         license="CC BY (California Department of Conservation)", license_verified=True,
         refresh_date="Updated as needed; data.ca.gov files dated 12/24/25", refresh_verified=True,
         join=dict(type="nearest_distance", column="dist_oil_well_ft")),
    dict(id="dtsc_envirostor", name="DTSC EnviroStor cleanup sites", signals=["Hazards"],
         access="file", local_file="envirostor_sites.csv",
         url="https://www.envirostor.dtsc.ca.gov/public/data_download", landing_url="https://www.envirostor.dtsc.ca.gov/public/",
         license=CA_PUBLIC, license_verified=False, refresh_date="Live database; record download date", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_envirostor_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"]),
         notes="Published by the Department of Toxic Substances Control."),
    dict(id="geotracker", name="State Water Board GeoTracker sites", signals=["Hazards"],
         access="file", local_file="geotracker_sites.csv",
         url="https://data.ca.gov/dataset/ground-water-water-quality-regulatory-information",
         landing_url="https://geotracker.waterboards.ca.gov/",
         license=CA_PUBLIC, license_verified=False, refresh_date="Periodic CSV snapshot (latest seen: 2026-01-05)",
         refresh_verified=True,
         join=dict(type="nearest_distance", column="dist_geotracker_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"]),
         notes="Published by the State Water Resources Control Board on data.ca.gov."),
    dict(id="nrhp", name="National Register of Historic Places (NPS Cultural Resources GIS)", signals=["Hazards"],
         access="file", local_file="nrhp.gpkg",
         url="https://www.nps.gov/subjects/nationalregister/data-downloads.htm",
         landing_url="https://home.nps.gov/orgs/1094/nrhp_spatialdata.htm",
         license=PUBLIC_DOMAIN, license_verified=True, refresh_date="Irregular snapshots; record download date",
         refresh_verified=True,
         join=dict(type="flag_intersects", column="nrhp"),
         notes="NPS states its public spatial data is neither complete nor current for the Register; properties "
               "under 10 acres are points. Treat a miss as unknown, not as 'not historic'."),
    dict(id="hcd_mobilehome_parks", name="HCD mobilehome park list", signals=["Preservation"],
         access="file", local_file="hcd_mobilehome_parks.csv",
         url="https://www.hcd.ca.gov/manufactured-and-mobilehomes/mobilehome-parks",
         landing_url="https://www.hcd.ca.gov/manufactured-and-mobilehomes", license=CA_PUBLIC,
         license_verified=False, refresh_date="No official bulk download found (Nov 2026)", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_mhp_ft", lat=["Latitude", "LATITUDE"], lon=["Longitude", "LONGITUDE"]),
         notes="HCD regulates parks but I found no downloadable statewide list. Do NOT substitute commercial lead "
               "lists (MHVillage, ByteScraper, etc.). Options: request the list from HCD, or use SCAG land use "
               "code 1131 (mobile home parks) from scag_land_use instead."),
    dict(id="hud_lihtc", name="HUD LIHTC database", signals=["Preservation"],
         access="file", local_file="LIHTCPUB.csv",
         url="https://www.huduser.gov/portal/datasets/lihtc.html", landing_url="https://lihtc.huduser.gov/",
         license=PUBLIC_DOMAIN, license_verified=True,
         refresh_date="Annual release; record the 'placed in service through' year at download", refresh_verified=False,
         join=dict(type="nearest_distance", column="dist_lihtc_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"])),
    dict(id="hud_mf_s8", name="HUD Multifamily Assistance & Section 8 Contracts", signals=["Preservation"],
         access="file", local_file="hud_mf_section8.csv",
         url="https://www.hud.gov/hud-partners/multifamily-assist-section8-database",
         landing_url="https://www.hud.gov/hud-partners/multifamily-assist-section8-database", license=PUBLIC_DOMAIN,
         license_verified=True, refresh_date="Current as of 07/01/2026 (updated monthly)", refresh_verified=True,
         join=dict(type="nearest_distance", column="dist_s8_ft", lat=["LATITUDE", "Latitude"], lon=["LONGITUDE", "Longitude"]),
         notes="Excel download. If it lacks coordinates, geocode property addresses with the Census geocoder."),
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


# ---------------- Provenance ----------------
# Who publishes each dataset and how authoritative that is. Tiers:
#   original   the agency that creates or is legally responsible for the data, serving it itself
#   compiler   a public agency compiling other governments' records (e.g. SCAG from HCD forms / assessor rolls)
#   community  crowd-sourced (OpenStreetMap); used only where the project plan calls for it, always low confidence
#   consortium open-data consortium (Overture); alternative source only
# No dataset may come from a third-party mirror; tests enforce that non-county data is not read from OCGIS.
SOURCE_CHECKED_ON = "2026-11-07"
PROVENANCE = {
    "ocgis_parcels": ("County of Orange, OC Survey", "original"),
    "ocgis_city_boundaries": ("County of Orange, OC Survey", "original"),
    "ocgis_unincorporated": ("County of Orange, OC Survey", "original"),
    "census_zcta": ("U.S. Census Bureau", "original"),
    "census_tracts": ("U.S. Census Bureau", "original"),
    "ocgis_building_footprints": ("County of Orange, OC Survey", "original"),
    "overture_buildings": ("Overture Maps Foundation", "consortium"),
    "ocgis_centerlines": ("County of Orange, OC Survey", "original"),
    "scag_land_use": ("Southern California Association of Governments (from county assessor rolls)", "compiler"),
    "scag_he_sites": ("SCAG (compiled from HCD Housing Element sites inventory forms)", "compiler"),
    "scag_he_rezone": ("SCAG (compiled from HCD Housing Element sites inventory forms)", "compiler"),
    "hcd_compliance": ("CA Dept. of Housing and Community Development", "original"),
    "hcd_sb35": ("CA Dept. of Housing and Community Development", "original"),
    "apr_table_h": ("CA Dept. of Housing and Community Development", "original"),
    "hcd_sla_notices": ("CA Dept. of Housing and Community Development", "original"),
    "dgs_state_land": ("CA Dept. of General Services", "original"),
    "osm_worship": ("OpenStreetMap contributors (via Geofabrik)", "community"),
    "oc_tax_defaulted": ("Orange County Treasurer-Tax Collector", "original"),
    "scag_hqta": ("Southern California Association of Governments", "original"),
    "octa_gtfs": ("Orange County Transportation Authority", "original"),
    "metrolink_gtfs": ("Southern California Regional Rail Authority (Metrolink)", "original"),
    "lodes_wac": ("U.S. Census Bureau, LEHD", "original"),
    "cde_schools": ("CA Dept. of Education", "original"),
    "osm_grocery": ("OpenStreetMap contributors (via Geofabrik)", "community"),
    "tcac_opportunity": ("CA Tax Credit Allocation Committee / HCD", "original"),
    "acs5": ("U.S. Census Bureau", "original"),
    "hud_income_limits": ("U.S. Dept. of Housing and Urban Development", "original"),
    "calenviroscreen4": ("CA Office of Environmental Health Hazard Assessment", "original"),
    "cdfi_oz": ("U.S. Treasury, CDFI Fund", "original"),
    "fema_nfhl": ("Federal Emergency Management Agency", "original"),
    "calfire_fhsz_lra": ("CAL FIRE, Office of the State Fire Marshal", "original"),
    "calfire_fhsz_sra": ("CAL FIRE, Office of the State Fire Marshal", "original"),
    "cgs_liquefaction": ("CA Dept. of Conservation, California Geological Survey", "original"),
    "cgs_fault_zones": ("CA Dept. of Conservation, California Geological Survey", "original"),
    "coastal_zone": ("California Coastal Commission", "original"),
    "calgem_wells": ("CA Dept. of Conservation, CalGEM", "original"),
    "dtsc_envirostor": ("CA Dept. of Toxic Substances Control", "original"),
    "geotracker": ("State Water Resources Control Board", "original"),
    "nrhp": ("National Park Service", "original"),
    "hcd_mobilehome_parks": ("CA Dept. of Housing and Community Development", "original"),
    "hud_lihtc": ("U.S. Dept. of Housing and Urban Development", "original"),
    "hud_mf_s8": ("U.S. Dept. of Housing and Urban Development", "original"),
    "apr_table_a2": ("CA Dept. of Housing and Community Development", "original"),
}
# Datasets whose publisher, URL and vintage were checked against the publisher's own pages on SOURCE_CHECKED_ON.
SOURCE_CHECKED = set(PROVENANCE) - {"overture_buildings", "hcd_sla_notices", "osm_worship", "osm_grocery",
                                    "cde_schools"}

for _d in DATASETS:
    _d["publisher"], _d["authority"] = PROVENANCE[_d["id"]]
    _d["source_checked_on"] = SOURCE_CHECKED_ON if _d["id"] in SOURCE_CHECKED else None
