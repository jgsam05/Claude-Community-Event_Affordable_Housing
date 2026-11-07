---
title: "OCA presentation guide"
subtitle: "Script, talking points and judge Q&A"
---

# OCA presentation guide

OCA finds where affordable homes could go in Orange County. You type a ZIP code. OCA checks every parcel (every piece of land) in that ZIP using free public data, scores each one, and shows a ranked list and a map, with the sources and a confidence level for every score.

This guide has everything you need to present it: a 30-second pitch, a 3-minute script, the main points to remember, a plain-language explanation of how the pipeline works, and answers to the questions judges are likely to ask.

Fill in anything in **[brackets]** before you present.

---

# The goal (our north star)

Everything in this guide, the app and the video comes back to this goal:

> **Build a web tool where a user enters an Orange County, CA ZIP code and gets a ranked, mapped list of parcels that are strong screening candidates for affordable housing development or preservation, using only free, public datasets.**
>
> **Candidates come from:** vacant or lightly built parcels (building footprint coverage), Housing Element sites and rezone sites, publicly owned and surplus land, faith-based parcels, tax-defaulted parcels, and existing subsidized housing with expiring affordability (preservation).
>
> **Each parcel is scored on:** development potential (lot size, buildable area, coverage, Housing Element status, state-law pathways), location quality (transit, jobs, schools, grocery, opportunity area, CalEnviroScreen, ACS rent burden), and feasibility risk (flood, fire, seismic, coastal, oil wells, contamination, historic). **Every score shows its components, sources and a confidence level.**

## How OCA meets the goal today

| Goal | Status |
|---|---|
| ZIP in, ranked and mapped list out | **Built.** Real map, ranked list, filters, selected-site panel. |
| Free, public datasets only | **Built.** 43 datasets cataloged with publisher, license and refresh date. |
| Six kinds of candidates | **Built** as filters: vacant or lightly built, Housing Element and rezone sites, public or surplus land, faith-based, tax-defaulted, preservation. Some need datasets that still have to be downloaded. |
| Development potential: lot size, buildable area, coverage, Housing Element status, state-law pathways | **Built.** Lot size, buildable area, coverage, HE status; state-law pathways as bonus points (SB 35 / SB 423, SB 4 faith-based). |
| Location quality: transit, jobs, schools, grocery, opportunity area, CalEnviroScreen, rent burden | **Partly.** Transit, jobs, opportunity area, schools and grocery are scored inside development potential. CalEnviroScreen adds risk points. Rent burden is counted as a confidence signal but not yet in the score. A separate location-quality score is the next step. |
| Feasibility risk: flood, fire, seismic, coastal, oil wells, contamination, historic | **Built.** Each one adds risk points. |
| Every score shows components, sources and confidence | **Built.** Reasons on every score, a full score report per parcel, and a confidence level (High, Medium, Low or not scored). |

---

# 1. The big picture (read this first)

## The 30-second pitch

> Finding land for affordable housing means digging through scattered county records, one dataset at a time. OCA does that work in seconds. Type any Orange County ZIP code and OCA checks every parcel against free public data, finds the strong candidates for new affordable housing or for preserving existing affordable homes, ranks them, and shows them on a real map. Each parcel is scored on development potential, location and feasibility risk, and every score shows its components, its sources and how confident we are. It's built for the nonprofit developers, city staff and congregations who build and protect affordable housing and don't have a research team.

## One sentence for each audience

- **For a judge who isn't technical:** "It's a search engine for land that could become affordable housing."
- **For a technical judge:** "A data pipeline joins about 40 public datasets onto every parcel in a ZIP, scores development potential, location quality and feasibility risk with a confidence level, and serves the result as GeoJSON to a map front end."
- **For a housing expert:** "It's a first-pass site screen: Housing Element sites, public and surplus land, faith-based land, tax-defaulted parcels and expiring subsidies, ranked and flagged for risk."

## Why it matters

- Land is the first hurdle for affordable housing, and finding it is slow and expensive for small organizations.
- The data exists (counties, cities, state and federal agencies publish it for free), but it lives in dozens of separate places and formats.
- OCA puts it in one place, scores it, and shows its work, so a person can defend the result to a board, a funder or a city council.

