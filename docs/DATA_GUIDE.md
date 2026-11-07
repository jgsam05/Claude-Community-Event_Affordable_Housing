# Data guide: what to use, what we changed, and why

Full machine-readable registry: `prototype/oc-housing-finder/config/datasets.yaml` (source, license, refresh date, status, caveats, rejected candidates). Readable table: `prototype/oc-housing-finder/DATASETS.md`.

## Use these (verified: queried live, returned Orange County rows)
| Need | Source | Join key | Note |
|---|---|---|---|
| Parcel shapes, address, assessed land and improvement value | OC Public Works "Legal Lots" (988k rows) | APN (AssessmentNo, strip dashes) | Values present on 84-96% of rows. Contains owner mailing address: we never ingest it. |
| Zoning code per parcel, all cities | SCAG Zoning_poly_OR | 8-digit APN (APN24) | Code only. No density, height or parking. |
| Existing land use | SCAG Existinglanduse_poly_OR (LU24) | APN24 | Our code map is partly unverified; unmapped codes are listed, never guessed. |
| Planned density and FAR | SCAG GeneralPlan_poly_OR | APN24 | The key to estimating units without city codes. |
| Housing Element sites | SCAG HousingElementSite_poly_scag (2,126 OC rows) | APN24 | Strong positive signal. |
| Flood | OC flood polygons (FEMA NFHL) | map location | Inside flood zone = risk. Inside mapped minimal-hazard zone = clear. "Not mapped" = unknown. |
| City / unincorporated | OC city boundaries | map location | ZIP is never used to pick a city. |
| Contamination | State GeoTracker (4,788 OC sites) | map location | Verified, not yet ingested (needs point buffering). |
| Neighborhood context | CalEnviroScreen 4.0 (582 OC tracts), TCAC opportunity areas | map location | Verified / candidate. |
| ZIP list | Census ZCTA (86 inside OC) | n/a | List saved in `data/raw/oc_zctas_candidate.json`. |

## How we reshaped the data (this is the "restructure" answer)
1. **Collapsed condo stacks into sites.** 22-30% of parcel rows are condo units that repeat one polygon (for example, 521 S Lyon St units 1 to N). SCAG does not match them by APN. Scored as separate parcels they would flood the map with duplicate dots and rank condo buildings as targets. We merge rows with identical geometry, sum the values, keep the unit count, and apply a "fragmented ownership" risk. (`tools/build_real_sites.py`)
2. **Removed freeway right-of-way.** Caltrans land such as "NA SANTA ANA FWY" showed up as huge vacant parcels and took the top ranks. We filter by address and drop slivers under 1,500 sq ft and non-lot types (1,000+ rows).
3. **Derived zone rules from plan density.** For each city and zone code we take the median positive SCAG general-plan max density and the majority land-use category (124 rules, all marked DERIVED, with a caveat on every affected parcel). Cities' real codes can replace these one at a time.
4. **Kept "unknown" separate from "no".** Outside a partial layer stays unknown and lowers confidence. It is never treated as clear.
5. **Added profiles.** `--profile real` and `OC_PROFILE=real` switch to real data without touching the synthetic demo and tests.

## Findings the team should know
- **92780 is the real cross-city ZIP** (Tustin 7,669 sites, unincorporated 1,643). 92627 is almost all Costa Mesa. Use 92780 as the required cross-city sample. In the OC parcel layer, `SiteZip5` is the address ZIP, so ZIPs rarely split across cities; the Census ZCTA polygon test in the task spec will expose more crossings.
- **The coastal layer is wrong for Huntington Beach and San Clemente.** Point tests on the pier and PCH fell outside it. Never treat "outside" as "not coastal".
- **SCAG land-use codes are only partly documented** in what we could fetch. Confirm against SCAG's code description PDF before trusting 1130 (mobile home parks) and the unmapped codes (3100 is common in Tustin and Irvine).
- **Free data stops at the parcel line.** Building area and year built need ParcelQuest or Regrid, or an estimate from Microsoft/Overture footprints (ODbL license).
- **Most sources state no license.** Registry says "not stated". Confirm before redistributing outside the event.

## Rejected (do not use)
Three search hits turned out to be other counties (Orange County NC, Mariposa, Sonoma). One state layer needs a token. Two hosts blocked access from our environment; we did not work around that.
