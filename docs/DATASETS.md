# Dataset catalog

Every input to the parcel screener, one entry per source. Generated from `backend/parcel_engine/registry.py` by `python -m parcel_engine.cli catalog`; edit the registry, not this file. A machine-readable copy is in [`datasets.csv`](datasets.csv).

Most data files are not stored in this repo. They are either queried live by the backend or downloaded into `backend/data/raw/`. Files already committed there are marked *In repo* below.

## Status

- 43 datasets: 15 pulled live by the backend, 2 committed in `backend/data/raw/` (lodes_wac, cde_schools), 26 still need a manual download.
- License checked against the publisher: 22 of 43.
- Refresh date checked against the publisher: 24 of 43.
- Source (publisher, URL, vintage) checked on 2026-11-07: 38 of 43.
- Authority: **original** = the agency responsible for the data, serving it itself; **compiler** = a public agency compiling other governments' records (SCAG); **community** = OpenStreetMap, used only where the project plan calls for it and always low confidence; **consortium** = Overture, alternative only. No dataset is read from a third-party mirror.
- Phase 1 requires every source documented with source, license and refresh date. Rows marked **no** under *Verified* still need someone to open the publisher's page and confirm.
- Ingest date is recorded per run in `backend/data/registry_state.json` and served by `GET /registry`.

## Summary