## Where the candidates come from (the six kinds of sites)

OCA doesn't just score every parcel the same way. It also flags **why** a parcel is a candidate:

1. **Vacant or lightly built:** little or no building on the lot, measured from county building footprints.
2. **Housing Element and rezone sites:** land a city has already listed, or plans to rezone, for new housing.
3. **Publicly owned and surplus land:** land owned by a public agency that may be available for housing.
4. **Faith-based parcels:** land owned by religious organizations, often with unused parking or space. State law (SB 4) makes housing on it easier.
5. **Tax-defaulted parcels:** property with long-unpaid taxes that may go to sale.
6. **Preservation:** existing subsidized housing whose affordability restrictions are about to expire, so it can be kept affordable.

## Who uses it

- **Main users:** small and mid-size nonprofit affordable-housing developers, and city and county housing staff.
- **Also:** congregations with spare land or parking, community groups and advocates, journalists and researchers.
- **Not the target:** large private-equity firms. They already pay for parcel data and underwriting tools.

---

# 2. How it works, in plain language

Think of OCA as an assembly line with four stations.

## Station 1: Pick the area

- You type a ZIP code.
- OCA looks up that ZIP's boundary from the U.S. Census Bureau.
- It confirms the ZIP is really in Orange County.

## Station 2: Collect every parcel

- OCA pulls every parcel inside that boundary from the County of Orange's official parcel map. Each one has a shape, an ID number (called an APN), a street address and sometimes a year built.
- It tags each parcel with its city (or "unincorporated") so you can see when a ZIP crosses city lines.
- It adds building footprints from the county, so it can measure how much of each lot is already built on.

## Station 3: Measure and attach facts

- **Measure the lot:** size, shape, street frontage, how much is buildable, how much is covered by buildings, and whether it is vacant.
- **Attach public datasets:** the pipeline checks each parcel against other public layers:
  - Is it on a city's Housing Element list of sites for new housing, or a rezone site?
  - Is the land publicly owned or surplus? Owned by a religious organization? Tax-defaulted?
  - Is it near transit or jobs? In a high-opportunity area?
  - Is there existing subsidized housing nearby with expiring affordability?
  - Flood, fire, earthquake (liquefaction and fault zones), coastal zone, oil wells, contamination, historic status.

## Station 4: Score it and explain it

Every parcel is scored on the three lenses from our goal, plus a confidence label:

| Lens | Plain-language question | What goes into it |
|---|---|---|
| **Development potential** | Can homes fit here? | Lot size, buildable area, building coverage, Housing Element status, state-law pathways (SB 35, SB 4), public and tax-defaulted bonuses |
| **Location quality** | Is it a good place for homes? | Transit, jobs, schools, grocery, opportunity area. Today these are built into the development potential score. CalEnviroScreen adds to risk. Rent burden is counted toward confidence. |
| **Feasibility risk** | What could go wrong? (lower is better) | Flood, fire, earthquake (liquefaction and faults), coastal zone, oil wells, contamination, historic status, tiny lots, preservation conflicts |
| **Confidence** | How much data stands behind this? | High, Medium, Low, or "not scored" |

On top of those, the engine combines potential and risk into one **Opportunity** score, which is what the ranking uses.

**The formula, simply:** Opportunity = development potential, reduced by risk. A site with no risk flags keeps all of its potential. A site with maximum risk keeps 30% of it.

**Each score comes with reasons in plain English**, like "6.15 acre lot, vacant, no building footprint," and a list of any data that was missing.

## What the user sees

- A ranked list of sites with a score ring on each card.
- A real map of the area with the parcels drawn on it and numbered pins on the best sites.
- Click a site to see its three scores, the reasons behind them and what to check first.
- A full score report for any parcel: every input, its value, its public source and its confidence.
- Filters for the six kinds of sites: vacant or lightly built, Housing Element sites, public or surplus land, faith-based, tax-defaulted and preservation (existing subsidized housing).
- Save the list as a CSV, or print the report.

