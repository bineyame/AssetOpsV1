# W2-05a items awaiting Architect ruling before merge (batched; coordinator 2026-10-18)

From the ev-sld compaction run (branch task/W2-05a-ev-foundation; parts panel now 1.29x mock):
1. Spec label "Configured mapping" fails the vocabulary scan (`mapping` only allowed in the four ruled exact phrases). Implementer used "Configured source roles:". Rule: keep that, or add a fifth exact allowlist phrase for "Configured mapping".
2. "Schedule state" word set chosen by implementer: `disabled` | `no service hours` | `service hours set` | `mixed schedules` | `no schedule declared`. Confirm or give exact wording.
3. Reporting cell text "{n} configured source role(s)". Confirm or give exact wording.
Batch with W2-05a's next Architect call (commit 5 / pre-review).
