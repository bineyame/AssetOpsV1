# W5-02b part 1 (K2a + K2b) re-review after fix rounds

Reviewer: fresh Claude reviewer. I did not author the slice or the fixes. Worktree `AssetOpsV1-review3`, branch
`task/W5-02b-cold-site-screens`, head `653fdbf3`. Fix diff `922eaa00..HEAD` outside `.agent`: nine `frontend/src`
files, `tools/w502-cold-work-evidence.mjs`, `tools/w502_cold_work_walkthrough.py` and `.ai/MILESTONE_REVIEW_BACKLOG.md`.
The backend is untouched.
Binding inputs: `.agent/W5-02b-K2-rulings.md` rulings 1-24 (24 is final), `.agent/W5-02-build-spec.md`, register rows
R88-R91, `.agent/W5-02b-phase-handoff.md`, and the evidence `.agent/W5-02b-evidence/` (capture `83c3e1c3` plus the
ruling-24 README section). I compared against v69 using `.agent/W5-02-04-mock-shots/`.

## Verdict: ACCEPT

Every original finding and every ruling is closed as stated. The fix rounds add no implementer decision and no
unlabelled mock departure. The ruling-24 re-evaluation is exact. The stored JSON does not need to be regenerated
before merge.

Counts: **High 0, Medium 0, Low 2.** Neither Low blocks merge.

## Checks run (this review, head 653fdbf3)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| Targeted vitest `--maxWorkers=1 --minWorkers=1`: `coldWorkActions`, `siteWorkActions`, `siteWorkCases`, `w1f4ChangesWorkStructure`, `test/__tests__/panelStructure` | 5 files, 99 passed, 0 failed |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| Stored `w502b-measurements.json`, re-filtered by me in node | 463 claims. Exactly two fail: `desktop worstcase-expanded-open: panel <= 650` and `narrow worstcase-expanded-open: panel <= 850`. Removing them leaves 461 claims with 0 failing |
| `git diff 4cac402a..HEAD -- frontend tools backend` | Only `tools/w502-cold-work-evidence.mjs` changed (+5/-3, the `panelCap` parameter). `git diff 1d7e2b39..HEAD` on the producer is empty |

Not run, as the brief requires (a full backend suite is running): Postgres tests, full vitest, `vite build`, browser
captures and `check-all.ps1`. For those I rely on the implementer's batch at frontend `4cac402a`:
- full vitest: 119 files, 2808 passed;
- `vite build` green;
- `check-all`: 11/11;
- focused Postgres `test_w502_*.py`: 34/34 at `1d7e2b39`.

The diffs above show that `4cac402a` frontend and `1d7e2b39` producer are byte-identical to the head, so that evidence
applies to this revision. I have not verified the build or the full vitest numbers myself.

## Closure of the original findings

| Finding | Status | Evidence |
|---|---|---|
| H1 desktop never wraps | Closed | See the H1 notes below |
| H2.1 sticky header colour | Closed | `w1f4-changes-work.css` sets `.w1f4-changes-work.cold-work-actions .data-table thead th:first-child { background: var(--surface-sunken) }`, the same token as the rest of `.data-table thead th` (`primitives.css:569-572`). `w502b-desktop-positive.png` shows a uniform grey header row, as in `mock-cold-work-1440.png` |
| H2.2 notice icon on its own line | Closed | Scoped flex rule on the four notice data-attributes. The notice is 42 px at 1440 in every state, which is the mock's 42 px |
| H2.3 `Open site` bare link | Closed | `SiteAnalyticsFrames.tsx:1417` has `className="button"`, with a ruling-18 test. `w502b-desktop-action-positive.png` matches `mock-cold-action-1440.png` |
| M1 range control (Q6) | Closed by rulings 1, 22 and 23 | See the M1 notes below |
| M2 INC `occurred_at` and links | Closed by rulings 4 and 21 | See the M2 notes below |
| L1 duplicate sticky CSS | Closed | `ColdRows` uses `DataTable stickyFirstColumn`. The local sticky positioning is gone |
| L2 `links.work` keys | Closed | `domainActionClient.ts:296` checks that all seven keys are nullable strings, with a malformed-key test |
| L3 bare-address probe | Closed by ruling 8 | Tests cover a W1 ID on `/verification` (not found) and a 503 probe on a bare address (W1 presenter kept at the original address) |
| L4 503 capture | Closed by ruling 3 | The `unavailable` process serves the healthy positive DB, and only the domain-work router gets `W502B_DOMAIN_WORK_DB_URL`. `attest` checks `site_read_http: 200`. The `cold-work-503` capture passes 11/11 at each width. The legacy `unavailable-503` images are labelled as a separate Site refusal |
| L5 access seam | Closed by ruling 6 | A backlog entry was added to `.ai/MILESTONE_REVIEW_BACKLOG.md` |
| L6 vocabulary exclusion | Closed by ruling 14 | The exclusion is narrowed to the exact literal |

