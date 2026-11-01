# POLISH-PB-0 review packet: strict capture gate, review-mode labels and guard 12

- **Task:** `tasks/POLISH-PB-0-capture-gate.md`.
- **Spec:** `.agent/build-sheet-POLISH.md` §2, §5 PB-0, and Addendum 1 (3.5 units), Addendum 3 (capture setup and
  counting rule) and Addendum 5 (review M1: region rules).
- **Branch:** `task/POLISH-PB-0-capture-gate`; base `83918ac00`.
- **Review status:** USER_REVIEW_REQUIRED: false. Merges on review ACCEPT.
- **Fix round 1** answers `.agent/review-POLISH-PB-0.md`: M1, L1, L2 and L3.

## Outcome delivered

- **P-04 mechanism (Addendum 1 Q1):** client mode hides every `[data-mock-deviation]` with one CSS rule. Review mode
  (`?review=labels`, session-scoped; `?review=off` turns it off) shows the labels.
- **Strict capture gate:** a client-mode capture fails on any client-vocabulary hit.
  - Ids are checked on all visible `<main>` text. Only `[data-technical-details]` hides them (Addendum 5).
  - Exempt-region hits are recorded in `exempt_hits[]`.
- **Guard 12:** fails on an untagged label, an unregistered id or a missing hide rule. Its test file also pins the
  region rules of the vocabulary scan.

## Files materially changed

- `frontend/src/ui/reviewLabels.ts` (new): `applyReviewLabels(search, storage, root)`; every storage call is in try/catch.
- `frontend/src/main.tsx`: imports `ui/mock-deviation.css` app-wide and calls `applyReviewLabels()` before `createRoot`.
- `frontend/src/ui/mock-deviation.css`: the §2 hide rule, verbatim.
- `frontend/src/ui/__tests__/reviewLabels.test.ts` (new, 8 tests) and `mockDeviationStyle.test.ts` (+1 test, `main.tsx` wiring).
- `.agent/mock-departure-register.md`: the first sentence under "Post-W6 audit Architect rulings" is replaced by §2, verbatim.
- `tools/evidence-checks.mjs`: `LOADING_LINE`, `SETTLE_PROBE`, `mainSettled` (OUT-D L1). Tests are in
  `tools/checks/test_evidence_checks.mjs`.
- `tools/demo-combined-vocabulary.mjs` (new, fix M1) holds the pure scan:
  - the kinds: `ID_KINDS`, `UTC_KIND`, `WORD_KINDS`, `LABEL_KIND`, plus the terms and glosses from `productVocabulary.json`;
  - `classifyCapture` (the region rules);
  - `CAPTURE_TEXTS` (the in-page reads).
- `tools/demo-combined-evidence.mjs` adds:
  - `DEMOB_STRICT` and `DEMOB_REVIEW_LABELS`;
  - settle through `mainSettled`;
  - per capture, `vocabulary`, `vocabulary_counted` and `exempt_hits`.
- Guard 12 files:
  - `tools/checks/mock-deviation-labels.mjs`;
  - `tools/checks/test_mock_deviation_labels.mjs` (5 label tests + 7 region-rule tests);
  - the fixtures in `tools/checks/fixtures/mock-deviation-labels/`;
  - the registration in `tools/check-all.ps1`.
- `.ai/CODE_STATE.md` ("POLISH PB-0").

## Acceptance criteria

| Criterion | Status |
|---|---|
| `DEMOB_STRICT=1` exits 1 on any counted hit | Met. Recount: exit 1, 692 hits. |
| Region rules (Addendum 5, correcting §5 PB-0 and Addendum 1): ids (UUID, `Finding <8 hex>`, padded code, enum code, raw timestamp) on all visible `<main>` text, hidden only by `[data-technical-details]`, in the strict and `-open` captures alike; `data-vocabulary-exempt` exempts product kinds only; `data-time-zone-note` exempts only UTC; MOCK DEVIATION never exempt | Met. 7 tests. Live: the 3 EV `REC <uuid>` hits per width now count. |
| `exempt_hits[]` `{kind, match, region, context}` in captures.json, with per-capture counts in the packet | Met. Counts are below. |
| VOCAB additions; T028 + w1 terms from `productVocabulary.json`; `w1.codes` excluded (M3) | Met |
| `DEMOB_REVIEW_LABELS=1` opens `/?review=labels` once | Met (first round). R453 is visible at 390 and hidden at 1440 by its width rule. |
| Settle: no `aria-busy="true"`, no `[data-repeat-check="loading"]`, whole-line loading only (M1/M2 cases tested) | Met |
| Guard 12 (a, b, c) with 4 fixtures, in check-all | Met: 12/12 |
| P-04 mechanism and register sentence (Q1) | Met |
| Strict baseline recorded and classified (Addendum 3) | Met. See below. |

