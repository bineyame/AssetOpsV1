## D-SR.83b The stored Overview carries schedule facts, not schedule clocks, and keys on them live (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review; supersedes the boundary half of D-SR.83a)

- Blocker (WIP `8375912a1`): the Overview reads `schedule_tick_head` and `schedule_site_head`. Neither table moves the watermark, and the body echoes their clocks (`freshness.schedule.heartbeat_at`, `*_age_seconds`, `site_last_completed_at`). The walkthrough serve ticks every 120 s (`demo_combined.py` serve loop), so a stored body would show stale schedule data.
- **Rejected options.**
  - (ii) Triggers on the heads: the tick head has no tenant, so every tick (120 s) would move every tenant's watermark and invalidate the whole store, including the board and Portfolio. It is also a migration on the walk DB.
  - (iii) A query fix: there is no measured breakdown, and it touches the selection and source fences.
  - Splitting the body into live and stored parts: eligibility feeds `_money` and the per-Finding `upstream_status`, so a split re-implements the read.
- **Ruling: (iv), a live schedule term in the stored route's watermark, with the body cut down to the schedule facts that decide its output.** This is the same pattern as the file-state term `F` (CH-5c2).
  1. `scheduling/health.py` (pure): add `schedule_facts(tick, head, now, th) -> dict`, returning `{"stopped": env["state"] == "STOPPED", "site_observation_codes": sorted(codes of site_observation), "errors": [the head error tuple that upstream.py:183-185 builds, or empty]}`. These are exactly the inputs to the SCHEDULE blockers and errors. RUNNING/IDLE, ages and timestamps are left out because they change every tick and decide nothing.
  2. `scheduling/upstream.py`: keep D-SR.83a's `read_instant` at :100. Remove `_register_schedule_flips`: the live term below detects every flip at lookup, and boundaries at heartbeat + 300 s would expire every row about every 5 min. Add `"schedule_facts": schedule_facts(...)` to the `window` return. The existing `schedule` key stays for `scheduling/run.py`. Add `schedule_term(t, s, environment) -> str`: read `tick_head` and `site_head`, take `now = read_scope.read_instant(db_now)`, and return the sha256 of the canonical JSON of `schedule_facts(...)`.
  3. `chain/response_store.py`: `StoredRoute` gains `term: Callable[[], str] | None = None`. In `_state`, after `F`, add `if req.term is not None: w = f"{w}|s:{req.term()}"`. Both (a) and (c) then include it, so a flip during the compose is a `race` and is never stored.
  4. `site_overview/read.py` body:
     - `freshness.schedule` = `up["schedule_facts"]` plus `"environment"`.
     - `freshness.consequence_work[*]` keeps every field except `age_seconds`, which becomes `enqueued_at` (stable). The upstream row already has `enqueued_at`, so add it there and drop `age_seconds` in the overview's projection only.
     - No frontend reads either field (checked `siteOverviewClient.ts`, `SiteWindowOverview.tsx`), so there is no mock impact. Update `test_s5_overview_read.py` and `test_s5_overview_postgres.py` expectations.
  5. `site_overview/route.py`: pass `term=lambda: self.read.upstream.schedule_term(tenant_id, site_id, self.read.environment)` into the `StoredRoute`.
- **c4 mask.** Add only `db_now` and `built_at` to `WALL` in `tools/chain_response_probe.py:30`. Both are exactly the compose's read instant, the same class as the board's `known_at`. This narrows D-SR.83a's "never mask" to "never mask a derived value". No age or state is masked.
- **f4.** Add `finding_index_api`, `scheduling.health`, `scheduling.upstream`, `site_overview.money_state`, `site_overview.read` and `site_overview.route` to `config/chain/stored-composer-modules-v1.json`. Add the three routes to the planted-read expected set (`test_ch5c2...:263`). For the table audit, add `"route_terms": {"/api/sites/{site_id}/overview": ["schedule_tick_head", "schedule_site_head"]}` to `config/chain/watermark-inputs-v1.json`. The audit accepts those two tables on that route only, and tracks no new table. If the table guard cannot express a per-route exemption in under about 15 lines, stop and ask.
- **Finding index and estate scope:** neither reads the schedule heads (their read time already goes through `read_instant`). Land them first as their own commit with c4 and f4 green. If either shows a body difference other than the module list, stop and ask.
- **New tests.**
  - `response_store`: a `term` change between (a) and (c) gives `race`, and a changed term at lookup misses.
  - `upstream`: `schedule_facts` is unchanged across a healthy tick (new heartbeat, RUNNING to IDLE), and changes on STOPPED and on `SITE_VISIT_STALE`.
  - Overview route: the second GET is `stored`, and after the planted heartbeat goes stale it is a miss whose body reads `SCHEDULE_STOPPED`.
- **Result.** The serve's 120 s ticks leave the term and the watermark unchanged, so the prebuilt Overviews stay hits (about 0.1–0.3 s). Only a real schedule state change recomposes. No migration and no DB rebuild. The merge gate and walk1113 steps are as in D-SR.83.

Decisions logged for owner review: **D-SR.83b**.
