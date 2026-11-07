# Scoring method (v0.1.0)

All weights live in `parcel_engine/scoring.py`. Every number below is a starting assumption to test against APR Table A2, not a calibrated value.

## Confidence

There are 10 signals, matching the front end's "N of 10 signals". A signal counts as found when its dataset loaded and the parcel got a value. A layer that loaded but has nothing at the parcel counts as found: "not in a flood zone" is data, while "flood layer unavailable" is missing.

1. Lot size
2. Building coverage
3. Year built (vacant parcels count as found)
4. Land use code
5. Housing Element status
6. Transit access (HQTA or GTFS)
7. Jobs access (LODES)
8. Opportunity area (TCAC)
9. Rent burden / income (ACS)
10. Hazard layers (FEMA + CAL FIRE + CGS liquefaction all loaded)

Each low-confidence input that is true for a parcel subtracts 0.5 from the count. These are an OSM place of worship and a tax-defaulted APN parsed from a PDF.

| Effective signals | Level | Score shown |
|---|---|---|
| 9–10 | High | yes |
| 7–8.5 | Medium | yes |
| 5–6.5 | Low | yes (muted on map) |
| < 5 | Insufficient | no (`opp: null`) |

SB 4 faith-based parcels are capped at Low.

## Development Potential (0–100)

Core components are each 0–1, weighted, and renormalised over the components that are available:

| Component | Weight | Value |
|---|---|---|
| Lot size | 25 | log scale, 0.1 ac → 0, 2 ac → 1 |
| Building coverage | 25 | vacant → 1, else 1 − coverage/50% |
| Transit | 15 | in HQTA 1; rail ≤ ½ mi 0.8; bus stop ≤ ¼ mi 0.5 |
| Jobs | 10 | percentile of tract jobs within the ZIP |
| Opportunity area | 10 | High/Highest 1, Moderate 0.5 |
| Land use | 8 | SCAG code in `LAND_USE_UNDERUSED` (codes need verifying) |
| Age | 4 | built before 1980 |
| Amenities | 3 | grocery / school within ½ mi |

Bonus points are added on top, with the total capped at 100: HE site or rezone +15, public/surplus land +10, faith-based +5, SB 35 jurisdiction +3, HE out of compliance (builder's remedy watch) +2, tax-defaulted +2.

## Feasibility Risk (0–100, higher = harder)

Points are additive, capped at 100:

| Risk | Points |
|---|---|
| FEMA SFHA | 20 |
| Fire hazard zone: Very High / High / Moderate | 20 / 12 / 5 |
| Liquefaction | 10 |
| Alquist-Priolo fault zone | 15 |
| Coastal Zone | 10 |
| Oil well ≤ 100 ft / ≤ 500 ft | 15 / 8 |
| Cleanup site ≤ 250 ft / ≤ 1,000 ft | 15 / 6 |
| NRHP | 15 |
| Lot < 5,000 sq ft | 10 |
| Frontage < 40 ft | 5 |
| Existing mobile home park, LIHTC or Section 8 on parcel (preservation) | 20 |
| CalEnviroScreen ≥ 75th percentile | 5 |

## Opportunity Score

`Opportunity = Development Potential × (1 − 0.7 × Risk / 100)`

A parcel with zero risk keeps its full potential. At maximum risk it keeps 30%.

## Reasons

- Each score gets a summary such as `"High: Housing Element rezone site, vacant (no building footprint), inside HQTA."`.
- The `reasons` list (top 5) follows the front end template `[Signal] [value] — [comparison to ZIP].` and has `dir: up|down`.
- `missing` lists signal names. The front end renders these as "X unavailable — not scored."

## Validation

`validation.validate()` compares scored parcels with APNs in APR Table A2. It reports base rate, top-decile hit rate, lift and AUC. A2 includes ADUs and single-unit permits, so it tests "where housing gets built", not affordable feasibility. Read lift and AUC as a sanity check, not as accuracy.
