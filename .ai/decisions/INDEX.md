# Decision index

Decisions by ID. The former `.ai/DECISIONS.md` was split verbatim on 2026-11-18;
its four parts concatenate, in this order, to the original (headers aside):

| Part | Holds | Size |
| --- | --- | --- |
| `2026-10-late.md` | 2026-10-07 to 10-23, newest first (it was prepended) | 83 KB |
| `old-index-2026-10.md` | the old in-file "Decision Index For Agent Context" | 17 KB |
| `2026-09.md` | 2026-09-11 to 09-30, oldest first | 182 KB |
| `2026-10-early.md` | 2026-10-01 to 10-09, oldest first | 211 KB |

Find a decision: grep its ID in `index-*.md` (one line each: ID, title, status, file),
then open the file at that ID. Never read a part whole. 45 early decisions
have no ID; find them by date heading (`## 2026-09-11` ...) in the parts.

| Index | Covers | IDs |
| --- | --- | --- |
| `index-2026-09-1.md` | Dated decisions 2026-09 | `D-2026-09-11-simulator-gate` to `D-2026-09-22-reconciliation-panel-retirement` (40) |
| `index-2026-09-2.md` | Dated decisions 2026-09 | `D-2026-09-24-codex-spend-before-the-limit` to `D-2026-09-30-t025e-live-follow` (15) |
| `index-2026-10-1.md` | Dated decisions 2026-10 | `D-2026-10-01-run-binds-scenario-to-site` to `D-2026-10-11-s3-dispatch-interval-assessment` (38) |
| `index-2026-10-2.md` | Dated decisions 2026-10 | `D-2026-10-11-s3-phase-1-fixture-and-late-evidence` to `D-2026-10-16-s602-closure` (40) |
| `index-2026-10-3.md` | Dated decisions 2026-10 | `D-2026-10-16-s602-questions` to `D-2026-10-31-scn-kobo-reserve-matters` (41) |
| `index-rulings-1.md` | Demo-sprint and later rulings | `D-SR.1` to `D-SR.51` (58) |
| `index-rulings-2.md` | Demo-sprint and later rulings | `D-SR.52` to `D-AW-4` (51) |
| `index-rulings-3.md` | Demo-sprint and later rulings | `D-AW-5` to `D-E5.13` (55) |
| `index-rulings-4.md` | Demo-sprint and later rulings | `D-E5.14` to `D-PRICE.4` (54) |
| `index-rulings-5.md` | Demo-sprint and later rulings | `D-R3.7` to `D-W1-8` (55) |
| `index-rulings-6.md` | Demo-sprint and later rulings | `D-W1-9` to `D-WARM.8` (23) |

The `index-rulings-*` lines are index-only: demo-sprint and later rulings
(D-SR, D-E5, D-ANY, D-AW, D-W1, D-MONEY and the rest) whose text stays in
`.agent/` build sheets, Architect files and the coordinator handoff until
declutter step 4. Most live in `.agent/build-sheet-OWN-GAPS-2026-11-08.md`.

New decisions: append to `<YYYY-MM>.md` of the month (create it if absent; the
first is 2026-11.md) with a `Decision: \`D-YYYY-MM-DD-slug\`` line, or record a
family ruling in its rulings file; add one line to the last matching `index-*.md`
in the same commit. `python tools/check-decision-index.py` checks that every cited
ID resolves and every indexed file exists.