## Checks run (code at `ba152757d`)

- `node --test tools/checks/test_mock_deviation_labels.mjs`: **12 pass, 0 fail**.
- `node --test tools/checks/test_evidence_checks.mjs`: **12 pass, 0 fail**.
- `node --check tools/demo-combined-evidence.mjs`: OK.
- First round, at `29b4171aa`: the frontend is unchanged since then.
  - Scoped vitest (`reviewLabels`, `mockDeviationStyle`): 11 passed.
  - `tsc --noEmit`: exit 0.
- `tools\check-all.ps1 -Python …plan2\.venv\Scripts\python.exe` at `ba152757d`: **All 12 guards passed**. The estate
  guard self-tests took 386 s.
- **Non-vacuity.** Each change was made on the committed tree and reverted with `git checkout --`.
  - Labels:
    - Removing `data-mock-deviation="R436"` fails as "untagged".
    - Changing R452 to R9999 fails as "not a register row".
    - Removing the CSS rule fails as "hide rule missing".
  - The old any-"Loading" regex fails 1 settle test.
  - Fix M1: scanning ids on the exempt-filtered text (the reviewed bug) fails "an id inside data-vocabulary-exempt
    still counts" (11/12).
- Not run: full suites. They are out of scope for a tools and shell slice, and lane A runs in parallel.

## Live captures (Addendum 3 setup)

- **Setup.**
  - `serve` ran from `AssetOpsV1-demo3` on `assetops_demo3_full_test` / `var/demo3_full`.
  - Vite ran from `polB/frontend` with `ASSETOPS_API_PORT=8990`.
  - Each capture started after the first `performance:` line.
  - No manual writes, `prepare` or `add-day`.
- **Process cleanup.** Every process was stopped by PID, and ports 8990 and 5490 were free after each run.
  - First round: serve 18236, Vite 9096.
  - Recount: serve 25828, Vite 32628.
- **Recount, at `ba152757d`.**
  - Run: `DEMOB_STRICT=1 capture …demo3\var\demo3_full <scratch>\cap-strict2`, 409 s; 28/28 captures settled; exit 1.
  - **692 counted hits**: 346 per width, identical at 1440 and 390. Client-mode **MOCK DEVIATION hits: 0**.
  - The first round counted 164. The difference:
    - +3 per width are the EV `REC <uuid>` timeline items, previously hidden by `data-vocabulary-exempt`.
    - +261 per width are ids on the `-open` capture (Addendum 5 applies the id checks there too).

### Baseline classification, per width (Addendum 3 and Addendum 5)

Standard captures, 85 per width:

| Class | Hits | Owner |
|---|---|---|
| `UTC` suffix: "Evidence cutoff … UTC", "(UTC days)", board times (13 screens) | 13 | **Frontend**, PB-1 (D-4; `estateShared.tsx` and others) |
| "Scenario" / "No reviewed scenario" (portfolio, EV board) | 4 | **Frontend**, PB-2 (`EstatePortfolio.tsx`) |
| "draft" / "Draft" (Maintenance preventive) | 2 | **Frontend**, PB-3 (`GlobalPreventive.tsx`) |
| "running hours" (Maintenance preventive) | 1 | **Frontend**, PB-3 (`GlobalPreventive.tsx:44`) |
| "Generator · Running" (cold board, normal night) | 1 | **Frontend**, PB-3 (`ColdAssessmentViews.tsx:734` passes `"Running"`) |
| EV `REC <uuid>` timeline items (`ev-board-fault`) | 3 | **Frontend**, PB-3 (`EvAssessmentViews.tsx:806,871`; §3.1 EV row; Addendum 5) |
| `Finding <8 hex>` labels | 10 | Awaiting PA-2 (labels to titles) |
| Finding-title wording "bounded candidate avoidable running" (candidate, candidate avoidable, running) | 6 | Awaiting PA-2 (Finding titles) |
| Zero-padded codes ACT-, WR-, INC-, PM- | 19 | Awaiting PA-2 (`display_code`) |
| UUIDs in Portfolio finding rows | 5 | Awaiting PA-2 (estate portfolio) |
| "critical load …" (Kobo board) | 2 | Awaiting PA-2. These are server binding labels (`binding_roles.py`), not frontend. |
| "Cold replay lab" / "EV charging lab" (Lab name plus T028 "replay") | 19 | Awaiting **PA-3**: server Site names fixed by PA-3's data change (D-5, R646). Addendum 3 names PA-1/PA-2; PA-3 is the owner here. |
| **Subtotal** | **85** | Frontend 24 (21 from the first round + 3 EV); awaiting 61 |

