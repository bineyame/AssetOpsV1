# 6a reviewer guide

**Rev 1, ready for the handshake** (P6 approved by the owner, 22 Nov 2026). Architect (Claude), 2026-11-21 rev 0,
2026-11-22 rev 1. Discovery review (W5): a new schema, a person rule, and the record that every step-6 money figure
hangs on. Read `spec.md`, the P6 proposal (`specs/6-decision-valued/P6-proposal.md`), its rulings D-P6.1 to D-P6.19
(`specs/6-decision-valued/rulings.md`), 3C2 `spec.md` §2 (the pattern this copies), then the diff. The unit is
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
   gives 14 options and F-P2 gives 15. Test 1 holds the 13 keys as literals and proves the grid equal to 0K4d's
   `KOBO_GRID`. The lever's `changes` are `candidate_l` and `battery_throughput_kwh` (D-P6.3), and `check_levers` runs
   in `check_all()` with ten rules, the shared axis unit among them (D-P6.12).
6. **The heading (OD-25).** `home_category` follows the Finding's pinned factor when a Finding is given, and the
   lever's purpose factor otherwise. `check_levers` refuses a lever whose purpose factor sits under another heading
   from a pin that lists it.
7. **Nothing is valued here.** 6a computes no figure. A grep for arithmetic on `amount` or `value` outside the
   adapter's parameter binding finds nothing. The read serves names and never emails.
8. **One writer.** The persistence guard's new block exists, and its two failing runs are recorded in the packet.
9. **Words.** Every refusal is a variant of the one statement `decision.refused` (D-P6.7, D-3C2.14's pattern), with
   every number or example a slot; the catalogue validator passes. No sentence is written inline in `records.py` or
   in a command.
10. **The read (D-P6.8).** `for_tenant` gives `state` by spec §3.5's order, `decides_role`, `recommended` and the
    period filter; test 7 covers all five states. No route and no served string change (D-P6.9).
11. **Seams.** `git diff main...HEAD --stat` lists only spec §2 to §4's files. `structure/levers.py` and
    `decisions/records.py` import as test 9 states.

## Open for the handshake

- The owner's answers are recorded (spec §10, D-P6.13 to D-P6.19); none is open for 6a.
- Whether Peter is the right one-off declarer for KOBO-001's controller change, or whether the field technician also
  should be (default: no, D-P6.18).
- Each `count` slot's form against `i18n/catalogue.py` (spec §3.4's last line).
