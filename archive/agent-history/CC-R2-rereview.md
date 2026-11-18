# CC-R2 re-review (fresh Claude reviewer, 2026-10-28)

Branch `task/CC-R2-placement` at `a6893a8a`. Diffed against `27d7c525` (prior review) for the fixes, and
`71aa1fea..HEAD` for scope. Authority: `.agent/CC-R2-review.md` F1-F4 (with the F3 amendment), and
`.agent/CC-R2-questions.md` Q5/Q6 rulings. Light reruns only: no DB, no browser, no full suite.

## Verdict: ACCEPT-WITH-FIXES

F1-F4 and Q5/Q6 are applied exactly, the F2 pin is tool-only, and the evidence matches the owed list as amended by
Q6. One Medium blocks merge: the visual check that the prior review asked for fails. The Placement group label breaks
mid-word at 1440 px (M1).

## Checks run (by me, at a6893a8a)

- Backend tier 1: the 30 non-Postgres `test_w30*`, `test_cc_*`, `test_s4_finding*` and `test_w40*` files, run with
  the Lane C PYTHONPATH (`-cc2`), the plan2 venv and no DB URL. Result: **441 passed, 15 skipped** (7.7 s).
  `assetops_backend.__file__` resolved to `AssetOpsV1-cc2\backend`.
- `py_compile` passed on `tools/s602b_test_scoped_cases.py` and `tools/s602b_verification_walkthrough.py`.
  `node --check tools/s602b-verification-evidence.mjs` passed.
- Frontend: `npx.cmd vitest run src/estate src/sites/__tests__/coldSiteViews.test.tsx
  src/sites/__tests__/evSiteMoneyRoutes.test.tsx`. Result: **7 files, 158 passed**. That is the 157 from before plus
  the new `showsCustomerMechanismWordsNotRawCodes` test.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv): passed.
  `tools/check-agent-workflow.ps1`: passed.
- **Not run (by dispatch):** tier 2, s602b `prepare` and `capture`, `npm run build`, the full suites. The
  heavy-evidence claims below come from the packet and the committed artifacts. I did not rerun them.

## Rulings applied (verified in the diff `27d7c525..HEAD`)

**F1.** The literal was superseded by Q6. It is now `ESTATE_PORTFOLIO = ...from=2026-10-21...&to=2026-10-22`, at
`tools/s602b_test_scoped_cases.py:51`, and the same window appears in the `.mjs` `portfolioSuite`. Spec Producer 1 is
annotated "Superseded by CC-R2-Q6".

**F2.** `_pin_read_clock` (`tools/s602b_test_scoped_cases.py:224-243`):
- It wraps `read` on both `PostgresEstateRead` and `PostgresEvidenceMoneyRead`, and sets `snap.read_at = pinned`
  before `work`. `EstateSnapshot.read_at` is a plain attribute (`postgres_estate_read.py:104`).
- It is called only from `pinned_app` (`:260`), which is used by `estate_assertions` and `serve`.
- `git grep` finds no reference to it outside `tools/`. `git diff 27d7c525..HEAD -- backend/assetops_backend` touches
  only the `placement.py:26` text. No product module changed, and there is no environment flag.
- The `serve` banner reads "Action clock and estate read time pinned at ..."

**F3.**
- `MECHANISM_WORDS` and `mechanismWords` are at `frontend/src/estate/portfolioWords.ts:218-232`. They have the four
  ruled words, including the amended "Possible extended generator support", the "Mechanism not recorded" fallback,
  and a MOCK DEVIATION comment.
- They are used at `EstatePortfolio.tsx:200`.
- The fixture mechanism is `GENERATOR_SUPPORT_CANDIDATE`.
- The test asserts the four words, the null and unknown fallbacks, and no `[A-Z]+_[A-Z_]+` token in the panel. The
  `.mjs` claim 4 has the same token check.

**F4.** "No end is recorded for this episode" is in `placement.py:26` and in every test literal I checked: the pure
test, the Postgres test, the fixtures, `estatePortfolio.test.tsx` and the spec table.

**Q5.** `test_cc_placement_postgres.py`:
- `EV_UNPRICED` is the exact constant.
- The docstrings are as ruled.
- It asserts `episode_end == "2026-10-06T08:16:00Z"`, `consequence.state == "UNPRICED"` and
  `placement == EV_UNPRICED`.
- Confidence and lens are unchanged.
- The Q-C21 correction is in the spec.

**Q6.**
- The `LABELS["estate"]` text, the `build()` estate branch (`None` Action, plan and outcome, `expect` None, `fake`
  None), the estate print, the docstring edit, and both reads in `estate_assertions` match the ruling literally.
  - Both reads check: CURRENT, no double count, no numeric priority, `next_cursor` null.
  - The 10-21 read checks the eight-fact tuple for F05 and the exact `placement_counts`.
  - The 10-11 read checks for exactly two NEEDS_INVESTIGATION / `EVIDENCE_SOURCE_UNKNOWN` rows, 09:30 then 08:00.
- The walkthrough serve branch prints the Portfolio URL.
- In `casesSuite`, a case with a null `action` calls only `portfolioSuite`. The claims are as ruled.

## Evidence owed before merge (prior list as amended by Q6)

1. **Tier 2.** The packet records 2 passed, 0 failed, 0 skipped, in 102.9 s on `assetops_cc2_test` at `f181d168`.
   That revision differs from HEAD only by evidence files and the packet. No JUnit file is committed, so this is a
   claim I did not rerun.
2. **Prepare.** The packet records rc 0 and all five cases built, with the exact Q6 estate print line. That line is
   printed only after every `estate_assertions` check passes, because a failure raises `SystemExit` first.
