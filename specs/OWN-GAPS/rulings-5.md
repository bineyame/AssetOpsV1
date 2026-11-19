## v3 fallback ruling (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9` on main), under the owner's 2026-11-08 delegation. Read at main `06a921a94`: FX-KOBO-GAPS review finding 1 (Medium) and Lows 2-4, `tools/demo_combined_finish.py:674-706`, `tools/demo_combined.py:872-873`. Nothing was run.

### D-E5.21 WK-GAP gates the v4 calendar only; on v3 it reports (option a)

- **Ruling.** D-E5.12's "pass on both calendars" stands, and D-E5.13 item 3's "fails on v3, the intended alarm" is withdrawn. The alarm was meant to catch a wrong default calendar, not an explicit fallback; the v4 L0 test and `DEFAULT_FILE` already catch the former.
- **Why not a diagnostic-only fallback (b).** Thursday-morning case: if tonight's v4 build fails its stop rules, the v3 calendar is the last accepted demo build (honest data, the older 2 missed / 3 partly checked week) and about 2 h 20 m to rebuild, so it is the realistic thing to present. A build that ends SELF-CHECK FAILED cannot be presented, and `add-dates` (script Step 7) would print a failure in front of the audience. The fallback must be presentable.
- **Rule.** WK-GAP gates (asserts the week and month patterns) only when the built `days.json` `schema.version` is 4 or higher. Below 4 it returns the read pattern with `"gated": false, "calendar": <source>` and passes. Key on the schema version, not the file name.

### Card FX-KOBO-V3 (Sonnet, XS, about 40 lines; fresh Claude review; may merge Wednesday)

Branch `task/FX-KOBO-V3`.
1. `tools/demo_rows.py`: pure `gap_gated(days_schema) -> bool` (version >= 4). `tools/demo_combined_finish.py` `wkgap`: compute both patterns as now; raise only when gated; on v3 return them with `gated: false`. Docstring cites D-E5.21.
2. `tools/demo_combined_kobo.py:563` (review Low 2): the manifest `"days"` label comes from `days.json` `source`.
3. L0: `gap_gated` true for v4, false for v3; the client4 v3 fixture (2 NO_DATA + 3 PARTIAL) raises when gated and returns `gated: false` when not (must-fail: drop the gate and the ungated case raises). Review Low 3: a v4 parametrisation of the positive half of the S-10 fillable test.
4. Gates: guards A, W, V and N, `test_demo_story_days.py`, the demo_rows L0. No build, no full suite. Tonight's v4 build does not wait for this card.
5. Review Low 4 (B-16 keeps the six fill days): no change; backlog.

Decision logged for owner review: **D-E5.21** the v3 fallback is a presentable build; WK-GAP gates v4 only.

## Money snapshot ruling (2026-11-10)

- Architect: Claude (fresh `assetops-architect`). Full answer: `.agent/architect-answer-money-snapshot-2026-11-10.md`.
  Owner question verbatim: `.agent/owner-money-snapshot-2026-11-10.md`.

### D-MONEY.1 Store the amount with its receipt (hybrid), rebuild on event, never recompute on read

Each stored money line carries `amount` (or `low`/`high`), `currency`, `basis` and
`receipt{v, formula, qty, unit, rate, rate_unit, rate_ref, segments: null, fx: null}`. The amount is computed from the
unrounded quantity and rounded to the cent half-up; a rebuild must reproduce it exactly. A corrected price or tariff
is a new assumption revision, and the affected days are rebuilt as new snapshot revisions. Old revisions are kept, so
"as known at k" holds. Amount-only storage (no audit, no explainable restatement) and recompute-on-read (slow,
code-dependent) are both refused.

### D-MONEY.2 Original currency only; conversion is read-time and named

No converted amount is stored. A later reporting-currency view converts at read time from an append-only, bitemporal
FX rate store (BL-67a), and shows the rate, its source and its date. Until then mixed currencies stay
`CURRENCY_MIXED`.

### D-MONEY.3 No stored totals

No row kind, migration or builder writes a cross-Site, cross-currency or verified-result total (A6, OWN-1104 R10,
FUEL-1 A2). The BL-66 estate roll-up rows hold per-Site money lines only. MN-3 adds a guard for this.

### D-MONEY.4 It lives in the BL-66 design; no separate ledger now

Day money stays in `site_day_snapshot.money`. Window, potential and evidence money go in `site_period_read`, under the
`money.lines` kind (with `money.potential` per Site-local day), in AR-4. `input_fp` includes every `rate_ref`. The
existing bitemporal assumption store is the minimal tariff catalogue. AR-1's generic contract takes this shape before
its migration is written. No new columns.

### D-MONEY.5 Sizing

MN-1 (receipts on `productive_kwh.money`, 0.25), MN-2 (stored potential money, 0.5) and MN-3 (no-total guard, 0.25)
fold into AR-4. ANY-2 goes from 3.75 to 4.75 units. ANY-1 is unchanged. FX, structured tariffs and the restatement
note are BL-67.

### Owner questions (open)

1. Reporting currency policy: one reporting currency? Which one, and which rate (transaction-date, period-average, or
   report-date)?
2. Restatement display: (i) the restated figure with a "restated on <date>, was X" note (the Architect's
   recommendation), or (ii) the original figure plus an adjustment line in the period of the correction?
3. Will AssetOps ever issue or settle invoices? If so, an immutable settlement ledger is needed later.

### Decisions logged for owner review

- **D-MONEY.1** Store the amount together with its receipt; rebuild on event.
- **D-MONEY.2** Store the original currency only; no stored conversions.
- **D-MONEY.3** No stored totals.
- **D-MONEY.4** Money goes in the BL-66 rows, not a separate ledger.
- **D-MONEY.5** MN-1/2/3 fold into AR-4 (+1.0 unit); the rest is BL-67.

## Portfolio lens ruling (2026-11-10)

- Architect: Claude (fresh `assetops-architect`, owner delegation `.agent/owner-away-architect-decides-2026-11-08.md`).
  Owner question verbatim: walkthrough item 6, `.agent/owner-walkthrough-2026-11-10.md`. Ruling: **(c) both**.
- Verified in code: `backend/assetops_backend/estate/portfolio.py:842-930`. The lens filters `members` into `shown`
  only. It changes `rows`, `total_count`, `next_cursor`, `selection_token` (lens is in the token, so the cursor is
  lens-bound) and the echoed `lens`. Everything else (summary counts, `placement_counts`, `category_counts`, claims,
  value cards, objectives, evidence prompt, opportunity, progress, money, footer, scope disclosure) is computed over
  `members` or the window and is identical for every lens. The outcome summary read is window-keyed and never refetched
  on a lens change. So only the "Where management should act first" panel depends on `lens`.

### D-E5.22 Frontend: keep the page while the lens loads (card PL-1, Sonnet, 0.25 unit; lands any time, no rebuild)

`frontend/src/estate/EstatePortfolio.tsx` `EstatePortfolioPage`: when the held read is `loaded` and differs from the
new key **only in lens** (same `from|to|known_at`), keep rendering the held body. The page never mixes two reads:
when the new response arrives it replaces the whole body (as today), so every figure stays from one response,
"as known at k". While it is pending:
- `PriorityPanel` gets `pending: EstateLens | null`. The chip for the pending lens is `aria-pressed`. The section has
  `aria-busy="true"`. Both count spans read "Loading findings". The table body is one row,
  `data-portfolio-loading-rows`: "Loading the {label} findings." The held rows are never shown under the new lens.
  "Load more Findings" is hidden. Early warnings stay (window-keyed).
