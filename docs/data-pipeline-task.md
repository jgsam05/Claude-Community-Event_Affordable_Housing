# Data Pipeline & API — Task Spec

**Owns:** everything from raw datasets to a scored parcel table and an API that serves it.

## Tasks

1. **ZIP → parcel selection.** Take a ZIP, pull its Census ZCTA polygon, and return the OCGIS parcels inside it. Tag each parcel with its city or "unincorporated" using OCGIS city boundaries. Build this so it handles ZIPs that cross city lines.
2. **Run `describe_layer` on the OCGIS parcel layer.** Report which conditional fields exist: use code, year built, assessed values, owner name. That report decides which conditional signals stay or get cut, so do it first.
3. **Compute geometry signals:** lot size, frontage, rough buildable area, and building coverage (Overture/Microsoft footprint area ÷ lot area). Flag parcels with no footprint as vacant.
4. **Join signals to parcels:** HE sites, SB 35, public land, transit (HQTA/GTFS), LODES, TCAC opportunity, ACS, CalEnviroScreen, and the hazard layers (FEMA, CAL FIRE, CGS, coastal, CalGEM, EnviroStor/GeoTracker, NRHP).
5. **Tax-defaulted parcels:** extract APNs from the OC Treasurer PDFs. Keep this separate from the other joins because the parsing is messy.
6. **Scoring:** Development Potential, Feasibility Risk, and an Opportunity Score that combines them. Each parcel also gets a confidence level based on how many inputs are missing or low-confidence. SB 4 faith-based parcels are capped at low confidence.
7. **Reason strings:** for every score, list the top contributing signals in plain language, e.g. "High: 0.4 acre lot, 8% building coverage, inside HQTA."
8. **Dataset registry:** one record per source with its URL, license, refresh date, and ingest date. This is a Phase 1 exit requirement, not optional.
9. **Validation:** compare high-scoring parcels against APR Table A2 permits.
10. **API:** `GET /zip/{zip}` returns GeoJSON with scores, confidence, and reasons for each parcel.

## Done when

The API returns correct, documented output for all 3 sample ZIPs, including the one that crosses city lines.
