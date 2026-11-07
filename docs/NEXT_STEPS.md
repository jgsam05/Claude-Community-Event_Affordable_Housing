# Next steps and opportunities

## Status against `docs/data-pipeline-task.md`
| # | Task | Status |
|---|---|---|
| 1 | ZIP to parcels, tagged by city | **Partly done.** Uses OC `SiteZip5`, city by map location. Census ZCTA polygon version not built. |
| 2 | Describe parcel layer | **Done.** Has: address, APN, ZIP, assessed land/improvement value, lot area. Missing: use code, year built, owner name (mailing address only; we drop it). |
| 3 | Geometry signals | **Partly.** Lot size done. Frontage, buildable area, footprint coverage not built. |
| 4 | Join signals | **Partly.** Done: HE sites, zoning, plan density, flood. Not yet: SB 35, public land, transit, LODES, TCAC, ACS, CalEnviroScreen, fire, CGS, coastal, CalGEM, GeoTracker, NRHP. |
| 5 | Tax-defaulted APNs | **Not built.** OC Treasurer list is a PDF. |
| 6 | Scoring | **Done** (Potential, Risk, Opportunity, confidence). SB 4 low-confidence cap not built. |
| 7 | Reason strings | **Done.** |
| 8 | Dataset registry | **Done** (`config/datasets.yaml`, `/api/datasets`). Ingest dates still to add. |
| 9 | Validation vs APR Table A2 | **Not built.** |
| 10 | API `GET /zip/{zip}` | **Done** as `/api/zip/{zip}` (GeoJSON, scores, confidence, reasons). |

## Run it
```
cd prototype/oc-housing-finder
pip install -r requirements.txt
for z in 92701 92805 92627 92780; do python tools/pull_real_zip.py $z; done
python tools/build_real_sites.py
python tools/pull_flood.py
python -m oc_housing.build --profile real --parcels data/parcels_in/real_sites.geojson --mapping config/parcel_mapping_real.yaml
OC_PROFILE=real uvicorn oc_housing.api:app
pytest
```
(Pulling a ZIP takes about a minute. Raw files are git-ignored.)

## Highest-value moves (do these first)
1. **Footprint coverage** (Microsoft/Overture): gives "underbuilt" a real signal and raises confidence. Biggest single accuracy gain.
2. **Tax-default PDF parse**: the only free distress signal.
3. **Fire, coastal, GeoTracker, transit, TCAC** overlays: each lowers the "unknown" share and sharpens risk.
4. **Verify SCAG land-use codes** against SCAG's description document.
5. **Validation**: backtest the top 100 sites against approved or proposed projects (HCD APR Table A2). This is the credibility slide.
6. **Have a planner review `config/laws.yaml`** and flip `verified: true`.
7. **Real city zoning tables** for the 2 to 3 cities in the demo, replacing derived rules.

## Opportunities to push
- Housing Element and rezone sites let us say "the city already agrees". Rank those first and explain why.
- Preservation watch: mobile home parks and expiring-use subsidized housing (HUD LIHTC, 190 OC properties) are at-risk affordable units. Protecting them is cheaper than building.
- Ownership by public agencies and faith groups (SB 4) is the fastest path, but needs owner type, which needs a paid parcel source. Worth asking an organizer whether ParcelQuest access exists.

## Limitations (so nobody overclaims)
Screening only, not legal or investment advice. Weights are reasoned defaults, not calibrated. Condo stacks and ROW filters are heuristics. Prop 13 makes assessed values a weak proxy for market price.