- The other panels stay as rendered (the server values are lens-independent, see above).
- A refusal replaces everything, as today. A window change still shows the full loading slot.
- Rapid clicks: the existing `live` guard keeps only the last lens.
Tests in `frontend/src/estate/__tests__/estatePortfolio.test.tsx` (deferred-promise client): (1) on a lens click,
the cards, pulse and context stay in the DOM and `data-estate-loading` is absent; (2) the panel shows the loading
row, `aria-busy`, and no held row; (3) when it resolves, the new rows and `total_count` are shown; (4) a refusal on
the lens read replaces the page; (5) cost, then risks quickly, shows the risks body only. No captures change (the
settled states are unchanged). MOCK DEVIATION: none (v69/v70 do not specify a lens loading state).

### D-E5.23 Tools: pre-build the lens variants (card PL-2, Sonnet, 0.25 unit; MUST merge before tonight's build)

`tools/demo_combined.py` `prebuilt_routes`: for each of `portfolio.week`, `portfolio.S` and `portfolio.month`, also
add `portfolio.{name}.{lens}` for `cost`, `risks`, `opportunities`, with the same query and `("lens", lens)` in place
of `("lens", "all")` (the response store keys the parsed lens, `chain/response_store.py:83-87`). There are 9 more
requests. `findings.week` is unchanged (not asked). Test: in `backend/tests/test_e4_prebuilt_routes_generator.py`,
assert the 9 ids and queries; the uniqueness asserts stay. Cost: a cold compose is about 4-10 s, so the build adds
about 40-90 s, and so does each add-dates tick that moves the watermark. An unmoved tick adds about 9 x 50 ms. Stop
rule: if the prebuild report exceeds the EX-3 "50% of the tick limit" budget, keep the `week` variants only and
report. The numbers do not change: a stored hit is the same route's body.

### D-E5.24 Client-side filtering by `lens_flags` is refused

Page one holds 50 rows. `total_count` and the cursor are server-side and bound to the lens, and the page rule is "the
page never re-sorts, re-selects or sums". A client filter would show a frontend count that is wrong past 50 rows.

### Interactions

- **PF-T (Portfolio tabs proposal)**: the lens loading state moves with `PriorityPanel` to Act first. Overview links
  drop `lens`, so the Overview top 3 reads `lens=all`, which is already pre-built. PL-1 is kept and only moved.
- **ANY-2**: stored period rows make cold composes fast. PL-2's list stays valid and harmless, and PL-1 stays.
  Splitting the lens rows into a separate read stays an ANY-2 option, per proposal §7.4.

Decisions logged for owner review: **D-E5.22** keep the page while the lens loads; **D-E5.23** pre-build the 9 lens
variants; **D-E5.24** no client-side lens filtering.

## Findings cards ruling (2026-11-10)

Walkthrough item 7 (`.agent/owner-walkthrough-2026-11-10.md`). Architect: Claude, under the owner's delegation
(`.agent/owner-away-architect-decides-2026-11-08.md`). Mockup draft for owner approval:
`frontend/mockups/v71/findings-cards.html`. MOCK DEVIATION from v6.9 `findingsScreen()` until the owner approves it.

Code facts verified:
- `frontend/src/estate/findingIndex.tsx:151-152`: "High priority" and "Low confidence" are literal "Not assessed".
- `backend/assetops_backend/estate/index.py:169,235`: every Findings row has `priority: None` and `confidence: None`.
  The summary keys `high_priority` and `low_confidence` (`:415`) are never set. No Finding-level priority or
  confidence exists anywhere.
- Related concepts that do exist: Portfolio placement groups (`estate/placement.py` `_rule`: ACT_NOW, etc.) and a
  placement confidence (`_confidence`: UNKNOWN / LIMITED / SUPPORTED_SOURCE_COHERENT). These sit on Portfolio rows
  only and are computed with Action and money context. Dispatch analytics also has a confidence, but that belongs
  to each analysis, not to a Finding.
- `index.py:417-424`: the counts are computed only when `_coverage_state == "COMPLETE"`, which needs every applicable
  Site to be CURRENT or HISTORICAL. A PARTIAL Site does return rows, but Findings next to its unanalysed days are
  withheld (`coverage.py` DAYS_WITHHELD). Any count with a PARTIAL Site in scope is therefore a lower bound.
- `index.py:421`: awaiting verification counts MINI_GRID only. The cause is structural. Cold and EV Actions are
  `domain_action` rows, and their plans are keyed by `domain_action_id`. The estate has no Finding-to-domain-Action
  join (`portfolio.py` R4.1 comment above THREAD_LABEL). The Portfolio's Cold/EV "Pending" is thread state
  ACTION_IN_HAND, meaning the action is agreed but not applied. That is not "awaiting verification", so the
  Portfolio and this card do not disagree about any fact.

### D-E5.25 "High priority" removed; "Low confidence" replaced by "Not yet confirmed"
Nothing can honestly feed "High priority". v6.9's intent ("Decision needed") is already served by the Portfolio's
"Where management should act first" (Act first tab), so this card is removed. v6.9's "Low confidence" intent
("evidence constrained, read with care") is served honestly by the stored lifecycle UNCONFIRMED. That state is the
existing "Not yet confirmed" chip on this page. "Supported findings" is relabelled "Confirmed findings" to match
LIFECYCLE_WORDS. Placement on Findings rows (to restore an "Act first" count here) is refused for the demo. It is
backlog: not demo-critical, and Opus, about 1 unit.

### D-E5.26 Show the counts with an honest qualifier; do not withhold
Withholding hides real, read rows, and with the demo data it hides them almost always. Rule: compute
`supported_findings`, `awaiting_verification` and the new `unconfirmed_findings` over the rows read, whatever the
coverage. When the coverage is not COMPLETE, the frontend marks each count "So far" and lists the Site breakdown.
The qualifier uses **analysis** words, not reading words. The brief's "1 site has partial readings" is refused: the
estate PARTIAL state means days not analysed yet, not partial readings. The proposal's term table maps estate
PARTIAL to "not analysed yet". Site state words: CURRENT/HISTORICAL "fully analysed"; PARTIAL "with days not
analysed yet"; PENDING_RECOMPUTE "still processing"; STALE_SOURCE "no new readings received"; UNKNOWN "not analysed
yet"; NOT_APPLICABLE is left out of the denominator.
Literal: `So far: {full} of {applicable} sites fully analysed` followed by each non-zero part
` · {n} site(s) with days not analysed yet` / ` · {n} site(s) still processing` / ` · {n} site(s) with no new readings received` /
` · {n} site(s) not analysed yet`, with "site" and "sites" chosen by count. The complete case is unchanged:
`Across {n} sites`. The cards no longer show "Some data missing".

### D-E5.27 Awaiting verification: mini-grid only is a disclosure defect (Medium), not a counting defect
The count is right by its stated rule, but the card reads as estate-wide. Fix now: the note appends
`mini-grid sites only; cold room and EV charging are not counted here yet`. The estate-wide count is backlog: chain
threads in CHANGE_APPLIED with an open verification window, labelled to match the Portfolio's "Outcome pending".
It is not demo-critical, and Opus, about 1 unit.

### D-E5.28 What each card is for (plain language, for the owner)
- **Confirmed findings:** how many problems or opportunities the readings confirm in this period.
- **Not yet confirmed:** things seen that the readings do not yet confirm. Read these with care.
- **Awaiting verification:** actions already taken where we are still waiting to see whether they worked.
- **High priority (removed):** "what needs a decision first". The Portfolio's Act first tab answers that.

### Fix cards
**FC-1 Frontend (Sonnet, 0.5 unit; lands before Thursday, no rebuild; after owner approves the mockup).**
- Files: `frontend/src/estate/findingIndex.tsx` (Cards: 3 cards, labels, D-E5.26/27 notes) and
  `frontend/src/estate/estateClient.ts` (`unconfirmed_findings?: number | null`).
