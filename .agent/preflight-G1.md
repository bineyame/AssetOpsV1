# Pre-flight G1 (`add-dates`) — questions for the Architect

Implementer (Claude), branch `task/OWN-G1-add-dates` from main `60858f6cc`. Read-only; no code written. Spec: build sheet
OWN-GAPS Rev 1 (R1.3, R1.5, §1, §4), with §2 (G2) and §3.2 (G3a) read as contracts (their code is not on main yet).

## Confirmed against the code (no question)

- `StoryDaysError(code, detail)` `tools/demo_story_days.py:59`; `plan_add_day` `:460`, `plan_add_runs` `:512`;
  `DUPLICATE_DAY` `:483`, `DAY_HAS_EVIDENCE` `:481`, `FULL_DAY_AFTER_TRIAL` `:491` (complement kinds only, so Kobo
  `normal` passes), `DAY_NOT_IN_PAST` `:502/:526`; `SITE_WEEKDAY = {"ev": 1}` `:46`, `weekday_offset` `:49`.
- `.busy` lock and its message `tools/demo_combined.py:739-743`; `Demo.tick()` `:623`; `db_now()` `:724`;
  `delivered_days` (Site-local) `:710`; `add-day` parser `:919-924` (the "no Kisiwa day kinds" comment `:920`).
- `finish check` = `tools/demo_combined_finish.py check <url> <work>` (`:1568`), run by `Demo.finish` `:597`;
  `finish.app_client(url, work)` `:1525` imports `lab_app.app` in process (so `ASSETOPS_OPERATIONAL_ENTRY=on` must be in
  `os.environ` before that import; I will set it in the child before the call, and run the child with `serve_env=True`).
- Kisiwa: zone `Africa/Dar_es_Salaam` (`demo_combined_kisiwa.py:194`), record literals `:201-203`, `story_registered`
  `:444`, `nights.day_document(soc, fuel)` (litres, floats) as used in `build` `:775`, `rp._publish_and_accept(path,
  run, epoch, received_at)` `host/tests/test_s6_verification_replay.py:195`, `_round_litre` used at `:497`;
  `kisiwa.json` `runs[-1].physics` holds `soc`/`fuel` as Fraction text (`run_guards` `:502-503`). Story nights =
  `story["kisiwa"]["runs"]` (10 runs from `S-9d 12:00Z`, so the last story night is S; `demo-kisiwa-story-v1.json`).
  Offsets 180/900/1140 min check out against a `d 12:00Z` run start (EAT = UTC+3). `kisiwa-days.json` does not exist yet.
- Timezones: Kobo and Cold `Africa/Addis_Ababa` (UTC+3), Kisiwa `Africa/Dar_es_Salaam` (UTC+3), **EV `Etc/UTC`**
  (`backend/tests/fixtures/w2/ev-lab-001.yaml:9`). S is a UTC midnight (`demo_combined.py:146-148`).
- EV Tuesday: `plan_add_day` moves any `day` back to the Tuesday on or before it (`weekday_offset`), so the G1 loop must
  only pass Tuesdays (it would otherwise hit `DUPLICATE_DAY` on the previous Tuesday). Compatible with §4.4.
- Tick report: `run.py` prints `report.as_json()` (`scheduling/run.py:92`) whose `sites[].stages[name].code` is
  readable (`tick.py:186-198`); Kisiwa is selected every tick (it has accepted evidence, `tick.py:14-16`).
- `STAGE_LIMIT_FIELDS` `scheduling/tick.py:272` (no `fuel_night` on main; G2 adds it).

## Questions (batched)

