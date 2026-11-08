# Review packet: DIESEL-K6a, the fuel Finding as a domain-Action origin (migration 0057)

- Spec: `.agent/build-sheet-DIESEL-1.md` §9m.1-§9m.3 (ruling DIESEL-1-R3m) and §9m2 (DIESEL-1-R3m2, the S-a3 fix).
- Branch: `task/DIESEL-K6a-fuel-action-origin`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k6a`.
- Commits: `b5481a7c4` (build + L0), `95b69f334` (R3m2), `9493e88e3` (merge main, K4a `3358553f8`),
  `99cd91ea2` (L2), plus this packet.
- User review required: no (backend-only; no page). Opus did the first build; first review is next.

## Outcome delivered

A `FUEL_BALANCE` domain Action can be created from the current SUPPORTED `fuel-balance-1` Finding revision on a
MINIGRID Site, linked to a COMPLETEd maintenance request, and joined to the fuel Finding's thread. It declares no
intent. Migration 0057 widens `domain_action_domain_chk` and adds the fuel arm of `verification_plan_family` (plus
`rule_id` / `plan_version`), so K6b needs no migration. The Cold/EV Action index never sees a fuel Action, and the
request page never sends one to a W1 Action page.

## Files materially changed

| File | Change |
|---|---|
| `backend/migrations/versions/0057_fuel_verification.py` | new; §9m.2 verbatim; `down_revision = "0056_unexplained_fuel_finding"` |
| `B/work/domain_action.py` | `FUEL_DOMAIN`, `FUEL_FINDING_DOMAIN`, `FUEL_MESSAGES`, `FUEL_SPEC`; `ACTION_DOMAINS` only |
| `B/work/domain_intent.py` | `create_action` fuel branch: `fuel_finding_selected`, never `selected_pin` |
| `B/work/adapters/postgres_domain_intent.py` | `_DomainTx.fuel_finding_selected` (card SQL verbatim) |
| `B/work/adapters/postgres_domain_action_index.py` | both predicates `domain IN ('COLDCHAIN', 'EV_CHARGING')`, comment line |
| `B/work/adapters/postgres_work_read.py` | `_FINDING_DOMAIN_OF` fuel entry (+ import); R3m2 conditional `action_domain` key |
| `B/work/site_index.py` | R3m2: a fuel link gets `href = None` (approved by R3m2) |
| `backend/tests/test_k6a_fuel_action_origin.py` | L0, 9 tests |
| `backend/tests/test_k6a_fuel_action_origin_postgres.py` | L2, 7 tests |
| `backend/tests/test_w504_ev_intent_postgres.py:154` | approved one-key edit |
| `backend/tests/test_out_b2_vocabulary.py` | scan list gains the five messages and the summary (merge kept K4a's block too) |

## Acceptance criteria

| Item | Status |
|---|---|
| 0057 per §9m.2 (domain CHECK, three family CHECKs, guarded downgrade) | Met; L2 1 |
| `FUEL_SPEC` in `ACTION_DOMAINS` only; `DOMAINS`/`BY_FINDING_DOMAIN` unchanged | Met; L0 2 |
| Fuel selection check, `selected_pin` skipped, `_pin` not edited | Met; L0 3, L2 2 |
| Positive Cold/EV index filter | Met; L2 4 |
| `_FINDING_DOMAIN_OF` entry; request lineage true, pin None | Met; L2 5 |
| R3m2: no `/actions/{id}` href for a fuel Action (detail and index) | Met; L0 R3m2 test, L2 5 |
| Thread link with no new code | Met; L2 6 |
| Five messages and summary pass guard V and H4 | Met; L0 5, `test_out_b2_vocabulary` |
| Must stay green unchanged | Met, with the coordinator-cleared :132 DDL pin (Known Deviations 1) |
| Guards | Met: `tools\check-all.ps1 -Python <plan2 venv>` on `723360e51`, all 17 guards passed (1,445 s), including architecture seams and agent workflow |

## Checks run (DB `assetops_k6_test`, created empty for this unit; harness clones)

- L0: `test_k6a_fuel_action_origin.py` 9 passed; with adjacent light files, 109 passed and 25 skipped (the DB-gated ones skip).
- L2: `test_k6a_fuel_action_origin_postgres.py`: 7 passed in 22 s.
- Must stay green (`ASSETOPS_TEST_DATABASE_URL` = `assetops_k6_test`), each step run alone with free RAM checked first (3.0-3.4 GB):
  - `test_w502_*` (index API/postgres, intent API/postgres, work links): 26 passed (452 s).
  - `test_w504_*` (intent API/postgres, work producer): 24 passed, 1 failed (820 s) on the :132 DDL pin; after the cleared edit, `test_w504_ev_intent_postgres.py` 15 passed (528 s).
  - `test_ch9b1_*`, `test_ch9b2_*` (both), `test_ch9b3_*`, `test_s4_finding_domain_filter_postgres`: 24 passed (118 s).
  - `test_k4a_*`, `test_k3_*`, `test_k2_*`: 32 passed (74 s).
- Must-fail proofs. Each was applied after the commit and reverted with `git checkout --`.
  - L0, `FUEL_SPEC.origin = ORIGIN_OPPORTUNITY`: 6 failed.
  - L0, `FUEL_SPEC` added to `DOMAINS`: the domain-table test failed.
  - L0, fuel branch falls through to `selected_pin`: 2 failed.
  - L0, R3m2 branch removed: the href test failed.
  - L2, `fr.lifecycle = 'SUPPORTED'` dropped: the withdrawn-revision refusal did not raise.
  - L2, `max(revision_no)` dropped: the older-revision refusal did not raise.
  - L2, index predicate reverted to `origin_opportunity_id IS NULL`: `action(id)` returned the fuel row.
  - L2, R3m2 branch removed: the request detail served `/sites/KOBO-001/actions/{id}/verification`.
- Head bookkeeping: none needed. The K2, K3 and K4a tests name fixed `MIGRATION, PREVIOUS` pairs that still hold, and they passed unchanged.

## Known deviations

1. Coordinator-cleared S-a5: DDL pin follows 0057 (§9m), same kind as the approved :154 edit.
   `test_w504_ev_intent_postgres.py:132` (`test_sole_head_chain_and_named_checks`) now ends
   `'MINI'::text, 'FUEL_BALANCE'::text])))`; nothing else in that file changed.
2. L2 4's Cold row is a raw `COLDCHAIN` `domain_action` insert on the Kobo Site carrying the fuel Finding pair (the
   0051 CHECKs admit it), not a Cold Action built as `test_w502_*` does. It proves the positive filter still lists a
   Cold row without standing up the cold Site; the real Cold path is covered by the unchanged `test_w502_*` run.
3. L2 1's "downgrade refused with a fuel plan row" runs with the plan's Action present (a fuel plan always cites a
   domain Action); the Action-only refusal is its own test.

## Residual risk

- The fuel Action shows on the request page as a plain "Action" with no link until K6b's verdict page and Ref land.
- `chain/site_chain.py` `action_wire_ref` still gives a fuel Action an `ACTION` Ref (K6b, §9m.1(6)).

## Review focus

0057's fuel arm text against §9m.2. The `create_action` branch order (site type, then Finding domain, then fuel
selection). Whether Known Deviation 1 takes the one-line edit.
