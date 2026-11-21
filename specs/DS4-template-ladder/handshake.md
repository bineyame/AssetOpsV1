# DS4 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

Pre-flight points the Implementer confirms against `main` (answer each in I-questions only if it does not hold):
the billing reader accepts a one-row file at `Revision` 2 as a late revision (spec §4 B3); `observe_structure run`
exits 0 on the built October snapshot; the DS3 parity v4 batch's envelopes fall on contiguous Site-local days; the
`scheduling.run tick` perf line carries per-stage `elapsed_ms` for the enrolled Site; `pseudonym_key erase` and
`key_state` behave as spec T13 states.

## Reviewer questions

(none yet)

## Implementer questions

(none yet)
