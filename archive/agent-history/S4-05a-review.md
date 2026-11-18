# S4-05a slice review - immutable source binding and exact-revision resolver

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review4`, branch
`review/S4-05a-slice` at `5143b0b9`; diff `fd7afd2c..5143b0b9`. Code revision `a3640cce`; `git diff --stat
a3640cce..5143b0b9` touches only `.agent/`, `.ai/` and `tasks/` docs (verified). Judged against
`tasks/S4-05a-provenance-binding-resolver.md`, `tasks/S4-05-stored-demo-provenance.md`,
`.agent/architect-S4-05-answers.md` (Q1-Q3, rule 8, Follow-up M1), the plan reviews and the phase-1 review.

## Verdict

**Accept.** No High or Medium. Two Lows and one disclosure note; none blocks the merge.

## Findings

### L1 (Low, guard teeth): rule 8 still misses two UPDATE spellings on provenance

- `tools/checks/configuration-persistence.ps1`, the phase-1 L1 split-statement rule (added block after the
  ledger DDL check). The regex needs the table name directly after `UPDATE`/`DELETE FROM`/`TRUNCATE` on the
  same line. I applied these mutations, ran `tools/check-architecture.ps1`, and restored each one:
  - ledger: `"UPDATE "` / `"evidence_publication SET ..."` (keyword split from the table name): **passed**.
  - ledger: `UPDATE public.evidence_publication SET ...` (schema-qualified): **passed**.
  - finding store: the same two forms: **both passed**.
  - Caught: the ledger split `DELETE FROM "` / `"batch_publication_link`, a schema-qualified `DELETE` in the
    finding store, a split `ON CONFLICT` on a publication INSERT, and a keyword-split or quoted-name INSERT
    into `evidence_publication` from the finding store. So forging a publication from another writer is
    still caught.
- Why it matters: the Architect asked rule 8 itself to reject UPDATE on these tables. At run time the 0014
  `BEFORE UPDATE OR DELETE` triggers still refuse these statements, so this is defence in depth, not a path
  to corruption.
- Fix (optional): allow an optional `[a-z_]+\.` schema prefix and quotes in the provenance regex, and flag a
  line that ends in a bare `UPDATE`/`DELETE FROM`/`TRUNCATE` string fragment in a writer module, or join
  adjacent string literals before matching. Add both mutations to the proof set.

### L2 (Low, contract edge for S4-05b): a consequence can be positive while its FindingRevision is UNKNOWN

- `backend/assetops_backend/evidence/source_provenance.py:275-282`. `CONSEQUENCE_POWER_INPUT_CONFLICT` and
  any downgrade apply only when the union is `MIXED`. When the FindingRevision's cited set is **empty**
  (`EMPTY_CITATION_SET`, UNKNOWN) and the consequence's power IDs are all bound to one fixture/version, the
  union is non-empty and resolves positive. Probe: `Reads([bound('p')], [], ['p'])` gives
  `state=AUTHORED_DEMONSTRATION`, `finding_revision_state=UNKNOWN`, `reasons=[]`.
- Every other UNKNOWN cause (missing, foreign or broken IDs) carries into the union, and an all-unbound
  Finding plus bound power gives `MIXED`. So the empty set is the only gap. Whether a consequence can be
  appended over an empty-cited revision in production is unclear (`clone_revision` builds such a head in
  tests).
- Why it matters: the Architect's union rule, read literally, allows this result. But Q3 blocks current
  money when the source state is UNKNOWN. An S4-05b read that gates consequence money on `state` alone would
  show a current amount whose Finding basis is UNKNOWN.
- Fix: either make the union UNKNOWN (`EMPTY_CITATION_SET` naming the Finding part) when the Finding set is
  empty, or record in the S4-05b contract that consequence money gates on both `state` and
  `finding_revision_state`. Add a test either way. If the intended answer is unclear, batch it to the
  Architect. It does not block S4-05a, because no read consumes the resolver yet.

### Note (disclosed deviation, accepted): UNKNOWN precedence drops the MIXED reasons

When a set is UNKNOWN by precedence, `reasons` lists only the UNKNOWN causes. The per-ID `evidence[]` still
carries every binding, so S4-05b can recover the MIXED detail. The Architect requires naming the
problematic IDs and the precedence, and both are met. If S4-05b's owner copy needs "also mixed", it can derive
that from `evidence[]`. This is a preference, not a gap.

## Focus items judged

- **Truth table.** `classify` matches Follow-up M1 and Q2 row by row:
  - An authored set needs one `(fixture_id, fixture_version)` across any number of publications.
  - A registered set needs one run ID. Several run IDs always give `MIXED`
    (`MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS`, N-L2). One run ID with two identity digests gives
    `RUN_IDENTITY_CONFLICT`.
  - Crossed classes and bound-plus-unbound mixes give `MIXED`, with every MIXED reason reported.
  - Empty, all-unbound, missing, foreign-Site or broken input gives `UNKNOWN`. Missing, foreign and broken take
    precedence over `MIXED`.
  - Each reason carries its exact sorted IDs, and `problematic_accepted_evidence_ids` is their union.
  - Broken links are detected at every hop: batch, evidence-batch scope, link-vs-batch commitment,
    publication present, publication-vs-link commitment, and class coherence. A broken link is never quietly
    treated as unbound or bound. `batch_publication_link.batch_id` is the primary key, so the unscoped
    LEFT JOIN cannot fan out.
- **Consequence.** The union of the selected FindingRevision's cited set (read through the consequence
  revision's own `finding_revision_id`, not the head) and that revision's own power-interval IDs. Both parts
  and `finding_revision_state` are reported separately. The real-pipeline test proves the
  consequence-only conflict with P01 cited and P02 power. See L2 for the empty edge.
- **Historical revisions.** `finding_revision_evidence` reads by the exact revision ID. The PG test shows the
  old revision keeps `AUTHORED_DEMONSTRATION` and its publication IDs after a new UNKNOWN head. An absent
  revision returns `None`, never the head.
- **Cross-tenant disclosure.** `accepted_evidence` is joined on tenant + Site. `in_tenant_elsewhere` is
  tenant-scoped, so another tenant's ID is `EVIDENCE_NOT_FOUND`, which is tested. A foreign-Site ID reveals
  no publication, which is also tested. The revision reads check tenant + Site first, and another tenant or
  Site gets `None`. The link and publication joins are unscoped only past the scoped accepted row, and their
  values are compared, not echoed. A broken row exposes at most a link's publication UUID, which the FKs make
  unreachable.
- **M1 fix.** `register_publication` refuses `GATEWAY_NOT_SIMULATED` for every class. The refusal runs under
  `_lock_slot`, after the gateway/source re-read and before any INSERT.
  `test_a_live_gateway_cannot_carry_any_publication` covers a LIVE simulation record and a LIVE authored
  record, and asserts that no publication row was written. `gateway.mode` cannot later change from
  SIMULATED to LIVE (existing immutability trigger, `test_s2_evidence_ledger_postgres.py:450`), and the link
  FK pins the publication's gateway. So the check made at publication time holds at admission.
- **L1 rule-8 split-statement teeth.** The fix catches the reviewed form and split DELETE/TRUNCATE. Residual
  evasions are listed in L1 above.
- **Reads on the ledger (deviation): acceptable.** Only the eight writer modules import the driver. Every
  read today, `finding_read`/`consequence_read` included, goes through one of those stores. The new methods
  call `self._run(work)` without `write=True`, issue only SELECTs, and the guard's write rules still pass.
  Cost: the evidence ledger now knows the shapes of `finding_revision_evidence` and
  `financial_consequence_*`, and repeats the cited-set SELECT already in
  `postgres_finding_store.py:283`. That coupling is acceptable for a read-only resolver. Hosting the reads
  in the finding and consequence stores behind the same `ProvenanceReads` protocol would be the cleaner
  split later. That is a preference.
- **No cutover yet.** The diff touches no read DTO, route, `finding_read.py`, `consequence_read.py` or
  date/spec heuristic. `source_provenance.py` is pure and route-safe.
- **Migration 0014 re-chain.** Stated in the phase-1 and phase-2 handoffs: it collides with LR-01
  0014/0015 and S6-01a 0014, and whichever merges later renumbers it and updates the head assertions. The
  `down_revision = "0013_schedule_state"` chain is correct against `fd7afd2c`.

## Checks run (this worktree; `assetops_backend.__file__` = `AssetOpsV1-review4\backend\...`)

- Focused pytest on the private base `assetops_s405aslice_test`, created and then dropped:
  `test_s405_resolver.py`, `test_s405_resolver_postgres.py`, `test_s405_publication_postgres.py`,
  `test_s2_evidence_ledger_postgres.py`, `test_s4_evidence_consequence_work_postgres.py`. Result:
  `78 passed in 140.71s`; JUnit tests=78, failures=0, errors=0, skipped=0.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. Both ran through a
  temporary `.venv` junction, which I removed afterwards.
- Guard mutations: 9 applied and restored, with a clean tree afterwards. Results are in L1.
- Pure probe for L2 (no file changes).
- Full backend suite: not rerun. I cite the implementer's run on code revision `a3640cce`: tests=2170,
  failures=0, errors=0, skipped=0, 687 s wall. Later commits are docs only (verified).
- Frontend: not run (no frontend change). Layout evidence: not applicable.

## Residual risk (beyond the packet)

- L2 must be settled before S4-05b wires consequence money.
- The broken-link proof drops FKs inside a rolled-back transaction, so it exercises the SQL but not a
  production path (disclosed).
- The run identity digest is never re-verified after registration (disclosed, phase 1).
