# W1-UX-02 review packet - Site, Finding and money presentation

Task `tasks/W1-UX-02-site-money.md`; umbrella `tasks/W1-UX-mockup-fidelity.md`; decisions `D-2026-10-16-w1-ux`, `D-2026-10-16-w1-ux-disclosure`; shared API `.agent/W1-UX-01-handoff.md`. Branch `task/W1-UX-02` from main `a8cbb3d1`; review diff `git diff b982905b..HEAD -- ':!.agent'`. Frontend and one evidence tool only. No backend change. USER_REVIEW_REQUIRED: a fresh independent slice review gates merge. There is no per-slice owner walkthrough; the owner sees these screens in the combined W1 walkthrough.

## Outcome delivered

All eight screens now lead with the v69 question as a `HeadlineVisualCard`. Beside each lead sit a shared `ProductStatus` state line (plain state, scope, "As of"), a small visual (`StepStrip`/`ValueBars`/strip figure; an unknown value is a hatched "not known" mark), "What this means"/"What to do", the owning destination link and the closed `ExactReferences` disclosure, which comes last. Raw codes, IDs, revisions, versions, cursor tokens and raw reasons were moved out of the default reading into labelled exact references.

All eight routes are opted into the W1 vocabulary set. Duplicate word maps were wrapped, then replaced: `FRESHNESS_WORDS` removed, `MONEY_STATE_WORDS` now uses `moneyWords`, `CURRENTNESS_WORDS` became `findingCurrentnessWords`, `STATUS_WORDS` uses `currentnessWords`, and `STATE_HEADLINE` became `consequenceWords`. Domain-only states keep local `ProductWords`; unknown codes fall back non-positively.

## Migrated call sites (path:line at HEAD)

