# W6-01a A2 re-review (fix round `fc80b6cf`): ACCEPT

Reviewer: fresh Claude reviewer. Read only; no code changed. Checked M1 and L1 from `.agent/W6-01a-A2-review.md`.

## M1: closed
- **Derivation.** The §2 caps for `Incident cases` are 600 (1440) and 690 (390). The A2 manifest records the non-table
  panel parts as 131 and 171 px. 600-131 = 469 and 690-171 = 519, which are the values in
  `frontend/src/work/globalWork.css`. The `<=760px` media query switches to 519. They are not new design numbers.
- **Guarantee from the CSS.** The only variable-height part of the panel is the `DataTable` scroll container
  (`.global-work .data-table__scroll`). It now has `max-height` plus `overflow:auto`. The rest of the panel is the heading,
  the description, the 390-width scroll hint and the pager, and none of it grows with the number of rows. So for any
  number or height of rows the panel is at most the cap plus those fixed parts, and the table scrolls vertically inside
  it. This is a CSS argument, not a measurement.
- **Sticky header.** `thead th` is `position:sticky; top:0`. Its scrolling ancestor is the `overflow:auto` container, and
  `primitives.css` gives `thead th` an opaque `--surface-sunken` background, so rows do not show through it.
- **Recaptures** (`A2-m1/screenshots/app-*.json`): at 1440 the panel is 489 (cap 600). At 390 it is 629 on positive and
  682 on historical (cap 690). The document width equals the viewport in all four captures.
- Vitest: `globalIncidents.test.tsx` 21 passed.

## L1: closed
`// W6-01a: Incidents rail root is live.` is present in all six files. The counts are 1, 1, 2, 2 (siteDetailRoute),
3 (siteFoundationRoute), 1 and 2 (sharedVisualVocabulary), one per edited literal.

## Findings (all Low, non-blocking)
- **L7 (Low): the A2 manifest does not meet R8.**
  - The spec at §3.1 R8 requires "Each manifest notes `dev server StrictMode issues each read twice; the built app
    issues one`". It also requires manifests to "record one response per page read" and the assertions to use the
    response the page rendered.
  - `.agent/W6-01-evidence/A2/manifest.json` has no StrictMode note. Neither it nor `m1_recapture` records the requests
    made or the rendered response. The earlier `[200, 200]` per-read values are not an explicit claim of "exactly one
    request", so the manifest does not make that false claim.
  - Literal fix: add a top-level `"r8_note"` key with the text "dev server StrictMode issues each read twice; the built
    app issues one". Add, per capture, `"requests": [<each request URL and status, both StrictMode reads>]` and
    `"rendered_response": <the response whose body the page rendered>`. Do not write "one HTTP request".
- **L8 (Low): off-by-one in the derivation.** The recaptures give panel minus table of 132 at 1440 (489-357) and 172 at
  390 (629-457), against the 131 and 171 used in the cap. The worst case is therefore 601 and 691, which is 1 px over
  the stated caps. This may be sub-pixel rounding. A 1 px margin fixes it: use 468 and 518, or re-measure at
  sub-pixel precision. The caps are design limits, so 1 px does not block.
- **L9 (Low, note only): between 761 and 1100 px the scroll hint is visible but the 469 cap applies.** The hint adds
  about 17 px, so the panel can reach about 617 px. The spec defines caps only at 1440 and 390, so this is outside it.

## Missing five-three-line-row producer: not blocking
The CSS reasoning above guarantees the cap for any row count or height, and the spec gives no producer for that
fixture. The `stress` fixture is fixed by A2Q2, and the header and horizontal scrolling paths are both exercised by the
existing captures. The unmeasured over-cap path is already recorded as open in the manifest. A browser measurement
should be added when an Architect ruling allows longer `stress` titles. It is not an A2 gate.

## Not verified
No browser runs and no backend tests (per instruction). Only the focused vitest file above was run.
