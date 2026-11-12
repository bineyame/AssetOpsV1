# Architect: one sequenced view of walkthrough comments and backlog, for the client-demo scope (2026-11-11)

## Revision 6 (Architect, Claude, 2026-11-12): UQ-FI, a first-impression UI pass for 17 Nov

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude (since 2026-10-27).
- Owner, verbatim (`.agent/owner-ui-first-impression-2026-11-12.md`): "option 1, show me the design sheet after the demo". Option 1 = UQ-1-level type, spacing and Inter across the app, plus one headline per demo page and repeated "not available" lines collapsed to one per section; own lane from Fri; starts only after the owner approves the parked v7.2 sheet; held whole if not ACCEPTed by Sat 20:00.
- Supersedes revision 3's "UQ-1 out" line for this subset only. UQ-0's other parts, UQ-2 (dark), UQ-3, UQ-4 and UQ-5..8 stay in the backlog (BL-69). Rulings **D-UQFI.1-5** below, logged for owner review.
- Basis: `.agent/architect-answer-ui-quality-2026-11-10.md` problems 1-3 (type, no headline, honesty wording crowding the page). Problems 4 (charts) and 5 (i18n) are not touched.

### 6.1 Scope: UQ-FI, 1.9 units (D-UQFI.1)

| Card | What | Units |
|---|---|---|
| UQ-FI-0 | One extra panel on the v7.2 sheet, "One headline, one gap line per section": a before/after of the Kobo Finding header and the Cold board's empty lower half, drawn from today's words. Optional; only if it can reach the owner with the sheet tonight | 0.1 |
| UQ-FI-1 | (a) Tokens across the whole app: the 8-step type scale, a 12 px floor, 14 px body, Inter self-hosted, tabular figures, the 4 px spacing scale (tokens defined; snapped only on demo-path files); every raw `font-size` in `frontend/src` moved onto the scale by a committed codemod; the style ratchet | 0.9 |
| UQ-FI-2 | (b) Demo-path pages only: one headline per page; repeated gap lines collapsed to one per section through one shared component | 0.7 |
| Evidence | Before/after captures of every demo-path page at 1440 and 1280 px, with measurements; packet | 0.2 |
| **Total** | | **1.9** (1.8 without UQ-FI-0) |

