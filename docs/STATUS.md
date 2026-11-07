# Where we are (branch `data-reality-check`, 2026-11-07)

**One sentence:** we now have a working pipeline that takes a real Orange County ZIP and returns ranked, mapped sites with an Opportunity score, separate Development Potential and Feasibility Risk scores, a confidence level, and a plain-language reason for each. It runs on real public data for 4 ZIPs. It is a screening tool, not a verdict on any property.

## What works today
- **Real parcels** for ZIPs 92701 (Santa Ana), 92805 (Anaheim), 92627 (Costa Mesa) and 92780 (Tustin + unincorporated + a sliver of Irvine/Santa Ana). 34,668 sites after cleaning.
- **Real zoning codes, land use and plan density** for every parcel the state planning agency (SCAG) covers.
- **Real flood-zone checks** (FEMA, via OC Public Works).
- **Real Housing Element site flags** (sites cities themselves committed to for affordable housing).
- **City assignment by map location**, never by ZIP, so a ZIP that crosses city lines is handled correctly.
- **42 automated tests** pass. Every score has a "why" sentence. A dataset registry lists source, license and refresh date for each input.
- **Browser demo** (an Artifact, link shared in chat) shows the map, ranked list and reasons for the 4 ZIPs.

## What does NOT work yet (be honest in the demo)
- **No building size, year built, owner type, sale price or tax-default data.** No free source exists. Confidence therefore tops out near 65%, and the demo says so.
- **Zone limits are derived**, not read from each city's code: max units = SCAG general-plan max density x lot size. Good enough to rank, not good enough to promise unit counts.
- **State-law math** (density bonus, SB 9, AB 2011) is from general knowledge and flagged unverified. Needs a planner or housing attorney.
- **Hazards only partly loaded:** flood yes. Fire, coastal, contamination, airport: not yet (see `docs/DATA_GUIDE.md`).
- **Not validated** against real approved projects yet (spec task 9).

## Read next
`docs/DATA_GUIDE.md` (which data to trust and how we reshaped it), `docs/PRESENTATION.md` (how to show it), `docs/NEXT_STEPS.md` (task-by-task status against `data-pipeline-task.md`, plus opportunities).
