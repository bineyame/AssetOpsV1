# CC-R2 Portfolio placement (D5) and the estate producer case

Status: in_review

Lane C (commercial). Branch `task/CC-R2-placement`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-cc2`, branched from
the CC-R1 head `71aa1fea`.

The contract is `.agent/build-spec-commercial-2026-10-27.md` "CC-R2", including its "Implementer questions and
resolutions" and CC-R1-Q1/Q2. It also includes `Docs/demo-sprint/commercial-capability-readiness.html` Appendix C D5,
as amended, and owner Q11 (the MG-C stand-in is kept). The index is `.agent/build-sequence-2026-10-27.md`.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-cc2\backend;C:\Users\assef\Bineyame\AssetOpsV1-cc2\contracts;C:\Users\assef\Bineyame\AssetOpsV1-cc2\simulator;C:\Users\assef\Bineyame\AssetOpsV1-cc2\gateway;C:\Users\assef\Bineyame\AssetOpsV1-cc2\host;C:\Users\assef\Bineyame\AssetOpsV1-cc2"
```

## Gates (from the spec)

- Pure:
  - one case per rule and per reason code;
  - a row with a MIXED source and a PRICED consequence lands in NEEDS_INVESTIGATION;
  - a Verified row with a PRICED consequence lands in MONITOR;
  - the six-part marker passes and the five-part marker fails.
- Producer 1 (s602b case `estate`):
  - F01 is MONITOR / `VERIFIED_WATCH_RETURN`;
  - F03 09:30 is ACT_NOW with `RECURRED` and `NO_ACTION_RECORDED`;
  - F05 is NEEDS_INVESTIGATION with `LIFECYCLE_UNCONFIRMED`;
  - there are no double-count violations and no numeric priority.
- Producer 2 (W3-03 `build_portfolio_fixture`):
  - `lens=risks` returns exactly the cold and EV rows;
  - the cold placement is pinned;
  - the EV row is UNPRICED_RISK;
  - `limit=2` paging returns every row once, in group order;
  - there are no double-count violations.
- Browser: group headings and reason lines in `estatePortfolio.test.tsx`, read through `settledScreen`.
- Stop if any of these happens:
  - placement needs a fact that is not on the row;
  - the selection token would have to include placement;
  - KOBO-001 rows in `estate` resolve to a source of UNKNOWN or MIXED;
  - the F03/F05 steps stop F01 from being VERIFIED.

Open questions: `.agent/CC-R2-questions.md` (Q1-Q4). Packet: `.agent/CC-R2-review-packet.md`.
