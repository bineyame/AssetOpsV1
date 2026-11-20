# Build sheet CH-3: thread lifecycle and verification feedback

- Architect: Claude, 2026-11-03.
- Plan: `Docs/demo-sprint/client-demo-plan.html` (agreed). Lane 2 (6 units).
- Design: `Docs/demo-sprint/implementation-logic-design-proposal.html`:
  - §4.4 thread state machine;
  - §5.2 A5 (verification feedback and row effect);
  - AG-23 (OD-2) and AG-24 (OD-3);
  - §9 walkthrough;
  - §15 CH-3 row.
- Branch: `task/CH-3-lifecycle`, cut from main after **CH-2** merges. It uses the outbox `action.event@1` / `verification.outcome@1` events once CH-1b has merged; until then it runs from the backfill step (d) and from the `chain_threads` stage scan (§3).
- Paths: `B/` = `backend/assetops_backend/`. Lines are to main at `75637eb56`, plus CH-2 at `6185d261d`.

## 0. Result and boundary

**Observable result** (I-01, I-02, I-11, I-12 and I-24; ST-2):
- **Kobo generator thread:** reads "Fix verified, monitoring" from 1 Nov. The 31 Oct board tags the cost row "Before the change on 1 Nov" and shows the after state. On 1 Nov the thread gives no Needs-attention signal, and the row state comes from the KPI verdict.
- **Money:** ACT-001's cost check is `MODELLED_NO_IMPROVEMENT`, so no money is credited, and the copy says "modelled, not saved".
- **Recurrence:** a new occurrence after the verified change reads "Came back on …" (RECURRED). The old Action moves to Earlier and is never shown as in hand for the new occurrence (CH-2 L1).
- **Cold and EV:** the threads read "Action agreed" (ACTION_IN_HAND).
- **Portfolio progress:** the verified count and "Priority sites" come from thread states (I-24).

**Not in this slice.**
- The Grow and Portfolio window composition (CH-6).
- Cold and EV verification plans (§16; ex-slice F).
- No change to the verification rules, the cost model or matchers (High).
- Screens are not rebuilt (CH-5a). Copy changes go only to the four lines in §5, through the existing board composition.

## 1. Lifecycle policy (declared config, reviewed as code): `config/chain/thread-lifecycle-v1.json`

```json
{"schema": "thread-lifecycle", "version": 1, "policy_version": "thread-lifecycle/1",
 "close_after_clean_complete_days": {"default": 7, "by_site_type": {}},
 "inconclusive_expiry_days": 7,
 "clean_day_measures": {
   "GENERATOR_SUPPORT_CANDIDATE": ["avoidable_gen_min"],
   "COLD_START_FAILURE": ["backup_start_chain"],
   "COLD_EXCURSION": ["chamber_temp_c"],
   "EV_INTERRUPTION": ["charging_kwh"],
   "PRODUCTIVE_USE_HEADROOM": ["noon_headroom_kw"]}}
```

- `close_after_clean_complete_days` is OD-2 / AG-23: 7 Complete days with no recurrence, configurable per Site type.
- `inconclusive_expiry_days` is design §4.4: "later_end + 7 days".
- `clean_day_measures` is the evidence basis of a "clean Complete day" per mechanism.
  - It names measures, never outcomes (OL-1).
  - CH-8 moves it into the catalogue's `finding_types` section unchanged.
- The loader lives in `chain/adapters/file_chain_config.py` (the rule-2 placement from CH-1a). An invalid file raises `ChainConfigError`.

## 2. State machine and A5 (`B/chain/lifecycle.py`, pure)

```python
TRANSITIONS = {  # (from_state, cause) -> to_state ; design §4.4
  (None|'OPEN'|'REOPENED'|'RECURRED', 'ACTION_ACCEPTED')  -> 'ACTION_IN_HAND',   # action_event ACCEPTED, or domain_action raised
  ('ACTION_IN_HAND',                 'ACTION_APPLIED')   -> 'CHANGE_APPLIED',   # action_event APPLIED, or domain case COMPLETED
  ('CHANGE_APPLIED',                 'VERIFIED')         -> 'RESOLVED_MONITORING',
  ('CHANGE_APPLIED',                 'INEFFECTIVE')      -> 'REOPENED',
  ('CHANGE_APPLIED',                 'INCONCLUSIVE_EXPIRED') -> 'REOPENED',
  ('RESOLVED_MONITORING',            'RESOLUTION_WITHDRAWN') -> 'CHANGE_APPLIED',
  ('RESOLVED_MONITORING',            'CLEAN_DAYS')       -> 'CLOSED',
  ('RESOLVED_MONITORING'|'CLOSED',   'OCCURRENCE')       -> 'RECURRED',          # already appended by CH-2 place()
  ('OPEN',                           'SUPPORT_LOST')     -> 'WITHDRAWN',         # guard: no Action on the thread
}
def next_events(head, causes, policy) -> list[EventPlan]      # causes ordered by (effective_day, recorded_at, id)
def effective_day(cause, site_tz) -> date
    # ACCEPTED: local day of action_event.recorded_at; APPLIED: local day of the change's effective_from (mini)
    # or of the case completion (domain); VERIFIED: local day of change(a).effective_from (A5);
    # INEFFECTIVE/RESOLUTION_WITHDRAWN: local day of recorded_at; CLEAN_DAYS: the Nth clean Complete day
```

