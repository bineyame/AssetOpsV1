# Review: POLISH PA-3 (producers, links, Addendum 12 wire fields, polish rebuild)

Reviewer: fresh Claude reviewer (independent; did not author the slice). Date 2026-11-01.
Worktree `AssetOpsV1-polA3`, branch `task/POLISH-PA-3-producers-rebuild`, head `080069629`; diff `0ad27df7f...080069629`.
Spec: plan2 `.agent/build-sheet-POLISH.md` §1.3, §3.1 (PA-3 rows), §4, §5 PA-3, §6, §7, Addenda 3, 5, 9, 10, 11, 12.

## Verdict: ACCEPT

There are no High or Medium findings. The four Lows below are records or test-hygiene items, plus one spec note for
the Architect. None of them blocks the merge.

## Checklist results

1. **Links: met.**
   - `tools/demo_combined.py:173-203` `story_links` is pure. Kobo boards use `?date=`. Cold and EV boards use the
     `days.json` `start`/`end`, and EV goes to `/ev`.
   - A null window gives the whole UTC calendar day, labelled ", no event: whole day" (`:192-196`).
   - `links()` (`:482`) calls `story_links`, and `serve` calls `self.links(web)` (`:519`).
   - Every route exists in `App.tsx` or `operatorSiteRoutes.ts`: `/portfolio`, `/findings`, `/maintenance`,
     `/maintenance/preventive`, `SITE_DETAIL` (`SiteOverview` reads `date`), `SITE_EV_ROUTE_PATH`, the action
     verification route and `SITE_FINDING_ROUTE_PATH`.
   - No `/outcomes` or `/overview` form remains.
   - The final capture URLs (`captures.json`) are these forms, and every capture is settled with no overflow.
   - The real `days.json` has no cold or EV day with a null window, so the whole-day path is exercised only by the pure
     test, and only for cold.
2. **Guards: met.**
   - `DB_RE` (`:52`) and `WORK_PREFIXES` (`:53`) are widened only to `polish`.
   - `MARKER` and the drop guard are unchanged.
   - The pure test accepts `assetops_polish_full_test` / `var/polish_full` and refuses `assetops_other_x_test` and
     `var/other_x`.
3. **Narratives: met.**
   - In w502 only `:208` (the former `:202`, the fixture WR) and `:467` (the former `:461`, the earlier visits)
     change, through `narrated()`.
   - `narrated()` reads `globals()["DEMO_NARRATIVES"]`, and the exec namespace is the globals, so standalone w502
     passes nothing and keeps the test default narrative.
   - The worst-case `:315` path is untouched.
   - Kobo and EV pass `narrative=f"{title}."` directly.
4. **Lab names: met.**
   - `dataclasses.replace` changes only `record.display_name`, and `ImportSource.sha256` is still `source.sha256`.
   - `import_site` returns the existing Site on a matching sha (`foundation_service.py:271-289`), so repeat installs
     return the same Site and keep the name. This is pinned with and without `display_name` in the w202 and w205a
     Postgres tests.
   - EV `_install` reads `registered.INSTALL_AT` lazily, so the swapped clock is kept.
   - No data or numbers were tuned.
5. **CO-1: met.**
   - `demo_combined_finish.py:463-481`: the column is `earlier` for VERIFIED, INEFFECTIVE or INCONCLUSIVE, and
     `issues` + `in_hand` otherwise.
   - The match is on the href path only (`split("?")[0] == path`), so a text-only match never passes.
   - The Must-not-harm checks are: the href contains the Action id and `/verification?event_id=`, the text contains
     `display_code(code)`, and the L1 sentence is present.
   - Each of the 5 pure tests can fail. I checked by mutation reasoning: popping the item href, popping the
     Must-not-harm href, a PENDING state with the Action under `earlier`, removing the L1 sentence, and the raw code
     (`ACT-000001` does not contain `ACT-001`) all raise.
   - **Deviation, reading the state from the Action read: sound.** The board's own `ActionFact.verification_state`
     comes from the same `verification.summary(...)["state"]` (`site_outcomes/mini.py:552,559`). So the check and the
     board placement use one source. `kobo.json` holds only the outcome id.