- Null count (before FC-2): value `Not counted yet`, amber. Note `Counted once every site is fully analysed`
  followed by the same parts.
- Tests: `frontend/src/estate/__tests__/estateRoots.test.tsx` (complete; partial with numbers; partial with null;
  no "Not assessed" or "Some data missing" in the cards; the mini-grid note) and `estateFixtures.ts`.

**FC-2 Backend (Sonnet, 0.25 unit; MUST merge before tonight's build to land Thursday).**
- File: `backend/assetops_backend/estate/index.py:417-424`. Compute the three counts unconditionally and add
  `unconfirmed_findings`. Leave `basis_count` and `total_count` unchanged (null unless COMPLETE). Remove
  `high_priority` and `low_confidence` from the summary only if the frontend type is updated in the same pass;
  otherwise leave them null.
- Tests: regenerate `backend/tests/fixtures/w3/w301-estate-golden.json` (review the diff: only summary keys may
  change). Add one backend test: a PARTIAL scope returns numeric counts equal to the rows read. The prebuilt lens
  variants (D-E5.23) pick the change up in the build.
- If FC-2 misses the build, FC-1's null path is the honest fallback (mockup section C).

Decisions logged for owner review: **D-E5.25** to **D-E5.28**. The owner approves `frontend/mockups/v71/findings-cards.html`
before FC-1 merges.

## Non-Kobo Site pages ruling (2026-11-10)

Walkthrough item 11 (`.agent/owner-walkthrough-2026-11-10.md`). Architect: Claude, under the owner's delegation
(`.agent/owner-away-architect-decides-2026-11-08.md`). Full answer, table (56 values: A 17 · B 17 · C 16 · D 6) and
cards: `.agent/architect-answer-non-kobo-sites-2026-11-10.md`.

### D-E5.29 Verdict: product bug for Cold and EV, story data defect for Kisiwa
- Cold and EV: Site reads select an analysis only when the stored window contains the requested one (Cold,
  `postgres_assessment_store.py:2222-2228`) or equals it (EV, `:2933-2941`). The story analyses 16:00–17:05 and
  08:00–09:05, so day and week views read "Unknown" or "Not assessed". The exact window shows the 4.9 °C peak and
  the USD 4.50 estimate.
- Kisiwa: `tools/demo_combined_kisiwa.py:789,1189` publishes one epoch per night (18:00–12:00) on a fresh gateway.
  Every day therefore holds two epochs, and `cohort.py:93-101` marks it AMBIGUOUS (9 of 11 days).
- This also explains the Portfolio's "Kisiwa 0 of 7 days checked" and corrects `architect-combined-pass-2026-11-08.md` row 4.

### D-E5.30 DATA-1 (Opus, 0.5 unit): one Kisiwa recording session; MUST merge before tonight's build
- One epoch `kisiwa-gw-1` on one persistent `work/"kisiwa-gateway"` (`gateway_dir`, DD1a1-R5), in both publish paths.
- New finish check `KISIWA-COHORT`.
- New Kisiwa dispatch content is read from the build before the demo; its figures are quoted from the build.
- Fallback if DATA-1 misses the build: present Kisiwa through Fuel nights, the Finding and verification only.

### D-E5.31 PB-1 (Opus, 2 units, plus Sonnet 0.25 frontend): analysed periods inside a window; before the client session
- A selection that contains or equals the window is unchanged.
- Otherwise the periods wholly inside the window are listed; the status uses the most recent one with an open
  Finding, or else the most recent one.
- Window-bar literals: `Analysed period: {from}–{to}` and `Analysed periods in this range: {n} · showing {from}–{to}`;
  with no period inside, `No analysed period in this range`.
- Pinned mode is unchanged. EV provenance is judged per period.
- MOCK DEVIATION: one window-bar line; owner informed.

### D-E5.32 Thursday mitigation: analysed-period story links (DATA-2, Sonnet, 0.25 unit; before the build)
- A second link per Cold and EV day for the exact analysed period; the whole-day link stays for Work and Actions.

### D-E5.33 Kisiwa objectives MG-2 and MG-5, after DATA-1 (DATA-6, Sonnet, 0.25 unit; before the client session)
- Reverses DIESEL-1 §9p.4. CO-6 / `objective_site_count` changes from 3 to 4. Story change; owner informed.

### D-E5.34 NOT BUILT values become plain roadmap wording (RM-1, Sonnet, 0.5 unit)
- RM-2 hides the unsupported Site lens chips on client screens. **Owner approval needed (mockup).**

### D-E5.35 Integration ranking for the client
1. Billing and collections.
2. Sign-in.
3. Work-order cost (CMMS).
4. Fleet roster and telematics.
5. Cold stock value and occupancy.

### D-E5.36 Story order
- Kobo, then Kisiwa. Cold and EV are brief beats on their analysed periods.
- Until PB-1 lands, no Cold or EV Health, Performance or Financials on a day or week window.

### D-E5.37 More Cold and EV days only after PB-1 (DATA-11, Sonnet, 0.5 unit, about +10 min prepare)
- Story change; owner informed.

Other cards (answer file):
- Thursday frontend: PB-5 Kisiwa feeder legend uses Foundation display names (`SiteWindowOverview.tsx:701`);
  PB-6 copy batch; PB-8 Fuel tab loading (`MiniPerformance.tsx:1633`).
- Before the client session: PB-3 EV event-driven grading; PB-4 an AMBIGUOUS day is "not analysed yet", never
  "Checked: nothing to report"; PB-7 the coverage denominator counts from the Site's first reading.
- Optional: DATA-5 story diagnostics; DATA-10 Kisiwa generator plan.
- Backlog: DATA-4, DATA-7, DATA-8 (owner approval).

Decisions logged for owner review: **D-E5.29** to **D-E5.37**.

## D-E5.38 to D-E5.40: Portfolio coverage counts UTC days (CO-6, WK-GAP fail on client6) — Architect, 2026-11-11, owner-delegated, logged for owner review

Found by the fresh demo build (worktree `AssetOpsV1-e3d` at 5cc98edfa, DB `assetops_polish_client6_test`). Verified in code:
`estate/coverage.py` `_mini_grid_basis` walks `snapshot.dispatch_days` (one entry per UTC day), counts a day as
checked whenever that UTC window has an available selection, and `_requested_days` counts UTC midnights. It never
reads the Site timezone. Calendar v4 puts S-3's `night-early` part at 21:00-03:00 UTC, so the UTC window of 11-04
holds a selection although Site-local 11-04 (Africa/Addis_Ababa) has no readings. Live
`GET :8990/api/estate/portfolio?from=2026-11-02T00:00:00Z&to=2026-11-09T00:00:00Z`: Kobo coverage `CURRENT`,
`requested 7, checked 7, gaps []`. Correction to the diagnosis: the Portfolio already has a Site-local day rule.
`summary.claims[*].days` comes from `chain.claims.claim_days` -> `chain.read.window_days(lo, hi, tz)` over stored
chain day grades, and it is honest on this build (estate 12 complete, 1 partial, 3 low, 6 no data of 22). Coverage is
the one estate reader still on UTC days, so this is two day definitions on one screen, not a missing definition.

### D-E5.38 One day definition: coverage uses the chain's Site-local graded days
- Requested days = `chain.read.window_days(from_, to, site.timezone)` (CH-5a2a: a UTC-midnight window names its
  calendar dates, each read as the Site-local day of that date). This is the summary claims' frame.
- Each day's state = the stored chain day grade (weakest row, `chain/reader.py` `_day_grade`, the same rows
  `claim_days` reads). NO_DATA -> gap (`UNASSESSED`, reason `NO_READINGS`); PENDING -> the Site is
  PENDING_RECOMPUTE; COMPLETE, PARTIAL, LOW -> checked (the days line already says "partly checked" and "too little
  data" from the same grades). The trial day S stays checked (PARTIAL grade), as the owner's v4 pattern expects.
- The dispatch-selection, match-pass and S3-status rules over the UTC windows stay as they are; they still decide
  PENDING / STALE / unmatched. Only the day count, `gaps` and the `gap` flag move to the graded local days.
- Rejected: the builder's option (b), a rule over the two UTC windows a local day touches. Both windows touching
  local 11-04 have selections, and it would be a third day definition.
- Spec for the fix (DATA-12, Sonnet, 1 unit, product code): `site_coverage(...)` and `_mini_grid` gain a keyword
  `day_grades: Mapping[date, str] | None = None`. The three callers (`estate/index.py:148`,
  `estate/evidence_money.py:463`, `estate/financials.py:417`) pass the mini-grid Site's grades from the same
  `req.day(site_id, site_type, window_days(...))` read the claims use (memoised by `read_scope`, so no extra query).
  `None` keeps today's behaviour, so cold, EV, actions and the fake-snapshot tests are untouched. Pin it with a
  unit test in `backend/tests/test_estate_coverage*.py`: a UTC+3 Site whose local day D is NO_DATA while both UTC
  windows touching D have selections reads PARTIAL, `gaps == [D]`, `requested 7`, `checked 6`, `text` set; plus CO-6
  and WK-GAP passing on a client6-shaped build. Serving: no rebuild. Coverage is composed per request from stored rows,
  and stored responses are keyed by `code_version`, which hashes every backend source file, so a code change misses
  the store on its own; a serve restart re-runs `write_prebuilt_routes` and the pre-build re-warms. Visible effect:
  Kobo becomes PARTIAL on the Portfolio, so its days line and "days not analysed yet" note appear and the PARTIAL
  money and finding withholding (§2.5, `EstatePortfolio.tsx:127`) applies to Kobo; the Portfolio pairs need recapture.

### D-E5.39 Thursday 13 Nov: do not fix; fix before the client session
- What a viewer sees wrong today: no false number. The Portfolio omits Kobo's caveat ("5 of 7 days checked" and the
  "days not analysed yet" note) and treats Kobo as fully current, while the Site board shows 11-04 as no data. The
  claim lines ("4 open on the days checked") are correct. The fix changes Kobo's Portfolio money and findings display
  two days before the demo on an unreviewed path, which is a larger risk than a missing caveat at an associates'
  technical demo.