---

# 3. The workflow, step by step

## The user's workflow (five steps)

1. **Enter a ZIP code.** Any Orange County ZIP.
2. **Pick the kind of site you care about.** Filter by vacant land, public land, faith-based land and so on.
3. **Read the ranked list.** Best matches first, each with a one-line reason.
4. **Select a site on the list or the map.** See its three scores and what to check first.
5. **Open the full score report.** Every input with its source and confidence, so you can explain it to others.

## The data workflow (behind the scenes)

```
ZIP code
  -> Census ZIP boundary
  -> County parcels inside it
  -> City / unincorporated tag
  -> Measure each lot (size, shape, buildings, vacant)
  -> Join public datasets (housing sites, public land, transit, jobs,
     opportunity, hazards, preservation)
  -> Score: development potential, feasibility risk, opportunity
  -> Confidence level + plain-English reasons
  -> GeoJSON from the API
  -> Map and list in the web app
```

## The team workflow

- **Backend (scoring engine and API):** a Python service that builds the scored table and serves it at `GET /zip/{zip}`.
- **Front end:** a plain JavaScript app that shows what the backend returns. It never recomputes scores, so the numbers always match the engine.
- **Design:** one design guide covers the brand, colors, type, voice and screens, so everything looks and reads as one product.
- **Demo video:** a 30-second video, built on the real map and real scores.

---

# 4. The three ideas that make it trustworthy

## 1. Every score shows its work

- No mystery numbers. Each score has components, plain-English reasons, and public sources.
- This matters because OCA's users have to explain their choices to boards, funders and city councils.

## 2. Confidence is built in

- OCA counts 10 data signals per parcel: lot size, building coverage, year built, land use, Housing Element status, transit, jobs, opportunity area, rent burden, and hazards.
- **High** confidence: 9 to 10 signals. **Medium:** 7 to 8.5. **Low:** 5 to 6.5 (shown muted on the map). **Below 5: not scored.** OCA refuses to guess.
- Missing data always says so, for example "Transit access unavailable, not scored."

## 3. It only uses free public data, from the original publisher

- County, state and federal agencies publish the data. OCA catalogs every dataset with its publisher, license and refresh date (43 datasets so far).
- Nothing comes from a paid or third-party mirror. The one community source is OpenStreetMap, used for two signals (places of worship and grocery stores) and always marked low confidence.

---

# 5. The 3-minute script

**Speaker notes are in italics. Times are approximate. Speak slowly. Pause after each section.**

## Opening (0:00 to 0:20)

*[Show the title slide or the OCA home screen.]*

"Hi, we're **[team name]**. We built **OCA**, a free tool that finds where affordable homes could go in Orange County.

Let me start with the problem."

## The problem (0:20 to 0:45)

"Finding land for affordable housing is slow. The information is out there, but it's scattered. The county has one map for parcels. The cities each publish their own housing plans. The state has lists of public land. FEMA has flood maps. Someone has to pull all of that together by hand, parcel by parcel.

A big developer can pay for that. A small nonprofit, a city planner or a congregation usually can't."

## Who it's for (0:45 to 1:00)

"OCA is for the people who build and protect affordable housing: nonprofit developers, city and county staff, congregations with spare land, and community groups."

## The demo (1:00 to 2:00)

*[Switch to the app, or play the demo video. Show the real map.]*

"Here's how it works. You type in a ZIP code. I'll use **92701**, downtown Santa Ana.

OCA pulls every parcel in that ZIP from the county's official records: **[5,312]** of them. It measures each one and checks it against public datasets: Housing Element sites, public and faith-based land, tax-defaulted parcels, subsidized housing, transit and jobs, and flood, fire and earthquake zones.

On the left is a ranked list of the best places to look. On the right is a real map of Santa Ana with the actual parcels drawn on it. The numbered pins are the top sites.

I'll click the first one. It's a **[6-acre]** vacant parcel. OCA shows three things:

- **Can homes fit?** The development potential: **[97 out of 100]**.
- **What could go wrong?** The feasibility risk: **[0]**, since no hazard flags were found.
- **How much data is this based on?** The confidence: **[6 of 10]** data signals found.

