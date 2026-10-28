# CC-M Combined schema slice (owner Q14): migrations 0036 and 0037

Status: in_progress

Lane C (commercial). Branch `task/CC-M-combined-schema`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ccm`, from
`main` `9cec4fcb` (CC-R1, CC-R2, TEL-01..05b merged).

The contract is `.agent/build-spec-commercial-2026-10-27.md` "CC-M", with Q-C12 (head literals) and Q-C42 (column
list). The persistence-guard extension for the trial writer (Q-C13) is CC-D2's ("CC-D2 Files, Guard"): CC-M adds the
table only, with no writer.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-ccm\backend;C:\Users\assef\Bineyame\AssetOpsV1-ccm\contracts;C:\Users\assef\Bineyame\AssetOpsV1-ccm\simulator;C:\Users\assef\Bineyame\AssetOpsV1-ccm\gateway;C:\Users\assef\Bineyame\AssetOpsV1-ccm\host;C:\Users\assef\Bineyame\AssetOpsV1-ccm"
```

## Gates (from the spec)

- `alembic upgrade head`, `downgrade 0035_w5_ev_work`, `upgrade head` on a fresh `*_test` database.
- The trigger refuses UPDATE and DELETE.
- The `PRODUCTIVE_USE_CONTRIBUTION` kind insert passes after 0036 and fails before.
- The chain CHECK refuses revision 2 without `supersedes_revision_id`.
- `pg_harness.assert_at_head`.
- Full backend and frontend suites green on an idle machine (tier 4), on the coordinator's go.

## Stop

Any existing migration needs editing.

## Phases

1. Build, focused migration tests, head-literal tests, guards. Done; see `.agent/CC-M-review-packet.md`.
2. One full backend suite plus the frontend suite, on the coordinator's go.
