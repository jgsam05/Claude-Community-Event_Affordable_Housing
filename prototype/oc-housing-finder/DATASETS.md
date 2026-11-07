# Dataset catalog (OC Housing Finder)

Checked 2026-11-07. **verified** = queried live and returned Orange County rows. **candidate** = found, not yet queried. License "not stated" = publisher lists none; confirm before redistributing.

| ID | Publisher | Status | Used for | License | Refresh | Caveat |
|---|---|---|---|---|---|---|
| oc_city_boundaries | OC Public Works (OC GIS) | verified | jurisdiction join (parcel -> city) | not stated | not reported | 40 "City" rows = 34 cities + 6 census communities; 5 Supervisory District rows. Assumption documented in README. |
| oc_parcels_attributes | OC Public Works / OC Assessor-derived | verified | parcel polygons, APN (AssessmentNo), SiteZip5 (direct ZIP filter), LandVal, ImprovedVal, site address | not stated | not reported | Measured on 4 ZIPs (2026-11-07): LandVal present on 84-96% of rows, ImprovedVal on 82-95%. Values are strings; blank = unknown. |
| scag_zoning | SCAG | verified | zoning code per parcel for ALL OC cities (join on APN24/PID24); Santa Ana alone returned 42,896 rows | not stated | not reported (2024 vintage per field names; confirm) | Zoning CODE only; max density/height/parking still must come from each city's code (config zoning CSV). Need the SCAG zone-category field to bridge. |
| scag_landuse | SCAG | verified | vacant / parking / commercial / mobile-home classification (dictionary in data/raw/scag_landuse_description.txt) | not stated (SCAG disclaimer saved in data/raw) | not reported |  |
| scag_general_plan | SCAG | verified | planned density; zoning-vs-GP mismatch signal (rezone potential) | not stated | not reported |  |
| scag_he_sites | SCAG (from city adopted Housing Elements) | verified | parcels the city itself identified for RHNA lower-income capacity (strong positive signal) | not stated | not reported | Field names for capacity were not confirmed (sample query returned no rows with guessed field names); inspect fields before mapping. |
| scag_he_rezone | SCAG | verified | parcels cities committed to rezone | not stated | not reported |  |
| oc_unincorp_zoning | OC Public Works | verified |  | not stated | last edit 2026-03-03 |  |
| oc_flood | OC Public Works | verified | flood risk (overlay mode flag; county-wide) | not stated (derived from FEMA public data) | last edit 2026-03-10 | Simplified polygons; not a flood determination. |
| geotracker | State Water Resources Control Board | verified | contamination risk (point buffer, e.g. 100 m; open cases only - check status field) | not stated | not reported |  |
| ces4 | OEHHA / Water Board hosted copy | verified | neighborhood burden (location context, not a risk penalty) | not stated | not reported |  |
| tcac_opportunity | CA HCD / TCAC; SCAG hosts 2021 service | candidate |  | ? | ? | 2025 shapefile/xlsx exist on HCD site (no license stated). Layer index not queried. Prefer newest. |
| scag_transit | SCAG | verified | transit_distance_m (AB 2097 parking exemption / AB 2011 style tests) | not stated | not reported | Plan-year 2050 includes planned stops |
| fire_hazard | CAL FIRE / OSFM | candidate |  | no restrictions on distribution; cite CAL FIRE (per service description) | ? | Service is the older map; newer LRA/2025 zones should replace it. Layer index and OC coverage not yet queried. Irvine redirect not followed. |
| fema_nfhl | FEMA | candidate |  | ? | ? | Alternative to oc_flood; not queried. |
| coastal_zone | Caltrans DEA | verified_with_gaps |  | not stated | not reported | {'Point tests': 'Seal Beach, Newport Pier, Corona del Mar, Laguna Beach, Dana Point = inside. Huntington Beach (PCH at Main and Beach) and San Clemente pier = N |
| hud_lihtc | HUD | verified | existing affordable housing nearby / preservation (expiring-use) signal | public domain (US federal; confirm on HUD page) | not reported (per-property data; PIS year often 8888 = unknown) | Many YR_PIS = '8888' (unknown placed-in-service). |
| census_zcta | US Census Bureau | verified | authoritative ZIP list. 86 ZCTAs have internal point inside OC (data/raw/oc_zctas_candidate.json). | public domain (US federal) | Census 2020 vintage | ZCTAs approximate ZIPs; PO-box/unique ZIPs missing. Parcel's own SiteZip5 is the ZIP of record. |
| ms_building_footprints |  | candidate | derive building footprint area / coverage ratio per parcel (proxy for underbuilt). No year built. | ODbL (README) | ? |  |
| oc_ttc_defaults |  | candidate |  | ? | ? | PDF only; parse test not done. Distress signal. |
| parcel_vendor |  | candidate |  | ? | ? | Only source for use code, sqft, year built, sales, owner type. Paid. Needed for Phase 2 accuracy. |
| laws |  | unverified |  | ? | ? | config/laws.yaml, written from general knowledge, needs counsel/planner review. |

## Rejected
- OrangeCounty_Parcels (ArcGIS search hit): Orange County, North Carolina
- Parcel_Information_Public_Map_View: Mariposa County, CA
- Coastal_Zone_Boundary_DRAFT: Sonoma County, 2017
- CGS liquefaction MS58: Token required
- OEHHA download page / maps.coastal.ca.gov:6443: Blocked (403 / connection reset) from this environment; not bypassed