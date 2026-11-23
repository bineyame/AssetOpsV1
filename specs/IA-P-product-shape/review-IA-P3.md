# IA-P3 review (P4b, P5, P6, P7): discovery review, round 1

Reviewer: fresh Claude reviewer (did not author the slice). Branch `task/IA-P3-sites-site-inbox`, head `368fdadc4`
(code head `6dbfb3a34`; `368fdadc4` changes only `packet-IA-P3.md`). Judged against spec rev 3 §2.3, §5.2, §5.3, §6 P4b
to P7, §7; rulings D-IAP.35 to D-IAP.47; register R790 to R799; `git diff main...HEAD`.

## Summary (round 1)

- **Verdict: accept with findings fixed on the branch.** H1 blocks the merge. M1 and M2 are fixed on the branch.
- The P4b list, the P5 six tabs and object pages, the D-IAP.39/46 parity proof and the P6 inbox match their spec and
  rulings. The plants the packet lists match the tests I read. The register rows are in place.
- **H1**: the new scope switch offers a group on `/findings` and `/actions`. Those lists then say "No Findings in this
  range." / "No Actions in this range." with tiles at 0, under a raw enum chip ("COLDCHAIN"). That is a false statement
  (packet §9.4 names the cause; §9.5 Q1).
- **M1**: on `/incidents`, `/maintenance` and `/financials` a group scope is written and the button shows it, but the
  page shows every Site and no chip says so. This is the same class D-IAP.40 rules on.
- **M2**: Outcomes L2 leaves out the directory Sites that E1 lacks, so its rows are not the Sites list rows. This is an
  implementer choice that was not raised, and a test pins it.
- 4 Low. Checks: guards pass, the 11 focused vitest files pass (201 tests), tsc is clean. I did not rerun the full
  suites, Postgres or the gates (see "Checks").

## Findings

### High

**H1. A group scope on Findings and Actions shows a false empty list.** (acceptance gap: spec §5.3 "honest numbers",
D-IAP.40 Q23 "every surface drawn by `HomeList` applies the address `scope`")
- Where:
  - `frontend/src/ui/homeListModel.ts:78`: `inScope` returns false for every row of a def without `domain`.
  - `frontend/src/estate/homeLists.tsx:212-213` (`findingsDef`) and `:278-279` (`actionsDef`): `site` but no `domain`.
    Their `scopeWord` prints the raw scope value.
  - `frontend/src/shell/ScopeSwitch.tsx:46` and `:62-72`: the switch offers every domain present and writes
    `scope=group:{DOMAIN}` on `/findings` and `/actions`.