3. **Capture.** `results-estate.json` has 20 entries, and all are `ok: true`. Each width has 10:
   - the viewport check;
   - the page loads;
   - one heading, "Needs investigation first · 1";
   - F05 under its heading, with both reason lines;
   - confidence UNKNOWN, "Unconfirmed Finding · Source not resolved", no guarded word and no raw code;
   - the bottom line, and the disclosure closed on load;
   - `noOverflow`, with `wide: []` at both widths;
   - the five policy lines and the footer;
   - the mock loads and renders.

   The six PNGs and the `comparison.md` row are present.

## Screenshot check against v69 `#/portfolio`

What I saw, with the PNGs read and the priority panel cropped at 1440:
- The panel order and grid match the mock: the five cards, the pulse row, the priority table with Objectives and the
  evidence aside, the opportunity panel, "What changed" and the footer.
- The labelled deviations show as described:
  - R502: the group heading row replaces the priority badges.
  - Q3: the subtitle and bottom line.
  - F3: the Finding cell reads "... · Possible extended generator support", with no raw code.
  - The closed "How placement works" disclosure. The policy shot shows it open, with the five lines and the footer.
- At 390 px the table scrolls inside its own scroller, as the mock's does, and the page does not scroll sideways.
- The `comparison.md` heading list leaves out "Evidence that would change a decision" for the app. The panel is
  visibly present in the PNG, so this is how the existing W3-03 aside is marked up, not a CC-R2 change.

## Findings

### Medium

**M1. The Placement group label breaks mid-word at 1440 px ("Needs investigatio / n first").**
- **Where.** `frontend/src/estate/estatePortfolio.css:52` sets `th:nth-child(4){width:9%}`, which is the old Priority
  badge width. `:48` sets `td{overflow-wrap:anywhere}`. The cell is `EstatePortfolio.tsx:211`.
- **What the PNG shows.** In `app-case-estate-portfolio-desktop.png`, the Placement cell is about 60 px wide. The
  `<strong>` label breaks inside "investigation", and the two reason lines stack into about 14 one- or two-word
  lines.
- **Why it matters.**
  - The prior review asked for exactly this visual check: "the Placement column (9%) does not wrap the group label
    awkwardly".
  - The packet records the reason-line wrap as a UI/UX-pass observation but does not mention the broken word.
  - This is a CC-R2 regression on a client-facing surface at the primary desktop width. The mock's column only ever
    held a one-word badge, and R502 put a label plus reasons into it.
  - The scripted claims cannot catch it.
- **Fix.**
  - Stop the label breaking inside a word. For example, set
    `.portfolio-findings td[data-portfolio-placement]{overflow-wrap:normal;word-break:normal}`.
  - Widen column 4 to fit "investigation" plus its padding, about 13%, taking the width from columns 2 and 3.
  - Recapture part `estate` only, at both widths. Then confirm visually that the label wraps at word boundaries and
    that `noOverflow` still passes at 390.
  - If the coordinator prefers to defer this to the post-W6 UI/UX pass, that is an Architect or owner call. It
    should then be registered as a known defect, not left unrecorded.

### Low

**L1. The policy disclosure still says "the episode is open".**
- `frontend/src/estate/portfolioWords.ts:46` (and the `.mjs` `POLICY_LINES`) read "Act now: the episode is open,
  returned or reopened ...".
- F4 established that a null end means "no recorded end", not "open", and changed the reason text to match. The
  policy line still uses "open". The claim is milder in a rule summary, but for a start-failure row it repeats the
  wording F4 removed.
- Suggest that the Architect align it, for example "no end is recorded, it returned or reopened". This is copy, not
  an Implementer gap.

**L2. The app screenshots have a long blank tail.**
- The desktop shots are 1440×5454, with content ending near 1300 px. The narrow shots are 390×3984, with content
  ending near 2800 px.
- The W3-03 Portfolio captures were about 1250-1380 px tall. The mock shot is 1558 px.
- The cause is the capture tool's height calculation (`tools/s602b-verification-evidence.mjs:120-124`, which takes
  the largest inner `scrollHeight`). That code is outside CC-R2's diff.
- It does not affect any claim. I could not confirm, without a browser, whether a page element really reports that
  height. Noted for the capture tool, not for this slice.

## Narrow `site-tabs__link:421` failures (other parts)

- These are outside CC-R2's diff. `git diff --stat 71aa1fea..HEAD` touches:
  - no `frontend/src/shell` file;
  - no shared CSS: the only CSS change is `estatePortfolio.css`, scoped to `.estate-portfolio`;
  - no tab markup. In `frontend/src/sites`, the only change is an import-spacing fix in `MiniScenarios.tsx`.
- `71aa1fea` is an ancestor of `main`.
- The same claim last passed in the W1-UX-06 capture: `.agent/W1-UX-06-evidence/s602b-capture.txt:66`, "narrow
  recommendation ... wide: []", at `9517eb8e`. So the overflow came in on the main lineage after that point. HEAD
  includes W1-F5b's tab-row changes and the later Site-frame commits, for example `427b4ee8` and `b902f95b`.
- I did not reproduce it on main, because the dispatch rules out browser runs. It is pre-existing with respect to
  CC-R2, and it should be raised as a main-lineage defect.

## Residual risk

- Only one placement group is evidenced on a served page, by ruling (Q6). Multi-group rendering (several heading rows,
  ordering, count text) is proven only in jsdom and at tier 2. The served multi-group Portfolio belongs to the demo
  sprint.
- L1 from the prior review still stands: the heading counts span all lenses.
