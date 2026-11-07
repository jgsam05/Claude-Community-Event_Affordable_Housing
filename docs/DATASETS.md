# Dataset catalog

Every input to the parcel screener, one entry per source. Generated from `backend/parcel_engine/registry.py` by `python -m parcel_engine.cli catalog`; edit the registry, not this file. A machine-readable copy is in [`datasets.csv`](datasets.csv).

Most data files are not stored in this repo. They are either queried live by the backend or downloaded into `backend/data/raw/`. Files already committed there are marked *In repo* below.

## Status

- 43 datasets: 13 pulled live by the backend, 2 committed in `backend/data/raw/` (lodes_wac, cde_schools), 28 still need a manual download.
- License checked against the publisher: 12 of 43.
- Refresh date checked against the publisher: 2 of 43.
- Phase 1 requires every source documented with source, license and refresh date. Rows marked **no** under *Verified* still need someone to open the publisher's page and confirm.
- Ingest date is recorded per run in `backend/data/registry_state.json` and served by `GET /registry`.

## Summary

| Dataset | Signal(s) | Access | License | Refresh | Verified (license / refresh) |
|---|---|---|---|---|---|
| [OCGIS Parcels](#ocgis-parcels) | Lot size, Year built | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | Not published on layer (no editingInfo.lastEditDate) | **no** / **no** |
| [OCGIS City Boundaries](#ocgis-city-boundaries) | Jurisdiction | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [OCGIS Unincorporated Area](#ocgis-unincorporated) | Jurisdiction, Valid OC ZIP | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [Census 2020 ZCTA (TIGERweb)](#census-zcta) | ZIP selection | arcgis_rest | Public domain (U.S. Government work) | 2020 Census vintage | yes / yes |
| [Census tracts (TIGERweb)](#census-tracts) | Tract join key | arcgis_rest | Public domain (U.S. Government work) | Current TIGERweb vintage | yes / **no** |
| [OCGIS Building Footprints](#ocgis-building-footprints) | Building coverage | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [Overture Maps buildings](#overture-buildings) | Building coverage | file | ODbL 1.0 (buildings theme) | Monthly Overture release; record release id at ingest | **no** / **no** |
| [OCGIS Street Centerlines](#ocgis-centerlines) | Frontage | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [SCAG parcel land use](#scag-land-use) | Land use code | file | SCAG Open Data terms of use | 2019 annual land use (verify) | **no** / **no** |
| [SCAG 6th Cycle Housing Element sites inventory](#scag-he-sites) | Housing Element site | file | SCAG Open Data terms of use | 6th Cycle (2021-2029); verify | **no** / **no** |
| [SCAG 6th Cycle Housing Element rezone sites](#scag-he-rezone) | Housing Element site | file | SCAG Open Data terms of use | 6th Cycle; verify | **no** / **no** |
| [HCD Housing Element Compliance Report](#hcd-compliance) | HE compliance | file | California public record; state open-data terms | Updated continuously; record pull date | **no** / **no** |
| [HCD SB 35 statewide determination](#hcd-sb35) | SB 35 | file | California public record; state open-data terms | Annual determination; verify year | **no** / **no** |
| [HCD APR Table H (locally owned surplus sites)](#apr-table-h) | Public land | file | California public record; state open-data terms | Annual APR cycle; verify | **no** / **no** |
| [HCD Surplus Land Act notices](#hcd-sla-notices) | Public land | file | California public record; state open-data terms | verify | **no** / **no** |
| [DGS state-owned land](#dgs-state-land) | Public land | file | California public record; state open-data terms | verify | **no** / **no** |
| [OSM places of worship](#osm-worship) | Faith-based (SB 4) | file | ODbL 1.0 (attribution + share-alike) | Geofabrik daily extract; record extract date | yes / **no** |
| [OC Treasurer tax-defaulted parcels (PDF)](#oc-tax-defaulted) | Tax-defaulted | pdf_dir | County public record | Per auction list; record PDF date | **no** / **no** |
| [SCAG High Quality Transit Areas](#scag-hqta) | Transit (HQTA) | file | SCAG Open Data terms of use | Connect SoCal 2024 HQTA (verify) | **no** / **no** |
| [OCTA GTFS stops](#octa-gtfs) | Transit stops | file | OCTA GTFS license (verify) | Per service change; read feed_info.txt | **no** / **no** |
| [Metrolink GTFS stops](#metrolink-gtfs) | Transit stops | file | Metrolink GTFS license (verify) | Per service change; read feed_info.txt | **no** / **no** |
| [Census LEHD LODES8 WAC (jobs by workplace)](#lodes-wac) | Jobs access | in repo | Public domain (U.S. Government work) | LODES8, 2022 job year | yes / **no** |
| [CDE public schools](#cde-schools) | Schools | in repo | California public record; state open-data terms | Updated daily; record download date | **no** / **no** |
| [OSM/Overture grocery stores](#osm-grocery) | Grocery | file | ODbL 1.0 (attribution + share-alike) | Record extract date | yes / **no** |
| [TCAC/HCD Opportunity Map](#tcac-opportunity) | Opportunity area | file | California public record; state open-data terms | Annual map; record map year | **no** / **no** |
| [ACS 5-year (rent burden, median household income)](#acs5) | Rent burden / income | census_api | Public domain (U.S. Government work) | 2019-2023 ACS 5-year (released Dec 2024) | yes / **no** |
| [HUD income limits (Orange County AMI)](#hud-income-limits) | AMI | file | Public domain (U.S. Government work) | FY income limits; record FY | yes / **no** |
| [CalEnviroScreen 4.0](#calenviroscreen4) | Environmental burden | file | California public record; state open-data terms | Oct 2021 (version 4.0) | **no** / **no** |
| [CDFI Fund Opportunity Zones tract list](#cdfi-oz) | Opportunity Zone | file | Public domain (U.S. Government work) | 2018 designations | yes / **no** |
| [FEMA National Flood Hazard Layer (flood zones)](#fema-nfhl) | Hazards | arcgis_rest | Public domain (U.S. Government work) | Continuously updated; record query date | yes / yes |
| [CAL FIRE FHSZ (LRA, OCGIS mirror)](#calfire-fhsz-lra) | Hazards | arcgis_rest | California public record; state open-data terms | 2025 LRA maps (verify mirror vintage) | **no** / **no** |
| [CAL FIRE FHSZ (SRA, OCGIS mirror)](#calfire-fhsz-sra) | Hazards | arcgis_rest | California public record; state open-data terms | 2023 SRA maps (verify mirror vintage) | **no** / **no** |
| [CGS liquefaction zones (OCGIS mirror)](#cgs-liquefaction) | Hazards | arcgis_rest | California public record; state open-data terms | verify | **no** / **no** |
| [CGS Alquist-Priolo fault zones](#cgs-fault-zones) | Hazards | file | California public record; state open-data terms | verify | **no** / **no** |
| [Coastal Zone boundary (OCGIS mirror of CCC)](#coastal-zone) | Hazards | arcgis_rest | California public record; state open-data terms | verify | **no** / **no** |
| [CalGEM oil and gas wells](#calgem-wells) | Hazards | file | California public record; state open-data terms | Updated weekly; record download date | **no** / **no** |
| [DTSC EnviroStor sites](#dtsc-envirostor) | Hazards | file | California public record; state open-data terms | Record download date | **no** / **no** |
| [Water Board GeoTracker cleanup sites](#geotracker) | Hazards | file | California public record; state open-data terms | Record download date | **no** / **no** |
| [National Register of Historic Places](#nrhp) | Hazards | file | Public domain (U.S. Government work) | verify | yes / **no** |
| [HCD mobilehome park list](#hcd-mobilehome-parks) | Preservation | file | California public record; state open-data terms | verify | **no** / **no** |
| [HUD LIHTC database](#hud-lihtc) | Preservation | file | Public domain (U.S. Government work) | Annual release; record placed-in-service year | yes / **no** |
| [HUD Multifamily Section 8 contracts](#hud-mf-s8) | Preservation | file | Public domain (U.S. Government work) | Monthly; record download date | yes / **no** |
| [HCD APR Table A2 (building activity by APN)](#apr-table-a2) | Validation | file | California public record; state open-data terms | Annual APR cycle; record report years | **no** / **no** |

## Base geography

### ocgis-parcels

**OCGIS Parcels**

- **Signals:** Lot size, Year built
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0
- **Publisher page:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer
- **License:** OC Survey / OCGIS public data; terms of use on ocgis.com (verified: **no**)
- **Refresh date:** Not published on layer (no editingInfo.lastEditDate) (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Defines the parcels. APN, address and year built come from here; lot size, frontage and buildable area are computed from the polygon.
- **Notes:** Fields: OBJECTID, SITE_ADDRESS, ASSESSMENT_NO (APN), YEAR_BUILT, NBR_BEDROOMS. No use code, assessed value or owner name. See docs/describe_layer_report.md.

### ocgis-city-boundaries

**OCGIS City Boundaries**

- **Signals:** Jurisdiction
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/City_Boundaries/MapServer/0
- **Publisher page:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/City_Boundaries/MapServer
- **License:** OC Survey / OCGIS public data; terms of use on ocgis.com (verified: **no**)
- **Refresh date:** verify at ingest (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Tags each parcel with the city containing its interior point; flags parcels split by a city line.
- **Notes:** Fields JURISDICTI, CITY. Areas outside every polygon are tagged Unincorporated.

### ocgis-unincorporated

**OCGIS Unincorporated Area**

- **Signals:** Jurisdiction, Valid OC ZIP
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Unincorporated_Area/MapServer/0
- **Publisher page:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Unincorporated_Area/MapServer
- **License:** OC Survey / OCGIS public data; terms of use on ocgis.com (verified: **no**)
- **Refresh date:** verify at ingest (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** With city boundaries, defines the county footprint used to reject non-OC ZIPs.
- **Notes:** With city boundaries, defines the county footprint used to validate OC ZIPs.

### census-zcta

**Census 2020 ZCTA (TIGERweb)**

- **Signals:** ZIP selection
- **Source URL:** https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7
- **Publisher page:** https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** 2020 Census vintage (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** The ZIP polygon. A parcel belongs to the ZIP containing its interior point.
- **Notes:** Layer 7 = Census 2020 ZCTAs. Field GEOID = 5-digit ZCTA.

### census-tracts

**Census tracts (TIGERweb)**

- **Signals:** Tract join key
- **Source URL:** https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/0
- **Publisher page:** https://tigerweb.geo.census.gov/tigerwebmain/TIGERweb_main.html
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Current TIGERweb vintage (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Gives each parcel a tract GEOID for the ACS, LODES and Opportunity Zone joins.
- **Notes:** Tract GEOID used to join ACS, LODES, Opportunity Zones. Confirm layer 0 is tracts.

### ocgis-building-footprints

**OCGIS Building Footprints**

- **Signals:** Building coverage
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Building_Footprints/FeatureServer/0
- **Publisher page:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Building_Footprints/FeatureServer
- **License:** OC Survey / OCGIS public data; terms of use on ocgis.com (verified: **no**)
- **Refresh date:** verify at ingest (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Footprint area inside the parcel ÷ lot area = building coverage; no footprint = vacant.
- **Notes:** Default footprint source because it is bbox-queryable. Overture/Microsoft are file alternatives (set FOOTPRINT_SOURCE).

### overture-buildings

**Overture Maps buildings**

- **Signals:** Building coverage
- **Source URL:** https://docs.overturemaps.org/guides/buildings/
- **Publisher page:** https://overturemaps.org/download/
- **License:** ODbL 1.0 (buildings theme) (verified: **no**)
- **Refresh date:** Monthly Overture release; record release id at ingest (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/overture_buildings_oc.parquet`.
- **How it's used:** Alternative footprint source (set FOOTPRINT_SOURCE=overture_buildings).

### ocgis-centerlines

**OCGIS Street Centerlines**

- **Signals:** Frontage
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Street_Centerlines_With_Labels/FeatureServer/0
- **Publisher page:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Street_Centerlines_With_Labels/FeatureServer
- **License:** OC Survey / OCGIS public data; terms of use on ocgis.com (verified: **no**)
- **Refresh date:** verify at ingest (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Frontage = parcel edge within 60 ft of a centerline.
- **Notes:** Used for frontage. If unavailable, frontage falls back to the short side of the parcel's minimum rotated rectangle (flagged frontage_method=mrr_estimate).

### scag-land-use

**SCAG parcel land use**

- **Signals:** Land use code
- **Source URL:** https://gisdata-scag.opendata.arcgis.com/
- **Publisher page:** https://gisdata-scag.opendata.arcgis.com/
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** 2019 annual land use (verify) (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/scag_land_use_oc.gpkg`.
- **How it's used:** Parcel takes `land_use_code` from the polygon containing its interior point.
- **Notes:** Replaces the missing OCGIS use code. Code meanings in scoring.LAND_USE_UNDERUSED (verify).

## Housing policy

### scag-he-sites

**SCAG 6th Cycle Housing Element sites inventory**

- **Signals:** Housing Element site
- **Source URL:** https://gisdata-scag.opendata.arcgis.com/
- **Publisher page:** https://scag.ca.gov/housing-element-parcel-tool
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** 6th Cycle (2021-2029); verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/scag_he_sites_6th.gpkg`.
- **How it's used:** Parcel gets `he_site` = true if it overlaps any feature.

### scag-he-rezone

**SCAG 6th Cycle Housing Element rezone sites**

- **Signals:** Housing Element site
- **Source URL:** https://gisdata-scag.opendata.arcgis.com/
- **Publisher page:** https://scag.ca.gov/housing-element-parcel-tool
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** 6th Cycle; verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/scag_he_rezone_6th.gpkg`.
- **How it's used:** Parcel gets `he_rezone` = true if it overlaps any feature.

### hcd-compliance

**HCD Housing Element Compliance Report**

- **Signals:** HE compliance
- **Source URL:** https://www.hcd.ca.gov/planning-and-community-development/housing-elements
- **Publisher page:** https://www.hcd.ca.gov/planning-and-community-development/housing-elements
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Updated continuously; record pull date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_he_compliance.csv`.
- **How it's used:** Joined by city / unincorporated to give `he_status`.

### hcd-sb35

**HCD SB 35 statewide determination**

- **Signals:** SB 35
- **Source URL:** https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process
- **Publisher page:** https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Annual determination; verify year (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_sb35_determination.csv`.
- **How it's used:** Joined by city / unincorporated to give `sb35_status`.

### apr-table-h

**HCD APR Table H (locally owned surplus sites)**

- **Signals:** Public land
- **Source URL:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
- **Publisher page:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Annual APR cycle; verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/apr_table_h.csv`.
- **How it's used:** Parcel gets `public_surplus` = true if its APN is on the list.

### hcd-sla-notices

**HCD Surplus Land Act notices**

- **Signals:** Public land
- **Source URL:** https://www.hcd.ca.gov/planning-and-community-development/public-lands
- **Publisher page:** https://www.hcd.ca.gov/planning-and-community-development/public-lands
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_sla_notices.csv`.
- **How it's used:** Parcel gets `sla_notice` = true if its APN is on the list.

### dgs-state-land

**DGS state-owned land**

- **Signals:** Public land
- **Source URL:** https://www.dgs.ca.gov/RESD
- **Publisher page:** https://www.dgs.ca.gov/RESD
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/dgs_state_owned.gpkg`.
- **How it's used:** Parcel gets `state_owned` = true if it overlaps any feature.

### osm-worship

**OSM places of worship**

- **Signals:** Faith-based (SB 4)
- **Source URL:** https://download.geofabrik.de/north-america/us/california/socal.html
- **Publisher page:** https://www.openstreetmap.org/copyright
- **License:** ODbL 1.0 (attribution + share-alike) (verified: yes)
- **Refresh date:** Geofabrik daily extract; record extract date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/osm_places_of_worship_oc.geojson`.
- **How it's used:** Parcel gets `faith_based` = true if it overlaps any feature.
- **Low confidence:** a parcel flagged by this source loses half a signal of confidence.
- **Notes:** Low confidence: OSM tags the use, not the owner. Parcels flagged here are capped at Low.

### oc-tax-defaulted

**OC Treasurer tax-defaulted parcels (PDF)**

- **Signals:** Tax-defaulted
- **Source URL:** https://www.octreasurer.gov/
- **Publisher page:** https://www.octreasurer.gov/
- **License:** County public record (verified: **no**)
- **Refresh date:** Per auction list; record PDF date (verified: **no**)
- **How to get it:** Manual download. Put the PDFs in `backend/data/raw/oc_treasurer_pdfs/`, then run `python -m parcel_engine.cli parse-tax-pdfs`.
- **How it's used:** Parcel gets `tax_defaulted` = true if its APN is on the list.
- **Low confidence:** a parcel flagged by this source loses half a signal of confidence.
- **Notes:** Parsed separately by parcel_engine.tax_default into data/cache/tax_defaulted_apns.csv.

## Access

### scag-hqta

**SCAG High Quality Transit Areas**

- **Signals:** Transit (HQTA)
- **Source URL:** https://gisdata-scag.opendata.arcgis.com/
- **Publisher page:** https://gisdata-scag.opendata.arcgis.com/
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** Connect SoCal 2024 HQTA (verify) (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/scag_hqta.gpkg`.
- **How it's used:** Parcel gets `in_hqta` = true if it overlaps any feature.

### octa-gtfs

**OCTA GTFS stops**

- **Signals:** Transit stops
- **Source URL:** https://www.octa.net/about/about-octa/doing-business-with-octa/gtfs/
- **Publisher page:** https://www.octa.net/
- **License:** OCTA GTFS license (verify) (verified: **no**)
- **Refresh date:** Per service change; read feed_info.txt (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/octa_gtfs.zip`.
- **How it's used:** Parcel gets `dist_bus_stop_ft`: feet to the nearest feature (capped at 3 miles).

### metrolink-gtfs

**Metrolink GTFS stops**

- **Signals:** Transit stops
- **Source URL:** https://metrolinktrains.com/about/gtfs/
- **Publisher page:** https://metrolinktrains.com/
- **License:** Metrolink GTFS license (verify) (verified: **no**)
- **Refresh date:** Per service change; read feed_info.txt (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/metrolink_gtfs.zip`.
- **How it's used:** Parcel gets `dist_rail_ft`: feet to the nearest feature (capped at 3 miles).

### lodes-wac

**Census LEHD LODES8 WAC (jobs by workplace)**

- **Signals:** Jobs access
- **Source URL:** https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_2022.csv.gz
- **Publisher page:** https://lehd.ces.census.gov/data/
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** LODES8, 2022 job year (verified: **no**)
- **How to get it:** **In repo:** `backend/data/raw/ca_wac_S000_JT00_2022.csv.gz`.
- **How it's used:** Block-level jobs (C000) summed to tract to give `tract_jobs`.
- **Notes:** Block-level C000 summed to tract (first 11 digits of w_geocode).

### cde-schools

**CDE public schools**

- **Signals:** Schools
- **Source URL:** https://www.cde.ca.gov/ds/si/ds/pubschls.asp
- **Publisher page:** https://www.cde.ca.gov/ds/si/ds/pubschls.asp
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Updated daily; record download date (verified: **no**)
- **How to get it:** **In repo:** `backend/data/raw/pubschls.txt`.
- **How it's used:** Parcel gets `dist_school_ft`: feet to the nearest feature (capped at 3 miles).

### osm-grocery

**OSM/Overture grocery stores**

- **Signals:** Grocery
- **Source URL:** https://download.geofabrik.de/north-america/us/california/socal.html
- **Publisher page:** https://www.openstreetmap.org/copyright
- **License:** ODbL 1.0 (attribution + share-alike) (verified: yes)
- **Refresh date:** Record extract date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/osm_grocery_oc.geojson`.
- **How it's used:** Parcel gets `dist_grocery_ft`: feet to the nearest feature (capped at 3 miles).

## Opportunity and need

### tcac-opportunity

**TCAC/HCD Opportunity Map**

- **Signals:** Opportunity area
- **Source URL:** https://www.treasurer.ca.gov/ctcac/opportunity.asp
- **Publisher page:** https://www.treasurer.ca.gov/ctcac/opportunity.asp
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Annual map; record map year (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/tcac_opportunity_map.gpkg`.
- **How it's used:** Parcel takes `tcac_category` from the polygon containing its interior point.

### acs5

**ACS 5-year (rent burden, median household income)**

- **Signals:** Rent burden / income
- **Source URL:** https://api.census.gov/data/2023/acs/acs5
- **Publisher page:** https://www.census.gov/programs-surveys/acs
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** 2019-2023 ACS 5-year (released Dec 2024) (verified: **no**)
- **How to get it:** Pulled live from the Census Data API for Orange County tracts and cached.
- **How it's used:** Joined by Census tract to give `median_hh_income` and `rent_burden_share`.

### hud-income-limits

**HUD income limits (Orange County AMI)**

- **Signals:** AMI
- **Source URL:** https://www.huduser.gov/portal/datasets/il.html
- **Publisher page:** https://www.huduser.gov/portal/datasets/il.html
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** FY income limits; record FY (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hud_income_limits.csv`.
- **How it's used:** Not joined yet. Reserved for expressing tract income as % of AMI.
- **Notes:** County-level constant; used to express tract income as % AMI.

### calenviroscreen4

**CalEnviroScreen 4.0**

- **Signals:** Environmental burden
- **Source URL:** https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-40
- **Publisher page:** https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-40
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Oct 2021 (version 4.0) (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/calenviroscreen40.gpkg`.
- **How it's used:** Parcel takes `ces_percentile` from the polygon containing its interior point.

### cdfi-oz

**CDFI Fund Opportunity Zones tract list**

- **Signals:** Opportunity Zone
- **Source URL:** https://www.cdfifund.gov/opportunity-zones
- **Publisher page:** https://www.cdfifund.gov/opportunity-zones
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** 2018 designations (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/opportunity_zones.csv`.
- **How it's used:** Joined by Census tract to give `in_oz`.

## Hazards and constraints

### fema-nfhl

**FEMA National Flood Hazard Layer (flood zones)**

- **Signals:** Hazards
- **Source URL:** https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28
- **Publisher page:** https://www.fema.gov/flood-maps/national-flood-hazard-layer
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Continuously updated; record query date (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `flood_sfha` = true if it overlaps any feature where SFHA_TF = 'T'.

### calfire-fhsz-lra

**CAL FIRE FHSZ (LRA, OCGIS mirror)**

- **Signals:** Hazards
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_LRA/MapServer/0
- **Publisher page:** https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** 2025 LRA maps (verify mirror vintage) (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel takes `fhsz_lra` from the polygon containing its interior point.

### calfire-fhsz-sra

**CAL FIRE FHSZ (SRA, OCGIS mirror)**

- **Signals:** Hazards
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_SRA/MapServer/0
- **Publisher page:** https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** 2023 SRA maps (verify mirror vintage) (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel takes `fhsz_sra` from the polygon containing its interior point.

### cgs-liquefaction

**CGS liquefaction zones (OCGIS mirror)**

- **Signals:** Hazards
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Liquefaction/MapServer/0
- **Publisher page:** https://www.conservation.ca.gov/cgs/sh/program
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `liquefaction` = true if it overlaps any feature.

### cgs-fault-zones

**CGS Alquist-Priolo fault zones**

- **Signals:** Hazards
- **Source URL:** https://www.conservation.ca.gov/cgs/alquist-priolo
- **Publisher page:** https://www.conservation.ca.gov/cgs/alquist-priolo
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/cgs_ap_fault_zones.gpkg`.
- **How it's used:** Parcel gets `fault_zone` = true if it overlaps any feature.

### coastal-zone

**Coastal Zone boundary (OCGIS mirror of CCC)**

- **Signals:** Hazards
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Coastal_Zone/MapServer/0
- **Publisher page:** https://www.coastal.ca.gov/maps/czb/
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `coastal_zone` = true if it overlaps any feature.

### calgem-wells

**CalGEM oil and gas wells**

- **Signals:** Hazards
- **Source URL:** https://www.conservation.ca.gov/calgem/maps
- **Publisher page:** https://www.conservation.ca.gov/calgem/maps
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Updated weekly; record download date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/calgem_wells.csv`.
- **How it's used:** Parcel gets `dist_oil_well_ft`: feet to the nearest feature (capped at 3 miles).

### dtsc-envirostor

**DTSC EnviroStor sites**

- **Signals:** Hazards
- **Source URL:** https://www.envirostor.dtsc.ca.gov/public/data_download
- **Publisher page:** https://www.envirostor.dtsc.ca.gov/public/
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Record download date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/envirostor_sites.csv`.
- **How it's used:** Parcel gets `dist_envirostor_ft`: feet to the nearest feature (capped at 3 miles).

### geotracker

**Water Board GeoTracker cleanup sites**

- **Signals:** Hazards
- **Source URL:** https://geotracker.waterboards.ca.gov/data_download
- **Publisher page:** https://geotracker.waterboards.ca.gov/
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Record download date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/geotracker_sites.csv`.
- **How it's used:** Parcel gets `dist_geotracker_ft`: feet to the nearest feature (capped at 3 miles).

### nrhp

**National Register of Historic Places**

- **Signals:** Hazards
- **Source URL:** https://www.nps.gov/subjects/nationalregister/data-downloads.htm
- **Publisher page:** https://www.nps.gov/subjects/nationalregister/data-downloads.htm
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/nrhp.gpkg`.
- **How it's used:** Parcel gets `nrhp` = true if it overlaps any feature.

## Preservation

### hcd-mobilehome-parks

**HCD mobilehome park list**

- **Signals:** Preservation
- **Source URL:** https://www.hcd.ca.gov/manufactured-and-mobilehomes/mobilehome-parks
- **Publisher page:** https://www.hcd.ca.gov/manufactured-and-mobilehomes
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_mobilehome_parks.csv`.
- **How it's used:** Parcel gets `dist_mhp_ft`: feet to the nearest feature (capped at 3 miles).

### hud-lihtc

**HUD LIHTC database**

- **Signals:** Preservation
- **Source URL:** https://www.huduser.gov/portal/datasets/lihtc.html
- **Publisher page:** https://www.huduser.gov/portal/datasets/lihtc.html
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Annual release; record placed-in-service year (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/LIHTCPUB.csv`.
- **How it's used:** Parcel gets `dist_lihtc_ft`: feet to the nearest feature (capped at 3 miles).

### hud-mf-s8

**HUD Multifamily Section 8 contracts**

- **Signals:** Preservation
- **Source URL:** https://www.hud.gov/program_offices/housing/mfh/exp/mfhdiscl
- **Publisher page:** https://www.hud.gov/program_offices/housing/mfh/exp/mfhdiscl
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Monthly; record download date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hud_mf_section8.csv`.
- **How it's used:** Parcel gets `dist_s8_ft`: feet to the nearest feature (capped at 3 miles).

## Validation

### apr-table-a2

**HCD APR Table A2 (building activity by APN)**

- **Signals:** Validation
- **Source URL:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
- **Publisher page:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Annual APR cycle; record report years (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/apr_table_a2.csv`.
- **How it's used:** Not a scoring input. Permitted APNs are compared with scores (lift, AUC).

## Removed signals (no free, legal, county-wide dataset)

Code enforcement and vacant/foreclosure registries; long-term vacancy (HUD/USPS, restricted); absentee owners (needs owner mailing addresses); frequent transfers and sale prices (paid data); methane zones; local historic designations; displacement risk index; state at-risk housing list (CHPC, by request).

## Conditional signals cut after describe_layer

The OCGIS parcel layer has no use code, assessed values or owner name (see [`backend/docs/describe_layer_report.md`](../backend/docs/describe_layer_report.md)). Land use comes from SCAG instead; improvement-to-land ratio and land cost per unit are removed; owner type is limited to public ownership from Table H, SLA notices and DGS. Airport compatibility zones and city zoning are not ingested.
