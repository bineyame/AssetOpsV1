# Post-W6 audit: standing brief for every batch agent

Binding spec: `.agent/post-W6-audit-spec.md` (Method, pair definition, index fields, classification). Precedent: the completed `.agent/post-W6-audit/batch-0N/` folders (ledger .md, .json, differences.json, index.html, tools/). Reuse their capture wrappers and ledger builders. Mock authority: `frontend/mockups/v69/index.html` rendered at 1440 and 390 CSS px. The register `.agent/mock-departure-register.md` is READ-ONLY; the Architect assigns IDs.

## Cross-cutting findings already recorded
Cite these by ID, list the pairs that show each one, and do not re-describe them:
- B1-01/B2-01: shell top bar missing
- B1-02/B2-04: tall dark header at 390 on short pages
- B1-07/B2-03: 14px prose vs mock 12px
- B1-04/B2-36: rail "Not available yet"
- B2-02: page-local Window/date controls
- B1-53: raw system vocabulary, UUIDs or codes on screen
- B3-01: duplicate Overview/Analysis tab row
- B2-21/B3-04: UTC instead of site-local time

## Hard rules
- Edit NO product code. Capture wrappers must be capture-only (drive URLs, wait, screenshot, measure DOM). No seeding, fabricated data or bypassed refusals. Data only from reviewed producer/walkthrough modes. Check the W1-F5b/W2 evidence and the slice packets for which producer made each screen.
- DBs (container `assetopsv1-postgres-1` only): you may create and drop (a) `assetops_audit_bNN*_test`, and (b) per `.agent/owner-producer-scratch-db-authorization-2026-10-24.md`, a producer's own prefix plus an `_audit` suffix, created and dropped ONLY by that producer's own modes. Run producers UNMODIFIED; never use a guard- or name-rewriting wrapper. Before you prepare, check `pg_database`. If that producer's `_audit` DB already exists, another batch owns it, so wait or use an alternative. Never touch any other DB.
- Ports: API 18N01-18N09, Vite 518N, CDP 952N, where N is your batch's port digit in your prompt. Stop only PIDs you spawned, by PID. Never kill by name.
- Do not run `vite build`, full vitest or the full backend suite.
- Evidence goes in `.agent/post-W6-audit/batch-NN/`: app and mock screenshots for each ID at 1440 and 390, plus further states (refused, empty, limited, worst case); `batch-NN.json`; `batch-NN.md`; `differences.json`; `index.html`.
- First reconcile your IDs against the routes mounted in `frontend/src/App.tsx`. Note any spec route-table errors.
- For every difference (panel count/order/titles, rows, columns, chips, links, typography, colours, overflow, height ratio; anything over about 1.3x needs a measured reason), record what differs, the evidence paths and a PROPOSED disposition: (a) an existing Rxx with its status verified, (b) a candidate D1/D2/D4/D5/D6, or (c) D3. Check the spec's mandatory UI-pass items: "1 incidents" plural, raw `c1 · EV_CONNECTOR`, the domainActionClient window-error copy, the R88/R112 Window control, prose size and the tall header. Check closure of the D3 rows R22/R23/R24/R37/R38/R60 where they touch your screens. Report crashes and console errors as defects.
- Be token-efficient. On a network or API stop, resume by checking which of your PIDs and DBs are alive.

## Finish
`git add -f .agent/post-W6-audit/batch-NN`, then commit with "Post-W6 audit batch NN: <name> evidence + ledger" and end the message with "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Stop servers and drop DBs. Report concisely: pair count, differences with proposed dispositions (one line each), blockers, commit SHA.
