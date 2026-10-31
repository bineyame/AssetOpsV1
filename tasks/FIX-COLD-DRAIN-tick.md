# FIX-COLD-DRAIN The scheduled tick drives the cold and EV producers

Status: in_review

USER_REVIEW_REQUIRED: false

Product fix (no UI, no migration). Branch `task/FIX-COLD-DRAIN-tick`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-drain`,
from main `ce5df006c`. Merges before DEMO-A, independently of LINK-LINEAGE and COV-PARTIAL (no shared files).

Spec: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-FIX-COLD-DRAIN.md` units U1-U4 (Architect ruling
(a), DEMO-A CO-6). Coordinator corrections: register IDs R623 (D3, resolved) and R624 (D5, open); Q1 ruled (b):
a failed cold/EV consequence item keeps the drain stage `OK` and retries under its own `retry_due_at`, with no
Site back-off; P4 "byte-identical" read as the packet states.

Packet: [.agent/FIX-COLD-DRAIN-packet.md](../.agent/FIX-COLD-DRAIN-packet.md).

## Acceptance

- The tick runs, per Site and under the Site claim re-checked before each child:
  `s3, cold_assess, ev_assess, mini, opportunity, s4, consequence, cold_consequence, ev_consequence`.
- Each child is its own killable process with `PGOPTIONS` timeouts. The first failure is kept and the later
  children still run.
- On a real `*_test` database, one tick assesses and drains cold work. The Portfolio day is no longer pending, and
  a second tick changes nothing (P1). EV is assessed, then drained, in one tick (P2). A failed item retries on its
  own schedule (P3). A mini-only Site is unchanged apart from the four new 0-count stage keys (P4).
- Fake-runner T1-T5: order, limits and lease sum, first-failure retention, lost claim before a new child, summed head
  counts.
