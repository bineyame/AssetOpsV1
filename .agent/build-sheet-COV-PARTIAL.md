# Build sheet COV-PARTIAL · estate coverage on `estate-coverage/2`: partly checked Sites, gap days named

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-31. Owner, verbatim (`.agent/owner-client-demo-sequence-2026-10-31.md`):
"yes to both, go ahead" (decision 2, R613). Code read at main `15eed62c8`. Branch `task/COV-PARTIAL-estate-coverage`
from `15eed62c8`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-covp`. Backend paths are relative to
`backend/assetops_backend/` unless they start with `backend/`, `tools/` or `frontend/`. Effort **2.0 builder days** +
one `-Tier all`. Self-contained; the precedent is `build-sheet-IDX-GAPS.md` (`finding-index/2`).

## 0. Rules that bind every unit

- **Nothing reads as zero or on track.** `PARTIAL` is not in `COVERED` (`estate/coverage.py:30`), so every existing
  consumer treats a partly checked Site as not covered (unit U, no money lines, no estate count claim). No root
  `status` and no Portfolio `status` may be `CURRENT` while any Site is `PARTIAL` (property test X1).
- **PARTIAL replaces UNKNOWN only in one case** (§2). Every other combination returns today's state and today's body
  plus the additive `days` key (regression test T1).
- **No number invented.** Rows of a partly checked Site carry no amount (§2.5); no line, card or total includes it.
- The frontend authors no "not available yet" string (`missing-claim-scan.mjs:36`): it comes from backend `days.text`.
  No state code on screen, in `title` or `aria-label`. Mini-grid live basis only; cold/EV/Actions `days: null`.
- Do not touch `site_outcomes/**`, `analytics/**`, `work/**`, migrations, `field/ gateway/ contracts/ simulator/ host/`.

## 1. Code reality: every reader of Site coverage

| Reader | Where | Treatment |
|---|---|---|
| Mini coverage rule (all-days) | `estate/coverage.py:80-140`; UNKNOWN at `:98-100`, `:119` | **U1**: PARTIAL, `days`, rows from checked days |
| Wire projection `_coverage_site` | `estate/index.py:48-52` (all roots, Portfolio `coverage.sites` and `scope_disclosure.sites[].coverage`) | **U1**: adds `days` |
| Root status `_status` (Findings, Evidence, Financials) | `estate/index.py:31-38` | **U1**: PARTIAL ranks as UNKNOWN (else it would fall through to CURRENT) |
| Unchanged code, PARTIAL read as not covered: `_coverage_state` (`index.py:41-45`); Scope root `coverage_state`/`covered_site_count` (`index.py:356-366`, PARTIAL shown, not counted); Portfolio units (`portfolio.py:61-104`, U); placement (`placement.py:56`, `:135`, R5.6 text); financial lines (`financials.py:414`, none); Evidence rows (`evidence_money.py:258-312`, gap days already UNASSESSED) | — | unchanged |
| Portfolio `status` | `estate/portfolio.py:552-561` | **U2**: new value `PARTIAL` (§3) |
| Board estate port `site_work_rows`, `site_readiness` | `estate/portfolio.py:500-520`, `evidence_money.py:493-508` | one board day: PARTIAL impossible (T10); docstring line only |
| Outcome summary (Portfolio matrix, cards' dots) | `site_outcomes/read.py:384-431` | does not read coverage: unchanged |
| Selection token | `estate/scope.py:194-211` (no `state`, no `days`) | unchanged code; tokens move only through the arrays |
| Frontend words and notices | `portfolioWords.ts:96-158`, `estateShared.tsx:153-185`, `EstateEvidence.tsx:78`, `findingIndex.tsx:114-122`, `:221-262`, `EstatePortfolio.tsx:74`, `:94-107`, `:455-500`, `:607-620` | **U3** |
| Tools/tests asserting a mini week UNKNOWN | `tools/demo_combined_finish.py` `co6` (`-demo3`); builder greps `"UNKNOWN"` in `backend/tests/test_w30*` and `tools/*.py` | listed in pre-flight; §6 |

**Schema call (C1): no schema-version bump.** The frontend accepts estate bodies on the schema string only
(`estateClient.ts:552`) and maps unknown states to fallback words; this slice updates every state map in one commit;
a bump would move six roots and their tests for one additive Site state. The policy is stated on the wire instead
(`days.policy = "estate-coverage/2"`). The w301 golden moves by the added `days` key only (U4).

## 2. The rule (`_mini_grid_basis`, live basis)

1. `days = snapshot.dispatch_days(...)` as today. `gap_days` = days with `not available` or `selection is None`.
   `requested` = number of UTC midnights in `[from_, to)`; if `len(days) != requested` → today's UNKNOWN (C5).
2. Today's flags, with one split: an unselected day sets `gap` (not `unknown`); `unknown` keeps every other cause
   (a selected day whose S3 status is not CURRENT/PENDING/FAILED/STALE).
3. State: historical → today's rule unchanged (`HISTORICAL` if provable and days else UNKNOWN). Live:
   `UNKNOWN if not days or not selected_days or (gap and (unknown or pending or stale)) or unknown`
   `else PENDING if pending else STALE if stale else PARTIAL if gap else CURRENT`.
   So PARTIAL ⇔ ≥ 1 gap day, ≥ 1 selected day, and every selected day would give CURRENT.
4. PARTIAL fields: `match_state` "COMPLETE", `job_state` "SETTLED", `source_freshness` "RECENT" (from the checked
   days; `settled()` still refuses PARTIAL by state), `selection_id` = latest selected day's revision, as today.
5. Rows when `state in COVERED or state == PARTIAL`. For PARTIAL: drop every head whose
   `analytics.finding_index.touched(h, gap_days)` is non-empty (episode end None → `k`, as `_intersects`); call the
   money helper with `withhold=True` (new keyword on `_mini_grid_money`, equal to the `historical` branch `:187-188`:
   a stored PRICED consequence returns `_consequence("UNKNOWN", cid, ...)`, never an amount). Arrays as today.
6. `days` block on every mini-grid coverage (any state); `None` for cold, EV, Actions and `not_applicable()`:
```json
{"policy": "estate-coverage/2", "requested": 7, "checked": 3,
 "gaps": [{"day": "2026-10-26", "state": "UNASSESSED", "reason": "NO_ASSESSED_SELECTION"}],
 "withheld": false, "text": "3 of 7 days checked · 4 days not available yet"}
```
   `gaps` ascending, one entry per gap day (`[]` when none). `text` only when state is PARTIAL, else null:
   `DAYS_CHECKED = "{c} of {n} days checked · {g} {day|days} not available yet"`; when `withheld`, append
   `DAYS_WITHHELD = "; Findings next to those days are not shown yet"` (IDX-GAPS copy).

**Calls (logged):** C2 PARTIAL needs the selected days clean; a gap beside pending/stale work stays UNKNOWN (no
precedence change for any existing case). C3 no EDGE_NEXT_TO_GAP rule: the estate lists stored heads only, a skipped
cluster can only be missing, and a PARTIAL Site never claims a count (F unit U). C4 historical gaps stay UNKNOWN
(no demo need; a standing register row). C5 a day-count mismatch is UNKNOWN, never a computed fraction.
C6 PARTIAL rows carry no amount: the Cost card excludes the Site, so a row amount would be an estate figure from a
period not fully checked.

## 3. Portfolio status (U2)

Per Site in the `_portfolio` loop (`portfolio.py:530-551`): `all_g = all(c == G for c in (f, e, *m))` (the existing
`covered` test) and `partial = cov["state"] == e_cov["state"] == m_cov["state"] == "PARTIAL"`. Then, keeping order:
`EMPTY_SCOPE` → `HISTORICAL` → `PENDING` → **`PARTIAL` when some Site is `partial` and every Site is `all_g` or
`partial`** → `UNKNOWN` when any unit state is not COMPLETE → `CURRENT`. Add `PARTIAL_STATUS = "PARTIAL"`.
Envelope `coverage`, `summary` counts, `evidence_prompt`, value cards: unchanged code (they already read U).

## 4. Units (4). Effort 2.0 d

### U1 · Coverage rule and wire · 0.75 d · per-unit review (shared estate seam)
Files: `estate/coverage.py`, `estate/index.py` (`_status`, `_coverage_site`), `estate/portfolio.py:500-506` docstring.
- `coverage.py`: `PARTIAL = "PARTIAL"`; §2 steps 1-6; `_empty` gains `"days": None`; `not_applicable()` keeps it None.
- `index.py` `_status`: loop `(PENDING, STALE, UNKNOWN)`, then `if PARTIAL in states: return UNKNOWN`, else CURRENT.
  `_coverage_site` adds `"days": cov.get("days")`.
- Tests: new `backend/tests/test_cov_partial.py` (fake snapshot like `test_w301_estate_coverage.py`):
  T1 every existing `test_w301_estate_coverage.py` case returns its old body plus `days` (assert by deleting `days`);
  T2 gap + clean selected days → PARTIAL, `days` exact, text "1 of 2 days checked · 1 day not available yet";
  T3 gap + pending → UNKNOWN; T4 gap + stale → UNKNOWN; T5 all gaps → UNKNOWN, `checked 0`, text null; T6 historical
  + gap → UNKNOWN; T7 head 23:50-23:58 on D with D+1 a gap → withheld, `withheld` true, text suffix; head 08:00 on D
  listed; T8 stored PRICED head on a PARTIAL Site → consequence UNKNOWN with its `source_revision_id`, amounts null;
  T9 `len(days) != requested` → UNKNOWN; T10 one day is never PARTIAL; T11 `_status(False, ["CURRENT", "PARTIAL"])
  == "UNKNOWN"`; T12 cold/EV/Actions `days is None`, otherwise byte-identical.
  Update only the literals in `test_w301_estate_coverage.py` that asserted UNKNOWN for a live gap with clean
  selected days (list each in the packet). Any other test change: stop.

### U2 · Portfolio status and the root audit · 0.5 d
Files: `estate/portfolio.py`, tests.
- §3. Tests (`backend/tests/test_w303_portfolio_reduction.py` or new `test_cov_partial_portfolio.py`, fakes):
  S1 one partial Site + two all-G Sites → `PARTIAL`; S2 partial + a U Site (not partial) → `UNKNOWN`; S3 partial +
  pending → `PENDING`; S4 historical → `HISTORICAL`; S5 only partial Sites → `PARTIAL`; S6 no partial → today.
- **X1 (never on track):** for the Findings, Evidence, Financials, Scope and Portfolio roots over a fake estate with
  one PARTIAL Site: root `status != "CURRENT"`, `covered_site_count`/`covered` excludes it, `summary.finding_count is
  None`, no financial line has that `site_id`, and no row of that Site has a non-null `amount`.
- X2: the Portfolio row of a PARTIAL Site gets `placement` from the not-covered path (R5.6 text, no move).

### U3 · Frontend · 0.5 d · slice review
Files: `frontend/src/estate/estateClient.ts`, `portfolioWords.ts`, `EstatePortfolio.tsx`, `estateShared.tsx`,
`EstateEvidence.tsx`, `findingIndex.tsx`, fixture `__tests__/portfolioFixtures.ts` (+ a PARTIAL variant).
- Types: `EstateSiteState` adds `"PARTIAL"`; `EstateCoverageSite` adds `days: EstateCoverageDays | null` with
  `{policy: string; requested: number; checked: number; gaps: {day: string; state: string; reason: string}[];
  withheld: boolean; text: string | null}`; `EstatePortfolioStatus` adds `"PARTIAL"`.
- Words (exact): `COVERAGE_STATE_WORDS.PARTIAL = "Partly checked"`; `SITE_STATE_WORDS.PARTIAL` and
  `EstateEvidence.tsx:78` PARTIAL = `{ text: "Some days not checked yet", tone: "amber" }`; `contextWords("PARTIAL")`
  = `{ badge: "Some days not checked yet", tone: "amber", sentence: "Portfolio: Partly checked" }`;
  `limitationSentences`: when any Site is PARTIAL push `"Some sites have days not checked yet."` before the coverage line.
- Day names: `gapDayList(days)` = gap days formatted `Intl.DateTimeFormat("en-GB", {day: "numeric", month: "short",
  timeZone: "UTC"})` on `${day}T00:00:00Z`, joined ", " (e.g. "26 Oct, 27 Oct").
- **Portfolio placement (v70 `portfolio.js:43`, context row):** inside `.portfolio-context > div`, after
  `data-portfolio-domains`, one `<span className="portfolio-partial" data-portfolio-partial={site_code}>` per
  `scope_disclosure.sites` entry with `coverage.state === "PARTIAL"`, in Site order:
  `{site_name}: {days.text}` + (`gaps.length <= 7` ? ` · not checked: {gapDayList}` : ` · the days are listed under Assessment scope & periods`).
  It wraps with the row (flex-wrap exists); 1 line at 1440 px for one Site, ≤ 2 at 390 px, no horizontal scroll.
- Scope drawer (`:493-496`): `Mini-grid · Partly checked`, then `<small data-portfolio-scope-gaps>Days not checked yet:
  {gapDayList}</small>` (full list, any length).
- Row consequence: `consequenceFirst` (`EstatePortfolio.tsx:94`) and `consequenceWords` (`findingIndex.tsx:114`): for
  Site/row state PARTIAL return `"Partly checked · " + (source_revision_id === null ? "No consequence recorded" :
  state === "UNPRICED" ? "Unpriced" : "Value withheld")`, before every other branch except PRICED-with-amounts (which
  the backend never sends for PARTIAL). `EV_INCOMPLETE` (`:74`) is EV-only: unchanged.
- Estate Findings (`findingCauseCopy`, `findingIndex.tsx:233-262`): `partial` = coverage Sites with state PARTIAL and
  a scope name; panel (when `total_count === null`) `"{names} {is|are} partly checked; totals are unknown."`; notice
  `"{name}: {days.text}."` per partial Site, in place of the generic `PARTIAL_COVERAGE` line when it is the only cause.
- Vitest (`npx vitest related --run <changed>`): Portfolio PARTIAL badge and sentence; the note text and day list;
  the > 7-gap form; scope drawer row; row "Partly checked · Value withheld"; Findings notice and panel; chips on
  Findings and Evidence; existing snapshots unchanged for non-PARTIAL fixtures; `missing-claim-scan` and the
  vocabulary test green. Every string above was written to pass `productVocabulary.json`; the builder runs the scan
  and stops on a hit.
- Captures 1440/390: Portfolio week (note, open drawer), estate Findings notice.

### U4 · Postgres proof, golden, register, suite · 0.25 d + suite
- New `backend/tests/test_cov_partial_postgres.py` (reuse the w301 estate Postgres fixture helpers; DB
  `assetops_covp_test`): one mini Site, day D assessed and matched with F01 at 08:00-09:00, D+1 without evidence;
  `GET /api/estate/portfolio?from=D&to=D+2d`: Site coverage PARTIAL, `days` = `{requested 2, checked 1, gaps
  [{D+1, UNASSESSED, NO_ASSESSED_SELECTION}], withheld false, text "1 of 2 days checked · 1 day not available yet"}`,
  `status == "PARTIAL"`, F01 in `rows` with no amount; `/api/estate/findings` same window: `status == "UNKNOWN"`, F01
  listed; `/api/estate/financials`: no line for the Site; window `[D, D+1)`: coverage CURRENT, unchanged body.
- Golden: `ASSETOPS_WRITE_W301_GOLDEN=1` regeneration; the diff must be only added `"days"` keys; anything else: stop.
- Register (§7), `.ai/DECISIONS.md` (§8). Parallel with LINK-LINEAGE: no shared product file; merge after it (§5 gate).

## 5. Validation tier

| Unit | Tests |
|---|---|
| U1 | `test_cov_partial.py test_w301_estate_coverage.py test_w301_estate_api.py test_w302_evidence_api.py test_w302_money_api.py` |
| U2 | U1 set + `test_w303_portfolio_reduction.py test_w303_portfolio_api.py test_w303_portfolio_workflow_labels.py test_post_w6_w3_estate_links.py` |
| U3 | `npx vitest related --run <changed files>`, `npx tsc --noEmit`, `node tools/checks/missing-claim-scan.mjs` |
| U4 | `test_cov_partial_postgres.py test_w301_estate_index_postgres.py test_w301_estate_golden_postgres.py test_w303_portfolio_fixture_postgres.py test_w303_portfolio_comparison_postgres.py test_fix01_estate_two_revisions_postgres.py test_out_b4_board_postgres.py` + the U1/U2 sets |

`tools\check-all.ps1` at every commit. **Merge gate: one `-Tier all`** (shared `estate/` seam) on an idle machine,
on the tree that already contains LINK-LINEAGE, plus one full `npx vitest run`. Known failures: w301 estate index
`INVALID_CURSOR` (pre-existing), vitest `w1f4VerificationStructure` (3 tests); the `coldWorkCases` K3b flake passes alone.

## 6. Effect on DEMO-SPARSE CO-6 / CO-6b and R613

- **CO-6 (week S−6d..S+1d)** in `tools/demo_combined_finish.py` `co6`: replace the Kobo UNKNOWN assertions with:
  `kobo["state"] == "PARTIAL"`; `kobo["days"]["gaps"]` days == the computed `unassessed` list; `checked == 7 −
  len(unassessed)`; `text` == the §2 template with those numbers (plus the suffix iff `withheld`); `body["status"] in
  ("PARTIAL", "UNKNOWN")` and `!= "CURRENT"`, recorded; Kobo's day-S Finding in `body["rows"]` unless withheld
  (recorded). Everything else in CO-6 stays. If Kobo reads UNKNOWN, record the cause (a pending/stale checked day).
- **CO-6b (day S):** unchanged (one day: CURRENT); add `kobo["days"]["gaps"] == []`.
- Demo script (Addendum 2 step 4): "partly checked: N of 7 days, the rest named" replaces "Unknown". **R613: resolved** (residual → R621).
- Who edits CO-6: the later of DEMO-A and this slice (LINK-LINEAGE §5 rule). Data unchanged; one `prepare` re-checks it.

## 7. Register rows (R620-R622; all standing)

- **R620** · U3 · portfolio · D3. Mock `v70/portfolio.js:43`: badge and Site counts only. Shown: "Some days not checked yet" badge and one note per partly checked Site. Reason: a gap day is named, never a verdict.
- **R621** · U1 · estate roots · D5. Shown: a historical (earlier cutoff) period with a gap day stays Unknown. Reason: no demo need.
- **R622** · U3 · findings, evidence (estate) · D3. Shown: the "Some days not checked yet" chip and per-Site notice; the mock has no day gaps.

## 8. DECISIONS entry (append verbatim)

Decision: `D-2026-10-31-estate-coverage-v2` (Architect: Claude, build sheet COV-PARTIAL). Owner, verbatim
(`.agent/owner-client-demo-sequence-2026-10-31.md`): "yes to both, go ahead". A live mini-grid Site whose estate period
has at least one day without an assessed selection and whose selected days are all current is PARTIAL, with
`days {requested, checked, gaps[], withheld, text}`; it lists Findings from checked days (withholding any that touch a
gap day) with no amount, contributes no money, count or covered Site, makes every estate root status Unknown and the
Portfolio status Partial (never Current). Any gap beside pending, stale or unknown work, and any historical gap, keeps
Unknown. No schema bump (policy `estate-coverage/2` on the wire). Resolves R613; adds R620-R622.

## 9. Screens this changes (walkthrough) and pre-flight

Changed only on multi-day periods with a gap day: **Portfolio** (badge, note, scope drawer, the Site's ranked rows),
**estate Findings** (four lenses), **estate Evidence**, **Financials** (chip/limitation line). Unchanged: every Site
screen, outcome matrix, category cards, any one-day Portfolio: walk the day-S Portfolio now, the week after merge.
Pre-flight (`.agent/COV-PARTIAL-preflight.md`, one batch, then stop): clean worktree; never `-ExecutionPolicy`; no BOM;
DBs `assetops_covp_<x>_test` only; list each literal asserting a live mini gap period UNKNOWN; confirm `dispatch_days`
returns one entry per requested day.
