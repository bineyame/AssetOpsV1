# FX-KOBO-GAPS review

Reviewer: fresh Claude reviewer (not the author). Revision `94f998602` on `task/FX-KOBO-GAPS`, diff `main...task/FX-KOBO-GAPS`.
Spec: D-E5.11-15 and D-E5.16-20 (`AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md`); owner text
`.agent/owner-kobo-gap-pattern-2026-11-10.md`; packet `.agent/FX-KOBO-GAPS-packet.md`.

## Verdict: ACCEPT WITH NOTES

The v4 calendar, the six new days, WK-GAP (week and month), WK-2a/2b, the singular wording and the re-pins are correct
and safe for tonight's v4 prepare. Nothing found would make the v4 build refuse, mis-chain or false-fail. One Medium is
about the v3 rollback path. The Architect needs to acknowledge it before anyone relies on the fallback. It does not block
the v4 build.

## Questions settled

1. **v4 calendar.** The file diff against v3 shows only the label and status, `schema.version` 3->4, the six new
   S-27..S-22 entries, S-4 `missing`, and S-3/S-2/S-1 `steady`. `kinds`, `trial`, `mill_change_day`, Cold and EV are
   byte-equal. I resolved it independently for S = 11-08 and 11-09:
   - Week: missed [S-4], partial [S], five full days.
   - Month [S-28, S]: missing {S-10, S-4}; story-only {S-28, S-21, S-14, S-7, S}.
   - Trial pair, generator days, S-10 (FILL-1), S-9 mill change and its later days, and pinned S-19..S-15 are all
     unchanged.
   - SP-3 gives g = 4. That matches D-E5.20's "4 · 5".
2. **Six new days, same ingest path.** They are ordinary calendar entries. They go through `_expand` ->
   `check_full_day` / `check_full_day_chains` / `check_mill_side` / `_tiled` -> `resolve` -> `run_day`. That is the
   same path as S-20..S-15:
   - S-27 has no full neighbour (S-28 is story-only), so the `FRESH_NIGHT` branch applies.
   - S-26..S-22 use `night-early-after-before` against `kobo-steady-before-mill` `end_24`. That is the same pair as
     S-19 after S-20.
   - Epochs: S-28..S-11 is one stream (`day-1`), S-9..S-5 is `day-21`, and S-3..S+1 is `day-28`. All `received_at`
     values are in source order, there are no duplicates, and validate/installs pass.
   - No `late` entry remains, so `LATE_IN_STREAM` cannot fire.
   - `apply_baseline("b22")` drops nothing.
   - `kobo_expected_seconds` scales the cap with the entries.
   - Studies: client4 shows that the scan does not queue October studies. Its only October study is the reconciled
     10-20..10-24 one, even though S-20..S-11 were full days. So the "no new study" claim holds.
3. **WK-GAP month clause: no false-fail.** Backfill step a builds every measure on every day from first evidence
   (`chain/backfill.py:136-141`). Subjects come from the Foundation, not the day. Read-only check of
   `assetops_polish_client4_test`:
   - Each of the 4 measures has exactly one subject, with a snapshot on all 29 days 10-11..11-08.
   - Full days read COMPLETE, story-only days PARTIAL, and unbuilt or missing days NO_DATA. That includes 10-19, a
     `steady-before-first` day after a story-only day, which is the S-27 analogue.
   - `productive_kwh` has no rows only on 10-09/10-10, which is before S-28.
   - NOT_EXPECTED does not occur. No tolerance is needed.
4. **Finish rows.**
   - WK-2a is keyed on S-1's kind (27.50 / 42.08) and is fine.
   - WK-2b: `opportunity_items` drops studies with 0 eligible days (`chain/opportunities.py:74`). That is why v3 read
     "No potential found yet". On v4 the S and S+1 studies both have 3 eligible days and are UNKNOWN (any missing day,
     `projection.frozen_result`). So a Not-judged sentence shows, and it is accepted for any n.
   - Thread is RECURRED, so the potential is shown. `after.py` O12 (S-8 "No potential", S-5 "Not judged yet") still
     holds by the same reasoning.
   - Singular wording is fine.
   - SP-1/F-CAL/CO-6 are data-driven.
   - **WK-FILL is acceptable.** It is report-only, has no assertion, and its keys (`offset`, `epoch`, `kind`) are always
     in the payload.
