# WK-SC: the story clock (implementer spec)

**3.0 u in three units, one part, branch `task/WK-SC-story-clock`, one discovery review** (a protected seam: the
clocks of person acts; a guard that must never reach a real tenant). Architect (Claude, DD lane), 23 Nov 2026.
Rulings: D-DD.135, D-DD.137 (narrowed by D-DD.172), D-DD.172, D-DD.173 (`rulings.md`). Owner: O1 "Build story clock
(Recommended)", O2 "Executive acts (Recommended)" (`owner/owner-dd-strategy-2026-11-22.md`). Build card:
`cards/WK-SC.md`. `USER_REVIEW_REQUIRED: true` (it changes what the served demo says "today" is).

## A. For the owner (one paragraph)

The demo world's readings stop at 6 Nov 06:00, and its ten decisions and nine agreed actions are dated 6-30 Nov.
Against the real calendar the product refuses seven of the nine due dates (they are in the past) and the date
presets ("Last month", "Last 7 days") point at weeks with no data. The story clock makes the demo world's
**operating calendar** start at 6 Nov 06:00 and run forward from there. The executive (Amina, Esther, Daniel) agrees
the actions and chooses the options; the site manager is kept as the proposer in the demo manifest (the product has
no proposer field, so it is not on screen). **The system's own timestamps stay true**: when a reading was received or
a record stored is the real time it happened. The clock exists only in demo and test databases and refuses to start
anywhere else.

## 0. Existing, then new

| Existing (main) | New |
|---|---|
| `prepare_clock.require_prepare_database(url)`: the one check that a story clock runs only on `assetops_polish_*` or `*_test` (DD1b1-R Q6); DD3d-a widens it to the world rung names and refuses operator names (D-DD.168) | `prepare_clock.story_now()` and `story_clock()` read `ASSETOPS_STORY_NOW` only after that check |
| `tools/demo_story_clock.py`: process-local story clocks for the old demo prepare | reused pattern, not reused code (that module dates per received day) |
| Each service takes an injected `clock` (agreed actions, decisions, evaluation, verification); production composition passes the wall clock | world-time compositions pass `story_clock()` where it is set; system-time compositions are unchanged |
| `decisions/run.py` uses one `now` for `known_at` (system) and `run_at` (act) | two reads: `known_at` = wall, `run_at` = story |
| `agreed.py` judges the due date and OVERDUE against the act clock's UTC date | against the story date when set |
| `walk_world.py prepare` records statements and snapshots; `demo_workflow` items listed pending (DD6, D-DD.135) | `prepare.workflow:*` steps create 10 decisions, 9 Actions, 7 choices under per-step story instants |
| `walk_world.py serve` builds the API env (`api_env`) | adds `ASSETOPS_STORY_NOW` = the serve anchor (§3.3) |
| `frontend/src/ui/sharedRange.ts` presets default `now = Date.now()` | `now = appNow()`, from `GET /api/clock` |

## 1. Structure: two clocks (D-DD.172)

A clock read is classed by what it is compared with or stamped beside.

| Class | What it is | Sites (main, 87067a97f) | Source |
|---|---|---|---|
| **World time** | when something happened in the operator's world; the operator's calendar | `agreed_action.created_at` and the due check and OVERDUE state (`actions/agreed.py` `record` step 8, `state_code`, `for_tenant`); `decision.prepared_at`, `option_one_off.declared_at`, the 6h option-record act time (migration 0073; name it in pre-flight), `option_evaluation_run.run_at`, `decision_choice.chosen_at` (`decisions/records.py`, `decisions/run.py`); the verification `today` (`actions/verification_families.py` `assess_plan(..., today)`, passed by `actions/verification.py`); the deep-dive read's action states (`deep_dive/read.py`: its `now` is used for the agreed list's `today` only; confirm in pre-flight); the screen calendar (range presets) | story clock when set, else wall |
| **System time** | when the system received, stored or knew something | `received_at` (ingestion `system_clock`), `recorded_at`/`command_now` (work store), every `known_at` of a read or run (incl. `option_evaluation_run.known_at`, `structure/observe/service.py`, attribution), leases, cursors, schedulers, source health (compares `received_at`), the gateway clock | wall, always |

