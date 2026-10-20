# W4-01 pending rulings (batched, 2026-10-20, after commit 1 `4cb89c68`)

None blocks commit 1. Each needs an answer before commit 2 or 3 is built. No builder default is assumed.

1. **Client `authorization_basis` on a SERVICE command (commit 2/3).** Review closure B6 says "no
   `authorization_basis` accepted from the client"; S28 says the server "derives/overwrites" it; the request wire
   example still carries `actor.authorization_basis`. When a body includes `actor.authorization_basis`: refuse 422
   `WORK_INPUT_INVALID`, or accept, ignore and exclude it from the canonical hash? Which exact value does the server
   store for the development SERVICE principal (for example the `command_access` grant name)?
2. **Shared provenance patch owner (commit 2, Q11).** Has W3-01 commit 1 (`evidence/public_provenance.py`) merged to
   main, or reached a reviewed state the W4 branch should consume? If not, W4 commit 2 carries "that same reviewed
   patch": name the exact reviewed revision/diff to carry so the two lanes do not produce two variants.
3. **Rule-8 per-table anti-vacuity at commit 2.** S25 requires per-table INSERT counts for all 11 tables in commit 2.
   `maintenance_plan` and `operational_record` writers are in commit 2's service, but the routes arrive in commit 3.
   Confirm all 11 table INSERTs (including plan and operational record) land in `postgres_work_store.py` in commit 2.

## Run 2 (q2) - commit 2 stopped before commit (2026-10-20, branch head `f6fd3c4f`)

Questions 1-3 above are answered by "Run 1 rulings (q1)". Run 2 stopped on these; commit 2 is saved uncommitted in
`.agent/W4-01-commit2-partial.patch`. No builder default is assumed for either.

4. **Positive fixture evidence is received after the command's DB time (blocking).** The mandated closure-3 setup
   (`run_case(runner, CASES["F01"])` via `CaseRunner`) ingests through `PostgresEvidenceLedger(...,
   test_decision_clock_override=Clock(decided_at))` (`test_s4_finding_store_postgres.py:117-120`), so F01's accepted
   evidence has `received_at` = authored `decided` instants (2026-10-30/31). Real DB time is 2026-10-20. B7 makes
   `accepted_evidence.received_at <= command DB time` the acceptance cutoff, so the positive incident citing the
   public F01 row's `cited.accepted_evidence_ids` is refused 422 `WORK_LINK_SCOPE_INVALID` (observed on
   `w401b_test`). The same holds for any occurrence-bounds reading tied to those dates. Which is the contract: (a) a
   test-only DB-time override for the work store analogous to the ledger's `test_decision_clock_override` (name and
   seam?), (b) a different positive setup whose evidence is received before real time, (c) cite the pinned Finding/
   Action lineage without posting `cited_accepted_evidence_ids` (Q11 already unions them), or (d) another rule?
5. **Second in-scope Action for the wrong-Action-event vector.** The dry-read requires
   `test_foreign_asset_and_evidence_refuse` to refuse an event "belonging to another in-scope Action". After F01's
   Action is accepted, F02's `GET .../recommendation` returns `proposal: null` (the S6 prior-action trial rule), so
   the closure-3 accept route cannot make a second Action on F02 in this setup. Name the setup that yields a second
   Action (another authored case/asset, the S6 `authored_case` helper, or an SQL fixture row), or confirm the vector
   may use another existing Action-producing path.