And it says in plain words why it ranked here: a large lot, vacant, no building on it. Location matters too: things like transit, jobs, schools and groceries are built into that potential score, and flood, fire, earthquake and contamination count against it as risk.

Notice the confidence is **Low** for this ZIP. That's on purpose. Some of our datasets, like transit and neighborhood opportunity data, aren't loaded yet, so OCA tells you so instead of pretending to be sure. It never hides what it doesn't know."

## How it works (2:00 to 2:25)

"Behind the screen, there's a data pipeline. It starts with the ZIP boundary from the Census, collects every county parcel inside it, measures each lot, and joins in public datasets. Then it scores each parcel on **development potential**, **location quality** and **feasibility risk**, and combines them into an overall **opportunity** score, which is potential reduced by risk. Every score comes with its components, its sources and a confidence level. The front end just shows what the engine produces. It never changes the numbers."

## Close (2:25 to 3:00)

"OCA is a screening tool. It tells you where to look first. It doesn't replace checking zoning, ownership and a title report, and we say that on every screen.

What's built today: the pipeline, the scoring engine, a real working map, and a score report with sources and confidence for every parcel, running on real Orange County data.

What's next: loading the remaining datasets so confidence goes up, adding zoning, and testing our scores against where housing actually gets built.

We built OCA so a small team can find a good site in minutes instead of weeks. Thank you. We'd love your questions."

---

# 6. If you have less or more time

## 60-second version

1. **Problem:** "Land for affordable housing is hard to find. The data is scattered."
2. **Solution:** "OCA: type a ZIP, get a ranked, mapped list of parcels worth a closer look, from free public data."
3. **Demo:** show the map, click one site, show the three scores and the confidence.
4. **Trust:** "Every score shows its reasons, sources and confidence. When data is missing, it says so."
5. **Close:** "A first look, built for small teams who can't buy expensive tools."

## If you have 5 minutes

Add these to the 3-minute script:

- Open the **score report** for one parcel and show the table of inputs, sources and confidence.
- Show the **filters** (vacant, public land, faith-based, tax-defaulted, preservation).
- Open the **Sources & methods** page and show the formula and the dataset list.
- Show the **How to use** page.

---

# 7. Major points to remember

## The product, in five bullets

- OCA = ZIP code in, ranked and mapped list of strong screening candidates for affordable housing development or preservation out.
- It finds candidates from six sources: vacant or lightly built land, Housing Element and rezone sites, public and surplus land, faith-based parcels, tax-defaulted parcels, and subsidized housing with expiring affordability.
- It scores each parcel on development potential, location quality and feasibility risk, then ranks by an overall opportunity score.
- Every score comes with plain-English reasons, public sources and a confidence level.
- It uses only free public data, directly from the agencies that publish it.
- It is a **screening tool**: it says where to look first, not what to build.

## The numbers worth knowing

| Fact | Number |
|---|---|
| Data signals per parcel | 10 |
| Confidence levels | High (9 to 10 signals), Medium (7 to 8.5), Low (5 to 6.5), Not scored (under 5) |
| Datasets cataloged | 43 (15 pulled live, 2 stored in the repo, 26 still need manual download) |
| Scoring lenses | 3 (development potential, location quality, feasibility risk), combined into an overall opportunity score, plus confidence |
| Kinds of sites | 6 (vacant or lightly built, Housing Element, public or surplus land, faith-based, tax-defaulted, preservation) |
| Our real test run | ZIP 92701 (Santa Ana): **5,312 parcels** pulled from county records, 5,311 scored |
| Opportunity formula | Development potential x (1 - 0.7 x risk / 100) |

## What counts as location quality

Transit access (high-quality transit areas, rail and bus stops), jobs nearby, a high-opportunity neighborhood, and schools and grocery within about half a mile. Pollution burden (CalEnviroScreen) adds risk. Rent burden (how many renters pay over 30% of income) is counted as a data signal for confidence.

## What development potential rewards