6. **Addendum 12: met.**
   - **Q1:** `board.py:429-441` `_case_wire` adds the stored `kind` and ISO-UTC `occurred_at` to case items in
     `in_hand` and `earlier`. Plan items get `kind: "PLAN"`. Existing keys are unchanged, and the data comes from
     `CaseFact`, which is already loaded.
   - **Q2:** `site_time_zone` comes from `s.timezone`, added to the existing tenant-scoped `_IMPORTED_SITES` select.
   - **Q3:** `asset_label` adds a correlated count to the existing `_ASSET` select, scoped by tenant and site. It uses
     the same non-retired predicate as the PA-2b reads (`postgres_global_read.py:50`, `postgres_work_read.py:79`) and
     the same `asset_words.asset_label` helper.
   - None of the three adds a new query path or a migration.
   - **"MAINTENANCE_REQUEST" instead of "WORK_REQUEST": fine.** The addendum says "as stored", and `CaseFact.kind` is
     documented as `INCIDENT | MAINTENANCE_REQUEST` (`board.py:163`). PB-3 filters only on `INCIDENT`. The packet
     states the shape.
   - **`legacy()`:** it drops only `kind` and `occurred_at`, and only in exact-dict asserts on `in_hand`/`earlier`.
     The new keys are pinned in three places: `test_case_items_carry_their_stored_kind_and_occurred_at`, the exact
     incident item in `test_incidents_and_closed_cases`, and a key-set assert. See L4 for one gap.
7. **P-08: met.** `var/polish_full/ev.json` fault day records `action.code` `ACT-000003`,
   `raised_at` `2026-11-01T11:30:19Z` (build time, after every story window), and `intent_id`. `Action raised_at` is
   the posted body value, which the packet discloses.
8. **TARIFF_GAP: met.**
   - `ev_site_reads.py:75` matches Addendum 11 word for word, and `test_polish_pa3_ev_tariff_copy.py` pins it.
   - The `ev-board-fault-1440.png` Next step reads "Publish a charging tariff / Needed before charging income can be
     estimated."
9. **Register: accurate.**
   - R645 matches the §1.3 text and adds the runbook line.
   - R646 records the override, the sha idempotency and the fixture names kept for tests.
   - R111 is marked closed for the demo build by R646.
   - R655 gains both TARIFF_GAP strings. The R535/R552 historical notes are fine.
10. **Evidence: verified.**
    - `var/polish_full/check.json` has 17 rows, all `pass`, and `idx_present` is true.
    - The H2 JUnit is in the coordinator scratchpad at `h2-junit.xml`, timestamp 2026-11-01T14:34:31+03:00. It shows
      tests=19, failures=0, errors=0, skipped=0, time 1878.8 s, and covers CO-1..CO-12, SP-3..7 and the self-check.
    - The build revision `84ab3ca3d` differs from head `080069629` only under `.agent/`, `.ai/` and `tasks/`.
    - `captures.json` is strict. It holds 28 captures, all settled with no overflow, and 15 counted hits per width:
      - portfolio-week 7: 5 uuid from `EstatePortfolio.tsx:143`, 2 "Scenario" from `:367`;
      - cold-board-normal 1: `ColdAssessmentViews.tsx:734`;
      - ev-board-fault 4: 3 `REC <uuid>`, and "Scenario details" from `EvSiteViews.tsx:760`;
      - maintenance-preventive 3: from `GlobalPreventive.tsx:45/50` and the Draft badge.
    - All 15 are frontend sources and none are server text.
    - Kobo, cold-failure, findings and wr-overview are 0, so lane A is at 0.
    - Spot-checked `ev-board-fault-1440.png`:
      - h1 "Depot Charging Hub";
      - Already in hand lists only PM-013 (consistent with R645);
      - tariff wording is new;
      - "Investigate Connector c1".

## Findings

**L1 (spec note for the Architect, not an implementation defect).** `tools/demo_combined_finish.py:477-478`
- **Problem:** the non-final branch of the CO-1 check (`issues` + `in_hand`) follows Addendum 10, but it does not
  match the board. `earlier_result_for_action` (`board.py:349-353`, `ACTION_RESULT`) places an *applied* Action with
  PENDING or REASSESSMENT_PENDING under `earlier` ("Pending"), not under `in_hand`.
