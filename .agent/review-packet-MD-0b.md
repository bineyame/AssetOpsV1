# Review packet: MD-0b, mechanism dataset verification add-on (1 unit, lane 2)

- Branch `task/MD-0b-verification` (worktree `C:\Users\assef\Bineyame\AssetOpsV1-md0b`), cut from main `ff499d54d`. Not merged.
- Authority: `AssetOpsV1-plan2\.agent\build-sheet-MD-0.md` §2.2, §2.5, §2.6 e, §10.2 test 8, §11 (pre-ruled split),
  §14 Q3, §15-§18; `build-sheet-CH-5a.md` §A14 CH5a1-R3 M1; `review-FIX-MAIN-1.md` L1.
- Commits: `66f81c0b2` build, `25f77c008` baseline after minimum runtime, `da85c6738` L0 alignment, `7fc32f7f0` generator
  power at its source time, `746bafec2` story-time expectations, `7fb9161e1` + revert `59407800f` (Known deviation 5),
  `016ecdb08` CH-5a1 GAP-K7 hard. (`git log ff499d54d..HEAD`.)
- USER_REVIEW_REQUIRED: no screen or copy change. **Three Architect items** (A1-A3 below); A1 and A2 are new
  coherence findings that §5 says stop the slice, so the branch should not merge until they are ruled.

## Pre-flight (answered from code; no blocking question, so the build proceeded on the defaults below)

