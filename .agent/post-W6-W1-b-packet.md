# post-W6 W1-mini-Action-b: review packet

**Task:** card W1-mini-Action-b (`.agent/post-W6-audit/fix-slices.md`), as amended by `.agent/post-W6-W1-rulings.md`
(cross-card 1-5, W1-b 30-47, closeout 48-63) and `.agent/post-W6-W1-b-preflight-rulings.md` (1-12).
**Branch:** `task/post-W6-W1-b` (worktree `AssetOpsV1-review7`). Main at W1-a merge 3b4979d0 is merged in (d960eeee).
**Reviewer diff:** `git diff main...HEAD -- ':!.agent'`.
**Product commits:** 3ad08bb5 (unit A), e886124c (unit B), 6e55c0b6 (unit C), 2dbd3351, 9bf2ecdc, 14fa2c2b (guard),
e6af4ff0 (Q23 cap fallback). Register: 62ed43d2, merge d960eeee.
**User review:** none of its own. It merges on independent review ACCEPT (owner-absent / W1 rules); the owner sees it
in the post-W6 walkthrough. R383-R385 are D2 rows waiting for an owner decision.
**Open cap decisions (Architect):** Evidence requirements and the Q37 Action history measurement are over their caps
in synthetic probes, and no fallback is ruled for them. See Caps. No product change was made for either.

## Outcome delivered

Every Q19-Q36 ruling is built as amended. File anchors are in `.agent/post-W6-W1-b-handoff.md` under "What landed".
`.ai/CODE_STATE.md` "post-W6 W1-mini-Action-b" has the summary.

- **Site Findings table:** each row's Domain cell links "Dispatch" for that row's day. A revision is added only when
  the ID is proved to be a 15-minute interval revision (pre-flight 2). The renewable helper link is live.
- **Financials:**
  - Portfolio roll-up goes to `/financials`.
  - "Inspect technical basis" goes to the Dispatch analysis for that day only (pre-flight 1).
  - The assumptions form has a "Return to financial overview" footer.
- **Interpretation history:**
  - Three compact rows; "Previous versions", "Next versions" and "Back to newest" follow a cursor stack in the URL.
  - Each row has a "Show this version" disclosure.
  - Price versions sit in a closed disclosure.
  - New this round: the version table sits in one focusable scroll region (Q23 fallback, see Caps).
- **Rail:** Findings is active on Finding detail paths and Actions on Action detail paths. Navigation guard fixtures
  cover this.
- **Frames:**
  - Recommendation and the five Action views have no Site tabs.
  - Finding overview, Analysis, Evidence and History keep the tabs with one `MOCK DEVIATION D2 (R383)` line.
  - Action views have "Open site", the `/overview` alias and the ruled unknown-section body.
  - The Action subtitle suffix appears only for a valid Action code.
  - The obsolete Analysis helper is removed.
- **Action history:**
  - RESOLVED and RESOLUTION_WITHDRAWN have their own words.
  - Resolution events are deduplicated, and counts come from the deduplicated union.
  - The "Latest at read time" chip shows; "Show all" appears only past three entries.
- **Verification:**
  - Available chips are blue (info).
  - The source is named once.
  - Plan row headings use the scoped normal weight.
  - A selection conflict uses the ruled note; the history gap shows only when it differs.
- **Sitework (mini only):** "Manage in Actions" links to Site `/actions`.

## Merge with W1-a (d960eeee)

- **Register conflict:** W1-b keeps R383-R385; W1-a's R386-R395 are kept as they are. There are no duplicate IDs.
- **R395 overlap:** W1-a's R395 records the same departure as R383 (Finding Site tabs). R383 is the pre-flight ruling 3
  row: it adds finding-analysis and the visible label. R395 is now marked "superseded by R383" and kept for
  traceability. **Reviewer:** confirm this disposition.
- **`SiteAnalyticsFrames.tsx` conflict:** resolved to W1-b's version: tabs are removed on Recommendation, and the R383
  label sits under the retained row. The comment names R395 as superseded.
- `siteDetailRoute.test.tsx` is now green; W1-a flipped its crumb assertion.

