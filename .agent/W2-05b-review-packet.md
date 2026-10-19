# W2-05b review packet - EV producer (commits 1-5)

Task `tasks/W2-05b-ev-producer.md`; binding spec `.agent/W2-05b-build-spec.md` (`D-2026-10-18-w2-05-buildspec`,
rulings q1-q6). Branch `task/W2-05b-ev-producer`, worktree `AssetOpsV1-review5`. Not merged.
USER_REVIEW_REQUIRED: true, in the later owner W2 walkthrough, after independent review.

## Outcome
A registered EV-LAB-001 Lab run (six closed `ev-scenario/1` documents) executes the `ev-charger/1` pack once,
publishes `ev-publication/1` v4 reports through the real gateway Stage, commits through the ordinary
outbox -> authenticated Batch V2 -> S2 receipt path to AcceptedEvidence, and is read back by an owner-gated,
SELECT-only `GET /api/sites/{site_code}/ev/replay`. Six `ev-replay-manifest/1` fixtures pin the result. No W2-06
assessment, Finding or consequence row is produced.

## Commits (main..HEAD, no merges)
| Commit | Content |
| --- | --- |
| `59608b3f` | commit 1: strict `ev-scenario/1` catalog, EV frozen identity, EV Lab choice (API + `EvRunSetupFrame`) |
| `1d7bfd7c` | commit 2: closed `ev-charger/1` pack, total state/forcing table |
| `110f66de` | commit 3: public transform, `ev-publication/1` v4 mapping, registered Stage branch |
| `f2eafdee` | q2 corrections (N1 owner gate, N3 Lab panel, N8 ordinals) |
| `21745982` | q3 fixes (Q15 UNPLUGGED map, Q16 fault episode, Q17 IDENTITY_KWH) |
| `6c1a9a3c` | q4 Q18/Q19 (old-map Draft refusal; corrected-map republish CLI) |
| `548ca728` | commit 4: schema-7 artifact, delayed schedule, restart, Commit gate |
| `2d6c165b` | q5 fixes (N13 frozen Foundation device/component cross-check) |
| `fe84204e` | commit 5 part 1: `EvReplayService`, route, ledger REPEATABLE READ snapshot reads, N1 composition |
| `596d4c55` | commit 5 part 2: six manifests + `backend/tests/test_w205b_ev_replay_postgres.py` |
| `70a46d55` | gate inventory test: EV replay route is Lab-gated beside cold |
| handoff/notes commits | `3be98748`, `17340e61`, `f13f54f4`, `5c5c809e`, `b17ffa8c`, `888bc259`, `89f118b4`, `b75dbb9c`, `bd967b59` |

Final code revision: `70a46d55`. Packet commit follows it.

## Conformance per ruling round
- **q1 (Q1-Q14)**: Q1 window object, Q4 observation rows, Q5 seed 20517, Q9 copy, Q11 ten-key catalog rows,
  Q12 profiles, Q13-Q14 total state/forcing table - built in commits 1-2 (`test_w205b_ev_scenarios.py`,
  `simulator/tests/test_ev_pack.py`). Commit 3-5 closure followed as written.
- **q2 (N1-N8)**: N1 `create_app(ev_access, ev_owner)` default 403, injected owner 200 (catalog and replay); N3
  separate `EV charging run setup` Lab panel (captures below); N8 ordinal guard and pinned complete digest.
- **q3 (Q15-Q17, N9-N12)**: seven-label state map, fault-episode correlation, `IDENTITY_KWH` energy only.
- **q4 (Q18-Q25)**: old-map Draft refusal `EV_STATE_MAP_REFUSAL`; republish CLI; schema-7 keys (33, ruled order);
  schedule in the existing `PublicationSchedule`; Foundation -> `EvParameters`; binding rows by revision ID;
  `EV_NOTES`; `ev-delay-` ID.
- **q5 (N13-N17)**: N13 built (swap refusal before schedule/gateway; unchanged fixture reaches Stage); N14-N17
  ratified with no change; N17's real end-to-end proof is the commit-5 Postgres test.
- **q6 (Q26-Q31)**: manifest `assertions` are the literal q6 table (`EXPECTED` in the test). The test cross-checks
  each value from accepted GOOD public rows reached through persisted publication/batch/disposition links
  (test-local, not a classifier): START/terminal matched by exact session+connector, eligible deltas wholly inside
  `[START,terminal)`, nonoverlap asserted, union coverage -> `unknown_meter_seconds`. Raw accepted sums
  30/15/10/25/30/30.000 asserted beside the recomputed private world totals 30/15/10/30/30/30 (never equated).
  Fault: c2 selected, c1 FAULT 08:00/CLEAR 08:05 with no c1 START/ABORT/session delta. Contradictory: two accepted
  ENDs 08:30/08:31 with distinct event IDs, all energy fields null. Late: at 09:00 START + 30.000 known kWh and no
  END -> `INCOMPLETE`, held END PENDING and absent from batches/accepted/digest; at 09:05 released once with
  source 08:31, unchanged report key/text/event ID, `published_at >= 09:05`, received after 09:05, new batch only
  in the final replay; a repeated advance releases nothing.

