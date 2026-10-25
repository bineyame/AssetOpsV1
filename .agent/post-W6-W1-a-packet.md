# post-W6 W1-mini-Action-a: review packet

**Task:** card W1-mini-Action-a (`.agent/post-W6-audit/fix-slices.md`), as amended by the binding rulings in
`.agent/post-W6-W1-rulings.md` (cross-card 1-5, 6-29, and closeout points 48-63).
**Branch:** `task/post-W6-W1-a`. Main (shell 4fc39160, W3-estate d9a73b80) is merged in.
**Reviewer diff:** `git diff main...HEAD -- ':!.agent'`.
**Product commits:** 575fc2ab, b09a5c07, cf4266f0, 2afb0fcf, de2da2fc, 56d36bf2, 22a1dd70 (comments only), a054e1ae (test only).
**User review:** none of its own. Per the owner-absent / W1 rules it merges on independent review ACCEPT; the owner sees it in the post-W6 walkthrough. The D2 rows R389, R392 and R395 wait for owner approval there.

## Outcome delivered

All 18 D3 IDs are built as ruled:
R156, R157, R159, R164, R171 (measurement only), R178, R184-R193, R195, R196.

Cross-card 1:
- `sites/siteTime.ts` is the same blob as W2-EV 3c533f0f (`2b390038`).
- `findingTime.ts` is a thin wrapper over it.
- Shell's measured-time helpers in `LedgerSiteEvidence.tsx` now hand their work to it.

Every ruling, with file anchors, is in `.agent/post-W6-W1-a-handoff.md` "What landed". In short:

**Mini Overview**
- The breadcrumb ends `› Overview`, with the Site crumb linked.
- The objective cards' "View detail" links move to the card footer:
  - Dispatch links to the selected day; Battery links to its Asset page.
  - The Dispatch border follows only the stored classification.
- Operating context gets an SLD panel-head link.
- The Finding's reasons are labelled "Finding reason {n}", so they no longer repeat the assessment's labels or keys.

**Dispatch**
- A whole-window revision is refused with the ruled copy and an "Open this day" link.
- Before, the page went blank.

**Finding**
- Section row:
  - Analysis is a live tab.
  - "Open site" is on every section.
  - The money aside is gone.
  - A refused selection shows the short disabled Alternatives tab, with its full reason on the line below.
  - The ruled headings are in place.
- Overview:
  - The status period is in Site time, with a closed "UTC time" detail.
  - New links: "Inspect evidence", "Inspect financial assumptions", "See analysis and alternatives", and an Alternatives item in "Where to look next".
  - One cost read is made for the exact Finding version.
- History: a "Time ({zone})" column in local time, with the exact UTC instant in the title and the detail.

**Site Findings**
- The lens chips sit above the strip.
- Cost, Risks and Opportunities stay disabled (D5).
- The strip carries "Manage in Findings →".

## Files materially changed

**Mini Overview and Dispatch**
- `sites/SiteDetails.tsx`
- `shell/SiteDetailFrame.tsx`
- `sites/SiteWindowOverview.tsx`
- `sites/PerformanceDispatch.tsx`
- `sites/performanceDispatchClient.ts`

**Finding pages and Site Findings**
- `sites/SiteFinding.tsx`
- `sites/SiteFindingEvidence.tsx`
- `sites/SiteFindingHistory.tsx`
- `sites/SiteFindingIndex.tsx`
- `sites/SiteRecommendation.tsx`
- `shell/SiteAnalyticsFrames.tsx`

**Time**
- `sites/LedgerSiteEvidence.tsx`
- `sites/siteTime.ts` (new)
- `sites/findingTime.ts` (new)

**Guards**
- `test/panelStructure.ts`: the leading-element allowlist admits `[data-alternatives-finding-unavailable]`, the line ruled under Q16.
- `tools/checks/navigation-truthfulness.ps1`: in the expected inventory, Alternatives replaces Analysis, under Q7/Q16.
- `tools/checks/navigation-rail-fixtures.ps1`: the fixtures are rewritten to match. check-architecture passes, which confirms each fixture's mutation still makes the guard fail.

