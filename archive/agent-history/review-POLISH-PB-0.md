# Review: POLISH PB-0 (strict capture gate, review-mode labels, guard 12)

Reviewer: independent Claude reviewer (did not author the slice). Date 2026-11-01.
Branch `task/POLISH-PB-0-capture-gate`, worktree `AssetOpsV1-polB`, head `944f01cdc`. Diff reviewed: `83918ac00...944f01cdc`.
Spec: `.agent/build-sheet-POLISH.md` §2, §3 (Ids rule), §5 PB-0, §7, Addenda 1 and 3.

## Verdict: REVISE

One Medium: the strict gate passes client-visible UUIDs that sit inside existing `data-vocabulary-exempt` markup,
on a captured key (`ev-board-fault`). The rest of the slice is sound and the fix is small. The Lows are packet corrections.

## Findings

### M1. The `[data-vocabulary-exempt]` exclusion hides client-visible UUIDs from the strict gate (acceptance gap)

- Where:
  - `tools/demo-combined-evidence.mjs:146-152` (`FILTERED_TEXT` hides every `[data-vocabulary-exempt]` before the scan);
  - the markup it trusts, for example `frontend/src/sites/EvAssessmentViews.tsx:871` (`REC ${record}`) and `:806` (`F ${finding_id}`);
  - `frontend/src/sites/SiteAction.tsx:1393,1410,1422` (failure/observation codes and a foundation revision UUID, shown outside any disclosure);
  - `frontend/src/sites/ColdAssessmentViews.tsx:237` (assessment revision id).
- What is wrong:
  - The kept-build capture `ev-board-fault-1440.png` shows three full UUIDs in the "What happened on the service day" timeline:
    `REC 685ffc5f-5d95-476c-b074-7c9b65d142ad`, `REC 6841630a-…`, `REC 7b649120-…`.
  - They are not among the 164 baseline hits, because the elements carry `data-vocabulary-exempt="source-reference"`.
  - `captures.json` records 26 excluded regions on `ev-board-fault`, 50 on `kobo-board-S` and 63 on `kobo-verification`.
    The excluded text itself is not recorded, so no reviewer can see what the gate skipped.
- Why it matters:
  - Sheet §3 (line 194) says no UUID or 8-character id is visible outside a "Technical details" disclosure, and that the
    scan skips only that disclosure. §3 row 305 assigns exactly these EV `REC <uuid>` / `F <id>` items to a later slice.
  - With the exclusion as built, the PB-3 and PC strict captures would pass even if those UUIDs stayed visible.
    The gate cannot enforce the rule it exists for, and the baseline undercounts.
  - The dispatch condition "exempt regions cannot be used to hide client-visible developer text" fails today on a captured screen.
  - Some current uses also fall outside the exemption's own definition in `productVocabulary.json` `exemptions.source-reference`
    ("source-owned identifier"): product failure codes, revision ids and finding ids are not source-owned.
- Note: §5 PB-0 (line 450) does list `[data-vocabulary-exempt]` as an exclusion, so the spec conflicts with §3. The implementer followed §5 literally.
- Fix (pick one with the Architect; the first needs no new ruling beyond resolving §3 against §5):
  - keep the product-term exemption for `[data-vocabulary-exempt]` (Lab names, user-owned names), but still run the id
    classes over those regions: `uuid`, `finding id label`, `zero-padded record code`, `enum code` and `raw timestamp`.
    Only `[data-technical-details]` (and closed disclosures, which `innerText` already omits) should hide ids;
  - in addition, record the excluded-region text (or its id-class hits as `excluded`) in `captures.json`;
  - re-run or re-derive the strict baseline and add the EV `REC` UUIDs (3 per width) to the classification, owned by PB-3 (§3 row 305).
  - Fixing the markup itself is PB-2/PB-3 scope and not required here.

### L1. Baseline classification: one frontend hit is filed as awaiting PA-2

