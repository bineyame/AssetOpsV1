# POLISH-PB-0 review packet: strict capture gate, review-mode labels and guard 12

Task: `tasks/POLISH-PB-0-capture-gate.md`. Spec: `.agent/build-sheet-POLISH.md` §2, §5 PB-0, and Addendum 1 (3.5 units)
and Addendum 2 Q-B. Branch `task/POLISH-PB-0-capture-gate`; base `83918ac00`. USER_REVIEW_REQUIRED: false. This slice
merges on review ACCEPT.

## Outcome delivered

- **P-04 mechanism (Addendum 1 Q1):** client mode hides every `[data-mock-deviation]` with one CSS rule. Review mode
  (`?review=labels`, session-scoped; `?review=off` turns it off) shows the labels.
- **Strict capture gate:** a client-mode capture now fails on any client-vocabulary hit.
- **Guard 12:** fails on an untagged label, an unregistered id, or a missing hide rule.

## Files materially changed

- `frontend/src/ui/reviewLabels.ts` (new). `applyReviewLabels(search, storage, root)`; every storage call is wrapped
  in try/catch.
- `frontend/src/main.tsx`: imports `ui/mock-deviation.css` app-wide and calls `applyReviewLabels()` before `createRoot`.
- `frontend/src/ui/mock-deviation.css`: the §2 hide rule, verbatim.
- `frontend/src/ui/__tests__/reviewLabels.test.ts` (new, 8 tests). Covers param on/off/other, session persistence,
  storage methods failing, the storage accessor throwing, the dataset attribute, and the CSS rule. The CSS is read
  from disk because vitest serves `?raw` CSS as empty text.
- `frontend/src/ui/__tests__/mockDeviationStyle.test.ts`: adds a test that `main.tsx` imports the CSS and applies
  review mode before `createRoot`.
- `.agent/mock-departure-register.md`: the first sentence under "Post-W6 audit Architect rulings" is replaced by the
  §2 text, verbatim.
- `tools/evidence-checks.mjs`: `LOADING_LINE`, `SETTLE_PROBE`, `mainSettled` (OUT-D L1, M1/M2).
- `tools/checks/test_evidence_checks.mjs`: 2 settle tests, including the 3 Addendum 1 M2 cases.
- `tools/demo-combined-evidence.mjs`, PB-0 work items:
  - `DEMOB_STRICT`;
  - `DEMOB_REVIEW_LABELS`;
  - the VOCAB additions;
  - the product terms;
  - the exclusions;
  - the `-open` rule;
  - settle through `mainSettled`;
  - `vocabulary_counted` per capture and in total.
- `tools/checks/mock-deviation-labels.mjs` and `test_mock_deviation_labels.mjs` (new), with
  `tools/checks/fixtures/mock-deviation-labels/`: pass, untagged, unknown-id, register, hide-rule and no-hide-rule.
- `tools/check-all.ps1`: guard 12 "Mock deviation labels and client vocabulary".
- `.ai/CODE_STATE.md` ("POLISH PB-0").

## Acceptance criteria (sheet §5 PB-0, §2, Addendum 1)

| Criterion | Status |
|---|---|
| Strict gate `DEMOB_STRICT=1` exits 1 on any counted hit. Exclusions are `[data-technical-details]`, `[data-time-zone-note]` and `[data-vocabulary-exempt]`. The `-open` capture counts only "MOCK DEVIATION". | Met. Live run: exit 1 with 164 hits. The `-open` capture counted 0. |
| VOCAB: `PM\|REC` added and `-0{3,}` required; `\bUTC\b`, `Finding <8 hex>`, `(replay\|charging) lab`i and snake_case added | Met. Regex sanity: `ACT-001` passes; `ACT-000001`, `PM-0001` and `REC-0002` hit. |
| T028 and w1 terms come from `productVocabulary.json`, word-bounded and case-insensitive. `w1.codes` are excluded (M3). | Met (62 T028 + 17 w1 terms) |
| `DEMOB_REVIEW_LABELS=1` opens `/?review=labels` once per tab | Met. Live: `review labels on`. R453 is visible at 390 (+21 px page height) and hidden at 1440 by its width rule. |
| Settle waits for no `[data-repeat-check="loading"]` and no `[aria-busy="true"]` in `<main>` | Met. The repeat-check wait is inert until PB-3, as expected. |
| OUT-D L1/M1/M2: whole-line `LOADING_LINE` and `mainSettled` in `tools/evidence-checks.mjs`, tested, used by `settle()` | Met. Tested: "Loading the site's overview." and "Loading…" are not settled; "Loading and door records" is settled. |
| Guard 12 (a, b, c) with 4 fixtures, in check-all | Met. check-all: **All 12 guards passed.** |
| P-04 mechanism (Q1): CSS rule, `reviewLabels.ts` with its vitest, `main.tsx` first call and app-wide CSS, register sentence verbatim | Met |
| `node --check` on the tool | Met |
| Strict run against the kept build is expected to fail, with its count recorded as the baseline | Met: 164. The baseline and its classification are below. |

## Checks run (revision 29b4171aa; packet and CODE_STATE added after)

- `npx vitest run src/ui/__tests__/reviewLabels.test.ts src/ui/__tests__/mockDeviationStyle.test.ts`: 2 files, **11 passed**.
- `npx tsc --noEmit`: exit 0.
- `node --test tools/checks/test_mock_deviation_labels.mjs`: **5 pass, 0 fail**.
- `node --test tools/checks/test_evidence_checks.mjs`: **12 pass, 0 fail**.
- `node --check tools/demo-combined-evidence.mjs`: OK.
- `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`: **All 12 guards passed.**
  The estate guard self-tests took 367 s because lane A was running in parallel.
