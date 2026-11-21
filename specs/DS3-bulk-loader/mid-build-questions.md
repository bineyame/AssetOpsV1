# DS3 mid-build questions

Questions raised during the build about something the spec did not fix (spec rev 2). Count: 3 (open; Q1 and Q2 each hold one test, Q3 stops nothing).

## Q1 (open): the v4 slice's fourth shape is refused by the real path

- **Spec.** §3 "v4 slice (D-DS3.11)": one batch `V = kit.seal([v4.event(100001, "START_RESULT", "evt-1", "FAILED"),
  v4.start(100002, "start-1"), v4.point(100003), v4.delta(100004)])`; "The real path must accept all four ordinals
  (asserted; if not, a mid-build question, not a change of shapes)".
- **Found.** On the parity seed (with `patched_v4` active), central ingestion returns
  `ReceiptCounts(total=4, accepted=3, rejected=1)`: ordinal 3 (`v4.delta`) is `MAPPING_INCOMPATIBLE`, "this channel
  does not carry MEASUREMENT INTERVAL_DELTA". `Builder.delta` sends on `charger-controller/session-event`, which
  `V4_CHANNEL_MAPPINGS` (the closed cold table) maps as an EVENT channel (`ledger.py:437-440`). In
  `test_w200_source_events_postgres.py` `v4.delta` appears only in refusal cases (`:203-205`); an accepted
  `INTERVAL_DELTA` needs an EV connector channel (`<prefix>-connector-meter/energy`,
  `source_envelope_v4.py:683`), which `patched_v4` does not bind.
- **What is built.** `test_ds3_parity_postgres.py` holds the v4 slice exactly as specified in its own test,
  `..._with_the_v4_slice`, marked `xfail(strict=True)` naming this question; the two-Kobo-days parity test passes
  on its own. Plant P15 (the `event_id`/`correlation_id` swap) depends on the v4 slice and is held with it.
- **Options for the Architect.** (a) drop `v4.delta` from the slice (three v4 shapes, three ordinals; the event
  columns are still compared; `connector_id` and `session_id` come from `v4.start`); (b) add a `patched_v4`
  override binding an EV connector-meter energy channel so a delta is accepted; (c) another shape of your choice.
  The builder's default if asked to choose: (a), the smallest change, with no new fixture.

## Q2 (open): the census meets a third per-statement table, `event_outbox`

- **Spec.** §3 "Census" and D-DS3.10: every table's delta is equal on both paths except `recompute_job` and
  `chain_input_change`; "a table with a non-zero delta that the test does not name fails with its name". Reverse:
  "Name a further table in the census's per-table rules when a trigger with per-statement rows is added" (the
  Architect's call, not the builder's).
- **Found.** Two Kobo days: `event_outbox` delta real 1062, bulk 110 (by source and type: `accepted_evidence`/`reading.accepted` 960 real, 10 bulk;
  `recompute_job`/`job.changed` 102 and 100; `foundation_revision`/`foundation.revised` 2 and 2). Migration `0044`
  writes it from statement-level `AFTER INSERT ... REFERENCING NEW TABLE` triggers: "one row per (Site, statement,
  event type)" (`0044_chain_events.py:2-3`). The real path inserts `accepted_evidence` one row per statement (a
  savepoint per ordinal), the bulk path one statement per batch, so the row counts differ by design, exactly as
  for `chain_input_change`. Every other census table is equal or within its rule; equal rows and the recompute-job
  rules pass.
- **What is built.** The census rule for unnamed tables is its own test, `test_the_census_names_every_table_the_load_writes`,
  marked `xfail(strict=True)` naming this question; the parity test asserts everything else.
- **Options.** (a) give `event_outbox` `chain_input_change`'s rule: the set of distinct `(tenant_id, site_id,
  source, type)` among new rows equal, bulk count at most real (the readers consume events per Site and type);
  (b) compare its aggregated subjects (roles, asset ids, span) per Site and type; (c) other. Builder's default if
  asked: (a).

## Q3 (open, nothing stopped): the walkthrough database's name passes `permitted_database`

- **Spec.** §2.4 `permitted_database`: a name ending `_test` (or `<prefix>_audit*`), not an operator's, on
  `127.0.0.1`/`localhost` and the container port; D-DS3.12: "the world command never loads the served
  walkthrough database". Test 1 lists `assetops_polish_walk1113` as false.
- **Found.** The walkthrough database is named `assetops_polish_walk1113_test` (`.ai/NOW.md` §3), which ends `_test`
  and so is permitted by the rule as specified, on the same container. Nothing in DS3 refuses it by name.
- **Built as specified**; no part is stopped. Options: (a) refuse names matching the walkthrough pattern
  (`*_walk*`) explicitly, with a test-1 case; (b) leave it to RULES §7 and DS4's held question (D-DS3.12).