- Talking point if asked: "The Portfolio's day count still uses UTC days, while the Site board uses Kobo's local day.
  Kobo's 4 November has no readings; the Portfolio misses that because a night shift crosses midnight. One day
  definition is the fix, scheduled before the client session."
- DATA-12 goes into the pre-client plan (client session about 1-8 Dec), ahead of the walkthrough polish recapture.

### D-E5.40 Mark CO-6 and WK-GAP as a known defect for this build only
- `add-dates` appends and settles the dates first, then runs `finish check`; on FAIL it exits non-zero with "This
  build no longer passes its checks; prepare a fresh one before a demo." So the data is in, but Wednesday's live
  capture would read a failed command and a wrong instruction.
- Tool-only change (Sonnet, 0.25 unit, no product code): `tools/demo_combined_finish.py` gets
  `KNOWN_DEFECTS = {"CO-6": "D-E5.38", "WK-GAP": "D-E5.38"}`. A failing listed row is kept out of `failed` and the
  exit code only when its failure is the coverage signature (CO-6: Kobo coverage state not PARTIAL with `gaps: []`;
  WK-GAP: the `"CO-6 coverage gaps", [], ...` assertion). Anything else in those rows still fails. `check.json`
  records `known_defect: "D-E5.38"` and the failure text; the summary prints "known defect"; a listed row that passes
  prints "known defect no longer reproduces; remove the marker". Before relying on it, run CO-6's checks after line
  492 once on client6 with the coverage block skipped, so the marker hides nothing else. DATA-12 removes the map.

Decisions logged for owner review: **D-E5.38** to **D-E5.40**.

## D-E5.41 to D-E5.44: DATA-12 review rulings (Architect, Claude, 2026-11-11; review ACCEPT WITH NOTES on fd85f1d31)

### D-E5.41 Fix before merge, one Sonnet round (card DATA-12-FX, about 0.35 unit)
- Not merged as is. M1 would regress Kisiwa honesty on the current rule: today an unselected UTC day is a gap, and with the grades it reads CURRENT with its findings and money silently missing.
- Lane A is not blocked. A2 (PB-4 + PB-7 + BL-50 + L2) starts now from main and rebases once DATA-12 merges. Its only shared file is `tools/demo_combined_finish.py`.

### D-E5.42 Day rule, completing D-E5.38 (the M1 and L4 answers)
For each requested local day D (`window_days`, the CH-5a2a frame: the UTC dispatch day with D's calendar date is D's analysis window), the grade decides first:
- **NOT_EXPECTED:** dropped from both requested and checked. The Site does not operate that day.
- **NO_DATA:** a gap, reason `NO_READINGS`.
- **PENDING:** the Site is PENDING_RECOMPUTE.
- **COMPLETE, PARTIAL or LOW, but the dispatch day with D's date has no available selection:** a gap, reason `NOT_ANALYSED` (the words "not analysed yet"). This is the M1 fix.
- **Otherwise:** checked.

The selection, match-pass and S3 rules are unchanged.

