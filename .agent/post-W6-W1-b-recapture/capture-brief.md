# post-W6 W1-b recapture: brief for the capture agents

Worktree `C:\Users\assef\Bineyame\AssetOpsV1-review7`, branch `task/post-W6-W1-b`. Capture the CURRENT HEAD
(record `git rev-parse --short HEAD`; set `AUDIT_REVISION` to it). Rulings: `.agent/post-W6-W1-rulings.md` cross-card
4-5, W1-b 30-63 (Q37-Q43 especially), `.agent/post-W6-W1-b-preflight-rulings.md`.

## What to capture
`selection.json` (this folder) lists 142 pairs: 118 indexed pairs of the eleven W1-b screens (tag `w1b`) and 24 Q40
representative pairs (tag `q40`). Fields: `batch, screen, case, width, route, producer, frozen_app, frozen_titles,
frozen_heights`. `frozen_app` (`batch-NN/<part>/...png`) names the frozen part folder, so it names the producer mode
and capture targets. You capture only the batches assigned to you in your dispatch.

## How (same method as `.agent/post-W6-W1-a-recapture/capture-brief.md`)
- Read only what you need of each frozen batch: `.agent/post-W6-audit/batch-NN/batch-NN.md` ("Frozen run" and
  producer sections), its capture script, the `targets-*.json` files and launch helpers. Working commands from earlier
  recaptures: `.agent/post-W6-W1-a-recapture/batch-*/run.md` and `.agent/post-W6-shell-recapture/batch-*/run.md`.
  Run the SAME producers, unmodified, in the same modes. Build filtered targets files that hold only selected cases.
- Reuse the capture script unchanged except for the filtered targets file. Start Vite from THIS worktree's `frontend/`.
- Output: `.agent/post-W6-W1-b-recapture/batch-NN/<part>/` screenshots plus the script's `evidence.json`.
- For every pair record panel titles in order, each panel's closed height and document `scrollWidth - clientWidth`.
  If evidence.json lacks them, add a separate post-capture measurement script (never edit product code).
- Capped panels (closed, disclosures closed) and ruled caps:
  - `assumptions` (and anywhere it appears) "Interpretation history": <= 800 at 1440, <= 1400 at 390.
  - `financials` "Trade-offs and exclusions": <= 450 at 390 (record 1440 too).
  - `action-evidence` / `verification` "Evidence requirements": <= 500 at 1440, <= 1050 at 390 (caps ruling 1; was 450/800).
  - `action-history` "Action history": <= 800 at 390 (record 1440 too).
  - Also record (no cap, Q37): Finding page header height on the `finding` representative.
- Also check and record per pair: on `recommendation` and every Action page, no Site tab row; on `finding`,
  `finding-evidence`, `finding-history` exactly one `[data-mock-deviation="R383"]` directly after the Site tab row;
  none on `alternatives`. On Finding and Action pages, the active rail item (Findings / Actions).

## Viewer clicks (Q43: read/viewer actions only; log separately in `viewer-clicks.md`)
- `assumptions`: where the history has more than three versions, click "Previous versions", then "Next versions"
  (and "Back to newest" if offered); log URL before/after, click, resulting rows and the Interpretation history height.
- `action-history`: where "Show all N entries" is offered, click it; log the same, plus the expanded height.
- No other clicks, no mutations.

## Synthetic cap probe (only for worst cases producers cannot make)
Method: `C:/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-W3-closeout-rulings.md` ruling 1. Tooling: copy
`.agent/post-W6-W1-a-fix-probe/tools/` into `.agent/post-W6-W1-b-recapture/probe/tools/` and add variants for your
capped panels. On the real mounted page: unmodified screenshot first, then in that session clone a real row into five
rows, set every intended text field to 160 chars, assert `verified` (all five rows and every intended field changed),
measure at 1440 and 390, label outputs `synthetic`. Intended fields: Action history - the meaning cell of five rows
(plus Q29/Q30 counts line present); Interpretation history - Fuel price, Recorded amount, Status of five rows (closed
"Show this version"); Trade-offs - five exclusion/trade-off items; Evidence requirements - requirement and status cell
of five rows. Record five row heights, panel height, clipped elements, doc overflow, 390 table scroller.
If a cap is exceeded, STOP that panel and report the measurements; do not change product code.

## Hard rules
- No product code or test edits. Data only from reviewed producer modes. Do not commit.
- DBs only in container `assetopsv1-postgres-1`: create/drop `assetops_w1brc_bNN*_test`; a producer's own
  `<prefix>_audit*` only through that producer's own modes. Check `pg_database` first; an existing `_audit` DB belongs to
  another agent (wait or use a `_test` name). Never touch any other DB. Drop every DB you create.
- Ports: only those in your dispatch. Check `netstat -ano | grep LISTEN` before use. Never use 181[0-2]x, 5181-5184,
  9521-9524, 189xx, 5189, 8971-8977. Stop only your PIDs, by PID; confirm none still listen at the end.
- No full vitest, `vite build` or backend suites. Another agent builds in `AssetOpsV1-review8`.
- If the permission system refuses a step, do not work around it; record the exact refusal as a gap.
- Write `batch-NN/run.md` (<= 25 lines): producer commands, DBs, ports, SHA, captured/selected counts, gaps + reason.
- Token-efficient: bounded reads; logs to files, read trimmed.
