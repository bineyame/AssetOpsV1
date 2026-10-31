# SCN Kobo scenario where the reserve change matters

Status: in_review

Owner-commissioned Lab scenario (end of `.agent/owner-client-demo-sequence-2026-10-30.md`): a registered Kobo run in
which the 30 -> 25 % reserve trial changes generator energy. Branch `task/SCN-kobo-reserve-matters`, worktree
`C:\Users\assef\Bineyame\AssetOpsV1-scn`, from main `ca6d7d61b`. Implementation contract:
`C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-SCN-kobo-reserve.md` (§0 rules, §2 U1, Addendum 1 design
D2 and its five kernel properties, §4 acceptance). Decision `D-2026-10-31-scn-kobo-reserve-matters`.

## Scope (this branch)

- U1: `config/scenarios/kobo-mini-grid-reserve-matters.yaml` v1 (design D2) and its registration in
  `PINNED_SCENARIO_FINGERPRINTS`, `NEW_SINCE_T025G`, `NEVER_SHIPPED_AS_V1`, shipped count 13 -> 14.
- U2: `host/tests/test_scn_reserve_matters.py`, design properties only, never money.
- Not here: U3 (the real-chain probe in `-demo3` after merge) and the DEMO-SPARSE day-list consumption.

## Gates

- The first design (sheet §2) stopped at U2 property 2; D2 ran once and passed. No further design.
- No price, SFC, profile, template, verification or cost-check change; existing digests unchanged.
- USER_REVIEW_REQUIRED: false (Lab content, no UI); fresh independent review gates merge. The owner hears the U3
  result whatever it shows.

Packet: `.agent/SCN-packet.md`.