5. **Pins.**
   - The v3 K7 pins are unchanged and still asserted on `V3_FILE`, so only the day list moved the v4 hash. That is a
     legitimate re-pin.
   - `kinds` equality is strict (`test_demo_story_days.py`, the `rest` dict comparison).
6. **Rollback.** `--days ...v3.json` still resolves (48 Kobo runs). See finding 1 for what happens after it builds.

## Findings

1. **Medium: the v3 rollback prepare now ends in SELF-CHECK FAILED, and live `add-dates` on it raises.**
   Locations: `tools/demo_combined_finish.py:674-706`, `tools/demo_combined.py:1001-1004`, `tools/demo_combined.py:1358`,
   `tools/demo_combined.py:1375`.
   - What happens: WK-GAP is designed to fail on a v3 calendar (D-E5.13 item 3, "the intended alarm"). A failed row makes
     `prepare` raise `SELF-CHECK FAILED` after the full build. `add-dates` (script Step 7) re-runs `finish check` and
     raises "This build no longer passes its checks" in front of the audience.
   - Why it matters: D-E5.12 says the fallback is "no code revert" and the rows "pass on both calendars". The packet's
     rollback claim covers resolve only and does not name this.
   - Classification: this is a ruling contradiction, not a coding defect.
   - Fix: the Architect either accepts and documents that a v3 fallback build reports WK-GAP failing (and that add-dates
     on it prints FAIL), or rules that WK-GAP is report-only when `days.json` `source` is v3.
2. **Low: the trial manifest label is hard-coded to v4.** Location: `tools/demo_combined_kobo.py:563`.
   - A v3 rollback build records `"days": ...v4.json`. This is pre-existing in form (it was hard-coded to v3).
   - Fix: use `days.json` `source`.
3. **Low: FILL-1 on the default calendar has no L0 test.** Location: `backend/tests/test_demo_story_days.py:883-884`.
   - `test_s10_is_fillable...` moved to `V3_FILE`, so no test asserts that S-10 is fillable on v4.
   - I checked by hand: `plan_add_runs(v4, ..., "steady-before-first" | "normal", day="S-10d")` succeeds for S =
     11-08 and 11-09.
   - Fix: add a v4 parametrisation of the positive half.
4. **Low: the B-16 time fallback now keeps the six fill days.** Location: `tools/demo_story_days.py:449-457`.
   - `apply_baseline("b16")` drops only [S-20, S-15), so S-27..S-22 (about +13 min) stay in the build. B-16 exists to
     save time.
   - Note for the Architect. No change asked tonight.
5. **Low (preference, outside the card): the other limit sentence has the same singular problem.**
   - `LIMIT_DAYS` still reads "1 of the 5 study days lack a reading" (`test_ch4_opportunity_postgres.py:235`).

## Checks run (this revision, plan2 venv, absolute PYTHONPATH, one file at a time)

| Check | Result |
|---|---|
| test_demo_story_days.py | 91 passed |
| test_demo_combined_finish_rows.py | 67 passed |
| test_ch4_opportunities.py | 16 passed |
| test_k7_kisiwa_story.py | 101 passed |
| test_demo_combined_finish_days / _co1 / _mill / _links | 1 / 5 / 15 / 11 passed |
| test_own_g1_add_dates.py | 45 passed |
| test_k7f_kis10_window.py | 3 passed |
| check-architecture.ps1 / check-agent-workflow.ps1 (no -ExecutionPolicy) | both passed |
| Offline resolve v4 and v3, epochs, b16, FILL-1, SP-3 g, SP-4 UTC gaps | as stated above |
| client4 DB (read-only SELECTs) | snapshot coverage, studies, thread events as stated above |

## Not verified

- No prepare and no Postgres finish run, so the served figures are unconfirmed. These are the D-E5.20 figures, the
  CO-5/SP-1 S-28 board now that S-27's night starts at S-28 21:00Z, the RECURRED day and the October totals.
- No full suite (demo-sprint policy). Frontend is untouched.

## Residual risk beyond the packet

- The CO-5/SP-1 S-28 UTC window now holds S-27's night readings (21:00Z-24:00Z). This is analogous to S-21/S-20, which
  passes today, but it has not been measured on S-28. It is a stop row.