**Q1 (High) — Kisiwa's "yesterday" night is not finished until 15:00 local today.** §4.2 defaults `--to` to yesterday;
§4.5 refuses a night whose run end > DB now − 5 min (`DAY_NOT_IN_PAST`) and stops the command. Night d's run is
`[d 12:00Z, d+1 12:00Z)`, so yesterday's night ends **today 15:00 local** (+30 min for §4.5 step 6). R1.5 has the owner
run `add-dates` "at least 3 h before" a demo, i.e. normally in the morning: every morning run would stop on Kisiwa with
`DAY_NOT_IN_PAST` (Kobo ends 00:00 local, Cold 20:05 local, EV 09:00 UTC, so they are fine).
Proposed: for Kisiwa only, the default `--to` is the latest night whose run end + 5 min ≤ DB now (yesterday after
~15:05 local, else the day before); an explicit `--to` naming an unfinished Kisiwa night prints "KISIWA-001 {date}: the
night is not over yet (it ends {15:00 local})" under `left_empty`/skipped and is not a refusal. The other Sites keep
yesterday.

**Q2 (High) — §4.5 steps 6–8 run inside the child, but §4.4's tick runs in the parent after the child.** Step 7 needs
"the tick's `fuel_night` code `OK`", and step 6 says "the date-major tick (§4.4) then checks it". The child cannot
verify a tick that runs after it exits. Proposed: the child `add-day` does steps 1–6 (start state, log, run, readings
→ `PUBLISHED`, records, wait) and exits; the parent runs `Demo.tick()` (changed to also return the parsed tick
report); then a second child verb `demo_combined_kisiwa.py verify-day <url> <work> <json>` (the json carries the
tick's Kisiwa `fuel_night` stage) does steps 7–8 (`DONE` or `ADD_NIGHT_UNEXPECTED`). Resume (step 9) then covers a crash
between the two. Also: the parent ticks only on a date where at least one Site added something (an EV-Wednesday-only or
all-skipped date gets no tick).

**Q3 (High) — KIS-1 and KIS-9 fail on the first added Kisiwa night; the pre-authorised fix names only KIS-2/KIS-6.**
- KIS-1: `demo_combined_rows.py:1077` asserts `len(prices) == nights`, with `prices` one per stored night window (all
  nights, `demo_combined_finish.py:1076`) and `nights = len(kisiwa.json runs)` = 10 (`:1083`). One added night → 11 ≠ 10.
- KIS-9 (`demo_combined_rows.py:783-793`, records read unbounded at `demo_combined_finish.py:1383-1384`): exactly one
  `FUEL_DELIVERY`; the dip instants must equal the story log's; every dip recorded exactly 15 min after it occurred.
  Added dips/deliveries (posted at DB now) break all three.
Proposed: extend the pre-authorised bound to these two: KIS-1's window query and `_kisiwa_read`'s `records` query take
only the story calendar's nights / `occurred_at` in `[run1_start, runs[-1].end)` from `story.json`. Same "any other
failure stops" rule otherwise.

**Q4 (High) — the §4.7 rehearsal clone cannot run G1 as written.** `AssetOpsV1-k10\var\demo3_r3u` was prepared from
code `a282414ea` (S = 2026-11-06); its `tree\` has no `fuel_night` (→ `FUEL_STAGE_MISSING`), no entry route (probe gets
404, not 403/422) and no Kisiwa `add-day` child. Every child and the tick run from `<work>\tree` (`demo_combined.py:334`,
`:759`). Its DB is at head 0058 (tree has `0058_fuel_watermark_inputs.py`), which G1–G3 keep.
Proposed: after copying to `var/g1_audit`, replace `var/g1_audit/tree` with a `git archive` of the G1 branch HEAD (G2
and G3a merged in), the same `parts` as `prepare` (`demo_combined.py:439-451`), keeping `keys.json`, `story.json`,
`days.json`, `kisiwa.json` and `operational-actions/`. (`kisiwa.json` `log.path` still points into the K10 folder,
which `_kisiwa_read` only reads; acceptable.) Also: the clone name `assetops_k9_audit_g1` does not match
`require_prepare_database` (`prepare_clock.py:13`, `assetops_polish_*|*_test`); the add-day child sets no story clock,
so I would not call it there. Confirm, or name a `*_test` clone instead.

**Q5 (Medium) — how to tell a story day from an added day for `STORY_DAY` and the default `--from`.** `days.json["days"]`
mixes prepare entries and `add-day` entries (`demo_combined.py:771-774`); nothing marks which is which (`assess` is
not reliable: story kinds may carry `assess: tick`). Proposed: last story day per Site = max over
`days.json["doc"]["sites"][site]` of `weekday_offset(site, S, day_offset(e["day"]))` (the baselined calendar; `add-day`
never edits `doc`); default `--from` = day after the max offset in `days.json["days"]` for that Site (EV: next Tuesday).
Kisiwa: last story night = `story["kisiwa"]["runs"][-1]["night_date"]`; last night = max of that and the last
`DONE`/`PUBLISHED` `kisiwa-days.json` entry.

**Q6 (Medium) — the tick can miss Kisiwa (serve loop race) and step 7 then has no `fuel_night` code.** A running
`serve` ticks every 2 min with the same environment claim; the add-dates tick then reports `SKIPPED_CLAIMED`, or Kisiwa
may be in `RETRY_DUE` back-off. Proposed: verification reads the night's window (revision ≥ 1, `WITHIN_MARGIN`, no fuel
Finding) as the pass condition; the tick's `fuel_night` code is required to be `OK` only when the tick visited Kisiwa.
If the window is not there yet, run up to two more ticks before `ADD_NIGHT_UNEXPECTED`.

**Q7 (Medium) — where the `FUEL_STAGE_MISSING` / `ENTRY_DISABLED` probes run, and what a 404 means.** Both must read the
build's code (`<work>/tree`), not the checkout the owner runs `demo_combined.py` from, so they run in a tree child
(proposed: `demo_combined_kisiwa.py preflight <url> <work>`, run with `serve_env=True`, printing `{fuel_stage: bool,
entry_status, entry_code}`). §4.3 refuses only on 403 `WORK_WRITE_FORBIDDEN`. Proposed: anything other than 422
`OPREC_ENTRY_INVALID` refuses `ENTRY_DISABLED` (a 404/405 means the build predates G3a). And a build whose tree has no
Kisiwa `add-day` verb refuses up front (`FUEL_STAGE_MISSING` will usually catch it first; prepare from a post-G1 main).

**Q8 (Medium) — a Kisiwa night older than 30 days publishes readings, then its records are refused.** G3a refuses
`occurred_at` more than 30 days back (`WORK_OCCURRED_AT_TOO_OLD`, §3.2 refusal 6); readings would already be
`PUBLISHED`, and resume would fail every time (`PARTIAL_NIGHT`). `GAP_NOT_ALLOWED` forces Kisiwa to start right after its
last night, so this happens when the build is ~29+ days old. Proposed: a whole-command refusal `DATE_TOO_OLD` (Kisiwa
only) when the first night's 18:00 dip is more than 30 days − 1 hour before DB now: "Kisiwa {date} is too old to add
records for; prepare a fresh build."

**Q9 (Low) — small CLI edges.**
(a) A `--site` the build did not prepare (`story["sites"]`): refuse `UNKNOWN_KIND` "{site} is not in this build";
`--site all` = the build's Sites. (b) `add-day --site KISIWA-001` with `--as` or `--assess-now`: refuse `UNKNOWN_KIND`.
(c) The add log: `log_id` `kisiwa-001-story-{S yyyymmdd}-add-{d yyyymmdd}` uses `story["S"]`'s date as written (the
story log uses run 1's local date, `demo_combined_kisiwa.py:263`; confirm S is intended); its header is a new constant
(the story `LOG_HEADER` `:205-210` names a whole-day move); the delivery action carries the shipped log's fields
(`actor: Fuel supplier`, `component_id`, `volume_l`, `ticket {reference, volume_l}`, `recorded_after_minutes: 30`,
informational only since the record is posted at DB now), dips `actor: Shift operator`. (d) `serve`'s "Add a story day
live" lines (`demo_combined.py:840-843`) become one `add-dates` line. Proposed answers as stated.
