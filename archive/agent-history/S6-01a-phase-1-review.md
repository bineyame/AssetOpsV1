# S6-01a phase 1 - independent review

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review3`, branch
`review/S6-01a-phase-1` at `1c47a687`; diff `fd7afd2c..1c47a687` (build commit `9a115431`).
Judged against `tasks/S6-01a-action-store-read.md` phase 1, `.agent/architect-S6-01-answers.md` Q1-Q5 + M1-M3 and
`D-2026-10-15-s601-action-store-and-ui`.

## Verdict

**Accept with findings fixed on the branch.** No High. One Medium (M1, capability scope), which belongs naturally
with phase 2's `D-action-records` fixture and must be fixed on the branch (or ruled by the Architect) before slice
review. Lows are non-blocking.

## Checks run (by me, on `1c47a687`)

- `assetops_backend.__file__` resolved to `AssetOpsV1-review3/backend/...`. Private DB `assetops_s601arev_test`
  (dropped afterwards).
- `pytest test_s6_action_rule.py test_s6_action_store_postgres.py test_s4_finding_read_postgres.py
  test_s1_foundation_postgres.py test_s1_bindings_postgres.py test_pg_harness.py`: JUnit 109 cases, 0 skipped,
  0 failed, 2 min 15 s. (A first attempt failed every Postgres case at setup because the base DB did not exist yet;
  not a slice defect.)
- Migration subset (`-k "downgrade or migration or head or alembic"`) of `test_s4_evidence_consequence_work_postgres.py`
  and `test_s2_evidence_ledger_postgres.py`: 4 passed (includes downgrade through 0014 and head pins).
- `tools/check-architecture.ps1`: passed (rule 8 runs here). `tools/check-agent-workflow.ps1`: passed.
- Rule-8 mutation spot checks (each reverted, tree clean): lowercase `insert into action_event` in the Foundation
  adapter, `ON CONFLICT DO NOTHING` and lowercase `update action_event set` in the Action adapter,
  `INSERT INTO action(` (no space) in the Finding store, `INSERT INTO foundation_revision` in the Action adapter - all
  fail the guard with the right message.
- Not run: full suite (phase 1, by brief); `tools/check-all.ps1` (no `.venv`/`node_modules` in this worktree; the
  architecture and workflow guards were run directly); frontend checks (no frontend change). Implementer's
  check-all 9/9 is cited, not re-verified.

## What I verified holds

- `reserve-trial-1` (`actions/reserve_trial.py`): gates in ruled order (mechanism, SUPPORTED, latest, current, Candidate
  present); SOC read from the `battery_soc` accepted evidence that the INTERVAL assessment's Candidate segment cites
  (adapter `:118-149`), GOOD/numeric/`%`, same-instant conflict, asset match; strict `> r + 10` with
  `SOC_HEADROOM_POINTS` imported from `dispatch_v3`; one unambiguous percent reserve per cited covering Foundation;
  band [15, 90]; current Site reserve must equal the pinned reserve on the same asset; proposal exactly `r - 5`.
  Typed reasons cover every ruled case. Limitation text claims no cause, runtime, saving or safety. Rule-level
  boundaries (30 vs 30.0001, 15/90 vs 14.99/90.01, missing/conflicting/non-numeric, asset, stale) and the persisted
  30 vs 30.5 case are tested. DB backs the band: `old_value BETWEEN 15 AND 90`, `proposed_value = old_value - 5`.
- Recommendation key includes tenant, Site, FindingRevision, pinned FoundationRevision, rule/version, asset; acceptance
  key = digest of key + ACCEPT; both unique per tenant/Site. Pre-accept proposal is served with no row; after accept
  the immutable snapshot (+ Action link) is returned with a separately labelled live status, and survives a reserve
  change, reassessment and a newer revision (tested).
- Concurrency: per-key advisory xact lock, re-check, then INSERT; unique constraints as backstop. Four concurrent
  identical accepts -> one Action, one event (tested). Distinct-key racers resolve to one Action + 409 by the same path.
- Append-only: `ledger_append_only` BEFORE UPDATE OR DELETE on all six tables (same pattern as every prior ledger;
  no ledger guards TRUNCATE). One ACCEPTED / at most one APPLIED per Action; non-OBSERVED events `occurred = recorded`;
  OBSERVED <= 30 days back with fixed `DEMO_REVIEW_NOTE`; actor `SYSTEM`/`service:` enforced by CHECK.
- Same-Site composite FKs on every child (Action -> Site/Finding/FindingRevision/assessment/Foundation/asset; children
  -> `action(tenant_id, site_id, id)`). `finding_revision_finding_scope_unique (tenant_id, site_id, finding_id, id)` is
  redundant for uniqueness (id is the PK) but is the necessary FK target proving the origin revision belongs to the
  origin Finding; cost is one index. No collision with LR-01's 0015 (it touches `finding_revision_basis_unique` only).
- Ninth writer: INSERT-only; registered in `$pgWriters`/`$pgWritesSeen`/`$pgDriverSeen`; reverse ownership enforced for
  every other module including the Foundation adapter; existing eight restrictions untouched.
- Capability: grants come only from the server file named by `ASSETOPS_ACTION_DEMO_GRANTS`; malformed/absent grants
  deny; POST re-checks after the read exposes it; any body key naming actor/author/principal/capability/authority is
  422 and unknown keys are 422; refusals (401/403/capability 403/404/422) write nothing (counted in the test).
- OBSERVED: `accepted_at <= occurred_at <= recorded_at`, <= 30 days, future 422, identical retry same event,
  conflicting reuse 409; state-neutral (application stays PENDING).
- Selectors: `event_id` returns the `(recorded_at, id)` prefix; `recorded_at` includes ties; both -> 422
  `ACTION_SELECTOR_CONFLICT` on both reads; selector preserved in links; backdated OBSERVED does not reorder (tested).
- Interpretations: "reviewed = persisted S4-01 matcher revision" and "current = latest AND S4 `claim_is_current` AND
  Performance gate open" are reasonable readings of the packet (no reviewed flag exists; `claim_is_current` already
  requires CURRENT basis + SUPPORTED). No finding.

## Findings

### M1 (Medium, acceptance gap) - the capability is not fixture- or Action-scoped

`backend/assetops_backend/actions/capability.py:42-69`. The grant matches `site_code` (optionally `site_id`/
`tenant_id`) and command only. `fixture_id` is one document-wide string that is echoed into the capability and the
event's `triggering_fixture`, but nothing ties the target Finding or Action to that fixture. Q4/packet require a
"tenant/Site/fixture/command-scoped" capability and M3 a "tenant/Site/Action-scoped" one for OBSERVED.

Why it matters: a grant for a Site lets SYSTEM demonstration commands accept (and, once phase 2 lands, apply a real
Foundation publish to) any supported Finding in that Site, including non-fixture or future real-source data, while
labelling it with a fixture ID it does not belong to. That is the exposure Q4's guard was meant to close, and it
becomes materially worse when apply exists.

Fix (on the branch, with phase 2's `D-action-records` manifest): bind the grant to the fixture's manifest - e.g. the
command target must be a Finding/Action created from the fixture (manifest IDs, or S4-05 `AUTHORED_DEMONSTRATION`
provenance of the revision's accepted evidence) - and make `tenant_id`/`site_id` required in a grant. Add tests: a
granted Site with a non-fixture Finding is 403 with nothing written. Alternatively obtain an explicit Architect ruling
that Site + command is the intended scope and the fixture ID is a label only.

### L1 (Low, interpretation) - re-accept with a new idempotency key is 409, not a replay

`backend/assetops_backend/actions/service.py:146-151` puts `idempotency_key` in the acceptance payload digest. The
server acceptance key already deduplicates acceptance, and the packet's "identical accept returns the same
Action/event; same key with altered payload is 409" most naturally treats the idempotency key as envelope, not
payload. The 409 is safe (nothing is written, `action_id` is returned, and GET recommendation shows ACCEPTED), so I
do not block on it. But it is a contract choice S6-01b must consume: either exclude the idempotency key from the
accept digest (new key + same semantic command -> 200 replay of the original event), or keep 409 and have S6-01b
treat `ACTION_ACCEPTANCE_CONFLICT` with `action_id` as "already accepted" and record the choice in the contract
fixture. Route to the Architect/Planner only if the coordinator wants it fixed now.

### L2 (Low, interpretation) - segment SOC uses the lowest usable reading

`reserve_trial.py:218-228`. The ruling is existential ("a usable numeric reading strictly greater than r + 10"); the
implementation requires every usable reading in the segment to clear the threshold. This only narrows eligibility (no
over-claim), and is disclosed in the handoff. Record it in the contract fixture/Architect notes so S6-01b's
unavailable copy for `SOC_NOT_ABOVE_HEADROOM` is accurate ("not every reading was above..."), or switch to the
existential rule.

### L3 (Low, test gap) - composite-FK teeth and wrong-Site read are not proven with real IDs

`backend/tests/test_s6_action_store_postgres.py:339` reads `OTHER-001/actions/{uuid4()}` - a random ID, so a real
Action ID under the wrong Site is not exercised on GET action/events (OBSERVE does use the real ID). The schema test
(`:433-487`) proves append-only and uniqueness but no insert with a cross-Site/other-Finding origin revision or
cross-Site basis evidence. The code and DDL are correct by reading; add the two cheap assertions in phase 2.

### L4 (Low, phase-2 carry) - FAILED's Foundation IDs have no same-Site FK

`migrations/versions/0014_action_store.py:144-145`: `expected_foundation_revision_id` / `current_foundation_revision_id`
on `action_event` have no `(tenant_id, site_id, id)` FK to `foundation_revision`. Phase 2 writes them; add the
composite FKs while 0014 is still unmerged.

### L5 (Low) - OBSERVE digest is offset-sensitive

`service.py:200-201` digests `occurred_at.isoformat()` in the client's offset, so the same instant resent as `Z` vs
`+03:00` is a 409. Normalise to UTC before digesting.

Note (no finding): the Action read exposes `system_demo_capability.apply.allowed = true` while no apply route exists;
this is transient until phase 2.

## Migration re-chain obligation

S6-01a's `0014_action_store` revises `0013_schedule_state` (main's head at `fd7afd2c`). LR-01's
`0014_source_clock_attestation` and `0015_finding_returning_basis` also start from 0013 and are already merged into
`task/S5-01-site-overview`. Whichever reaches main first, if LR-01 (directly or via S5-01) lands before S6-01a, S6-01a
must: rename to the next number with `down_revision = "0015_finding_returning_basis"`; update the four head pins
(`test_s1_bindings_postgres.py:118`, `test_s2_evidence_ledger_postgres.py:445`,
`test_s4_evidence_consequence_work_postgres.py:516,539`) and any LR-01 head pins; and rerun slice review and the full
suite on the re-chained revision. LR-01 0015 changes matcher replay (same-basis revisions allowed), which can change
which FindingRevision is latest in the S6 Postgres tests, so the S6 tests must be rerun, not assumed.

## Residual risk not named in the packet

- Production composition uses `development_access` for commands, so with a grants file configured any network client
  can run SYSTEM demonstration commands; the grants file is the only gate (as Q4 intends, but deploy-sensitive).
- Acceptance evaluates the rule in one read transaction and inserts in another; a reserve change in between yields an
  Action on a just-stale basis. Harmless in phase 1 (no publish); phase 2's under-lock expected-Foundation check must
  catch it (stale 409 + FAILED).
