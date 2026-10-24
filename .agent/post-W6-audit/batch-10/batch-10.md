# Post-W6 audit batch 10: W3 estate indices

IDs: `findings`, `findings-cost`, `findings-risks`, `findings-opportunities`, `actions`. Branch `audit/batch-10` at main `723770c3` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

## Route reconciliation

| ID | App route (`frontend/src/App.tsx`) | Status |
| --- | --- | --- |
| `findings` | `FINDINGS_PATH` `/findings` -> `EstateFindingsFrame lens="all"` | mounted |
| `findings-cost` | `FINDINGS_COST_PATH` `/findings/cost` -> `lens="cost"` | mounted |
| `findings-risks` | `FINDINGS_RISKS_PATH` `/findings/risks` -> `lens="risks"` | mounted |
| `findings-opportunities` | `FINDINGS_OPPORTUNITIES_PATH` `/findings/opportunities` -> `lens="opportunities"` | mounted |
| `actions` | `ACTIONS_PATH` `/actions` -> `EstateActionsFrame` | mounted |

The spec route table is correct for all five IDs.

## Producer, environment and capture

- **Producer (reviewed, unmodified).** `.agent/W3-01-evidence/serve.py`, the W3-01 commit-4 capture harness. It seeds one `demo` tenant through the ordinary replay paths: COLD-LAB-001 (W2-02 `late-reading`, settled), EV-LAB-001 (W2-05b `interrupted` with the W2-07 tariff and EV consequence worker), KOBO-001 (S4 F01+F02 and the S6 bound Action), and FOREIGN-001 under a second tenant. It then serves the real `create_app()`. Its capture-control POSTs `/__capture/late-kobo` and `/__capture/empty-site` are part of the reviewed harness and produced the pending and partial states. `PYTHONPATH` was `backend;backend/tests;gateway;simulator;contracts;host`.
- **Database.** `w301cap_test`, the name hard-coded in the producer. It falls under the owner's `*_test` authorization (`.agent/owner-test-db-authorization-2026-10-18.md`, which names tool-created capture DBs). I checked `pg_database` first: there was no `w301cap_test` and no batch-8 DB. I created it with `createdb` and dropped it `WITH (FORCE)` after capture. No `_audit` DB was needed.
- **Ports (deviation).** serve.py hard-codes API `127.0.0.1:9741`. Running it unmodified, as the brief requires, means it is outside 18001-18009. I checked first that 9741 was free; batch 8 uses 188xx. Vite ran on 5180 (`--strictPort`, `ASSETOPS_API_PORT=9741`) and Chrome CDP on 9520. All three were started by me and stopped by PID.
- **Environment fix (capture-only).** The first link-check run showed "Site unavailable" for every KOBO-001 link. `/api/sites` returned 503 with `var/sites/kobo-001.yaml has changed since Site KOBO-001 was imported`. The cause was an ignored, untracked `var/sites/` left in this worktree on Oct 23. I moved it aside to `var/sites.b10-aside` for the run, recaptured, and restored it afterwards. The estate pages do not read it.
- **Capture.** `tools/capture-b10.mjs` is batch 9's `capture-b9.mjs` with three changes: CDP port 9520, profile prefix, and extra DOM reads (row text, row links, estate card/chip/notice text). It only navigates, waits, screenshots and measures. `tools/mk_targets.py` writes the target URLs, using the W3-01 `app-*.json` windows. Claims: positive 164/168 (the 4 failures are refused pairs with 0 panels against the mock's 1), historical 60/60, pending 72/72, partial 70/72 (the refused `partial-wide` pair), links 104/120 (the link targets are not their mock screens, so panel-count claims fail by design). Logs are in `logs/`, and API bodies in `logs/api-*.json`.

## Cases and pairs

- **positive:** all 5 IDs (representative), plus `no-window` (bare route) for all 5, `state-merged-empty` (findings), `empty-day` (actions), and `refused-33d` (findings, actions).
- **historical:** all 5 IDs. `known_at` 2026-11-02T11:08:27Z, before the late delivery.
- **pending:** all 5 IDs after `late-kobo` (KOBO PENDING_RECOMPUTE, row withheld), plus `page-two-pending` (cursor from `limit=1`).
- **partial:** all 5 IDs after `empty-site`, plus `partial-wide`, which is the W3-01 33-day URL and is refused.

Total **62 pairs**: 10 representative and 52 further states. A further 20 link-check captures are not counted.

Not producible by this producer: a populated Cost, Risks or Opportunities lens; priority, confidence or lens values; a priced consequence; cold or EV Actions; worst-case 160-character rows; stale-source chips. Populated-lens layout is therefore unverified.

## Structural verdict

