# CC-R2 questions for the Architect (Lane C)

Branch `task/CC-R2-placement`. Owner rule: no isolated design decisions. Everything else in CC-R2 is built. Each
item below is built exactly as the spec says, or left unchanged, and I stopped there.

## CC-R2-Q1 Confidence reason texts trip the product vocabulary guard (same class as CC-R1-Q1)

The spec fixes the `confidence_reasons` texts as "Supported claim" / "Unconfirmed claim" and
"Registered simulation source" (build spec CC-R2 "Confidence", Q-C19/Q-C20). The Portfolio Confidence column shows
them joined by " · " (CC-R2 "Frontend"). `claim` and `simulation` are guarded terms in
`frontend/src/test/productVocabulary.json` (D-2026-10-04). CC-R1-Q1 kept `simulated` guarded and changed the
verdict label to "test data".

- **Built:** the backend sends the spec texts verbatim (`estate/placement.py:_confidence`, `_SOURCE_TEXT`), and the
  frontend shows them. No vocabulary scan runs on the Confidence cell. The placement reason lines, group headings
  and policy text contain no guarded term.
- **Needs:** the ruled texts for the two lifecycle reasons and the `REGISTERED_SIMULATION` source reason. For
  example "Supported Finding" / "Unconfirmed Finding" and "Generated test data source" (matching "Generated test
  data"). Alternatively, a ruling that the Confidence cell is exempt. Changing them touches only the texts in
  `placement.py`, `test_cc_placement.py`, `test_cc_placement_postgres.py`, and `portfolioFixtures.ts`.

## CC-R2-Q2 The W3-03 portfolio fixture has no EV Finding row

CC-00 fact, from a tier-2 run on `assetops_cc2_test`: `build_portfolio_fixture` (cold `excursion`, EV `complete`,
KOBO-001 W1) gives three Portfolio members:

- two cold Findings, `COLD_EXCURSION` and `COLD_START_FAILURE`, both with a null `episode_end`;
- the KOBO-001 W1 row.

The EV `complete` producer selects no EV Finding. The gate "the EV row is UNPRICED_RISK /
UNPRICED_SERVICE_INTERRUPTION unless CC-00 records rank 1 or 2" therefore has no row to assert.

- **Built:** `test_cc_placement_postgres.py` pins the CC-00 fact (`ev == []`). It asserts that `lens=risks` equals
  the set of cold and EV rows, which here is the two cold rows. It pins both cold rows to ACT_NOW /
  `EPISODE_OPEN` + `NO_ACTION_RECORDED`. EV placement is covered by the pure test only
  (`test_cc_placement.py::test_rule_5_unpriced_risk`, `EV_INTERRUPTION`).
- **Needs:** one of the following.
  - (a) Accept pure-only EV coverage for CC-R2.
  - (b) Name an existing producer with a selected EV interruption Finding to assert against. One possibility is a
    W3-01 golden EV case other than `complete`; I have not checked which one selects one.

## CC-R2-Q3 Panel copy now contradicts the Confidence column

`frontend/src/estate/EstatePortfolio.tsx` has a panel-bottom line, "Priority and confidence are not assessed for
these records." It is computed from `priority !== null && confidence !== null`, and `priority` is always null. The
panel subtitle `portfolioWords.ts:PRIORITY_SUBTITLE` says "...priority and confidence appear when assessed." Every
Portfolio row now carries a confidence, so the bottom line is no longer true. The spec does not cover either text.

- **Built:** both left unchanged. `estatePortfolio.test.tsx:136` still asserts the old bottom line.
- **Needs:** the replacement wording, or a ruling to remove the line. The `<details>` "How placement works" already
  sits under the table.

## CC-R2-Q4 The tier-3 capture has no estate Portfolio claim

Build spec §0.3 says tier-3 evidence uses `tools/s602b-verification-evidence.mjs` ("estate Portfolio for case
`estate`"). Adding `estate` to the walkthrough `CASES` makes that script's generic `casesSuite` check the F01
verification page (`expect.current_state` VERIFIED). The script has no Portfolio page claim, though: group
headings, reason lines and the three placements. The `.mjs` is not in the CC-R2 file list.

- **Built:** no change to the `.mjs`.
- **Needs:** confirmation that the coordinator's tier-3 step adds the Portfolio claim to the `.mjs`, or a ruling
  that CC-R2 adds it in a follow-up commit before capture.

---

# Rulings (Architect, Claude, 2026-10-28)

Checked against `estate/placement.py`, `EstatePortfolio.tsx`, `portfolioWords.ts`, `productVocabulary.json`,
`tools/s602b-verification-evidence.mjs`, `tools/s602b_test_scoped_cases.py`, the W2/W3 EV test chains, build spec
CC-R2, Appendix C D5 and v69 `#/portfolio` (`index.html:133-135`). Every literal below is exact.

## CC-R2-Q1 ruling: change the texts; no exemption

`claim` and `simulation` stay guarded (D-2026-10-04, CC-R1-Q1 precedent). The Confidence cell gets no exemption.
The texts follow the existing customer source words (`ui/productWords.ts:220-221`, `coldAssessmentWords.ts:108`).

| Fact | Old text | Ruled text |
|---|---|---|
| lifecycle not UNCONFIRMED | Supported claim | `Supported Finding` |
| lifecycle UNCONFIRMED | Unconfirmed claim | `Unconfirmed Finding` |
| source REGISTERED_SIMULATION | Registered simulation source | `Generated test data source` |
| source AUTHORED_DEMONSTRATION | Authored demonstration source | `Prepared example data source` |
| source MIXED | Mixed sources | unchanged |
| source UNKNOWN or null | Source not resolved | unchanged |
| WITHHELD | Cost basis withheld | unchanged |
| site coverage | Site coverage incomplete; other Findings may be missing | unchanged |

`AUTHORED_DEMONSTRATION` is not guarded. It changes so that the two source words read as a pair, matching
"Prepared example data". The enum codes and the confidence words ("Supported, coherent source" / "Limited" /
"Unknown") are unchanged. The Appendix C D5 example `confidence_reasons` reads with these texts.

Code:
- Update the texts in `placement.py` (`_confidence` and `_SOURCE_TEXT`), `test_cc_placement.py`,
  `test_cc_placement_postgres.py`, `portfolioFixtures.ts` and `estatePortfolio.test.tsx:132`.
- New test in `estatePortfolio.test.tsx`: render a Portfolio whose rows carry every confidence text and every
  reason text, then assert `forbiddenPhrases(priorityPanel.textContent)` is `[]` (from
  `src/test/productVocabulary.ts`).
- New pure test in `test_cc_placement.py`: no value in `REASON_TEXT`, `GROUP_LABEL`, `_SOURCE_TEXT` or the
  lifecycle, withheld and coverage texts contains `claim`, `simulat` or `scenario` (case-insensitive).

## CC-R2-Q2 ruling: (b), using the existing EV `interrupted` chain

The fixture fact stays pinned (`ev == []`). Change the module docstring to say so, and remove "open question
CC-R2-Q2" from it.

CC-00 records that the EV `complete` case selects no Finding. W2-05b `interrupted` selects exactly one SUPPORTED
`EV_INTERRUPTION` Finding, and its session `end_at` is null (`test_w205b_ev_replay_postgres.py:132`,
`test_w206_ev_reads_postgres.py:248-262`). So CC-00 records rank 2 for an EV row (Q-C21: EV can only be open). The
spec's "unless CC-00 records rank 1 or 2" applies: the expected value is ACT_NOW, not UNPRICED_RISK.
`UNPRICED_SERVICE_INTERRUPTION` stays pure-only (`test_rule_5_unpriced_risk`).

New test `test_ev_interruption_placement(ev_chain)` in `test_cc_placement_postgres.py`. No builder is
parameterised.
1. Build: `built = ev_chain("interrupted")`, then `built.start_release_upload()` and `run_worker(built)`, as
   `test_w206_ev_reads_postgres._settled` does. Then run `golden_tariff(built, currency="KES")` and `money(built)`,
   and assert every outcome succeeded, as `build_portfolio_fixture` does.
2. Read: `Portfolio(built.engine, built.tenant_id).ok(...)` for the window 2026-10-06T00:00:00Z to
   2026-10-07T00:00:00Z with `limit=100`. Use the same keywords that `fx.window` passes.
3. Assert exactly one row, with these values:
   - `domain == "EV_CHARGING"` and `mechanism == "EV_INTERRUPTION"`
   - `episode_end is None` and `workflow_label == "Recommendation not accepted"`
   - `placement == ACT_NOW_OPEN`
   - `confidence == "SUPPORTED_SOURCE_COHERENT"` and
     `confidence_reasons == ["Supported Finding", "Generated test data source"]`
   - `priority is None`

   Also assert `double_count_violations(body) == []`. The same window with `lens="risks"` returns that one row.
4. **Stop** (report it; never fake it): there is no EV row, the source is not `REGISTERED_SIMULATION`, or
   `episode_end` is not null.

## CC-R2-Q3 ruling: replace both texts; the bottom line no longer depends on priority

v69 (`index.html:133,135`) reads "Findings ranked by consequence and urgency, with evidence confidence alongside."
and "Priority and confidence answer different questions." The build places Findings in groups and does not rank
them (CC-R2 Rejected: numeric priority). The column is "Placement" (CC-R2 Frontend).

- **Subtitle.** `PRIORITY_SUBTITLE` =
  `"Selected Findings across accessible Sites, grouped by where to look first, with evidence confidence alongside."`
  **MOCK DEVIATION:** the mock says "ranked by consequence and urgency". Groups are not a value ranking, as the
  policy footer says.
- **Bottom line.** New `portfolioWords.ts` literal `PRIORITY_BOTTOM_LINE` =
  `"Placement and confidence answer different questions."`. The panel-bottom `<span>` shows it when
  `rows.length > 0`. When there are no rows, omit the `<span>` and keep the "Open all Findings →" link. Delete the
  `both` computation. **MOCK DEVIATION:** the mock says "Priority", but the spec renames the column to
  "Placement".
- **Tests.** `estatePortfolio.test.tsx:137` asserts the new line. Add an assertion for the subtitle literal. Add an
  empty-rows render that asserts the panel bottom has no `<span>`. Use the existing empty Portfolio test if there
  is one; otherwise add one.

## CC-R2-Q4 ruling: CC-R2 adds the Portfolio claim in a follow-up commit, before capture

The builder adds the claim on `task/CC-R2-placement`. CC-R2's file list gains `tools/s602b-verification-evidence.mjs`
and `tools/s602b_test_scoped_cases.py`. The coordinator runs the capture.

**Producer change (`s602b_test_scoped_cases.py:estate_assertions`).** The returned dict also carries
`"rows": {"F01": "<finding_id>|<finding_revision_id>", "F03": ..., "F05": ...}`. Each value is the row's
`data-portfolio-row` key.

**Script change (`.mjs`).** Add `async function portfolioSuite(label, c)`. `casesSuite` calls it after the generic
verification claim when `c.placement` is present, which is case `estate` only. Keep the existing F01 VERIFIED claim.

`portfolioSuite` loads `${CASES_BASE}/portfolio?from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z` with ready
`${settled} && document.querySelector('[data-estate-root="portfolio"] [data-portfolio-row]')`. It makes these
claims:
1. **Group headings.** The `[data-placement-group]` values, in DOM order, have no repeats and follow GROUPS order.
   They include `NEEDS_INVESTIGATION`, `ACT_NOW` and `MONITOR`. Each heading's text is exactly
   `` `${GROUP_LABEL} · ${c.placement.counts[group]}` ``. When `counts` is null, the text is the label alone.
2. **Three placements.** Each row `[data-portfolio-row="<key>"]` has the expected `data-portfolio-placement`:
   MONITOR for F01, ACT_NOW for F03 and NEEDS_INVESTIGATION for F05. The nearest `[data-placement-group]` row
   before it holds the same group.
3. **Reason lines.** These check the `[data-portfolio-placement-reasons]` text.
   - F01 equals `Change verified on test data; watch for a return`.
   - F03 matches `/Returned after an earlier episode \(Finding [0-9a-f]{8}\)/` and contains
     `No accepted Action; open the recommendation`.
   - F05 contains `The latest assessment no longer confirms this Finding; check its basis`.
4. **Confidence.** Every row's `[data-portfolio-confidence]` attribute is one of the three codes, and its text is
   not empty. The text of `[data-portfolio-panel="priority"]` matches none of `/\bclaims?\b/i`, `/simulat/i` or
   `/\bscenarios?\b/i`.
5. **Bottom line and policy.** The panel-bottom `<span>` text equals the Q3 literal. The `<details>` summary "How
   placement works" is closed on load. When opened, it shows the five policy lines and the footer.
6. **Layout.** Call `noOverflow(label, "estate Portfolio")` and
   `mockScreen(label, "portfolio", "document.querySelector('.priority-panel')")`. Then call
   `comparison.push(["portfolio (priority panel)", label, mockHeadings, await headings()])`.
7. **Screenshots** at each width: `app-case-estate-portfolio-${label}` before the disclosure is opened,
   `app-case-estate-portfolio-policy-${label}` after it, and `mock-portfolio-${label}`.

**Viewports.** Use the script's existing `WIDTHS`: desktop 1440×1000 and narrow 390×900. At 390 the table scrolls
inside its own scroller, and the page never scrolls sideways. This is the same rule as the mock's 760px rule.

**How it is produced** (tier 3, §0.3; DBs per Q-C47):
1. Run `python tools/s602b_verification_walkthrough.py --db assetops_s602b_audit_cc --work var/s602b_cc prepare`.
   If a placement assertion fails, case `estate` exits before any capture.
2. Start both frontends as `serve` prints them (web 5466 and 5467). `serve` must not be running.
3. Run `python tools/s602b_verification_walkthrough.py --db assetops_s602b_audit_cc --work var/s602b_cc capture`.
   Its parts include `ASSETOPS_S602B_PART=estate`.
4. Put this evidence in the packet: `var/s602b_cc/evidence/results-estate.json` with every claim `ok`, the six PNGs
   and the `comparison.md` row. Then run `... drop`.

If Chrome is unavailable, record `layout evidence: not run`. The slice merges on review ACCEPT, and the capture runs
before the Lane C Codex batch review.