**Register:** `.agent/mock-departure-register.md`
- R21 is narrowed.
- New rows R386-R395. R383-R385 belong to W1-b.

## Acceptance criteria (rulings), status

| Ruling | Status | Evidence |
|---|---|---|
| Q1 R156 | done | `siteDetailScreen`, `s5SiteWindowOverview` W1-a block, `siteDetailRoute` |
| Q2/Q48 R157 | done | s5 W1-a Q2 tests (footer slot, destinations, tones, no invented value) |
| Q3 R159 | done | s5 Q3 tests (selected window and bare route) |
| Q4 R164 | done | s5 Q4 (both lists, distinct labels, no duplicate-key warning) |
| Q5 R171 | measurement | capture caps table (see Captures) |
| Q6 R178 | done | `performanceDispatch` (window-shaped, WINDOW scope, other-day valid interval) |
| Q7 R184 | done | `miniDecisions` W1-a test (live Analysis, aria-current); u6b updates |
| Q8/Q13 R185/R190 | done | `siteFinding` Q8 test; old aside expectations flipped |
| Q9 R186 | done | `miniDecisions` (Open site on all sections) |
| Q10 R187 | done | `siteFinding` Q10 (Addis, UTC, midnight, fallback); `findingTime.test.ts` |
| Q11 R188 | done; cap see Captures | `siteFinding` Q11 |
| Q12 R189 | done | `siteFinding` Q12: priced, withheld, unpriced, stale, failed, missing, wrong-revision, no-read |
| Q14 R191 | done; cap see Captures | `siteFinding` Q14 |
| Q15 R192 | done; cap see Captures | `siteFinding` Q15 order and hrefs |
| Q16 R193 | done | `siteFindingEvidence`, `siteFindingHistory`, `miniDecisions`, `w1f4RecommendationStructure` |
| Q17 R195 | done; cap see Captures | `siteFindingHistory` Q17 (EAT, UTC fallback); `findingTime` boundary day |
| Q18 R196 | done | `s404SiteFindingIndex` (lenses above strip, disabled, Manage URL) |
| G1/Q46 splits | done | R387-R394 rows, plus `MOCK DEVIATION` source labels |
| Q47 | done | R386 backlog row (global error boundary) |
| Q52 | done | R395 row, plus source label |
| Cross-card 1 | done | `measuredTime.test.ts` (shell's tests plus the delegation case), `siteAction.test.tsx` title contract |

**Mutation proofs:** every new test fails with its fix reverted.

| Unit | Failing tests with fix reverted |
|---|---|
| Dispatch | 2 |
| Overview | 9 |
| Finding and Site Findings | 33 |

## Checks run

**Full vitest**
- Final run at a054e1ae: 3068 of 3068 passed, wall time 3 m 13 s.
- Earlier run at ec9bfbe9: 1 failure. `siteDetailRoute`'s pinned link list did not include the new linked Site crumb. Fixed in 56d36bf2.
- Run between those (22a1dd70, while another agent was capturing): 2 failures under load, both passing in isolation.
  - `evEnergy` "store read has not settled": not this slice's code.
  - The 205-version History heading assertion: it now waits for the frame's title effect (a054e1ae).

**Other checks**
- Production build (`npm run build`) at 56d36bf2: passed. The only warning is the existing chunk-size warning.
- `tsc --noEmit`: clean.
- `check-all.ps1` at a054e1ae: all 11 guards passed.
- Backend suite: not run, because this is a frontend-only slice (coordinator).

## Captures

Recapture: `.agent/post-W6-W1-a-recapture/index.md`. Per-batch `run.md` files give the producers, DBs and ports.

**Coverage**
- 98 of 98 pairs captured at 56d36bf2, at 1440 and 390: the 88 indexed W1-a pairs and 10 Q40 representatives.
- Later commits change only comments and register text, so the captures match the final SHA.

**Results**
- No capture gaps for producible states (the five-long-row case is covered by the fix-round synthetic probe below).
- overflowX is 0 on every pair.
- 96 of 98 pairs match the frozen panel titles. The two that differ are dispatch `window-id-as-revision`, where the frozen run was a blank page and this run shows the R178 refusal: "This assessment cannot be shown as 15-minute blocks", with "Open this day".

**Closed caps: all pass.** Each value is the highest among the cases that are not exempt.

| Screen | Panel | 1440 (cap) | 390 (cap) |
|---|---|---|---|
| finding | What happened | no cap at 1440 | 562 (600) |
| finding | What limits this conclusion | 343 (450) | 493 (800) |
| finding | Where to look next | 613 (650) | 716 (1000) |
| finding-history | Revision history | 635 (850) | 1188 (2000) |
| dispatch | Selected block | not measured | 640 (750); refusal 126 |
| evidence-analysis | How each limit is set | 311 (400) | 542 (800) |
| evidence-analysis | Accepted records behind the conclusions | 919 (1200) | 1097 (1800) |

**Q11 and Q15 fallbacks:** not needed for the producible states. The fix-round synthetic probe showed five 160-char related rows exceed 650 at 1440, so the Q15 fallback was then applied (see Fix round). Q11 not applied.

**Five-long-row case (Q38, Q42):** a capture gap for producers; superseded by the labelled synthetic probe in the Fix round. Original note: The producers cannot make five 160-character related-Finding or limit rows, because the rows are fixed words. Unit tests confirm every related and limit row renders. Height cannot be measured in jsdom.

## Known deviations

1. Q10: superseded by Architect closeout ruling 2 (fix round): the What happened description and its prose sentences now use the same Site-time period. Remaining UTC-labelled repeats: the Analysis-view answer card scope, the Analysis `StatusChips` period and the chosen-block caption/axis (block-level, labelled UTC).
2. Q12: confirmed by closeout ruling 4; the reason now names the currentness (exact STALE text).
3. Q16:
   - While the selection is loading, Alternatives is plain text; the disabled tab appears only on refusal.
   - The full reason is on its own line below the tab row. That needed one entry added to the leading-element allowlist.
4. Q18: the opportunity helper stays inside the panel. Moving it above the strip would trip the panel-structure guard.
5. Cross-card 1:
   - Asmara, Djibouti and Mogadishu keep the shell's "EAT" label in a small set in the wrapper, because `siteTime.ts` must stay identical to W2-EV's.
   - W2-EV can fold these three zones into the canonical table.
6. The Recommendation Analysis helper stays for W1-b to remove (Q28/Q44).

## Residual risk

- Each W2 branch must rebase over the mini Finding hunks listed in the handoff and rerun the mini regression tests.
- The cost card sends one extra GET for each loaded mini Finding. A failed or slow read shows "Not available", never a stale amount.

## User-review focus

- The Finding page's new links, and their order in "Where to look next".
- The status period in Site time.
- The Cost exposure card's states.
- On a refused Finding, the disabled Alternatives tab and the reason line below it.
- The Site Findings lens row above the strip.


## Fix round (review M1, L1, L4; closeout rulings 1-4)

Commits on `task/post-W6-W1-a` after 3fd3df6d: 7ec5a29a (rulings 1-4, L1 test), a typecheck fix, the L1 proof-hardening test commit, and the M1 Related Findings fallback commit; then probe tools/captures and this record. Rulings file: `.agent/post-W6-W1-a-closeout-rulings.md`.

**Product changes (all in `frontend/src/sites/SiteFinding.tsx`)**
- Ruling 2: `periodText()` uses `findingLocalPeriod`; What happened description is exactly `Period covered · {local period} · {duration}`; its three prose sentences and the series-limit end line use Site time. Unformattable instants show the UTC-labelled period.
- Ruling 3: one suffix `(site time zone unavailable; UTC shown)` for missing and invalid zones (replaces "not recorded").
- Ruling 4: gate already required PRICED, CURRENT, amount, currency; a not-current priced answer now says why. STALE: "The cost for this Finding version is out of date; no current amount is shown."; other currentness values are named.
- M1 fallback (Q15): more than two related Findings sit behind the count disclosure "Show all N related Findings" (`RELATED_INLINE_MAX = 2`); every link stays reachable. Choice of threshold is mine (the ruling gives none): it keeps the one- and two-related real states unchanged.
- Ruling 1: R386 register row replaced verbatim.

**Tests and revert proofs** (`siteFinding.test.tsx`, 75 tests): ruling 2 (Addis period, template, prose agreement; series-limit end), ruling 3 (missing and invalid zone), ruling 4 (STALE exact text; HISTORICAL names currentness), M1 fallback (2 inline, 5 behind disclosure), L1 (deferred cost promises; selection switched with a real navigation; the earlier version's PRICED answer arrives late and is never shown, the current one then shows). Each was proved by single-file revert of `SiteFinding.tsx` then `git checkout`: ruling 2 revert -> 4 fail; ruling 3 -> 3 fail; ruling 4 -> 2 fail; fallback `RELATED_INLINE_MAX = 99` -> 1 fail; L1: removing the request-key check AND the `active` flag -> 1 fail. Honest note: the two L1 guards are independent, so removing either one alone still passes (the other covers it). The test's late payload names the current version so the payload version check cannot mask the guard.

**M1 synthetic cap probe** (`.agent/post-W6-W1-a-fix-probe/`, tools in `tools/`, results `out-*/probe-results.json`, screenshots `-synthetic.png`; every output has `synthetic: true`). Method per Architect W3 closeout ruling 1: real mounted page from the s404 `late-stale` producer (Finding with four versions), unmodified screenshot first, then in-session DOM clones; verified flags assert every intended field changed. Heights: closed panel, 1440 / 390; document overflowX 0 and clipped elements 0 in every run.

| Panel (cap 1440/390) | Variant | 1440 | 390 | Result |
|---|---|---|---|---|
| Where to look next (650/1000) | five related rows, real labels | 613 | 821 | pass |
| | five related rows, 160-char labels, inline (pre-fix) | 753 | 986 | over at 1440 |
| | same, behind count disclosure (fixed; opened, exempt: 780/1013) | 614 | 682 | pass |
| What limits (450/800) | five rows cloned from real rows | 357 | 611 | pass |
| | five 160-char rows | 465 | 632 | **over at 1440 by 15 px** |
| Revision history (850/2000) | five real version rows + five 160-char related rows | 728 | 1683 | pass |
| | five version rows with every text field 160 chars + five related | 858 | 2800 | **over at both widths** |
| How each limit is set (400/800) | five 160-char role rows (rows sit in a closed disclosure, closed panel) | 266 | 497-517 | pass |
| | same opened (exempt): 1389-1426 / 3287-3414, no clipping, doc overflow 0, role table scrolls inside itself at 390 | | | readable |

Not fixed, no ruled fallback exists and the ruling says stop: What limits 160-char all-row stress (465 vs 450 at 1440) and Revision history all-field 160-char stress (858 vs 850; 2800 vs 2000). Both pass with real-length text, and the product's rows are generated words, so the stress is a contrived worst case. Measurements returned for an Architect cap/fallback decision.

**Recaptures** (SHA 7cefaca5; `recap/`): Finding overview pairs `open`, `version1`, `late-stale`, `priced`, `priced-current` at 1440 and 390 (heights and caps in `post-W6-W1-a-recapture/index.md` Fix round), all within caps, overflowX 0; priced-current shows the 0.00 to 15.82 USD card, priced shows Not available. A STALE card is not producible by any reviewed producer: covered by the unit test only. All producer DBs dropped; ports 18121-18127, 5183 and 9523 free at the end.

**L4:** index "Capture gaps: none" contradiction fixed (gaps listed with the probe pointer); Finding `open` reclassified as a normal closed state with caps applied (values unchanged); the shared SiteDetails crumb pair was captured (EV charging lab, `Sites > EV charging lab > Overview`, `recap/shared-crumb/`), so mini is not the only reach.

**Checks (final product revision; later commits are docs and capture files only):** targeted `siteFinding.test.tsx` 75/75; full vitest once, 129 files, 3076/3076; `tsc --noEmit` exit 0; `tools/check-all.ps1` 11/11 guards passed. No backend suite run (not requested).