## Acceptance (rulings) status

| Ruling | Status | Proof |
|---|---|---|
| Q19/Q20 (pre-flight 2) | done | s404SiteFindingIndex; sitefindings captures |
| Q21/Q22 (pre-flight 1) | done | siteFinancials (day-only, proved interval, absent window); financials captures |
| Q23 (pre-flight 7) | done + fallback | siteFinancials Q23 paging and region tests; viewer clicks; probe within caps |
| Q24 | done | siteFinancials; assumptions captures |
| Q25 (pre-flight 6) | done | operatorRailInventory, navigation guard fixtures; rail checked on 142 pairs |
| Q26/Q52 (pre-flight 3) | done | frame tests; captures: R383 once under the tabs on finding/evidence/history, none elsewhere |
| Q27, Q33 (pre-flight 4, 9) | done | siteAction; extra captures of the unknown section and `/overview` |
| Q28 | done | miniDecisions |
| Q29/Q30 (pre-flight 5) | done | siteAction; withdrawn capture; Show all viewer clicks |
| Q31/Q32/Q34 (pre-flight 8, 11) | done | siteActionVerification, w1f4VerificationStructure; action-plan/evidence/verification captures |
| Q35 | done | siteAction pending/unknown/loaded |
| Q36 (pre-flight 10) | done | siteWorkActions (mini link; cold and EV unchanged); sitework captures |
| Q46 | done | R384/R385 rows and labels |
| Q37/Q38/Q42 caps | partly open | see Caps |

## Captures (`.agent/post-W6-W1-b-recapture/`)

- **142 of 142 pairs captured at 1440 and 390:** 118 indexed W1-b pairs and 24 Q40 representatives.
  - Two agents captured them, with reviewed producers run unmodified.
  - SHA d960eeee/2af5fef6. The product tree is the same at both; 2af5fef6 adds only `.agent` files.
  - Per-batch `run.md` files list the producers, DBs and ports.
- **After the Q23 fix (e6af4ff0):** the 12 `assumptions` pairs and the cold/EV assumptions reps were recaptured
  (16/16, in `*-fix` folders). Heights are unchanged.
- **Every pair:**
  - Titles match the frozen titles; horizontal page overflow is 0; there are no console errors.
  - The tab, R383 and rail checks had no failures (72 Action/Recommendation measurements, plus all Finding reps).
- **Batch 15 (cold-action):** w502 hard-codes ports 8971-8977. It was captured after confirming all seven were free.
- **Extras:**
  - The s602b `withdrawn` case is captured: RESOLUTION_WITHDRAWN is producible, so there is **no producer gap**.
  - The unknown Action section and the `/overview` alias are captured for s601b.
- **Viewer clicks** (`viewer-clicks-A.md` and `-B.md`; read-only; the URL and result are logged):
  - Previous/Next versions and Back to newest on s405, and on s408 default, T1, T3 and T3-page2. Every state is within
    cap.
  - Show all on s601b `all`: 355 → 506 at 1440, 451 → 572 at 390.
  - Show all on the withdrawn history: 312 → 428 at 1440, 609 → 700 at 390.

## Caps

Heights are of the closed panel in px. "Synthetic" is the labelled DOM probe on the real mounted page (W3 closeout
ruling 1). Every synthetic run asserted `verified` (all rows and every intended field changed to 160 characters). Probe
records are in `probe/probe-A.md` and `probe/probe-B.md`.

| Panel | Cap 1440/390 | Real max 1440/390 | Synthetic 1440/390 | Result |
|---|---|---|---|---|
| Interpretation history | 800 / 1400 | 681 / 1068 | before the fix: 729/1713 (3 rows), 1028/2572 (5 rows); after the fix: 749/1312 (3 and 5 rows) | **pass after the ruled fallback** (pre-flight 7: internal scroll) |
| Trade-offs and exclusions | – / 450 | 393 / 413 | 410 / 446 | pass (4 px margin) |
| Evidence requirements | 450 / 800 | 396 / 605 | 458 / 956 | **exceeded; no ruled fallback; stopped** |
| Action history (Q37) | – / 800 | 362 / 501 (expanded: 506/572; withdrawn 428/700) | five 160-char meanings: 558/963 | **exceeded at 390; no ruled fallback; stopped** |

