# OCA design principles and style guide

This is the single reference for how OCA looks, sounds and behaves. Every screen, page and video should follow it. The visual source is in `oca-canvas/`.

## 1. What OCA is

OCA is a free screening tool. A person enters an Orange County, CA ZIP code and gets a ranked, mapped list of parcels worth a closer look for affordable housing, either new development or preservation of existing affordable homes. It uses only free public data, and every score shows its components, sources and a confidence level.

OCA points people to where to look first. It does not confirm zoning, ownership, price or buildability. This is always said plainly.

## 2. Who it is for

Main audience: small and mid-size nonprofit affordable housing developers, and city and county housing staff.

Also: congregations with spare land, community groups and advocates, and journalists and researchers.

Not the target: large private equity firms. They already have paid parcel data and underwriting tools. Affordable-housing and preservation funds are the narrow exception.

Design for professionals who are not engineers and who must explain results to a board, funder or council. Credibility and clarity matter more than delight.

## 3. Principles

1. **Say what it is for, every time.** A new visitor must understand the purpose within seconds. Results pages open with "What OCA does", and a How to use page is one click away.
2. **Show the reasoning.** Never show a score without its parts. Each number has components, a public source and a confidence level.
3. **Friendly first, detail on demand.** Plain-English labels and a one-line reason come first. Raw inputs, sources and tables sit one step deeper. Direction A is the default experience. Direction B (the data view) serves professionals.
4. **Calm and credible.** No stock photos, hype, gradients or decoration. Quiet surfaces, clear hierarchy, honest limits.
5. **Easy to read.** Body text is at least 14px, and most reading text is 15 to 17px. Small labels are never below 13px. Touch targets are at least 44px.
6. **Never color alone.** Every status also carries a word, for example "High confidence". Colors that must be told apart also differ in lightness.
7. **Sample data is labeled.** Any placeholder parcel, score or number is marked as sample data until real data is connected.

## 4. Name and logo

- The name is **OCA**, always three capital letters. Never "Oca" or "oca", in the logo, headings, page titles, alt text or copy. It does not stand for anything specific.
- Wordmark: Archivo ExtraBold (800), wide letter-spacing (about 0.1em).
- Symbol: four slightly tilted, uneven parcel shapes in a 2×2 arrangement. Each is semi-transparent (about 45% fill) with a solid outline of the same color. A solid circle with a white ring sits inside each one, like the pins on the map. Corners are lightly rounded.
- Color assignment: top-left blue, top-right yellow, bottom-left green, bottom-right orange.
- Versions: full color on light, light tints on dark, white on blue, one color (ink) for single-color use, and a standalone app icon.
- Keep clear space around the mark of at least the height of one circle. Do not rotate, recolor outside these versions or stretch it.

## 5. Color

| Name | Hex | Use |
| --- | --- | --- |
| Blue | `#2B5FC7` | Primary actions, links, candidate pins |
| Blue dark | `#1E4399` | Link text and hover on light backgrounds |
| Green | `#12844A` | Strong scores, complete data |
| Yellow | `#E8A800` | Highlights, partial data. Never used for text on white |
| Orange | `#C2490F` | Selection, risk and warnings |
| Ink | `#1B1F2A` | Text, one-color logo, dark surfaces |
| Muted text | `#4B5363` | Secondary text |
| Border | `#DDE1E8` | Lines and card edges |
| Ground | `#F7F8FA` | Page background |
| Surface | `#FFFFFF` | Cards and panels |

Soft tints for chips and callouts: green `#E3F3EA` (text `#0B5E34`), yellow `#FFF3CC` (text `#5A4000`), orange `#FBE7DD` (text `#8A3208`), blue `#E8EEFB` (text `#1E4399`).

Meaning is consistent everywhere: green is good or complete, yellow is partial or caution, orange is risk or selection, blue is action.

Confidence labels: **High** (green tint) for complete, current public records. **Medium** (yellow tint) for derived or partly estimated values. **Low** (orange tint) for missing or stale data.