## Manifests
`contract-fixtures/w2/ev/{complete,interrupted,fault,missing-meter,late-record,contradictory}.json`, sorted compact
JSON with final newline, 18 top-level keys, compact profile strings, `receipt_dispositions` rows
`{batch_external_id,ordinal,decision,error_code,accepted_evidence_id}`. Generated once with
`ASSETOPS_W205B_WRITE_MANIFESTS=1` on the first private DB (per-case UUID counter, gateway epoch `ev-<case>`,
cold W2-02 precedent); every ordinary run is a second clean DB compared byte for byte (bytes, digest and
disposition shape, which also equal the pinned IDs because allocation is held deterministic by the test only).
Complete: 164 batches, 223 envelopes, all ACCEPTED; missing-meter 222.

## Operator republish command (q4 Q19)
`python -m assetops_backend.sites.ev_lab --tenant demo --republish-corrected-bindings`
(idempotent; prints the selected revision ID/SHA when the corrected map is already effective; refuses a timeline
that is not the known old 05a shape.)

## Lab captures (q2 N3)
`.agent/W2-05b-captures/app-1440.png`, `app-390.png` (app), `mock-1440.png`, `mock-390.png` (v69). The EV panel is
a sibling after the cold panel, before `What this workspace is`; no horizontal overflow (scrollWidth = viewport).
Reviewer to confirm the ruled sentence rendered as the Panel `description` sub-line (smaller than the cold body).

## Checks run (final code revision `70a46d55` unless stated)
| Check | Result |
| --- | --- |
| `tools/check-all.ps1 -Python <plan2 venv>` (at `596d4c55`; later commits are test/doc only) | 10/10 passed, incl. dependency registry checker |
| writer-guard probes `tools/writer_guard_probes.py --seam` (full corpus, at `596d4c55`) | 129 CAUGHT, 15 ALLOWED, 0 MISSED/REFUSED, tree restored |
| writer-guard probes, default runner (`check-architecture.ps1`): `w200 foreign event evidence writer`, `w200 foreign rejection writer`, `w200 foreign disposition writer` | 3 CAUGHT, tree restored |
| `backend/tests/test_w205b_ev_replay_postgres.py` (private `w205b_c5_test`) | 12 passed |
| `test_w205b_ev_scenarios.py` + `test_w205b_ev_replay_api.py` + `test_w205a_ev_foundation_postgres.py` | 129 passed |
| simulator `test_ev_pack.py`, `test_ev_public_transform.py`, `test_cold_pack.py` | 94 passed |
| gateway suite | 260 passed |
| contracts suite | 6 passed |
| **full backend**, `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q -rfE --durations=30 --junitxml=...`, at `596d4c55`+`bd967b59` (code = final except the gate test), DB `w205b_c5_test` | wall 1979 s; JUnit tests 3096, failures 1, errors 0, skipped 0 |
| the one failure: `test_simulator_lab_gate.py::TestGateEnabled::test_enabling_the_gate_adds_only_the_simulator_lab_surface` (`/api/sites/{site_code}/ev/replay` missing from the inventory since `fe84204e`) | fixed in `70a46d55` (test-only); file rerun 20 passed |
| full host suite, serial, `pytest host/tests -q -rfEs --junitxml=...` at `70a46d55` | 780 passed; JUnit failures 0, errors 0, skipped 0; wall 686 s |
| frontend `tsc --noEmit` | exit 0 |
| frontend `npm.cmd test` (vitest, full) | 89 files, 2295 passed; wall 202 s |

An earlier full backend attempt was stopped by its 30-min cap at about 99% (one `F` seen, a worker killed by the
cap); the rerun above identified the failure. The full backend suite was **not** re-run after the test-only fix
(owner rule: no full rerun after test-only changes); a zero-failure full JUnit at `70a46d55` is therefore not
recorded. Both runs were much slower than the guide's 8-10 min (low free memory, about 4 GB).
Test DBs were created with `createdb` and dropped (`w205b_c5_test` and its harness clones); the copied
`var/sites/mg-001.yaml` was removed.

## Non-vacuous proofs (commit 5 part 2)
- Changing missing-meter `unknown_meter_seconds` 300 -> 0 in `EXPECTED` fails `test_six_registered_replays[missing-meter]`.
- Disabling `EvReplayService._linked_batch`'s COMPLETED check fails `test_corrupt_link_and_missing_run_answer_503`.
Both reverted with `git checkout --`.

## Known deviations / open notes
- N18 (pending rulings): no EV walkthrough ASGI app exists; the N1 composition is proven by tests. Asked whether 05b
  or the later owner walkthrough owes it.
- N19: "S2 delta/connector" proved as the ledger's existing `EV_CONNECTOR_MISMATCH` refusal on a GOOD
  `INTERVAL_DELTA` naming the c2 asset (task text: "S2 EV connector/delta refusals"); event/session conflicts as
  `EVENT_ID_CONFLICT` and `SESSION_ID_CONFLICT`. Asked to confirm.
- `.ai/CODE_STATE.md`, `.ai/ACTIVE_CONTEXT.md` and the task `Status:` were not edited (left to the coordinator, as for
  W2-05a).

## Implementer decisions
None. Every behaviour follows the spec and the q1-q6 rulings. Points the rulings leave open are N18-N19 above,
recorded as questions; nothing was built on them beyond the existing mechanisms.

## Residual risk / review focus
- The test-local cross-check is deliberately narrow (selected connector, one START); it is a fixture check, not
  W2-06 logic.
- Manifests pin test-held UUIDs; regenerating needs the write flag and review.
- Replay snapshot isolation (REPEATABLE READ, READ ONLY, one connection) is exercised on the real DB path but no
  concurrent-writer race test proves it.