**Intended fields:**
- **Interpretation history:** the Fuel price and Recorded amount cells. The Status badge and change line can only hold
  fixed words, so they stayed real.
- **Trade-offs:** the gap line and the allowance line. The two paragraphs are fixed copy.
  - An earlier five-item probe gave 550 at 390. It replaced fixed copy, so it is superseded.
- **Evidence requirements:** the 7 detail texts in the 4 fixed rows. The table can only have those four rows, so the
  first five-row probe (521/1114) is superseded.
  - These details are built from counts and minutes, so a 160-character value is a conservative upper bound.
- **Action history:** the meaning sentence; reference codes kept.
  - Context runs: the default three rows with 160-character meanings measure 408/566. Six real expanded rows with
    160-character meanings measure 612/649; at 390 that table is 1006 px wide and scrolls sideways.
  - The 963 comes from five clones in the narrow (461/318) table, where the meaning column wraps the most.

**Fallback detail:**
- The version table scrolls in a region with role=region, label "Fuel cost versions" and tabIndex 0.
- The region's maximum height is 480 px at 1440 and 900 px at ≤640 px, so the closed panel stays under its cap.
- A cue appears only on overflow. On real data nothing overflows and the cue stays hidden.
- With every disclosure open the panel measures 1636/2531. That state is exempt from the cap, and nothing is clipped.
- Two tests cover the region (component and stylesheet). Each fails when its file is reverted to e6af4ff0^.

**Not capped (Q37):** the Finding header on the late-stale rep is 59/91.

## Checks

| Check | Revision | Result |
|---|---|---|
| Focused files after the merge (24 files, including siteDetailRoute) | d960eeee | 749/749 pass |
| `siteFinancials.test.tsx` after the fix | e6af4ff0 | 95/95 pass |
| Revert proofs for the fallback | e6af4ff0 | 1 test fails with `ConsequenceHistory.tsx` reverted, and 1 with `w1ux02-money.css` reverted |
| Full vitest, once (log in the scratchpad) | cb87309a, product = e6af4ff0 | 129 files, 3123/3124 (see the note below) |
| `npm run build` (tsc + vite build) | cb87309a | exit 0 |
| `tools/check-all.ps1` | d960eeee and cb87309a | 11/11 guards pass |

- **The one full-vitest failure:** `evEnergy.test.tsx` "energy_states_table_loading" timed out (`the store read has
  not settled`). It also failed once on an isolated rerun right after the full suite, then passed 4 times out of 4. It
  passes on main 3b4979d0. W1-b does not touch EV Energy, so this looks like a load-sensitive timeout, not a
  regression.
- No backend suite was run; this is a frontend-only slice, and none was requested.

## Known deviations

- R395 is marked superseded by R383 (see Merge). This is a register disposition made by the builder.
- Two caps are over, with no ruled fallback: Evidence requirements (458 against 450 at 1440, 956 against 800 at 390)
  and Action history Q37 (963 against 800 at 390). These need an Architect decision. Possible remedies, none of them
  applied: an internal scroll region like Q23, a wider meaning column at 390, or a cap amendment based on the realistic
  maximum detail lengths.
- The handoff's "Choices where the rulings were silent" still stand:
  - The R383 label also shows on the unknown Finding section state.
  - Paging links carry the limit explicitly.
  - Unknown events read "Recorded event".
  - Evidence row headings are unchanged (Q31 scope).

## Residual risk

- The `evEnergy` timeout is flaky under load.
- Trade-offs has a 4 px margin at 390.
- Capture tooling left `.venv` (a junction to the main venv) and `var/sites/kobo-001.yaml` in review7. Both are
  gitignored.
- The D3 dispositions for R197-R230 follow review.

## User-review focus

- In the post-W6 walkthrough:
  - The R383 line on the Finding views.
  - Action history counts and Show all.
  - Interpretation history paging and the scroll cue.
- Owner decisions are pending for the R383, R384 and R385 D2 rows.
