# Build sheet CH-1b: event register, outbox, dirty queue and drain

- Architect: Claude, 2026-11-03.
- Plan: `Docs/demo-sprint/client-demo-plan.html` (agreed). Lane 1 (3 units).
- Design: `Docs/demo-sprint/implementation-logic-design-proposal.html`:
  - AG-1 and AG-7;
  - §4.3 `event_outbox` and `snapshot_dirty`;
  - §5.2 A0 (the register and `consume`) and A1;
  - §6 S1;
  - §11b (budgets and the measured diagnosis).
- Branch: `task/CH-1b-events`, cut from main **after CH-2 merges**. It rewires CH-2's `chain_threads` stage.
- Paths: `B/` = `backend/assetops_backend/`, `M/` = `backend/migrations/versions/`. Lines are to main at `75637eb56`, plus CH-2 at `6185d261d` where named.

## 0. Result and boundary

**Observable result.** A new fact (a reading, a selection, a price, a foundation revision, a Finding or OPP revision, an Action event) writes an outbox event in the same transaction. The tick consumes the events, marks the affected Site-local days and measures dirty, and rebuilds only those snapshots. On the L3 clone, publishing a new productive price through the product's own CLI re-revisions exactly the priced days, with the new money (ST-7 path, WN-5, I-25).

**Not in this slice.**
- The lifecycle consumer (CH-3). CH-1b emits `action.event@1` and `verification.outcome@1`, and only the thread consumer reads them here.
- No broker, relay or schema registry (AG-7).
- No outbox pruning (scale path S1).
- No change to matchers, money or verification rules (High).

**Carried items folded in:**

| Carried from | Item |
|---|---|
| CH-2 L6 | The thread stage scans incrementally, and a cap hit defers instead of backing off the whole Site. |
| CH-1a L2 | Asset-subject measures on NOT_EXPECTED days. |
| CH-1a L3 | Per-subject chamber and backup values. |
| CH-1a L6 | The CLI prints the stored revision on a skip. |
| CH-1a residuals | `_WINDOWS` ignores `selected_at`; `pending_jobs` ignores `known_at`. |
| CH-1a review M1 | The drain must work with the fingerprint (pending flag plus run ids). |

## 1. Migration `M/0044_chain_events.py`

- `revision = "0044_chain_events"`.
- `down_revision` is the main head at branch time: `"0042_chain_threads"` once CH-2 has merged (CH-2 re-points 0042 onto 0043).
- Head pins are not edited: tests use `pg_harness.alembic_head()`.

```sql
CREATE TABLE event_outbox (                          -- AG-7, broker-ready envelope
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type text NOT NULL CHECK (type ~ '^[a-z]+\.[a-z_]+$'),          -- 'reading.accepted'
  schema_version int NOT NULL CHECK (schema_version >= 1),
  occurred_at timestamptz NOT NULL,                  -- the fact's story time (span start / valid_from / created_at)
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  source text NOT NULL,                              -- '<table>'
  tenant_id uuid NOT NULL, site_id uuid NULL,
  subject jsonb NOT NULL,                            -- see §2 per type
  idempotency_key text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT event_outbox_idem UNIQUE (source, idempotency_key));
CREATE INDEX event_outbox_site_order ON event_outbox (site_id, recorded_at, event_id);
CREATE TRIGGER event_outbox_immutable BEFORE UPDATE OR DELETE ON event_outbox
  FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE TABLE event_consumption (                     -- processed(consumer, event_id), append-only
  consumer text NOT NULL CHECK (consumer IN ('snapshots','threads','lifecycle')),
  event_id uuid NOT NULL REFERENCES event_outbox (event_id),
  processed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (consumer, event_id));
CREATE TRIGGER event_consumption_immutable BEFORE UPDATE OR DELETE ON event_consumption
  FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE TABLE snapshot_dirty (                        -- the rebuild queue (mutable queue, like recompute_job)
  tenant_id uuid NOT NULL, site_id uuid NOT NULL, local_day date NOT NULL, measure text NOT NULL,
  first_event_id uuid NOT NULL REFERENCES event_outbox (event_id),
  marked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (tenant_id, site_id, local_day, measure),
  FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id));
```