Rule for any site not listed: compared with or stored beside a system instant → system time. Compared with an
operating-world date or instant (due, occurred day, a person's act) → world time. The builder sweeps every
`clock`/`now`/`utc_now`/`datetime.now`/`Date.now()` read under `backend/assetops_backend/` and `frontend/src/`
(about 66 backend files) and lists each in the packet as W or S, with a one-line reason. A W site not in the table
above stops for the Architect: it is a scope change. An S site needs no change.

Why not one clock: world rows are loaded at wall time, so a read with `known_at` = 6 Nov would see none of them, and
`decisions/run.py` reads its inputs with `known_at` = now. Why act times are world time: migration 0070 checks
`due_on >= created_at::date`, so an Action due 9 Nov cannot be created at a 23 Nov act time. In the story, the
executive agreed it on 6 Nov.

Honesty: a run row may carry `known_at` (system, e.g. 25 Nov) later than its `run_at` (world, 6 Nov). That is true:
the world's data reached the system after the story date. It happens only in demo and test databases.

## 2. Data and the clock API (`backend/assetops_backend/prepare_clock.py`)

```python
STORY_NOW_ENV = "ASSETOPS_STORY_NOW"

class PrepareClockRefused(RuntimeError): code = "PREPARE_CLOCK_REFUSED"   # existing

def story_anchor(environ: Mapping[str, str] | None = None) -> datetime | None:
    """None when unset. Set: require_prepare_database(environ["DATABASE_URL"]) first; then the value must be an ISO
    instant with an offset and whole seconds (e.g. 2026-11-06T06:00:00+03:00), and not later than the wall clock.
    Anything else raises PrepareClockRefused with one of the codes below."""

def story_clock(environ=None) -> Callable[[], datetime] | None:
    """None when unset. Else a running clock: anchor + (monotonic now - monotonic at the first call of this clock),
    truncated to whole seconds, tz UTC. One instance per process (module-level cache keyed by the anchor)."""

def world_clock(fallback: Callable[[], datetime], environ=None) -> Callable[[], datetime]:
    """story_clock() if set, else `fallback` (the composition's existing wall clock)."""
```

Refusal codes (message after the code, stderr; CLI exit 2; serve exits non-zero before binding the port):
`PREPARE_CLOCK_REFUSED` (database outside the check, existing), `STORY_CLOCK_INVALID` (not an aware whole-second ISO
instant), `STORY_CLOCK_FUTURE` (later than the wall clock). `ASSETOPS_STORY_NOW` is read nowhere else (a static test,
§5).

## 3. Wiring

### 3.1 Backend compositions (unit 1)

- `actions/composition.build_agreed_actions(url, clock=...)`: default `clock = world_clock(_now)`. `AgreedActionService`
  is unchanged: its one clock is the act clock, and its `today` is that clock's UTC date, which is world time.
- `decisions/composition.build_decisions` and `build_evaluation`: default `clock = world_clock(_now)` for act times.
  `EvaluationService` (`decisions/run.py`) gains `knowledge_clock: Callable[[], datetime] = _wall` (the existing wall
  `_now`): `known_at = _now(self._knowledge_clock)` feeds `site_inputs(...)` and the run's `known_at`;
  `run_at = _now(self._clock)`. With no story clock both are wall, as today (a test pins equality).
- Verification: `actions/composition.build_verification...` passes `today` = the Site-local date of
  `world_clock(utc_now)()` to `evaluate_site_domain_plans` (the existing `today` parameter); `now`/`known_at` stays
  `utc_now`.
- `main.create_app`: calls `prepare_clock.story_anchor()` once at start (fails fast), and wires the deep-dive read's
  clock (`deep_dive/read.py`) through `world_clock(...)` only for its agreed-list `today`. If that read uses its
  `now` as a `known_at` too, split it as in `run.py` and list it in the packet.
- `GET /api/clock` on `health_router` (no auth, no tenant data): `{"now": "<UTC ISO, Z, whole seconds>", "story":
  true|false}` from `world_clock(wall)`. Registered wherever the architecture guard's route list requires (name it
  in pre-flight).

### 3.2 The walkthrough's workflow (unit 2, `tools/walk_world.py`)

- Walk definition `/2` gains optional `"story": {"now": "2026-11-06T06:00:00+03:00"}`. `walk_definition()` requires
  it to equal the world definition's `telemetry.span.to` taken at the tenants' offset (+03:00; D-DD.103), or refuses
  `WALK_STORY_MISMATCH`. Absent: no story clock, and the workflow steps are skipped and recorded `{"step",
  "skipped": true, "reason": "no story"}`.
- `cmd_prepare`, after the snapshots: `plan += workflow_plan(m, wd, M)`. Each step runs one product CLI under
  `walk.step_env(tenant, ...)` plus `ASSETOPS_STORY_NOW = story.now + k seconds` (k = the step's ordinal in the
  workflow plan, from 0). Each step therefore has its own world instant, and the rows order as `M` orders them.