**H1 notes:**
- The cold cell rule is now `.w1f4-changes-work.cold-work-actions .panel .data-table td` (0,4,1), which beats the W1
  nowrap rule (0,3,1). The Due and State nowrap exceptions are raised to the same specificity.
- New per-cell claims test containment, the preview line count and the opened body. They pass in every state with rows,
  at both widths.
- In `w502b-desktop-worstcase-disclosure.png` the preview wraps to two lines with an ellipsis, and the opened body stays
  inside the 340 px Action cell.

**M1 notes:**
- `ColdWorkWindow` sits after the subtabs and before the strip on all three cold subtabs.
- `Apply` keeps `known_at`, drops the cursor and reads page one. Invalid input makes no read.
- Cold Incidents and Maintenance drop the W4 form (`windowForm={site.site_type !== "COLDCHAIN"}`). MINIGRID and EV keep
  it, and a MINIGRID test covers this.
- Captures `window-apply`, `window-invalid`, `cold-incidents` and `cold-maintenance` pass at both widths.

**M2 notes:**
- The producer asserts `D+16h` alignment, INC < WR < record inside the hour, and that the stored `occurred_at` and
  links equal the intended ones.
- UNKNOWN has exactly one `COLD_START_FAILURE` link plus a `limit`.
- `cold-incidents` shows `22 Oct · from 19:11` and `Finding 1b0f5635 · Finding 82ba2f4c`. 19:11 is D+16h11m at UTC+3.

## Ruling-by-ruling verification

| Ruling | Verified |
|---|---|
| 1, 22 | Placement, labels (`From (UTC)`, `To (UTC, exclusive)`, `Apply`) and the `INVALID_WINDOW` literal match. The control is right-aligned at 1440 and full width at 390 (claims pass; seen in the 1440 and 390 positive captures). It uses the existing `.site-date-bar` chrome slot, so `expectV69Panels("cold-work")` still holds. Labelled R88 in code and CSS |
| 2, 20, 24 | Caps are 650/850 for the panel and 1600/2000 for the page. The all-open state is exempt only from the panel cap, through `capWork(..., panelCap=false)`. The page cap, no-overflow, containment, preview and badge claims are kept |
| 3 | Done, as in L4 above. No product router changed |
| 4, 21 | Done, as in M2 above |
| 5 | The producer selects only `generator-1`. R89 is cited. The K3a Asset cell is not in scope |
| 6 | Backlog entry present |
| 7 | Comment and test pin `{detail:{code,message,intent:null,results:null}}` |
| 8 | Route-form tests present |
| 9 | `COLD_WORK_SUBTITLE_FALLBACK` is always used, with a test that the Foundation `summary` text is absent. Labelled R90 |
| 10, 11, 12 | Untitled placeholder panel plus the blue notice. `— actions` and `Actions (—)`. The `Finding version` summary stays on one line (nowrap rule) |
| 13 | Only `.work-cases-clamp` hides overflow. The opened body wraps |
| 15 | `SCREEN_LEADING` admits `[data-cold-work-currentness]` only on `cold-work`. It must directly precede panel 1 and directly follow `.status-strip`. Tests cover both admission and rejection |
| 16 | Tones are tested. `Show the first 4` is absent from the cold list. Line 455 is the W1/mini list, which is unchanged |
| 17 | `K0 < raised <= db_now` is asserted. The long Actions are each later than the fixture Action |
| 18, 19 | Done, as in H2.3 and L1/L2 above |
| 23 | Done, as in M1 above |

Labels: R88, R90 and R91 appear at their code sites (`SiteWorkActions.tsx:619,850`, `SiteAnalyticsFrames.tsx:1896,2087`,
`SiteFoundationChange.tsx:103`, `coldWorkPresentation.ts:35,91`, `w1f4-changes-work.css:346`, `panelStructure.ts:64`).
R89 is cited in the producer. Its K3a Asset cell does not exist yet. All four register rows are present
(`mock-departure-register.md:148-151`).

I found no new unlabelled departure. The remaining visible differences from v69 are each already ruled:
- `Scoped to Cold` short name;
- the narrow table scrolling inside its panel, with a sticky first column;
- the interim Sites rail (R69);
- `Finding {id8}` sources (R65/R66);
- subtab counts `(—)` on the not-yet-built K3 case tabs.

## Ruling-24 re-evaluation: sound; the README record is enough

- **The removed claims are exactly the exempt ones.** The stored JSON has 463 claims. The only failures are the two
  `worstcase-expanded-open` panel-cap claims, which ruling 24 exempts. Every other all-open claim passes at both widths:
  - no document overflow (1425/1425 and 390/390);
  - page main 1203 ≤ 1600 and 1629 ≤ 2000;
  - cell containment and opened-body containment;
  - one-line summaries and codes;
  - sticky first column;
  - badges.