`kobo-board-S-open`, 261 per width:

| Class | Hits | Owner |
|---|---|---|
| UUIDs (251), enum codes (2: `DEVELOPMENT_TENANT_OPERATOR_CONTEXT`, `LATEST_RECORDED_REVISION_OF_EACH_CANONICAL_FINDING`), raw timestamps (3), all inside opened disclosures not tagged Technical details | 256 | **Frontend**, PB-2 (Technical details tagging, R656) |
| Zero-padded codes (5) | 5 | Awaiting PA-2 (`display_code`) |

The awaiting split follows Addendum 5's 21 / 61 for the first-round classes: 21 + 3 frontend, 61 awaiting.

Not observed in this capture set: `SiteAction.tsx:1393,1410,1422` (PB-2) and `ColdAssessmentViews.tsx:237` (PB-3).
Their screens are not among the 14 keys. Per Addendum 5, their owning slices cover them with the view's vitest
product-vocabulary check.

### Exempt hits per capture (both widths identical)

- Every capture except `kobo-board-S-open` records **0** exempt hits.
- `kobo-board-S-open` records **23** exempt hits, all in `[data-vocabulary-exempt]`:
  - `source-reference`: 12 (claim, PCS ×3, PV ×2, 4 snake_case source names, "UUID", run).
  - `user-owned`: 1 (load).
  - `lab`: 10 (simulator ×3, run ×3, runs, scenarios, simulation, scenario).
- There are no `[data-technical-details]` or `[data-time-zone-note]` regions yet (PB-1/PB-2).
- For the reviewer: the `lab` exemption value appears on the opened Kobo board (Lab entry text). Addendum 5 refuses
  new uses of it on Site names. These are existing uses and are recorded here so a jump is visible.

### Glosses stripped before the product-term scan (only from `productVocabulary.json`)

- **Global `glosses`:**
  - "Scenarios · Not available yet"
  - "Scenarios, Not available yet"
  - "Claim boundary"
  - "Inspect temperature claim"
  - "solar power (PV)"
  - "battery charge (SOC)"
  - "battery power converter (PCS)"
  - "Session identity mapping"
  - "Grid supply + load manager"
  - "Site meter & load manager"
  - "Load manager · Not declared"
- **`w1.glosses`:**
  - "generator ran"
  - "generator running"
  - "generator run time"
  - The other four duplicate the global entries above.
- `screenGlosses` (`cold-scenarios`, `cold-financials`, `cold-assumptions`) match no capture key and are not applied.

## Known deviations

- **D1.** The sheet says `tools/checks/evidence-checks.mjs`; the file is `tools/evidence-checks.mjs` (M1 pre-flight, confirmed).
- **D2.** Scope is 3.5 units with the P-04 mechanism (Addendum 1 Q1).
- **D3.** The region rules follow Addendum 5, not §5 PB-0's flat exclusion list. "MOCK DEVIATION" has its own
  full-text kind. In review mode, label hits are recorded but not counted; other kinds inside a label, such as the
  `R453` id, still count.
- **D4.** Guard 12 strips comments lexically: block comments, and `//` not preceded by `:`.
  - Comment markers inside string literals fool it. `frontend/src/App.tsx:524` has
    `"/maintenance/requests/:caseId/*"`, so the stripper blanks code from that `/*` to the next `*/` (line 525).
  - App.tsx has no labels, so the result is unaffected today.
  - A label placed between such string markers would escape check (a). The capture tool's full-`<main>`
    MOCK DEVIATION scan in client mode is the runtime backstop for any label that renders.
- **D5.** `.ai/ACTIVE_CONTEXT.md` is not updated. Two lanes run in parallel and the coordinator owns routing.

## Residual risk

- **Untested regions.** `[data-vocabulary-exempt]` is live (40+ elements; 23 recorded hits on the open board).
  `[data-technical-details]` and `[data-time-zone-note]` are not rendered yet (PB-1/PB-2), so their branches are
  proven only by the tool tests.
- **Ids in exempt regions.** Ids inside `[data-vocabulary-exempt]` now count. A later slice cannot hide them by
  tagging; only a Technical details disclosure can.
- **Counting rule (Addendum 3).** Hits from server text owned by PA-1/PA-2 are logged as "awaiting PA-x" and do not
  fail a slice; frontend hits do. The Lab-name class awaits PA-3 under the same rule.
- **Ordinary operational copy.** Product terms such as "load" and "running" may be legitimate in places. Any
  allowance must go into `productVocabulary.json` glosses, not the tool.

## User-review focus

None required (USER_REVIEW_REQUIRED: false). The reviewer should check:
- `classifyCapture` region rules;
- the `-open` classification (256 frontend ids for PB-2);
- the `lab` exempt hits.