**Rules for applying causes.**
- **Illegal transitions** (a cause not valid from the current state) are skipped and reported. They are never written and never raise; later causes still apply. This is the design's "the Action store and its rules do not change".
- **Idempotent** on `UNIQUE(thread_id, cause_kind, cause_id)` (M/0042).
  - `cause_kind` mapping: ACTION_EVENT for ACCEPTED/APPLIED/RESOLUTION_WITHDRAWN, VERIFICATION_OUTCOME, DOMAIN_CASE, CLEAN_DAYS (`cause_id = "<thread>:<Nth day>"`), SUPPORT_LOST and WITHDRAWAL.
- **Action-to-thread scope.** Only an Action linked to the thread (`chain_action.thread_id`) produces causes.
- **Segments** (an Action linked to an earlier segment does not move a later one): see §3.
- **INCONCLUSIVE.** At each lifecycle run, a thread in CHANGE_APPLIED whose latest outcome is INCONCLUSIVE and whose plan `later_end + inconclusive_expiry_days` is before `db_now` gets `INCONCLUSIVE_EXPIRED` (`cause_id = outcome id`). Pre-flight P2 names the field holding the plan's `later_end`.
- **CLEAN_DAYS.** On a RESOLVED_MONITORING thread, count the Site-local days after the RESOLVED_MONITORING `effective_day` where:
  - every `clean_day_measures` snapshot for the thread's subject is COMPLETE; and
  - no occurrence started that day.

  This uses `SnapshotReader.grade_counts_many` / `latest` from CH-1a; it is a read, with no new table. On the Nth such day, CLOSED.
  - **Honest consequence today:** Kobo days are PARTIAL under the 24 h calendar (CH-1a §5c), so the Kobo thread stays RESOLVED_MONITORING until DD-1 extends the days. The copy says how many fully checked days are still needed (§5).

## 3. Segments: the RECURRED join (CH-2 L1)

- **Definition.** A thread's segments are split at each `OPEN`, `RECURRED` or `REOPENED` event, numbered 1..n. Each occurrence belongs to the segment current at its `joined_at` in event order, and each Action to the segment current at its link time.
  - Segments are **computed** in `B/chain/lookup.py` from events and occurrences in one query. Nothing is stored.
  - The CH-2 `thread_lookup` gains `segment_no` per occurrence and per Action, plus `state` and `state_effective_day` per thread, all as of `known_at` (the L5 discipline: events with `recorded_at <= known_at`).