Text must meet 4.5:1 contrast on its background (3:1 at 24px and above).

## 6. Typography

- **Archivo** (600 to 800): headings, scores and the wordmark. Sharp and compact.
- **IBM Plex Sans** (400 to 600): body copy, tables, labels and buttons. Crisp at small sizes.
- **JetBrains Mono**: parcel IDs (APNs) and source labels in the data view only.

Scale: page title 44 to 48px, section title 26 to 30px, card title 17 to 20px, body 15 to 17px, small text 13 to 14px. Scores use Archivo 700 to 800. Numbers in tables use tabular figures.

Use sentence case for headings, labels and buttons. Only the name OCA is in capitals. Buttons start with a verb: "Find sites", "See how it was scored", "Open OCA".

## 7. Layout, shape and motion

- Spacing follows a 4 and 8 point rhythm. Page gutters are 32px on desktop and 16px on phones.
- Pages are fluid, with a content max width of about 1120 to 1280px. At phone width, columns stack, toolbars wrap and wide tables scroll inside their own box.
- Direction A: rounded cards (16px radius), pill buttons and chips, soft borders, score ring on each card.
- Direction B: tighter, 8px radius, thin borders, dense table, tabular numbers.
- Map pins are real buttons with an accessible name. The selected site is always orange and larger.
- Motion is soft and short. Respect reduced-motion settings. No decorative animation.

## 8. Voice and copy

- Plain language. Explain terms like Housing Element, APN and surplus land the first time, or link to the glossary.
- Honest and direct. Say what the tool does and does not do.
- No invented statistics. Missing facts are marked as placeholders.
- Avoid blame in errors and always offer a way to recover.

## 9. The three scores

Every site gets three scores out of 100. Overall = 45% development potential + 35% location quality + 20% (100 minus feasibility risk).

| Score | Direction | Plain-English question | Inputs |
| --- | --- | --- | --- |
| Development potential | Higher is better | Can homes fit? | Lot size, buildable area, building coverage, Housing Element status, state-law pathways |
| Location quality | Higher is better | Is it a good location? | Transit, jobs, schools, grocery, opportunity area, CalEnviroScreen, rent burden |
| Feasibility risk | Lower is better | What could go wrong? | Flood, fire, seismic, coastal, oil wells, contamination, historic |

Every component lists a value, its public source and a confidence level.

## 10. The six kinds of sites

Vacant or lightly built, Housing Element sites (including rezone sites), public or surplus land, faith-based parcels, tax-defaulted parcels, and preservation (existing subsidized housing with expiring affordability).

## 11. Pages and screens

| Screen | Purpose |
| --- | --- |
| Results (Direction A) | Default view: ZIP search, filters, ranked cards, map, selected-site panel, "What OCA does" explainer |
| Data view (Direction B) | Dense table with sources per score group, for professionals |
| Parcel score report | Every input with its source and confidence |
| How to use | Who it is for, five steps, reading the scores, site types, limits, glossary |

## 12. Demo video (30 seconds)

Half introduction, half user demo.

- 0 to 4 s: the problem. 4 to 9 s: who it is for. 9 to 15 s: what it is.
- 15 to 20 s: search a ZIP. 20 to 25 s: the three scores. 25 to 30 s: sources, then the OCA end card.
- About 74 words of voiceover, captions on, calm instrumental music, OCA colors and type only.
- Demo scenes should be a real screen recording of the working app.

## 13. Checklist before shipping any screen

- [ ] The name is OCA in capitals everywhere
- [ ] A new visitor can tell what OCA is for
- [ ] Every score shows components, sources and confidence
- [ ] Only palette colors and the two main fonts are used
- [ ] Text is at least 13px and passes contrast
- [ ] Status is shown with a word as well as color
- [ ] Works at phone width with no sideways page scroll
- [ ] Placeholder data is labeled as sample data