- The plan, per tenant in definition order (`lakeside-power`, `harvest-cold`, `metro-bus`):
  1. For each 6h §7 row of the tenant (`specs/6h-named-option-levers/spec.md` lines 348-358): `prepare_decision
     --tenant --as <analyst> --site <code> --lever <id> --period <P> --horizon <N> [--finding <uuid>] [--current
     ...]`. The analyst is `M`'s `ANALYST` person of the tenant. Email by DD1's rule. `--finding` is the latest
     Finding of the named code at the Site in the walk database (one SQL read, the same connection walk_world already
     uses). None found: the step is recorded pending `FINDING_NOT_FOUND` and the row's later steps are skipped.
     Kobo's `--current` is Kobo's declared stop/reserve settings (read from the Foundation by the builder; name the
     source in pre-flight).
  2. Per option record and one-off of the row: `state_option_record --emulated` and `state_one_off` as the Site's
     `SITE_MANAGER` in `M`. Values are read from `M` by option id (6h §7: "never retyped").
  3. `evaluate_options --as <analyst> --decision <id>`.
  4. For each of `M`'s `demo_workflow.actions` of the tenant: `record_action --tenant --as <executive> --title <M
     action> --owner <M owner email> --due <M due> --site <item's Site code>`.
  5. For each of D-DD.173's seven items: `choose_option --as <executive> --decision <its decision> --option <key>
     [--action <its one Action>]`.
- Each step's exit and JSON line go to the walk manifest's `workflow` list, `{"step", "item", "rc", "out" |
  "refused": "<CODE>"}`. A refusal (exit 2) does not stop prepare. The item is listed pending with its code, and
  nothing is retried or tuned. Exit 3 (store) stops prepare as today.
- `M` (`Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml`) `demo_workflow`: each item's
  `chosen_by` and each Action's `created_by` become the tenant's `OPERATOR_EXECUTIVE`. The former value moves to a new
  key `proposed_by`. `check_manifest.py` `workflow()` checks OD-16 as `owner == proposed_by` for items (and
  `created_by` is the executive for every Action). One `M` commit, rev bump.
- Which commands an item maps to is the table in D-DD.173. `M` stays the source of every name, title, due date and
  value. The table maps only item → (Site, lever, option key).

### 3.3 Serve (unit 2)

- `cmd_serve` adds `ASSETOPS_STORY_NOW` to `api_env` when the walk definition has `story`. The anchor is the later
  of `story.now + 60 s` and the latest world-time act in the walk database + 1 s (one SQL `max()` over the act
  columns of §1, listed as `STORY_ACT_COLUMNS` in `prepare_clock.py`). A restarted serve then never runs earlier
  than a row a previous serve wrote. The walk manifest records `serve.story_anchor`.
- The web process gets no variable: the screen reads `/api/clock`.

### 3.4 The screen's calendar (unit 3, `frontend/src/`)

- `ui/clock.ts` (new): `initAppClock(fetcher): Promise<void>` calls `GET /api/clock` once and keeps `offsetMs =
  Date.parse(now) - Date.now()`, or 0 on any failure (the wall clock). `appNow(): number = Date.now() + offsetMs`.
  `isStoryClock(): boolean`.
- `main.tsx` awaits `initAppClock` before the first render (one request, bounded by a 2 s timeout; on timeout offset
  0).
- Every `now: number = Date.now()` default in `ui/sharedRange.ts` (`presetRange`, `presetOf`, `readSharedRange`,
  `readWindow`, `pageDay`, `addressRange`, `entryRange`) becomes `now: number = appNow()`. The other 12 files that
  read `Date.now()`/`new Date()` are classed W or S by §1's rule. Calendar uses become `appNow()`; timing, retry,
  idempotency and cache uses stay. List them in the packet.
- No new element, word or style. No mock element changes: `frontend/mockups/v70/` shows no clock (no MOCK DEVIATION).
  W3 default, owner may weigh in: no "as of" marker is added; the range control's dates already show the period.

## 4. Guards: the clock never reaches a real tenant

1. **One reader, one check.** `ASSETOPS_STORY_NOW` is read only by `prepare_clock.story_anchor`, which calls
   `require_prepare_database(DATABASE_URL)` first. That check admits only `assetops_polish_*`, `*_test` and the world
   rung names, and refuses `assetops_op*` (operator) names before any pattern (D-DD.168).
2. **Fail closed.** Set and refused: the serve does not start and a CLI exits 2. The variable is never silently
   ignored.
3. **No future.** An anchor later than the wall clock is refused (`STORY_CLOCK_FUTURE`).
4. **Never inherited.** `walk_world.api_env` and `step_env` are built, not inherited (D-WK.5). The variable is set
   only when the walk definition has `story`. `tools/world.py` never sets it.
5. **Static tests.** The string `ASSETOPS_STORY_NOW` appears only in `prepare_clock.py`, `tools/walk_world.py`, tests
   and specs. It does not appear in `host/`, `gateway/`, `deploy/`, any `docker-compose*`, `.env*` or systemd unit.
   `story_clock`/`world_clock` are imported only by the compositions of §3.1 and `main.py`. No system-time module
   (the work store, ingestion, schedulers, source health) imports them.
6. **Protected.** Ports 5490/8990/8992, the owner's walk (`assetops_polish_walk1113_test`, `PROTECTED_DATABASES`)
   and the development database are untouched. The development database fails the check by name.

## 5. Tests (each can fail)

- `backend/tests/test_wksc_story_clock.py` (pure): unset gives None and `world_clock` returns the fallback. Set with
  `DATABASE_URL` on `assetops_polish_walk2001_test` gives an anchored running clock (two reads, whole seconds,
  monotonic). Each refusal: dev database `assetops`, operator name `assetops_op_lake_test`, naive value, fractional
  seconds, a value one minute after the wall clock.
- `backend/tests/test_wksc_static_guard.py`: §4.5 as greps over the tree.
- `backend/tests/test_wksc_agreed_postgres.py` (harness `*_test`): under a story clock at 2026-11-06T06:00+03:00 an
  Action due 2026-11-09 records, state Open; due 2026-11-06 records; `created_at` = the story instant. With no clock
  the same due date refuses (existing code). At story 2026-11-10 the first reads Overdue.
- `backend/tests/test_wksc_decisions_postgres.py`: under a story clock, an evaluate run's `run_at` = story,
  `known_at` = wall. Rows recorded after the story instant are in its inputs (the run sees a reading loaded at wall
  time). With no clock `run_at == known_at`.
- Verification: `today` under a story clock is the story's Site-local date (a plan effective 2026-11-09 shows its
  later window open on 6 Nov, not closed).
- `test_wk_walk_world.py`: `/2` with `story` read and the mismatch refusal. `workflow_plan` order and per-step
  instants (k seconds). A refused choice recorded and prepare continuing. The serve anchor = max(story + 60 s, latest
  act + 1 s). No `story` gives skipped workflow steps and no variable in `api_env`.
- `simulator/tests/world` or `check_manifest.py`: `workflow()` with `proposed_by`.
- Frontend (vitest via `tools/heavy-slot.sh`): `presetRange("lastmonth", appNow())` with an offset putting now at
  2026-11-06T06:00+03:00 gives 1-31 Oct 2026. A failed `/api/clock` gives offset 0.

## 6. Plants (introduce, see the named test fail, revert)

(a) Skip `require_prepare_database` in `story_anchor`: the operator-name and dev-database refusal tests fail.
(b) Wire the story clock into `known_at` in `run.py`: the decisions test fails (the run sees no loaded reading).
(c) Set `ASSETOPS_STORY_NOW` in `tools/world.py`'s env: the static guard fails. (d) Drop the `+ k` step offset: the
order test fails.

## 7. Gates (done when, questions)

1. On a walk copy prepared from the DD6 world with `story`, does `prepare` record 10 decisions, 9 Actions and up to
   7 choices, each with exit 0 or a listed refusal code, and a re-run record nothing new (`already_*` true)?
2. Does the served API answer `/api/clock` with `story: true` and a `now` on 6 Nov, and does the Portfolio open on
   "Last month" = October 2026?
3. Does every Action due 6-30 Nov read Open (none Overdue) on the story date?
4. Does every guard test pass, and does each plant fail?
5. Are C-DD9's Decisions, Actions and Results cells still PENDING only with "IA-P lane" (the pages read the estate
   portfolio until 6f1/IA-P), with "WK-SC" gone from their closing units?

## 8. Scope limits

- No plan, version or release states (M's `plan_state`, `AWAITS_APPROVAL`): later units (6f2).
- No proposer on screen (no product field; owner told).
- No change to readings, books, the world build (L0-L2) or any system-time site.
- BAT-EVIDENCE and MTO-INV-CLAIM decisions are not made (MD-6H-3). KIS-SERVICE has no Action on 6 Nov.

## 9. Units

| Unit | Content | Size |
|---|---|---|
| WK-SC.1 | clock API, guards, §3.1 wiring, `/api/clock`, the sweep table, tests §5 (pure, static, agreed, decisions, verification) | 1.25 |
| WK-SC.2 | walk `/2` `story`, the workflow plan (6h §7's ten decisions, nine Actions, seven choices), `M` `proposed_by` and `workflow()`, serve anchor, walk tests | 1.25 |
| WK-SC.3 | `ui/clock.ts`, `main.tsx`, `sharedRange.ts` defaults, frontend sweep, vitest | 0.5 |

Order: after DD6 is on main (walk `/2`, `prepare`, `serve`) and DD3d-a (the widened check). Independent of 6f1.