**Producers: AFTER INSERT triggers, written in the same transaction as the fact (design A0).**
- No Python writer changes. This follows the existing precedent `enqueue_mini_depth` (`M/0029:305`).
- Each trigger is **statement-level** with a transition table (`REFERENCING NEW TABLE AS n FOR EACH STATEMENT`). It writes **one** event per (site, statement, type), aggregating the spans, so a batch of readings costs one row.
- Each `idempotency_key` is a deterministic text built from the source ids (for example `min(id)|max(id)|count`).

| Source table (trigger) | Event type | `subject` |
|---|---|---|
| `accepted_evidence` | `reading.accepted@1` | `{"roles": [...], "asset_ids": [...], "span": [min(start), max(end)]}` |
| `analytic_run_selection` | `assessment.revised@1` | `{"analytic_ids": [...], "windows": [[s, e], ...]}` |
| `mini_depth_selection` | `assessment.revised@1` | `{"domain": "renewable", "windows": [...]}` |
| `recompute_job` (INSERT, plus UPDATE OF status; the one non-insert trigger) | `job.changed@1` | `{"domain": ..., "window": [s, e], "status": ...}`. This makes PENDING appear and clear. |
| `financial_assumption_revision` | `price.revised@1` | `{"key": ..., "valid": [from, to]}` |
| `foundation_revision` | `foundation.revised@1` | `{"valid_from": ...}` |
| `finding_revision`, `mini_opportunity_revision` | `finding.revised@1`, `opportunity.revised@1` | `{"ids": [...]}` |
| `action_event`, `verification_outcome`, `domain_action` | `action.event@1`, `verification.outcome@1` | `{"ids": [...]}` |
| `outcome_objective_revision` | `objective.revised@1` | `{"ids": [...]}`. Days are `none`: windows are re-judged at read. |

**Downgrade.** It refuses when `event_outbox` has rows (`M/0030:240-252` style). Otherwise it drops the triggers, then the tables.

**Pre-flight P1:** confirm each source table's tenant and site columns, and which of these sources CH-1a's adapters actually read. For example, cold and EV selections are in `analytic_run_selection` (analytic ids); confirm the analytic ids per domain.

## 2. Event register `config/chain/event-register-v1.yaml` (design A0; reviewed as code; read by `chain/adapters/file_chain_config.py`)

```yaml
register_version: 1
events:
  reading.accepted@1:    {days: span_local,   measures: by_role}
  assessment.revised@1:  {days: windows_local, measures: by_analytic}
  job.changed@1:         {days: window_local, measures: by_job_domain}
  price.revised@1:       {days: valid_local,  measures: by_assumption_key}
  foundation.revised@1:  {days: from_valid_local_to_today, measures: all_of_site}
  objective.revised@1:   {days: none}
  finding.revised@1:     {days: none, consumer: threads}
  opportunity.revised@1: {days: none, consumer: threads}
  action.event@1:        {days: none, consumer: [threads, lifecycle]}
  verification.outcome@1:{days: none, consumer: lifecycle}
inputs:                  # measure → what dirties it (mirrors chain/measures.py; CH-8 merges it into the catalogue)
  productive_kwh:     {roles: [feeder_demand], assumption_keys: [productive_use_price_per_kwh], foundation: true}
  avoidable_gen_min:  {analytics: [dispatch], job_domains: [dispatch]}
  noon_headroom_kw:   {mini_depth: [renewable], job_domains: [mini_renewable]}
  chamber_temp_c:     {roles: [chamber_temperature], analytics: [cold_chain], job_domains: [cold_chain]}
  backup_start_chain: {roles: [backup_start_event, <backup-chain roles, B/analytics/cold.py:39-55>], analytics: [cold_chain], job_domains: [cold_chain]}
  charging_kwh:       {analytics: [ev_charging], assumption_keys: [ev_gross_tariff_per_kwh], job_domains: [ev_charging]}
```

- **Resolution** happens in the consumer, never in SQL. Spans are converted to Site-local days through `site.timezone` and the calendar loader. A span covering several days marks each day.
- **Guard (pure, check-all line):** `tools/checks/test_event_register.py`. It checks that:
  - every `MeasureSpec` in `chain/measures.py` has an `inputs` entry;
  - every entry names existing measures, roles and assumption keys;
  - every event type has a fixture test.