### D-E5.43 L1 and L3 fixed in the same round; L2 deferred
- **L1:** grades are read at `req.known_at` on page one (the claims' key) and at `k` on cursor pages.
- **L3:** `analytics/finding_index.touched` takes an optional `tz`. When gap days are local, the day bounds are Site-local midnights ± `CONTINUITY_TOLERANCE`. Without this, Kobo night findings starting between local 00:00 and 03:20 are wrongly withheld.
- **L2** (module-global provider in `main.py`) goes to the backlog, after 17 Nov. It has no effect in a single served app.

**Card DATA-12-FX (Sonnet, same branch and worktree `AssetOpsV1-data12`):**
1. `coverage.py`: apply the D-E5.42 rule.
2. Callers: L1.
3. `touched(..., tz=None)` with local bounds when given; pass the Site tz from the gap-day caller.
4. Tests, each pinned:
   - a local day with data whose same-date dispatch day has no selection reads PARTIAL with `gaps == [D]` and reason `NOT_ANALYSED`;
   - a NOT_EXPECTED day changes neither requested nor checked;
   - a UTC+3 finding starting at local D+1 01:00 is not withheld when D is a gap;
   - a live request makes one `chain.day` read per mini-grid Site (count the calls).
5. Coordinator verifies the diff; a fresh Sonnet re-review covers M1 and L3 only.

### D-E5.44 Money on a partly covered Site: owner question (story-visible)
- **Today's rule (COV-PARTIAL §2.5)** withholds a PARTIAL Site's money for the whole range:
  - `financials.py:420-426` keeps only CURRENT and HISTORICAL;
  - `EstatePortfolio.tsx` shows "Partly checked · value shown once every day is checked".
- **With DATA-12, Kobo is PARTIAL on any week that contains 4 Nov.** So the default week loses Kobo's money: the client script's main money beat.
- **The Architect's view:** withholding is honest but unhelpful for an executive. The honest and useful form is money for the analysed days only, named as such, never extrapolated to the missing day. It is a reversal of an earlier ruling, so the owner decides.
- **Card if approved: PARTIAL-MONEY** (Opus, about 0.5 unit, lane A after A2, before 17 Nov).
  - Financials and the Portfolio row and cards sum the lines of checked days only.
  - Each label reads `{amount} for {n} of {m} days analysed · {gap list} not analysed`.
  - The no-total and receipt rules are unchanged.
  - It is folded into AR-4's design later.
- **Until the owner answers:** DATA-12 merges with today's withholding, and the script refresh moves the money beat to ranges without a gap.
- **Question for the owner (plain language):** "When one day in a week has no readings, the Portfolio now hides that Site's money for the whole week (Kobo's week of 2-8 Nov, because 4 Nov has no readings). Option 1: keep hiding it until every day is analysed. Option 2 (recommended): show the money for the days that were analysed, clearly labelled '6 of 7 days analysed · 4 Nov not analysed', never estimating the missing day. Option 2 is about half a day of work before 17 Nov."

Decisions logged for owner review: **D-E5.41** to **D-E5.44**.

### D-E5.45 Owner answer to D-E5.44: option 2 (2026-11-11)
Owner, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`): "option 2 for money".

**Card PARTIAL-MONEY.** Opus. About 0.5 unit. Wt `AssetOpsV1-pmoney`, branch `task/PARTIAL-MONEY`, cut from main after DATA-12 and DATA-12-FX merge.
- **Rule:**
  - A PARTIAL mini-grid Site's money uses only the lines of its checked local days (D-E5.42).
  - Never estimate, scale or fill the gap days.
  - The no-total and receipt rules are unchanged.
  - PENDING, STALE, UNKNOWN and HISTORICAL keep today's withholding.
- **Label:**
  - Literal: `{amount} for {n} of {m} days analysed · {gap days} not analysed`.
  - Gap days are given as Site-local dates ("4 Nov"). More than 3 gap days read `{g} days not analysed`.
- **Files:**
  - `estate/financials.py` `select_financial_scope` (`covered` admits PARTIAL; `mini_grid_lines` filtered to checked days);
  - `estate/evidence_money.py` (Portfolio cards and rows, same filter);
  - `frontend/src/estate/EstatePortfolio.tsx` (`partialConsequence` and `consequenceFirst` show the amount with the label);
  - the Financials page label; `portfolioWords.ts`.
- **Pinned tests:**
  1. A week with one NO_DATA day: the amount equals the sum of the other 6 days' lines exactly, and the label is as above.
  2. A gap day's own line is never included.
  3. Categories stay "covered" only for PARTIAL with at least 1 checked day.
  4. A PENDING Site is still withheld.
  5. Frontend: `estatePortfolio.test.tsx` for the label and amount.
  6. No total across currencies.
- **Lane A,** after A2 and before UQ-6a. It displaces nothing by name; it consumes about 0.5 of option Y's buffer. If Thursday's re-assessment shows lag, AR-6 (Cold/EV boards under 1 s) moves after 17 Nov first.

## D-E5.46 Day-gap words state the data fact; "not analysed yet" only when the system still has work to do (Architect, Claude, 2026-11-11, owner-directed, logged for owner review)
Owner, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`, last entry): "not analysed yet only makes sense when system action is pending, for when the data is not complete, that fact need to be stated 'not enough data received for the day' or something similar or 'data received is invalid' or something better".

**Code facts.** A local day with readings and no trustworthy result has one of three causes:
- (a) the run's cohort is `AMBIGUOUS` (`assessment_inputs.py` CohortSelection) or its generator series is ambiguous (`dispatch_v3.py`, limitations `AMBIGUOUS_COHORT`, `GENERATOR_SERIES_AMBIGUOUS`; the window claim is `WINDOW_INDETERMINATE`). These are conflicting reports for the same channel and time, such as the Kisiwa boundary duplicates.
- (b) there is no usable cohort (`EMPTY`, limitation `NO_COHORT`) or no generator state (`NO_GENERATOR_STATE`). The claim is also `WINDOW_INDETERMINATE`.
- (c) the dispatch day has no available selection (`coverage.py`: `not day["available"] or selection is None`), with or without an outstanding job.

DATA-12-FX's `NOT_ANALYSED` tests only (c). A day in (a) or (b) that has a selection counts as checked today, which overstates coverage.

**Rule: one gap reason per day.** Precedence follows the order of the table.

| Gap reason (backend) | When | Full words (Site, Findings, day boards) | Short form (Portfolio / coverage / money) |
|---|---|---|---|
| `NO_READINGS` | grade NO_DATA | No readings received for this day | no readings |
| `READINGS_CONFLICT` | selected window INDETERMINATE with `AMBIGUOUS_COHORT` or `GENERATOR_SERIES_AMBIGUOUS` | Readings for this day conflict (duplicate or overlapping reports), so it can't be analysed | conflicting readings |
| `NOT_ENOUGH_READINGS` | selected window INDETERMINATE with `NO_COHORT` or `NO_GENERATOR_STATE` | Not enough readings received to analyse this day | not enough readings |
| `NOT_ANALYSED` | no available selection (cause c), including an outstanding or failed job | Not analysed yet | not analysed yet |
| (Site state PENDING_RECOMPUTE) | grade PENDING or an outstanding job | Still processing | still processing |

- Never "error", "invalid", codes, or wording that blames the system for a data fact.
- "Not analysed yet" and "still processing" are kept only for system work.
- **Money label** (amends D-E5.45): `{amount} for {n} of {m} days analysed · {day list}: {short reason}`, with one group per reason, for example `6 of 7 days analysed · 4 Nov: no readings`. Days that share a reason are grouped (`3, 4 Nov: conflicting readings`). More than 3 gap days reads `· {g} days without a usable result`.
- **Portfolio coverage line** (amends D-E5.26): Site PARTIAL reads `{n} site(s) with incomplete days` in place of "with days not analysed yet". The Site's days line lists each gap day with its short reason. UNKNOWN keeps "not analysed yet".

**Updated owner-facing term family** (supersedes the walkthrough 5.3 list): complete readings / partial readings / too few readings / no readings received / not enough readings received (day) / conflicting readings (day) / still processing / not analysed yet (system work only) / incomplete days (Site summary).
- A day with no readings at all keeps "no readings received".

**Cards**
- **DATA-12-FX:** unchanged; finish and merge as built. Its `NOT_ANALYSED` is exactly cause (c), which is already correct.
- **GAP-REASONS (new, Sonnet, about 0.35 unit, lane A, cut from main after DATA-12-FX merges, before PARTIAL-MONEY):**
  - `coverage.py` reads the selected window's claim and limitation prefixes, and turns an INDETERMINATE (a) or (b) day into a gap with `READINGS_CONFLICT` or `NOT_ENOUGH_READINGS`;
  - `_days_block` carries the reason;
  - pinned tests cover one day per reason and the precedence;
  - verify on client6 Kisiwa that the boundary-duplicate day reads `READINGS_CONFLICT`.
- **PB-4 (A2):** the AMBIGUOUS day reads "Readings for this day conflict (duplicate or overlapping reports), so it can't be analysed" in place of "not analysed yet" (`SiteFindingIndex.tsx`, `OverviewFindingList.tsx`). It is never "Checked: nothing to report". If A2 has already committed the old words, change them in the same branch.
- **PARTIAL-MONEY:** uses the money label above, keyed on each gap's reason.
- **PF-W:** adds the two new terms and "incomplete days" to `portfolioWords.ts`, and replaces "days not analysed yet" in the coverage line.

Decision logged for owner review: **D-E5.46**.

## D-E5.47 An infrastructure read failure is never stored and never shown as a data fact (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

