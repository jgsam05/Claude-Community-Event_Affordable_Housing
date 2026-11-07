# OC Affordable Housing Opportunity Finder

Enter an Orange County, CA ZIP code and get a ranked, mapped list of parcels that
look like good candidates for affordable housing: vacant land, parking lots,
underbuilt commercial, public/faith-owned land, and parcels where zoning or
state law could unlock more units. Every score shows its reasoning.

> **Status: working prototype running on SYNTHETIC demo parcels.** The pipeline,
> scoring, API and map are real and tested. The parcels, the zoning rules for the
> demo cities, and the state-law parameters are **not** real data yet. See
> "What is real vs. placeholder" before anyone relies on a result.

## Run it

```bash
pip install -r requirements.txt
python -m oc_housing.build          # fetches real OC boundaries, builds demo parcels
uvicorn oc_housing.api:app --reload # open http://127.0.0.1:8000
pytest                              # 40 tests
```

Demo ZIPs: `92701` (Santa Ana), `92805` (Anaheim), `92627` (straddles Costa Mesa and
Newport Beach on purpose). The map uses Leaflet and OpenStreetMap tiles from CDNs,
so the browser needs internet access.

## What is real vs. placeholder

| Piece | Status |
|---|---|
| OC city + unincorporated boundaries | **Real**, fetched live from OC GIS (`OCCityBoundaries`, layer 8). See assumptions below. |
| Jurisdiction join (parcel to city) | **Real**, spatial. ZIP codes are never used to pick a city. |
| Parcels | **Synthetic.** IDs start `SYN-`, flagged on every record and in the UI banner. |
| Zoning rules (Santa Ana, Anaheim) | **Sample values**, marked `SAMPLE-*`. Not municipal code. |
| Zoning for all other cities | **Not ingested.** Parcels there score on non-zoning signals, show "zoning not ingested", and get lower confidence. Zoning is never guessed. |
| State-law unit math (`config/laws.yaml`) | **Unverified** (`verified: false`). Written from general knowledge. Needs review by housing counsel or a city planner. |
| Hazard / transit / opportunity-area layers | **Not loaded.** The overlay mechanism is built and tested; the data is not downloaded. |

## Assumptions about the boundary layer (please verify)

Inspecting the live layer showed: 814 of 859 rows are empty (ignored); the 40 "City"
rows are 34 incorporated cities plus 6 unincorporated census communities (Coto de
Caza, Ladera Ranch, Las Flores, Midway City, North Tustin, Rossmoor); and the 5
"Unincorporated" rows are named `Supervisory District N` and do not overlap any
city. We treat communities and districts as **Unincorporated Orange County** (county
rules). The 34 count matches the known number of OC cities, which is a good sign,
but the community list and the district interpretation are mine. Confirm with
OC Public Works. Details: `config/jurisdictions.yaml`.

## Loading real data

1. **Parcels (do this first; it is the main blocker).** The OC Assessor does not
   publish attributed parcel data (use code, year built, values) as a free
   download. Its site points to ParcelQuest; vendors such as Regrid also sell it. Get
   an export as GeoJSON in EPSG:4326, set the column names in
   `config/parcel_mapping.yaml` (the names there are placeholders), translate your
   source's use codes in the same file, then:
   `python -m oc_housing.build --parcels data/parcels_in/your_export.geojson`
   The build reports unmapped use codes and skipped rows instead of guessing.
2. **Zoning, one city at a time.** Copy rules from the city's municipal code into
   `data/zoning/<city>.csv` (columns in `data/zoning/_TEMPLATE.csv`), with
   `source_url` and `retrieved` filled in. Put the city's zoning polygons in
   `data/overlays/` and declare them in `config/overlays.yaml` (`mode: value`) so
   each parcel gets a zone code. Start with the largest, highest-need cities.
3. **Constraints and signals.** Download fire hazard, flood, coastal zone,
   airport, contamination, Housing Element sites, and transit layers as GeoJSON
   polygons and declare them in `config/overlays.yaml`. Use `mode: flag` only for
   layers that cover the whole county, otherwise "outside the layer" would wrongly
   read as "checked and clear". Use `flag_inside_only` for partial layers.
4. **Distress.** Join the OC Treasurer-Tax Collector defaulted-property list on APN
   to fill `tax_default`.
5. **Review `config/laws.yaml`** with someone qualified, then set `verified: true`.

Verify each source's URL, license, and refresh date before use. Nothing here
scrapes anything.

## How scoring works (`config/scoring.yaml`)

- **Development Potential (0-100):** weighted average of land-use fit, underbuilt
  signals, lot size, legal upside (units unlockable), distress, ownership, and
  location.
- **Feasibility Risk (0-100, higher is worse):** coastal zone, fire, flood,
  airport, contamination, historic, mobile home park.
- **Overall** = potential reduced by a configurable fraction of risk.
- **Unknown data is excluded from the average, not counted as zero.** It lowers
  **confidence** instead. Use the Min confidence filter to hide thin-data parcels;
  note that a parcel with little data can otherwise rank well on what is known.
- Zoning known but no pathway yields housing counts as **zero upside** (not
  unknown), so non-residential lots do not rank high by default.
- Assessed values are caveated for Prop 13; a sale within 7 years is trusted over
  assessed land value for cost per unit.
- Mobile home parks are surfaced as **preservation watch**, not development targets.

Weights live in config; changing them re-scores on restart (or `POST /api/reload`)
with no ETL re-run.

## API

`GET /api/zip/{zip}` (filters: `min_score, max_risk, min_confidence, min_lot, city,
land_use, result_type`), `/api/zip/{zip}/export.csv|geojson`, `/api/zip/{zip}/gaps`,
`/api/parcel/{id}`, `/api/coverage` (zoning status for all 34 cities + county),
`/api/meta`, `/api/health`. Exports never include owner names, only owner type.

## Known limitations

- Frontend was syntax-checked and the API it calls is tested, but **the page has not
  been visually inspected in a browser.** Open it and report anything off.
- Scoring weights are reasoned defaults, not calibrated. The planned validation
  (backtest top-scored parcels against actually proposed or approved projects from
  HCD Annual Progress Reports and SB 35 / AB 2011 approvals) is **not built**.
- AB 2011 estimates skip the corridor adjacency and width test; SB 9 skips
  owner-occupancy and other conditions; density bonus assumes the maximum.
- No ZIP validation beyond "5 digits and data loaded." An authoritative OC ZIP list
  (Census ZCTA) is not wired in.
- Data lives in memory loaded from one JSON file. Fine for tens of thousands of
  parcels; for all of OC (~1M parcels) move to PostGIS or DuckDB and precompute per ZIP.

## Results are screening-level only

Not legal, zoning, or investment advice. Verify with the city and a qualified
professional before acting on any result.