- **Non-vacuity**, each run on the committed tree and reverted with `git checkout --`:
  - Removing `data-mock-deviation="R436"` (ColdAssessmentViews) fails with `:1287: untagged MOCK DEVIATION label`.
  - `R452` changed to `R9999` fails with `not a register row`.
  - Deleting the CSS hide rule fails with `the hide rule is missing`.
  - Changing `LOADING_LINE` to an any-"Loading" form fails 1 settle test (11/12).
- The repository scan is non-empty: 151 tsx files, ≥10 of them with tagged labels.
- Not run: full frontend and backend suites. They are out of scope for a tools and shell slice, and lane A was running.

## Live captures (Addendum 2 Q-B slot; Addendum 3 setup)

- **Setup.** `serve` ran from `AssetOpsV1-demo3` (PID 18236) against `assetops_demo3_full_test` with
  `var/demo3_full`. Vite ran from `polB/frontend` (PID 9096, `ASSETOPS_API_PORT=8990`).
  - The first `performance:` line appeared before capture.
  - Both processes were stopped by PID. Ports 8990 and 5490 were free afterwards, and the slot was released.
  - An earlier serve from polB was refused by `Demo.__init__` (work dir outside polB's var) and exited without
    running a tick.
  - No manual writes, `prepare` or `add-day`.
- **Strict client mode:** `DEMOB_STRICT=1 capture …demo3\var\demo3_full <scratch>\cap-strict`.
  - 409 s wall time; 28/28 captures settled; exit 1.
  - **164 counted hits**: 82 per width, the same at 1440 and 390.
  - **MOCK DEVIATION hits: 0** in client mode.
- **Review mode:** `DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=kobo-board-S,cold-board-failure`.
  - Exit 0 (not strict). `review labels on`.
  - "MOCK DEVIATION D2 (R453)" was recorded at 390 only.

### Baseline classification (Addendum 3 rule; counts are per width, x2 for both widths)

| Class | Hits | Owner |
|---|---|---|
| `UTC` suffix: "Evidence cutoff … UTC", "(UTC days)", times on boards (13 screens) | 13 | **Frontend**, PB-1 time consolidation (D-4). `estateShared.tsx` and others. |
| "Scenario" / "No reviewed scenario" (portfolio, EV board) | 4 | **Frontend**, PB-2 copy (`EstatePortfolio.tsx`) |
| "draft" / "Draft" (Maintenance preventive) | 2 | **Frontend**, PB-3 (`GlobalPreventive.tsx`) |
| "Generator · Running" (cold board, normal night) | 1 | **Frontend**, PB-2/PB-3. Origin to confirm. |
| `Finding <8 hex>` labels (findings lists, WR overview) | 10 | Awaiting PA-2 (Finding labels replaced by titles) |
| Finding title "bounded candidate avoidable running" (`finding_episode.py`/`dispatch.py`) | 7 | Awaiting PA-2 (Finding titles) |
| Zero-padded codes ACT-, WR-, INC-, PM- (boards, lists, WR overview) | 19 | Awaiting PA-2 (`display_code`). Codes rendered by frontend lists are confirmed in PB-3. |
| UUIDs in Portfolio finding rows | 5 | Awaiting PA-2 (estate portfolio) / PB-2 technical-details disclosure (R656) |
| "critical load …" signal labels (Kobo board) | 2 | Awaiting PA-2 asset-label rule (server config labels in `binding_roles.py`). To confirm. |
| "Cold replay lab" / "EV charging lab" (lab name plus T028 "replay") | 19 | Awaiting PA-3 (D-5 Lab Site names) |
| **Total per width** | **82** | Frontend 20; awaiting PA-x 62 |

These hits are not this slice's to fix (Addendum 3). Every frontend-owned hit sits on a string that PB-1, PB-2 or
PB-3 owns.

### Glosses stripped before the product-term scan (Addendum 1 M3; only from `productVocabulary.json`)

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
  - "Session identity mapping"
  - "Grid supply + load manager"
  - "Site meter & load manager"
  - "Load manager · Not declared"
- `screenGlosses` (keyed `cold-scenarios`, `cold-financials`, `cold-assumptions`) match no capture key, so they are not applied.

## Known deviations

- **D1.** The sheet says `tools/checks/evidence-checks.mjs`; the file is `tools/evidence-checks.mjs` (M1, confirmed).
- **D2.** The PB-0 scope grew to 3.5 units with the P-04 mechanism (Addendum 1 Q1).
- **D3.** The vocabulary is recorded on the filtered text: the exempt regions are hidden for one `innerText` read,
  then restored. Before this slice it was recorded on the full text.
  - "MOCK DEVIATION" moved out of the "dev term" regex into its own full-text scan.
  - In review mode, label hits are recorded but not counted. Other hits inside a label (the `R453` id) still count.
- **D4.** Comment stripping in guard 12 is lexical: block comments, and `//` not preceded by `:`. A `/*` inside a
  string literal could hide code from the scan. There is no such case in `frontend/src` today.
- **D5.** `.ai/ACTIVE_CONTEXT.md` is not updated. Two lanes run in parallel and the coordinator owns routing.

## Residual risk

- `[data-technical-details]` and `[data-time-zone-note]` are not rendered yet (PB-1/PB-2), so the exclusions are
  untested live. The per-capture `vocabulary_excluded_regions` count is in captures.json.
- The baseline includes product terms ("load", "running") that ordinary operational copy may legitimately use. Any
  new allowance must go into `productVocabulary.json` glosses, not the tool.

## User-review focus

None required (USER_REVIEW_REQUIRED: false). The reviewer should check:
- the guard 12 scan rules (`tools/checks/mock-deviation-labels.mjs`);
- the whole-line loading regex;
- the baseline classification.