- **OL-1:** the register names measures only, never outcomes.

## 3. Consumers and the drain (`B/chain/events.py`, `B/chain/drain.py`)

```python
consume(consumer, tenant_id, site_id, limit) -> ConsumeReport
    # SELECT events of this site with NOT EXISTS (event_consumption for this consumer), ORDER BY recorded_at, event_id,
    # LIMIT limit. 'snapshots': resolve → INSERT … ON CONFLICT (pk) DO UPDATE SET marked_at = clock_timestamp()
    # (re-marks during a build are not lost); then INSERT event_consumption. One transaction per event.
drain(tenant_id, site, limit, deadline) -> DrainReport
    # pop: SELECT … FROM snapshot_dirty WHERE site ORDER BY local_day, measure LIMIT limit
    # for each: builder.build(…, local_day, measure); then compare-and-delete:
    #   DELETE FROM snapshot_dirty WHERE pk = … AND marked_at = :marked_at_read   (a re-mark keeps the row)
    # stop at deadline: remaining rows stay queued → report {processed, deferred}; never a failure
```

- **Fingerprint (CH-1a M1).** The drain always calls `build`. Skipping is decided only by `input_fp`, which now includes the pending flag and the selected run or revision ids. So a job that completes, or a re-assessment, always re-revisions, and an unchanged day writes nothing.
  - Test: PENDING, then settled with the same evidence ids, gives revision 2.
  - Test: draining twice gives 0 writes the second time.
- **Tick** (`B/scheduling/tick.py` `_site`, `B/scheduling/stages.py`):
  - **`chain_threads`** (CH-2, `stages.py:194`) changes to: `consume('threads')` over `finding.revised`, `opportunity.revised` and `action.event`. It places or links only the ids in those events, which is incremental.
    - It no longer rescans all sources; that was CH-2 L6.
    - The full-scan `run_threads` stays for the backfill only.
  - **New stage `chain_snapshots`:** `consume('snapshots')`, then `drain`. It has a new bound, `TickLimits.chain_snapshot_seconds: float = 60`, and `chain_snapshot_items: int = 200`, validated like the others (`tick.py:78-97`). Add it to CH-0's perf-line limit map.
  - **Cap hit (L6), for both stages.** A deadline or item cap returns `{"code": "OK", "deferred": n}`. It **never** sets the Site's failure or back-off; only a real error does. Test this with a fake runner.
- **Backfill (CH-2 `chain/backfill.py`) step (a).** It builds directly with `build_range` (no outbox needed) and then records one `backfill.site@1` event per Site for replay provenance. Add `backfill.site@1` to the register with `days: none`.

## 4. CH-1a carried fixes (in `B/chain/`)

- **L2.** When a day has no expected period, `adapter.subjects(ctx)` resolves subjects at the Site-local day start (`postgres_chain_inputs.py:145-149`, `:175-177`). The builder then writes a NOT_EXPECTED row per subject, and `reader._counts` (`reader.py:63-65`) never substitutes NO_DATA for a day that has a NOT_EXPECTED row.
  - Test: a synthetic ASSET measure on a TUE-only calendar.
- **L3.** `ChamberTemperature.measure` and `BackupStartChain` filter readings and chains by `asset_id` = the subject, where the reading or chain carries one (`measure_impls.py:237-244`, `:261-279`). Readings with no asset id are Site-wide and are used only when the Site has exactly one subject of that kind; otherwise they count as NO_DATA for the subject.
  - Pre-flight P2: which readings carry `asset_id`.
- **L6.** On the skip path, the builder returns the row with `revision = latest[0]` (the stored revision), so the CLI prints the true revision (`builder.py:77-90`).
- **Residual 1.** `_WINDOWS` adds `AND sel.selected_at <= :k` (`postgres_chain_inputs.py:57-61`).
- **Residual 2.** `_JOBS`/`pending_jobs` honours `known_at`, as `_RENEWABLE_JOBS` does (`:63-75`, `:270-273`): `available_at <= :k`, and NOT EXISTS a later selection of the window visible at `:k`.
- Each fix has an L0 or L2 test.

## 5. DS-R1 and OL-1

