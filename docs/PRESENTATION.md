# How to present this

The visualization carries the pitch. Three jobs: show where, show why, show how sure.

## What the demo already does
- Map of the top candidates colored by Opportunity, Development Potential, or Feasibility Risk.
- Ranked list and a detail panel with the plain-language "Why", the three scores, and confidence.
- Outline color per city, so the cross-city ZIP (92780) is visible at a glance.
- The dataset registry on the same page (source, license, refresh).

## Story for judges (90 seconds)
1. **Problem:** affordable housing sites are hidden in scattered public data.
2. **Show 92780:** one ZIP, two jurisdictions, different rules. Click the top site and read its reason.
3. **Show confidence:** point at the 65% ceiling and say exactly what data would raise it. Honesty about limits is a strength here.
4. **Show the data work:** 30% of rows were condo duplicates and freeway land. Cleaning them changed the ranking.
5. **Ask:** a planner or city partner to supply zoning rules and tax-default lists.

## Visualization upgrades, in priority order
1. Real basemap (street tiles) in the team's own site. The Artifact page cannot load tiles, but a normal web app can.
2. Show *all* sites in the ZIP faintly and the top candidates strongly, so people see what was screened out.
3. Side-by-side scores: Potential on one axis, Risk on the other, so "high potential, high risk" sites are visible. A scatter plot linked to the map.
4. A "what would raise confidence" meter per parcel that names the missing data.
5. Equity layer: overlay CalEnviroScreen and TCAC opportunity areas, so the tool can say "this site is in a high-opportunity area".
6. Before/after of the data cleaning (rows to sites) as a one-slide proof of rigor.