- Where: packet "Baseline classification" table, `.agent/POLISH-PB-0-packet.md`, Finding-title row (7 hits).
- What: the Finding-title text accounts for 6 of those 7 hits. They are `candidate`, `candidate avoidable` and `running`
  on `portfolio-week` and `findings-all`. The 7th is `running` on `maintenance-preventive`. Its context is "Scheduled
  maintenance by calendar or running hours", which is frontend copy (`frontend/src/work/GlobalPreventive.tsx:44`, owned by PB-3).
- Effect: the correct split is 21 frontend / 61 awaiting per width, not 20 / 62. The total of 82 per width (164) is unchanged.
- Fix: move it to the frontend PB-3 row.
  - Also note that "Cold replay lab" / "EV charging lab" are classed as awaiting **PA-3**. Addendum 3's wording covers
    PA-1/PA-2 server text. The class is reasonable, because these are server Site names and R646 is PA-3's, but say so explicitly.
  - Two rows are still marked "to confirm". "Generator · Running" looks frontend: `ColdAssessmentViews.tsx:734` passes `"Running"`.
    "critical load" comes from server binding labels (`binding_roles.py`). Resolve both in the packet.

### L2. Deviation 4 is acceptable, but its "no such case today" claim is inaccurate

- Where: `tools/checks/mock-deviation-labels.mjs:24-27` (`stripComments`); packet D4.
- What: `frontend/src/App.tsx:524` has the string `"/maintenance/requests/:caseId/*"`. The lexical stripper treats its
  `/*` as the start of a block comment and blanks code up to the `*/` on line 525. App.tsx has no labels, so the result is unaffected today.
- My probe showed that a label placed between a `"/*"` string and a later `"*/"` string escapes check (a).
- Judgement: acceptable for this slice. Every route to a false pass needs comment markers inside string literals around
  a label. The client-mode full-`<main>` "MOCK DEVIATION" scan in the capture tool is a runtime backstop for visible labels.
- Fix: correct the D4 sentence in the packet. Optionally make the stripper skip string and template literals later.

### L3. Packet residual-risk statement about exclusions is inaccurate

- Where: packet "Residual risk", first bullet.
- What: it says the exclusions are "untested live". `[data-vocabulary-exempt]` is live on 40+ elements and excluded
  26–63 regions per capture in this very baseline. Only `[data-technical-details]` and `[data-time-zone-note]` are not rendered yet.
- The packet also cites "Addendum 2 Q-B" for the capture slot, although the setup followed Addendum 3, which supersedes it.
- Fix: amend with M1.

## Verified as claimed

- **Labels hidden by default for clients:**
  - the `mock-deviation.css:12` rule is the §2 text verbatim;
  - `main.tsx` imports it app-wide, so the `globalWorkParts` `MockDeviation` component (`globalWorkParts.tsx:102-108`)
    is covered, and it carries `data-mock-deviation={id}`;
  - the global import adds only `.mock-deviation-line` styling and the hide rule, so no other product behaviour changes.
- **`reviewLabels.ts`:**
  - `?review=labels` sets the flag in sessionStorage and `?review=off` removes it; any other value reads the stored state;
  - every storage call, including the accessor itself, is inside try/catch, and with no storage the parameter decides;
  - `applyReviewLabels()` runs before `createRoot`.
- **Guard 12:**
  - Registered in `check-all.ps1:66`; 12 `Invoke-Guard` lines.
  - Each condition fails on its own, by my own probes against the exported functions on the real repository inputs:
    - (a) dropping a tag in `operatorSiteTabs.tsx` gives "untagged … :154";
    - (b) an id of `R9999` gives "not a register row";
    - (c) removing the CSS rule gives "the hide rule is missing".
  - It fails closed on unusual JSX: an arrow function in the attributes, or the text in a child of the tagged element.
    That is acceptable.