| Item | Touched how | Resolution |
|---|---|---|
| 4. Live re-assessment shown only as "not checked yet until the next tick" (`tools/demo_combined.py` serve text) | The re-assessment path itself | **Fixed structurally.** A new day re-assesses through the outbox and drain. The serve text is not edited here (DD-1 owns the script). |
| 4. One-noon-hour solar period | The register maps `noon_headroom_kw` by `mini_renewable` | **Labelled keep → CH-9.** |
| Thresholds and limits | New `TickLimits` fields | These are declared defaults, not fitted to the data. The 60 s and 200 items are the CH-2 precedent. |

**OL-1:** no outcome ids appear in the register, the events or the drain.

## 6. Localised test ladder

1. **L0, pure:** `tools\run-host-tests.ps1 -- backend/tests/test_ch1b_register.py backend/tests/test_ch1b_drain.py`
   - Register resolution per event type, including spans across midnight local, Addis and UTC.
   - The register guard.
   - The drain's cap and defer reporting, with memory ports.
   - L6 revision printing.
2. **L2, Postgres:** `tools\run-host-tests.ps1 -- backend/tests/test_ch1b_outbox_postgres.py`
   - The 0044 catalogue.
   - A trigger writes in the same transaction: rollback leaves no event.
   - A statement-level batch gives one event.
   - The consumer is idempotent: the same event twice marks once.
   - A re-mark during a build survives compare-and-delete.
   - PENDING then settled gives revision 2.
   - Drain twice gives 0 writes.
   - The fixes for L2, L3, `_WINDOWS` and `pending_jobs`.
   - Seed with the CH-1a L2 set-up (MG-W402 and the stub reader), using `setup_cache`.
3. **Existing, scoped:**
   - `test_ch1a_*.py`, `test_ch2_*.py`, `test_ch0_tick_timing.py`;
   - `test_s4_schedule_tick_postgres.py -m "not slow"`;
   - every test file importing `chain.builder`, `chain.adapters.postgres_chain_inputs`, `scheduling.tick` or `scheduling.stages` (list them in the packet);
   - **every test of a source table that gains a trigger.** List them by table: the evidence ledger, analytic runs, mini depth, financial assumptions, foundation, finding store, mini decisions, action store, objectives. Triggers change insert timing, so these run scoped.
4. **L3:** `python tools/chain_clone.py create ch1b --migrate`, then:
   - run the backfill;
   - drain, expecting 0 writes;
   - with the product CLI `python -m assetops_backend.publish_assumption`, publish a new productive price valid from `2026-10-30`;
   - consume and drain;
   - expect new revisions **only** for `productive_kwh` days ≥ 30 Oct, with the new money, and none for any other measure;
   - report the drain time and its share of `chain_snapshot_seconds`;
   - `drop`.
5. **Guards:** A, W, the chain-coherence fixtures, the new register guard line, and the **estate guard self-tests** (this slice edits `configuration-persistence.ps1`: the new writer and readers).

## 7. Guard registration

- `$eventWriter`: `chain/adapters/postgres_event_store.py`, with tables `event_consumption` and `snapshot_dirty`.
  - Insert-only for `event_consumption`.
  - `snapshot_dirty` allows `INSERT … ON CONFLICT DO UPDATE` and the compare-and-delete `DELETE`. Its rule is declared like `recompute_job`'s mutable-queue rule (pre-flight P3: find that rule).
- `event_outbox` is written only by triggers. The guard must not expect a Python writer for it; the anti-vacuity check uses the migration.

## 8. Pre-flight items (answer from code, batch them, then stop)

- **P1:** the source tables' columns and analytic ids (§1).
- **P2:** which cold readings and chains carry `asset_id` (§4 L3).
- **P3:** how `configuration-persistence.ps1` declares a mutable queue table today (`recompute_job`), and whether trigger-only tables need an entry.
- **P4:** whether a statement-level trigger on `accepted_evidence` coexists with the constraint trigger `enqueue_mini_depth` (`M/0029:305`) without changing its deferral.
- **P5:** the cost of the triggers on the L2 ingestion fixtures. Report the insert-time delta. If it is above +20%, stop and ask.

## 9. Review focus

- Every fact source writes its event in the same transaction, and no Python writer is edited.
- A cap hit never backs off a Site.
- The fingerprint decides every skip.
- The carried fixes each have a test.
- There is no outcome wiring (OL-1).
