# Fabric Fast Track — Delivery Log

| Date       | Event                       | Format | Slides                                                |
|------------|-----------------------------|--------|-------------------------------------------------------|
| 2026-05-23 | Raleigh Day of Data 2026    | 60 min | [PDF](deliveries/raleigh-dod-2026/slides.pdf)         |

## How to add a delivery

1. Export the .pptx to PDF, conference-neutral (footer = `Jonathan Stewart · sqlbites.net`, no event name).
2. Save as `deliveries/<event-slug>/slides.pdf`.
3. Add a row to the table above.
4. Add a row to the `<table class="deliveries">` in `index.html`.

## Note on the slides

All published PDFs (canonical and per-delivery) are conference-neutral. The conference is
recorded in the table above, not baked into the footer. This deck is the v18 source re-export:
the title eyebrow, per-slide footer, and the newspaper-agenda image were all regenerated with
the `Raleigh Day of Data 2026` branding removed (the newspaper masthead/footer is rendered from
`deck.json` via the remotion-forge `newspaper-intro` template, edition set neutral).
