# Review Lows carried to a follow-up round (FUEL-1 / DIESEL-1 / CH-5d1), 2026-11-07

Coordinator list so non-blocking review findings are not lost. Each line cites its review file; an Architect decides which go into one small Sonnet round before DS-1 and which go to the backlog.

- MV-1 (`review-MV-1.md`): L1 price lookup has no error guard (`actions/verification.py:400-419`) — a failed price read 500s the verdict page; L2 no test pins "price as known at verdict" / window end; L3 MILL-3b builds expected currency from the page; L4 PRICE_SPANS_WINDOW wording.
- A1 (`review-A1.md`): L2 third gap (bridge/overview label naming fuel-cost-2 untested) — close at A3; L3 basis-only re-declare counts as conflict; L4 `outcome_map.py:164` descriptor, `site_overview/read.py:38-39` style nit.
- CH-5d1 (`review-CH-5d1.md`): L1 COH O1 never checks `value.text` with 2+ priced Sites; L2 the L2m Postgres test never ran (TEMPLATE_STALE until E2).
- K1a (`review-K1a.md`): L1 old-sentence test covers v1/v5/v6 only; L2 probe evidence line reads stale after merge.
- MB-1a (`review-MB-1a.md`): L1 Assure drops "not available" when trial read fails but mill listed; L2 claim vs board can disagree on a counted Finding thread (unreachable in demo); L3 dead " not yet verified" exclusion; L4 no case pins `accepted_at == cutoff`.
- PV-1 (`review-PV-1.md`): L1 value lines sort by stored code text (ACT-000002 above ACT-001 on the card) — display order; L2 whitespace slip `mini.py:554`; L3 PV-A assumes ACT-001 VERIFIED and does not flag `sums_checked == 0`; L4 trial line reads verification state as of now, not the board cutoff (pre-existing, `chain/read.py:405-417`).
- MB-1b (`review-MB-1b.md`): open Architect call — pin the S-8 mill thread-line kind to MONITORING in MILL-4 (beyond the card); residual: MILL-4 bounds k but does not prove its exact value on real rows.
- K3 (`review-K3.md`): L1 no test pins STARTING/FAILED as a stop marker (`verification_rules.py:375`) — add a FAILED end-sample tfc2 assertion (expect 3300); L2 `fuel_balance/rules.py:9-10` docstring says slot helpers "never edited" (stale after R3h). Note for K4: K3's single-head test hard-codes 0055; 0056 must make it head-agnostic.
- WD-1m (`review-WD-1m.md`): L1 case 7 can't fail on the class (use the published verdict fixture); L2 no test for the "known by cutoff" gate on `source_class`. Watch at E3: real Kobo data must yield an example class or MILL-5 fails.
- K0 (`review-K0.md`): L1 `site_code` mismatch refusal untested (`runs/operational_actions.py:232-233`); L2 action order (`at`, then `action_id`) never exercised. Residual: an action straddling a run start is silently left out (K7 must keep each action inside one run's day); provenance `_answered` uses `next(...)` without default.
- K7 CARRY (owed to the K7-D builder when it resumes; DIESEL-1-R3k2 §9n.3, verbatim there): once K7 merges, a combined dataset without Kisiwa makes KIS rows FAIL, not skip (`tools/demo_combined_finish.py:957-959` and every KIS row with the "not in this dataset" branch), with an L0 fail self-test.
- K7 CHANGE (DIESEL-1-R3m): K7-D step 5 Action body `"domain": "MINI"` becomes `"FUEL_BALANCE"`; S-7 clears once K6a merges.
- K2 (`review-K2.md`): L1 closed by K3's card (R3d).
- F0 (`review-F0.md`): L1/L2 routed to K0/K3 cards (R3c §9c.3).
- K1 (`review-K1.md`): L1 handled by F0e (R3e); L3 Kisiwa template meter names "clinic"/"mill" → K8.
- Main drift: `test_ch1a_grading.py::test_period_bounds_addis_utc_tue_only_and_24h` fails on main (`unknown period 'midday'`), reported by the MB-1b builder; not yet traced.
- Main drift (reported by the K4a builder, same failure on main): 6 tests in `test_w301_estate_golden_postgres` (`$.summary.claims` has an extra `count.opportunities` the golden lacks) and `test_s4_schedule_health_postgres::TestDatabaseTime::test_skewed_application_clocks…` (clock-skew patch ineffective). Not yet traced.
- Main drift: `test_w502_domain_intent_api.py` fails to collect without a DB URL (`NameError: COLD`; DB-gated import at `:23`), pre-existing (DIESEL-1-R3m2).
- Main drift: two TEMPLATE_STALE mechanism tests (and three `test_ch6b_estate_postgres` setup errors) until the E2 template rebuild.