- **Settle predicate:**
  - "Loading the site's overview." and "Loading…" are not settled; "Loading and door records" is settled.
  - `SETTLE_PROBE` checks `aria-busy` on and inside `<main>` and `[data-repeat-check="loading"]`.
  - The regex is broader than the Addendum 1 M2 form ("Loading <words>." also blocks), but it fails closed and the M2 cases hold.
- **Vocabulary:**
  - terms come from `productVocabulary.json` `terms` (62) and `w1.terms` (17), and `w1.codes` is not used;
  - glosses come only from `glosses` (11) and `w1.glosses` (7), all listed in the packet, and there is no tool-local list;
  - "MOCK DEVIATION" is scanned on the full `<main>` text (`MEASURE` `main.innerText`) for every capture, including `-open`;
  - in client mode a label hit is counted.
- **`DEMOB_STRICT`:** returns 1 when `counted > 0`. The kept-build `captures.json` shows `strict: true`,
  `vocabulary_counted: 164`, 82 per width, and identical counts at 1440 and 390.
- **Register sentence:** `.agent/mock-departure-register.md:212` is the §2 text verbatim. The rest of the paragraph is kept.

## Checks I ran (head `944f01cdc`)

- `node --test tools/checks/test_mock_deviation_labels.mjs`: 5 pass, 0 fail.
- `node --test tools/checks/test_evidence_checks.mjs`: 12 pass, 0 fail.
- `node tools/checks/mock-deviation-labels.mjs`: OK, 151 files.
- `node --check tools/demo-combined-evidence.mjs`: OK.
- `npx.cmd tsc --noEmit` (frontend): exit 0.
- `npx.cmd vitest run src/ui/__tests__/reviewLabels.test.ts src/ui/__tests__/mockDeviationStyle.test.ts`: 2 files,
  11 passed. Vitest did run in this session.
- `tools/check-agent-workflow.ps1`: passed.
- `tools/check-architecture.ps1`:
  - it fails in polB with Rule 8 "no Python interpreter at '' or .venv", because polB has no `.venv`, and that cascades into "vacuous" messages;
  - with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv it passed;
  - this is an environment issue, not the slice. Base `83918ac00` in plan2 passes.
- Guard 12 non-vacuity probes and edge cases: a throwaway script in my scratchpad imported the exported functions. No worktree edits.
- Inspected the implementer's kept-build `captures.json` and the `kobo-verification-1440` and `ev-board-fault-1440` screenshots.

## Not verified

- Full `check-all.ps1` (the estate guard self-tests are slow; I ran the guard 12 and evidence tests and two of the PowerShell guards directly).
- The live strict and review-mode captures. They need serve, Vite and Chrome, which this review was told not to run.
  I relied on the implementer's `captures.json` and PNGs for the 164 count, the 0 client-mode MOCK DEVIATION hits and
  the R453 behaviour at 390 and 1440.
- The full frontend and backend suites. They were not run, and the slice touches no backend code.

## Residual risk not named in the packet

- Beyond M1: `data-vocabulary-exempt="lab"` exempts product terms on Lab entries.
  - Lab names on client screens ("Cold replay lab") are still caught today, because their text is not inside exempt elements.
  - A later slice that wraps Site names in a `lab` exemption would silently clear 19 hits per width.
  - The Architect may want the strict gate to treat `lab` and `source-reference` exemptions as review-visible
    (recorded, not dropped) rather than invisible.

## Re-review (fix round 1)

Reviewer: fresh independent Claude reviewer (did not author the slice or the fix). Date 2026-11-01.
Worktree `AssetOpsV1-polB`, head `f053ab26c`. Diff reviewed: `944f01cdc...f053ab26c` (fix `ba152757d`, packet `f053ab26c`).
Ruling: build sheet Addendum 5.

### Verdict: ACCEPT

M1 is closed per Addendum 5, and L1-L3 are folded. Two new Lows are test-strength notes. They do not block.

### M1: closed

