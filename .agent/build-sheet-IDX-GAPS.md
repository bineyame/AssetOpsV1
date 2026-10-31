# Build sheet IDX-GAPS · Finding index `finding-index/2`: show Findings from assessed days, name the gaps

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-31. Owner approval (verbatim, end of
`.agent/owner-client-demo-sequence-2026-10-30.md`): "approve all three, go ahead" on
`.agent/architect-sparse-days-proposal-2026-10-31.md` (recommendation 1). Code read at main `ca6d7d61b`. Worktree
`C:\Users\assef\Bineyame\AssetOpsV1-idxgaps`, branch `task/IDX-GAPS-finding-index-v2` (created, on `ca6d7d61b`).
Backend paths are relative to `backend/assetops_backend/` unless they start with `backend/`, `tools/` or `frontend/`.
This sheet is self-contained. Read nothing else unless a step names it.

## 0. Rules that bind every unit

- This is the **single approved exception** to "don't change the board rules". The board keeps its 31-day window,
  categories, statuses, Must-not-harm and placement rules. Only the Finding source's settledness changes (U2).
- **Nothing shown today may become hidden.** Every v1 CURRENT body is still CURRENT in v2, with identical rows, count,
  order and paging (U1 test T1). **No gap may read as zero or normal.** A day that is not assessed is always named:
  never counted as "no Findings", never as On track.
- STALE stays: a writer change during the read (fence moved) returns v1's status, no rows, no count, unchanged.
- Do not touch `main.py`, any `*/composition.py`, `estate/**`, `work/**`, `field/ gateway/ contracts/ simulator/ host/
  contract-fixtures/`, `backend/migrations/`, `tools/checks/*`. No new port, store method or SQL.
- The frontend authors no "Not available yet" string (`tools/checks/missing-claim-scan.mjs` `PATTERNS`). The board
  gap line is backend text; the Findings page copy below avoids that phrase.
- No status code (`PARTIAL`, `UNASSESSED`…) or policy version on screen, in `title` or `aria-label`, except the
  existing labelled raw value in the closed references ("Recorded list state", `SiteFindingIndex.tsx:439`).
- Every string in §3 was scanned against `terms` + `w1.terms` + `w1.codes` + the four `w1.patterns` of
  `frontend/src/test/productVocabulary.json`: 0 hits. A string you invent is scanned the same way.
- Register IDs **R610-R613** (DEMO-COMBINED holds R600-R609; DEMO-SPARSE takes R615-R619).

## 1. Code reality (consumers of the S4-04 index and what each does with PARTIAL)

| Consumer | Reads `analytics/finding_index.py`? | v1 behaviour | v2 treatment |
|---|---|---|---|
| Route `GET /api/sites/{code}/finding-index` (`finding_index_api.py:40-76`) | yes, `FindingIndexService.read` | passes body through; no status logic | **unchanged code**; body gains §4 fields |
| Board, mini (`site_outcomes/read.py:229-234` port → `site_outcomes/mini.py:271-275`) | yes, pages `[S+1−31d, S+1)` | settled unless status ∈ `UNSETTLED_INDEX_STATUS` = FAILED/STALE/PENDING (`mini.py:90`). **UNASSESSED settles with 0 rows** (DEMO-A probe R2 check 3): a gap read as zero, and the cause of "linked finding outside this view" (`board.py:268-270`) | **U2**: settled only on CURRENT, or PARTIAL whose board day is not a gap; gap line on the wire |
| Estate outcome summary = Portfolio cells (`site_outcomes/read.py:384-431`) | indirectly: composes each mini Site through `self.board(...)` on `mini_summary_day(hi)` (`:396`) | inherits board | inherits U2; no new field on the summary; Portfolio UI unchanged |
| Cold and EV boards (`cold.py:178`, `ev.py:226`) | no (own assessment lists) | — | unchanged |
| Site Findings page, mini (`frontend/src/sites/SiteFindingIndex.tsx`, mounted `shell/SiteAnalyticsFrames.tsx:548`) | yes, via `findingIndexClient.ts` | rows only for CURRENT (`:670`); other states "not known" + `DayStrip` | **U3**: PARTIAL lists rows, names the gap days |
| Overview day list (`frontend/src/sites/OverviewFindingList.tsx`, mounted `SiteWindowOverview.tsx:947`) | yes, one-day window | rows only for CURRENT && `is_current` (`:89`, `:276`) | **U3**: PARTIAL lists rows with one note |
| Client validator (`findingIndexClient.ts:23`, `:137-143`) | — | accepts only `schema_version === "site-finding-index-1"`; status union lacks PARTIAL | **U3**: `-2`, PARTIAL |
| Estate Findings index and Portfolio Findings (`estate/coverage.py:80-140`, `estate/adapters/postgres_estate_read.py:158`) | **no**: reads the store snapshot `index_snapshot_on` and applies its own all-days rule over the estate period (`coverage.py:118`, rows only when `state in COVERED`, `:122`) | — | **unchanged** (out of scope). Residual: a period containing one unassessed day stays Unknown there. Register **R613** (open) |
| Work link coverage (`work/link_coverage.py:50-68`, `work/adapters/postgres_work_read.py:260-277`) | no: store snapshot, judged per link over the Finding's own episode days | already per-Finding | unchanged |
| Work Site index (`work/site_index.py:13`, `:182`) | no (`sfi1-` port is null by design) | — | unchanged |
| Tools `tools/s404_finding_index_walkthrough.py`, `tools/s502_overview_finding_list_walkthrough.py`, `tools/w601_seed.py:525` | yes (HTTP / test helpers) | print status, days, reasons (`s404…:100`) | builder greps for `site-finding-index-1` / `"CURRENT"` asserts; update a literal only, no logic |

