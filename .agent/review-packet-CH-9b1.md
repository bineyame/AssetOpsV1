# Review packet: CH-9b1 (Actions from an opportunity on `domain_action`)

Branch `task/CH-9b1-opportunity-actions` (builds `15cdc456d`, `b33016c89`, `c54e4f56f`). Rulings: build-sheet-CH-9b.md "CH9b1-R". Status: in_review. USER_REVIEW_REQUIRED: no (backend only).

## READ FIRST: link-latency risk (demo walkthrough)
No outbox event fires when a domain Action is created. A MINI (mill) Action is linked to its opportunity thread only by
(a) backfill step c (`run_threads steps c`), or (b) the next scheduler stage run that handles an `opportunity.revised`
event (`scheduling/stages.py:247` passes the placed opportunity ids to `unlinked_actions_for`). In the demo build
(DD-1 story ticks) the mill Action **may NOT show as linked on the Grow row** at walkthrough time: if the story creates
the Action after the opportunity's last revision and no later revision of that opportunity occurs, nothing links it
until someone runs `python -m assetops_backend.chain.backfill --steps c,d`. The L2 test proves the link works once a
step c runs; it does not prove the tick links it unaided. Mitigations (owner/coordinator choice, not built here):
create the mill Action in the story before the final opportunity-revising tick, or have the story finish run
`--steps c,d`, or add an outbox event on domain Action creation (new event-register entry, a CH-5c/W2 scope item).
Lifecycle ACTION_IN_HAND/CHANGE_APPLIED are written by step d / the lifecycle stage, so they follow the same latency.

## Outcome
`domain_action` carries an opportunity origin (typed `Origin`; MINI domain; exactly one origin pair); a mill Action is
created via `DomainIntentService.create_action(domain="MINI")`, linked to a W4 case, and links to its opportunity thread
(`chain_action_thread.origin_opportunity_id`). Lifecycle: ACTION_IN_HAND from the row, CHANGE_APPLIED on case COMPLETE
(day = case `occurred_at`); a linked Action keeps a 0-eligible opportunity thread from WITHDRAWN (CH-4 R6). The Finding-only
surfaces (domain Action index, Cold/EV outcomes, work store) filter `origin_opportunity_id IS NULL` and carry the
`CH-9b1 origin: Finding-only` marker, guarded by `test_ch9b1_origin_readers.py`. File anchors: handoff `.agent/CH-9b1-handoff.md`.

## Migration 0051 (`0051_action_opportunity_origin`, down `0050_chain_response_expiry`)
MINI domain on `domain_action_domain_chk` (the only domain CHECK; `work_case` has none, `0027_w4_work_cases.py:15-31`),
`domain_action_one_origin` + `domain_action_mini_origin` CHECKs, opportunity FKs, Finding pair DROP NOT NULL,
`mini_opportunity_revision_opportunity_scope` UNIQUE, `chain_action_thread.origin_opportunity_id` +
`chain_action_thread_one_origin`, trigger on `IS NOT DISTINCT FROM`, `chain_action` view +2 columns. Downgrade refuses while
an opportunity-origin Action or link exists. `git log main`: no later migration (main head still 0050), so one head.

## Acceptance evidence (all against Postgres, `assetops_test`)
- `test_ch9b1_opportunity_actions_postgres.py` 5 passed: mill Action create (idempotent on key) -> case COMPLETE -> step c
  LINKED with opportunity origin only -> lifecycle OPEN, ACTION_IN_HAND, CHANGE_APPLIED (day = case day, cause DOMAIN_CASE),
  no WITHDRAWN; CHECKs both ways (both pairs, neither, non-MINI opportunity origin, MINI with Finding pair -> rejected,
  legal MINI row accepted); MINI body with a Finding pair refused with zero writes; 0051 downgrade refused with a MINI row,
  then 0050<->0051 round trip with `domain_action`/`chain_action_thread` rows identical and CHECKs restored.
- Scoped runs: `test_ch2/3/4_*postgres` 10 passed + 1 failed; L0 ch2/ch3/ch4/ch9b1 files, `test_ch9_*`, `test_s6_verification_*`
  227 passed + 4 failed; w502 + w504 intent/index 62 passed + 2 failed (the 2 fixed in `c54e4f56f`, re-run 2 passed).
  The 5 remaining failures are **pre-existing**, not caused by 0051: `test_0042_catalogue_and_head` (trigger set grew with
  0047), `test_0048_replaces_the_noon_only_bodies_under_the_0049_head`, `test_downgrade_restores_the_0029_bodies`,
  `test_0049_enqueues_v1_service_hours_only_and_drains_to_v2` (pin 0049 as head), and
  `test_verified_resolves_then_late_evidence_withdraws_and_overlap_blocks` (S6 contract-shape fixture). The last three
  ch9/s6 failures were reproduced identically on a detached `main` worktree (removed afterwards). Not fixed here (out of scope).
- Polish clone `assetops_chainclone_ch9b1_test`: create+migrate to 0051, settle (1 tick), W6 `chain_watermark_guard`
  26 requests, non-200 0, unresolved [], untracked [], file_violations 0, modules 125; `chain_response_probe fresh`
  with `ASSETOPS_RESPONSE_STORE=on`: 23/23 stored bodies equal a fresh compose; backfill b,c,d (3 LINKED), collect 85
  requests all 200; COH check: every rule `0 new` (COH-2 2/2, COH-7 8/8 expected), self-check 10 pass 0 fail. Clone dropped.
  (Before backfill b,c,d the check shows NEW COH-10/11: no threads placed, expected.) Polish has no MINI Action.
- Guards: check-architecture passed; check-agent-workflow passed; chain coherence + event register 115 passed;
  perf-budget fixtures 8/8; estate guard 3 named self-tests passed (154 s). Non-vacuity of the Q5 allowlist guard: 5
  mutations in `test_ch9b1_origin_readers.py` (earlier build).

## Known Deviations
1. **Q6 (coordinator ruling), alternative proof.** The readers at this revision name the new columns, so "capture at 0050
   with this code" is impossible. Proof used instead (`test_q6_finding_and_cold_bodies_byte_equal_after_the_mill_action`):
   on one DB with the S6 reserve trial (MINI_TRIAL) and a Cold domain Action, capture every Finding-origin row the readers
   join (`chain_action`, `domain_action`, case links, `chain_action_thread`, thread events) plus the Finding Site's
   `lifecycle_inputs` (the clock field `now` excluded, the one value that moves between reads), add the mill Action, link,
   complete it, run lifecycle, capture again: byte-equal; the mill link existing is asserted so the proof is not vacuous.
   Plus the 0050<->0051 round trip of rows above. It does not compare HTTP bodies at 0050 vs 0051.
2. Tests pinning old DB shape updated for 0051: `test_ch2_threads.py:182` (typed origin), `test_w504_ev_intent_postgres.py`
   (domain CHECK now admits MINI + `domain_action_mini_origin`).

## Residual risk
- **Dry-run `all_actions`** (`chain/adapters/postgres_thread_sources.py`) now reads `domain_action.origin_opportunity_id`,
  so `backfill --dry-run` no longer runs against a DB below 0051.
- Link latency (top). A MINI Action raised before its opportunity is placed links at placement (pending-placement path).
- 5 pre-existing failures above sit on main and should get their own fix task.
- The L2 round trip deletes its own rows with `session_replication_role = replica` on a test DB only.
