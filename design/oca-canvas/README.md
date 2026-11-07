# OCA design canvas

Design source for the OCA affordable-housing site screener, exported from the Claude design canvas.

- `canvas.json`: canvas index (artboard positions, titles, notes)
- `Oca-Brand.dc.html`: logo, color and type
- `Main.dc.html`: Direction A, friendly search results (interactive)
- `Direction-B.dc.html`: Direction B, data-tool view (interactive)
- `Parcel-Report.dc.html`: full score report for one parcel
- `How-to-use.dc.html`: how-to-use page
- `Video-Storyboard.dc.html`: 30-second demo video storyboard

All parcels, APNs and scores are illustrative sample data. The `.dc.html` files expect the canvas runtime (`support.js`) and are meant to be opened in the canvas.

Palette: Blue `#2B5FC7`, Green `#12844A`, Yellow `#E8A800`, Orange `#C2490F`, Ink `#1B1F2A`. Fonts: Archivo (headings), IBM Plex Sans (body), JetBrains Mono (IDs).

The mockups still show an earlier score model (development potential, location quality, feasibility risk, weighted 45/35/20). The working app and `../DESIGN.md` §9 follow the backend instead: Opportunity = development potential × (1 − 0.7 × risk ÷ 100).
