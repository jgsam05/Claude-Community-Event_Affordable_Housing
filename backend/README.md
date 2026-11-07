# Parcel Screener — back end

This turns raw public datasets into a scored parcel table and serves it as GeoJSON for `../parcel-screener-prototype`.

```
ZIP ─► Census ZCTA polygon ─► OCGIS parcels inside it ─► city / Unincorporated tag
    ─► geometry signals (lot, frontage, buildable, coverage, vacant)
    ─► registry-driven joins (HE, SB 35, public land, transit, jobs, TCAC, ACS, CES, OZ, hazards, preservation)
    ─► tax-defaulted APNs (separate PDF parser)
    ─► Development Potential, Feasibility Risk, Opportunity, confidence, reasons
    ─► GET /zip/{zip}  (GeoJSON, EPSG:4326)
```

## Run

```bash
pip install -r requirements.txt
python -m parcel_engine.cli describe-layer      # 1. field report for the parcel layer (do first)
python -m parcel_engine.cli samples             # 2. score 92618, 92620, 92705 -> data/scored/
uvicorn parcel_engine.api:app --port 8000       # 3. serve
```

Offline / demo: `PARCEL_ENGINE_MODE=fixture uvicorn parcel_engine.api:app`. This serves **synthetic** parcels for the three sample ZIPs. Tests run this way: `pytest -q`.

## Endpoints

| Route | Returns |
|---|---|
| `GET /zip/{zip}` | FeatureCollection, one Feature per parcel, sorted by Opportunity. `?refresh=1` rebuilds. 400 = not 5 digits, 404 = not a ZCTA or not in Orange County. |
| `GET /zip/{zip}/validation` | APR Table A2 comparison for that ZIP |
| `GET /registry` | Every dataset with URL, license, refresh date, ingest date, plus `phase1_gaps` |
| `GET /describe-layer` | Conditional-field report (live mode) |
| `GET /health` | mode, sample ZIPs |

Key Feature properties: `apn, address, jurisdiction, straddles_city_line, opp, development_potential, feasibility_risk, level, sig, signals_total, opp_reason, dev_reason, risk_reason, reasons[{dir,text,score}], missing[], low_confidence_inputs[], confidence_cap, rank`. All raw signal values are included too (lot_sqft, building_coverage, in_hqta, flood_sfha, dist_*_ft, …).

`metadata` holds the jurisdictions in the ZIP with parcel counts, `crosses_city_lines`, level counts, per-dataset load status and ingest date, `data_as_of`, and validation.

## Sample ZIPs

| ZIP | Why |
|---|---|
| 92618 | Irvine, the front end's normal case |
| 92620 | Irvine, the front end's thin-data case |
| **92705** | **Cross-city:** Santa Ana, Tustin, and unincorporated North Tustin. The city mix was confirmed from OCGIS footprint city labels; the boundary layer makes the actual assignment. |

## Data: what's automatic vs. manual

**Queried live from the publisher's own service:** OCGIS parcels, city boundaries, unincorporated area, building footprints, centerlines (County of Orange); TIGERweb ZCTAs and tracts and the ACS 5-year API (Census Bureau); FEMA NFHL; CGS liquefaction and Alquist-Priolo fault zones (Dept. of Conservation); CalGEM wells; SCAG Housing Element sites, rezone sites and 2024 existing land use.

**Manual download into `data/raw/`** (file names are in `registry.py` → `local_file`): SCAG HE sites/rezone, HQTA and land use; HCD compliance, SB 35, SLA notices; APR Tables H and A2; DGS; OSM worship and grocery; OCTA/Metrolink GTFS; LODES WAC; CDE schools; TCAC map; CalEnviroScreen; OZ list; CGS fault zones; CalGEM; EnviroStor; GeoTracker; NRHP; HCD mobilehome parks; HUD LIHTC and Section 8.

Tax-defaulted PDFs go in `data/raw/oc_treasurer_pdfs/`, then run `python -m parcel_engine.cli parse-tax-pdfs`.

A dataset that isn't present doesn't break anything. Its signals count as missing, which lowers confidence, and `metadata.datasets` shows `not_ingested`. Column names in downloaded files vary, so each join lists candidate column names. A mismatch shows up as `schema: …` in the dataset status.

## Design choices to review

- **Footprints default to OCGIS `Building_Footprints`, not Overture/Microsoft.** OCGIS can be queried by bounding box. Overture is supported as a file (`FOOTPRINT_SOURCE=overture_buildings`).
- **Every dataset comes from its original publisher** (or SCAG, which compiles HCD and assessor records), never a third-party mirror. Each registry record names the publisher and an authority tier; OpenStreetMap is used only for the two signals the project plan assigns to it and always counts as low confidence. See `docs/DATASETS.md`.
- **Parcel belongs to the ZIP containing its interior point**, so no parcel shows up in two ZIPs. A parcel cut by a city line is tagged with the city at its interior point and flagged `straddles_city_line`.
- **Valid OC ZIP** means at least 5% of the ZCTA's area falls inside OC city boundaries plus the unincorporated area.

## Phase 1 status

| Item | Status |
|---|---|
| Pipeline, scoring, reasons, API, registry, validation, tax PDF parser | Built, 22 tests pass (fixture + mocked HTTP) |
| describe_layer on OCGIS parcels | Done from layer metadata (see `docs/describe_layer_report.md`). Fill rates still to measure. |
| Real output for 92618 / 92620 / 92705 | **Not yet run.** The build environment couldn't reach county/state hosts. |
| Registry fully documented | URLs and licenses filled in. Most `license_verified` / `refresh_verified` are False until checked. `GET /registry` → `phase1_gaps` lists them. |
| Validation vs. APR A2 | Code done. Needs `apr_table_a2.csv`. |
