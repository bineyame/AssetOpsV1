# Demo-sprint review Lows (open; fold into a Sonnet fix round or the backlog)

- TEL-T1 L1: the emulator does not count a write sent during a pause.
- TEL-T1 L2: the client ignores the MBAP protocol identifier in replies.
- TEL-T1 L3: the new guard patterns share blind spots with the existing rules (bare `import_module("host")`, comma-joined imports).
- TEL-04 L1: an unexpected exception after START exits 1 with no EXIT line; an identity refusal exits 1, not 3 (`modbus_poller.py:558`, `:517`).
- TEL-04 L2: a KeyError gives exit 1, not 2 (`modbus_poller.py:531`).
- TEL-04 L3: the inner deliver loop in the proof has no deadline (`proof:182`).
- TEL-04 L4: the CONFIG_FAULT, unavailable-limit and SEAL_REFUSED exits are untested.
- CC-R1 Lows: fixed in CC-R2 commit 1407a4b0.
- TEL-05 L1: `NO_GENERATOR_STATE` is only a substring match (acceptance test line 237).
- TEL-05 L2: no check that no Finding exists (line 240).

## Regressions to investigate (not Lows)
- site-tabs regression: `site-tabs__link` overflows to 421px at 390px on the existing Recommendation/hold pages (found by the CC-R2 capture). It passed in W1-UX-06 (9517eb8e), so it came in on main later. Outside CC-R2's diff. Possibly related to the owner-pending R453 tab wrap.
- TEL-05b Lows (4): see `.agent/TEL-05b-rereview.md`. The main one: the warm-connect failure line omits the error the ruling asks for.
- TEL-06 L1: stale 'open question Q1' docstring at `field/tests/test_field_export_csv.py:3-5`.
- CC-M Lows (3): see `.agent/CC-M-review.md`.

- 2026-10-29 (PERF-01 attribution run): 3 frontend failures in `w1f4VerificationStructure.test.tsx` fail on main under both threads and forks, so they predate PERF-01. There is also one flaky failure under forks in `s404SiteFindingIndex`. Fold both into the next Sonnet fix round.
- Optimize card detail uses the word 'Candidate' (forbidden-vocabulary word, pre-existing text) — fold into the W1-conclusion plain-language pass (OUT-A review L1).
- 2026-10-30: two w301 estate-index Postgres tests fail with NoResultFound when run alone, on main too (order-dependent?). Investigate in the fix round.
- 2026-10-30 HIGH: main (32adae2f) now fails about 24 Postgres tests that passed in slice A's full run at 08:31 the same day. All trace to `test_s4_consequence_store_postgres.py:111` `PowerSite.on(POWER_DAY=2026-10-06)`, which finds no finding revision with that episode_start. Reached from `test_w303_portfolio_fixture_postgres.py:253`. The cause looks like real-clock or time-of-day dependence. It is reproducible identically on main and on OUT-B. Investigation is under way.
- FIX-01 review L2: add latest_window tests for a three-way chained overlap and identical bounds. Also the residual risk that Findings (highest revision) and Portfolio (latest selection) could disagree if an operator re-pins an older assessment.
- OUT-D review Lows: L1 capture ready-check regex /^Loading\b/ catches 'Loading and door records' (shared capture tool); L2 packet mixes Kobo datasets; L3 R580/R586 wording incomplete; L4 test tidy.
- OUT-E review Lows: L1 register the capture gap (no visual of the new lines; inconclusive capture not taken), by extending R595; L2 reword R591 (cost stored, not shown); L3 history() should order by revision_no.
- OUT-E L4 (needs an Architect or owner ruling): an INEFFECTIVE trial can still reach MODELLED_IMPROVEMENT, so the Cost row would show "Did not fix it" next to a modelled money line. That tension with "no change credited to the trial" needs a ruling plus a pinning test.
- DEMO-A0 review L1: tighten the no-production-use guard to catch string-literal kwargs and setattr forms, or text-check every module.

## IDX-GAPS final review Lows (2026-10-31, merged 9fc84ffe9)
- L1 test_idx_gaps_postgres.py:91-147: add P3c, the tolerance-only withholding case on real data (unit tests cover it today).
- L2 SiteFindingIndex.tsx:815: "those days" has no referent when no requested day is a gap but a Finding is withheld; copy change needs the Architect (Addendum 1 Q5).
- L3 OverviewFindingList.tsx:356: PARTIAL read still carries the current-rows data hook (preference).

## Main regression found 2026-10-31 (FIX-S4-DOMAIN full run 20261031-134829-7b9013) - MEDIUM, needs triage
- test_w301_estate_index_postgres.py::test_historical_minigrid_outstanding_marker_page_two_keeps_basis: EstateRefusal INVALID_CURSOR at :897 (page one limit=1 returns no next cursor).
- test_w301_estate_index_postgres.py::test_cold_revision_waits_for_its_selected_assessment: KeyError at :952 (passes in full run, fails alone).
- Both reproduce on main ee678cbe5 with the old store, so they predate FIX-S4. Suspect clock or order dependence (compare the 2026-10-30 clock fixture breakage). FIX-S4 Lows: L1 finding_service.py:67 pass analytic_id=analytic; L2 pure test only checks text; L3 fence spans all domains (extra re-plans only).