**v1 rule** (`finding_index.py:262-350`): `discover` (`:200`) grows the requested UTC days across any edge a stored
canonical episode `reaches` (`:172`, tolerance 20 min, `dispatch_v3.CONTINUITY_TOLERANCE`) or a selected Candidate
segment reaches (`candidate_reach`, `:183`). `_day` (`:239`) gives each day S3 status, demoted to PENDING when the
match pass has not covered its seq or deferred it. Overall status = worst of `_RANK` (`:55`) present, else STALE if
the fence moved, else CURRENT (`:285`). Rows, count and cursor only when CURRENT (`:313`).

**Existing tests that pin behaviour v2 must keep:** `test_s4_finding_index_postgres.py` (all CURRENT asserts; the
`assert_no_claim` cases at `:164`, `:191-193`, `:200`; fence test `:453-460`), `test_s4_deferred_match_postgres.py`
(scenario A/B: a deferred or stale neighbour keeps the one-day window PENDING with no rows), `test_s4_finding_index_reach.py`.
**One test changes meaning:** `test_out_b2_mini.py:296-301` asserts UNASSESSED settles; v2 replaces it (U2).

## 2. Units (4). Effort 3.25 builder days plus one full suite

### U1 · Index v2: per-Finding withholding, PARTIAL, `gaps[]` · 1.0 d · per-unit review (shared seam)
File: `analytics/finding_index.py` only.
- Constants: `SCHEMA_VERSION = "site-finding-index-2"` (`:41`); add `POLICY_VERSION = "finding-index/2"` and
  `PARTIAL = "PARTIAL"`. Token prefix becomes `"sfi2-"` (`_token`, `:231`) and the basis dict (`:288`) gains
  `"policy": POLICY_VERSION`, so no v1 cursor validates against a v2 basis.
- New pure helpers (module level, unit-testable without a store):
```python
def touched(head, days: list[date]) -> set[date]:
    """Inspected days the episode touches: those it intersects, widened by the continuity tolerance either side."""
    return {d for d in days if head["episode_start"] <= _day_start(d + timedelta(days=1)) + CONTINUITY_TOLERANCE
            and head["episode_end"] >= _day_start(d) - CONTINUITY_TOLERANCE}   # inclusive, as `reaches` (:172)

def gap_days(inspected: list[dict], reach: Callable[[date], tuple[bool, bool]]) -> dict[date, tuple[str, str]]:
    """G: day -> (state, reason). A non-CURRENT day: (its status, "NOT_CURRENT"). A CURRENT day whose selected
    Candidate segment reaches an edge into a non-CURRENT (or uninspected) neighbour: ("CURRENT", "EDGE_NEXT_TO_GAP")
    - the matcher may have skipped that cluster (the `candidate_reach` H1 reason)."""
```
- `read()` after `:285`, when **not** `moved`:
  1. `G = gap_days(inspected, edge_reach)`; `requested = requested_days(start, end)`.
  2. If `G` is empty: status CURRENT (v1 path, unchanged).
  3. Else if some requested day is not in `G`: status **PARTIAL**. `rows` = the v1 intersecting heads (`:286`) whose
     `touched(h, days) ∩ G` is empty. Every withheld head adds, for each of its touched days not already in `G`, a
     gap entry `("CURRENT", "WITHHELD_FINDING")` (these days do not withhold other heads; eligibility uses `G` only).
  4. Else: v1 rank status (`next(x for x in _RANK if x in statuses)`), no rows.
  When `moved`: v1 exactly (`:285`), no rows, and `gaps` still listed.