- **The tool change matches.** Comparing the tool with its capture-time version (`83c3e1c3..HEAD`), the only change is
  that one claim is no longer emitted, for that one state.
- **The stored JSON does not need to be regenerated before merge.** Reasons:
  1. The rendered code (frontend `4cac402a`) and the producer (`1d7e2b39`) are byte-identical to the head. A recapture
     would measure the same DOM.
  2. No guard or tool reads `w502b-measurements.json` except the capture tool, which writes it.
  3. The README states that the JSON still says `failed: 2` and why.

  The next capture run regenerates it (K3b reuses this tool). That is the natural point. No separate run is needed.

## Code quality of the named changes

**Ruling 20, `LongText` (`SiteWorkActions.tsx:672`): sound.**
- Hooks run before the `!long` early return.
- The preview slot and the `Disclosure` keep stable child positions, so the `<details>` element is not remounted and
  keeps its open state.
- React's unchanged `open={false}` prop does not reset it.
- The `toggle` listener is in the capture phase, because `toggle` does not bubble. The
  `details.parentElement === el` filter stops a nested `Finding version` disclosure from flipping the state.
- The opened body renders `children ?? text`, so the Action link stays reachable once. The test checks a single link and
  a single occurrence.
- The shared `Disclosure` is unchanged.

**Ruling 23, `windowForm` prop (`siteWorkCases.tsx:66,737,759`): sound.**
- It defaults to `true`. With `false`, only `actions` becomes `undefined`.
- The single caller passes `site.site_type !== "COLDCHAIN"`, so MINIGRID and EV are unchanged.
- A test proves MINIGRID still has the in-panel form inside `section.panel` and makes no domain read.

**`panelCap` parameter (`w502-cold-work-evidence.mjs:288-295`): sound and minimal.**
- The default is `true`.
- Only the all-open call passes `false`, and it cites ruling 24 there.

**Producer attest enforcement (`w502_cold_work_walkthrough.py:600-646`): sound for every mode that has reads.**
- It fails on a `blocked` mode.
- It fails on a link set other than the ruled one.
- It fails when the limit is missing (UNKNOWN) or present (other modes).
- It fails when the 503 process's Site read is not 200.
- Prepare also asserts the stored row. See Low 2 for the one gap.

## Findings

### Low

**Low 1. One window error message covers every invalid input, including `from >= to` and an empty field.**
- Where:
  - `domainActionClient.ts:350-351` (`invalidScope`), used by `ColdWorkWindow` at `SiteWorkActions.tsx:631-638`;
  - the capture pins it at `tools/w502-cold-work-evidence.mjs:457`, where `from = to` expects
    `The window may span at most 31 days.`
- What is wrong: a user who picks the same day twice, or a reversed range, is told the window may span at most 31 days.
  That does not describe what they did wrong.
- Why it is Low: ruling 22 confirms "the client's existing `INVALID_WINDOW` message", and that message is one literal,
  so the build matches the ruling. It is a plain-language copy issue, not an acceptance gap.
- Fix: in the W1-conclusion plain-language pass, or by an Architect literal, use one message per failed rule (or a
  neutral `Choose a start date before the end date, at most 31 days apart.`). Update the capture claim to match.

**Low 2. `attest` passes a mode that has no reads.**
- Where: `tools/w502_cold_work_walkthrough.py:604-606`.
- What is wrong: when prepare fails for a mode (`modes[m] = {"blocked": "prepare failed: ..."}` at `:515`), `attest`
  prints `BLOCKED` and `continue`s without adding a failure. `ATTEST OK` can then print with a mode missing. This
  behaviour predates the fixes, but ruling 21 now means no mode is expected to be blocked.
- Why it is Low: the capture tool's manifest claims (`!manifest.modes[k].blocked`) would still fail. The capture of
  record shows every mode not blocked, so the evidence is unaffected.
- Fix: add `failures.append(f"{m}: no reads ({doc.get('blocked')})")` before the `continue`.

## Residual risk not named in the packet

- **Shared sticky-header colour.** `DataTable stickyFirstColumn` (`primitives.css:5406-5412`) still paints the sticky
  header cell `--surface-raised` (white) for every consumer. K2 corrects it only under `.cold-work-actions`. Any other
  consumer, such as the W5-03a EV E2 screens, shows the same white header cell that H2.1 found. That belongs in the
  primitive. It is out of K2 scope.
- **Opened-disclosure interaction (owner walkthrough note, not a finding).** With the ruling-20 behaviour, the native
  `<summary>` `Read full text` moves from below the preview to above the opened value, and its label does not change
  while open. This is native `<details>` behaviour, and the mock specifies no disclosure. Raise it at the owner
  walkthrough if it reads oddly.
- **Window control at 390.** The full-width control adds about 140 px above the strip at 390. This is within the
  page caps and is the ruled R88 placement. It is one more item for the future shared-topbar candidate.
