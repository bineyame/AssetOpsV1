# W2-F review packet — W2 structural corrections

Task: `tasks/W2-F-structural-fixes.md`. Contract: `.agent/W2-F-build-spec.md` (ledger + "Review closure (2026-10-21)"
+ "Copy rulings (q1)"). Branch `task/W2-F-structural-fixes`. Per-unit detail: `.agent/W2-F-phase-handoff.md`.
`USER_REVIEW_REQUIRED: false` (independent review + structural re-audit gate merge and W5 readiness).

Status: **partial for review** — units 1a-4 and 5 built; **M12 (unit 4b) is open** and lands after W4-03 merges.

## Commits

| Unit | Commit | Scope |
| --- | --- | --- |
| 1a | `8028d57d` | H1 backend capability truth (B1, S1-S4, S6) |
| 1b | `f3ccb41c` | H1 UI copy, M4, M6, M7, cold M13 (S1/S2/S5/S7/S8/S12, N0, N6) |
| 2 | `672671d4` | M3, cold M5/M10 (N1, N7, N9) |
| 3 | `d0f8abd9` | M2, M8, M9, M14, EV Overview M10 (B2, S9, N3, N8) |
| 4a | `83971293` | Architect copy ruling q1 |
| 4 | `fbb197db` | EV M5, M10, M11, M13 (S10, S12, N1) |
| 5 | this commit | captures, re-audit, packet (no feature behavior) |
| 4b | not built | M12 EV Scenarios tab + guard + rail fixture (S11, N4) — after W4-03 |

## Acceptance

| Criterion | Status |
| --- | --- |
| H1: excursion fixture -> Limited cooling, None product, explicit missing basis; Overview/Backup/Evidence one rule | Met (backend `test_w2f_recovery_and_exposure_truth_across_selected_reads[excursion,normal]`; captures below) |
| 13 Medium findings close under named tests; every affected state keeps its mock slot | 12/13 met; **M12 open (4b)** |
| Selected IDs, cutoff, provenance, cursor, exact links unchanged; nothing invented | Met per unit tests; no manifest/route/migration change |
| Focused tests, tsc/build, guards, registry checker, one same-revision full backend suite on private `*_test` DB | Focused per unit (handoff); tsc/build/check-all at unit 5 below. **Full backend suite: not run** — it must be on the final revision, which is after 4b |
| 1440/390 app/mock pairs, stocked/no-selection/refused; 14-finding re-audit | Met (below); EV Financials captures re-taken after 4b |

## 14-finding re-audit (rendered captures, `.agent/W2-F-evidence/`)

| Finding | Observed in capture | Result |
| --- | --- | --- |
| H1 | cold-evidence stocked: Cooling recovery `Limited` + ruled q1 limitation; Product exposure `None` + `Product identity, stock value and a reviewed response rule are not declared. · Required basis: ...`. Normal: Overview Cooling `Limited` / `Recovery comparison not assessed`; Backup `Cooling resumed: Not recorded` | Closed |
| M2 | cold/ev readiness: every Unconfirmed row `Commissioning record` | Closed |
| M3 | cold, cold-evidence, cold-financials refused: `Window cannot be read` strip, Overview 5 / Financials 4 `Not assessed` tiles, panel gaps kept; invalid window -> no date line (N7) | Closed |
| M4 | temperature panel 3 `Claim boundary` in stocked/no-selection/refused | Closed |
| M5 | cold financials `2 consequence lines` = 2 bridge rows; EV `3 consequence lines` = 3 rows; `Displayed rows include unpriced context` | Closed |
| M6 | temperature `19–23 °C·min · Observed excursion estimate`; financials `Consequence basis: at least 19 °C·min; upper bound not established` | Closed |
| M7 | cold-assumptions and financials: `Stock value in chamber`, `Product exposure rule`, `Currency`, all `Not declared` | Closed |
| M8 | ev overview `Single line diagram →` + `Opens configuration at window end; evidence cutoff is not carried.` (also on refused) | Closed |
| M9 | ev overview `Needs attention` + `Confidence: Bounded`; refused `Unknown` / `Confidence: Unknown` | Closed (see reading 5.2) |
| M10 | `REC {full UUID}` cold Analysis, EV timeline/Analysis; `F {UUID}`, `SES {external id}` EV Finding | Closed |
| M11 | ev-evidence: Availability `Connector status coverage not assessed`; Cause `Charger diagnostics and vehicle request not recorded` | Closed |
| M12 | ev-financials subtabs still Overview / Assumptions only | **Open — unit 4b after W4-03** |
| M13 | cold finding `Confidence: Observed · ... · Selected source: Generated test data`; EV `Open` / `Confidence: Observed` / separate `Observed interruption`; EV refused `Unknown` / `Confidence: Unknown` | Closed |
| M14 | ev-sld parts row `Charger 2 · Not declared` | Closed |

