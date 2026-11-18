# S2-01b questions 5 (fix round 1, F1)

The review set the direction for F1; these are the choices it did not name.
Each is implemented with the fail-closed default below and can be changed
without touching sealed bytes.

## Q1. Registered Stage status vocabulary

`STAGED` used to mean "anything is in the ledger". Default: `STAGED` now means
every envelope this run handed the gateway is in a sealed batch. New statuses:
`SEALING_PENDING` (some envelope unbatched, no recorded refusal),
`SEALING_REFUSED` (unbatched and the ledger records why), `HELD` (every report
held, no envelope). All are derived from the ledger, so they survive a restart.
Owner: Architect, if the Lab should use different words.

## Q2. Hold kind for an individually unbatchable report

Default: `UNBATCHABLE` at field `value`, raised before the outbox insert and the
sequence-state write, so no sequence is consumed. The only unbounded field in a
report is the canonical decimal value; everything else is bounded by the
snapshot binding.

## Q3. One stuck group does not stop other groups

Default: a group that cannot be sealed keeps its envelopes unbatched from the
first unsealable one (sequence order is preserved, nothing after it is sealed
out of order), writes one durable `seal_refusal` row per group, and the other
groups seal. The `seal` call then raises `SEAL_REFUSED` after commit, which the
host surfaces as a typed `PublicationRefused`. Sealing that group later deletes
its refusal row. With the byte-fit and the admission hold this path is not
reachable from valid input; it remains as a durable, fail-closed backstop.