- Paging: `:303` `BASIS_NOT_CURRENT if status not in (CURRENT, PARTIAL)`; `:313` `if status in (CURRENT, PARTIAL)`.
  PARTIAL `total_count` = len(eligible rows). Order and the `after` rule are unchanged.
- Body (`:324-350`): add `"policy_version": POLICY_VERSION`, `"gaps": [{"day", "state", "reason"}]` sorted by day
  (all inspected days in `G` plus WITHHELD_FINDING entries; `[]` when CURRENT), `"withheld": bool` (any head
  withheld). `is_current` stays `status == CURRENT` (False for PARTIAL). `rows_statement` for PARTIAL:
  `"Rows from assessed days only: a Finding that touches a day listed in gaps is not shown, and the count covers the
  shown rows only."` (API text, not rendered). `status_reasons` keep every non-current day's reasons, as v1.
- Module docstring (`:11-18`): replace the "Every other status returns no rows" sentence with the v2 rule (5 lines).
- Tests, new `backend/tests/test_idx_gaps_index.py` (fake store + fake dispatch, no DB):
  - **T1 (no regression):** for 6 v1-CURRENT fixtures (empty, 1 row, 3 rows paged by 2, cross-midnight episode with
    both days CURRENT, merged head, deferred-but-current-after-pass): status CURRENT, `gaps == []`, and rows,
    `total_count`, order and the `next_cursor` page walk equal literal expected lists written in the test (taken
    from a v1 run on `ca6d7d61b` before the change, recorded in the packet).
  - T2 one UNASSESSED day mid-window, Finding on a CURRENT day 08:00-09:00 → PARTIAL, 1 row, `gaps == [{day,
    "UNASSESSED", "NOT_CURRENT"}]`, `total_count == 1`, `is_current is False`.
  - T3 Finding 23:45-23:58 on day D, D+1 UNASSESSED → withheld; `gaps` has D+1 NOT_CURRENT and D WITHHELD_FINDING;
    another Finding on D at 08:00 is shown; `withheld is True`.
  - T4 Candidate segment reaching D's end edge, D+1 PENDING → D is EDGE_NEXT_TO_GAP; a Finding on D at 08:00 is
    withheld; a one-day window `[D, D+1)` is PENDING with no rows (v1 status; scenario A preserved).
  - T5 every requested day in `G` → v1 rank status, `rows == []`, `total_count is None`, `gaps` listed.
  - T6 fence moved with a gap present → v1 status, no rows (STALE_PROJECTION when every day CURRENT).
  - T7 cursor from a PARTIAL page validates on the same basis; fails `SELECTION_CHANGED` after a gap day turns
    CURRENT; a `sfi1-` token fails.
  - T8 pending day (S3 CURRENT, unmatched) mid-window → its gap state is PENDING, reason NOT_CURRENT.
- Update `test_s4_finding_index_postgres.py:181` literal `"sfi1-"` → `"sfi2-"` and any `site-finding-index-1` literal.

### U2 · Board: PARTIAL settles when the board day is not a gap; the gap line · 0.75 d · per-unit review
Files: `site_outcomes/mini.py`, `site_outcomes/board.py`, `site_outcomes/read.py`.
- `mini.py:146-175` `Reads`: add `self.first: dict[str, dict] = {}`; in `pages` store the first body per name.
- `mini.py:90`: `UNSETTLED_INDEX_STATUS = ("FAILED", "STALE_PROJECTION", "STALE", "PENDING", "UNASSESSED")`. Note:
  the dispatch constant is `"STALE_PROJECTION"` (`analytics/dispatch_read.py:34`); v1's `"STALE"` never matched it
  and the fence status is `STALE_PROJECTION` too. Keep `"STALE"` in the tuple for safety.
- New pure `index_settled(body, day) -> bool` in `mini.py`: True when status == CURRENT; when status == PARTIAL,
  True iff `day.isoformat()` is not the `day` of any `gaps[]` entry; otherwise False.
