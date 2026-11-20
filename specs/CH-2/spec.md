# Build sheet CH-2: Finding threads, the Action-to-thread link, the backfill

- Architect: Claude, 2026-11-03.
- Plan: `Docs/demo-sprint/client-demo-plan.html` (agreed). Lane 2 starter.
- Design: `Docs/demo-sprint/implementation-logic-design-proposal.html`:
  - AG-10, AG-25;
  - §4.3 `finding_thread*` and `chain_action`;
  - §4.4 thread states;
  - §5.2 A2;
  - §12 backfill;
  - §15 CH-2 row (6 units).
- Branch: `task/CH-2-threads`, cut from main after **CH-0** merges.
- Paths: `B/` = `backend/assetops_backend/`, `M/` = `backend/migrations/versions/`. Lines are to `73a558a1b`.

## 0. Result and boundary

**Observable result.**
- Kobo's three generator Findings (17, 24 and 31 Oct) are occurrences 1–3 of one thread.
- The Cold lab start failure is one thread with 2 occurrences.
- Every Action and domain Action is linked to its thread.
- The Portfolio shows ACT-001 on its Finding row (I-03).
- The Cold and EV boards list ACT-002 and ACT-003 in hand when their Finding is on the board (I-09, display part; the story-time producer change is in DD-1).
- The coherence check gains the thread rules and passes them on the L3 clone.

**Not in this slice.**
- The lifecycle transitions ACTION_IN_HAND, CHANGE_APPLIED and RESOLVED_MONITORING (CH-3, A5). CH-2 writes only the occurrence-driven events OPEN and RECURRED (A2).
- Opportunity screens (CH-4). CH-2 places OPP occurrences, because the backfill covers them, but changes no opportunity UI.
- ChainReader and the deletion of the old joins (CH-5a). CH-2 changes exactly two joins (§5) and nothing else on the read path.
- No change to matchers, `finding_episode` recurrence proof, money or verification rules (High).

## 1. Architect rulings on design gaps found in the code (logged; none needs the owner)

| # | Gap (code reality) | Ruling |
|---|---|---|
| R1 | `action` and `domain_action` are append-only. `M/0016:230-231` uses `ledger_append_only`, and `M/0033:133-134` uses `w4_append_only`. The design's `ALTER TABLE action ADD thread_id` plus a backfill UPDATE (§4.3, §12 c and e) would be refused by those triggers. | Leave both tables unaltered. Add an append-only link table, **`chain_action_thread`**, and build `chain_action` as a view over the two tables LEFT JOINed to it. Step (e), NOT NULL, becomes the coherence rule COH-11, "every Action has a thread link". |
| R2 | `finding_revision` and `mini_opportunity_revision` have no `recorded_at`. | Order the backfill by `created_at`, then `id`. |
| R3 | OPP rows have no mechanism or subject. | The thread key is mechanism `PRODUCTIVE_USE_HEADROOM`, `subject_kind='SITE'`, `subject_ref='SITE'`, `finding_type='PRODUCTIVE_USE_HEADROOM@1'`. |
| R4 | The design keys Cold on `SITE`, but cold Findings always carry `subject_asset_id` (`postgres_finding_store.py:636-649`; `M/0022:45-54`). | The subject comes from stored columns, as the design's §11 risk mitigation says: Kobo uses `generator_asset_id`, Cold and EV use `subject_asset_id`, all as `ASSET`. If the two Cold occurrences carry different asset ids on the L3 clone, **report it**; do not merge them. |
| R5 | The design's FKs are single-column, but this codebase scopes FKs by tenant and Site. | Use composite FKs to `finding(tenant_id, site_id, id)` (`M/0009:55`) and to `mini_opportunity`'s scope key (pre-flight P1). |
| R6 | Migration ids, for two lanes | `0042_chain_threads`. Its `down_revision` is `"0041_walk1_objective_min_days"` if CH-1a's 0043 is not on main at merge, else `"0043_chain_snapshots"`. No merge migration. |

## 2. Migration `M/0042_chain_threads.py`

