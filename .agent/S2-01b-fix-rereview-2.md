# S2-01b fix round 2 re-review (fresh Claude reviewer)

Verdict: ACCEPT. No block findings.

Scope: a98162c..HEAD, against .agent/architect-S2-01b-answers-5.md.

- Q2 guard (service.py ~543-553): UNBATCHABLE/value now only when kind == TOO_LARGE and field == "batch". That is the byte-size failure in ingestion_batch_v2.py:239. The other TOO_LARGE ("envelopes") cannot arise for a singleton. Any other cause is re-raised as _Held(kind, field, detail), preserving the actual kind and field. Held still occurs before sequence/outbox allocation. New test asserts INVALID_FIELD/mapping.snapshot_sha256 is kept, with zero outbox and sequence rows. The existing size/no-sequence test is unchanged.
- Q1 wording: STAGED statement, comments and the TS doc comment now claim only admitted envelopes are sealed, with held reports listed separately. New test pins the text.
- I ran gateway/tests/test_gateway_ledger.py: 43 passed. I did not re-run the other suites.

Findings (carry, non-blocking):
- C1: the non-size path is proven only by a monkeypatched seal_batch_v2. That is acceptable, since no natural non-size singleton failure is known.
- C2: the TS comment line is long (style only).
- Earlier carried items (R1, layout note) are unchanged. Layout evidence was not applicable to this diff.