- What happens: `ns` is 0, so `HomeList` renders `def.none` ("No Findings in this range.", "No Actions in this
  range."). The tiles show 0, and the chip reads "COLDCHAIN" (system vocabulary). This happens for a domain that has
  Findings or Actions in the range.
- Why it matters:
  - The page states a falsehood to an operator executive, one click from a top-bar control, on two of the four home
    lists.
  - Before P7 no control wrote a group scope on these lists, so P7 brings the defect in.
  - The packet discloses it (§9.4) but ships it.
- Fix (Architect, Q1 below; my default):
  - Give `findingsDef` and `actionsDef` a `domain` from the Site directory, joined on `site_code`. Use the
    `EstateClientProvider` directory, read only while the scope is a group (P7 already reads it on demand).
  - Give them the `scopeWord` that `decisionsDef` and `sitesDef` use (`DOMAIN_WORD`).
  - While the directory is loading or refused, a group scope shows the list's loading state or the refusal sentence,
    never `def.none`.
  - Tests first: one `/findings?scope=group:COLDCHAIN` and one `/actions?scope=group:…` case that holds rows. Plant:
    drop `domain`, and both must fail.
  - Sweep (W6): every `HomeListDef` with `site` and no `domain`. `grep -n "site: (" frontend/src/estate/*.tsx` finds
    four defs; two lack `domain`.

### Medium

**M1. Group scope on estate pages that show every Site, with no chip.** (acceptance gap against D-IAP.40's stated
class, "every page that keeps a non-all `scope` in the address but shows every Site carries the chip")
- Where: `frontend/src/shell/ScopeSwitch.tsx:32` (`EVERY_SITE_PAGES` lists only the five named pages) and `:62-72`.
  The switch is drawn on every operator page (`OperatorShellLayout.tsx`).
- What happens: on `/incidents`, `/maintenance`, `/maintenance/preventive` and `/financials`, choosing "Cold-chain"
  writes `scope=group:COLDCHAIN`. The button then reads "Cold-chain ▾", but the page lists every Site's records and no
  chip says so. None of these pages reads `scope` (`grep -rn '"scope"' frontend/src` finds no reader outside the
  list, Outcomes and shell code).
- Why it matters: the control claims the view is narrowed when it is not. It is the case MD-IAP-5 exists for, missed
  because the ruling names its pages one by one.
- Fix (class, not instance): turn the test around. The chip shows on every operator page that is neither a `HomeList`
  list (`LIST_PATHS`) nor a Site page (`/sites/{code}…`), while the scope is not all. Extend R798 to name these pages.
  Add one `scopeSwitch` case for `/incidents`. If the Architect prefers to keep the five-page list, the alternative is
  to offer no group entries on such pages; I default to the chip (Q3).

**M2. Outcomes L2 leaves out the directory Sites that E1 lacks.** (acceptance gap: §6 P4b test "the Outcomes rows = the
Sites list rows", D-IAP.35 Q1's reason "a Site never leaves a page")
- Where:
  - `frontend/src/estate/sitesList.tsx:291`: `siteItems(body, waitingBySite)`, with no directory. The directory is read
    one line up, but only for lifecycle words.
  - `frontend/src/estate/__tests__/sitesList.test.tsx:325` pins "L2 gains no directory-only row".
- What happens: with a Lab-created or legacy Site in the directory, `/sites` lists N+1 rows and Outcomes L2 lists N.
  L2's "Show all {n}" names a count that the page it links to does not show. The parity test at
  `sitesList.test.tsx:336` passes only because its default directory holds no extra Site.
- Why it matters: §6 P4b says one def draws both surfaces, with equal rows. Dropping a known Site from Outcomes is the
  case D-IAP.35 Q1 ruled against. The choice was not raised (`.ai/RULES.md` §7: an implementer choice the spec did not
  fix is raised, not decided).
- Fix: pass `listed` to `siteItems` in `OutcomesSites`. Flip test 325 so the directory-only row follows E1's rows on
  both surfaces. Add a directory-only Site to the "Outcomes rows are the Sites list rows" case.

### Low

**L1. `/results` reads page 1 outside the shared cache, so the request goes out twice with the shell** (packet §9.4,
§9.5 Q2). `frontend/src/estate/Results.tsx:30`. Fix: `useEstateRead(reads, "portfolio", window)`, as P7 did for the
Portfolio tabs (`EstatePortfolio.tsx`). Re-pin the `sr2RequestUrls` `/results` row if it counts the request.

**L2. The COLD and EV Evidence line is "Records · Analysis · Uploads"; spec §2.3 says "In Evidence: Records · Uploads".**
- Where: `frontend/src/sites/coldSiteViews.tsx:441-445` and `frontend/src/sites/EvSiteViews.tsx:421-425`.
- Merging the existing Analysis sub-tab into the line keeps content, which is right. But the departure from §2.3's line
  is in neither the register nor packet §10.
- Fix: add a D2 register row, or list it in §10 for the Architect to accept.

**L3. R328 is stale.** `.agent/mock-departure-register.md:431` still describes the mini Finding crumb as `Findings ›
Finding`, to become `Findings › {code} › Alternatives`. P5 replaced that crumb with the object-page trail
`{Decisions|Findings} › {Site} › {title}` (D-IAP.38 Q20) and removed `FINDING_CRUMB`. Fix: restate R328's closure
condition against the new trail, or close it, citing D-IAP.38. Check: `grep -n "Findings › {code}"`.

**L4. The site scope compares Site codes case-sensitively, while the Sites list treats Site identity as case-blind.**
`frontend/src/ui/homeListModel.ts:77` and `frontend/src/shell/ScopeSwitch.tsx:56` use `===`, while
`frontend/src/estate/sitesList.tsx:58` uses `site_id_key`. The scope entries come from the directory's `site_id`, and
the rows match on the estate's `site_code`. No fixture differs in case today. Fix (optional): compare case-blind in
`inScope` and `scopeWord`.

## Checked and found as claimed (no finding)

- **P4b**:
  - `sitesDef` columns, facets, sorts and tiles follow §5.2. R6 shows the gap tile only for the whole unfiltered list.
    The More line has two strings (D-IAP.35 Q5).
  - Directory rows follow E1's rows, with Group from `DOMAIN_WORD` and E0 waiting (D-IAP.35 Q1). The lifecycle word is
    the title's `<small>`, with plant `nolife` (D-IAP.44).
  - `SitesIndex` is deleted (D-IAP.45). `/sites` is in `RANGE_PAGES` and `FILLED_PAGES`. Outcomes L1/L2/L3 order and
    the "Each Site's objectives" disclosure are in place.
- **P5**:
  - There are six tabs, and `SITE_TAB_OF` maps the old labels.
  - Object pages draw no tab row and use a three-part `ui/Breadcrumbs` trail (home list chosen by view). R383 is closed.
  - The COLD/EV alias in `SiteFindingsFrame` keeps `from`, `to` and `known_at`. MINI keeps its index under Evidence
    (D-IAP.42, R796).
  - The parity server layer asserts a non-empty subset, the cap, the MINI flip and the D-IAP.46 projection, with no
    xfail. The client layer runs the pinned bodies through `findingItems` and then `homeListModel` at
    `site:{code}`, with plant `parity`.
  - The "Change & effect" removal is R797. The 41 + 19 + 27 + 27 migrated tests are each classed; I read the
    retirements the packet asks about and agree with the (b) calls.
- **P6**:
  - One function (`waitingForAChoice` / `waitingTotalOf`) feeds both the tile and the badge.
  - The rows come only through `decisionItems` on the shared cache key, and the cache key holds only
    `from`/`to`/`known_at`, so a page's `state` or `cursor` cannot change the badge.
  - The drawer has a dialog role, focus to Close, and Escape and the scrim close it.
  - `Drawer` was moved unchanged.
- **P7**:
  - The top-bar order is Scope · Search · range · Waiting for you.
  - The palette indexes only live targets and is capped at 20, with words ANDed.
  - Ctrl K toggles it and focus returns.
  - The walk pages grew from 10 to 14.
  - The Portfolio tabs now read page 1 from the shared cache (§8.4's double read is gone).
- **Dark mode**: "panels draw light in dark" is not new. `ui/tokens.css` defines `--surface-raised` (and the other
  surfaces) only once, with no dark block, so the whole app renders light in dark (the builder's `p7` dark shots show
  it). This is not a finding against IA-P3. It is listed as residual risk.

## Checks

Run by me at `368fdadc4`, from the worktree:

| Check | Result |
| --- | --- |
| `ASSETOPS_GUARD_PYTHON=… pwsh -NoProfile -File tools/check-architecture.ps1` | "Architecture check passed." |
| `pwsh -NoProfile -File tools/check-agent-workflow.ps1` | "Agent workflow check passed." |
| `tools/checks/statement_catalogue.py` | exit 0 |
| `heavy-slot.sh -- npx vitest run` on `sitesList`, `siteTypeMatrix`, `outcomesOneRead`, `siteFindingsParity`, `homeLists`, `scopeSwitch`, `searchPalette`, `waitingForYou`, `siteFindingsAlias`, `siteObjectPages`, `operatorSiteTabs` | 11 files, 201 passed |
| `npx tsc --noEmit` (same slot) | clean |

Cited from the builder, not rerun (no finding needs a rerun):
- vitest `src/estate src/shell src/ui src/sites` at `6dbfb3a34`: 10 failed / 4148 passed
  (`/opt/assetecon/evidence/IA-P/IA-P3/p7/vitest-head.log`), all in main `12e618be3`'s set of 12. The revision checks
  out, because `368fdadc4` differs only in the packet.
- `test_iap_*`: 88 passed. Walk tests: 103.
- `iap_gates.cjs`: 64/64 (`p7/gates.log`).
- The plants as listed.

Could not verify:
- The backend parity layer on Postgres and the gates in a browser (not rerun).
- The vNEXT/v70 mock elements for the scope menu and palette beyond the builder's shots (spot-checked
  `p7-search-1440x900-dark`, `p7-scope-390x844-light` and `p6-inbox-390x844-light`).

## Residual risk the packet does not name

- **The shell now runs the full all-pages estate portfolio read (up to 20 × 50 rows) on every operator page**,
  including every Site page, to draw the badge. On the demo DB this is a new load on pages that never read it before.
  Watch it in the demo walk.
- **The app has no dark tokens** (see above). "Clean in light and dark" (§5.3) holds only in the sense that dark
  renders as light.
- **The Overview and Outcomes show "This page shows every Site" while their Decisions rows and L2 follow the scope.**
  The ruling accepts this, but the owner may find the chip contradicts the rows under it. Show it in the walkthrough.

## Questions for the Architect

1. **(§9.5 Q1; H1, BLOCKER for the merge)** What does a group scope mean on `/findings` and `/actions`?
   - Default: their defs take `domain` from the Site directory joined on `site_code` (the provider's directory, read
     only while the scope is a group), with `DOMAIN_WORD` as the chip word.
   - Not "ignore the scope". That would show every Site under a "Cold-chain ▾" button.
   - Not a served field. IA-P3 changes no backend (§11).
2. **(§9.5 Q2; L1)** Should `/results` fold its page-1 read into the shared cache? Default: yes, as P7 did for the
   Portfolio tabs.
3. **(M1; widens D-IAP.40's page list)** Does the chip go on every operator page that is neither a `HomeList` list nor a
   Site page (Incidents, Maintenance, Financials included)? Default: yes, as a class rule in `EverySiteChip`, with R798
   extended to name them.

## Re-review (fix round 1)

Head a17981bdc. Verification re-review (W5) of H1, M1, M2 and the Lows, plus the full estate/shell/ui/sites vitest.

- **Verdict: ACCEPT with one new Medium (N1) to fix on the branch.** H1, M1, M2, L1 to L4 are closed.
- **H1**: `findingsDef` and `actionsDef` take `domainOf` from `useSiteDomains` (directory read only while the scope is a
  group, case-blind join); loading and a refused directory have their own states, never `def.none`. Shot at
  `/findings?scope=group:COLDCHAIN` (fixture, built dist at head): 2 rows (Cold Room), chip "Cold-chain", no "COLDCHAIN",
  no false "No Findings" (`rr1/h1-findings.png`). `/actions` same scope says "No Actions" because the fixture holds only
  KOBO-001 actions; that empty is true (the row case is unit-tested).
- **M1** (`ScopeSwitch.tsx` chip class: not a list and not a Site page), **M2** (directory rows reach `siteItems`),
  **L1** (`/results` through `useEstateRead`), **L4** (case-blind), **L2/L3** (R800, R328): read in the diff, as the packet says.
- **Checks I ran**: full `src/estate src/shell src/ui src/sites` at head: 190 files, 10 failed / 4155 passed
  (`/opt/assetecon/evidence/IA-P/IA-P3/rr1/full.log`); `tsc --noEmit` clean. Failures: siteRangeMatrix 2 (on main too,
  rerun on main 83a5e577d gives the same 2), sr2RequestUrls, domainActionVerification, evActionFixRound,
  evSiteMoneyRoutes 2, siteWorkCases (the packet's main set), siteRangeMatrix `ev / (R)` (flaky: passes on rerun), and **N1**.
  Builder's full run at head was 14 / 4151 (it did not rerun in full after its 3 test fixes); mine is 10 / 4155. Main as the
  builder measured it (12e618be3): 12 / 4081.

**N1 (Medium, acceptance gap: packet §11 says every remaining failure is main's set).** `src/shell/__tests__/simulatorLabGate.test.tsx`
"offers no way to create a site from the operator route /" fails at head and at ee220fd55, and passes on main (83a5e577d).
At `/`, with the estate unstubbed, the page draws a `<button class="dd-button">Try again</button>` that the test's
selector (`button:not([data-shared-range-button]):not([data-shell-control])`) counts. It is a P6/P4b test-migration miss
(the round-1 review ran 11 files and the builder's list omitted it). Fix: stub the estate read for that route or mark
the refusal button as not a create path, as P6 did for `data-shell-control`; the test must pass at `/` and `/sites`.
Not caused by this fix round; it is not a product defect found, only a red test the branch owns.

Not verified: the Postgres-backed `test_iap_*` and `iap_gates` runs (cited from the packet, not rerun); main's full count
(cited, not rerun). Residual risk: unchanged from round 1.
