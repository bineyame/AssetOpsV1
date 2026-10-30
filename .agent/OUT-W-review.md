# OUT-W final review (estate event windows)

Reviewer: fresh Claude reviewer, independent of the author. Branch `task/OUT-W-estate-event-windows` at head 7d18f6f0,
compared with main 833e7c95. The focus is W3 and the whole slice. W1 and W2 already have per-unit ACCEPTs.

## Verdict: ACCEPT

There are no High or Medium findings. The two Low items below do not block the merge.

## What I verified

- **`read.py` `summary()`**
  - Each cold or EV Site's window choice is wrapped in `_event_window`. Any failure there becomes None, which means the Site falls back to the period, so the window choice can never fail or empty a Site.
  - Mini Sites are untouched (DAY).
  - `window` and `window_basis` are both None only when the board itself fails.
  - The href carries the window only for LATEST_EVENT. It is built from the board's own `window`, so the link opens exactly the window the Site was judged on.
  - `known_at` is added only when the request had one.
- **Module logger (`read.py:34`, `read.py:350-363`)**
  - It logs only the Site code and `type(error).__name__`, never the message or any data.
  - `PortUnavailable` is caught first and is silent.
  - `test_fallback_logs_site_code_and_type_only` proves both: a `secret-dsn://x` message does not appear in the log, and an unconfigured estate logs nothing.
- **`site_selected_windows` (`evidence_money.py:513`)**
  - It uses the same snapshot, scope, cutoff and `selected_windows` call as the Evidence root.
  - It returns [] for mini or no cutoff, and None when the Site is not authorized.
- **c3, real Postgres (code read; not rerun, because I was told not to use Postgres)**
  - Day and week are both asserted, with no branching. Each asserts:
    - LATEST_EVENT, with the window equal to the latest window the spy captured;
    - Cost NEEDS_ATTENTION with lead CC-3;
    - exactly one REPEATED warning;
    - an href that starts `/sites/COLD-LAB-001?from=` and has no `known_at`;
    - no money hits;
    - a windows read under 2 s.
  - The week's latest window must also equal the day's.
- **c4, real Postgres (code read)**
  - 8 Oct is asserted as PERIOD, with the window equal to the day and a plain `/sites/EV-LAB-001/ev` href.
  - 6 Oct is asserted as 409 `ESTATE_SELECTION_INCONSISTENT`. The flip comment names what to assert after FIX-01, and because the test asserts 409 it will fail loudly when FIX-01 lands rather than pass silently.
  - **Spy restore:** `ev.compose` is restored right after the board-on-E read. `seen` is filled only by that read, and the connector and PEAK assertions consume only `seen` and `body`. The summary's boards are therefore excluded from that evidence, not hidden from it. Nothing is lost: before this change, the summary reads would have overwritten `seen`.
- **Frontend**
  - The type adds `window` and `window_basis`. The fixtures give COLD-001 an event href and Depot a plain one.
  - The vitest checks the header and all 4 cells for both Sites.
  - `PortfolioOutcomes.tsx` already links to `overview_href`, and no component changed.
- **Register:** R575 is resolved, R576 is standing, and R577 is open with FIX-01 as its owner. This matches the Architect's ruling (a).
- **Captures** (`.agent/OUT-W-captures/`)
  - The logs read 62/62 and 10/10 claims passed. Product sha 315ef5aa has the same code as the head.
  - I viewed `portfolio-day-1440-app` and `portfolio-day-1440-click-app`. The click lands on Cold replay lab, "Selected window 29 Oct 2026 16:00-17:05 UTC", with Cost "Needs attention · 3 repair visits in 60 days without a result" and the "Risk · Repeated maintenance without a result" issue.
  - The 390 shots exist for every target. I checked only that they exist; I did not view them.
- **Evidence revision:** the backend fast tier ran at 0e0ce581. `git diff 0e0ce581 7d18f6f0` touches only `.agent/` files, so the run covers the code under review.
  - `.agent/OUT-W-backend-fast.log` ends "4362 passed ... (0:58:40)", exit 0.
  - `.agent/OUT-W-vitest-full.log` reads 3526 passed and 3 failed, all in `w1f4VerificationStructure.test.tsx` (the known set).
- **Process:** nothing is tracked under `var/` (`git ls-files var` gives 0). The test DB is `w502b_positive_outw_test`, and the log shows it was dropped.

## Checks I ran (head 7d18f6f0)

| Check | Result |
|---|---|
| `pytest test_out_w1_selected_windows.py test_out_w2_summary_window.py test_out_b4_read.py -q` (plan2 venv, no Postgres) | 29 passed, 2.94 s |
| `npx.cmd tsc --noEmit` | exit 0, clean |
| `npx.cmd vitest run src/estate/__tests__/estatePortfolio.test.tsx` | 34 passed |
| `tools\check-all.ps1` (`ASSETOPS_GUARD_PYTHON` = plan2 venv, no execution-policy flag) | All 11 guards passed |

**Not rerun by me:** the Postgres tests (c3, c4, b4_board), the full fast tier, the full vitest, and the captures. I was told not to run Postgres or a browser. For those I cite the implementer's logs on the same code.

## Findings

- **L1 (Low, packet accuracy):** `.agent/OUT-W-packet.md` (Captures) says "Every app shot has its v70 pair at 1440 and 390". The `portfolio-week-click` captures have no mock pair (`mock_image` is empty in `shots/raw-evidence.json`, and `targets.json` has no `clickMock` on the week target). The week click lands on the same URL as the day click, which does have its cold pair, so nothing is unverified. The fix is to correct the sentence, or add `clickMock: "cold"` on the next capture run.
- **L2 (Low, residual risk already named):** while R577 stands, the whole estate summary refuses 409 on 6 Oct for the w504 build. This is pre-existing and comes from the route's `estate.scope`, not from OUT-W. When FIX-01 lands, the c4 assertion must be flipped as its comment says.

## Residual risk not in the packet

None beyond L2. One extra estate snapshot is read per cold or EV Site, serially. It measured about 0.08 s per Site on w502 and is already named in the packet.