**Rules that bound it:**
- Light theme only (today's colours). English only.
- No layout restructure: no grid, column or panel moves, no new panels, tabs or controls, no new charts, no new words. Two moves only: the headline element goes first in its page header, and a section's repeated gap lines become one line.
- Gap wording keeps D-E5.46: the fact is stated once per section, with every subject it applies to named; never hidden, softened, re-worded or merged across different facts.
- Tables, the Portfolio outcome matrix and tab rows are out of the collapse: each cell and each "Label · Not available yet" tab keeps its own words (collapsing them would change layout).

**Demo-path pages (from DS-1f `demo-script-client.html` checklist and DS-1b; both are on branch `task/DS-1f-fill`, not on main):**

| # | Page (frame) | Script step | Headline (existing text, moved first; nothing new) |
|---|---|---|---|
| P1 | Portfolio, all tabs (`EstatePortfolioFrame`) | 0, 1 | page title "Portfolio" + its existing subtitle sentence |
| P2 | Site board / Overview, Kobo, Cold room, EV depot, Kisiwa (Site board frame under `SiteDetailFrame`) | 2, 3, 3b, 4, 5, K, 7 | Site name + the board's day line |
| P3 | Finding detail: Kobo generator, Kisiwa unexplained fuel (incl. `SiteFuelFindingFrame`) | 2, K | the Finding's title (what happened), then its first sentence; the "Priority · Confidence · Earlier version n of m" line moves under them |
| P4 | Verification ("check") pages: Kobo ACT-001, Kisiwa ACT-004 (`SiteMillVerificationFrame`, `SiteFuelVerificationFrame`, or the action verification frame the pre-flight confirms) | 2, K | the page title; the verdict chip stays in the header |
| P5 | Daytime solar opportunity page | 3 | "Daytime solar unused at Kobo mini-grid" |
| P6 | Findings index, all lenses and the Opportunities tab (`EstateFindingsFrame`); Kisiwa Site Findings | 3, 6, K | "Findings across the estate" / the Site Findings title |
| P7 | Kisiwa Fuel night page; Kisiwa Service page; Operational records (live dip) | K | each page's title |
| P8 | Maintenance (optional step 4); Site price page (PR-2a/PR-3, if merged; demo beat 5.4 #10) | 4, price beat | page title; tokens only, no collapse work on the price page |

### 6.2 What the owner approves on the v7.2 sheet for UQ-FI (the coordinator presents these, in plain words)

1. **Inter** becomes the app's font, stored with the app (no internet needed), with the computer's own font as fallback; numbers in tables and money line up (tabular figures).
2. **Type sizes:** one scale of 8 sizes (12, 13, 14, 16, 18, 20, 24, 30 px); nothing smaller than 12 px; normal text 14 px.
3. **Headings:** page titles 24 px (today 27), section titles 16 px (today 15). Table text 13 px with 12 px column heads, and table rows keep today's height; the sheet's taller 44 px rows come after 17 Nov.
4. **Spacing:** the sheet's 4 px spacing steps, applied to the demo pages only.
5. **Colours stay as today, light theme only.**
6. **Left menu:** same items and order; group names 12 px (today 9 px), items 13 px.
7. **Not on the sheet, approved as a rule (or from the UQ-FI-0 panel):** one headline per demo page, and a repeated "not available / not assessed / no assessment" line said once per section, naming everything it applies to. You see the before/after pictures on Saturday.
8. **Not for 17 Nov (after the demo, from the same sheet):** the dark theme and the System/Light/Dark switch, the new colour palette, the reading-state colours and symbols, the outcome-category colours, new corners and shadows, the one-figure outcome card, taller table rows, and the French and Swahili samples.

### 6.3 Technical design (builders do not design)

**D-UQFI.2 Type scale and mapping.**
- New file `frontend/src/ui/fonts.css`, imported in `main.tsx` **before** `ui/tokens.css`:
  - `@font-face { font-family: "Inter"; src: url("/fonts/InterVariable.woff2") format("woff2-variations"), url("/fonts/InterVariable.woff2") format("woff2"); font-weight: 100 900; font-style: normal; font-display: swap; }`.
  - Files: `frontend/public/fonts/InterVariable.woff2` and `frontend/public/fonts/OFL.txt`, from the rsms/inter v4.1 GitHub release zip (fetched on the VPS). The packet records the release URL and the SHA-256 of both files. No CDN at runtime, no npm dependency.
- `ui/tokens.css`, primitive tier (new):
  - `--font-size-100: 0.75rem` (12), `-200: 0.8125rem` (13), `-300: 0.875rem` (14), `-400: 1rem` (16), `-500: 1.125rem` (18), `-600: 1.25rem` (20), `-700: 1.5rem` (24), `-800: 1.875rem` (30).
  - `--space-1: 4px` … `--space-2: 8px`, `-3: 12px`, `-4: 16px`, `-5: 20px`, `-6: 24px`, `-8: 32px`, `-10: 40px`, `-12: 48px`, `-16: 64px`.
  - `--font-sans: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif;` `--font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;` `--leading-body: 1.5`.
- Existing role tokens are **re-pointed, not renamed** (no call-site churn):

| Token | Today | UQ-FI |
|---|---|---|
| `--text-xs` | 11 | `--font-size-100` (12) |
| `--text-sm` | 13 | `--font-size-200` (13) |
| `--text-base` | 14 | `--font-size-300` (14) |
| `--text-lg` | 17 | `--font-size-400` (16) |
| `--text-xl` | 22 | `--font-size-600` (20) |
| `--text-2xl` | 28 | `--font-size-700` (24) |
| `--text-page-title` | 27 | `--font-size-700` (24) |
| `--text-panel-title` | 15 | `--font-size-400` (16) |
| `--text-subsection-title` | 13 | `--font-size-300` (14) |
| `--text-panel-note` | 11 | `--font-size-200` (13) |
| `--text-table` | 11 | `--font-size-200` (13) |
| `--text-table-head` | 9 | `--font-size-100` (12) |
| `--text-cell-secondary` | 10 | `--font-size-100` (12) |
| `--text-tab` | 12 | `--font-size-300` (14) |
| `--text-subtab` | 11 | `--font-size-200` (13) |
| `--text-rail` | 12 | `--font-size-200` (13) |
| `--text-rail-eyebrow` | 9 | `--font-size-100` (12) |

- `body` (in `ui/primitives.css`): `font-size: var(--text-base); line-height: var(--leading-body); font-family: var(--font-sans);`. Tabular figures: `font-variant-numeric: tabular-nums` on `table`, money and figure classes (`.money`, `[data-figure]`, card figure classes; the pre-flight lists the exact selectors).
- **Codemod** `tools/uqfi-type-codemod.mjs` (committed, idempotent, rerun by any branch that merges after it). Over `frontend/src/**/*.css` except `ui/tokens.css` and `ui/fonts.css`, each `font-size` value becomes a role or primitive variable:
  - any px value ≤ 12 (7, 8, 9, 9.5, 10, 10.5, 11, 12), `0.75rem`, `var(--text-xs, …)`, `var(--font-size-sm, 0.85em)` → `var(--font-size-100)`;
  - 13 px, `0.8125rem` → `-200`; 14 px, `0.875rem` → `-300`; 15, 16 px, `1rem` → `-400`; 17, 18, 19 px → `-500`; 20, 22 px → `-600`; 23, 24, 25, 27 px → `-700`;
  - an existing `var(--text-*)` stays (its token was re-pointed); `inherit`, `1em` and `100%` stay;
  - a fallback inside `var(…, x)` is dropped;
  - any value it cannot map is printed and fails the run (the builder maps it by this table's nearest-step rule, ties go up, and adds it to the script).
  - The one inline `fontSize` in TSX (outside tests) uses the variable.
  - Monospace literals (`Consolas, monospace`, `ui-monospace, …`) become `var(--font-mono)`.
- **Spacing, demo-path files only:** padding, margin and gap px values in the CSS files the P1-P8 frames load are snapped to the nearest `--space-*` (ties down, so nothing grows by more than 2 px); 1 px and 2 px hairlines stay. Other files keep their values (the ratchet does not count spacing for 17 Nov).

**D-UQFI.3 Style ratchet (shrink-only), `tools/checks/style-ratchet.mjs`.**
- Same contract and code shape as `frontend-hardwiring.mjs`: per-file counts compared with `tools/checks/fixtures/style-ratchet-baseline.json`; any cell above baseline fails; a file outside the baseline counts from 0; the baseline changes only by `--shrink` (refused while any cell has risen); `--print` shows counts.
- Scan: `frontend/src/**/*.css` and `frontend/src/**/*.tsx` (not `__tests__`), excluding `ui/tokens.css` and `ui/fonts.css`. Cells per file:
  - `rawFontSize`: `font-size` values that are not `var(--text-*)`/`var(--font-size-*)`/`inherit`/`1em`/`100%`, plus inline TSX `fontSize`;
  - `rawFontFamily`: `font-family` not `var(--font-*)` or `inherit`;
  - `rawHex`: hex colour literals.
- **Wall, not ratchet (whole tree, tokens.css included):** any font-size resolving below 12 px fails. After the codemod, `rawFontSize` and `rawFontFamily` are 0 in every file, so those two baselines hold no rows; `rawHex` gets today's per-file counts (to shrink later, stage 1).
- `tools/checks/test_style_ratchet.mjs` (node test, like `test_frontend_hardwiring.mjs`): a rise fails, a new file counts from 0, `--shrink` refused on a rise, the 12 px wall, the allowed relative values.
- Wire into `tools/check-all.ps1` beside the hard-wiring guard: `Invoke-Guard "Style ratchet (UQ-FI)" $Node @("tools/checks/style-ratchet.mjs")`.

**D-UQFI.4 One headline, one gap line per section.**
- **Headline:** each P1-P8 page has exactly one `h1`, rendered through `PageHeader` (or `V69Layout`'s title slot) at `--text-page-title`, and it is the headline text in the 6.1 table. No other element on the page uses `--text-page-title` or a larger size. Elements that are visually headline-sized today (outcome row titles, card titles) drop to `--text-panel-title`. On P3 the status line moves below the title and first sentence; nothing is removed.
- **Gap grouping**, new `frontend/src/ui/gapGroup.ts` (pure) and `frontend/src/ui/GapGroup.tsx`:
  - `groupGaps(items: GapItem[]): GapGroupLine[]`, where `GapItem = { subject: string; fact: string; reason?: string; gapId?: string }` and `GapGroupLine = { fact: string; reason?: string; subjects: { subject: string; gapId?: string }[] }`.
  - Group key is `(reason ?? fact)` with exact string equality on `fact`; different facts or reasons never merge. Lines keep D-E5.46 precedence order (no readings, conflicting, not enough, not analysed yet, still processing), then other facts in first-seen order. Subjects keep their original order.
  - A group with one subject renders exactly as today (no change for single gaps).
  - `<GapGroup items={…} />` renders one `<p class="gap-group">` per line: `<span class="gap-group__fact">{fact}</span>` followed by `<ul class="gap-group__subjects">` with one `<li data-gap-id={gapId}>{subject}</li>` per subject (separators in CSS). The words are the server's or the page's existing words; the component concatenates no strings.
  - A section is one panel or card. Grouping never crosses sections. Where every block of a section says only a gap (for example the Cold board's lower-half cards "No cold assessment for this window"), those blocks become one `GapGroup` line in that section, naming each block's title as a subject.
  - Where the gap words come from `MissingClaim`, the subject `<li>` renders `MissingClaim` for that gap, so `missing-claim-scan.mjs` and the gap ids still see every gap.
- Site-type agnostic: no `site_type` or outcome-id branch (hard-wiring ratchet). Words never composed from codes.
- Collapse targets the pre-flight confirms on the live pages (at least): the Finding header's "Priority: not assessed · Confidence: not assessed"; the Cold board's four "No cold assessment for this window" cards; repeated "Not available yet"/"Unknown"/"not worked out yet" lines inside one Portfolio card or one board outcome row. Not: tables, the outcome matrix, tab rows, lens chips.
- **MOCK DEVIATION:** the type sizes need no label once the owner approves the sheet (the v7.2 sheet replaces the v6.9 type scale for what it covers). Each collapsed section carries a MOCK DEVIATION label citing D-UQFI.4 unless the UQ-FI-0 panel is approved (then it cites the sheet).

**Tests.**
- Frontend (vitest, named files only):
  - `ui/__tests__/gapGroup.test.tsx`: grouping by fact; different reasons never merge; D-E5.46 order; subject order; a single gap unchanged; gap ids preserved on every subject; no text composed (fact and subjects appear as separate nodes).
  - One test per P1-P7 frame (added to its existing test file, named in the pre-flight): exactly one `h1`, with the headline text; the set of gap ids and gap facts on the page is the same before and after (no gap lost).
  - `ui/__tests__/tokens.test.ts`: every `--text-*` and `--font-size-*` resolves to ≥ 0.75rem; `main.tsx` imports `fonts.css` before `tokens.css`.
  - Existing tests that assert removed duplicate lines are updated; each is listed in the packet with the reason.
- Guards: style ratchet (new), hard-wiring, missing-claim, mock-deviation labels, architecture check.
- **Visual evidence (required for review)**, new `tools/uqfi-captures.mjs`, the CDP approach of `tools/layout-evidence.mjs` (no new dependency):
  - `capture <links.json> <out-dir> [web-base] --widths 1440,1280` takes full-page PNGs of every P1-P8 URL (the DS-1f links output for the chosen DB) into `Docs/demo-sprint/uqfi-img/{before,after}/{nn}-{page}-{width}.png`.
  - Per page and width it records in `measure.json`: the smallest computed font-size of visible text (must be ≥ 12), page-level sideways scroll (must be none), the `h1` count (must be 1 after), the count of visible gap-fact lines before and after, and whether Inter is the rendered font (`document.fonts.check`).
  - **Before** captures from main at the lane's start, **after** from the branch; same DB, same serve, same URLs, light theme.
  - Also measured, no picture: sideways scroll at 390 px on P1-P3 (no regression).
- Packet: the codemod output (counts per file), distinct font-size values before and after (62 strings today, target the 8 steps plus `inherit`/`1em`/`100%`), the ratchet baseline, font SHA-256, the before/after index (an HTML page pairing the pictures), and the list of collapsed sections per page.

**D-UQFI.5 Collisions with work merging this week.**
- **Already merged** (PF-T, PF-C/PF-W, SR-1, SR-2, SR-2b, C1, PB-1c): UQ-FI is cut from main after them; nothing to do.
- **PR-2a / PR-3** (`sites/SitePrices.tsx`, `sitePrices.css`, `priceAction.css`, the PR-3 form):
  - From now, PR-2a and PR-3 CSS uses `var(--text-*)` only, no px font sizes (the coordinator relays this to both builders today).
  - Whichever merges first, the other rebases. If PR-2a/PR-3 merges first, UQ-FI reruns the codemod and the ratchet after the rebase and retakes the P8 price-page capture. If UQ-FI merges first, PR-3 runs the codemod on its own CSS and must pass the ratchet (new files count from 0).
  - UQ-FI does no collapse or headline work on the price page and does not touch PR-3's TSX.
  - Sat order: PR-3 merges first if ACCEPTed by 15:00; otherwise UQ-FI merges first (by 18:00) and PR-3 rebases.
- **AR-4:** backend only, no collision. If AR-4 changes a server word that a P-page groups, the grouping still works (exact fact match), and the before/after gap-count check in `measure.json` shows any change.
- **Any other branch merging after UQ-FI** that touches frontend CSS reruns the codemod and passes the ratchet.

### 6.4 Lane and order

| When | What |
|---|---|
| Thu evening (after the 14:00 demo) | The coordinator shows the owner the sheet with the 6.2 bullets (+ the UQ-FI-0 panel, if a Sonnet builder adds it on `task/UQ-0-v72-sheet` by then). |
| Fri 07:00, VPS | **Starts only on owner approval.** Lane D: UQ-FI-1, Opus, branch `task/UQ-FI-1-tokens` from main. First job: the before captures (one serve, read-only, the DB the coordinator names; not beside AR-4 parity). Then tokens, Inter, codemod, ratchet. |
| Fri 09:00, VPS | Lane E: UQ-FI-2, Opus, branch `task/UQ-FI-2-declutter`, stacked on UQ-FI-1's first commit (its logic and tests do not depend on token values). Pre-flight first: the frames, test files and collapse targets per page, in one batch. |
| Fri ~20:00 | UQ-FI-1 done; UQ-FI-2 rebases onto it. Rebase onto PR-2a if merged. |
| Sat 08:00 | After captures, `measure.json`, packet; both branches reviewed as one diff by one fresh Claude reviewer. |
| **Sat 14:00** | Review verdict. Sonnet fix round and re-review follow. |
| **Sat 18:00** | Merge, UQ-FI-1 then UQ-FI-2, together. |
| **Sat 20:00** | Not ACCEPTed → **held whole**, both branches unmerged. 17 Nov uses today's look; Saturday's suites and Sunday's recapture run on today's look. |

- **No approval by Fri 12:00:** UQ-FI does not start and returns to BL-69. There is not enough time left for a build and a review.
- Saturday's suites (from 20:00) and Sunday's recapture and DS-1f picture refresh then run on whatever look merged. The recapture is light theme only.
- VPS jobs: captures are one serve and one Chrome at a time, never beside a Postgres parity run or a prepare. UQ-FI needs no Postgres.

### 6.5 What it pushes out

- **Nothing.** Lanes A (CLEAN-1, FR-B trimmed), B (PR-2a, PR-3) and C (AR-4) stand as in 5.5. UQ-FI takes lanes D and E on the VPS, which has room for 4-5 lanes.
- What it costs instead: Saturday review load (AR-4, PR-3 and UQ-FI all reviewed Sat; separate fresh reviewers), and the VPS RAM during the before and after captures.
- **If they clash, priority:** AR-4 > PR-3 > UQ-FI > FR-B > CLEAN-1. FR-B drops first, as already ruled.

**Risks, stated plainly.**
1. **Bigger type breaks fits.** 11→13 px table text and 9→12 px heads can push a wide table (the Findings index was fitted at desktop width in W1-F5b) into sideways scroll at 1280 px. The fix is wrapping inside the cell, never a size under 12 px and never a layout change; `measure.json` catches it.
2. **The codemod touches 37 CSS files.** Snapshot and text tests that read CSS may fail. Only CSS-reading tests should change; any other failing test is a defect, not a golden to update.
3. **Owner approval is the gate.** If it slips past Fri 12:00, UQ-FI is off for 17 Nov.
4. **Collapse can hide a fact by accident.** The gap-id and gap-fact set test per page and the before/after counts guard it; a lost gap is High in review.
5. **DS-1f pictures** are from the old look. If UQ-FI merges, Sunday's recapture refreshes them (already planned); if held, nothing changes.

### Dispatch briefs (revision 6)

**UQ-FI-1 tokens, type, Inter, ratchet.** Opus. VPS wt `AssetOpsV1-uqfi1`, branch `task/UQ-FI-1-tokens` from main. 0.9 unit plus the before captures. Spec: 6.1, 6.3 (D-UQFI.2, D-UQFI.3), the approved v7.2 sheet (type section), 6.4. Pre-flight: unmappable font-size values, the money/figure selectors for tabular figures, the demo-path CSS file list. Vitest and node tests on named files only.

**UQ-FI-2 headline and gap lines.** Opus. VPS wt `AssetOpsV1-uqfi2`, branch `task/UQ-FI-2-declutter` stacked on UQ-FI-1. 0.7 unit plus the after captures and the packet (0.2). Spec: 6.1 page table, 6.3 (D-UQFI.4), D-E5.46. Pre-flight: per page, the frame, the test file, and the exact sections and lines to group, in one batch, before code.

## Revision 5a (Architect, Claude, 2026-11-12): order of the remaining any-range speed work

- Ruling **D-ANY.8** (`build-sheet-OWN-GAPS-2026-11-08.md`). Lanes and the freeze in 5.5 are unchanged.
- **Order:**
  1. AR-3 + AR-6 merge as they are.
  2. AR-4 rebases onto main (it does not merge the AR-3 branch) and switches `evidence_money.mini_grid_rows` to `coverage.dispatch_days`.
  3. money.lines (MN-1/2/3, with the PR-3 price-save refresh) is built meanwhile, code and no-DB tests first.
  4. evidence.provenance goes to the backlog.
- **AR-4 minimum for 17 Nov:** claim rows + the switch. money.lines is IN only if its parity passes by Sat 12:00; otherwise it moves to `task/ANY-2-AR4b`. The ≤2 s target is reported, not gated.

## Revision 5 (Architect, Claude, 2026-11-12): price entry back IN, saved as "Entered by site admin"

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude (since 2026-10-27).
- Owner, verbatim (`.agent/owner-price-entry-in-scope-2026-11-12.md`): "yes, price entry in scope as site admin"
- Supersedes revision 4's "PR-3 out" line only. AR-3+AR-6, AR-4, PR-1 and PR-2a stand as written. The attribution rule is **D-PRICE.1** (`build-sheet-OWN-GAPS-2026-11-08.md`).

### 5.1 What PR-3 is for 17 Nov (scope ruling)

- **IN:** a price form on the Site price page that saves one of the **three stored keys** (`diesel_price_per_litre`, `ev_gross_tariff_per_kwh`, `productive_use_price_per_kwh`, `financials/assumptions.py:30`), recorded as "Entered by site admin". It uses the dip-form precedent, and the same entry service and switch.
- **OUT of PR-3, kept out:**
  - New keys (`repair_visit_cost`, `planned_service_cost`, `charger_repair_cost`, `interrupted_session_cost`, `stock_value_at_risk`). No figure reads them. Saving one would change nothing on screen, and the page would then say something untrue ("the figures update once it is set"). Early warnings carry no money today (`test_out_c1_never_money`), so pricing a warning is a new money consumer, not a form.
  - Roles, sign-in and the human route. `POST /financial-assumptions` stays refused (`HUMAN_PRINCIPAL_REQUIRED`), and its tests are unchanged.
  - The "N figures change" preview count.
- **PR-4: not needed.** The recalculation path already exists:
  - a revision insert raises `price.revised` in `event_outbox` (trigger, migration `0044_chain_events.py:57-60`; register `config/chain/event-register-v1.yaml:13`, `by_assumption_key`);
  - diesel and EV publications queue consequence work (0011/0026 triggers);
  - the demo serve's tick (every 120 s, `tools/demo_combined.py:23`) drains `consequence`, `ev_consequence` and `chain_snapshots`;
  - affected figures read the existing `PENDING_RECOMPUTE` "Updating…" until then;
  - the productive-use price is read at request time (0040), so it shows at once.
  "Priced on" and "Restated on" notes (BL-67c) stay out.
- **PR-5: not needed** for a stored key; stays out.
- **Owner option, not the default (needs sign-off and pushes FR-B out): PR-3b, "price the visits warning", +0.75.** It adds the key `repair_visit_cost` (migration and unit), a priced part on REPEATED ("3 visits × 120 USD (your price)", never summed with the open part), and a ruling that relaxes never-money for that one warning. Only if the owner asks.

### 5.2 Where the dip form writes and how it is attributed (precedent, cited)

- Route: `POST /api/sites/{site_code}/work/operational-entries` (`backend/assetops_backend/work_api.py:198-216`).
- Actor: the server-configured entry service `ENTRY_PRINCIPAL = "service:operator-entry"` with attestation `service=operator-entry;job=site-admin-entry;rule=oprec-entry/1` (`backend/assetops_backend/work/operational_entry.py:25-27`). The browser never sends an actor.
- Switch: `ASSETOPS_OPERATIONAL_ENTRY=on`, read in `host/lab_app.py:77-97` (`operational_entry_from_environment`) and injected as `operational_entry_principal` (`main.py:248, 627`). The demo serve sets it (`tools/demo_combined.py:779`).
- Label: `OPERATOR_ENTRY_LABEL = "Entered by site admin"` (`frontend/src/work/OperationalRecords.tsx:89-90`; owner Q3, build sheet §3.1 line ~686).

### 5.3 PR-3 technical design (builders do not design)

**Server constants (new, in `financials/assumptions.py`):**
- `SITE_ADMIN_CHANNEL = "SITE_ADMIN_ENTRY"`; `SYSTEM_CHANNELS` becomes `("SYSTEM_CLI", "SYSTEM_FIXTURE", "SITE_ADMIN_ENTRY")`.
- `SITE_ADMIN_PRICE_PUBLISHER = SystemPrincipal(actor_id="service:operator-entry", authorization_basis="SITE_ADMIN_ENTRY: entered on screen through the server-configured entry service, labelled 'Entered by site admin'; no signed-in person (D-PRICE.1)", actor_kind="SYSTEM")`. The actor id is `ENTRY_PRINCIPAL` imported from `work/operational_entry.py`, not retyped.
- Provenance on every entry: `{"service": "operator-entry", "job": "site-admin-price-entry", "rule": "price-entry/1"}`, plus `"entry_note": <reason>` only when a reason is sent for a non-correction (below).

**Migration (next free number; `0060_site_admin_price_entry` expected).**
- Widen the `financial_assumption_revision` channel CHECK to `('SYSTEM_CLI','SYSTEM_FIXTURE','HUMAN_API','SITE_ADMIN_ENTRY')`. Guard on the installed constraint name, as 0040 does.
- The actor CHECK (`0010:76-78`) is unchanged and still holds: SYSTEM actor, no `author_id`, channel ≠ `HUMAN_API`.
- Downgrade refuses while any row has channel `SITE_ADMIN_ENTRY`, then restores the 0010 CHECK.
- No new table. If AR-4 or another branch takes the number first, whoever merges second renumbers and re-chains `down_revision`.

**Route.** `POST /api/sites/{site_code}/financial-assumptions/entries`, in `financial_api.py` `build_financial_assumption_router`. New keywords: `entry_principal: Principal = no_service_principal` (the same injected `operational_entry_principal`, so the one switch `ASSETOPS_OPERATIONAL_ENTRY` covers dips and prices), `store` (the assumption store or None), `site_zone` (`(tenant_id, site_id) -> ZoneInfo`, using the Site time-zone lookup that `entry_site_context` uses) and `read_access` (the price read's access). The existing human route is untouched.

Request, a closed JSON object; any other key gives 422 `PRICE_ENTRY_INVALID` with `fields`:

```json
{"key": "diesel_price_per_litre" | "ev_gross_tariff_per_kwh" | "productive_use_price_per_kwh",
 "value": "1.45", "currency": "USD",
 "basis": "AUTHORED_ESTIMATE" | "CONTRACT_RATE" | "RECORDED_PURCHASE",
 "source": "Supplier contract SC-88", "applies_from": "2026-11-10",
 "reason": "Contract rate replaces the estimate" | null,
 "dry_run": false, "idempotency_key": "price-entry-<32 lowercase hex>"}
```

Refusal order (fixed and tested); every refusal is `{"detail": {"code", "message"}}` and nothing is written:
1. 404 when `scope(site_code)` is None.
2. 403 `SITE_SCOPE_FORBIDDEN` from `read_access`.
3. 403 `PRICE_ENTRY_OFF`, "Saving prices is switched off on this server.", when `entry_principal` is None.
4. 422 `BODY_NOT_JSON`.
5. 422 `CLIENT_ACTOR_FORBIDDEN` (the existing `_client_actor_fields`).
6. 422 `PRICE_ENTRY_INVALID` for shape:
   - `key` one of the three;
   - `value` matches `^[0-9]{1,6}(\.[0-9]{1,4})?$` and is > 0;
   - `currency` in `ISO_4217`;
   - `basis` one of `BASES`;
   - `source` 1-120 characters after trimming, with no control characters;
   - `applies_from` an ISO date;
   - `reason` null or 1-200 characters;
   - `dry_run` a boolean, optional (default false);
   - `idempotency_key` matches `^price-entry-[0-9a-f]{32}$`.
7. 422 `PRICE_KEY_NOT_ENTERABLE` for a known future key (the PR-1 `PRICE_NOUN` keys outside `STORED_KEYS`): "No figure uses this price yet, so it cannot be saved here."
8. 503 `ASSUMPTION_STORE_UNAVAILABLE` when there is no store.
9. Derivation (below), then 422 `APPLIES_FROM_OUT_OF_RANGE`, `CURRENCY_DIFFERS` or `REASON_REQUIRED`.
10. The store's own `PublicationRefused` status and code pass through unchanged (409 overlap codes, idempotency conflict).

**Derivation (server only; the browser never sends a change kind, an instant or an actor).**
- `valid_from` is Site-local midnight of `applies_from`, as UTC. `valid_to` is None.
- Bounds: from Site-local today − 400 days to today + 366 days.
- The current series is read once (`store.snapshot`, current). `expected_prior_revision_id` is the series' highest revision, or None.
- Change kind:
  - no current assignment overlaps `[valid_from, ∞)` → `INITIAL`;
  - an overlap, and `valid_from` ≥ server now → `SUCCESSION`;
  - an overlap, and `valid_from` < server now (today or earlier) → `CORRECTION`. `reason` is required here, else 422 `REASON_REQUIRED`: "This date changes figures already shown. Say why."
- A reason sent with INITIAL or SUCCESSION is kept as `provenance.entry_note`, never as `correction_reason` (the store refuses that, `assumptions.py:147`).
- Currency must equal the series' current currency when a series exists ("This site's {noun} is kept in {CUR}."). With no series, any active ISO code is allowed.

**Dry run** (`"dry_run": true`). Runs steps 1-9 and `plan_assignments` (pure). It never calls `publish`. The response is 200:
`{"dry_run": true, "change_kind", "applies_from", "reason_required": bool, "summary"}`. The summary is server words:
- INITIAL: "First {noun} for {Site}: {value} {CUR} per {unit} from {d MMM yyyy}. Figures from that date get a price."
- SUCCESSION: "New {noun} from {date}. Earlier figures keep the current price."
- CORRECTION: "Correction from {date}. Figures from {date} are recalculated with this price; the earlier version is kept in the history."

**Save.** `store.publish(tenant_id, site_id, Publication(..., channel="SITE_ADMIN_ENTRY", source_reference=source, provenance=...), SITE_ADMIN_PRICE_PUBLISHER)`.
- The response is 201 for new, or 200 when `replayed` (same idempotency key and digest):
  `{"revision_id", "revision_no", "change_kind", "applies_from", "recorded_at", "replayed", "set_by": "Entered by site admin", "summary"}`.
- The summary reads: "Saved. {Noun} {value} {CUR} per {unit} from {date}. Figures that use it read "Updating…" for a few minutes, then show the new price."
- No recompute runs inline. The tick does it (5.1).

**How a saved price reaches PR-1 and PR-2a reads.** No new read code:
- PR-1 `price_action` is attached only to UNPRICED items. Once the price covers the window, the item reads priced and the link disappears.
- PR-2a's page read lists the new revision in History. It must map `actor_id` to `set_by_label`: `service:assetops-assumption-publisher` → "AssetOps administrator"; `service:operator-entry` → "Entered by site admin". The words are the server's. If PR-2a merges first, it ships the map with both entries.
- PR-2a's page read gains `entry: {"enabled": bool, "keys": [the stored keys this Site uses]}`. `enabled` is false when the principal is not configured, or when the request carries `known_at`.
- **AR-4 contract line:** the `money.lines` kind must declare `price.revised@1` (`by_assumption_key`, days from the valid date to today) in the register. PR-3's Postgres flow test must pass on whichever path is live, and whichever of AR-4 and PR-3 merges second reruns it.
- The response store needs nothing new. The outbox insert moves the watermark, and a test pins that a stored Financials body is not served after a save.

**UI (on the PR-2a page; `price-it.html` Part B is the base layout).**
- Rows of entry keys gain a **"Set a new price"** button. When the page opens with `?key=` set to an entry key, that row's form is open on arrival.
- The form opens **inline under its row** and stacks to one column at 390 px. Fields, all words from the server or one words file:
  - **Amount**, with its unit suffix ("USD per litre");
  - **Currency**: read-only text when a series exists, otherwise a select;
  - **Basis**: three radios, "An estimate", "A contract rate", "A recorded purchase";
  - **Where this price comes from** (required);
  - **Applies from**: date, default Site-local today;
  - **Reason**: shown when the dry run says `reason_required`.
- Two steps: **Continue** sends the dry run and shows its `summary` in a confirm panel; **Save price** posts.
- One idempotency key per opened form, reused on every retry.
- After save: the page stays, shows the server `summary` as a success note, re-reads the page (the row shows the new value; History's top entry reads "Entered by site admin"), and keeps "← Back to where you were" prominent.
- The sign-in sentence becomes: "Prices saved here are recorded as entered by site admin until sign-in is available."
- PR-1 label, server words in `price_action.wire`: a `SET_PRICE` key outside `STORED_KEYS` reads **"What pricing this needs →"** instead of "Set a {noun} …", so no link promises a save that cannot happen.

**Honest states.**

| State | What the user sees |
|---|---|
| Entry off (`enabled` false, no `known_at`) | The draft's sentence, "Prices are set by your AssetOps administrator until sign-in is available.", and no form |
| `known_at` view | "You are viewing prices as known at {k}. Set a price from the live view →" (the link drops `known_at`); no form |
| Future key row | "Not set" and "Saving this price comes once a figure uses it."; no button |
| 422 or 409 | The server message inline, and "Nothing was saved." |
| 503 | "Prices cannot be saved right now. Nothing was saved." |
| Network loss on save | "We could not confirm the save. Saving again is safe." (same key) |
| After save | Affected figures elsewhere show the existing "Updating…" until the tick; no new state |

**Tests.**
- **Backend, no DB** (`test_pr3_price_entry.py`):
  - each refusal in order;
  - each shape field;
  - a future key refused;
  - the change-kind table (none → INITIAL; tomorrow → SUCCESSION; today and past → CORRECTION, with REASON_REQUIRED);
  - `valid_from` at Site-local midnight for a non-UTC zone;
  - a dry run never calls `publish` (spy);
  - the actor, channel, attestation and provenance literals;
  - `entry_note`;
  - `set_by` and summary words;
  - the PR-1 label for future keys;
  - `entry.enabled` false under `known_at`.
- **Postgres** (own `*_test` DB, `test_pr3_price_entry_postgres.py`):
  - 0060 up and down, and down refused while a row exists;
  - a saved row has channel `SITE_ADMIN_ENTRY`, actor `service:operator-entry` and no `author_id`;
  - a `price.revised` outbox row;
  - a diesel CORRECTION queues consequence work, and after one drain (`recompute.run`, plus the chain snapshot consume and drain) the fuel-cost money line reads the new price, while the same read "as known at" before the save reads the old one;
  - a replay returns 200 with one row;
  - a productive-use INITIAL on a Site without one makes the mill value priced on the next read, and its `price_action` disappears;
  - a stored Financials response is not served after a save.
- **Frontend** (`sitePriceEntry.test.tsx`):
  - the form shows only on entry keys and only when `enabled`;
  - `?key=` opens the form;
  - Continue → dry run → summary;
  - the reason field appears on `reason_required`;
  - the save body has no actor field and reuses the key on retry;
  - the success note and re-read;
  - each honest state.
- **Guards:** hardwiring, missing-claim, mock-deviation labels and architecture check.
- Layout evidence at 1440 and 390 px for the open form and the success note.

**Units: 1.0 agent unit.** Server, migration and tests 0.55; frontend form and states 0.35; the Postgres flow test 0.1. Opus for the first build, Sonnet for fix rounds.

### 5.4 Defaults: owner sign-off needed, and which can stand

| # | Default | Owner sign-off? |
|---|---|---|
| 1 | Address `/sites/:code/financials/prices` (draft choice 1; PR-1 built it) | yes, draft choice |
| 2 | "Assumptions" subtab becomes "Prices"; the old address forwards (choice 2) | yes, draft choice |
| 3 | Future keys listed as "Not set", with "Saving this price comes once a figure uses it." and no button (choice 3, sharpened) | **yes** |
| 4 | Half-simple warnings link their simple part (choice 4). Their keys are future keys, so the link reads "What pricing this needs →" for 17 Nov | **yes** (changes PR-1 words) |
| 5 | Model items open Part C, with no "Tell your contact" (choice 5) | yes, draft choice |
| 6 | Form inline under the row; Continue → confirm → Save price; stay on the page with the success note and Back link | **yes** |
| 7 | Sentence: "Prices saved here are recorded as entered by site admin until sign-in is available." | **yes** (copy) |
| 8 | Preview is the change-kind sentence only, with no "N figures change" count (spec §4.2 reduced) | **yes** |
| 9 | Applies-from defaults to today; today or earlier over an existing price is a correction and needs a reason | no (follows spec §4.2, §4.5) |
| 10 | Demo beat: the presenter corrects Kobo's diesel price from a past story day with a reason, on the live view (no `known_at`), waits for "Updating…" (2-4 min), then shows the fuel cost and History "Entered by site admin". The save persists in that database, so it goes last in the session. | **yes** (script) |
| 11 | PR-3b (price the visits warning) stays out | **yes**, only if the owner wants warnings priced |

The coordinator sends items 3, 4, 6, 7, 8, 10 and 11 to the owner in one message, with the draft's choices 1, 2 and 5. Nothing waits on them before Friday morning: the server half needs no sign-off.

### 5.5 Lanes and order, from Thu 12 Nov ~12:30 to the freeze (last merge Sat 14 Nov 20:00)

| Lane | Thu pm | Fri | Sat (to 20:00) |
|---|---|---|---|
| A | AR-3 + AR-6: Postgres and client4 parity | review, merge by 14:00; then CLEAN-1 (0.25), moved from B | FR-B trimmed (0.5), moved from B; buffer gone |
| C | AR-4 (2.0): code; Postgres after AR-3's slot | Postgres and parity on client4 | review, merge by 16:00; held if not ACCEPTed by 20:00 |
| B | PR-1 Postgres files, review, merge; **PR-3 server** (0.55) code and no-DB tests on `task/PR-3-price-entry` from PR-1 | owner signs the draft (needed by Fri 09:00) → PR-2a (0.4) → review, merge Fri evening; **PR-3 frontend** (0.35) stacked on PR-2a; PR-3 Postgres flow test (slot after AR-4) | PR-3 review by 12:00, Sonnet fix round, merge by 18:00; held if not ACCEPTed by 20:00 |

- **Postgres priority:** AR-3 > AR-4 > PR-1/PR-2a/PR-3 > FR-B. PR-3's migration test is one short slot, never beside a parity run.
- **What moves:** FR-B (0.5) and CLEAN-1 (0.25) go from lane B to lane A. Lane A's buffer (EV-HB gate slack, Sunday fix-round prep) is used up. **Nothing new is pushed out of 17 Nov.** If AR-3 + AR-6 slips past Fri 14:00, FR-B drops first, then CLEAN-1. PR-3 does not touch AR files and does not compete with AR-4, except for the one register line in 5.3.
- **If the owner's draft sign-off slips past Fri 12:00:** PR-2a and PR-3's frontend build to the defaults above, labelled MOCK DEVIATION where they differ from the draft. The owner checks them at the Sunday walkthrough, and the Sunday Sonnet round fixes the words.
- **Hold rule for PR-3:** not ACCEPTed by Sat 20:00 means held unmerged, server and frontend together (a route with no screen is not shown, so there is no partial merge). PR-2a's read-only page then stands, with the administrator sentence, and the presenter says that prices are set by the AssetOps administrator. If PR-2a is also held, PR-1's honest "not available yet" target stands. PR-3 is stacked on PR-2a and never merges without it.
- **Walkthrough and final build:** PR-3 is in the Sat rehearsal build and the Sun 15:00 walkthrough. Saves made during the walkthrough stay in that database only. The Mon 16 final build is fresh, so they do not carry into 17 Nov. The prepare applies 0060 like any migration.

### Dispatch brief (revision 5)

**PR-3 site-admin price entry.** Opus. Wt `AssetOpsV1-pr3`, branch `task/PR-3-price-entry` from `task/PR-1-price-action` (rebase onto main after PR-1 merges, then onto PR-2a for the frontend). 1.0 unit.
- Spec: this revision, 5.2-5.4; D-PRICE.1; `.agent/architect-answer-price-it-2026-11-10.md` §4.2 and §4.5 (form fields, change kinds); precedent `work/operational_entry.py`, `work_api.py:198-216`.
- Thu pm: server, migration and no-DB tests only. Postgres only on the coordinator's go, own `*_test` DB, never client4, client6 or client7.
- Pre-flight questions (one batch, before code): the Site time-zone lookup to reuse; whether `store.snapshot` gives the current assignments the derivation needs; the migration number free at that moment.
- Packet: the refusal table as tested, the derivation table, the Postgres flow output (the before and after money line, and as-known-at), layout evidence, and any MOCK DEVIATION labels.

## Revision 4 (Architect, Claude, 2026-11-11 ~18:00): any-range speed first, "price it" next

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude.
- Owner, verbatim (`.agent/owner-price-it-and-speed-priority-2026-11-11.md`): "i want pricing early warnings and unpriced items to be done and the speedup for any date range priortised"
- Tonight is unchanged (D-ANY.6, build sheet): AR-0 baseline, AR-2, prepare by 22:30. The machine is reserved 22:15 to about 03:30. HON-1 and OPEN-NOW merge after the tag.

**Ruling on AR-4 and PF-O2: PF-O2 is not required.**
- PF-O2 is a new in-memory route over `summary()`. AR-4 changes what `summary()` reads (evidence and money from rows); it does not need the route.
- The dependency was only a guard against changing the same Portfolio read twice. PF-O1/O2 stays out for 17 Nov, so there is nothing to change twice. If PF-O2 is built later, it inherits the rows.
- PF-C is merged, so its money receipts are in place. AR-4 = 1.5 (spec) + 0.5 for parity on the PF-C receipt lines = **2.0**.
- AR-4 needs only AR-1 merged (tonight, if the baseline parity passes). It runs in its own lane beside AR-3 (spec: "AR-3/AR-4 can run in two lanes after AR-1").

**"Price it" for 17 Nov: the honest half only.**
- PR-1 `price_action` on unpriced items: early warnings, money cells, Finding cost tiles, verification value (0.5).
- PR-2a read-only Site price page: current prices, history, and "Prices are set by your AssetOps administrator until sign-in is available" (0.4). A v7.1 page draft goes to the owner first.
- **Out, and why:** PR-3 write path and PR-4 recalculation-on-publish need BL-54 sign-in (a hard dependency). PR-5 "what is needed" blocks (0.5) are out unless buffer remains on Fri. Without sign-in, saving a price is not possible in the session; the presenter says so.

**Order, Thu ~12:30 to Sat 20:00 (last merge), all Postgres one job at a time.**

| Lane | Thu pm | Fri | Sat (to 20:00) |
|---|---|---|---|
| A | AR-3 + AR-6 (1.5): code started tonight; Postgres and client4 parity Thu pm | review, merge by Fri 14:00 | buffer, Sunday fix round prep |
| C | AR-4 (2.0): code started tonight; parity Fri on client4 | Postgres and parity Fri pm (Postgres priority 2) | review, merge by Sat 16:00; held unmerged if not ACCEPTed by 20:00 |
| B | price-page v7.1 draft to the owner (tonight); PR-1 (0.5) | PR-2a (0.4) after owner approval | FR-B trimmed (0.5), CLEAN-1 (0.25) |

- **Postgres priority when slots clash:** AR-3 > AR-4 > PR-1/PR-2a > FR-B.
- **Moves out to fit:** PR-3, PR-4, PR-5; FR-B halved (only failures in the Sat freeze suites); AR-5 (pre-load stays as the safety net). Already out: PF-O1/O2 and UQ.
- **Honest risk:** AR-4 is the long pole. Its slack is about 4 h, and its parity gates the merge. If it slips, the Portfolio is fast for any range on coverage (AR-3) but money and evidence stay on pre-built ranges, and price-it is unaffected.
- Price-it does not compete with AR-4: different files and lane, and only light Postgres. Both land if AR-4's parity passes first time.

### Dispatch briefs (revision 4)

**AR-3 + AR-6.** Opus. Wt `AssetOpsV1-ar3`, branch `task/ANY-2-AR3-AR6` from `task/ANY-1-rows` (rebase onto main after ANY-1 merges). 1.5 units.
- Spec: `.agent/architect-answer-any-range-speed-2026-11-10.md` AR-3, AR-6, D-ANY.1-6.
- AR-3: kind `dispatch.day` on DATA-12 graded local days (not `dispatch_days`); `coverage._mini_grid_basis` reads rows; match pass unchanged.
- AR-6: the board's 4 work-index reads become one; Cold/EV boards under 1 s cold.
- Kill switch: the D-ANY.6 env list (an omitted kind = old path).
- Tonight: code and no-DB tests only, no heavy CPU after 22:15. Thu after 12:30: Postgres tests on the own `*_test` DB, then parity `--kinds dispatch.day` on client4 (never client6).
- Packet lists the added parity cases and the `perf_budget --any-range` before/after.

**AR-4 Portfolio evidence and money rows.** Opus. Wt `AssetOpsV1-ar4`, branch `task/ANY-2-AR4` from `task/ANY-1-rows` (rebase onto main after ANY-1 merges). 2.0 units.
- Kinds `evidence.claim`, `evidence.provenance`, `money.lines`; roll-ups read by `summary()`; no PF-O2.
- Every kind is proven byte-equal by AR-0 parity, including PF-C receipt lines and unaligned UTC windows. A kind that fails stays on the old path and is reported, never approximated.
- Tonight: code and no-DB tests only. Postgres from Thu 12:30, after AR-3's slot; parity on client4.
- Do not touch `estate/coverage` (AR-3's files); coordinate the shared register file by rebasing.

**PR-1 + price-page draft.** Opus. Wt `AssetOpsV1-pr1`, branch `task/PR-1-price-action` from main. 0.5 unit plus the draft.
- Spec: `.agent/architect-answer-price-it-2026-11-10.md` sections 3 and 7.
- Tonight: a v7.1 price-page mockup draft (read-only view, history, the administrator sentence) for the owner, in `frontend/mockups/`.
- PR-1: server `price_action` (two shapes) on every unpriced item; words server-side; frontend link to `/sites/:id/prices` with `return`. Until PR-2a lands, the target shows an honest "not available yet".
- No write path; `HUMAN_PRINCIPAL_REQUIRED` unchanged.
- Postgres tests only from Thu 12:30, own `*_test` DB.

## Revision 3 (Architect, Claude, 2026-11-11 evening): UI deferred, functional pull-in

- Owner, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`): "lets depriortize the UI asepct for now in the backlog and we'll come back to it later, lets focus on the functional ones".
- **Out of 17 Nov, to the backlog (BL-69):** UQ-0 sheet (built, branch `task/UQ-0-v72-sheet`, kept unmerged, awaits approval later), UQ-1 tokens/type/Inter, UQ-2 themes, UQ-3 states/quick wins, UQ-4..UQ-8. The session uses today's light look, English only. Lane D's C1 (PB-5/6/8, RM-1, RM-2, in review) stays IN: it is honesty and wording, not look. The C.5 collision rules about UQ-1 and UQ-2 no longer apply.
- **Freed: about 4 units** (UQ-0 0.5 done but parked, UQ-1 1.25, UQ-3 0.5, UQ-2 1.0, plus lane D time from Thu ~13:00).

**Pull-in, in order (functional only; each is small, reviewable and has no hidden dependency):**

| # | Id | What | Units | Why now | Depends on |
|---|---|---|---|---|---|
| 1 | HON-1 | "Complete readings" count excludes READINGS_CONFLICT and NOT_ENOUGH_READINGS days (Architect ruling on question 1: count them out) | 0.3 | The opening page now reads "complete readings on 7 of 7 days" next to "4 Nov: conflicting readings" (PARTIAL-MONEY packet residual risk). An executive sees a contradiction on page one; the owner's 2026-11-11 wording rule says incomplete or invalid data must be stated | none |
| 2 | OPEN-NOW | Server read of items open now, unfiltered by the range, and the Work pages' one line "Open now: 3 requests, whatever the dates" (approved Portfolio layout proposal, line 581) | 0.5 | Work pages now default to the last 7 full days (PB-1c), so an older open item is hidden. Operators ask "what is open"; this is the honesty half of R338 | none (SR merged) |
| 3 | AR-3 + AR-6 | ANY-2 core, already IN: coverage on rows; Cold/EV board work lists in one read | 1.5 | Starts now stacked on `task/ANY-1-rows` (code and unit tests only); Postgres tests after Thursday's demo and never beside the scratch prepare or the ANY-1 baseline | AR-1 (on the stack); merges only after ANY-1 merges |
| 4 | FR-B | Test hygiene fix round (carry list in the handoff "Carry to FR-B") | 1.0 | Saturday 20:00 suites decide whether the freeze build is trusted; fewer known failures means a break is visible. Lane D after Thursday's demo, targeted test files only | none |
| 5 | CLEAN-1 | Sonnet cleanup card: handoff follow-ups (UQ-6a unhandled-500 Content-Language, ch5c2 rerun when quiet) plus the F05 check below | 0.25 | Cheap; before the Sat suites | none |

- **Kept out (unchanged, still option X):**
  - **AR-4** (2.5). It needs AR-1 merged (Fri at best, after Thursday's baseline and AR-2) and PF-O2, which is not built. Freed units do not shorten that chain. The named workaround stays: Portfolio fast on pre-built ranges only (script ranges, lens variants, last 7 and 30 days).
  - **PF-O1/O2** (1.5). Layout work; today's grid fits 4-5 Sites; the owner's instruction puts layout after.
  - **UQ-4** (formats, language switcher). UI; English session.
- **Ruling on question 2 (F05 placement after s602b moved to PARTIAL):** a test gap, not a demo defect. CLEAN-1 confirms that one of `test_w303_selectors_postgres`, `test_w303_portfolio_scope_snapshot_postgres` or `test_s4_finding_index_postgres` asserts a Portfolio Finding row's placement on a fixture with chain day grades (AVAILABLE Site). If none does, add one assertion to the first of them by seeding grades, and drop the `rows.F05` expectation from `tools/s602b-verification-evidence.mjs` with a comment citing D-E5.38. Do not re-seed the s602b estate fixture.
- **Machine rule (unchanged, sharpened):** one heavy job at a time. Thu 06:30-12:30 every lane pauses. Thu afternoon the scratch prepare (about 2 h 45, EV-HB gate by Fri 18:00), then the ANY-1 baseline, run alone: builders write code and run non-Postgres tests only while either runs. Last merge Sat 20:00; anything not ACCEPTed is held unmerged.
- **Buffer:** about 0.5-1.0 of the freed units is left unassigned on purpose, for the EV-HB gate (revert or fix) and the Sunday fix round. ANY-1 still has no slack.

### Start-now briefs (revision 3)

**HON-1 complete-readings honesty.** Opus. Wt `AssetOpsV1-hon1`, branch `task/HON-1-complete-readings` from main. 0.3 unit. Lane C (or the first free lane).
- **Ruling:** a day graded READINGS_CONFLICT or NOT_ENOUGH_READINGS is not a "complete readings" day. The count reads "complete readings on 6 of 7 days" and the existing gap clause names the day and reason. No new wording beyond what GAP-REASONS already composes; if a count phrase must change, server text only via `card_text` (CH-6b2).
- **Where:** the day counts behind `portfolio_coverage` / `_coverage_days` (`backend/assetops_backend/site_outcomes/read.py` ~758-812) and the source of `day_counts` / `days_line` (`chain/vocabulary.py`). A Site with a conflict day is `complete: False`, so the Portfolio lead reads incomplete.
- **Check the same count on the Site Overview readings line and the Finding/cards "Why?" days**; one rule everywhere (the line and the cards cannot disagree, PF-C1).
- **Tests:** a targeted test per reason (conflict, not-enough) and one all-good week unchanged; update only goldens the change explains, listing each in the packet.
- Named test files only, own `*_test` DB, no prepare. Do not touch wt `AssetOpsV1-e3d`, DB client6, ports 8990/5490, Docker until Thursday's demo ends.

**OPEN-NOW Work pages "open now" line.** Opus. Wt `AssetOpsV1-opennow`, branch `task/OPEN-NOW-work-read` from main. 0.5 unit. Lane B.
- **Spec:** `.agent/architect-proposal-portfolio-layout-2026-11-10.md` line ~581; PB-1c packet note (global Work `state_counts` are window-filtered).
- **Backend:** add `open_now` counts (by work kind: requests, actions, as the Work pages show them) to the existing global and Site Work list responses, computed with no date filter but the same `known_at` cutoff and Site scope. No new endpoint unless the list contract cannot carry it; contract type in `contracts`.
- **Frontend:** one line above each Work list, "Open now: 3 requests, 1 action, whatever the dates"; zero reads "Nothing open now". Words server-side or in the existing Work words file, never composed from raw codes.
- **Tests:** backend count ignores the range but obeys `known_at`; one frontend test per Work page; revise register rows R338/S17 if found, else note in packet.
- Same machine rules as HON-1.

**AR-3 + AR-6 (ANY-2 core).** Opus. Wt `AssetOpsV1-ar3`, branch `task/ANY-2-AR3-AR6` from `task/ANY-1-rows` (bb3d7645c). 1.5 units. Lane A or C.
- **Spec:** `.agent/architect-answer-any-range-speed-2026-11-10.md` rows AR-3, AR-6 and D-ANY.1-5. AR-3 builds on DATA-12's graded local days, not `dispatch_days` (C.5).
- **Now:** code and non-Postgres tests only. Postgres tests only after the coordinator's go (after Thursday's demo, never beside the scratch prepare or the ANY-1 baseline).
- **Merge:** after ANY-1 (AR-0..AR-2) merges; rebase then. Held unmerged if not ACCEPTed by Sat 20:00; the Portfolio then uses pre-built ranges.
- Packet lists the parity cases it adds to AR-0's harness.

## Client demo Tue 17 Nov: cut and start order (Architect, Claude, 2026-11-11; revision 2 after the owner's answers; revision 1 is in git at 22d877b1d)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-tag-optionb-client-date-2026-11-11.md`): "yes tag it and add the backlog item, lets go with option B for now. Also, lets proceed with the items for today right away, and i want my walkthrough comment items to start building. THe client demo will be on 17-Nov"
- Owner answers, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`): "here is my response 1. No 2.No 3. yes 4. yes 5.I need more context on this 6. I need more context on this 7.I will start talking to different client starting with Minigrid and EV , likely executives 8.Sunday 3PM ready for walkthrough or am available finished earlier too"
- What that means:
  - **IN for 17 Nov:** any-range speed (ANY-1 and ANY-2), the shared date range (SR), and the design foundation with light and dark themes. (Revision 3: the design foundation moved to the backlog, owner 2026-11-11.)
  - **Approved:** `portfolio-tabs.html` is the layout spec, and RM-2 is approved.
  - **Pending, being explained to the owner:** PB-1c and DATA-6.
  - **Audience:** mini-grid and EV operators, likely executives. EV fixes (PB-3 + DATA-11) and visual quality gain value. BeagleBone loses it, so it moves to after.
  - **Walkthrough:** Sun 15 at 15:00, or earlier.
- Status at writing: A1 DATA-12 is built (fd85f1d31) and in review. B1 PF-T is building.

### C.1 Schedule (skeleton kept; one adjustment recommended)

| When | What |
|---|---|
| Tue 17 | Client demo. 30-min smoke check in the morning. |
| Mon 16 | **Final demo build** (S = Mon 16, prepare about 2 h 45), finish and live checks, figures into both scripts, tag `demo/2026-11-16-final`. Only a blocking frontend fix may land. |
| Sun 15 | **Owner walkthrough at 15:00.** One Sonnet fix round afterwards, merged by 22:00. |
| Sat 14 | **Last feature merge 12:00 (kept).** Then full suites and check-all with the lanes stopped (about 6 h). Rehearsal build overnight. Sun morning: live checks, recapture in both themes, script refresh with PILOT-1 (0.25). |

- **Recommended adjustment, for the owner to choose (C.4 option Y):** last merge **Sat 20:00** instead of 12:00.
  - Suites run overnight (20:00 to 02:00) and the rehearsal build runs 02:00 to 05:00.
  - Checks, recapture and script run Sun 05:00 to 14:00. The 15:00 walkthrough stays.
  - It buys about 8 hours on 3 lanes, about 1.5-2 units.
  - The cost: no buffer on Sunday morning. If the suites or the build find a break, the walkthrough runs on a build with known issues, listed for the owner.

### C.2 Demand against capacity (honest)

**What the owner now wants IN, in units:**

| Group | Items | Units |
|---|---|---|
| Honesty and Site pages | DATA-12 (built), PB-4, PB-7, BL-50, L2, PB-1a, PB-1b, PB-5/6/8, RM-1, RM-2; PB-1c and DATA-6 if approved | 6.4 |
| EV for EV executives | PB-3 + DATA-11 | 1.25 |
| Portfolio | PF-T (building), PF-C + PF-W, PF-O2 + PF-O1 | 3.75 |
| Shared date range | SR-1, SR-2, SR-3 | 1.75 |
| Design foundation | UQ-0 sheet, UQ-1 tokens/type/Inter, UQ-3 states + quick wins, UQ-2 light/dark, UQ-4 formats | 4.0 |
| Any-range speed | UQ-6a 0.25; ANY-1 = AR-0, AR-1, AR-2 (3.0); ANY-2 core = AR-3, AR-6 (1.5), AR-4 with money receipts (2.5) | 7.25 |
| Test hygiene | FR-B | 1.0 |
| **Total** | | **about 25.4** |

**Capacity to Sat 12:00, at the observed 1.5-1.75 units per lane-day:**
- 3 lanes from now and a 4th from Thu ~13:00 (only if the e3d serve is stopped after the demo and free RAM stays at 3 GB or more): about 10.5 lane-days, so **15.5-18 units**.
- With option Y (Sat 20:00): **17-20 units**.

**It does not fit. The gap is about 6-10 units.**
- More lanes do not close it. The screens work shares the shell, the tokens and the Portfolio files, and ANY is a serial chain: PB-1 → AR-0 baseline → AR-1 → AR-2, AR-3, AR-4.
- **ANY-2's AR-4 is the item that cannot land in any arrangement.** It needs AR-1, PF-C and PF-O2 merged first, that is Fri afternoon at best, and it is 2.5 units.

### C.3 What a third lane starting NOW buys
- **About 1.2 lane-days (about 2 units) before Thursday noon.**
- **More importantly, it makes ANY-1 possible at all.** Lane C builds PB-1a, then PB-1b, while lane A builds PB-4/PB-7, so all of them merge by about Thu 12:00-15:00. AR-0's baseline can then run Thursday afternoon.
- Without lane C, PB-1b merges about Fri midday, AR-1/AR-2 cannot finish by Saturday, and ANY-1 drops.
- **Memory rule:**
  - Lane C pauses during the E5b live capture and Thu 07:00-12:30.
  - Targeted tests only.
  - The coordinator checks free RAM before each dispatch and pauses lane D first, then C.
  - AR-1's migration tests are the single heavy slot, never beside a build or serve.
- **Recommend yes: start lane C now with PB-1a.**

### C.4 The trade the owner must make (one answer; my recommendation first)

**Option X (recommended): keep the skeleton; move about 7 units after 17 Nov.**
- **Trades (moved after 17 Nov):**
  - AR-4, Portfolio money and evidence on stored rows (2.5). This is a workaround, named as one: the Portfolio stays fast only on pre-built ranges, which are the script ranges, the lens variants and the shared-range presets (last 7 days, last 30 days) added to the pre-build list. Other Portfolio ranges take about 10 s.
  - UQ-4, formats and language switcher (1.0 with its share of UQ-6a's formatting). The session is in English; thousands separators come with the quick wins.
  - FR-B (1.0). Its known failures are listed as known in Saturday's suite run.
  - PF-O1/O2, the scalable outcomes list (1.5). With 4-5 Sites today's grid fits. The approved design is built first thing after the demo.
  - Total about 6.0, plus option Y as the buffer.
- **Kept IN:**
  - every honesty and Site-page fix;
  - PB-3 + DATA-11 (EV);
  - Portfolio tabs, coverage once and the new words;
  - the shared date range;
  - the design foundation with **both** themes;
  - UQ-6a, ANY-1 (Site boards fast for any range) and AR-3 + AR-6 (Portfolio coverage on rows; Cold/EV boards under 1 s).
- **Risk stated plainly:**
  - ANY-1 finishes at the end of lane A with no slack. If AR-2 is not ACCEPTed by the freeze, it is held unmerged, and the boards use the pre-built ranges in the session.
  - UQ-2 (dark theme) is last in lane D. If it misses, the session uses the light theme.

**Option Z: everything IN.** Only by moving the session, or by accepting unreviewed merges. Neither is recommended.

### C.5 Order and lanes (option X)

| Lane | Order | Start rule |
|---|---|---|
| **A, server** | A2 PB-4 + PB-7 + BL-50 + L2 (+DATA-6 if approved) → A5 UQ-6a → A6 AR-0 + AR-1 → AR-2 | A2 the moment A1 merges |
| **B, Portfolio and shell** | PF-T (building) → B2 PF-C + PF-W → B4 SR-1 → SR-2 + SR-3 | B2 the moment B1 merges (A1 merged too) |
| **C, Cold/EV then server** (**now**) | A3 PB-1a → A4 PB-1b → AR-3 + AR-6 (after AR-1 merges) → PB-3 + DATA-11 → PB-1c if approved | now |
| **D, look** (Thu ~13:00, memory permitting) | UQ-0 sheet (owner approves Thu evening) → UQ-1 → UQ-3 + quick wins → C1 PB-5/6/8 + RM-1 + RM-2 → UQ-2 themes | after Thursday's demo |

**ANY-1 baseline ordering (rule 1 of section 0.2, kept):**
- AR-0's harness code may be written as soon as UQ-6a merges.
- The **baseline run** happens only after PB-4, PB-7, PB-1a and PB-1b have all merged. Expected Thu ~15:00 with lane C now.
- AR-1's migration freezes the stored body shape, so UQ-6a must merge before AR-1's first commit.
- AR-1's Postgres tests wait until the Thursday demo has ended.
- **DATA-12 already changed coverage, so AR-3 builds on the graded local days,** not on `dispatch_days`.

**Collision rules:**
- UQ-1 touches about 35 CSS files. Lane B rebases on UQ-1 once, and new lane B CSS uses semantic tokens only.
- SR-1 lays the top-bar row once. UQ-2's theme control goes into that row.
- C1 runs in lane D after UQ-3 because its files (Site pages) are the ones UQ-3's empty/loading states touch.

### C.6 Machine rules for every brief
- 16 GB machine, about 3.5 GB free with the demo app up. Docker's VM crashed once.
- **One heavy job at a time.** Named test files only: no full suites, prepares, recaptures or captures until the freeze.
- **Until Thursday's demo ends, do not touch:**
  - wt `AssetOpsV1-e3d`;
  - DB `assetops_polish_client6_test`;
  - ports 8990/5490;
  - Docker (no restarts).
- Each builder uses its own `*_test` DB.
- Builders:
  - Write/Edit only, no subagents.
  - PYTHONPATH absolute under the worktree (incl. `contracts`, `simulator`).
  - Commits end with the Co-Authored-By line. Never push. `git add -f` for `.agent`.

### C.7 Briefs

Briefs already written, unchanged in content (dispatch per C.5):
- **A2** PB-4 + PB-7 + BL-50 + L2: Opus, 1.1. Dispatch on A1 merge.
- **A3** PB-1a: Opus, 1.0. **Now, lane C.** Wt `AssetOpsV1-pb1`.
- **A4** PB-1b: Opus, 1.0. Lane C, after A3.
- **B2** PF-C + PF-W: Opus, 1.25. On B1 merge.
- **C1** PB-5/6/8 + RM-1: Sonnet, 1.1. Lane D. RM-2 is now approved, so it is added (0.1): hide the Findings lens chips on Cold, EV and Kisiwa client screens, with a test per Site type.
- **C2** PB-1c: on approval only.

Moved after 17 Nov: B3 PF-O and C3 FR-B.

**A5 UQ-6a server message seam.** Opus. Wt `AssetOpsV1-uq6a`, branch `task/UQ-6a-message-seam`. 0.25 unit. Lane A, after A2. **Must merge before AR-1's first commit.**
- **Goal:** server words are stored and sent as `{key, params}` and rendered for the request locale at read; never stored as composed text.
- **Spec:** `.agent/architect-plan-pre-client-2026-11-10.md` UQ-6a row (section 1 table) and §4.3 D-I18N.1, D-I18N.2.
- **Scope now, English only:**
  - the contract type and the render function;
  - `Accept-Language` resolution falling back to `en`, and `Content-Language` on responses;
  - the locale in the response-store key.
  - No catalogue move of existing words (UQ-6b, after).
  - No Babel formatting: it goes with UQ-4, after.
- **Files:** a new `backend/assetops_backend/i18n/` module (messages, render, locale); the response-store key builder; one existing server body converted as the reference user (the Pre-flight names the smallest one).
- **Tests:** render of `{key, params}`; unknown locale falls back to `en`; the cache key differs by locale; `Content-Language` header; the converted body is byte-equal in English to today.

**A6 AR-0 + AR-1 parity guard and read-row foundation (start of ANY-1).** Opus. Wt `AssetOpsV1-any1`, branch `task/ANY-1-rows`. 1.5 units. Lane A after A5.
- **Spec:** `.agent/architect-answer-any-range-speed-2026-11-10.md` §4 (cards AR-0, AR-1; risks table); D-ANY.1-4 and D-MONEY.1-4 in `build-sheet-OWN-GAPS-2026-11-08.md` (the generic row contract carries money receipts); D-I18N.1 (row bodies hold keys).
- **Order inside the slice:**
  1. The AR-0 harness: every story request plus seeded random ranges (board any day; Portfolio any from/to up to 31 days; historical `known_at`); row-based compose equals today's compose byte for byte. `perf_budget.py` arbitrary-range cases with the store off and no pre-build: board 2 s or less, Portfolio month 2 s or less.
  2. **The baseline run only after PB-4, PB-7, PB-1a and PB-1b are on main** (the coordinator confirms).
  3. AR-1: migration at the next free number (`0059` on main today) (`site_period_read`, `revision_provenance`); port and Postgres adapter; one query per Sites x range x kinds; PENDING-at-k from outbox/consumption; register schema accepts the new kinds; backfill CLI.
- **Tests:** migration up/down on the builder's own `*_test` DB (heavy slot, after the Thursday demo); adapter round-trip; PENDING-at-k; register accepts kinds; parity harness self-test (one deliberate mismatch fails).
- **Next card (AR-2, lane A) and AR-3 + AR-6 (lane C)** are dispatched on AR-1's merge, from the same answer file.

**B4 SR-1 shared range bar and state.** Opus. Wt `AssetOpsV1-pft`, branch `task/SR-1-shared-range`. 0.5 unit. Lane B after B2.
- **Goal:** one date range in a new top-bar row on every page; left menu unchanged.
- **Spec:** `.agent/architect-proposal-portfolio-layout-2026-11-10.md` "Item 12.5", SR.3 and SR.4; layout: `frontend/mockups/v71/portfolio-tabs.html` Change 0b (approved spec), top bar "All pages" in `estate-outcomes-scale.html`; D-UI.2 (the range lives in the address only).
- **Files:**
  - `SharedRangeBar` in `OperatorShellLayout`; the demonstration banner stays;
  - `useSharedRange`, returning `{from, to, known_at, preset}` and reading both address forms;
  - `withRange`; the rail `search`;
  - filling in the address on entry;
  - presets (no "Today" preset); the `known_at` label;
  - phone sheet; button 44 px, dates only;
  - picker accessibility (`aria-pressed` presets, labelled inputs, Escape and Cancel return focus).
  - PF-T's Portfolio date bar is replaced by this bar.
- **Tests:** the hook parses both address forms; rail links carry the range; presets; focus handling; the Portfolio reads the shared range. Vitest on the named files only. SR-2 (pages onto the range) follows on merge.

### C.8 Still pending with the owner
- **PB-1c** ("Analysed period" line): context being given.
- **DATA-6** (Kisiwa targets): context being given.
- **Choose option X (recommended) or say which trade differs, and option Y (last merge Sat 20:00) yes or no.**
- **Approve the UQ-0 v7.2 sheet** on Thu evening when it is drawn.

## 0. Agent-pace plan, re-assess Thu 12 Nov morning (added 2026-11-11; replaces the working-day calendar in sections 1 and 3.2; scope, order and decisions stay)

Owner, verbatim (`.agent/owner-units-by-friday-2026-11-11.md`): "the time estimates are for human developement, we should be able to do the indicated units in time for Friday" and then "let it not say which would land by Friday, we wait until Thursday morning for re-assessment".

- **You are right that my calendar was too slow.** I sized lanes at 1.5 units per *working* day. Agents run most of the 24 hours, every day of the week.
- **This section therefore sets the lanes and the order at agent pace, starting now.** It does not forecast what lands by Friday. Progress is re-assessed Thursday morning against the actual merges.

### 0.1 What agents actually delivered (git log on main, 8-11 Nov)

| Day | Merged slices (unit sizes from the build sheets; a few estimated) | Units merged | What else that day used |
|---|---|---|---|
| Sun 8 | Kisiwa K4b, K5, K6a, K6b, K6c, K7-D/F, K8, K9, K10; G3a; R-1; idle fuel A3 | about 7 | four lanes, owner away, specs already closed |
| Mon 9 | G1 1.75, G2 2.25, G3b 1.25, R4.1, POLISH-1, E2 fix A, C1-C4 (about 2.0) | about 8 | G1-G3b built mostly on Sun 8; E2 suites and E3 build |
| Tue 10 | C5, E5-FX, FX-EV-TITLE, FX-COLD-LINKED, FX-KOBO-GAPS 0.6, V3, PL-1, PL-2, DATA-2, FC 0.75 | about 3.8 | E3c/E4 checks, your walkthrough, six Architect answers |
| Wed 11 (to 05:00) | DATA-1 0.5 | 0.5 | E3d demo build |

- **Average: about 6 units per calendar day across 3-4 lanes, about 1.75 per lane per day.** It fell to about 4 on a day with a demo build and a walkthrough.
- **Review and fix rounds are part of that rate.** The four days had 110 review commits and 34 fix commits. Most slices take one fix round, and DATA-1, PL-1 and FX-COLD-LINKED were each rejected once first.
- **Those were small fixes to closed specs. The IN list is heavier, so expect the lower end of the rate:**
  - ANY-1/2 is a new migration with byte-for-byte parity proofs;
  - the tokens and dark theme touch 35 CSS files and about 19 SVGs, and need recaptures;
  - the Portfolio is a new tab layout.
- **At that rate the 22.7 IN units are several calendar days of agent work, not hours.** Thursday's re-assessment measures the real rate on this work.

**What bounds the pace:**
- **Your approvals.** Mockup first:
  - SR and PF need the final v7.1 mockup approved.
  - UQ-1 to UQ-3 need the v7.2 sheet, which does not exist yet (0.5 units to draw).
  - PB-1c and RM-2 need your nod.
  - No approval, no build.
- **Review gates.** One Opus review per slice; only High and Medium findings block a merge.
- **This machine (16 GB):**
  - Free RAM fell to 1.71 GB with one build plus serve, and Docker's VM crashed once at 02:05.
  - Safe limit: **3 builder lanes on targeted tests only**, and one heavy job at a time.
  - Until the Thursday demo ends, **2 lanes**, so the e3d serve and `assetops_polish_client6_test` are not disturbed.
- **Wednesday's fixed work** takes the coordinator and 1-2 lanes:
  - add-dates and the live dip capture, retakes;
  - the script pass and the DS-1f/DS-1b merge;
  - the D-E5.29-37 frontend fixes, E4-RESUME (b), KD-COVERAGE;
  - your afternoon walkthrough.
- **The end check** needs about 6-8 hours of a quiet machine: full suites, check-all, a fresh demo build (about 2 h 45 min) and live checks.

### 0.2 Lane setup and order, starting now

- **Lanes.** Three lanes at most, each in its own worktree and branch. Every lane runs targeted tests only. No full suites, no demo prepares and no recaptures until the end check.
- **Lanes A and B always run.** Lane C runs only while memory allows: the coordinator checks free RAM before each dispatch and pauses C first.
- **Lane C runs FR-B first.** FR-B was planned Wed 11-Fri 13 beside the IN work, and Wednesday's fixed work comes before both.

| Lane | Order (each item merges on review ACCEPT before the next one that depends on it starts) |
|---|---|
| **A, server and data** | PB-1a Cold analysed periods (1.0) → PB-1b EV (1.0) → PB-4, PB-7, DATA-6 + DATA-1 L2, BL-50 (1.35) → UQ-6a message seam (0.25) → ANY-1: AR-0 parity baseline, AR-1 stored rows, AR-2 board depth (3.0) → ANY-2: AR-3, AR-6 (1.5) → AR-4 money and evidence rows (2.5, after PF-C and PF-O2 merge) |
| **B, screens** | UQ-0 v7.2 sheet (0.5, then your approval) → UQ-1 tokens, type, Inter (1.25) → SR-1 shared bar (0.5, after v7.1 approval) → UQ-2 themes, UQ-3 states (1.5) → PF-C, PF-W, PF-T, PF-O2, PF-O1 (3.75) → SR-2/3, PB-1c (1.5) → UQ-4 formats (0.75) |
| **C, fixes (memory permitting)** | FR-B (about 1.0) → RM-1 roadmap words + RM-2 (0.6) → then OPTIONAL items in the section 3.3 order. Before Thursday's demo ends, lane C waits. |

**Why only one screens lane:** a second one would collide in the same files (the shell, the tokens and the Portfolio). Lane C takes the screens work that does not touch them.

**Rules that keep it safe at speed:**
1. **ANY-1's parity baseline (AR-0) is taken only after PB-1, PB-4 and PB-7 merge.** Otherwise its proofs are redone.
2. **AR-1's migration tests run in a quiet window,** never beside a build or serve.
3. **Builder briefs stay small** (code and tests first, captures last). The end check does every recapture once.
4. **Small fix rounds go to Sonnet,** and the coordinator verifies mechanical closures from the diff.

### 0.3 The end check: once, at the end

- **It runs once, after every IN item has merged:** full suites, check-all, one fresh demo build, live checks, recapture in both themes, and the PILOT-1 page with the script refresh. Your full walkthrough follows it.
- **Check-all alone runs on main after each batch of merges** (it is light).
- **No mid-way demo build.** It would test a half-built Portfolio and repeat the 6-8 heavy hours, which goes against your overnight instruction to batch heavy work at the end.
- **On Thursday morning I re-assess from the merges and the measured rate:** the order, the session date (sections 3.2 and 5), and whether any OPTIONAL items fit.

### 0.4 Approvals needed today to unblock this

1. **The final v7.1 Portfolio mockup** (`frontend/mockups/v71/portfolio-tabs.html`, with the shared date range in Change 0b). It gates SR-1 and all of PF.
2. **The v7.2 foundation sheet** as soon as it is drawn (lane B's first item). Also **Inter** as the font, and **the theme follows the computer's setting**. They gate UQ-1, which every later screens item builds on.
3. **The item 11 changes:** hide the lens chips (RM-2), the "Analysed period" line (PB-1c), the Kisiwa targets (DATA-6), and the extra Cold and EV days (DATA-11, for OPTIONAL #1).
4. **Present the session in English.** French and Swahili stay OPTIONAL, so lane B does not carry 3.25 units of catalogue work.
5. **Three lanes, with agents running overnight and at the weekend.** The coordinator keeps heavy jobs to one at a time and pauses lane C when memory is short.

### 0.5 BeagleBone (TEL-08): OPTIONAL for the client demo, after the IN items in lane C

Owner, verbatim (same file): "on a side note, i have also obtained SD card and will get the beaglebone ready by EOD today"

**Where it stands.** The spec is `.agent/build-spec-telemetry-2026-10-27.md` §TEL-08; the board ruling is `.agent/architect-beaglebone-wheezy-2026-10-29.md`.
- The field poller (`field/assetops_field`), the GX-shaped emulator and the gateway are built and proven on the laptop (TEL-01 to TEL-06).
- TEL-08 itself was never built. `host/tests/field_bench.py` has helpers only; its `setup`, `activate` and `read` commands do not exist yet.
- The board's own OS (Debian 7, Python 2.7) cannot run the code (requires Python 3.12+). Hence the SD card.

**What you do (about 30-40 min, no code):**
1. **Flash the card.** Write the official BeagleBone Black **Debian 13 IoT** microSD image (kernel 6.x, Python 3.13) from beagleboard.org to the card with Balena Etcher or Raspberry Pi Imager. If only an "eMMC flasher" image is offered, do not use it.
2. **Boot from the card.** Hold the **S2 button** while you power on (5 V 2 A barrel, or USB power). The board's own memory is left untouched, so this is reversible.
3. **Network.** Connect the board by **Ethernet to the same router as the laptop**, with internet through it (for `apt` and time sync). Do not use USB networking.
4. **Access.** Log in once (default user `debian`) and add the coordinator's SSH public key to `~/.ssh/authorized_keys`. No passwords are shared in chat. The coordinator then creates the non-root `assetops` user.
5. **Laptop firewall (admin).** Allow inbound TCP **8443** (upload server) and **5020** (device emulator) on the Private/LAN profile.
6. **Report:** the board's IP, `uname -r`, `python3 --version`, and `timedatectl show -p NTPSynchronized` (must be `yes`).

You create no upload credentials. The bench `setup` command issues the gateway's upload credential and a 7-day self-signed TLS certificate, and they are copied to the board.

**What we build and verify once it is up (about 0.75 units, plus one heavy run slot of about 1 hour):**
- **Build** `field_bench.py` `setup`, `activate` and `read`, per §TEL-08. They use their own test database, `assetops_tel_bbb_test`, never the demo database.
- **Copy** the code to `/opt/assetops/src` and record matching tree hashes on the laptop and the board. Nothing is pip-installed on the board.
- **Run** gateway and poller on the board, with the emulator and the TLS upload server on the laptop. The replay is the Kobo GX-shaped window at rate 12.
- **Gates (TEL-05):** every upload receipt COMPLETED, accepted evidence for every role, and the assessment completes.
- **Uplink fault test:** stop the laptop upload server for 5 min. The board's queue must rise and drain back to 0, with no gap in the evidence.
- **Clock:** offsets within ±50 ms on the board and the laptop.
- **Record:** a claim line, "BeagleBone Black · Debian 13 IoT · kernel … · Python … · commit … · tree …".
- **Stop and report** if Linux needs any code change, or if the clock offset cannot be met.

**Where it sits.**
- Lane C, after FR-B and RM-1/RM-2, ahead of the other OPTIONAL items.
- Its 1-hour run takes the single heavy-job slot, never beside a build, a serve or AR-1's migration tests.
- It must finish before the end check. It never touches the Thursday e3d build.
- The code copy and the clock setup can be done as soon as you report the IP. They are light.

**Why OPTIONAL, not IN:**
- **For a business buyer the value is Low-Med.** The story screens already show the readings arriving.
- **For a technical buyer, or a client asking "what hardware sits on site?", the value is Med-High.** It turns "the gateway was tested on a laptop" into "it runs on a $60 edge box and survives a 5-minute uplink loss without losing data".
- **Best use:** one slide or a 2-minute live clip in the technical script, and a pilot-readiness line in PILOT-1 ("tested on BeagleBone Black"). It is not a beat in the client story.
- **Not shown live in the session.** A live board adds a network and clock dependency to the room.
- **It moves to IN** if you tell me the client's evaluator is technical or asks about on-site hardware.

## 1. In plain words

- **The test I used:** would a client deciding whether to buy notice it, and would leaving it out make something on screen look broken, contradictory or untrue? Speed, honesty and the first impression score high. Things that only matter at 100+ Sites, in a second language nobody has reviewed, or behind sign-in score low for this session.
- **IN for the client demo: about 22.7 units** (plus FR-B this week). That is **3.3 units less than my 26-unit plan**, even though the non-Kobo fixes turned out 2.7 units bigger than the placeholder (section 3).
- **OPTIONAL, if time: about 10 units**, ranked. **AFTER the client demo:** everything else, including sign-in, multi-currency, the full UI uplift and the engineering clean-up.
- **Dates (working days from Mon 16 Nov, weekends not assumed):** the IN build work finishes **Wed 25 to Thu 26 Nov**. With 5 working days for the final build, checks, your walkthrough and the script refresh:
  - **Tue 8 Dec: all IN items fit, plus about 6-7 units of OPTIONAL items, plus a 1-unit reserve for Thursday's feedback.** Recommended.
  - **Tue 1 Dec: fits only with two cuts** (Portfolio money/evidence speed AR-4, and the dark theme), so about 19.2 units, no reserve, and the Portfolio stays on its pre-built ranges in the session.
- **Pushback, honestly:** French and Swahili (3.25 units) show nothing in an English session and cannot be switched on without reviewers you have not named yet; scale features (region, 100-Site rows, condensed dots; 1.25 units) are invisible with 4 demo Sites. I moved them out of IN. Your approvals of them stand; only the timing changes.

## 2. Every open item

Value = what a converting client would notice. Rec = IN client demo / OPTIONAL (if time, ranked in section 3.3) / AFTER. Source: W-n = your 2026-11-10 walkthrough item n; BL = backlog; owner dates as given. Sizes in build units (about half a lane-day each at today's pace).

### 2.1 Walkthrough comments not yet built

| Id | What it is | Source | Size | Depends on | Value to a converting client | Risk if left out | Rec |
|---|---|---|---|---|---|---|---|
| PB-1a | Cold room pages show their analysed periods on any day or week | W-11 | 1.0 | - | **High:** today a day or week reads "Unknown" everywhere; after, the 4.9 °C event and stock risk show | Cold pages look broken the moment anyone leaves the script | IN |
| PB-1b | The same for the EV depot (source judged per period) | W-11 | 1.0 | - | **High:** same as PB-1a | EV pages look broken off-script | IN |
| PB-1c | "Analysed period" line with links under the date bar | W-11 | 0.25 | PB-1a/b, SR-1; your nod | Med: says which hours the figures cover | figures without their period | IN |
| PB-4 | Days never analysed stop saying "Checked: nothing to report" | W-11 | 0.5 | - | Med: removes an over-claim a sharp client can catch | honesty defect on real Sites | IN |
| PB-7 | Coverage counts start when a Site's readings began, not 31 days back | W-11 | 0.25 | - | Med: "20 of the last 31 days have no readings" on a new Site reads as failure | Kisiwa looks unreliable | IN |
| DATA-6 | Kisiwa targets: avoidable generator minutes 0, unserved critical supply 0 | W-11 (story change) | 0.25 | DATA-1 (done) | Med: removes three "No objective declared" lines on the diesel story | the board looks unconfigured | IN |
| RM-1 | Unbuilt integrations read as a short roadmap ("Billing records are not connected yet") | W-11 | 0.5 | - | **High:** 16 error-looking values become a credible roadmap | pages read as broken, not as "coming" | IN |
| RM-2 | Hide the Findings lens chips on Cold, EV and Kisiwa | W-11 (needs approval) | 0.1 | your approval | Low-Med: removes dead "Not available yet" chips | a small dead end | IN if approved |
| PB-3 + DATA-11 | EV charging graded by charger status, plus an ordinary story week for Cold and EV | W-11 | 1.25 | PB-1 | Med (**High if the client runs EV or cold rooms**): the EV income card stops saying "Not known yet" beside USD 4.50; weeks show more than one event | one contradiction on the EV Grow card; presenter avoids it (D-E5.36) | OPTIONAL #1 |
| DATA-8 | Kisiwa productive loads (pump, cold store) and a price per kWh | W-11 (needs approval) | 0.5 | your approval | Med: Kisiwa's Grow card gains a figure | Grow empty on the diesel Site | OPTIONAL #4 |
| DATA-5 | Gateway health records for Cold, EV and Kisiwa | W-11 | 0.5 | Kobo Health recapture | Low-Med: Health tab shows "Unknown" x8 | Health tab not shown | OPTIONAL #5 |
| DATA-4 | EV site diagram: connector rating, grid meter | W-11 (needs approval) | 0.5 | your approval | Med for an EV client, else Low | "connector capacity not read" | OPTIONAL #6 |
| DATA-10, DATA-13, BL-48 | Kisiwa generator service plan; due dates on story Actions; Grow lines on days with no complete readings | W-11, BL | 0.65 | - | Low-Med: three small "not set" lines | minor gaps a client may ask about | OPTIONAL #7 |
| DATA-7 | Kisiwa simulated over whole days, not only 6 pm to noon | W-11 (needs approval) | 1.5 | your approval; +prepare time | Med: today every Kisiwa day is "partly" covered, the pattern you rejected for Kobo | a client asks why every day is partial | OPTIONAL #8 (decision 6) |
| DATA-12; EV revenue measure; work-record cost | Longer Cold failure window; EV revenue target; repair costs on work records | W-11 | ~0.25; ~1; ~1 (est.) | billing / work-order integration | Low: RM-1 wording covers them | none | AFTER |
| PF-C | Evidence coverage shown once on the Portfolio | W-2 | 0.5 | SR-1 | **High:** the opening page reads cleaner | repetition on the first page | IN |
| PF-T | Portfolio tabs (Overview, Act first, Outcomes by site, Opportunity, What changed, Scope & coverage) | W-2, W-5.1/5.2 | 1.0 | SR-1, UQ-3, v7.1 approval | **High:** the opening page | crowded first page | IN |
| PF-W | "Checked" becomes complete / partial / too few / no readings received / still processing / not analysed yet | W-3, W-5.3 | 0.75 | - | **High:** "7 of 8 hours checked" stops implying the system failed to look | the main coverage words confuse | IN |
| SR-1..3 | One shared date range at the top of every page; left menu unchanged | W-4, W-12.5 | 1.75 | v7.1 approval, UQ-1 | **High:** one control, any page, any range | each page keeps its own date form | IN |
| PF-O1, PF-O2 | Scalable "Outcomes across the estate", grouped by outcome | W-9, W-12.1/12.3 | 1.5 | PF-T | Med-High: the list shows it will handle a large estate | grid looks cramped as Sites grow | IN |
| PF-O3 | Overview card dots condense above 8 Sites | W-9 | 0.25 | PF-O1 | Low: invisible with 4 Sites | none in the demo | AFTER |
| PF-R | Region attribute on Sites, with filter and grouping | W-12.2 | 0.25 | region values | Low: the control is hidden until Sites have regions | none with 4 Sites | AFTER (IN if the client asks about regions) |
| AR-7 | Outcome rows from stored rows (for 100+ Sites) | W-9 | 0.75 | ANY-2 | Low: invisible under about 25 Sites | none in the demo | AFTER |
| T-5.4 | "Complete readings" threshold per portfolio (80% today, one global file) | W-5.4 | ~0.5 (est.) | tenant settings | Low | none | AFTER |
| T-5.5 | Outcome map as a config file (today a reviewed code table) | W-5.5 | ~0.75 (est.) | - | Low: the client never sees it | none | AFTER |
| FCF-1 | Findings card counts Cold/EV "awaiting verification"; Portfolio Cold/EV rows read "Action agreed" (with BL-47) | W-7 | 1.0 | FC (done) | Med: removes the "mini-grid Sites only" note and a gap between screens | the note stays, which is honest | OPTIONAL #2 |
| D-E5.25 | An "Act first" count on the Findings page | W-7 | 1.0 | - | Low | none | AFTER |
| PR-1/2a | Price-it, first step: "Set a price" / "What is needed" on every unpriced item, and a read-only price page with history | W-10, W-12.4 | 0.75 | mockup first | Med-High for a commercial buyer: answers "how would I price this?" on screen | presenter answers verbally; the admin tool exists | OPTIONAL #3 |
| PR-2b..5 | Price-it editing: sign-in write path, recalculation, model blocks | W-10 | 2.0 | BL-54 sign-in | Med | - | AFTER |
| UQ-0..4 | Design foundation: v7.2 sheet, tokens, 12/14 px type, Inter, light and dark themes, empty/loading states, number and date formats | W-12.1, W-13 | 4.0 | v7.2 approval | **High:** first impression, "modern" | the app looks dated next to the story | IN (dark theme cut on 1 Dec) |
| UQ-6a | Server words stored as message keys, not sentences | W-13 | 0.25 | - | none visible | stored speed rows rebuilt later (~1-2 units) | IN |
| UQ-5, 6b, 7, 8 | French and Swahili: all words into catalogues, drafts, long-text guard | W-13 | 3.25 | reviewers named | Low unless the client works in French or Swahili; nothing changes in English | none in an English session | OPTIONAL #9 (decision 2) |
| BL-69 rest | Component library, chart standard, page-by-page uplift, accessibility pass | W-12.1 | ~7.25-8.0 | UQ | Med, long term | - | AFTER (first focused work after) |
| BL-67 | Several currencies, structured tariffs, restatement notes | W-1 | 3.0-3.5 | your currency answers | Low now: demo Sites use one flat price each | - | AFTER |

### 2.2 Backlog items

| Id | What it is | Source | Size | Depends on | Value to a converting client | Risk if left out | Rec |
|---|---|---|---|---|---|---|---|
| ANY-1 (BL-66) | Site boards fast for any range (under 2 s) | owner 11-03, 11-10 | 3.0 | PB-1, PB-4, PB-7, UQ-6a | **High:** off-script boards take 10-36 s today | "try another week" stalls live | IN |
| ANY-2 core (BL-66: AR-3, AR-6, AR-4 with money receipts) | Portfolio fast for any range; Cold/EV boards under 1 s | owner 11-10 | 4.0 | ANY-1, PF-C, PF-O2 | **High:** the Portfolio is the opening page | presenter stays on pre-built ranges | IN (AR-4 cut on 1 Dec) |
| AR-5 (BL-66, with BL-64/65) | Retire pre-loading | - | 0.75 | ANY-2 | none visible | - | AFTER |
| BL-50 | Site "Why?" sees the same issues as the board | BL | 0.25 | - | Med: "Why?" is a presented beat; on the Cold failure day it misses one issue | "why" gets an incomplete answer | IN |
| DATA-1 L2 | Kisiwa finish check covers windows without a selection | DATA-1 review | 0.1 | - | none; protects the build | a bad Kisiwa day slips into the build | IN |
| PILOT-1 (new) | One page in the client script: how a client starts (onboarding steps, integration ranking D-E5.35, what sign-in adds) | Architect | 0.25 | RM-1 | **High:** a converting client asks "what happens next?" | no path to pilot on paper | IN |
| BL-54 | Sign-in, named users and roles | BL | not sized (~3-5) | - | Med: asked about, answered by PILOT-1 | - | AFTER (pilot-critical) |
| BL-53, 55, 57, 59 | Real-source clock proof; production scheduler and onboarding runbook; public upload path for the demo build; historical data import | BL | not sized | BL-54 for some | Med as questions; PILOT-1 answers them | - | AFTER (pilot-critical) |
| BL-31, BL-45 | A real later "Change made" for Cold/EV; mill Actions on the Site boards | BL | 0.5; 1.0-1.5 | - | Low-Med: the script uses Kobo and the mill route | - | AFTER |
| BL-13, BL-16, BL-56 | Days line under board rows; idle fuel in the Kobo generator law (disclosed); demo banner only on demo data | BL | 0.25; 1.0; ~0.1 | - | Low | - | AFTER |
| BL-01..05, 08, 11, 12, 15, 22, 35, 51, 58 | Clean-up, refactors, renames and internal guards | BL | ~4.0 | - | none visible | - | AFTER |
| BL-06, 07, 09, 10, 14, 17, 18, 20, 21, 23-26, 32-34, 36-44 | Story-depth edge cases not on the script (each has a presenter rule) | BL | ~5+ (several unsized) | - | Low: only off-script | covered by "present less" rules | AFTER |
| BL-30, 46, 49, 52, 60-63 | Demo tooling and test debt (BL-63 is a producer fix the build check already covers) | BL | ~1.5 | - | none visible | - | AFTER |

## 3. Sequence of the IN items

### 3.1 Two lanes (pace about 1.5 units per lane per working day, including review and one fix round; 1.25 when slow)

Lane A, server and data (10.6 units):

| # | Item | Size | Cum. | Done by (1.5/day) |
|---|---|---|---|---|
| A1 | PB-1a Cold analysed periods | 1.0 | 1.0 | Mon 16 |
| A2 | PB-1b EV analysed periods | 1.0 | 2.0 | Tue 17 |
| A3 | PB-4, PB-7, DATA-6 + DATA-1 L2, BL-50 | 1.35 | 3.35 | Wed 18 |
| A4 | UQ-6a server message seam | 0.25 | 3.6 | Wed 18 |
| A5 | ANY-1: AR-0 parity baseline, AR-1 stored rows, AR-2 board depth | 3.0 | 6.6 | Fri 20 |
| A6 | ANY-2: AR-3 coverage rows, AR-6 work lists | 1.5 | 8.1 | Mon 23 |
| A7 | ANY-2: AR-4 evidence and money rows with receipts (MN-1/2/3) | 2.5 | 10.6 | Wed 25 (Thu 26 slow) |

Lane B, screens (10.35 units; UQ-0 this week):

| # | Item | Size | Cum. | Done by (1.5/day) |
|---|---|---|---|---|
| B0 | UQ-0 v7.2 foundation sheet (you approve it by Mon 16) | 0.5 | 0.5 | Fri 13 |
| B1 | UQ-1 tokens, type, Inter, style ratchet | 1.25 | 1.75 | Mon 16 |
| B2 | SR-1 shared date bar (v7.1 approved by Tue 17) | 0.5 | 2.25 | Tue 17 |
| B3 | UQ-2 light and dark themes; UQ-3 empty and loading states | 1.5 | 3.75 | Wed 18 |
| B4 | PF-C, PF-W, PF-T, PF-O2, PF-O1 (Portfolio tabs, words, outcomes list) | 3.75 | 7.5 | Fri 20 |
| B5 | SR-2/3 every page on the shared range; PB-1c analysed-period line | 1.5 | 9.0 | Mon 23 |
| B6 | UQ-4 formats; RM-1 roadmap words; RM-2 | 1.35 | 10.35 | Tue 24 (Wed 25 slow) |

Shared: PILOT-1 0.25 (with the script refresh) and E-final 1.5 (one demo build, end-game suites, live checks, recapture in both themes, both scripts refreshed). **IN total: 10.6 + 10.35 + 0.25 + 1.5 = 22.7 units.**

Why this order (causal, not convenient):
1. PB-1, PB-4 and PB-7 change what boards compose, so they land before AR-0 takes its byte-for-byte baseline; otherwise ANY-1's proofs are redone.
2. UQ-6a lands before AR-1 freezes the stored-row shape (words as keys from day one).
3. **Changed from the 26-unit plan:** lane B now builds the Portfolio (B4) before moving every page to the shared range (B5), so PF-C and PF-O2 are merged by Fri 20 and AR-4 (which touches the same Portfolio read) never waits.
4. SR-1 before PB-1c, UQ-2 and UQ-4: the top bar is laid out once. SR-2 after PB-1: Cold and EV "latest event inside the range" uses PB-1's rule.
5. UQ-1 and UQ-3 before the Portfolio, so it is written on the new tokens and states and never restyled.
6. OPTIONAL items fill gaps: lane A after A7, lane B after B6.

### 3.2 Date cut-offs (working calendar; no demo build is prepared on the 3rd-5th of a month)

E-final needs **5 working days**: (1) freeze, end-game suites, fixes; (2) demo build and live checks; (3) recapture and script refresh with PILOT-1; (4) your walkthrough; (5) one fix round and rebuild, or buffer. The final build is prepared the day before the session so "yesterday arrives" can be shown live.

| Session | Build freeze | E-final days | What fits |
|---|---|---|---|
| **Tue 1 Dec** | Tue 24 Nov | Wed 25, Thu 26, Fri 27, Mon 30 (prepare Mon 30) - only 4 days, no buffer | IN minus AR-4 (2.5) and UQ-2 dark theme (1.0) = **about 19.2 units**. Portfolio money and evidence stay computed on request: presenter stays on pre-built Portfolio ranges. No OPTIONAL items, no reserve for Thursday's feedback. You approve v7.2 and v7.1 by Mon 16. |
| **Tue 8 Dec (recommended)** | Mon 30 Nov | Tue 1, Wed 2 (rehearsal build allowed on the 2nd), Thu 3, Fri 4 (walkthrough, script), Mon 7 (final prepare) | **All IN (22.7)**, plus about 6-7 OPTIONAL units in the 3 spare lane-days (Wed 25 to Mon 30), plus a 1-unit reserve for Thursday's associates' feedback. |

A session on Thu 3 or Fri 4 Dec is possible only with the final build on Wed 2 and no slip at all; I do not recommend it.

### 3.3 OPTIONAL ranking (what to add, in order, if the 8 Dec date is set)

1. PB-3 + DATA-11 (1.25, lane A): first if the client runs EV or cold rooms.
2. FCF-1 with BL-47 (1.0, lane A).
3. PR-1/2a price-it first step (0.75, lane B; mockup first).
4. DATA-8 Kisiwa productive use and price (0.5; needs approval).
5. DATA-5 health records (0.5). 6. DATA-4 EV diagram (0.5; approval). 7. DATA-10, DATA-13, BL-48 (0.65).
8. DATA-7 Kisiwa whole days (1.5; approval; adds prepare time).
9. French and Swahili (3.25): only if a reviewer is named by Fri 20 Nov and the client prefers that language.

With 8 Dec, items 1-7 fit (about 5.2 units, at the slower pace) plus the 1-unit reserve; 8 and 9 fit only if the build runs at the faster pace and the reserve is unused.

## 4. Where the 26-unit plan changes, and why

| Change | Units | Why |
|---|---|---|
| Non-Kobo fixes: placeholder 1.5 becomes 4.2 (PB-1a/b/c, PB-4, PB-7, DATA-6, RM-1, RM-2, BL-50, L2) | +2.7 | The audit reported. PB-3 goes to OPTIONAL with DATA-11: alone it shows nothing, because the EV story has only 16 min of charger status. |
| French and Swahili catalogue work (UQ-5, 6b, 7, 8) to OPTIONAL | -3.25 | Nothing changes on screen in English, no reviewer is named, and the release rule keeps both languages off until reviewed. The seam (UQ-6a) and formats (UQ-4) stay IN, so nothing is redone later. |
| AR-5 and AR-7 to AFTER | -1.5 | Invisible with 4 Sites; the in-memory outcomes route is correct up to about 25 Sites. |
| FCF-1 to OPTIONAL | -1.0 | It was already cut #2; the card's "mini-grid Sites only" note is honest. |
| PF-O3 and region to AFTER | -0.5 | Invisible with 4 demo Sites. |
| PILOT-1 added | +0.25 | A converting client needs a path to a pilot; RM-1 and the integration ranking make one page cheap. |
| Lane B order: Portfolio before SR-2 | 0 | AR-4 no longer waits for the Portfolio. |
| Calendar | - | Earlier "earliest credible Mon 30 Nov" is withdrawn: full IN needs Tue 8 Dec; 1 Dec only with the section 3.2 cut. |
| **Net** | **26.0 to 22.7** | |

## 5. Your decisions that change the scope (my recommendation in bold)

1. **Client session date. Recommend Tue 8 Dec.** 1 Dec drops Portfolio any-range speed (AR-4) and the dark theme, with no buffer and no room for Thursday's feedback.
2. **French and Swahili before the session? Recommend no: present in English.** Keep the approval; build the catalogues after the session, or as OPTIONAL #9 only if you name a native Swahili and a fluent French reviewer by Fri 20 Nov and the client prefers that language.
3. **What does the client operate (diesel or solar mini-grids, cold rooms, EV depots)? Recommend telling me before Mon 23.** If EV or cold rooms, PB-3 + DATA-11 and DATA-4 move up to IN; if mini-grids, Kobo and Kisiwa lead (D-E5.36) and DATA-8 moves up.
4. **Approve the v7.2 foundation sheet and Inter by Mon 16, and the final v7.1 Portfolio mockup by Tue 17. Recommend yes, theme follows the computer's setting.** Each day of delay moves lane B and the date by a day.
5. **Approve the item 11 story and screen changes: RM-2 hide lens chips, the "Analysed period" line, Kisiwa targets, extra Cold and EV days. Recommend yes to all.**
6. **Kisiwa whole-day simulation (DATA-7, 1.5) and productive use (DATA-8, 0.5). Recommend DATA-8 yes (OPTIONAL #4), DATA-7 after the session**, with a presenter line: "Kisiwa's recorder in this story runs 6 pm to noon, so each day is partly covered." If you find that as indefensible as the Kobo pattern, DATA-7 moves into the reserve.
7. **Scale and region (PF-O3, region, AR-7). Recommend after**, unless the client has more than about 8 Sites or asks about regions; the demo data has no large estate to show it on.
8. **Per-portfolio threshold and outcome-map config file. Recommend after**; neither is visible to a client.