| Screen | Card / state line / visual / destination / disclosure |
| --- | --- |
| `sites` | `frontend/src/sites/SitesIndex.tsx`. `SitesAnswer` :212, state :221 (local words :189 "Registered sites, not ranked"), scope tiles :223, `ExactReferences` :257. Empty card :139, unreadable card :119 (`readResultWords("unavailable")`). Three `MissingClaim`s unchanged. No destination by Architect rule (a directory links by row). |
| `mini` | `frontend/src/sites/SiteWindowOverview.tsx`. Objective card first :769, question :308. Freshness strip :232 (`currentnessWords`, as of `db_now`), refs :247. Money :616, `MONEY_STATE_WORDS` :150, state :641, `ValueBars` :646 (PRICED with both bounds only), refs :670. Timeline figure :376. Audit-only Finding state :729, refs :737. `frontend/src/sites/OverviewFindingList.tsx`: state lines :244-289 (as of `knowledge_at`), refusals :333/:348, rows :181-184 without short codes, `ListReferences` :218. S5-02 no-parity kept. |
| `sitefindings` | `frontend/src/sites/SiteFindingIndex.tsx`. `Loaded` :420 (not current :428, proved zero :445, rows :468), `RefusedCard` :511, `Refused` :550. State lines :433/:450/:473/:537. `DayStrip` :297 (also in the rows state). `Rows` :360. Destination :500. `ExactReferences` :423/:542 (`bodyReferences` :303). `STATUS_WORDS` :89. |
| `finding` | `frontend/src/sites/SiteFinding.tsx`. `FindingAnswer` :280 (Overview and Analysis), state :303, causal `StepStrip` :335 (the Consequence step is always "not known"), destinations :362/:366, disclosure :372, refusal card :148. `findingWords.ts:114` `findingCurrentnessWords`. `findingPresentation.tsx:448` `FindingRefusalCard`. |
| `finding-evidence` | `frontend/src/sites/SiteFindingEvidence.tsx`. Card :348, state :362, record-trail strip :393, links :410, disclosure :424. `LINK_WORDS` stays word for word with backend `BROKEN_WORDS`. `LINK_DISPLAY_OVERRIDES` rewords the two "fingerprint" codes on screen only. |
| `finding-history` | `frontend/src/sites/SiteFindingHistory.tsx`. Card :261, state :285 (as of the selected version's recorded time), timeline :320, links :331, disclosure :341 (revision references, page cutoff). |
| `financials` | `frontend/src/sites/FindingConsequence.tsx`. `consequenceWords` ~:73-145, card :600, state :617 (S4-05 `SourceProvenanceNotice` beside it), `MoneyVisual` :449-459, `data-financials-why` line, destinations :661, `ExactReferences` :667. LR-01 `MoneyLimit` kept. `SiteFinancials.tsx:689` `PriceTimeStrip`. |
| `assumptions` | `frontend/src/sites/SiteFinancials.tsx`. Card :403, state :422 (as of the price list's `cutoff.recorded_at`), `PriceTimeStrip` :425, `ExactReferences` :448 and :597, refused :109, no cutoff :310. `MissingClaim G-assumptions-human-edit` unchanged. `frontend/src/sites/ConsequenceHistory.tsx`: recorded-only state :173 (never "current amount"), row refs :138, refused :231. |

CSS lives only in four new per-group files, `frontend/src/sites/w1ux02-{site,finding,findings-index,money}.css`. There are no shared-file edits: `ui/*`, `test/*`, `productVocabulary.json` and `primitives.css` are untouched.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Directory answers "Which site should I open?", registered scope, evidence limit, no health score | Met | `sitesIndex.test.tsx:687-750`; capture `sites` |
| Overview: day headline, timeline, scoped Finding row, bounded money card | Met to read strength | `s5SiteWindowOverview.test.tsx:377-560`, `s502OverviewFindingList.test.tsx:417-515` |
| Finding index/detail/evidence/history: conclusion, cause, consequence, next step; timeline/record trail; exact revision, source, day and history links kept | Met | `siteFinding.test.tsx:562-700`, `siteFindingEvidence.test.tsx:796+`, `siteFindingHistory.test.tsx:458+`, `s404SiteFindingIndex.test.tsx:257+` |
| Amount only when the current priced read qualifies; explicit "why no current amount" | Met | `siteFinancials.test.tsx:1193-1302` (9 non-positive states draw a not-known mark and no amount; 3 withheld states) |
| Price and effective-time visual; S4-08 history keeps its no-current-amount guarantee | Met | `siteFinancials.test.tsx:1302,1315-1440` |
| Raw IDs, versions and cursor tokens in labelled exact detail; plain "As of" stays in the default reading | Met | the per-route W1 tests assert absence outside and presence inside the disclosure |
| Every route opted into the W1 set; disclosure scan | Met, 8/8 routes | the `W1-UX-02:` tests above |
| `expectStateLineVisible` on every non-positive state; explicit checks for states with no recorded time | Met | listed per file above; untimed states assert "As of: time not recorded" explicitly |
| `MissingClaim`, S5-02 no-parity, S4-04 proved-zero, S4-05 provenance and LR-01 withheld states retained | Met | missing-claim scan passes (31 placements); the existing tests still pass |
| 1440/390 served captures against v69 | Met (see Checks) | `tools/w1-ux-02-evidence.mjs` |

## Changed existing test assertions (none weakened)

- `s404SiteFindingIndex.test.tsx`:
  - :116: the token text moved into the exact-reference row "List reference", with the same equality.
  - :116: the per-day "Assessed" cell became the strip step `data-step="done"` "Checked, and Findings matched".
  - :168: the link named by a short ID became "Recurs after an earlier Finding", with the same href plus `data-finding-index-related`.
  - :223: raw reasons moved to the exact row "Reason recorded 1", matching `/^2026-10-25: /`.
  - Added: the rows-state card has a day strip.
- `s502OverviewFindingList.test.tsx` :202 and :279: token text became `exactValue(..,"List selection reference")`, with the same equality.
- `s5SiteWindowOverview.test.tsx`, each now also asserting `expectStateLineVisible`:
  - :272 "Source closed" became "No current amount: source not open".
  - :293 "Unknown" became "We have not checked this period".
  - :336 "Failed" became "The latest check could not be completed".
- `sitesIndex.test.tsx` ~:474: the exact interactive-element list now starts with `DETAILS`/`SUMMARY` for the disclosure. It is still an exact list.
- `siteFinding.test.tsx`:
  - Chips: "Up to date" became "Using the latest checked readings"; "Earlier version" became "Earlier version, kept for the record"; "Not released" became "For the record only". The old negative `not.toMatch(/Up to date/)` is kept, and `not.toMatch(/Using the latest checked readings/)` is added.
  - Headings: "Not confirmed" now carries the full conclusion; "Open · out of date" became "Open in the last recorded version: ...".
  - The :344 `it.each` labels use the shared words, plus `expectStateLineVisible` and not-positive checks.
  - The mounts are wrapped in `<main>` so the scan runs on `<main>`.
- `siteFindingEvidence.test.tsx` :373 and :437: "first p/first child" became "first note of the state line after the sentence", plus `expectStateLineVisible`. The broken-link wording says "check value", from the display overlay.
- `siteFindingHistory.test.tsx` :254 and :338: same change, with the exact label.
- `siteFinancials.test.tsx`:
  - :481 "No price for the whole window" became the label "No price recorded", plus the exact UNPRICED sentence and the `data-financials-why`.
  - :547: the sentence drops "fuel-cost-1"; a new assertion checks the version is absent outside the disclosure and present inside it.
  - :560-567: the summary became "How this was worked out", and the readings row is asserted in its own closed details.
  - :781 and :854: withheld and reassessing now assert the label "No current amount can be shown" plus the exact `moneyWords` sentences.
- `findingLinkWordsParity.test.ts` is unchanged and passes. Group B's first cut had reworded `LINK_WORDS` and broken backend parity. It was restored, and the rewording moved to a display overlay. The new guard is `siteFindingEvidence.test.tsx` "rewords only backend-held link codes...". It was proven non-vacuous: with the overlay removed, 3 tests fail (reverted).

## Checks (final code revision `bc1cea1b`)

- Focused group runs: all pass (group reports; for example `s404` 29/29, siteFinancials and related 154/154, Finding family 145/145, sites and mini 137/137).
- `npx.cmd tsc --noEmit -p .`: 0 errors.
- Registry checker `check_v69_dependency_registry.cjs`: exit 0. `tools/check-all.ps1 -ExecutionPolicy Bypass`: all 9 guards passed.
- Full `npm.cmd test`:
  - At `f4b16c05`: 1 failed / 1838 passed, 74 files, 166 s. The failure was `findingLinkWordsParity` (fixed in `3179d267`).
  - Final run: at `bc1cea1b` 74/74 files, 1840/1840 tests passed, 145 s (wall 2 min 28 s). No flake hit.
- Captures: `node tools/w1-ux-02-evidence.mjs %TEMP%\w1ux02-evidence <id>[:case]=<url> ...`, one walkthrough at a time, each dropped afterwards. 50 PNGs. Per walkthrough (all at 1440 and 390; mock `#/<id>` captured beside each):
  - `sites` and `sites:empty`: v01a, private `assetops_v01aw1ux02`/`assetops_v01aempw1ux02`. 30/30 at `bc1cea1b`. The empty state is recorded as "no exact-reference disclosure in this state". The first run at `3179d267` failed 6 claims, only because the empty card had no disclosure; the script now records that case.
  - `mini:p01`, `mini:unassessed`: s5. 32/32.
  - `finding`, `finding:stale`, `finding-history`: s4_finding. 49/49.
  - `finding-evidence`, `financials:provenance`, `financials:withheld`: s405 owner case. 49/49. A first attempt scored 0/12 because a vite process died; it was restarted and rerun.
  - `sitefindings` and `sitefindings:empty`: s404. 32/32 at `bc1cea1b`. The first run failed "small visual" in the rows state; fixed in `6f3e9fb6` by adding the day strip to the rows state.
  - `financials`, `financials:notcalculated`, `financials:emptyprice`: s402b. 47/47. The stale `assetops_s402bcases` template was rebuilt with `tools/s402b_power_cases.py run`.
  - `assumptions`, `assumptions:history`: s408 owner case. 32/32 after the script's visual detector learned `figure[data-price-strip]` (`6e10b27c`).
  - Every server was stopped and every `%w1ux02%` DB and work folder dropped. `s4_finding_cases.py run` also needed `var/sites/kobo-001.yaml` (ignored copy).
  - The 390 claim confirms `documentElement.clientWidth` is within 370..390 before any narrow claim.

## Known deviations

- `FindingDetail.tsx` (packet seam) is unchanged. It is the legacy `/findings/{site}/{assessment}` page; `/sites/{site}/findings/{finding}` renders `SiteFinding.tsx`, which was migrated.
- Mock elements with no read are not built: the directory's attention/evidence-limited counts, type chips and per-site columns; the five-objective strip; Finding priority/confidence chips; the index's lens chips and priority/confidence/domain columns; the Financials revenue/asset/realised-savings tiles, maintenance line, trade-offs and Scenarios; and editable Assumptions with an impact preview (that gap stays tagged).
- No Financials Analysis tab was added. Method and limits stay visible in the "From finding to money" panel. The counted-readings table sits in its own closed `Disclosure`, not `ExactReferences`; the Evidence link is the owning destination.
- Several states have no read time, so they show "As of: time not recorded" and are tested explicitly:
  - the directory, list and refusal reads;
  - the Financials non-positive states;
  - (Corrected in fix round 1: the s402b priced case is not untimed. The API always serialises `recorded_at`; the capture judged the card before the second read landed. See Fix round 1, L1.)
  - A read time on the bridge needs an Architect decision.
- `tools/s502-overview-finding-list-evidence.mjs:148` reads `[data-finding-index-token]`, which no longer renders on the Overview. That historical script needs updating if it is reused.
- Local word maps that could become shared kinds later:
  - the index's `REFUSAL_WORDS` (closed, continuity, list changed, invalid, unauthenticated);
  - finding-only currentness states;
  - consequence-only money states.

## Residual risk

- Two screens are much longer than the mock (Overview, Financials), because existing sections stay below the new lead.
- Group-built: four parallel sub-implementers on disjoint files, integrated by the implementer. The reviewer should read the four groups' diffs as one.
- Money-gate words "Eligible"/"Pending reassessment" on the Overview money card are unchanged.

## User-review focus

- Do the eight lead cards answer the v69 question without overclaiming?
- The untimed "As of: time not recorded" states.
- The Financials readings table living in a closed disclosure.
- The display overlay for the backend's "fingerprint" link words, which a backend slice should retire.

## Fix round 1

Review `.agent/W1-UX-02-review.md` (RETURN, one Medium).

- **M1 fixed.** `SiteFinancials.tsx`: when the view is historical (`recorded_at` set), the headline reads "Diesel price covering today, as recorded then: <price>" and the strip's selected entry reads "Covered today, as recorded then" (new `recorded-then` state; `data-price-strip-entry="recorded-then"`). The default view keeps "Diesel price in use" and "In use today". The earlier-moment test now asserts the headline and strip carry no "in use" text, no `in-use` strip entry, and one `recorded-then` entry. The state sentence still says "may not be the price in use now", which is a hedge, not a claim, so the assertion is scoped to the headline and strip.
- **L2 fixed.** `FindingBridge` takes `consequencesLoading`; a PRICED CURRENT bridge draws "Loading the finding's money view." until the consequences read settles (no amount, no untimed bound). New test holds the second read open, asserts no headline amount, no `0.00 to 16.20` and no "time not recorded", then releases it and asserts the amount appears.
- **L3 fixed.** `SiteWindowOverview.tsx` `Money`: a `PRICED` read missing a bound uses the shared non-positive fallback words, so no "Current amount" label and no positive tone. New test (low and high each missing).
- **L5 fixed.** `STATUS_WORDS` in `SiteFindingIndex.tsx` is still used locally (line ~263, table day status), so it is not deleted; the `export` and the stale comment are removed. Nothing imported it (the other `STATUS_WORDS` is `dispatchWords.ts`, unrelated).
- **L1.** The packet's s402b explanation above is corrected. `tools/w1-ux-02-evidence.mjs` now (a) waits for the second read (`[data-financials-bridge-loading]` gone) plus 800 ms before judging the Financials card, as its own claim, and (b) accepts "As of: time not recorded" only when no amount is drawn (`amountShown` false: no `data-financials-amount="shown"` and no PRICED price selection). The script passes `node --check`. **Evidence re-capture: not run.** The walkthroughs need a live Postgres and the s402b/s408 templates; none was listening in this session, so the Financials/Assumptions 1440/390 captures are unverified after the fix. No fixtures were created, so none to drop.
- **For the owner's list (not fixed):**
  - L4: the Overview money card and Financials word the same money codes differently ("Fuel quantity not known" vs "Not calculated: no fuel amount, so no cost"); the Overview's "Upstream out of date" label and "Upstream" term are jargon. Belongs in the batched W1 plain-language task.
  - L6: non-positive Financials states (STALE, LR-01-withheld) show "As of: time not recorded" although the loaded recorded cost has a `recorded_at`; that instant dates the recorded cost, not the "no current amount" judgement, and the bridge carries no read instant. Needs an Architect decision with the existing "read time on the bridge" item.
- **Checks.** `npx.cmd tsc --noEmit`: clean. Focused `siteFinancials` (74) and `s5SiteWindowOverview` pass; the vocabulary tests (`t028Vocabulary`, `sharedVisualVocabulary`, `findingLinkWordsParity`, `productStatus`) ran inside the full `npm.cmd test`: 74/74 files, 1843/1843 tests, 128 s, no failure and no rerun needed. Two first-attempt test failures during the build were test-scoping mistakes (a whole-card "in use" match that hit the legitimate hedge sentence; a loading text shared with the bridge-null state) and were corrected in the new tests, not by weakening any assertion.