| Dataset | Publisher (authority) | Signal(s) | Access | License | Refresh | Verified (license / refresh) |
|---|---|---|---|---|---|---|
| [OCGIS Parcels](#ocgis-parcels) | County of Orange, OC Survey (original) | Lot size, Year built | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | Not published on layer (no editingInfo.lastEditDate) | **no** / **no** |
| [OCGIS City Boundaries](#ocgis-city-boundaries) | County of Orange, OC Survey (original) | Jurisdiction | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [OCGIS Unincorporated Area](#ocgis-unincorporated) | County of Orange, OC Survey (original) | Jurisdiction, Valid OC ZIP | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [Census 2020 ZCTA (TIGERweb)](#census-zcta) | U.S. Census Bureau (original) | ZIP selection | arcgis_rest | Public domain (U.S. Government work) | 2020 Census vintage | yes / yes |
| [Census tracts (TIGERweb)](#census-tracts) | U.S. Census Bureau (original) | Tract join key | arcgis_rest | Public domain (U.S. Government work) | Current TIGERweb vintage | yes / **no** |
| [OCGIS Building Footprints](#ocgis-building-footprints) | County of Orange, OC Survey (original) | Building coverage | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [Overture Maps buildings](#overture-buildings) | Overture Maps Foundation (consortium) | Building coverage | file | ODbL 1.0 (buildings theme) | Monthly Overture release; record release id at ingest | **no** / **no** |
| [OCGIS Street Centerlines](#ocgis-centerlines) | County of Orange, OC Survey (original) | Frontage | arcgis_rest | OC Survey / OCGIS public data; terms of use on ocgis.com | verify at ingest | **no** / **no** |
| [SCAG 2024 Existing Land Use, Orange County](#scag-land-use) | Southern California Association of Governments (from county assessor rolls) (compiler) | Land use code | arcgis_rest | SCAG Open Data terms of use | 2024 Annual Land Use, released June 2025 (on 2024 parcels, March 2025) | **no** / yes |
| [SCAG Region 6th Cycle Housing Element Sites (Table A)](#scag-he-sites) | SCAG (compiled from HCD Housing Element sites inventory forms) (compiler) | Housing Element site | arcgis_rest | SCAG Open Data terms of use | HCD sites inventory forms retrieved by SCAG October 2025 (168 jurisdictions) | **no** / yes |
| [SCAG Region 6th Cycle Housing Element Rezone Sites (Table B)](#scag-he-rezone) | SCAG (compiled from HCD Housing Element sites inventory forms) (compiler) | Housing Element site | arcgis_rest | SCAG Open Data terms of use | HCD sites inventory forms retrieved by SCAG October 2025 | **no** / yes |
| [HCD Housing Element Review and Compliance Report](#hcd-compliance) | CA Dept. of Housing and Community Development (original) | HE compliance | file | California public record; state open-data terms | Updated continuously; record pull date | **no** / **no** |
| [HCD SB 423 (formerly SB 35) Streamlined Ministerial Approval statewide determination](#hcd-sb35) | CA Dept. of Housing and Community Development (original) | SB 35 / SB 423 | file | California public record; state open-data terms | Annual HCD determination; record the determination date printed on the PDF | **no** / **no** |
| [HCD APR Table H (locally owned surplus sites)](#apr-table-h) | CA Dept. of Housing and Community Development (original) | Public land | file | California public record; state open-data terms | Annual APR cycle (reports due April 1); record report years | **no** / **no** |
| [HCD Surplus Land Act notices](#hcd-sla-notices) | CA Dept. of Housing and Community Development (original) | Public land | file | California public record; state open-data terms | verify | **no** / **no** |
| [DGS Statewide Property Inventory (state-owned real property)](#dgs-state-land) | CA Dept. of General Services (original) | Public land | file | No license stated by DGS (state public record) | Updated annually by agencies; RealProperty last modified 2025-10-22 | yes / yes |
| [OSM places of worship](#osm-worship) | OpenStreetMap contributors (via Geofabrik) (community) | Faith-based (SB 4) | file | ODbL 1.0 (attribution + share-alike) | Geofabrik daily extract; record extract date | yes / **no** |
| [OC Treasurer-Tax Collector tax-defaulted property lists (PDF)](#oc-tax-defaulted) | Orange County Treasurer-Tax Collector (original) | Tax-defaulted | pdf_dir | County public notice (published under Rev. & Tax. Code 3371 / 3702) | Delinquency list published each September (latest seen: executed Sept 2, 2025); auction Exhibit I each spring | yes / yes |
| [SCAG High Quality Transit Areas](#scag-hqta) | Southern California Association of Governments (original) | Transit (HQTA) | file | SCAG Open Data terms of use | Use Connect SoCal 2024 base-year (2022) HQTA; SCAG updates every 4 years | **no** / **no** |
| [OCTA GTFS stops](#octa-gtfs) | Orange County Transportation Authority (original) | Transit stops | file | OCTA open data terms: free use, OCTA retains ownership, no warranty | Quarterly service changes; read feed_info.txt / calendar.txt | yes / yes |
| [Metrolink GTFS stops](#metrolink-gtfs) | Southern California Regional Rail Authority (Metrolink) (original) | Transit stops | file | Metrolink: provided as is, no liability | Updated with schedule changes (about 5 times a year) | yes / yes |
| [Census LEHD LODES8 WAC (jobs by workplace)](#lodes-wac) | U.S. Census Bureau, LEHD (original) | Jobs access | in repo | Public domain (U.S. Government work) | Committed file is job year 2022; LODES 8.4 (Dec 18, 2025) adds 2023 | yes / yes |
| [CDE public schools](#cde-schools) | CA Dept. of Education (original) | Schools | in repo | California public record; state open-data terms | Updated daily; record download date | **no** / **no** |
| [OSM/Overture grocery stores](#osm-grocery) | OpenStreetMap contributors (via Geofabrik) (community) | Grocery | file | ODbL 1.0 (attribution + share-alike) | Record extract date | yes / **no** |
| [CTCAC/HCD Opportunity Map (2026)](#tcac-opportunity) | CA Tax Credit Allocation Committee / HCD (original) | Opportunity area | file | California public record; state open-data terms | 2026 map, adopted December 2025 (annual) | **no** / yes |
| [ACS 5-year 2020-2024 (rent burden, median household income)](#acs5) | U.S. Census Bureau (original) | Rent burden / income | census_api | Public domain (U.S. Government work) | 2020-2024 ACS 5-year, released January 29, 2026 | yes / yes |
| [HUD FY2026 income limits (Orange County AMI)](#hud-income-limits) | U.S. Dept. of Housing and Urban Development (original) | AMI | file | Public domain (U.S. Government work) | FY2026, effective May 1, 2026 | yes / yes |
| [CalEnviroScreen 5.0 (OEHHA)](#calenviroscreen4) | CA Office of Environmental Health Hazard Assessment (original) | Environmental burden | file | OEHHA conditions of use | CalEnviroScreen 5.0, final released July 2026 (replaces 4.0, Oct 2021) | **no** / yes |
| [Treasury/CDFI Fund Qualified Opportunity Zones (2026 list)](#cdfi-oz) | U.S. Treasury, CDFI Fund (original) | Opportunity Zone | file | Public domain (U.S. Government work) | 2026 designations announced Nov 5, 2026 (2018 list superseded) | yes / yes |
| [FEMA National Flood Hazard Layer (flood zones)](#fema-nfhl) | Federal Emergency Management Agency (original) | Hazards | arcgis_rest | Public domain (U.S. Government work) | Continuously updated; record query date | yes / yes |
| [CAL FIRE OSFM Fire Hazard Severity Zones, LRA (2025)](#calfire-fhsz-lra) | CAL FIRE, Office of the State Fire Marshal (original) | Hazards | file | CC BY (CAL FIRE listing on data.gov); data.ca.gov: no restrictions on public use | LRA maps released in 4 phases, Feb 10 - Mar 24, 2025 (combined file, Phases 1-4) | yes / yes |
| [CAL FIRE OSFM Fire Hazard Severity Zones, SRA (effective April 1, 2024)](#calfire-fhsz-sra) | CAL FIRE, Office of the State Fire Marshal (original) | Hazards | file | CC BY (CAL FIRE listing on data.gov); data.ca.gov: no restrictions on public use | Effective April 1, 2024; a 2026 SRA update was open for public comment (Nov 2026) | yes / yes |
| [CGS Seismic Hazards Program: Liquefaction Zones](#cgs-liquefaction) | CA Dept. of Conservation, California Geological Survey (original) | Hazards | arcgis_rest | CC BY (California Department of Conservation) | Last modified 2025-11-19 (publisher metadata) | yes / yes |
| [CGS Alquist-Priolo Earthquake Fault Zones](#cgs-fault-zones) | CA Dept. of Conservation, California Geological Survey (original) | Hazards | arcgis_rest | CC BY (California Department of Conservation) | Last modified 2025-11-19 (publisher metadata) | yes / yes |
| [California Coastal Commission Coastal Zone Boundary](#coastal-zone) | California Coastal Commission (original) | Hazards | file | CCC disclaimer: no warranty; users indemnify the Commission; not survey accuracy | Digital CZB from CCC GIS/Mapping Unit (2014-2016 vintages); official boundary adopted 1977 and amended since | yes / yes |
| [CalGEM WellSTAR oil and gas wells](#calgem-wells) | CA Dept. of Conservation, CalGEM (original) | Hazards | arcgis_rest | CC BY (California Department of Conservation) | Updated as needed; data.ca.gov files dated 12/24/25 | yes / yes |
| [DTSC EnviroStor cleanup sites](#dtsc-envirostor) | CA Dept. of Toxic Substances Control (original) | Hazards | file | California public record; state open-data terms | Live database; record download date | **no** / **no** |
| [State Water Board GeoTracker sites](#geotracker) | State Water Resources Control Board (original) | Hazards | file | California public record; state open-data terms | Periodic CSV snapshot (latest seen: 2026-01-05) | **no** / yes |
| [National Register of Historic Places (NPS Cultural Resources GIS)](#nrhp) | National Park Service (original) | Hazards | file | Public domain (U.S. Government work) | Irregular snapshots; record download date | yes / yes |
| [HCD mobilehome park list](#hcd-mobilehome-parks) | CA Dept. of Housing and Community Development (original) | Preservation | file | California public record; state open-data terms | No official bulk download found (Nov 2026) | **no** / **no** |
| [HUD LIHTC database](#hud-lihtc) | U.S. Dept. of Housing and Urban Development (original) | Preservation | file | Public domain (U.S. Government work) | Annual release; record the 'placed in service through' year at download | yes / **no** |
| [HUD Multifamily Assistance & Section 8 Contracts](#hud-mf-s8) | U.S. Dept. of Housing and Urban Development (original) | Preservation | file | Public domain (U.S. Government work) | Current as of 07/01/2026 (updated monthly) | yes / yes |
| [HCD APR Table A2 (building activity by APN)](#apr-table-a2) | CA Dept. of Housing and Community Development (original) | Validation | file | California public record; state open-data terms | Annual APR cycle; record report years | **no** / **no** |

## Base geography

### ocgis-parcels

**OCGIS Parcels**

- **Publisher:** County of Orange, OC Survey (authority: original)
- **Source checked against publisher:** 2026-11-07
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

- **Publisher:** County of Orange, OC Survey (authority: original)
- **Source checked against publisher:** 2026-11-07
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

- **Publisher:** County of Orange, OC Survey (authority: original)
- **Source checked against publisher:** 2026-11-07
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

- **Publisher:** U.S. Census Bureau (authority: original)
- **Source checked against publisher:** 2026-11-07
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

- **Publisher:** U.S. Census Bureau (authority: original)
- **Source checked against publisher:** 2026-11-07
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

- **Publisher:** County of Orange, OC Survey (authority: original)
- **Source checked against publisher:** 2026-11-07
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

- **Publisher:** Overture Maps Foundation (authority: consortium)
- **Source checked against publisher:** **not yet**
- **Signals:** Building coverage
- **Source URL:** https://docs.overturemaps.org/guides/buildings/
- **Publisher page:** https://overturemaps.org/download/
- **License:** ODbL 1.0 (buildings theme) (verified: **no**)
- **Refresh date:** Monthly Overture release; record release id at ingest (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/overture_buildings_oc.parquet`.
- **How it's used:** Alternative footprint source (set FOOTPRINT_SOURCE=overture_buildings).

### ocgis-centerlines

**OCGIS Street Centerlines**

- **Publisher:** County of Orange, OC Survey (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Frontage
- **Source URL:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Street_Centerlines_With_Labels/FeatureServer/0
- **Publisher page:** https://www.ocgis.com/arcpub/rest/services/Map_Layers/Street_Centerlines_With_Labels/FeatureServer
- **License:** OC Survey / OCGIS public data; terms of use on ocgis.com (verified: **no**)
- **Refresh date:** verify at ingest (verified: **no**)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Frontage = parcel edge within 60 ft of a centerline.
- **Notes:** Used for frontage. If unavailable, frontage falls back to the short side of the parcel's minimum rotated rectangle (flagged frontage_method=mrr_estimate).

### scag-land-use

**SCAG 2024 Existing Land Use, Orange County**

- **Publisher:** Southern California Association of Governments (from county assessor rolls) (authority: compiler)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Land use code
- **Source URL:** https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_OR/MapServer/0
- **Publisher page:** https://gisdata-scag.opendata.arcgis.com/
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** 2024 Annual Land Use, released June 2025 (on 2024 parcels, March 2025) (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel takes `land_use_code` from the polygon containing its interior point.
- **Notes:** Replaces the missing OCGIS use code. Served by SCAG itself. Confirm the 2024 code field name on first live run; code meanings in scoring.LAND_USE_UNDERUSED still need checking against SCAG's code book.

## Housing policy

### scag-he-sites

**SCAG Region 6th Cycle Housing Element Sites (Table A)**

- **Publisher:** SCAG (compiled from HCD Housing Element sites inventory forms) (authority: compiler)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Housing Element site
- **Source URL:** https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer/0
- **Publisher page:** https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** HCD sites inventory forms retrieved by SCAG October 2025 (168 jurisdictions) (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `he_site` = true if it overlaps any feature.
- **Notes:** Underlying data is HCD's Electronic Housing Element Sites Inventory Form (Table A), compiled by SCAG.

### scag-he-rezone

**SCAG Region 6th Cycle Housing Element Rezone Sites (Table B)**

- **Publisher:** SCAG (compiled from HCD Housing Element sites inventory forms) (authority: compiler)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Housing Element site
- **Source URL:** https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementRezone_poly_scag/MapServer/0
- **Publisher page:** https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementRezone_poly_scag/MapServer
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** HCD sites inventory forms retrieved by SCAG October 2025 (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `he_rezone` = true if it overlaps any feature.
- **Notes:** Underlying data is HCD's sites inventory form Table B (candidate sites to be rezoned).

### hcd-compliance

**HCD Housing Element Review and Compliance Report**

- **Publisher:** CA Dept. of Housing and Community Development (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** HE compliance
- **Source URL:** https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/housing-element-review-and-compliance-report
- **Publisher page:** https://www.hcd.ca.gov/planning-and-community-development/housing-open-data-tools/housing-element-review-and-compliance-report
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Updated continuously; record pull date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_he_compliance.csv`.
- **How it's used:** Joined by city / unincorporated to give `he_status`.

### hcd-sb35

**HCD SB 423 (formerly SB 35) Streamlined Ministerial Approval statewide determination**

- **Publisher:** CA Dept. of Housing and Community Development (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** SB 35 / SB 423
- **Source URL:** https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/sb423-determination-summary.pdf
- **Publisher page:** https://www.hcd.ca.gov/planning-and-community-development/statutory-determinations
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Annual HCD determination; record the determination date printed on the PDF (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_sb423_determination.csv`.
- **How it's used:** Joined by city / unincorporated to give `sb35_status`.
- **Notes:** SB 423 (2023) replaced the SB 35 determination; HCD now publishes the SB 423 summary. It is a PDF: convert to CSV with columns Jurisdiction, Determination (Not subject / 10% / 50%).

### apr-table-h

**HCD APR Table H (locally owned surplus sites)**

- **Publisher:** CA Dept. of Housing and Community Development (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Public land
- **Source URL:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
- **Publisher page:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Annual APR cycle (reports due April 1); record report years (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/apr_table_h.csv`.
- **How it's used:** Parcel gets `public_surplus` = true if its APN is on the list.
- **Notes:** Published by HCD (contact APR@hcd.ca.gov) on the state open data portal.

### hcd-sla-notices

**HCD Surplus Land Act notices**

- **Publisher:** CA Dept. of Housing and Community Development (authority: original)
- **Source checked against publisher:** **not yet**
- **Signals:** Public land
- **Source URL:** https://www.hcd.ca.gov/planning-and-community-development/public-lands
- **Publisher page:** https://www.hcd.ca.gov/planning-and-community-development/public-lands
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** verify (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_sla_notices.csv`.
- **How it's used:** Parcel gets `sla_notice` = true if its APN is on the list.

### dgs-state-land

**DGS Statewide Property Inventory (state-owned real property)**

- **Publisher:** CA Dept. of General Services (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Public land
- **Source URL:** https://catalog.data.gov/dataset/realproperty
- **Publisher page:** https://www.dgs.ca.gov/RESD/Resources/Page-Content/Real-Estate-Services-Division-Resources-List-Folder/Statewide-Property-Inventory
- **License:** No license stated by DGS (state public record) (verified: yes)
- **Refresh date:** Updated annually by agencies; RealProperty last modified 2025-10-22 (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/dgs_state_owned.gpkg`.
- **How it's used:** Parcel gets `state_owned` = true if it overlaps any feature.
- **Notes:** Excludes Caltrans highway right of way and some security-sensitive sites (Gov Code 11011).

### osm-worship

**OSM places of worship**

- **Publisher:** OpenStreetMap contributors (via Geofabrik) (authority: community)
- **Source checked against publisher:** **not yet**
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

**OC Treasurer-Tax Collector tax-defaulted property lists (PDF)**

- **Publisher:** Orange County Treasurer-Tax Collector (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Tax-defaulted
- **Source URL:** https://www.octreasurer.gov/taxdefaultedproperty
- **Publisher page:** https://www.octreasurer.gov/taxauction
- **License:** County public notice (published under Rev. & Tax. Code 3371 / 3702) (verified: yes)
- **Refresh date:** Delinquency list published each September (latest seen: executed Sept 2, 2025); auction Exhibit I each spring (verified: yes)
- **How to get it:** Manual download. Put the PDFs in `backend/data/raw/oc_treasurer_pdfs/`, then run `python -m parcel_engine.cli parse-tax-pdfs`.
- **How it's used:** Parcel gets `tax_defaulted` = true if its APN is on the list.
- **Low confidence:** a parcel flagged by this source loses half a signal of confidence.
- **Notes:** Parsed separately by parcel_engine.tax_default into data/cache/tax_defaulted_apns.csv. Lists change daily as parcels are redeemed; treat as a snapshot.

## Access

### scag-hqta

**SCAG High Quality Transit Areas**

- **Publisher:** Southern California Association of Governments (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Transit (HQTA)
- **Source URL:** https://gisdata-scag.opendata.arcgis.com/
- **Publisher page:** https://gisdata-scag.opendata.arcgis.com/
- **License:** SCAG Open Data terms of use (verified: **no**)
- **Refresh date:** Use Connect SoCal 2024 base-year (2022) HQTA; SCAG updates every 4 years (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/scag_hqta.gpkg`.
- **How it's used:** Parcel gets `in_hqta` = true if it overlaps any feature.
- **Notes:** SCAG serves the 2024 base-year HQTC lines live (OpenData/HQTC_Year_2022) but I could not find the matching HQTA polygon service, so this stays a download from SCAG's portal. Do not use the RTP2020 layers.

### octa-gtfs

**OCTA GTFS stops**

- **Publisher:** Orange County Transportation Authority (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Transit stops
- **Source URL:** https://www.octa.net/current/google_transit.zip
- **Publisher page:** https://octa.net/about/about-octa/open-data
- **License:** OCTA open data terms: free use, OCTA retains ownership, no warranty (verified: yes)
- **Refresh date:** Quarterly service changes; read feed_info.txt / calendar.txt (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/octa_gtfs.zip`.
- **How it's used:** Parcel gets `dist_bus_stop_ft`: feet to the nearest feature (capped at 3 miles).

### metrolink-gtfs

**Metrolink GTFS stops**

- **Publisher:** Southern California Regional Rail Authority (Metrolink) (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Transit stops
- **Source URL:** https://metrolinktrains.com/globalassets/about/gtfs/gtfs.zip
- **Publisher page:** https://metrolinktrains.com/about/gtfs/
- **License:** Metrolink: provided as is, no liability (verified: yes)
- **Refresh date:** Updated with schedule changes (about 5 times a year) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/metrolink_gtfs.zip`.
- **How it's used:** Parcel gets `dist_rail_ft`: feet to the nearest feature (capped at 3 miles).

### lodes-wac

**Census LEHD LODES8 WAC (jobs by workplace)**

- **Publisher:** U.S. Census Bureau, LEHD (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Jobs access
- **Source URL:** https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_2022.csv.gz
- **Publisher page:** https://lehd.ces.census.gov/data/#lodes
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Committed file is job year 2022; LODES 8.4 (Dec 18, 2025) adds 2023 (verified: yes)
- **How to get it:** **In repo:** `backend/data/raw/ca_wac_S000_JT00_2022.csv.gz`.
- **How it's used:** Block-level jobs (C000) summed to tract to give `tract_jobs`.
- **Notes:** Block-level C000 summed to tract (first 11 digits of w_geocode). To move to 2023, download ca_wac_S000_JT00_2023.csv.gz and change local_file and url.

### cde-schools

**CDE public schools**

- **Publisher:** CA Dept. of Education (authority: original)
- **Source checked against publisher:** **not yet**
- **Signals:** Schools
- **Source URL:** https://www.cde.ca.gov/ds/si/ds/pubschls.asp
- **Publisher page:** https://www.cde.ca.gov/ds/si/ds/pubschls.asp
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Updated daily; record download date (verified: **no**)
- **How to get it:** **In repo:** `backend/data/raw/pubschls.txt`.
- **How it's used:** Parcel gets `dist_school_ft`: feet to the nearest feature (capped at 3 miles).

### osm-grocery

**OSM/Overture grocery stores**

- **Publisher:** OpenStreetMap contributors (via Geofabrik) (authority: community)
- **Source checked against publisher:** **not yet**
- **Signals:** Grocery
- **Source URL:** https://download.geofabrik.de/north-america/us/california/socal.html
- **Publisher page:** https://www.openstreetmap.org/copyright
- **License:** ODbL 1.0 (attribution + share-alike) (verified: yes)
- **Refresh date:** Record extract date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/osm_grocery_oc.geojson`.
- **How it's used:** Parcel gets `dist_grocery_ft`: feet to the nearest feature (capped at 3 miles).

## Opportunity and need

### tcac-opportunity

**CTCAC/HCD Opportunity Map (2026)**

- **Publisher:** CA Tax Credit Allocation Committee / HCD (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Opportunity area
- **Source URL:** https://www.treasurer.ca.gov/ctcac/opportunity.asp
- **Publisher page:** https://www.treasurer.ca.gov/ctcac/opportunity.asp
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** 2026 map, adopted December 2025 (annual) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/tcac_opportunity_map_2026.gpkg`.
- **How it's used:** Parcel takes `tcac_category` from the polygon containing its interior point.
- **Notes:** Published by the State Treasurer's CTCAC with HCD. Shapefile is linked from the page above.

### acs5

**ACS 5-year 2020-2024 (rent burden, median household income)**

- **Publisher:** U.S. Census Bureau (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Rent burden / income
- **Source URL:** https://api.census.gov/data/2024/acs/acs5
- **Publisher page:** https://www.census.gov/programs-surveys/acs/news/data-releases/2024/release.html
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** 2020-2024 ACS 5-year, released January 29, 2026 (verified: yes)
- **How to get it:** Pulled live from the Census Data API for Orange County tracts and cached.
- **How it's used:** Joined by Census tract to give `median_hh_income` and `rent_burden_share`.

### hud-income-limits

**HUD FY2026 income limits (Orange County AMI)**

- **Publisher:** U.S. Dept. of Housing and Urban Development (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** AMI
- **Source URL:** https://www.huduser.gov/portal/datasets/il.html
- **Publisher page:** https://www.huduser.gov/portal/datasets/il.html
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** FY2026, effective May 1, 2026 (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/hud_income_limits_fy2026.csv`.
- **How it's used:** Not joined yet. Reserved for expressing tract income as % of AMI.
- **Notes:** County-level constant; used to express tract income as % AMI.

### calenviroscreen4

**CalEnviroScreen 5.0 (OEHHA)**

- **Publisher:** CA Office of Environmental Health Hazard Assessment (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Environmental burden
- **Source URL:** https://gis.data.ca.gov/datasets/OEHHA::calenviroscreen-5-0
- **Publisher page:** https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-50
- **License:** OEHHA conditions of use (verified: **no**)
- **Refresh date:** CalEnviroScreen 5.0, final released July 2026 (replaces 4.0, Oct 2021) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/calenviroscreen50.gpkg`.
- **How it's used:** Parcel takes `ces_percentile` from the polygon containing its interior point.
- **Notes:** Use the final 5.0 release, not the January 2026 draft. Confirm the percentile field name in the 5.0 data dictionary.

### cdfi-oz

**Treasury/CDFI Fund Qualified Opportunity Zones (2026 list)**

- **Publisher:** U.S. Treasury, CDFI Fund (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Opportunity Zone
- **Source URL:** https://www.cdfifund.gov/media/8018881/download?inline
- **Publisher page:** https://www.cdfifund.gov/opportunity-zones
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** 2026 designations announced Nov 5, 2026 (2018 list superseded) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/opportunity_zones_2026.csv`.
- **How it's used:** Joined by Census tract to give `in_oz`.
- **Notes:** Check the effective date of the 2026 designations against the 2018 list before relying on it.

## Hazards and constraints

### fema-nfhl

**FEMA National Flood Hazard Layer (flood zones)**

- **Publisher:** Federal Emergency Management Agency (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28
- **Publisher page:** https://www.fema.gov/flood-maps/national-flood-hazard-layer
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Continuously updated; record query date (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `flood_sfha` = true if it overlaps any feature where SFHA_TF = 'T'.
- **Notes:** FEMA's own service. Its robots.txt blocked my automated metadata check, so confirm layer 28 is 'Flood Hazard Zones' on first live run.

### calfire-fhsz-lra

**CAL FIRE OSFM Fire Hazard Severity Zones, LRA (2025)**

- **Publisher:** CAL FIRE, Office of the State Fire Marshal (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- **Publisher page:** https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- **License:** CC BY (CAL FIRE listing on data.gov); data.ca.gov: no restrictions on public use (verified: yes)
- **Refresh date:** LRA maps released in 4 phases, Feb 10 - Mar 24, 2025 (combined file, Phases 1-4) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/fhsz_lra_2025.zip`.
- **How it's used:** Parcel takes `fhsz_lra` from the polygon containing its interior point.
- **Notes:** Download 'LRA FHSZ Combined Data as Recommended by the Office of the State Fire Marshal - Phases 1 through 4' (file geodatabase zip) from the OSFM page. Cities adopt these by local ordinance.

### calfire-fhsz-sra

**CAL FIRE OSFM Fire Hazard Severity Zones, SRA (effective April 1, 2024)**

- **Publisher:** CAL FIRE, Office of the State Fire Marshal (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- **Publisher page:** https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- **License:** CC BY (CAL FIRE listing on data.gov); data.ca.gov: no restrictions on public use (verified: yes)
- **Refresh date:** Effective April 1, 2024; a 2026 SRA update was open for public comment (Nov 2026) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/fhsz_sra_2024.zip`.
- **How it's used:** Parcel takes `fhsz_sra` from the polygon containing its interior point.
- **Notes:** Download 'SRA FHSZ Data Effective April 1, 2024' from the OSFM page. Replace when the 2026 SRA maps are adopted.

### cgs-liquefaction

**CGS Seismic Hazards Program: Liquefaction Zones**

- **Publisher:** CA Dept. of Conservation, California Geological Survey (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Liquefaction_Zones/FeatureServer/0
- **Publisher page:** https://catalog.data.gov/dataset/cgs-liquefaction-zones
- **License:** CC BY (California Department of Conservation) (verified: yes)
- **Refresh date:** Last modified 2025-11-19 (publisher metadata) (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `liquefaction` = true if it overlaps any feature.
- **Notes:** Service published by the California Department of Conservation, CGS. Zones of Required Investigation; not an official natural hazard disclosure determination.

### cgs-fault-zones

**CGS Alquist-Priolo Earthquake Fault Zones**

- **Publisher:** CA Dept. of Conservation, California Geological Survey (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Alquist_Priolo_Fault_Zones/FeatureServer/0
- **Publisher page:** https://catalog.data.gov/dataset/cgs-alquist-priolo-fault-zones
- **License:** CC BY (California Department of Conservation) (verified: yes)
- **Refresh date:** Last modified 2025-11-19 (publisher metadata) (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `fault_zone` = true if it overlaps any feature.

### coastal-zone

**California Coastal Commission Coastal Zone Boundary**

- **Publisher:** California Coastal Commission (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://experience.arcgis.com/experience/61840fda04474fab9d1b5778740ad1b5
- **Publisher page:** https://www.coastal.ca.gov/maps/czb/
- **License:** CCC disclaimer: no warranty; users indemnify the Commission; not survey accuracy (verified: yes)
- **Refresh date:** Digital CZB from CCC GIS/Mapping Unit (2014-2016 vintages); official boundary adopted 1977 and amended since (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/ccc_coastal_zone_boundary.gpkg`.
- **How it's used:** Parcel gets `coastal_zone` = true if it overlaps any feature.
- **Notes:** Download from the Commission's own GIS Data app. The digital boundary is not adopted and does not supersede the official maps; parcels near the line need a CCC boundary determination.

### calgem-wells

**CalGEM WellSTAR oil and gas wells**

- **Publisher:** CA Dept. of Conservation, CalGEM (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://gis.conservation.ca.gov/server/rest/services/WellSTAR/Wells/MapServer/0
- **Publisher page:** https://catalog.data.gov/dataset/wellstar-oil-and-gas-wells
- **License:** CC BY (California Department of Conservation) (verified: yes)
- **Refresh date:** Updated as needed; data.ca.gov files dated 12/24/25 (verified: yes)
- **How to get it:** Queried live from the ArcGIS REST layer, clipped to the ZIP. Nothing to download.
- **How it's used:** Parcel gets `dist_oil_well_ft`: feet to the nearest feature (capped at 3 miles).

### dtsc-envirostor

**DTSC EnviroStor cleanup sites**

- **Publisher:** CA Dept. of Toxic Substances Control (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://www.envirostor.dtsc.ca.gov/public/data_download
- **Publisher page:** https://www.envirostor.dtsc.ca.gov/public/
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Live database; record download date (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/envirostor_sites.csv`.
- **How it's used:** Parcel gets `dist_envirostor_ft`: feet to the nearest feature (capped at 3 miles).
- **Notes:** Published by the Department of Toxic Substances Control.

### geotracker

**State Water Board GeoTracker sites**

- **Publisher:** State Water Resources Control Board (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://data.ca.gov/dataset/ground-water-water-quality-regulatory-information
- **Publisher page:** https://geotracker.waterboards.ca.gov/
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** Periodic CSV snapshot (latest seen: 2026-01-05) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/geotracker_sites.csv`.
- **How it's used:** Parcel gets `dist_geotracker_ft`: feet to the nearest feature (capped at 3 miles).
- **Notes:** Published by the State Water Resources Control Board on data.ca.gov.

### nrhp

**National Register of Historic Places (NPS Cultural Resources GIS)**

- **Publisher:** National Park Service (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Hazards
- **Source URL:** https://www.nps.gov/subjects/nationalregister/data-downloads.htm
- **Publisher page:** https://home.nps.gov/orgs/1094/nrhp_spatialdata.htm
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Irregular snapshots; record download date (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/nrhp.gpkg`.
- **How it's used:** Parcel gets `nrhp` = true if it overlaps any feature.
- **Notes:** NPS states its public spatial data is neither complete nor current for the Register; properties under 10 acres are points. Treat a miss as unknown, not as 'not historic'.

## Preservation

### hcd-mobilehome-parks

**HCD mobilehome park list**

- **Publisher:** CA Dept. of Housing and Community Development (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Preservation
- **Source URL:** https://www.hcd.ca.gov/manufactured-and-mobilehomes/mobilehome-parks
- **Publisher page:** https://www.hcd.ca.gov/manufactured-and-mobilehomes
- **License:** California public record; state open-data terms (verified: **no**)
- **Refresh date:** No official bulk download found (Nov 2026) (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/hcd_mobilehome_parks.csv`.
- **How it's used:** Parcel gets `dist_mhp_ft`: feet to the nearest feature (capped at 3 miles).
- **Notes:** HCD regulates parks but I found no downloadable statewide list. Do NOT substitute commercial lead lists (MHVillage, ByteScraper, etc.). Options: request the list from HCD, or use SCAG land use code 1131 (mobile home parks) from scag_land_use instead.

### hud-lihtc

**HUD LIHTC database**

- **Publisher:** U.S. Dept. of Housing and Urban Development (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Preservation
- **Source URL:** https://www.huduser.gov/portal/datasets/lihtc.html
- **Publisher page:** https://lihtc.huduser.gov/
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Annual release; record the 'placed in service through' year at download (verified: **no**)
- **How to get it:** Manual download. Save as `backend/data/raw/LIHTCPUB.csv`.
- **How it's used:** Parcel gets `dist_lihtc_ft`: feet to the nearest feature (capped at 3 miles).

### hud-mf-s8

**HUD Multifamily Assistance & Section 8 Contracts**

- **Publisher:** U.S. Dept. of Housing and Urban Development (authority: original)
- **Source checked against publisher:** 2026-11-07
- **Signals:** Preservation
- **Source URL:** https://www.hud.gov/hud-partners/multifamily-assist-section8-database
- **Publisher page:** https://www.hud.gov/hud-partners/multifamily-assist-section8-database
- **License:** Public domain (U.S. Government work) (verified: yes)
- **Refresh date:** Current as of 07/01/2026 (updated monthly) (verified: yes)
- **How to get it:** Manual download. Save as `backend/data/raw/hud_mf_section8.csv`.
- **How it's used:** Parcel gets `dist_s8_ft`: feet to the nearest feature (capped at 3 miles).
- **Notes:** Excel download. If it lacks coordinates, geocode property addresses with the Census geocoder.

## Validation

### apr-table-a2

**HCD APR Table A2 (building activity by APN)**

- **Publisher:** CA Dept. of Housing and Community Development (authority: original)
- **Source checked against publisher:** 2026-11-07
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
