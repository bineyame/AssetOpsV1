# DD3b review (discovery, round 1)

Reviewer: Claude (fresh, not the author), 2026-11-23. Branch `task/DD3b-mini-plant`, head `a5660833d` (main `601bdb489`
merged; main's later commits `3c24871dd`/`43e161bf7` are rulings and spec text only, D-DD.163). Diff `git diff main...HEAD`.

## Summary (round 1)

- **Verdict: accept with findings fixed on the branch** (H1 needs an Architect ruling first; see Questions).
- H1: `M`'s October fuel leaves are not the current world's. On HEAD the tool gives Kisiwa 903 L (M 904), candidate 70 L
  (67), variance 1,761.10 (1,759.80), and dips 1,680/1,577 (1,663/1,559); Kobo's dips 1,256/1,022 (1,253/1,019).
  `fuel-leaves.json` and Kisiwa's `fuel-notes.json` entry are stale (`--leaves --check` exits 1 for Kobo and Kisiwa;
  `--restate-notes --check` exits 1 for Kisiwa: the rule now places 1 Aug / 21 Aug / 16 Sep / 16 Oct, one day after the
  file's 31 Jul / 20 Aug / 15 Sep / 15 Oct). Cause: the whole `period` is a history
  scope-digest input, so the `M` commit re-seeded July-September and moved the world under it (a loop with no fixed point).
- M1: Kisiwa's candidate share moved from the ruled 0.36 / 11.27 / 0 / 10.17 % to 18.80 / 17.77 / 0 / 10.67 % (same cause),
  with no note in the packet. The owner accepted D-DD.151 on "about a tenth in August and October".
- L1: the D-DD.155 test is not as ruled (no `SIZED_ON` rule assertion, not renamed, an orphan comment).
- L2: `domain-and-decision-models.md:22` still says "95% evening load" (D-DD.147/151: about 70 %).
- Recomputed by hand: Kisiwa October diesel from the readings is 882.82 L burned + 20 L = **903 L** (M 904). Kisiwa's
  bridge on `M` closes: -55.00 - 87.10 + 1,927.90 - 26.00 = 1,759.80 (= 1,694.80 - (-65.00)).
- Held: Kobo 634 L and Mto 32 L (tool on HEAD equals `M`); bridges close on `M` at all three; v1-v8 untouched (0 lines
  removed in `mini_grid.py`, kernel not in the diff); guards pass.
- Known and accepted as listed: six H5 lines (D-DD.156, DD3d); 7 DDR rehearsal tests and ds4 t12 (D-DD.163, DD3d.4).

## Findings

### H1 (High, acceptance gap: D-DD.131, D-DD.93): `M`'s October fuel leaves and `fuel_balance` are not the tool's output on the current world

- Where: `config/world/fuel-notes.json` (Kisiwa entry); `Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml:193,202,204` (Kisiwa leaves,
  `fuel_balance`, GENERATOR_SUPPORT_CANDIDATE), `:123` (Kobo `fuel_balance`), `:4` (rev note);
  `config/world/fuel-leaves.json` (Kobo and Kisiwa ledgers); `simulator/tests/world/test_dd3b3_notes.py:274`.
- What: `tools/dd3_pure_run.py --leaves --check` on HEAD (log `/opt/assetecon/evidence/DD3b/review/leaves-notes-check.log`):

  | Leaf | Kobo `M` -> run | Kisiwa `M` -> run | Mto |
  |---|---|---|---|
  | `diesel_l` | 634 -> 634 | **904 -> 903** | 32 = 32 |
  | `necessary_l` / `candidate_l` | 489 / 25 = | **817 / 67 -> 813 / 70** | = |
  | `diesel_cost` / `contribution` / variance | = | **1,175.20 / 1,694.80 / 1,759.80 -> 1,173.90 / 1,696.10 / 1,761.10** | = |
  | `opening_dip_l` / `closing_dip_l` | **1,253 / 1,019 -> 1,256 / 1,022** | **1,663 / 1,559 -> 1,680 / 1,577** | = |
  | `model_implied_l` | 514 = | **884 -> 883** | = |
  | CANDIDATE_RUNNING / necessary line | = | **-87.10 / 1,927.90 -> -91.00 / 1,933.10** | = |
  | `fuel-leaves.json` | DIFFERS | DIFFERS | matches |
  | `fuel-notes.json` (`--restate-notes --check`) | matches | **DIFFERS** (each note one day later; July's purchase moves to 1 Aug) | matches |

  The Kisiwa leaves above come from the file's (stale) notes; on the rule's notes they may move again. The July note's
  move also changes Kisiwa's July and August expense books (`EMU_FUEL`, the 3a3 expenses pins).

  My own recompute from the merge DIR's readings (`merge-main/pure`, Kisiwa October, per unit on its `/2` curve:
  4.8 L/h no-load, SFC 0.31, 60 kW; 4,135 unit-minutes on, 2,400.09 kWh) gives 882.82 L burned, so `diesel_l` 903, and
  an opening tank reading of 1,680.2 L. The builder's own `dd_check --pure` line shows Kobo's 1,256.0 / 1,021.8 beside
  `M`'s 1,253 / 1,019, so the movement was in the evidence but not compared.
- Why: D-DD.131 rules that `M`'s leaves are the tool's printed values and that a test asserts `M` equals the tool's output.
  The test compares `M` with a recorded ledger (`fuel-leaves.json`), and that record was written before the D-DD.30
  regeneration. The regeneration re-seeded every Lakeside July-September leaf, because `scope_input`
  (`simulator/assetops_simulator/world/scope.py:71`) puts the whole `site_doc["period"]` (the October fuel leaves,
  `fuel_balance`, bridge) into the scope digest that seeds the history draws. So `delivered_kwh` moved (Kisiwa July
  7,697 -> 7,626; Kobo July 8,755 -> 8,621), the load moved, and October's entering state and candidate moved. The figures
  the product will serve from the readings (dips, litres split) now differ from `M`. Writing the new values into `M` would
  re-seed July-September again: as built the chain has no fixed point, so a re-run alone cannot close this.
- Fix: after the Architect rules on the loop (Q1), break it (for example, keep October's fuel leaves out of the history
  scope digest, or freeze the July-September draws), then run `--restate-notes` and `--leaves --write` once on the
  stable history, write `M` from the tool, regenerate the D-DD.30 chain, and confirm `--leaves --check` and
  `--restate-notes --check` exit 0 for all three Sites. Add a guard that fails when the record no longer equals the run,
  for example the `--check` runs in the slice's evidence or a slow-marked test, so the next regeneration cannot leave the
  record stale without anyone noticing.

### M1 (Medium, owner-facing figure moved without a note): Kisiwa's candidate share is not the share the owner accepted

- Where: `specs/DD-demo-data/packet-DD3b.md:340` (run 2: "18.80 / 17.77 / 0.00 / 10.67 %"), against `:275-276` and
  D-DD.151 (`rulings.md:2718-2726`: 0.36 / 11.27 / 0 / 10.17 %; "about a tenth of its generator time in August and
  October"); `owner/owner-demo-data-answers-2026-11-22.md:48` (the owner's "Accept" was on "~a tenth in Aug/Oct").
- What: the merge DIR prints July 1,065 of 5,665 min (18.80 %) and August 990 of 5,570 (17.77 %), up from 20 of 5,555 and
  625 of 5,545. The candidate steps are 10:00-10:40 cycle-charge tails with PV 21.6 kW against load 18.4-19.0 kW, just
  over the 1.1 x rule. The 1 % drop in July-September load from H1's re-seeding tipped many of them over. The packet
  prints the new figures without saying they moved or why.
- Why: D-DD.151 prints the share with no bound, so no check fails. But the owner accepted the story on the old figures,
  and the share is sensitive to a jitter draw that has nothing to do with the plant. That is a story fact moving under a
  hash.
- Fix: once H1 is settled, print the final share in the packet as old -> new with the cause, and tell the owner if it is no
  longer "about a tenth" (Q2).

### L1 (Low, ruling not built as written): D-DD.155's tank test

- Where: `simulator/tests/world/test_dd3_telemetry.py:254-265`.
- What: D-DD.155 asks for the declared-size assertion plus `SIZED_ON = {"KOBO-001": 1180, "KISIWA-001": 2400,
  "MTO-001": 320}`, asserting that D-DD.76's rule on those inputs gives the declared sizes, and for the test to be renamed
  `test_each_lakeside_tank_is_declared_at_its_d_dd_76_size`. The branch keeps only the declared assertion under another
  name, and leaves the `#: D-DD.76's storage sizes ...` comment with no constant under it (`STANDARD_TANKS_L` was deleted).
- Fix: add `STANDARD_TANKS_L` and `SIZED_ON` with the ruling's comment, assert the rule on them, rename the test.

### L2 (Low, W6 sweep miss): "95% evening load" in a touched design doc

- Where: `Docs/demo-sprint/product-direction-layer4/domain-and-decision-models.md:22` ("one genset at 95% evening load").
- What: D-DD.147/151 restate GEN-KS-02's evening load as about 70 % (41.87 kW of 60). `M`'s thread and the standby comment
  were changed; this doc was touched for figures in the same sweep but keeps 95 %. The mock's `loop-decisions.js`,
  `loop-portfolio.js` and `index.html` keep it too. That is deviation 19's alignment pass, accepted as listed there.
- Fix: restate the doc sentence (70 %, from the run) or add it to deviation 19's list for the alignment pass.

## Not findings (verified)

- **Pack v9.** `mini_grid.py` adds lines only after v8 (0 removed). The one-unit fast path hands every phase to v8. The
  per-unit split, the P floor, the fuel cap scaled to the tank and the FAILED inverter clip match D-DD.127/145 and
  deviations 2-4. A unit failing inside a run gives 0 output from the step holding the instant (test at
  `test_mini_grid_v9.py:183`). In the world neither Kisiwa event hits a running set: both units are STOPPED at
  30 Oct 18:40 and 14 Aug 19:20 (readings checked), and GEN-KS-01 is STOPPED from 17 Aug 11:00.
- **Writer.** Per-unit needs, lead-only policy, `pv-array-share` v9 only, `UNIT_EVENTS` as one-minute WINDOWs, the warm-up
  SOC, Kobo-only season v2 sun, and the required book keys match D-DD.97/104/126/129/145/146.
- **Books (D-DD.130).** At a notes Site the FUEL rows are the file's notes x price. `EMU_FUEL` checks the sum. A Site not
  in the file keeps the cycle.
- **Bridges on `M`.** Kobo 38.00 - 31.25 + 263.75 - 150.00 = 120.50; Kisiwa as above; Mto -8 - 56 - 16 - 40 + 375 + 0 =
  255.00. Each necessary line is -(necessary - plan `diesel_l`) x price.
- **Known failures.** The six H5 lines (D-DD.156, DD3d) and the 7 DDR rehearsal tests plus ds4 t12 (D-DD.163, DD3d.4) are
  listed as known. The builder's same-revision runs are cited, not rerun.
- **Deviation 16** (`fuel-leaves.json` unruled): a reasonable record, but see H1. It is only a record if something
  rechecks it against the run.

## Checks run

- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- `ASSETOPS_GUARD_PYTHON=<main venv> pwsh -NoProfile -File tools/check-architecture.ps1`: exit 0, "Architecture check
  passed." (`review/arch.log`)
- `tools/heavy-slot.sh -- bash review/checks.sh`: `dd3_pure_run.py --leaves --check` and `--restate-notes --check` for
  Kobo, Mto, Kisiwa (`review/leaves-notes-check.log`). Leaves: Kobo exit 1, Mto exit 0, Kisiwa exit 1. Notes: Kobo exit 0, Mto exit 0, Kisiwa exit 1 (DIFFERS).
- Hand recomputes: Kisiwa October diesel from the merge DIR's readings, and Kisiwa's bridge from `M` (above).
- Not rerun (cited from the builder at `a5660833d`): `world_history.py check` 0; `dd_check --pure` 0; check_manifest
  7,875 passed / 12 failed (main's 6 + six H5, `merge-main/check_manifest-3.log`, read); simulator 441 passed with 7
  main-identical failures; reach set at `b9afc1a04`. No Postgres run was needed.

## Could not verify

- That a regenerated chain after H1's fix converges. That depends on the ruling, not on a run.
- check_manifest after H1's fix: `M` and the derived values will move again.

## Residual risk the packet does not name

- The history scope digest covers all of `period`, so any later `M` edit to a mini-grid October leaf (DD3d's H5
  wording in `M` line 198 is a basis string inside `period.bridge`) re-seeds that Site's July-September history and moves
  the pure-run world again. Kobo's 634 L held this time by luck: its October burn is set by the overcast days.
- History July-September fuel leaves are history-generator draws: Mto 27/26/35 L candidate and Kobo 476-478 L necessary in
  months the readings burn 0 L. D-DD.130 keeps them, but the product's History can show fuel in months the world never ran
  a generator.

## Questions for the Architect

- **Q1 (BLOCKER, model).** The history scope digest includes the whole October `period`, so restating October's fuel
  leaves re-seeds July-September (`delivered_kwh`, revenue, fuel draws). That moves the world those leaves came from, and
  `M` can never equal the run. Which loop break is ruled: October fuel leaves (or the whole `period.actual` fuel family,
  `fuel_balance`, bridge and `findings_expected`) taken out of `scope_input`, or July-September frozen at their current
  draws, or another rule? After it, is one notes/leaves/`M` pass with `--check` = 0 at all three Sites the acceptance?
- **Q2 (owner-level).** Kisiwa's candidate share now prints 18.8 / 17.8 / 0 / 10.7 % (July-October), not the
  0.4 / 11.3 / 0 / 10.2 % the owner accepted in D-DD.151. After Q1 the figure moves again. Is the owner told the final
  share, and is "about a tenth" restated from the final run?