```sql
CREATE TABLE finding_thread (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  mechanism text NOT NULL CHECK (mechanism ~ '^[A-Z][A-Z0-9_]{1,62}$'),  -- stored mechanisms + 'PRODUCTIVE_USE_HEADROOM'
  subject_kind text NOT NULL CHECK (subject_kind IN ('SITE','ASSET','CONNECTION','CUSTOMER')),
  subject_ref text NOT NULL,
  finding_type text NOT NULL,                     -- '<MECHANISM>@<matcher or model version>'
  opened_at timestamptz NOT NULL,
  created_by text NOT NULL,                       -- 'backfill' | 'tick'
  CONSTRAINT finding_thread_key UNIQUE (tenant_id, site_id, mechanism, subject_kind, subject_ref),
  CONSTRAINT finding_thread_scope UNIQUE (tenant_id, site_id, id),
  FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id));

CREATE TABLE finding_thread_occurrence (
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  thread_id uuid NOT NULL,
  occurrence_no int NOT NULL CHECK (occurrence_no >= 1),
  finding_id uuid NULL, opportunity_id uuid NULL,
  episode_start timestamptz NULL, episode_end timestamptz NULL,
  joined_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  evidence_class text NOT NULL CHECK (evidence_class IN ('MEASURED','RECORDED','DECLARED','MODELLED','EXTERNAL')),
  PRIMARY KEY (thread_id, occurrence_no),
  CHECK ((finding_id IS NULL) <> (opportunity_id IS NULL)),
  CONSTRAINT occurrence_finding_once UNIQUE (finding_id),
  CONSTRAINT occurrence_opportunity_once UNIQUE (opportunity_id),
  FOREIGN KEY (tenant_id, site_id, thread_id) REFERENCES finding_thread (tenant_id, site_id, id),
  FOREIGN KEY (tenant_id, site_id, finding_id) REFERENCES finding (tenant_id, site_id, id),
  FOREIGN KEY (<mini_opportunity scope key>) REFERENCES mini_opportunity (<scope key>));   -- P1

CREATE TABLE finding_thread_event (
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  thread_id uuid NOT NULL, seq int NOT NULL CHECK (seq >= 1),
  state text NOT NULL CHECK (state IN ('OPEN','ACTION_IN_HAND','CHANGE_APPLIED','RESOLVED_MONITORING',
                                       'CLOSED','RECURRED','REOPENED','WITHDRAWN')),
  cause_kind text NOT NULL CHECK (cause_kind IN ('OCCURRENCE','ACTION_EVENT','VERIFICATION_OUTCOME',
                                                 'DOMAIN_CASE','CLEAN_DAYS','WITHDRAWAL','SUPPORT_LOST')),
  cause_id text NOT NULL,
  effective_day date NOT NULL,                    -- Site-local day of the cause (AG-27)
  policy_version text NOT NULL,                   -- 'thread-lifecycle/1'
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (thread_id, seq),
  CONSTRAINT thread_event_cause_once UNIQUE (thread_id, cause_kind, cause_id),
  FOREIGN KEY (tenant_id, site_id, thread_id) REFERENCES finding_thread (tenant_id, site_id, id));

CREATE TABLE chain_action_thread (                -- R1: replaces ALTER TABLE action/domain_action ADD thread_id
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  action_kind text NOT NULL CHECK (action_kind IN ('MINI_TRIAL','DOMAIN_INTENT')),
  action_id uuid NOT NULL,
  thread_id uuid NOT NULL,
  origin_finding_id uuid NOT NULL,
  linked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  linked_by text NOT NULL,                        -- 'backfill' | 'tick'
  PRIMARY KEY (action_kind, action_id),
  FOREIGN KEY (tenant_id, site_id, thread_id) REFERENCES finding_thread (tenant_id, site_id, id));
  -- action_id FKs: MINI_TRIAL → action (tenant_id, site_id, …) and DOMAIN_INTENT → domain_action
  -- (tenant_id, site_id, id) (M/0033:56) are enforced by a BEFORE INSERT trigger
  -- (chain_action_thread_target), because one column cannot carry two FKs; the trigger raises when the target is missing.

CREATE VIEW chain_action AS
  SELECT a.id, a.tenant_id, a.site_id, a.action_code, 'MINI_TRIAL'::text AS kind,
         l.thread_id, a.origin_finding_id, a.origin_finding_revision_id
    FROM action a LEFT JOIN chain_action_thread l ON l.action_kind = 'MINI_TRIAL' AND l.action_id = a.id
  UNION ALL
  SELECT d.id, d.tenant_id, d.site_id, d.action_code, 'DOMAIN_INTENT',
         l.thread_id, d.origin_finding_id, d.origin_finding_revision_id
    FROM domain_action d LEFT JOIN chain_action_thread l ON l.action_kind = 'DOMAIN_INTENT' AND l.action_id = d.id;

CREATE INDEX finding_thread_site ON finding_thread (tenant_id, site_id);
CREATE INDEX finding_thread_event_head ON finding_thread_event (thread_id, seq DESC);
CREATE INDEX chain_action_thread_by_thread ON chain_action_thread (thread_id);
-- append-only: ledger_append_only() triggers on all four tables (as M/0030:228-229)
```

