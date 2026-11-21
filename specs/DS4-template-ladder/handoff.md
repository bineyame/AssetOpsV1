# DS4 handoff (units 1 and 2 done, in review; unit 3 not started, held for owner row 40)

Implementer (Claude), 2026-11-21. Branch `task/DS4-template-ladder`, worktree `/opt/assetecon/AssetOpsV1-ds4`.
No live databases, no processes; scratch removed.

## Done

- `11e8abb5b` unit 1 part; `e7113c9f5` merged main `9f591dd5a` (MBQ-1 answers); `5f86021d0` unit 1 rest (T12-T14);
  `9eff83776` unit 2 (check C1-C7, `harness_run`, staleness, cover rule, `site_timezone`, T6/T8/T9/T9b/T15-T17).
- Packet `packet.md` (checks, plants, deviations). Evidence `/opt/assetecon/evidence/DS4/unit2-2026-11-21/`.

## Next (unit 3, after row 40)

- §4 `bench` and the pipeline bench, T10; the real runs in spec §6's order; packet section for unit 3.
- When 5a F1 merges into `main`: merge it here, empty `C4_KNOWN_FINDINGS` (the 12 D-DS4.27 lines), rerun T12
  (expects C4 PASS, `check` exit 0).

## Anchors

`tools/world.py`: `C4_CONTRACT`, `C4_SITE_CLASSES`, `C4_KNOWN_FINDINGS`, `site_class`, `judge_side`, `c4_oracle`,
`harness_run`, `_c1`..`_c7`, `cmd_check`. `evidence/bulk_load.py`: `envelope_span`, `cover_gap`, step 7a in `_one`.
Run DB tests via `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh --db --wait-seconds 5400 -- pwsh -NoProfile -File
tools/run-host-tests.ps1 -- <file>` (the default 1200 s wait timed out once behind other lanes).

## Risks

- C5's real `pwsh` path is injected in T12; it first runs for real in unit 3's `check`.