## Panel inventory (22 screens)

`evidence.json`: 72 pairs (22 screens; 1440x1000 and 390x900), 116 PNGs. Every pair has the mock's panel count and
order. Titles equal on 64/72; the 8 differences are the data-derived titles the audit accepts by design (readiness
`Gateway status · edge-cold-lab-001`/`edge-ev-lab-001` vs mock gateway codes; SLD diagram name `Cold replay lab`/`EV
charging lab` vs mock site names). App horizontal overflow > 0: 0/72 pairs; clipped text cells: 0/72. Viewed:
`cold-refused-390-app.png` (strip + 5 tiles + 5 panel gaps at 390).

Cases: cold-excursion phase — 12 cold screens stocked; cold, temperature, cold-evidence, cold-financials also
no-selection (2026-10-05 window) and refused (from > to). cold-normal phase — cold, coldbackup, cold-evidence,
cold-financials. ev phase — 10 EV screens interrupted; ev and ev-finding refused. Pending/historical and refused-valid
windows are jsdom-only (named unit tests).

Seed/capture: `seed.py` (ordinary W2 replay paths: cold W2-02 -> attest -> upload -> W2-03 worker -> W2-04 drain; EV
W2-05b -> EV worker -> tariff -> money), private DB `w2fe_test` (re-created per phase, dropped after; confirmed
absent). API uvicorn 9781, vite 6181, own headless Chrome on CDP 9782 (only that process killed). `capture.mjs`
at code revision `4d4fa252`.

## Checks (unit 5, code revision `4d4fa252`)

- Frontend full suite: 98 files, 2435 passed (206 s).
- `tsc --noEmit`: exit 0. `npm.cmd run build`: exit 0 (existing chunk-size warning).
- `tools/check-all.ps1`: all 11 guards passed (architecture, navigation truthfulness, agent workflow, dependency
  registry, screen ledger, ...).
- Backend: focused files per unit (handoff); full suite deferred to the final revision after 4b.

## Builder readings (all units; flag if wrong)

1a: (1) CONTRADICTORY = any selected chain result or step CONTRADICTORY; (2) claim limitation carried on LIMITED and
UNAVAILABLE; (3) product CONTRADICTORY keeps the existing excursion predicate; (4) S5 flag built in 1a; (5) cooling
SUPPORTED text removed, not kept unreachable.
1b: (1) vocabulary glosses — superseded by ruling q1 (only `Claim boundary` kept); (2) contradictory cooling with no
limitation -> `Coverage or claim basis incomplete`; (3) currency label from unit-value item, `No assumption in use` only
when all three rows `Not declared`; (4) temperature card value is the bound, note carries the estimate label; (5) cold
Finding refused state unchanged (no strip).
2: (1) M3 on Overview/Evidence/Financials only; (2) `Window cannot be read` for every refusal kind; (3) refused date line
keeps `Selected window`, cutoff omitted when not requested; (4) 390 proof jsdom + capture (now taken); (5) refused footer
`claim limits` — resolved by q1.
3: (1) SLD href built in shell (`routes.sld`); (2) no selected version = currentness `UNKNOWN`; (3) refused Overview
strip has only the two Unknown chips; (4) `Commissioning record` appended to every unconfirmed row incl. optional
manual-log; (5) new copy passes vocabulary guard.
4: (1) `none` placeholder row not counted, withheld/unpriced scenario row counted; (2) EV refused Financials has no
strip/count; (3) `FAULT_ASSOCIATION` always `Charger diagnostics and vehicle request not recorded` (no W2 role carries
them); (4) Sessions list and excluded-records lines keep short IDs (M10 scope).
5: (1) refused captures use an invalid window (from > to), so the N7 suppressed-date variant is what is rendered;
refused-valid is jsdom-only. (2) EV Overview interrupted renders `Confidence: Bounded` because the selected
`status.claim_level` is `OBSERVED` (S9: OBSERVED -> Bounded); the ledger's "interrupted -> Limited" applies only to a
selected BOUNDED level. (3) Full backend suite deferred to the final post-4b revision, per the "same-revision" rule.

## Rulings

- 1b-q1: RESOLVED (copy ruling q1, commit 4a).
- 4-q1: RESOLVED — coordinator confirms M12 lands as unit 4b after W4-03 merges (Architect's merge order).

## Known deviations / residual risk

- M12 open until 4b; EV Financials/Assumptions captures are re-taken after 4b.
- Full backend suite not yet run at a final revision.
- Captures show `Selected evidence through` = seed time (21 Oct), since cold windows carry no `known_at`.

## Reviewer focus

Readings 3.4, 4.1, 4.3, 5.2; the 8 data-derived title differences; H1 normal vs excursion parity.