**Downgrade.** Refuse when any of the four tables has rows, as `M/0030:240-252`. Otherwise drop, in reverse order: the view, the triggers, the indexes, then the tables.

## 3. `B/chain/threads.py`: ThreadRegistry (A2, pure core plus ports)

```python
@dataclass(frozen=True)
class Source:  # one Finding revision or one OPP revision, as read by the port
    tenant_id: UUID; site_id: UUID; site_tz: str
    finding_id: UUID | None; opportunity_id: UUID | None
    mechanism: str; subject_kind: str; subject_ref: str; finding_type: str
    transition: str | None          # finding_revision.transition; None for OPP
    lifecycle: str | None
    episode_start: datetime | None; episode_end: datetime | None
    created_at: datetime; revision_id: UUID

def key_of(src) -> tuple[UUID, UUID, str, str, str]          # (tenant, site, mechanism, subject_kind, subject_ref)
def plan_place(src, existing_occurrence: bool, thread: ThreadHead | None) -> PlacePlan
    # existing_occurrence → NOOP; transition == 'MERGED_INTO' → NOOP
    # thread None → CREATE_THREAD + ADD_OCCURRENCE(no=1) + EVENT(OPEN, OCCURRENCE, src id)
    # thread state in (RESOLVED_MONITORING, CLOSED) → ADD_OCCURRENCE(no=n+1) + EVENT(RECURRED)
    # thread state in (None, WITHDRAWN) → ADD_OCCURRENCE + EVENT(OPEN)
    # otherwise → ADD_OCCURRENCE only
```

**No outcome link (OL-1, plan §2.4).** A thread stores `mechanism` and `finding_type` only. Which outcomes it moves or checks stays declared in `B/outcomes/outcome_map.py`, keyed by `finding_signal_key(mechanism)`. Do not add outcome ids or map keys in `B/chain/`. CH-6's ratchet guard will fail on them.

**Subject mapping (R4).**

| Kind | subject_kind | subject_ref | mechanism | finding_type |
|---|---|---|---|---|
| mini_grid | ASSET | `generator_asset_id` | `finding.mechanism` | `f"{mechanism}@{matcher_version}"` (`M/0009` `matcher_version`) |
| cold_chain, ev_charging | ASSET | `subject_asset_id` | `finding.mechanism` | `f"{mechanism}@{matcher_version}"` |
| OPP | SITE | `'SITE'` | `PRODUCTIVE_USE_HEADROOM` | `PRODUCTIVE_USE_HEADROOM@1` |

**Other fields.**
- `evidence_class` is `MEASURED` for all of today's types (design §4.3).
- `effective_day` is the Site-local date (`site.timezone`) of `episode_start`, else of `created_at`.
- `opened_at` is the first occurrence's `episode_start`, else `created_at`.

**Linking an Action to its thread.** `link_action(kind, action_id, origin_finding_id)`:
- Look up the occurrence of `origin_finding_id` and write `chain_action_thread`.
- If there is no occurrence yet, return `PENDING_PLACEMENT` and write nothing; a later run links it.
- It is idempotent on the PK.