1. **How ACT-K1 reaches VERIFIED on real readings.** Through the Action API with the DEMO-A SYSTEM VERIFY harness
   (`verifying`, as `tools/demo_combined_kobo.py _trial_chain`): freeze plan, bind later selection, request
   evaluation. The evaluator is synchronous (`B/actions/verification.py:750-866`); no monkeypatch, no replaced window
   evidence or source resolution.
   - **Windows**: 60 min on a 5-min UTC boundary, same UTC clock hour, baseline ends before the change's
     `effective_from`, later starts at or after it (`verification.py:150-174`, `verification_rules.py:159-169`).
   - **Evaluator inputs**: 12 slots, each needs interval coverage of `generator_power`, `pcs_discharge_capability`,
     `pv_available_power`, every bound `feeder_demand` asset, critical requested/delivered, plus `generator_state` and
     SOC points at every slot start and the end (`verification_rules.py:371-536`). MD-0 lacked the bound
     `generator-controller/ac-power` (`generator_power`), so every window was incomplete: added as a derived channel.
   - **Source class**: `source_pair` needs the same positive class in both windows with the same authored lineage
     (`verification_rules.py:684-712`); MD-0 already publishes `assetops.mechanism-dataset` v1 before each batch
     (MD0-PF Q1), so both windows resolve `AUTHORED_DEMONSTRATION` (measured).
   - **Timing constraints found** (they made the sheet's §2.2 timing, freeze+bind+evaluate at D13 01:00, infeasible):
     a freeze is refused once the later window has accepted evidence (`verification.py:298-302`); a UTC day's
     dispatch run reads to 06:00Z of the next UTC day, so its run id changes until that data arrives (measured on the
     MD-0 template: `analytic_run_selection` 10-29 run `c5a8…` -> `a0e7…` on the first D12 job), and a baseline pin
     that moves is `BASELINE_SELECTION_CHANGED` -> INCONCLUSIVE (`verification.py:599`); the first 30 min of a run are
     INDETERMINATE (configured 30 min minimum runtime), so a window holding them is `VERIFICATION_BASELINE_UNSUPPORTED`
     (measured, first build attempt).
   - **Chosen timing** (fixture `actions[].verify`, with its source): baseline = overrun day 08:30-09:30 local;
     freeze = 2 days later 00:30 local; later window = that day 08:30-09:30; bind + evaluate 10:00 local.
2. **Close variant fits 14 days: yes.** Measured: RESOLVED_MONITORING D3, CLOSED D10 (7th fully checked day),
   RECURRED D13: exactly §2.5/§2.6 e. The product puts the VERIFIED cause's effective day on the change day (D3), not
   the evaluation day (D4).
3. **Cost (measured).** Main template 1,014 s seed (drain_mini 335 s of it), close template 1,231 s (drain 429 s);
   L2m file 516 s wall; L3m derive 62 s (main) / 236 s (close). Code: about 1 unit as sized.

## Outcome delivered

- `backend/conversions/mechanism-v1.json`: derived `generator_power` (`running_kw if RUNNING at the source time else
  zero`, 15 kW from `w4-mini-depth-cases-v1.json`); ACT-K1 `verify` block; `variants.close` (overruns D2/D13, ACT-K2,
  no gap, no studies, its own thread).
- `backend/tests/mechanism_dataset.py`: `action_hooks` (each day delivered up to each command cut, settled, then the
  command), `verify_freeze` / `verify_evaluate`, `drain_mini` step (product `MiniDepthWorker.run_pending` until a pass
  leaves none due; no special reconcile), `variant_spec`, per-variant templates (`assetops_mechanism_tplc_<fp8>_test`),
  `seed_database(variant="close")`, variant-aware `build_work`.
- `tools/mechanism_dataset.py`: `build --variant close`, `derive --variant states|close`, `status`/`ensure` over both
  templates, `drop --variant close` also drops the derived close DB.
- Tests: `test_md0_mechanism_postgres.py` (VERIFIED, story time, F1 hard, new close test), `test_md0_fixture.py`
  (5 new L0 cases), `test_ch5a1_mechanism_postgres.py` (GAP-K7 NONE hard).

## Acceptance

| Item | Status | Evidence |
|---|---|---|
| 1 ACT-K1 VERIFIED on real readings, authored path, no monkeypatch | Met | outcome `VERIFIED`, reasons `TARGET_AND_GUARDRAILS_PASS`, both windows `AUTHORED_DEMONSTRATION`, baseline 1,800 candidate s, Action events ACCEPTED, APPLIED, RESOLVED; one `verification_outcome` row. Thread: OPEN D4, ACTION_IN_HAND D11, CHANGE_APPLIED D12, RESOLVED_MONITORING D12, RECURRED D14 |
| 2 Close variant RESOLVED -> CLOSED (7 clean days) -> RECURRED | Met | `test_close_variant_…`: OPEN/ACTION_IN_HAND D2, CHANGE_APPLIED D3, RESOLVED_MONITORING D3, CLOSED D10, RECURRED D13; every delivered day COMPLETE; lifecycle `skipped 0` |
| 3 CH5a1-R3 M1 drain, F1 closed | Met | drain 979 jobs DONE (close 1,271). D6-D9 all three measures NO_DATA, none PENDING; D7 before fill `{NO_DATA}`; `readiness_of` D7 = NONE; both xfails (`test_md0…:185`, `:271`) are hard assertions and pass; CH-5a1 GAP-K7 xfail also hard (NONE) |
| 3 FIX-MAIN-1 L1 owner strings | Met | Removed with the xfails (they pass), not renamed |
| 4 D-AW-3 recorded verbatim | Met, record changed | `run_lifecycle`: `skipped 0`, `skipped_causes []`, counts ACTION_IN_HAND 1, CHANGE_APPLIED 1, RESOLVED_MONITORING 1, RECURRED 1; state on D14 RECURRED. See A3 |
| L0 / L1 | Pass | 57 passed (fixture + shape parity) |
| L2m | Pass | 7 passed, 0 xfailed, 0 skipped, 510.8 s pytest (516 s wall), templates `…tpl_457ce2a1_test` / `…tplc_457ce2a1_test` |
| L3m `check --threads` | **Fails, 0 expected / new findings** | main: COH-8 ×2 (A1); close: COH-8 ×1 + COH-6 ×4 (A1, A2). All other COH 0 |
| Scoped existing | Pass | CH-5a1 L2m + L0 + L1 + `tools/checks/test_chain_coherence.py`: 153 passed, 81 s wall |
| Guards | Pass | `tools\check-architecture.ps1`, `tools\check-agent-workflow.ps1` |

Derived outputs changed on MD-0 (old -> new, for the Architect): ACT-K1 CHANGE_APPLIED -> VERIFIED; thread adds
RESOLVED_MONITORING D12 and RECURRED D14; D6-D9 PENDING -> NO_DATA; all DISPATCH_BASELINE Findings unchanged (D14
recurrence stays `LINKED` once the generator mean takes its own source time's status, Known deviation 2). Studies
unchanged (3 opportunities, eligible 0/2/2, compared with the MD-0 legacy template).

## Architect items

- **A1 COH-8 (main week+month, close month): "Action is VERIFIED, but its progress row has
  origin_revision_selected False".** The origin is the accepted D11 (close: D2) Finding revision; that Finding later
  took BASIS_REFRESHED revisions, so the origin pair is no longer in the selected set. `B/estate/portfolio.py:538-558`
  documents that case as supported ("one whose origin revision is no longer selected"), while COH-8
  (`tools/checks/chain_coherence.py:645-662`) requires True for every VERIFIED Action. First exposure: no earlier
  normal-data VERIFIED. Proposed default: the check is stricter than the read contract; owner CH-5a2 (COH rules,
  lane 1, so not edited here) or CH-6 (verdict). Not added to `expected-mechanism.json` (§5 allows gap/R4 entries only).
- **A2 COH-6 ×4 (close only, week+month): board day D12 shows an opportunity, Opportunities lens and Portfolio list
  none.** The close variant has no studies (§2.5) but keeps the D12/D13 spare-solar noon remap from §2.2, so
  mini-depth is ELIGIBLE with no study. Proposed default: a fixture question (drop the spare-solar days from
  `variants.close`), unless the Architect reads it as a product board/lens disagreement (CH-5a2).
- **A3 D-AW-3 exposure.** With ACT-K1 verified before D14, the D14 overrun recurs from RESOLVED_MONITORING (a real
  transition), so main no longer has an occurrence during CHANGE_APPLIED: the skip D-AW-3 tracks is not exercised
  any more. Recorded verbatim as asked; CH-6b R16 needs its own case (proposed default), or an extra occurrence
  between D12 00:00 and the D13 evaluation is added to the fixture.

## Known deviations

1. Sheet §2.2 timing (freeze/bind/evaluate D13 01:00, later window D12) is infeasible under the product rules above;
   the later window is two days after the baseline, and the baseline starts at 08:30 (minimum runtime). Outcome days
   still match §2.6 a/e because the product dates the VERIFIED cause on the change day.
2. New input channel `generator_power` (MD0-S4 R1.2: a channel an analytic reads that MD-0 lacked). The first rule
   (status at the interval start) gave a positive mean after the last ON report and turned D14's recurrence from
   LINKED to `NOT_ESTABLISHED: SEPARATION_STOP_NOT_CONFIRMED: CONTRARY_REPORT`; the rule now uses the status at the
   mean's source time (one reading set per source time). `pv_power` is not reduced by generator output during the
   overrun hour (rule unchanged; only the noon hour reads it).
3. The input templates now include `drain_mini`, so a seed is about 5-7 min longer (main 1,014 s, close 1,231 s);
   `ensure` builds both templates when missing (container runner cost on a fingerprint change: about 40 min).
4. No task file exists for MD-0b (sheet-driven), so no `Status:` change; `.ai/ACTIVE_CONTEXT.md`/`CODE_STATE.md` are
   left to the coordinator (lane 1 is editing board files in parallel).
5. **Budget overrun**: the close build part that ran D10-D14 then `drain_mini` took 744 s (background, past the 600 s
   foreground rule), because the budget estimates from the longest step seen. A fix (drain always in its own part)
   was committed then reverted: `tools/mechanism_dataset.py` is itself a fingerprinted input and the edit staled both
   templates. Proposed for the next slice that rebuilds the template anyway.

## Residual risk

- The later window's UTC-day selections move after the evaluation (the rest of D13 arrives); nothing re-evaluates, so
  the outcome stands, but a read of the verification state could show reassessment pending. Not checked by a test.
- The close template run took 236 s to derive (main 62 s); L2m close adds about 4 min per run.

## Review focus

The verify timing rule in the fixture source text against `verification.py` freeze/`_assess`; that the evaluator is
untouched (no product file in the diff: `git diff ff499d54d --stat -- backend/assetops_backend` is empty); A1-A3.