**Defect (E3d, client6, 2-8 Nov outcome summary).** serve's prebuild rebuilt `/api/estate/outcome-summary` in 3.8 s during 88 "too many clients already" refusals. Every Site showed PARTIAL/Unknown and Kobo "No target set yet" although its objective rows were intact. The degraded body was stored and served until `valid_until`.

**Cause in code.**
- `site_outcomes/mini.py` `Reads.call`: `except Exception` records the read name in `failed` and returns None. The composer turns that into UNKNOWN and `read_state` PARTIAL (`site_outcomes/read.py` docstring lines 9-10). An objectives read that fails looks like "no objectives".
- `site_outcomes/read.py` `_summary`: `except Exception` gives `read_state = UNAVAILABLE` (line ~684). Other broad catches are at ~405, ~597, ~635 and ~721.
- `chain/response_store.py` `ResponseStore.serve`: it stores whatever `compose()` returns once the watermark is unchanged. Nothing tells it that the compose was degraded.
- `chain/prebuild.py` `run`: it counts only non-200 responses, and a degraded 200 reports OK.
- Connection pressure: about 20 adapters each call `create_engine(..., pool_pre_ping=True)` with the default pool (5+10). The prebuild's in-process `TestClient(create_app())` doubles that inside a server that is already running.

### Rule
1. **What counts as infrastructure (transient).** A failure is transient when the exception, or anything in its `__cause__`/`__context__` chain, is one of these:
   - `sqlalchemy.exc.OperationalError`, `InterfaceError`, `DisconnectionError` or `TimeoutError` (the pool timeout);
   - `psycopg.OperationalError` or `psycopg.errors.TooManyConnections`;
   - a `DBAPIError` with `connection_invalidated`;
   - `ConnectionError`, `OSError` or `socket.timeout`.

   A wrapper class on its own is NOT transient. `LedgerUnavailable`, `*StoreUnavailable` and `PortUnavailable` are also raised for deterministic states ("DATABASE_URL is not set", "tenant/Site not found", "not wired"), and those keep today's honest PARTIAL/UNKNOWN. One function decides: `infra.is_transient(error) -> bool` in a new `backend/assetops_backend/infra.py`.
2. **How composers signal it: a mark on the read scope, never a body field.** Add `ReadScope.degraded: list[str]` and `read_scope.note_failure(name, error)`, which appends when `is_transient(error)`. Calls go in:
   - `Reads.call`'s except;
   - the five broad catches in `site_outcomes/read.py`;
   - any other `except Exception` reached from a stored-route compose (the implementer greps `chain/`, `estate/` and `site_outcomes/` and lists every site in the packet).

   Backstop: one global `event.listen(Engine, "handle_error", ...)`, registered in `create_app`. It marks the current scope when `ctx.is_disconnect` is set or `ctx.original_exception` is an OperationalError. Wrappers that re-raise a DB error without `from error` get `from error` added (mechanical; listed in the packet).
3. **What the store does** (`ResponseStore.serve`, compose-only path included). After the compose, if `sc.degraded` is non-empty it does NOT insert. Instead:
   - (a) it serves the newest stored row for (route, request_key, code_version), whatever its W and even past `valid_until`. This is a new port method `latest_good(route, key, version)` on `postgres_response_store.py`; pruning keeps 3 rows, so one normally exists. The response gets the header `X-AssetOps-Stored: stale` and `Retry-After: 30`, with no ETag.
   - (b) with no such row, it answers **503** `{"code":"TEMPORARILY_UNAVAILABLE","message":"This view is temporarily unavailable. Retrying."}` with `Retry-After: 5`, and stores nothing.
   - It logs `stored_route_degraded` with the read names. An exception from the lookup path itself (the existing `unstored` branch) follows the same rule when it is transient.
4. **Frontend (minimal).** The board and summary fetches treat 503 `TEMPORARILY_UNAVAILABLE` as the state "Temporarily unavailable. Retrying...". They retry after 2, 4 and 8 s, then show "Still unavailable. Refresh to try again." It is never rendered as Unknown, PARTIAL or "No target set yet".
5. **Prebuild.** A path whose response is 503 or carries the `stale` header is retried 3 times, after 2, 5 and 10 s. The summary gains `degraded: {path: attempts}`, and `code` is `DEGRADED` when any path still fails. `tools/demo_combined.py` treats `DEGRADED` like `FAILED`: it prints the paths and exits non-zero. Before it starts, the prebuild logs the `pg_stat_activity` count.

### Card INFRA-1 (Opus, 0.75 unit server + Sonnet 0.15 frontend; lane C)
**Files:**
- new `backend/assetops_backend/infra.py`;
- `read_scope.py`;
- `site_outcomes/mini.py`;
- `site_outcomes/read.py`;
- `chain/response_store.py`;
- `chain/adapters/postgres_response_store.py`;
- `chain/prebuild.py`;
- `main.py` (the hook);
- `tools/demo_combined.py`;
- the frontend fetch helper for the summary and board.

**Pinned tests:**
- (T1, no DB) A fake rows port holds a good row. The compose calls a `Reads.call` whose fn raises `OperationalError("too many clients already")` halfway through. Assert: nothing inserted, the old bytes served, header `stale`, no ETag.
- (T2) The same with an empty store gives 503 `TEMPORARILY_UNAVAILABLE` and nothing inserted.
- (T3) `LedgerUnavailable("DATABASE_URL is not set")` without a cause still gives PARTIAL, and it is stored (the honest state is kept).
- (T4) `is_transient` table: a wrapped cause gives true, a bare wrapper gives false, and the pool `TimeoutError` gives true.
- (T5, `*_test` DB) The `handle_error` hook marks the scope when a connect to a closed port is refused.
- (T6) A prebuild against a client that returns 503 once and then 200 retries and reports OK. Always 503 reports `DEGRADED`, and `demo_combined` exits non-zero.
- (T7, frontend) 503 shows the retrying state, never "No target set yet".

**Fit in the 17 Nov plan (`architect-sequence-client-scope-2026-11-11.md` C.5).** Lane C, right after A4 PB-1b, in the wait for AR-1's merge before AR-3 + AR-6. It displaces nothing there. If PB-1b has not merged by Thu 18:00, INFRA-1 moves to the head of lane A after A2 and pushes A5/A6 by about 0.9 unit. AR-2 then follows the existing no-slack rule: held, and the boards use the pre-built ranges. **INFRA-1 must merge before the Sat 12:00 freeze and the rehearsal build**, because this defect can hit the client session.