**Writer.** `B/chain/adapters/postgres_thread_store.py` is insert-only on the four tables, and runs one transaction per Source. It takes `SELECT … FOR UPDATE` on the `finding_thread` key row, or relies on `INSERT … ON CONFLICT (key) DO NOTHING` followed by a re-select, so that concurrent ticks cannot make two threads.

**Reader port.** `B/chain/adapters/postgres_thread_sources.py` (`$pgReaders`) provides:
- `sources(tenant, site=None, after=None)`: Finding revisions joined to `finding`, plus OPP revisions joined to `mini_opportunity`, ordered by `(created_at, id)` (R2), with `site.timezone`;
- `unlinked_actions(tenant, site=None)`: `chain_action` rows with a null `thread_id`.

## 4. Backfill and the live catch-up

**`python -m assetops_backend.chain.backfill [--tenant <slug>] [--site <code>] [--steps b,c] [--dry-run]`**
- It follows `B/declare_objective.py` (argparse `prog`, the dev tenant only with exit 2 otherwise, DATABASE_URL required with exit 1 otherwise, one JSON line per step result).
- **Step (a), snapshots.** It runs only when `assetops_backend.chain.builder` is importable, i.e. CH-1a is merged. It calls `SnapshotBuilder.build_range` for each Site. If CH-1a is absent, it prints `{"step": "a", "skipped": "CH-1a not merged"}`.
- **Step (b).** `plan_place` and apply, over `sources()` in order.
- **Step (c).** `link_action` over `unlinked_actions()`.
- **Step (d)** belongs to CH-3. Here it prints `skipped` until CH-3 registers it.
- **Step (e)** is replaced by COH-11 (R1).
- **`--dry-run`** runs (b) and (c) in memory and prints the planned threads, occurrences and links without writing. This is the L4 read-only mode on `assetops_polish_full_test`: SELECT only, and it **never runs without `--dry-run` against that DB**. The CLI refuses a non-dry run when the database name is `assetops_polish_full_test` or `assetops_demo3_full_test`.
- **Deterministic and idempotent.** Thread ids are `uuid5(NAMESPACE, "thread|" + "|".join(key))`, so two runs produce identical rows. A second run writes 0 rows.