- `mini.py:271-275` becomes (`first = reads.first.get("finding_index")`):
  `findings_ok = finding_rows is not None and first is not None and index_settled(first, day) and not
  (reads.statuses.get("finding_index", set()) & set(UNSETTLED_INDEX_STATUS))`. Keep the
  `reads.failed.append("finding_index")` when not ok.
- Gap line: new pure `finding_gap_line(body, requested: int) -> dict | None` in `mini.py`, `requested` = 31.
  Count `g` = requested days (`body["discovery"]["requested_days"]`) whose gap entry state is not CURRENT. None when
  `g == 0` or body is None. Text (§3): all such states UNASSESSED → `GAPS_NO_READINGS`, else `GAPS_NOT_ASSESSED`;
  when `body["withheld"]` append `GAPS_WITHHELD`. Returns `{"text": str, "days": [iso days, ascending]}`.
  The line is set whenever `g ≥ 1`, settled or not (when unsettled the existing PARTIAL notice also shows).
- `board.py:193-240` `SiteFacts`: add `finding_gaps: Mapping[str, Any] | None = None`; `mini.py:361` passes it.
- `read.py:351-365` board wire: add `"finding_gaps": jsonable_encoder(comp.facts.finding_gaps)` (cold/EV: null).
  `POLICY_VERSIONS` (`read.py:36`) gains `"finding_index": "finding-index/2"` (board and summary; additive).