### Ops mitigation until INFRA-1 is in every demo build
- **No test suite, check-all or ad-hoc DB script** runs against `assetopsv1-postgres-1` during add-dates, prepare, the prebuild, live checks, recapture or a demo. The coordinator pauses the lanes' DB work for those windows. The same machine rule goes into C.6.
- At the next safe container restart (not during E3d's life, and never touching client6), start Postgres with `-c max_connections=300`. Until then, check `SELECT count(*) FROM pg_stat_activity` before a prebuild and wait while it is above 60.
- After any prebuild, check `/api/estate/outcome-summary` for the demo ranges: no Site may be PARTIAL/UNAVAILABLE unless the story says so. If one is, rerun the prebuild once the server is quiet. The bad row expires at `valid_until`, or a new commit moves W.
- Deferred to BL-71: one shared engine factory with a capped pool (`ASSETOPS_DB_POOL_SIZE`), the prebuild reusing the serve's engines (out of process, over HTTP), and the degraded rule for non-stored routes.

Decision logged for owner review: **D-E5.47**.

## D-ANY.5 ANY-1 Phase 1 review M1/M2: period-row knowledge time is transaction time (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

**Facts in code.**
- The existing compose binds `known_at` as **transaction time** only. CH5a1-R2 R-1 (`chain/adapters/postgres_chain_read.py` lines 30-31) says "a story-time evidence cutoff never reaches it".
- The tables already work this way: `site_day_snapshot.computed_at <= k` (`postgres_snapshot_store.py:111`), `created_at`/`source_known_at`/`decided_at <= k`, and `event_outbox.recorded_at` defaults to `clock_timestamp()` (0044).
- Story time bounds evidence only (`chain/read.py` `site_cutoff`).
- A day with no snapshot row at k reads `NO_DATA` (`chain/reader.py:111`).

**M1 ruling.**
- `site_period_read.computed_at`, `event_outbox.recorded_at` and `event_consumption.processed_at` stay wall-clock transaction time. Rows are never backdated to story time, because that would disagree with the snapshot and Finding reads at the same k.
- A historical read uses `computed_at <= k`, the latest revision (as built), with PENDING-at-k on the same clock.
- An October k on a November-built DB therefore truthfully sees "nothing known yet", and today's compose sees the same.
- A requested (site, day, kind) that has no row is never silent. `PeriodReadResult` gains `absent: tuple[(site_id, day, kind)]`, and each kind renders it exactly as today's compose renders no stored input at k (day grades give `NO_DATA`).
- There is no fallback compose on the serve path. Live absent rows are logged as `period_row_absent` and counted in perf.

**M2.** No bound now. The AR-0 baseline times `_UNCONSUMED_AT` on client6. If it exceeds 20 ms p95, add a low-water bound and drop `payload` from the select (if `resolve` does not read it) in AR-2.

**Phase-2 builder instruction.**
1. Write the Postgres tests first (M3): migration up/down, an adapter round-trip, and a late reading live and historical.
2. In the historical test, k falls between revision 1's and revision 2's `computed_at`, so revision 1 is served. A k before revision 1 gives `absent` and renders `NO_DATA`. A k after an outbox event but before its consumption gives PENDING.
3. Keep every `<= k` comparison on the transaction-time columns. Do not add a story-time clock.
4. Add `absent` to `PeriodReadResult`. Every AR-2 kind renders absent rows through the existing no-row rule.
5. The parity harness keeps its story-time k cases ("nothing known yet" parity). It adds one k taken from a real `computed_at` between two revisions on the parity DB.
6. Low items: unaligned Portfolio cases also randomise the end (`period_read_parity.py:115`), and `perf_budget --any-range` gains `--kinds`.
7. Time `_UNCONSUMED_AT` in the baseline and report the p95 in the packet (M2).

Decision logged for owner review: **D-ANY.5**.

## D-E5.48 DATA-11 Cold epochs and the EV depot's sparse look (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

Context: the owner raised DATA-11 to IN and will show the demo to mini-grid and EV executives. The builder's report is in `.agent/PB-3-DATA-11-packet.md` (head ae41f5ba7, Known Deviations 1 and 2).

### (1) Cold: one recording session per ordinary day is CONFIRMED for 17 Nov
- **It is faithful to the hardware.** A cold-room temperature logger normally uploads a signed daily batch, so each day's batch is its own attested session. Kisiwa (DATA-1) is different: there a single continuous gateway stream was split for no device reason.
- **Splitting around S-3 does not help.** The Cold producer attests once per epoch, over the first run's window (`tools/demo_combined_cold.py:90-101`). Any session holding more than one day would leave its later days unattested, which is a worse honesty failure.
- **Condition for the client.** If any client-facing page counts "sessions" for Cold, the rehearsal check reads that number, and the script calls them "daily uploads".
- **Deferred to BL-72.** The producer will attest per run, so a continuous Cold stream becomes possible.

### (2) EV: record the depot's whole declared charging hours (card EV-HB)
**Why EV looks sparse.**
- EV-LAB-001 declares charging hours as Tuesday 08:00-16:00 (`config/chain/operating-calendar-v1.json`, `SITE_WEEKDAY={"ev":1}`). The story records only 1 of those 8 hours (`ev_parsing.EV_WINDOW`).
- So the expected hours are mostly unrecorded, and E5 reads LOW.
- The connector model already reports status every minute (`observation/transform.py:600-603`). With PB-3, idle connectors count as known zero energy.

**Ruling.**
- Record the full declared window on every EV story day (the ordinary Tuesdays and the fault Tuesday). The charging sessions, kWh and USD 4.50 stay as they are.
- Do NOT change the Tuesday-only calendar before 17 Nov. Adding weekdays would turn every earlier story week's EV weekdays into expected days with no data, so the depot would look worse, not better. That change goes to BL-72 post-demo with the matching backfill.
- The script says: "The depot's declared charging day is Tuesday; AssetOps checks every declared hour and counts idle chargers as known."

**Card EV-HB** (Opus, 0.5 unit, lane C after PB-3 + DATA-11 merge; same worktree or a new one, `task/EV-HB-window`):
1. The registered EV window, the w205b/w504 window constants the producer moves per day, `received_at`, and the analysis window all become 08:00-16:00 local on each EV story day. The parser window comes from one constant.
2. The charging sessions (08:01-08:31) and the fault-day fault evidence keep their values byte-for-byte. Status minutes outside the sessions are UNPLUGGED/PLUGGED heartbeats.
3. Tests first:
   - (a) A pure test: a full-window ordinary day grades COMPLETE for `charging_kwh`.
   - (b) Story plan pins: kWh, USD and the fault findings are unchanged.
   - (c) One EV worker run of the 8-hour window in a scratch `<prefix>_audit` prepare, where the EV day row is not LOW.
4. Finish rows that must change, each with a reason in the packet:
   - E5 (EV estimated income: no longer "with too little data" for the declared days);
   - CO-6 `cold_ev_coverage`;
   - the EV `charging_kwh` grade/coverage pins in `demo_combined_finish` rows and `k7_story_pins.py`.

   Every other row stays equal.
5. Report the prepare-time delta. The estimate is about +5-10 min (8x the EV minute rows on each EV day).

**Gate.**
- If (c) is not green by Fri 13 Nov 18:00, EV-HB is dropped. E5 stays LOW, and the script line becomes: "We record one hour of the depot's charging day in this demo; it reads as too little data, honestly."
- The Saturday-night rehearsal prepare verifies E5 and the prepare time either way.

**BL-72 (post-demo, about 1.0 unit).** The Cold producer attests per run (a continuous stream), and the EV depot gets weekday charging hours with an EV story backfill for the earlier weeks.

Decision logged for owner review: **D-E5.48**.

## D-E5.49 EV fault day over the full recorded day: c1 stays out of service until repaired (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

**Ruling: option (a).**
- c1 is FAULTED from 08:16 and still out at 16:00. Clients read "out of service for 7 h 44 min".
- This is the honest consequence of recording the whole declared day under D-E5.48. The story already says no repair happened and the repair Action is still Pending, so a fault that cleared itself after 44 min would contradict it. It would also weaken the Action.
- For EV executives, "a charger has been down most of its charging day and the repair is still pending" is the more believable and more useful beat.
- What does not change:
  - the single Finding and its size;
  - per-session money (30/15 kWh, USD 9.00/4.50);
  - the Action's state.
- What does change: the CONNECTOR_OUT_OF_SERVICE warning duration, and "16 min unknown" disappears because status is known all day. This is a sanctioned exception to D-E5.48's "every other row stays equal". E5/WK-1 counting USD 9.00/9.00/4.50 (the day is now COMPLETE) is intended.

**Fix round (Sonnet, about 0.1 unit, same branch):**
1. Pin the 7 h 44 min out-of-service duration and its warning in `site_outcomes` tests and in the `demo_combined_finish` rows. List them in the EV-HB packet's rows table with the reason "D-E5.49".
2. Add a prepare-checklist line: on the EV fault day, c1 is out of service for 7 h 44 min, there is 0 min unknown, there is one Finding, the Action is Pending, and per-session USD is 9.00/4.50.
3. In `Docs/demo-sprint/implementation-logic-portfolio-sites-findings-actions.html` and the demo script, replace "44 min out, 16 min unknown" with "out of service from 08:16 for the rest of the charging day (7 h 44 min); repair still pending".

Decision logged for owner review: **D-E5.49**.

## D-ANY.6 Tonight's speed build for the Thursday 12 Nov technical demo (Architect, Claude, 2026-11-11 16:50, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude.
- Owner, verbatim (`.agent/owner-speed-before-thursday-2026-11-11.md`): "the speed work has to be done before Tursday demo"; chose "Rebuild tonight" (option b), accepting the risk.
- Supersedes for tonight only: the ANY-1 packet line "baseline after the Thursday demo" and the D-ANY.4 timing. D-ANY.1-5 rules otherwise stand.

**1. Slice and cutoffs.** Tonight = ANY-1 only (AR-0 baseline, AR-1, AR-2). AR-3, AR-4, AR-5 and AR-6 are not built for Thursday.
- 21:30 last ACCEPT. 22:00 go/no-go and merge. 22:15 build tag `demo/2026-11-12-rows`, fresh worktree `AssetOpsV1-e3e`. **22:30 latest prepare start** (about 2 h 45 min plus EV-HB 10 min, plus the AR-2 row build of at most 15 min, so done by about 01:45). 01:45-02:15 self-check plus full parity on the new DB. 02:15-03:15 live checks. 06:30 runbook and add-dates as planned.
- After the prepare starts, no full rerun fits. Only a single failed step can be rerun.
- **Fast on Thursday:** Site boards (mini depth: renewable, fuel, service, backup) for any day, about 1-1.5 s cold on Mini-grid and Diesel Sites.
- **Still slow off the pre-stored ranges:** Cold and EV boards (work-list reads; AR-6, about 2-3 s); the Portfolio for any range (AR-3/AR-4); every other page off the stored ranges.
- The pre-load list stays (AR-5 not built), so stored ranges are as fast as in client6. The presenter rule D-ANY.4 still holds for the Portfolio and for non-board pages.
- If AR-2 is not ACCEPTed by 22:00, it is held. The build still goes ahead at 22:30 from main (today's fixes, plus AR-1 only if its parity passed), and the boards stay on the pre-stored ranges.

**2. Baseline.**
- Run it now on `assetops_polish_client4_test` (not the fallback; 0059 is applied there). **Never on client6.** client2 is the spare.
- Parity must pass before AR-1 or AR-2 merges.
- To keep it fast: run the story requests plus `--random 16` (the default), not a wider sweep. Apply the AR-2 kinds only to client4 rows built by the backfill CLI.
- The full parity runs again on the new DB after the prepare, as part of its self-check.
- Time `_UNCONSUMED_AT` and record p95 in the packet. Above 20 ms p95: apply the low-water bound and drop `payload` from the select (inside AR-2).
- A fresh Claude reviewer reviews ANY-1 phase 2 now, in parallel.

**3. Other merges and machine rule.**
- C1 merges if it is ACCEPTed by 21:30.
- HON-1 and OPEN-NOW are not Thursday-critical (they target 17 Nov). They are held out of tonight's tag. They may merge to main after the tag is cut, once reviewed.
- Until 22:00, only the baseline and AR-2's own Postgres tests may touch Postgres, one at a time. Other builders run no-DB tests only.
- From 22:15 until the live checks end, **all builders stop**: no tests, no prepares, no Postgres. Code edits are allowed.

**4. Fallback.**
- If parity alone fails on the new DB: set the AR-2 kill switch (`ASSETOPS_PERIOD_READ_KINDS=` empty, so the old compose path is used) and rerun the board live checks (15 min).
- Any other self-check or live-check failure, or no green result by **05:00**: the demo uses `assetops_polish_client6_test` (tag demo/2026-11-11-e3d, runbook as planned). client6 is never modified.

Decision logged for owner review: **D-ANY.6**.

### D-ANY.6a AR-2 rows path misses a recompute job created after the row build (Architect, Claude, 2026-11-11 ~17:55, owner-delegated, logged for owner review)

- **Defect.** On the rows path, PENDING-at-k reads only unconsumed outbox events and snapshot dirty marks. The old compose path decides PENDING_RECOMPUTE from `recompute_job` itself (`mini_depth/read.py` `_JOBS`: status PENDING, LEASED or FAILED, `available_at <= k`, and no later selection), and it does so both live and at a historical k. A job raised by `mini_enqueue_hour` with no outbox event is therefore missed, and so is an existing PENDING job whose `available_at` was moved later.
- **Live-demo impact.** Tomorrow's add-dates enqueues exactly these jobs. Rows would read CURRENT while a recompute is pending, which is a false statement on the board. The fix is required, not optional.
- **Fix, ruled.** Do not emit events from the SQL function (a 0029 change with a wider blast radius). Do not use timing heuristics.
  - The rows path runs the oracle's own `_JOBS` predicate, batched: one statement over Sites × hours × mini domains at k.
  - An hour whose live job set at k equals the job set stored in its row renders from the row.
  - An hour with any other job set is served by the old `_hour` for that hour only. This is the D-ANY.1 rule "a case that cannot be proven equal stays on the old path". It is logged (`period_row_job_fallback`) and counted.
  - Byte-equal by construction. Expected cost is one extra statement per read; fallback hours are rare (only while a recompute is in flight).
- **Size and timing.** About 0.3 unit. Build by 19:45, Postgres test plus client4 parity by 20:30, review by 21:30.
- **If not ACCEPTed by 21:30: hold AR-2 entirely.** Do not merge it with the kill switch off. That gives the demo no speed, adds an unexercised prepare step, and leaves a latent false-CURRENT path. Tonight's build then uses main plus AR-1 (if its parity passed), and the boards stay on the pre-stored ranges.

Decision logged for owner review: **D-ANY.6a**.

### D-ANY.6b / D-E5.49a Tonight's build fails one check, CO-10 ("16 min unknown"): use client7 (Architect, Claude, 2026-11-11 ~22:10, owner-delegated, logged for owner review)

- **Finding.** In client7, the c1 warning reads "7 h 44 min out and 16 min unknown on 3 Nov".
  - 7 h 44 min + 16 min = 8 h, the whole charging day. The out-of-service part (08:16-16:00) is right.
  - The 16 min are 08:00-08:16, before the fault. The generated full-day heartbeat carries no connector status for c1 until the fault notice at 08:16.
  - The product is correct not to guess a status it never received. This is a data and story detail, not a product defect.
  - The D-E5.49 pin assumed status "known all day". The data does not give that.
- **Thursday demo:** use **client7**. The D-ANY.6 fallback covers failures that make the build untrustworthy. This one is an honest sentence about real data gaps, and the other 53 checks pass. client6 stays untouched as the fallback for any other failure.
- **Presenter line:** "c1 was out of service from 08:16 for the rest of the charging day; the first 16 minutes have no status reading; repair still pending."
- **17 Nov fix (data, about 0.1 unit, Sonnet):**
  - The EV-HB generator emits a c1 Available status with the day's first heartbeat at 08:00, so status is known all day.
  - Keep the D-E5.49 pin at 0 min unknown. Do not relax it.
  - Rerun CO-10 on the Monday build.

Decision logged for owner review: **D-ANY.6b / D-E5.49a**.