Panel count, order and titles match the mock on every non-refused pair: one panel, `Findings across the estate` / `Cost lens` / `Risks lens` / `Opportunities lens` / `Managed actions`. The cards, chips and lens row sit in mock order. Columns match exactly: 7 on Findings, 6 on Actions. No panel exceeds 1.3x the mock. The maximum is 1.02 (findings historical, 1440), and the rest are 0.19-0.96 because the app has fewer rows. The Findings card row is outside the panel and measures 150 px against the mock's roughly 112 px; W3-01 q14-1 waived the cap to 150 (B10-02). There are no console errors and no page horizontal overflow. The refused state shows the lens row, window controls and an alert ("Choose a valid date range of at most 31 days.") with no panel.

## Cross-cutting (cited)

| ID | Pairs |
| --- | --- |
| B1-01/B2-01 top bar + breadcrumb | all 62 |
| B1-04/B2-36 rail "Not available yet" | all 62 |
| B2-02 page-local window controls | all 62 (about 170 px at 390) |
| B1-07/B2-03 14 px sentences | every empty, partial, pending and page-two pair (state sentences, "First page") |
| B1-02/B2-04 tall 390 header | refused 390: 288 px findings, 318 px actions |
| B1-53 system IDs | every pair with rows ("Finding 00000005", UUID disclosure, "Action ACT-000001") |
| B2-21/B3-04 UTC | all 62 (estate UTC basis needs a ruling) |
| B3-01 duplicate tab row | does not recur |
| B3-13 Site lens chips | recurs on the cold and EV Site lists (link check) |
| B7-01/B9-10 | recurs on `/sites/COLD-LAB-001/findings` and `/sites/EV-LAB-001/findings` (link check); no estate row links there |

These carried checks do not occur on these screens: "1 incidents", `c1 · EV_CONNECTOR`, and the domainActionClient copy. D3 rows R22/R23/R24/R37/R38/R60 do not touch them.

## Differences (all dispositions are proposals)

| ID | Screens | What | Proposed disposition |
| --- | --- | --- | --- |
| B10-X1 | all | Cross-cutting rows above | Cite existing IDs. For the Window block, B2-02 or extend R88/R112 (D1). |
| **B10-01** | all | The register has **no row** for any estate screen, although W3-01 ruled many visible departures (Run 13 r2/r3/r5-8, q14-1, r1 L1, W9, B9/S11/S26) | Architect registers each ruled departure (D1/D2) or reclassifies it as D3 |
| B10-02 | 4 lenses, actions | Cards: "Supported findings"; "Not assessed" as headline; long Awaiting-verification note plus disclosure; 150 px card row (q14-1); "Coverage incomplete" headlines; text headline values about 16 px vs the mock's 26 px | D1 "Not assessed"; D2 wording; register q14-1; font is D3 Low or D2 |
| B10-03 | 4 lenses | Chips "All states / Supported / Unconfirmed / No longer supported / Merged" vs "All states / Open / Recommendation" (Run 13 r2); at 390 the chip row scrolls (460/358) and cuts off a chip | D2 vocabulary (register); 390 scroll D3 Low |
| **B10-04** | findings | Only mini-grid titles link. Cold/EV titles are inert (Run 13 r3), yet their `links.finding` destinations render the same Finding. Pending/partial/page-two pages have no Finding link at all. | D1 (register with resolving unit), or D3 Medium if the exact-revision route is proven |
| B10-05 | 4 lenses | Priority/Confidence plain "Not assessed"; State "Supported"; "No consequence recorded" on all rows (UNPRICED with no source revision, including EV despite its W2-07 consequence revision ...03d2); "No supported lens"; Site cell order differs between Findings (code over name) and Actions (name over code) | D1. Architect to check the EV consequence join (D3 Medium if it should join). Site order D2 or D3 Low. |
| B10-06 | cost, risks, opportunities | Every lens is empty in every state (honest reasons); populated-lens layout is unverified | D1 (register); cite B3-13 for the Site chips |
| B10-07 | actions | Title "Action ACT-000001" while the Action page says "ACT-000001 · Battery reserve trial"; "No success criterion recorded"; ruled lifecycle line; notice copy | Title D3 Low (match the Action page) or D1; lifecycle/notice D2 (register); cold/EV exclusion R02/R04 |
| B10-08 | 4 lenses (pending, partial, page two) | Pending KOBO is described as "no selected result" / "not yet assessed" although it has selection ...0584 and only new evidence is pending; the withheld row names no Site | D3 Low |
| B10-09 | findings 390 | KOBO title clamped with an ellipsis (53/35 px); the wide sticky Finding column leaves only Finding and Site visible | D3 Low |
| B10-10 | all, no-window | Bare route defaults to the last 7 browser days, which the pinned producer clock skews; honest partial/empty | Informational; B2-02 |
| B10-11 | link check | Site/Finding/Action links land correctly for all three domains; EV/KOBO Overviews "awaiting evidence migration"; B7-01/B9-10 recur on the cold/EV Site lists; var/sites environment note | Cite B7-01/B9-10; no new estate finding |

## Blockers

None. The port deviation and the environment fix are recorded above.