- Big lots and lots with little or no building on them (the two biggest factors).
- Being near transit, jobs and high-opportunity areas.
- Being on a city's Housing Element list or rezone list (bonus points).
- Public or surplus land, faith-based land and tax-defaulted parcels (smaller bonuses).

## What feasibility risk penalizes

Flood zone, fire zone, liquefaction, earthquake fault, coastal zone, oil wells, nearby contamination, historic status, very small lots, narrow frontage, and parcels with existing subsidized housing that could be lost.

## Usability points

- **Plain language everywhere.** The three scores are explained as questions: "Can homes fit?", "What could go wrong?", "How much data is there?"
- **The list is the accessible version of the map.** Every score and reason exists as text, and every map pin is a labeled button.
- **Never color alone.** Confidence is always a word ("Low confidence"), not just a color. Map pins carry rank numbers.
- **Readable.** Text is at least 13 pixels, with strong contrast; the layout works on a phone.
- **Easy to learn.** A one-click "How to use" page explains who it's for, the five steps and a glossary. Every screen says "screening tool, not a feasibility study."
- **Shareable.** Save the ranked list as a CSV or print any parcel's report.
- **Keyboard friendly.** Press Esc to close a selected site; all controls are real buttons.

---

# 8. Honest status (be upfront with judges)

Judges respect clear limits. Say these plainly.

## What works today

- The full pipeline: ZIP boundary, county parcels, building footprints, lot measurements, joins, scoring and reasons.
- A web app with a real map, ranked list, filters, selected-site panel, score report, how-to page and methods page.
- A real run on ZIP 92701: 5,312 real parcels scored from county records.
- A dataset catalog with the publisher, license and refresh date for every source.
- A 30-second demo video on the real map.

## What is not finished (and what we say about it)

- **Confidence is Low in our real run.** Only 6 of 10 signals loaded. Missing: transit access, opportunity area, rent burden and hazard layers. The census rent data now needs an API key. The scores are real, and OCA labels the gaps instead of hiding them.
- **26 datasets still need a manual download.** Examples: transit schedules, the state opportunity map, CalEnviroScreen, and the tax-defaulted property lists.
- **Location quality isn't its own score yet.** Transit, jobs, opportunity area, schools and grocery are scored inside development potential. Rent burden counts toward confidence, not the score. Splitting out a separate location score is a next step.
- **Zoning is not included yet.** OCA says so in the footer of every page.
- **Scores aren't validated yet.** The backend has code to compare scores against where housing actually got built (state APR Table A2), but we haven't run it. The weights are starting assumptions to test.
- **Data freshness varies.** Parcel records are current as of the pull date. Some publishers don't list a refresh date.
- **We checked one ZIP end to end.** The engine is built for any Orange County ZIP, but 92701 is the one we ran live.

## One technical detail you may be asked about

On the day of the run, the county's main "FeatureServer" parcel service returned errors. We switched the pipeline to the county's "MapServer" version of the same layers, which worked. That change is noted in the backend README.

---

# 9. Questions judges may ask (and good answers)

**Is this real data or fake?**
"Real. The 92701 results come from the County of Orange's own parcel records and public datasets, pulled live. The first demo screens used sample data and were labeled that way."

**Why is the confidence Low?**
"Because we're honest about what's missing. We counted 10 data signals; our run found 6. Transit, opportunity-area and rent data aren't loaded yet. The scores are real, but the label tells you they stand on less evidence."

**How do you know the scores are right?**
"We don't claim they're final. They're a transparent starting formula. Every reason is shown so a person can disagree. The backend includes a validation step that compares scores to where housing was actually permitted. That's the next test we run."

**Why not just use Zillow, CoStar or a GIS tool?**
"Paid tools cost money and are built for market investors. Public GIS maps show one question at a time. OCA combines the housing-specific questions into one ranked, explained list, free."

**Who owns the land? Can you contact the owner?**
"OCA doesn't show owner names. It points to promising parcels. The next step, confirming ownership and zoning, is done with the city and a title report."

**Your goal says three scores, including location quality. Where is it?**
"Location quality is in the engine: transit, jobs, opportunity area, schools and grocery all feed the potential score, CalEnviroScreen adds risk points, and rent burden counts toward confidence. We haven't split it into its own number yet, and we'd rather say so than pretend."

