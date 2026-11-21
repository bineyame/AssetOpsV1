# 0K4d handoff (superseded: commits 2 and 3 built, see `packet.md`)

Commits 2 and 3 are built and the slice is `in_review`; `packet.md` holds the figures and checks. The text below is the handoff after commit 1, kept for its record.

## After commit 1

Implementer (Claude), 2026-11-21, branch `task/0K4d-rerun-restate`, worktree `/opt/assetecon/AssetOpsV1-0k4d`, off
`main` at `d90cb2853`. Spec rev 2; every R and I question answered (rulings table "Handshake answers (rev 2 of 0K4c
and 0K4d)", D-0K4.26 to D-0K4.30). Spec `Status` stays `live` until commit 3 writes the packet.

## Done (commit 1, 0.75 u)

- `backend/assetops_backend/runs/admission.py`: §2.1 as written (`ADMISSION_PARTS`, `JUDGED`, `AdmissionRule`,
  `AdmissionPart`, `DawnInformation`, `Admission`, `admit`). Imports exactly `__future__`, `dataclasses`, `fractions`,
  `runs.replay_study` (`EVIDENCE_CLASS`, `INPUT_CLASSES`, `CaseOutcome`). Built-in exceptions with codes only:
  `ADMISSION_RULE_INVALID`, `ADMISSION_PART_INVALID`, `ADMISSION_LABELS_INVALID`, `ADMISSION_INPUT_INVALID`,
  `ADMISSION_INPUT_CLASS_MISMATCH`, `ADMISSION_DAWN_EMPTY`. The limit words, basis and derivation are not here
  (D-0K4.27): the Kobo tool writes `admission_rule` in commit 2.
- `runs/replay_study.py`: `CaseOutcome` gains the four measures after `clipped_steps` and a class docstring saying the
  dawn fields are information; `StudyFrame.assumptions = ()` (tuple of str, else `TypeError("STUDY_ASSUMPTIONS_INVALID")`);
  `StudyResult.assumptions` copied from the frame on every status; public `admission_measures(p, local_times,
  first_previous)` in `__all__`, called by `_outcome` (`ValueError("ADMISSION_MEASURES_MISALIGNED")` on a length
  mismatch). B12's import set unchanged.
- `backend/tests/test_0k4d_admission.py`: AD1-AD8 (11 tests), including AD7 through `replay_study` with a scripted port
  (baseline reserve 30, case 25, one step at SOC 27).
- `backend/tests/test_0k1_replay_port_seam.py`: allow-list gains the AD test only (it imports
  `assetops_contracts.forward_replay`); `admission.py` never names `forward_replay`, so it is not allowed in (stricter
  than the spec's "if the seam test names them").

Evidence: `/opt/assetecon/evidence/0K4d/commit1/` (plants.txt, statement_catalogue.txt, check-all.txt).
For the packet (commit 3): statement catalogue `OK`, no `HAND_BUILT_NEW`, both baseline files untouched; the R5 regex
pair has no hit in `admission.py` or the `replay_study.py` diff.

## Next: commit 2 (1.0 u), only once 0K4a and 0K4c are on `main`

1. `git merge main` (needs 0K4a: v8, `host/tests/trajectory_digest.py`; 0K4b: `host/tests/kobo_assumed.py`;
   0K4c: season v2 in `host/tests/kobo_season.py`, `season_site_v2`, `inputs_digest`). None exist on `d90cb2853`.
2. Pre-flight, before editing either tool: `main`'s `tools/kobo_replay_study.py --days 8` (no flags) and record each
   case's `avoided_l` exact as V5's literals; then `--time-one` on both tools on v8/v2 (the Mto tool gains it first,
   D-0K2.24's form) and the two caps (spec §0).
3. §2.3 (`host/tests/mto.py:45,61,65`: `mto_site_v2`, `MTO_ASSUMED`, `MTO_ASSUMED_DERIVATION`, `version`/`site`/`season`
   arguments), `ASSUMED_DERIVATION` in `kobo_assumed.py`, D-0K4.27's words verbatim.
4. §2.4 tools: flags at `tools/kobo_replay_study.py:190-194` and `tools/mto_headroom_study.py` `main`; `dawn_class`
   (`kobo_replay_study.py:73`) takes the season's overcast function; `StudyFrame(assumptions=...)` at :139; `admit` per
   case with `admission not available (<status>)` when not CALIBRATED; the identity header of D-0K4.28.
5. `host/tests/test_0k4d_v8_study.py` V0 (only if 0K4c did not build S7's frozen half and S8; check its ancestor
   rule), V1-V6; plants P6, P7, P9, P10. Then the two 61-day runs, one at a time, `--label 0K4d-kobo` / `0K4d-mto`.

## Next: commit 3 (0.5 u)

§2.5 restatement of `domain-and-decision-models.md` §4.2 (anchor by text, D-0K4.29), the numeral list, regression set
of spec §3, `python tools/select-tests.py --base main`, check-all fast once, `check_manifest.py` output recorded,
`packet.md`, spec `Status: in_review`, the built-state entry and its index line.

## Risks

- `AdmissionRule.__post_init__` (limits are ints of at least 1) and `admission_measures`' length check are small
  additions the spec did not name; both raise coded built-ins.
- `admit` reads the dawn from `case.dawn` against `dawn_limit_pct` (default 35), not from `case.dawn_days_below`
  (which uses the frame's limit); equal while the frame keeps 35.
- 6c must import `admit`; the `Admission` record has no served English (D-0K4.19).

## Carried from 0K4c's review (coordinator, 21 Nov)
- V0 also asserts that a passed `overcast` function overrides the season's calendar (0K4c L1, `kobo_season.py:180-181`).
- Hash the v7-base inputs for the `study.json` digest, as S9 does (`inputs_digest(season_inputs(base_run(61), 61, season="v2"))`), not the v8 run's own inputs, or it will not match S9's `465ab6e0...`.
- `dawn_class` needs a season-name to overcast-calendar map; nothing provides one yet.
- The digest covers forcings and initial values only, not the rest of `FrozenWorldInputs`; state it in the packet's residual risk.