- **Id checks on all visible main text.** `classifyCapture` (`tools/demo-combined-vocabulary.mjs:89-102`) scans `ID_KINDS`
  (UUID, `Finding <8 hex>`, padded code, enum code, raw timestamp, `:14-20`) on `ids`. `CAPTURE_TEXTS` builds `ids`
  as main text with only `[data-technical-details]` hidden (`:119`, `ids:read(TD)`). The check runs the same way for
  `-open`: `open` drops only UTC and the product kinds (`:91`).
- **Exemption scope.**
  - `data-vocabulary-exempt` removes text only from `words`, which feeds the product kinds (`WORD_KINDS` plus the T028/w1 terms).
  - `data-time-zone-note` removes text only from `utc` (UTC kind).
  - MOCK DEVIATION is scanned on `full`, so nothing exempts it. In review mode it is recorded but not counted (`:99`).
  - Behaviour change I confirmed and judge ruled: UTC inside `data-vocabulary-exempt` now counts, because Addendum 5
    lists UTC as exempt only in a time-zone note. Test 3 pins it.
- **`exempt_hits[]` shape.** Each entry is `{kind, match, region: "<attr>=<value>", context}` (`:96`). The recount
  `captures.json` entries have exactly those keys.
- **Equivalence with the old inline scan.**
  - The regexes, the term and gloss sources, the per-kind dedup, the context width and `-open` label handling on full
    main text are unchanged from the removed `VOCAB`/`scan`/`scanClient`.
  - The only behaviour differences are the ruled ones: ids in VX/TZ count, product words in TZ count, UTC in VX counts,
    ids count on `-open`, and exempt hits are recorded.
  - `vocabulary_excluded_regions` was dropped. Nothing in `tools/` reads it.
  - Hit order in `vocabulary[]` changed. That is cosmetic.
- **The 7 region-rule tests can fail.** I mutated a scratch copy of the module 12 ways and ran the 7 tests against each copy:
  - ids scanned on `words` fails test 1;
  - ids scanned on `full` fails test 2;
  - UTC scanned on `words` fails test 3;
  - product kinds scanned on `utc` fails tests 3 and 4;
  - a time-zone note that also exempts ids fails test 4;
  - labels scanned on `ids` fails test 5;
  - review mode counting labels fails test 5;
  - `open` that still counts product kinds fails test 6;
  - `open` that drops ids fails test 6;
  - a region string without its value fails tests 2 and 3;
  - no exempt-hit recording fails tests 2, 3 and 4;
  - removing gloss stripping fails **nothing** (see N1).
- **Live evidence.** I read the implementer's recount `captures.json`. The tool files are identical between `ba152757d`
  and `f053ab26c`; only the packet and CODE_STATE changed.
  - It has `strict: true` and `vocabulary_counted: 692`, which is 346 at each width. All 28 captures settled.
  - On `ev-board-fault` the three `REC <uuid>` timeline items now count as `uuid`.

### Q2: the 10 `data-vocabulary-exempt="lab"` hits on `kobo-board-S-open`

- **Source.** All 10 come from the two Simulator Lab quick actions rendered by `SiteQuickAction` (`frontend/src/sites/SiteDetails.tsx:493,497`).
  They are passed `vocabularyExempt="lab"` at `frontend/src/shell/SiteDetailFrame.tsx:219`, and their text is fixed in
  `frontend/src/shell/simulatorLabRoutes.tsx:521-539`:
  - "Open in Simulator Lab" / "Start Simulation";
  - the two "not available" reasons.
- **Count.** The recorded matches are Simulator x3, run x2, Run, runs, scenarios, scenario and Simulation. That is 10,
  and it agrees with the text.
- **Rule check.** None of them is a Site name, an asset name or a record code. "to this site" is generic.
  - The text is the Lab entry that `productVocabulary.json` `exemptions.lab` defines.
  - The only other `="lab"` use is the nav-rail label (`frontend/src/shell/WorkspaceShellLayout.tsx:67`, the constant
    Simulator Lab entry label). It sits outside `<main>`.
- **Result.** No breach of Addendum 5, and no finding for any slice.

### Q3: L1-L3 folds and the recount classification