- **Join rule** (`B/estate/portfolio.py` `_action_for` thread branch, `:144-150` on CH-2; the board's in-hand lookup):
  - An Action is "in hand" or current for a Finding only when they share the thread **and** the segment.
  - An Action from an earlier segment is listed under **Earlier**, with its verification result, never under In hand.
- **Test:** occurrences 1–3, then VERIFIED, then occurrence 4. Occurrence 4 shows RECURRED with no in-hand Action, and ACT-001 sits under Earlier.

## 4. Where it runs

- **`B/chain/lifecycle_run.py` `run_lifecycle(tenant, site, known_at=None)`.** It reads the causes for the Site's threads:
  - `action_event` for ACCEPTED/APPLIED/RESOLUTION_WITHDRAWN via `chain_action`;
  - `verification_outcome`;
  - domain actions raised;
  - case COMPLETED (the domain-action case link, plus the work-case completion: pre-flight P3);
  - SUPPORT_LOST (all occurrences' latest Finding revision `NO_LONGER_SUPPORTED`).

  It then appends the planned events through the CH-2 thread store, which is insert-only.
- **Backfill step (d).** `chain/backfill.py` registers step `d = run_lifecycle` for every Site, in `recorded_at` order. That replaces the "skipped" placeholder.
- **Tick.** If CH-1b is merged, `consume('lifecycle')` over `action.event@1` and `verification.outcome@1` triggers `run_lifecycle` for the Site. Otherwise, the `chain_threads` stage calls `run_lifecycle` after placing and linking. In both cases it also runs the time-based causes (INCONCLUSIVE_EXPIRED, CLEAN_DAYS) once per stage run. A cap hit defers; it never backs off the Site.

## 5. Row effect and copy (A5 read time; minimal edits to today's composition)

- **`B/outcomes/status.py` `Signal`** (`:45-53`).
  - `applied` today means "its exact-revision Action is APPLIED or later". It now comes from the thread: true when the Finding's thread state on day `d` is CHANGE_APPLIED or later **in the Finding's segment**.
  - When the thread state on `d` is RESOLVED_MONITORING or CLOSED, the Signal is built with `open=False`. A verified fix gives no Needs-attention signal (I-02).
  - `outcome_state` (`:55`) is unchanged otherwise. The KPI verdict still decides On track or Missed.
- **Board composition** (`B/site_outcomes/board.py`, `mini.py`, `cold.py`, `ev.py`). Build each Finding's Signal from the CH-2 lookup (`state`, `state_effective_day`, `segment_no`) **at the board's `known_at` and day**. Four copy lines, as literals:

| Case | Line (row `subline` or issue text; no system words) |
|---|---|
| Board day d < effective day e of the change (I-12) | `"Before the change on {e:%-d %b}"`. Then, from the first COMPLETE day ≥ e: `" · after the change: {state_label} from {day:%-d %b}"`. With no such day: `" · after the change: not judged yet, no fully checked day since {e:%-d %b}"`. |
| RESOLVED_MONITORING on d | `"Fix verified, monitoring ({code}) · {k} more fully checked days to close"` |
| CLOSED on d | `"Fix verified and closed ({code}) · no return in {n} fully checked days"` |
| RECURRED on d | `"Came back on {day:%-d %b} after the fix ({code})"` |

  - `{code}` uses `display_code`, as at `tools/demo_combined_finish.py:25`.
  - Each line is shown only when it applies. Run the vocabulary guard (V) on them.
  - These are new board lines, so the packet lists them as MOCK DEVIATION candidates against MA-1 M4.
- **Verified claim scope (I-11).** `trial_line` (`board.py:402-414`) appends the scope of what was verified: `" · checked over {start:%H:%M}–{end:%H:%M} on {day:%-d %b}"`, using the verification plan's later window. Pre-flight P2 names it. The verdict and the rule are unchanged.
- **Money (OD-3 / AG-24).** A thread or Action is credited money only when `cost_check.state == "MODELLED_IMPROVEMENT"` with a **priced positive** amount **and** the outcome is VERIFIED.
  - Otherwise the line reads `"modelled, not saved"`, which is the existing `COST_NO_CHANGE` / `COST_NOT_CREDITED` family (`board.py:387-399`). Confirm that the wording matches, and add only the missing literal.
  - The Portfolio's recovered value (I-24, `B/estate/portfolio.py:345,610`) is the sum of credited amounts per currency, or `"No money credited · modelled, not saved"`.
- **Portfolio progress (I-24).**
  - `verified_resolution_count` = threads in RESOLVED_MONITORING or CLOSED in the window.
  - `priority_site_count` = Sites with at least one thread in OPEN, RECURRED or REOPENED in the window (no longer `null`). The thread state is taken at the window's `known_at`.
  - The additive Portfolio and board `thread` objects (CH-2 §5.3) gain `state`, `state_effective_day` and `segment_no`.

## 6. Coherence rules (append to `tools/checks/chain_coherence.py`)

- **COH-13, lifecycle agreement.** For each Finding, `thread.state` and `state_effective_day` agree between the board (same day) and the Portfolio (the window containing the day).
- **COH-14, verified implies no attention.** A board row whose only open Finding Signal is on a RESOLVED_MONITORING or CLOSED thread is not NEEDS_ATTENTION for that reason.
- **COH-15, segment.** No board or Portfolio shows an Action as in hand for a Finding in a later segment.
- Update `expected-today.json`: the I-01, I-02 and I-12 expectations resolve; I-09 stays with DD-1.

## 7. DS-R1 and OL-1

| Item | Touched how | Resolution |
|---|---|---|
| 4. "ACT-001 verified on one hour" | The verified line | **Fixed in wording** (I-11 scope line). The rule is unchanged. |
| 4. "Verified on example data" (`board.py:50`, `mini.py:85,89`) | Not edited (another line) | Labelled keep → CH-5a |
| 3. The exact-revision `applied` rule (`status.py:51`, Kobo-shaped refresh chain) | Replaced | **Fixed.** Uses thread and segment state. |
| Close-after-N and expiry numbers | Declared config | OD-2 values, not fitted to the data |

**OL-1:** `status.py` keeps reading which outcomes a Finding moves only from `outcome_map` (`finding_signal_key`). The lifecycle adds no outcome ids.

## 8. Localised test ladder

1. **L0:** `tools\run-host-tests.ps1 -- backend/tests/test_ch3_lifecycle.py backend/tests/test_ch3_rows.py`
   - Every transition, plus illegal transitions skipped.
   - Effective days in Addis and UTC.
   - INCONCLUSIVE expiry.
   - CLEAN_DAYS with PARTIAL days not counted.
   - Segments, with the occurrence-4 case.
   - `Signal` from the thread state.
   - The four copy lines.
   - The money rule for each `cost_check` state.
   - Portfolio counts.
2. **L2:** `tools\run-host-tests.ps1 -- backend/tests/test_ch3_lifecycle_postgres.py`
   - The s6 harness Action: accept, apply, verify (`test_s6_action_store_postgres.py:119-131`, `test_s6_verification_evaluator_postgres.py`), all on the CH-2 L2 set-up. Expect OPEN, then ACTION_IN_HAND, then CHANGE_APPLIED, then RESOLVED_MONITORING.
   - Rerunning `run_lifecycle` writes 0 rows.
   - A domain action raised gives ACTION_IN_HAND.
   - The SUPPORT_LOST guard holds when an Action exists.
3. **Existing, scoped:**
   - `test_s6_verification_*.py`, `test_s6_action_store_postgres.py`;
   - `test_out_b1_board.py`, `test_out_b4_board_postgres.py`, `test_out_c2_board.py`, `test_out_d4_board.py`, `test_polish_pa1_board_truth.py`;
   - `test_w303_portfolio_*.py`;
   - `test_ch2_*.py`;
   - every importer of `outcomes.status`, `site_outcomes.board` or `chain.lookup` (list them).
   - Expected board-text changes are listed in the packet with old → new. Anything else that changes is a regression.
4. **L4:** `python -m assetops_backend.chain.backfill --dry-run --steps b,c,d` on `assetops_polish_full_test` prints:
   - Kobo generator: RESOLVED_MONITORING, effective 2026-11-01;
   - Cold start failure: ACTION_IN_HAND;
   - Cold excursion: OPEN;
   - EV interruption: ACTION_IN_HAND;
   - Kobo headroom: OPEN.
   - The effective days for Cold and EV are after the story window (build-time Actions; DD-1).
5. **L3:** clone, migrate, backfill (b, c, d), then `chain_coherence.py collect` and `check`.
   - COH-13 to COH-15 pass, and I-01, I-02 and I-12 resolve.
   - Report the 31 Oct and 1 Nov Kobo cost rows verbatim. Expected: 31 Oct is Needs attention + "Before the change on 1 Nov · after the change: not judged yet, no fully checked day since 1 Nov" (PARTIAL days until DD-1). 1 Nov is not Needs attention for the generator Finding + "Fix verified, monitoring (ACT-001) · 7 more fully checked days to close".
   - Drop the clone.
6. **Frontend:** `npx vitest related --run src/estate/estateClient.ts src/sites/outcomeBoardClient.ts` (type additions only).
7. **Guards:** A, W, V (copy), the chain-coherence fixtures line. The estate guard self-tests run only if `configuration-persistence.ps1` is edited, which no new writer should need.

## 9. Pre-flight items (answer from code, batch them, then stop)

- **P1:** the CH-2 thread store's append API, and whether it allows appending a non-OCCURRENCE event.
- **P2:** the verification plan fields for `later_end` and the later window (`B/actions/verification_rules.py`, the 0019 tables).
- **P3:** the domain-action case-completion source (`domain_action_case_link` plus the work-case completion revision or event).
- **P4:** every place that builds a FINDING `Signal` with `applied=` (`B/site_outcomes/*`), to swap in the thread state.
- **P5:** the existing "not saved" literals in `board.py` (`COST_*`). Reuse them; do not duplicate.

## 10. Review focus

- Thread state alone decides "applied" and "verified, monitoring". The verification rules and cost model are untouched.
- Segments prevent an old Action from reading as current after a recurrence.
- The money rule follows OD-3 exactly.
- Every new line comes from the four literals and passes V.
- No outcome wiring is added (OL-1).
