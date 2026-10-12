# V-01a questions, batch 1 (Implementer, 2026-10-12)

Each question has a fail-closed default that is already built. Nothing here blocks review.

**Q1. SLD drawing arrangement (`sld:1`).** v6.9 draws a bus-bar single line diagram (sources left, a vertical 400/230 V bus, feeders with breakers and meters right, a monitoring row). The app draws the S1-02 archetype grid (component boxes joined by AC/DC/fuel lines, the AC bus as a box). Same parts and connections, different drawing. Redrawing is an intrinsic-width SVG geometry change across `SiteSingleLineDiagram.tsx` and its layout guards.
Default: keep the current drawing and record it as an accepted visual difference. A bus-bar redraw would be its own task if the owner wants it.

**Q2. Page heading.** v6.9 puts the Site name as the h1 ("Kobo Mini-grid") with the view as subtitle. The app uses the view as h1 ("Foundation") with the Site name and code beneath, the same pattern as the S2-S4 screens already compared.
Default: keep the app-wide pattern (accepted difference).

**Q3. Readiness colours.** v6.9 colours configuration tiles green/amber ("Complete", "Needs review"). The app keeps configuration badges and tiles neutral, because the Badge vocabulary deliberately has no health tone and PRE-S3-04 requires configuration readiness not to read as operational status.
Default: neutral (accepted difference).

**Q4. "Bound component stays stable".** The app has no selected-component state (no clickable SLD part). I read the criterion as: each part's bound channels for the selected period stay identical across reload and view switches, and change only when the period changes. That is now measured. Adding a selected-part URL parameter would be a new interaction.
Default: no new selection state.

**Q5. Topology card icons.** v6.9 shows a glyph on each topology card. The app cards are text only. The SLD glyphs are internal to the SVG drawing.
Default: text only (accepted difference). This is cosmetic and cheap to add later if wanted.