- **L1: folded** (packet `:97-113`).
  - Standard captures come to 85 per width: frontend 24 (13 + 4 + 2 + 1 + 1 + 3) and awaiting 61 (10 + 6 + 19 + 5 + 2 + 19).
  - I recomputed the per-kind totals from `captures.json`:
    - uuid 8 (5 portfolio + 3 EV), UTC 13, lab name 12 + replay 7 = 19, running 4, scenario 4;
    - candidate 2, candidate avoidable 2, padded 19, load 2, Finding id 10, draft 2.
    - The sum is 85, and it matches the table.
  - "Generator · Running" and "critical load" are resolved.
  - The Lab-name class is marked PA-3 with the reason given.
- **`-open`.** It comes to 261 per width: 251 uuid, 2 enum, 3 raw timestamps and 5 padded codes. These match `captures.json`.
  - The two enums and three timestamps are disclosure fields such as "Access reference …" and "List built at …".
  - That is consistent with PB-2 tagging them as Technical details.
- **Total.** 85 + 261 = 346, times 2 widths = 692. That is consistent.
- **L2: folded** (D4, packet `:167-172`). The App.tsx `/*` case is stated correctly.
- **L3: folded** (packet `:175-179`). The residual risk is now accurate.
  - The packet no longer cites "Addendum 2 Q-B" (grep finds no match).
  - The setup cites Addendum 3.

### New findings (Low, non-blocking)

- **N1 (Low, test strength).** The gloss test cannot fail when gloss stripping is removed (`tools/checks/test_mock_deviation_labels.mjs:110-114`).
  - Its text is "The generator running hours; maintenance by running hours". The second "running" yields the same
    `kind|match` key, and dedup collapses the two, so the expected list is identical with or without the gloss.
  - Only the `GLOSSES.includes` line can fail.
  - I probed separately: `classifyCapture` on "generator running" returns 0 counted, so stripping does work today.
  - Fix: add an assertion that text containing only "generator running" counts 0. This can ride with any later slice.
- **N2 (Low, residual risk).** The in-page `CAPTURE_TEXTS` selectors (`tools/demo-combined-vocabulary.mjs:104-119`) have no unit test.
  - The 7 tests build `{full, ids, utc, words}` by hand (`test_mock_deviation_labels.mjs:53-61`).
  - Changing `ids:read(TD)` to `read(TD+','+VX)` would bring the reviewed M1 bug back, and every test would still pass.
  - By hand reading the selectors are correct, and the live recount (EV REC UUIDs counted) evidences them on this revision.
  - Fix (optional): a string assertion on the `ids`/`utc`/`words` selectors, or a jsdom test with an `innerText` shim.

### Checks I ran (head `f053ab26c`)

- `node --test tools/checks/test_mock_deviation_labels.mjs`: 12 pass, 0 fail.
- `node --test tools/checks/test_evidence_checks.mjs`: 12 pass, 0 fail.
- `node --check` on `tools/demo-combined-evidence.mjs` and `tools/demo-combined-vocabulary.mjs`: OK.
- `node tools/checks/mock-deviation-labels.mjs`: OK, 151 files.
- The mutation probes on a scratch copy of the module (listed above). No worktree edits.
- A node read of the implementer's recount `captures.json` (`cap-strict2`) for totals, kinds, the exempt-hit shape and
  the lab contexts.

### Not verified

- **tsc and vitest: not rerun.** The fix diff touches no frontend file; the first review ran them with exit 0 and 11 passed.
- **Live captures: not rerun.** That needs serve, Vite and Chrome, which this review was told not to run.
- **Which tool revision produced the recount: not proven by the artifact.** `captures.json` `code` (`79dda4ea0`)
  records the dataset's revision, not the tool's.
  - The `exempt_hits` shape and the 692 count are consistent with `ba152757d`.
- **check-all / check-architecture: not run.** The implementer reports 12/12 at `ba152757d`, and the tool code is
  unchanged since then.