**How do you handle preservation, not just new buildings?**
"Preservation is one of our six site types: existing subsidized housing, like mobile home parks and tax-credit or Section 8 properties, is flagged. Those parcels also get risk points, because redeveloping them could mean losing affordable homes."

**What state laws does it consider?**
"Streamlining under SB 35 (now SB 423) and faith-based housing under SB 4. They add bonus points to development potential, and the reason is shown on the card."

**What about zoning?**
"Not included yet, and we say so on every screen. It's the first thing we'd add. Housing Element status is included as a proxy, since those sites are already identified for housing."

**Can it work for other counties?**
"The pipeline is built around registries of datasets, so another county would mean swapping in its parcel layer and adding its local housing data. The state and federal sources already cover all of California."

**How often is the data updated?**
"Each dataset has a recorded refresh date in the catalog. The backend can rebuild a ZIP on demand, so it's as fresh as the publishers' data."

**Is it fair? Could it steer housing to the wrong neighborhoods?**
"It reports need and opportunity side by side instead of hiding either. Its location data includes neighborhood opportunity and pollution burden. And because every reason is visible, people can question the ranking."

**What would you build next?**
"Load the remaining datasets so confidence goes up, add zoning, run the validation against real permits, and let a user compare sites side by side."

**Why a screening tool, not a decision tool?**
"Because land decisions depend on zoning, ownership, price and site conditions we can't see in public data. OCA saves the first weeks of research so teams spend money checking the best sites."

---

# 10. Demo checklist

Before you present:

- [ ] Run the app and open **ZIP 92701** (`http://localhost:8001/#/zip/92701`). It works without the backend.
- [ ] Check the internet connection (the map tiles load from Esri).
- [ ] Have the **demo video** ready as a backup.
- [ ] Practice clicking: ZIP, first site, the score report.
- [ ] Know your numbers: **5,312 parcels**, **10 signals**, **3 scores**, **6 kinds of sites**, **43 datasets**.
- [ ] Decide who says what: **[Presenter 1: problem and demo]**, **[Presenter 2: how it works and close]**.
- [ ] Prepare to answer: "Why is confidence Low?" and "What about zoning?"

If the map doesn't load: the list and score report show the same information as text. Say so, and continue.

---

# 11. Glossary (say these in plain words)

| Term | Plain meaning |
|---|---|
| **Parcel** | One piece of land with its own number in the county records. |
| **APN** | Assessor Parcel Number, the unique ID for a parcel. |
| **Housing Element** | The part of a city's plan that lists where new housing can go. |
| **Rezone site** | Land a city plans to change the rules on so housing can be built. |
| **Surplus land** | Public land an agency no longer needs. State law can require offering it for housing first. |
| **Faith-based parcel** | Land owned by a religious organization, often with unused parking or space. State law makes it easier to build housing on it. |
| **Tax-defaulted** | Property with long-unpaid taxes that may go to sale. |
| **Preservation** | Keeping existing affordable homes affordable when their rent restrictions are about to expire. |
| **Building coverage** | The share of a lot covered by buildings. Low coverage means more room to build. |
| **Liquefaction** | Ground that can turn soft in an earthquake. |
| **CalEnviroScreen** | A state score of how much pollution burden a neighborhood carries. |
| **Rent burden** | When renters pay more than 30% of their income on housing. |
| **GeoJSON** | A standard file format for map shapes and their data. |
| **API** | The way the web app asks the backend for results. |

---

# 12. Where everything lives

- **Web app:** `parcel-screener-prototype/` (open it with `python -m http.server 8001`).
- **Backend and scoring:** `backend/` (see `backend/README.md` and `backend/docs/scoring.md`).
- **Dataset catalog:** `docs/DATASETS.md` and `docs/datasets.csv`.
- **Design guide:** `design/DESIGN.md`.
- **Demo video source:** `design/video/`.
- **Real 92701 snapshot:** `parcel-screener-prototype/data/92701.geojson`.
