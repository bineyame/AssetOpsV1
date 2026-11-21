# 6a reviewer guide

**DRAFT, awaiting owner P6.** Architect (Claude), 2026-11-21, rev 0. Discovery review (W5): a new schema, a person
rule, and the record that every step-6 money figure hangs on. Read `spec.md`, the P6 proposal
(`specs/6-decision-valued/P6-proposal.md`), 3C2 `spec.md` §2 (the pattern this copies), then the diff. The unit is
done when every question in spec §7 is answered yes with evidence, and every plant in spec §6 fails its named test.

## What to check, and how

1. **Gates.** The packet names gate P's owner record, gate A's head and number, and gate S's two greps. The
   migration's `down_revision` is `main`'s head at merge, with one `alembic heads`.
2. **The schema, line by line.** Every check, unique key, foreign key and trigger in spec §2 is in the migration, and
   test 6 asserts each by constraint name. Look hardest at three things:
   - the deferred `decision_has_no_action` trigger;
   - the deferred `option_evaluation_run_complete` trigger;
   - the composite `(tenant_id, …)` foreign keys, so that no row can point across tenants.
3. **Append-only.** Each of the seven tables has both triggers. UPDATE, DELETE and TRUNCATE are each refused in
   test 6. The downgrade refuses when rows exist.
4. **The rules, in order.** Read `prepare`, `state_one_off` and `choose` against spec §3.3 step by step. Check that:
   - the re-run read comes before any write;
   - the role is checked against held grants, so a site manager on another Site is refused;
   - one clock read is made per call (D-3C2.10).
5. **The grid.** Prepare writes no action at position 0, then the grid without today's point, in grid order. F-P1
   gives 14 options and F-P2 gives 15. Test 1 holds the 13 keys as literals, and equals 0K4d's `KOBO_GRID` once 0K4d
   has merged.
6. **The heading (OD-25).** `home_category` follows the Finding's pinned factor when a Finding is given, and the
   lever's purpose factor otherwise. `check_levers` refuses a lever whose purpose factor sits under another heading
   from a pin that lists it.
7. **Nothing is valued here.** 6a computes no figure. A grep for arithmetic on `amount` or `value` outside the
   adapter's parameter binding finds nothing. The read serves names and never emails.
8. **One writer.** The persistence guard's new block exists, and its two failing runs are recorded in the packet.
9. **Words.** Every refusal is an SC-1 statement (D-3C2.14's pattern). No sentence is written inline in
   `records.py` or in a command.
10. **Seams.** `git diff main...HEAD --stat` lists only spec §2 to §4's files. `structure/levers.py` and
    `decisions/records.py` import as test 9 states.

## Open for the handshake

- Whether the answers to spec §10 (P6 #1, #3 and #6) change any rule: the spec moves to rev 1 after the owner's
  sitting.
- Whether Peter is the right one-off declarer for KOBO-001's controller change, or whether the field technician also
  should be (default: no).