**Live path (until CH-1b's outbox).** `B/scheduling/tick.py` `_site` gains one stage `chain_threads` after `s4`. It is a stage child in `B/scheduling/stages.py` running backfill steps (b) and (c) for that Site only, bounded by a new `TickLimits.chain_seconds: float = 60` and validated like the others (`tick.py:78-97`). CH-0's per-stage perf line maps `chain_threads` to `chain_seconds`. CH-1b later replaces the trigger with outbox events; the step functions stay the same.

## 5. The two read-path changes (and only these)

1. **Portfolio Action join (I-03).** `B/estate/portfolio.py:127-137` `_action_for` today matches `(source_finding_id, source_finding_revision_id)` exactly.
   - Change it to match on **thread**: the row's Finding occurrence thread equals the Action's `chain_action.thread_id`. The latest `_selected_recorded_at` still wins, and `ActionSelectionError` is kept for real conflicts.
   - The thread id per row and per Action is supplied by the estate read adapter (`B/estate/adapters/postgres_estate_read.py`) through one added join to `finding_thread_occurrence` and `chain_action`. The source fields come from `B/estate/coverage.py:394-395`.
   - When no thread exists (for example a DB without a backfill), the old exact match remains as a fallback, so nothing changes for un-backfilled data.
   - The same `action_for` is used by `B/site_outcomes/mini.py:627`. Keep the call; it inherits the change.
2. **Board "in hand" for domain Actions (I-09, display).** `B/site_outcomes/board.py:630-649` looks Actions up by `origin_finding_id`.
   - Add a thread match: a domain Action whose thread equals the thread of a Finding shown on the board is listed as in hand, under the existing `in_hand` item shape and wording.
   - `linked_actions` (`:530-533`) and `refresh_chain` (`:497-520`) are **not** changed; CH-5a deletes them.
3. **Additive body fields, no copy change.**
   - Portfolio rows gain `thread: {"id": str, "occurrence_no": int, "occurrences": int} | null`.
   - Board FINDING issue `ref` gains the same `thread` object.
   - Update the frontend types (`F/estate/estateClient.ts` `EstatePortfolioRow`, `F/sites/outcomeBoardClient.ts` `OutcomeIssue.ref`) as optional fields. Nothing renders them yet; CH-5a renders recurrence.

## 6. Coherence rules added to `tools/checks/chain_coherence.py`

There is no new route. The thread rules read only the additive body fields from §5: the Portfolio row's `thread` and the board's `ref.thread`.

| Rule | Pass condition |
|---|---|
| COH-10 thread identity | Expected threads per Site, from `tools/checks/fixtures/chain_coherence/expected-threads.json`: Kobo generator: 3 occurrences (findings `4d121cdb…`, `cbbc4916…`, `706d2f14…`; full ids from the clone); Cold start failure: 2 (`f9ed0fec…`, `2505d188…`); EV interruption: 1; Kobo headroom: OPP-000003 and OPP-000004. Each Finding's `thread.occurrence_no`/`occurrences` agrees across the board and the Portfolio for the same window. |
| COH-11 every Action linked | Every Action in estate actions and in the domain action index has a thread (Portfolio row `thread` present wherever COH-2 applies). |

On the L3 clone after the backfill, the CH-0 findings for COH-2 (Kobo ACT-001) and COH-3 (Cold and EV) are **resolved**. Remove them from `expected-today.json` in this slice. Cold ACT-002 and EV ACT-003 stay expected under COH-3 only if they fall outside the board window, which is the producer issue DD-1 fixes; note which.

## 6b. Demo-shaped logic this slice touches (standing rule DS-R1, plan §2.3)

| Item | Touched how | Resolution in this slice |
|---|---|---|
| 3. Generator-shaped subject (Finding identity built around `generator_asset_id`, `M/0009:41-43`) | The thread key | **Fixed for threads.** The key is generic: `subject_kind` and `subject_ref` from stored columns per domain (R4). There is no generator assumption outside the mini_grid mapping row, and a fourth domain needs only a mapping row. The L0 tests include a synthetic domain with `subject_asset_id`. |
| 2. The Portfolio "No action agreed yet" for a refreshed Finding revision (exact-revision join, `B/estate/portfolio.py:127-137`) | The join is changed | **Fixed** by the thread join (§5.1). The old exact match remains only as a fallback for data with no threads. |
| 4. Cold and EV Actions recorded at build time | The board in-hand join (§5.2) | **Labelled keep, owned by DD-1.** CH-2 does not widen any window to make them appear. |
| 4. "Verified on example data" (`B/site_outcomes/board.py:50`) | Same file; that line and its function are not edited | Not touched (DS-R1 "touches" means the function or copy itself). Owned by CH-5a. |
| `reserve-trial-1` CHECK, dispatch constants | Not touched | SWEEP-DS / CH-8 |
| 4. Build time used as story time (review M1). OPP occurrences and OPEN events took `created_at`, the build day, not the study window (`M/0030:144-147`). | Thread time fields | **Fixed.** Every thread time comes from a stored story time:<br>• OPP: the Site-local start of `first_day` and the end of `last_day`;<br>• Findings: `episode_start`/`episode_end`.<br>`created_at` is used only where no story time is stored, and then it is labelled `time_basis: "recorded_at"` in the occurrence's provenance and listed in the packet for SWEEP-DS. |

Reviewers check this table against the diff.

## 7. Localised test ladder

1. **L0 pure:** `tools\run-host-tests.ps1 -- backend/tests/test_ch2_threads.py`
   - `plan_place` truth table: new key, existing occurrence, MERGED_INTO, each thread state, split-off Finding as a new occurrence on the same thread;
   - `key_of` per kind;
   - uuid5 determinism;
   - `effective_day` in Addis and UTC.
2. **L2 Postgres, scoped:** `tools\run-host-tests.ps1 -- backend/tests/test_ch2_thread_store_postgres.py`, on `pg_harness.fresh_database()` (as `test_s1_bindings_postgres.py:66-85`; it migrates to head, which proves 0042's `down_revision`).
   - The 0042 catalogue, the four append-only triggers and the target trigger.
   - Downgrade refused with rows.
   - The view returns both kinds.
   - Two concurrent placements of the same key give one thread.
   - **Property tests:**
     - running the backfill twice gives identical rows (a full table dump compare);
     - shuffled source order within the same `created_at` gives an identical result.
   - Seed with the existing Finding case runner (`test_s4_finding_store_postgres.py` `SPEC`, `CaseRunner`, `run_case`), plus one Action through the s6 harness (`test_s6_action_store_postgres.py:119-131`). Register the seeded set-up in `setup_cache` `FUNCTION_OPS` (`backend/tests/setup_cache.py:77`).
3. **Existing, scoped, unchanged:**
   - `test_s4_finding_episode.py`, `test_s4_finding_index_postgres.py`, `test_s6_action_store_postgres.py`;
   - `test_w303_portfolio_api.py`, `test_w303_portfolio_reduction.py`, `test_w303_portfolio_fixture_postgres.py`;
   - `test_out_b4_board_postgres.py`, `test_out_b1_board.py`;
   - the tick tests `test_s4_schedule_tick_postgres.py -m "not slow"`;
   - `test_ch0_tick_timing.py`;
   - every test importing `estate.portfolio` or `site_outcomes.board` (list them in the packet).
4. **L4:** `python -m assetops_backend.chain.backfill --dry-run` against `assetops_polish_full_test` (SELECT only). It must print the §6 expected threads. Run it before the clone, as a seconds-long proof of identity.
5. **L3:**
   - `python tools/chain_clone.py create ch2 --migrate`;
   - run the backfill (`--steps b,c`) twice, expecting 0 rows on the second run;
   - `chain_coherence.py collect` and `check` with the updated expect file: COH-10 and COH-11 pass, and COH-2 Kobo is resolved;
   - `python tools/chain_clone.py drop ch2`.
6. **Frontend, scoped:** `npx vitest related --run src/estate/estateClient.ts src/sites/outcomeBoardClient.ts`, for the type changes only.
7. **Guards, run directly:**
   - A, Architecture seams;
   - W, Agent workflow;
   - the chain-coherence fixtures line;
   - **the estate guard self-tests**, because this slice edits `configuration-persistence.ps1`;
   - all others deferred.

## 8. Guard registration (`tools/checks/configuration-persistence.ps1`)

As for `$trialComparisonWriter` (`:866-869`, `:878`, `:933`, `:938`, `:1012`, `:1234-1247`, `:1499-1501`):
- `$threadWriter = backend/assetops_backend/chain/adapters/postgres_thread_store.py`, with tables `finding_thread`, `finding_thread_occurrence`, `finding_thread_event` and `chain_action_thread`, insert-only;
- `$pgReaders` gains `postgres_thread_sources.py`;
- the `chain` `$domains` entry is shared with CH-1a. Whichever slice merges second adds to it, not a second entry.

## 9. Pre-flight items (answer from code, batch them, then stop)

- **P1.** The `mini_opportunity` scope unique key (`M/0030:144-170`), for the composite FK.
- **P2.** The domain action index and the board's domain-action lookup (`B/site_outcomes/cold.py:198`, `board.py:636-649`, `read.py:203`): confirm where the thread join is cheapest without touching `linked_actions`.
- **P3.** Whether the estate read adapter's snapshot (`postgres_estate_read.py`) can carry the thread join in its existing query, or needs one extra query per request. Either is fine. State the count; P-1 says to avoid per-Site queries.
- **P4.** The stage-child registration pattern in `B/scheduling/stages.py` for the new `chain_threads` stage, and the `schedule_site_head` stage CHECK (`M/0030:231-233` lists the stages). Does a new stage name need a CHECK change? If so, put it in 0042; it is append-only-neutral.
- **P5.** The full ids of the expected Findings and OPPs: take them from the L4 dry run.

## 10. Review focus

- No UPDATE or DELETE on `action`, `domain_action` or any chain table (R1), and the old tables are unaltered.
- The thread key comes only from stored columns. Recurrence proof (`finding_episode`) is untouched.
- Exactly two read-path joins change, each with a fallback to the old behaviour when no thread exists.
- The backfill is deterministic: uuid5 ids, two runs identical.
- Any change to matchers, money or verification is High.