- Tests:
  - `test_out_b2_mini.py:296-301`: replace the UNASSESSED-settles assertion with three cases: UNASSESSED (no rows)
    → unsettled; PARTIAL with board day in `gaps` → unsettled; PARTIAL with board day CURRENT and rows [F104] →
    settled, `outcome(rows[COST], "MG-2") == "NEEDS_ATTENTION"`, `facts.finding_gaps["text"]` = the §3 example for
    the fake's gaps. Add `"STALE_PROJECTION"` to the `:297` loop.
  - New `backend/tests/test_idx_gaps_board.py` (pure): `finding_gap_line` for g = 0 (None), 1 UNASSESSED
    ("1 of 31 days has no assessed readings"), 23 UNASSESSED, 2 with one PENDING (not-assessed form), withheld suffix;
    `index_settled` truth table; the text passes the vocabulary scan (reuse `test_out_b2_vocabulary.py`'s helper).
  - `test_out_b2_vocabulary.py`: add the three §3 board strings to its scanned set.

### U3 · Frontend: client, Findings page, Overview list, board line · 1.0 d · slice review
Files: `frontend/src/sites/findingIndexClient.ts`, `SiteFindingIndex.tsx`, `OverviewFindingList.tsx`,
`OutcomeBoard.tsx`, `outcomeBoardClient.ts`, `frontend/src/ui/productWords.ts`, fixtures
`frontend/src/sites/__tests__/findingIndexFixtures.ts`, `frontend/src/test/outcomeBoardFixture.ts`.
- Client: `FindingIndexStatus` (`:23`) adds `"PARTIAL"`; body type gains `policy_version: string`,
  `gaps: { day: string; state: FindingIndexStatus; reason: string }[]`, `withheld: boolean`; `schema_version:
  "site-finding-index-2"` (`:88`, `:140`). Export `listsRows(body) = (body.status === "CURRENT" && body.is_current)
  || body.status === "PARTIAL"` and `gapDays(body)` = gaps on requested days with state ≠ CURRENT.
- `productWords.ts` `CURRENTNESS` (`:62`): add `PARTIAL` (§3). Its tone `"limited"`.
- `SiteFindingIndex.tsx` `Loaded` (`:664`): the not-current branch condition becomes
  `!listsRows(body) || body.total_count === null`. New branch before `:690` for `body.status === "PARTIAL"`:
  `View state="partial"` (data attribute `data-site-findings="partial"` via the existing `View` prop), claim §3
  (count form or zero form), status `ProductStatus words={currentnessWords("PARTIAL")}`, body = `<Rows>` (when rows)
  + pages nav (reuse `:722-734`) + `<Gap>` with the §3 gap paragraph (+ withheld sentence when `body.withheld`) +
  `<DayStrip body={body} rows />` (`:422`; it already labels each day, e.g. "We have not checked this period").
  `NOT_CURRENT_CODES` (`:191`) unchanged (PARTIAL is not a not-current code).
- `OverviewFindingList.tsx`: `:89` and `:276` use `!listsRows(body)`. In the rows branch (`:332-395`), when PARTIAL
  append §3 `OVERVIEW_PARTIAL` after the count span. `compareParity` keeps its per-day check (`:111`).
- `OutcomeBoard.tsx` `OutcomeBoardView` (`:333-345`): after the rows, when `body.finding_gaps` render
  `<p className="v69-chart-note" data-outcome-finding-gaps>{body.finding_gaps.text}</p>`. Type in
  `outcomeBoardClient.ts:136`: `finding_gaps?: { text: string; days: string[] } | null`.
- Vitest (`npx vitest related --run <changed>`): Findings page PARTIAL with 1 row (claim, row link, gap paragraph,
  day strip names the gap day), PARTIAL with 0 rows (zero form, never "No Findings in this window", never the
  proved-empty words), withheld sentence; the v1 CURRENT snapshots unchanged; Overview list PARTIAL lists the row and
  the note; board renders the line only when present; `missing-claim-scan` and the vocabulary test stay green.
- Capture at 390 and 1440 px: Findings page PARTIAL, board with the line (mini overview). Line clamp: the board line
  is one line at 1440, may wrap to 2 at 390; no horizontal scroll (`tools/checks/shell-overflow.ps1`).

### U4 · Postgres proofs, register, full suite · 0.5 d + suite · slice review
- New `backend/tests/test_idx_gaps_postgres.py` (reuse `test_s4_finding_index_postgres.py` helpers `CaseRunner`,
  `run_case`, `client_for`, `ok`, `assert_no_claim`, `block`, `SPEC`; DB `assetops_idx_gaps_test`):
  - P1 one missing day: F01 (2026-10-06 08:00-09:00) assessed + matched; window `[10-06, 10-08)` (10-07 has no
    evidence) → PARTIAL, F01 the only row, `gaps == [{"day": "2026-10-07", "state": "UNASSESSED", ...}]`.
  - P2 one pending day: deliver late evidence on a CURRENT neighbour day 10-08 (as `:198-200`), window
    `[10-06, 10-09)` → PARTIAL, F01 shown, 10-08 PENDING or STALE_PROJECTION in gaps.
  - P3 an episode next to a gap still withheld: deliver a Candidate block 2026-10-06 23:45-23:59, assess + match, no
    evidence on 10-07 → window `[10-06, 10-07)` gives the v1 status with no rows (10-06 is in `G` by the edge rule,
    or 10-07 is inspected and NOT_CURRENT); window `[10-05, 10-07)` with 10-05 assessed gives PARTIAL without the
    late episode.
  - P4 fence moved with a gap → no rows (patch the fence as `:453-460` does).
  - P5 board: `outcome-board?from=2026-10-06&to=2026-10-07` over P1's data: Finding index settled, `finding_gaps.text`
    names "30 of 31 days have no assessed readings" (or the exact count the data gives; assert the template).
- Register rows (§5) appended to `.agent/mock-departure-register.md`; add a note on **R595**: "IDX-GAPS merged; the
  Cost-row read-back is checked on the combined dataset (DEMO-SPARSE acceptance A-B1)". R595 stays open until then.
- Decision record: append `D-2026-10-31-finding-index-v2` to `.ai/DECISIONS.md` (5 lines: the rule, the owner quote,
  the board exception, estate unchanged, R613).

## 3. Copy (exact; all scanned, 0 hits)

Backend (board, `mini.py` `COPY`):
- `GAPS_NO_READINGS` = `"Not available yet · {g} of {n} days {has|have} no assessed readings"` — example "Not
  available yet · 23 of 31 days have no assessed readings".
- `GAPS_NOT_ASSESSED` = `"Not available yet · {g} of {n} days {is|are} not assessed yet"`.
- `GAPS_WITHHELD` (appended) = `"; Findings next to those days are not shown yet"`.
Frontend:
- `PARTIAL` words: label `"Some days are not checked yet"`; sentence `"This list uses the days that have been
  checked. The days not checked yet are named below, and nothing is concluded about them."`; next `"Look again
  after the remaining days have been checked."`.
- Findings page claim: `"{n} {Finding|Findings} on the assessed days"`; zero form `"No Findings on the assessed days"`.
- Gap paragraph: `"{g} of {N} days in this window are not checked yet, so nothing is concluded about them."`;
  withheld sentence: `"A Finding that reaches into one of those days is not shown until that day is checked."`
- `OVERVIEW_PARTIAL` = `"A Finding that reaches into a neighbouring day not checked yet is not shown."`
Pluralise with the existing `plural` helpers; `{N}` = requested days, `{g}` = `gapDays(body).length`.

## 4. Wire (index: schema `site-finding-index-2`; board/summary: additive)

Index body adds `policy_version` ("finding-index/2"), `gaps[{day, state, reason}]` (`reason` ∈ NOT_CURRENT,
EDGE_NEXT_TO_GAP, WITHHELD_FINDING), `withheld`; `status` adds PARTIAL; `selection_token` prefix `sfi2-`. Board adds
`finding_gaps {text, days[]} | null`; `policy_versions.finding_index`. Summary: `policy_versions.finding_index` only.
**Goldens/contracts:** none embeds the index or board body (checked: `contract-fixtures/`, `backend/tests/fixtures/`,
the `ASSETOPS_WRITE_S6/S603/S6_VERIFICATION/S7_CONTRACT` tests). `w301-estate-golden.json` covers estate roots only.
If a golden moves anyway, stop and report; regenerate only through its write flag (`ASSETOPS_WRITE_W301_GOLDEN=1`),
never by hand, and put the diff in the packet. Frontend fixtures are hand-edited (they are test data, not goldens).

## 5. Register rows (R610-R613)

- **R610** · IDX-GAPS U2/U3 · mini overview board · D3 honesty · standing. Mock (`v70/outcomes.js:116-124`): no gap
  line. Shown: one note under the rows, "Not available yet · {g} of {n} days have no assessed readings". Reason: the
  board reads 31 days; a day without assessed readings is named, never counted as none.
- **R611** · U3 · `sitefindings` · D3 · standing. Mock: "Findings at this site" lists rows with no day gaps. Shown: on
  a window with days not checked, the claim reads "… on the assessed days", plus the gap paragraph and the day strip.
- **R612** · U3 · Site overview Findings list · D3 · standing. Shown: the `OVERVIEW_PARTIAL` note on a PARTIAL day.
- **R613** · IDX-GAPS §1 · portfolio, findings (estate) · D5 build order · open. Shown: estate Findings over a
  multi-day period keep the all-days rule, so one unassessed day leaves that period Unknown. Reason: the estate read
  does not use the Site index; changing it is a separate slice if the owner wants it.

## 6. Validation tier

| Unit | Focused backend | Frontend |
|---|---|---|
| U1 | `test_idx_gaps_index.py test_s4_finding_index_reach.py test_s4_finding_index_postgres.py test_s4_deferred_match_postgres.py` | — |
| U2 | `test_idx_gaps_board.py test_out_b2_mini.py test_out_b2_vocabulary.py test_out_b1_board.py test_out_b4_read.py test_out_b4_route.py test_out_b4_board_postgres.py test_out_e4_readback_postgres.py test_out_d4_board.py` | — |
| U3 | — | `npx vitest related --run <changed files>`, `npx tsc --noEmit`, `node tools/checks/missing-claim-scan.mjs` |
| U4 | `test_idx_gaps_postgres.py` + the U1 and U2 sets | captures |

`tools\check-all.ps1` at every unit commit. **Merge gate: one full backend run `tools\run-backend-suite-in-container.ps1
-Tier all` on an idle machine (about 41 min; `analytics/` and `site_outcomes/` are shared seams, so `select-tests`
is not used to narrow it), plus one full `npx vitest run`.** Known failures (ignore exactly these): vitest
`src/sites/__tests__/w1f4VerificationStructure.test.tsx` (3 tests, `AssetOpsV1-outA/.agent/OUT-A-packet.md:99-104`);
the `coldWorkCases` "W5-02 K3b … Incident What happened" flake must pass alone. Any other failure blocks.

## 7. Pre-flight (answer in one batch before code, then stop)

- [ ] Worktree on `ca6d7d61b`; `git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'` empty; `.venv` junction.
- [ ] Python `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; PYTHONPATH =
  `<wt>\backend;<wt>\contracts;<wt>\tools;<wt>\simulator;<wt>\gateway;<wt>\host;<wt>\field`
  (`<wt>` = `C:\Users\assef\Bineyame\AssetOpsV1-idxgaps`); `assetops_backend.__file__` resolves to `-idxgaps`.
- [ ] **Never pass `-ExecutionPolicy`** to any script; run guards directly (`.ai/ROLE_CONFIG.md:647`). If the host
  test script is blocked, run pytest directly. `check-all` with `ASSETOPS_GUARD_PYTHON` = that venv.
- [ ] DB names only `assetops_idx_gaps_<x>_test` (or a producer's `<prefix>_audit*`), dropped by the fixture.
- [ ] `.py` files written **without a BOM** (no PowerShell `Out-File`/`Set-Content` for source; use the Edit tool).
- [ ] Serving the app for captures: set `ASSETOPS_WORK_CURSOR_KEY_HEX` and `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX`
  (64 hex chars each) or Work and Portfolio reads refuse.
- [ ] Each anchor opens to its symbol (±15 lines noted, not asked).
- [ ] Record, before code, the v1 board result on `test_out_b4_board_postgres.py` s602b days and
  `test_out_e4_readback_postgres.py` (index status, settled, ACT row). After U2, list every assertion that moves and
  why (expected: R595's "outside this view" Protect entry moves to Cost with F-104 when the board day is CURRENT;
  anything else moving is a stop-and-ask).
- [ ] Vocabulary: `ran running run runs runtime load draft claim candidate necessary binding scenario simulated
  stage fixture cursor projection replay`, case-sensitive `SOC PV PCS`, uppercase codes and `UPPER_UNDERSCORE`
  never on screen.
- [ ] Register: `grep -c "| R61[0-3] " .agent/mock-departure-register.md` is 0 before U4.

## 8. Acceptance

1. Every v1 CURRENT body is unchanged in rows, count, order and pages (T1, all `test_s4_*` CURRENT asserts green).
2. One missing day no longer blanks a 31-day list: PARTIAL, true rows, the day named (T2, P1).
3. A Finding next to an unassessed, pending, failed or stale day is withheld, and its host day is named (T3, T4, P3).
4. A writer change during the read gives no rows (T6, P4); the deferred-match scenarios keep PENDING.
5. The board settles the Finding source on PARTIAL only when its own day is not a gap, and shows the gap line (P5);
   an UNASSESSED body no longer settles as zero.
6. The Findings page and Overview list show PARTIAL rows with the gap days; no zero or proved-empty wording (U3).
7. Portfolio cells for mini follow the board; no Portfolio UI change. Estate Findings unchanged (R613 open).
8. R610-R613 in the register; R595 note added; decision recorded; full `-Tier all` and full vitest green.

## 9. Review points

U1: the `G` rule never lets a row through whose touched days include a gap; v1 paths byte-identical when `G` is
empty; `is_current` false for PARTIAL. U2: `index_settled` uses the board day, not the window; the gap count uses
requested days only; no "Not available yet" text authored in the frontend. U3: no code on screen; PARTIAL zero form
never reuses the proved-empty words; captures at 390/1440. U4: the Postgres cases prove withholding with real
matcher output, not fakes.

## Addendum 1 · pre-flight rulings (Architect: Claude, `.ai/ROLE_CONFIG.md:9`, 2026-10-31)

- **Q1 · accept; an expected move, not a stop.** The s602b board day is UNASSESSED, so v1's "linked finding outside
  this view" was a gap read as zero. v2 shows the existing unsettled text instead. Update (a) `PROTECT` in
  `test_out_e4_readback_postgres.py` to "Verified on test data · Not available yet · linked finding could not be
  loaded", and (b) `test_out_b4_board_postgres.py:402` to `["estate", "finding_index"]`. List both in the packet.
  **Stop condition:** if any row's `state` or any measured outcome on those days changes, stop. Only the suffix, the
  `failed` list and `read_state` may move. Add this to the R595 note: "s602b days now read the unsettled text; the
  Cost-row read-back waits for DEMO-SPARSE SP/CO-3".
- **Q2 · accept.** Outside PARTIAL, `gaps` holds only the G entries (NOT_CURRENT, EDGE_NEXT_TO_GAP) and `withheld` is
  False. WITHHELD_FINDING entries and `withheld = True` occur only on PARTIAL.
- **Q3 · accept.** The token basis `rows` stay as in v1 (all intersecting heads). The basis `days` already carry each
  day's status, so a gap day turning CURRENT changes the token (T7).
- **Q4 · accept.** T1 pins page-by-page row ids, `total_count` and whether `next_cursor` is present, not the cursor
  strings.
- **Q5 · accept.** When no requested day is a gap, the gap is a discovered neighbour day. The Findings page and the
  Overview list then omit the count paragraph. They show the withheld sentence when `withheld`, else
  `OVERVIEW_PARTIAL` (on the Findings page too), and the day strip still renders. `{N}` always means the requested
  days. The board line is already None when `g == 0`.
- **Q6 · confirmed.** `_RANK`'s STALE is `dispatch_read.STALE` = `"STALE_PROJECTION"` (`analytics/dispatch_read.py:34`).
  `UNSETTLED_INDEX_STATUS` must include that literal (U2).
- **DEMO-SPARSE Q1** (the Kobo demo configurations re-timed to install +10/+20/+30 min): accepted with conditions,
  logged in `AssetOpsV1-demo3/.agent/DEMO-SPARSE-preflight.md` "Ruling Q1". It does not touch this slice.

## Addendum 2 · U2 rulings on the s602b result (Architect: Claude, 2026-10-31)

- **Addendum 1 Q1 is withdrawn.** Its premise was wrong: the s602b days read PARTIAL with rows, and the board day is
  not a gap. Do not make edits (a) and (b). `b4:402` stays `["estate"]`. The stop condition is met: all 5 board reads
  keep identical row and outcome states, `failed` lists and `read_state` against a true v1 run (record the comparison
  in the packet).
- **(a) accept.** On board day 11-02 the Cost Earlier list holds exactly one ACT-000001 entry, with the exact detail
  text. The fixtures are deterministic, so the full string is pinned.
- **(b) accept.** Pin PROTECT in its safeguard form ("Reliable service and battery and generator life checked as
  safeguards in ACT-000001"), with the verification href and detail null. Assert that "outside this view" is absent
  on every row.
- **(c) accept, with one widening.** "not realised savings" must appear in the Cost row. Elsewhere it may appear only
  in Assure's verified-results line (R594). Never in Grow or Protect.
- **(d) accept.** R595 → `resolved by IDX-GAPS (<sha>)`: the Cost-row read-back is proven on the s602b board. CO-3
  stays in DEMO-SPARSE's acceptance for the registered combined dataset; that needs no register row.
- **OUT-B4 addendum 6 CO-1 assertions on `two_board_days`** (F-104 under Cost, Protect lists it as checked, Cost
  `must_not_harm` with ACT-000001's link). Restore them in IDX-GAPS only if they pass unmodified, with no product or
  fixture change. Any that do not hold stay dropped: name them in the packet and leave them to DEMO-SPARSE CO-1.
- **Correction (U1 review M1, `.agent/IDX-GAPS-U1-review.md`).** The `touched` snippet in U1 is now inclusive at
  both tolerance bounds: `episode_end >= day_start(d) - TOL` and, symmetrically, `episode_start <= day_end(d) + TOL`.
  This matches `reaches` (`finding_index.py:172-174`) and the matcher's `margin_ok` (`dispatch_v3:418`), which treat
  the exact 20-minute boundary as continuous. Add a test case at exactly `edge - 20 min` and at exactly `edge + 20 min`.

## Addendum 3 · plain Finding titles on the mini board (Architect: Claude, 2026-10-31)

- **(A) accepted; (B) refused**, because a vocabulary hit on screen is never registered away.
- In `site_outcomes/mini.py`, add `FINDING_TITLES` keyed by **lifecycle**, not by the stored title string, copied
  verbatim from `frontend/src/sites/findingWords.ts:11-40` `LIFECYCLE_WORDS[*].title`:
  - SUPPORTED → "Generator support merits review"
  - UNCONFIRMED → "Generator support review: not confirmed"
  - NO_LONGER_SUPPORTED → "Generator support review: no longer supported"
  - MERGED → "Generator support review: joined into an earlier Finding"
  - an unknown lifecycle falls back to "Generator support review", the frontend fallback (`OverviewFindingList.tsx`
    `LIFECYCLE_WORDS[...]?.title ?? "Generator support review"`).
- `_findings` (`mini.py:~485`) uses `FINDING_TITLES.get(r["lifecycle"], FALLBACK)` in place of `r["title"]`. The stored
  title stays untouched in the store and the index wire.
- Test: in `test_out_b2_mini.py`, assert each value occurs as a literal in `findingWords.ts`, the same pattern as the
  `SOURCE_TEXT` equality test. Add the 5 strings to `test_out_b2_vocabulary.py`'s scanned set.
- **Cold and EV need no change.** Their stored titles are already plain (`postgres_finding_store.py:41-42`
  `COLD_TITLES`, `analytics/ev.py:56` `FINDING_TITLE`) and pass the scan. No shared backend mapping exists
  (`estate/evidence_money.py:52` holds only a capability label), so the mini dict is the one place.