- **How it could bite:** the Action read is the current state (`at=None`). Late evidence could turn the read into
  REASSESSMENT_PENDING, and the check would then look in the wrong column.
- **Severity:** it fails closed. It would fail the check falsely and can never pass it falsely, and today's build is
  VERIFIED.
- **Fix:** if this matters later, the Architect could rule that an applied Action is looked for in `earlier` whatever
  its state. No change is needed for this merge.

**L2 (test hygiene).**
- **Joined assert lines:** `backend/tests/test_w202_cold_lab_bindings_postgres.py:116` and
  `backend/tests/test_w205a_ev_foundation_postgres.py:499` have a line-join artifact, `==         "..."`. There are
  also three blank lines before the new w202 tests.
- **Uncovered branches:**
  - `test_w601c_request_detail.py` (Q3) uses a single-asset case, so it does not exercise the code-appended
    (`type_count > 1`) branch on the wire. The helper itself is covered by the PA-2b tests.
  - `test_demo_combined_links.py` has no EV whole-day case.
- **Fix:** clean up the joins, and optionally add the two cases.

**L3 (records).**
- **Corrupted packet command:** `.agent/POLISH-PA-3-packet.md:128-129` has a literal carriage return.
  "`tools\run-host-tests.ps1`" lost its `\r`, so it reads "`tools<CR>un-host-tests.ps1`". The JUnit path is also
  elided ("…"). Restore the command and name the JUnit file.
- **Stale acceptance criterion:** `tasks/POLISH-PA-3-producers-rebuild.md:24` (acceptance 6) still states the
  Addendum 9 Q4 form ("matching href or `display_code(action_code)`"). Addendum 10 superseded it with href-only
  matching and a state-chosen column. Update the line so the task file matches what was built.

**L4 (test coverage).** `backend/tests/test_out_b1_board.py:20-22` (and the copies in b2/b3)
- **Problem:** `legacy()` would also hide a `kind` wrongly added to an Action or domain-Action item in `in_hand` or
  `earlier`. No test pins that Action items carry no `kind`.
- **Fix:** add one assert, for example `"kind" not in` the DA-001 item in
  `test_cold_protect_lists_domain_action_in_hand_...`.

## Checks I ran

- **Pure, via `tools\run-host-tests.ps1`:** `test_demo_combined_links.py`, `test_demo_combined_finish_co1.py`,
  `test_polish_pa3_ev_tariff_copy.py`, `test_out_b1_board.py`, `test_out_b2_mini.py` and `test_out_b3_cold_ev.py`.
  Result: **92 passed** in 2.6 s.
- **Postgres, on per-run `_test` DBs, `-n 3 --dist loadfile`:** `test_w601b_global_maintenance.py`,
  `test_w601c_request_detail.py`, `test_w202_cold_lab_bindings_postgres.py`, `test_w205a_ev_foundation_postgres.py`
  and `test_w207_ev_site_reads_postgres.py`. Result: **81 passed**, 9 warnings, 1021 s.
- **`tools/check-architecture.ps1`:**
  - With no guard interpreter it fails, because Rule 8's SQL extractor finds no `.venv` in this worktree. That is
    environmental: the check was vacuous, and no code violation was found.
  - With `ASSETOPS_GUARD_PYTHON` set to the plan2 venv: **passed**.
- **`tools/check-agent-workflow.ps1`: passed.**
- **Read-only:** `var/polish_full/{check.json,ev.json,days.json}`, the H2 JUnit and `captures.json`.

## Not verified

- The frontend suite, the build and `tsc` were not run, because the slice has no frontend changes.
- The slow build test, `prepare`, serve and the captures were not rerun (all forbidden). I rely on the artifacts
  above, which match the packet's numbers and revision.
- `check-all` 12/12 is the implementer's claim. I ran only the two guards above.

## Residual risk (beyond the packet)

- `ev_site_reads.py:27` `NO_MONEY = "No gross tariff scenario assessed."` is outside Addendum 11's scope and not on a
  capture screen. The same applies to the frontend "gross tariff scenario" strings (`EstatePortfolio.tsx:587`,
  `EvEnergy.tsx:73/76`).
- The "Bounded money consequence" heading still renders on `ev-board-fault`. It is frontend, and the vocabulary gate
  does not count it.
- All three are PB-3/PC copy items to confirm at the final gate.
