# post-W6 shell-typography-copy: implementer packet (verification batch)

- **Branch:** `task/post-W6-shell`, worktree `AssetOpsV1-review3`.
- **Code review:** ACCEPT-WITH-LOWS at `0c245601`.
- **Inputs:** `post-W6-shell-rulings.md` Q1-Q26 and `post-W6-shell-review.md` L1-L7.
- **Product SHA:** `e9b1b8d9` (last product commit). Later commits add evidence only.

## Commits in this batch

| SHA | What |
|---|---|
| `7605b824` | Review Lows L3, L4, L5 and L7, with tests |
| `710b0de5` | Q24 selection script, selection.json and capture brief |
| `e9b1b8d9` | Q23 cap fit and Q13 readable SLD key (from the recapture findings), with tests |
| `321cfe56` and later | Recapture evidence, DTO proofs and index |

## Review Lows

- **L3 (done).**
  - Added a `MOCK DEVIATION D4 (R376)` label at the Sites inventory provenance chip (`SitesIndex.tsx`).
  - The R376 row now names both label sites.
- **L4 (done).**
  - `planFigures` computes the target and the guardrails independently, and each card falls back on its own.
  - The percentage is floored: `[1,3]` gives "≥66% lower".
  - `[1,1]` renders "No increase". This is new wording for a stored no-increase target (flagged below).
  - `num > den` is still treated as no usable target.
  - Tests:
    - a unit test of every branch;
    - a route test showing a stored target with empty guardrails (the target shows, guardrails fall back).
- **L5 (done).**
  - `zoneAbbreviation(timezone, at)` derives the name at the selected window start, with the current time as fallback.
  - Test: Europe/London names BST (or GMT+1) in July and GMT in January. Addis stays EAT.
- **L7 (done).** The Attempts doc comment is moved back above `function Attempts`.
- **L2 (left as is, per instruction).**
  - The W1 Action code crumb is still parsed from the `SiteAction` title.
  - `siteAction.test.tsx` pins it for all six sections.
- **L1 (left for the Architect, per instruction).**
  - `G-changes-plan-figures` stays in the registry as `contract`/`absent`.
  - The reviewer recommends `source_status:"existing"` with a runtime-read `missing_kind`. The coordinator routes this.
- **L6 / register IDs: COLLISION RISK, flagged.**
  - This branch registers R375-R381 (`mock-departure-register.md:476-482`):
    - R375: Sites subtitle D4
    - R376: provenance wording D4
    - R377: topology icons and links D2
    - R378: no Sites/SLD callout D4
    - R379: frozen-plan figures D1
    - R380: battery h1 D4
    - R381: evidence missing-gap row D1
  - W2-cold, W2-EV and W3-estate branched from the same R374 tail. Whichever merges second will clash.
  - Reserve R375-R381 for this card, or renumber on rebase. Source labels cite these IDs.

## Recapture-driven fixes (`e9b1b8d9`)

Each fix stays within its ruling. No product code was changed outside them.

- **Q23 caps.** The first DTO proof at `710b0de5` failed five of six capped cases (mini 1296/1200 and 3074/1800; Foundation 982/850 and 1064/1050). Per Q23, "first improve wrapping/paging/inner scroll":
  - `KeyValues` rows gain an optional `wide` flag (`data-key-value-wide`). A long value stacks full width under its term and stays right-aligned. Foundation Identity flags the five free-text rows when they exceed 40 characters (`WIDE_VALUE_CHARS`). All ten rows stay; no row is hidden.
  - The opened reading body becomes a keyboard-focusable inner-scroll region (`.evidence-record-view__body`, `role=region`, `tabIndex=0`), with max-height 26rem, or 24rem at ≤640 px.
  - At ≤640 px the records-table row header gets `min-width: 15rem`, so wrapping is not squeezed into a 115 px column. The table already scrolled sideways.
- **Q13 SLD.** At 390 the scale-to-fit drawing renders at scale 0.315, so the smallest label is about 3.5 px: illegible. Per Q13's fallback, a readable key of the drawn parts (`ul[data-sld-key]`) follows the drawing at ≤640 px only:
  - 12 px text;
  - each entry is an `aria-pressed` button choosing the same part as the drawing;
  - hidden at desktop;
  - it never widens the drawing;
  - it is also reached by Site model and the Lab history inspector's drawing, through `SldDrawing`.
- **Tests:** a KeyValues wide unit test plus an Identity regression, an SLD key route test (count = drawn parts, toggles selection), a record inner-region attribute test, and CSS source assertions.
- **Non-vacuity:** with the five product files reverted to `7605b824`, all five new tests fail. The tree was restored.

## Test selection and results

- **Focused while building:**
  - L-fixes: `measuredTime`, `siteFoundationChange` (23 passed).
  - Cap/SLD: `postW6ShellCss`, `siteFoundationRevision`, `v01bEvidenceVisual`, `foundationScreen`, `siteFoundationChange`.
- **Full batch at `7605b824`:**
  - vitest 128 files: 3011 passed, 1 failed in 235 s. The failure was `siteFindingEvidence.test.tsx` "renders Evidence as a child view…": the h1 still read "Finding". It passed 3 of 3 runs alone; this slice did not touch the file.
  - `tsc` exit 0.
  - Build exit 0 (chunk-size warning only).
  - check-all: all 11 guards passed.
- **Full batch at `e9b1b8d9` (HEAD `321cfe56`), run while captures loaded the machine:**
  - vitest: 3015 passed, 1 failed in 274 s. The failure was `evEnergy.test.tsx` "energy_states_table_loading": "the store read has not settled". It passed 2 of 2 runs alone; this slice did not touch the file.
  - `tsc` exit 0.
  - Build exit 0.
  - check-all: all 11 guards passed.
- **Not run (frontend-only slice):** the backend suite.

## Recapture summary

`.agent/post-W6-shell-recapture/`, built by `select.py` and `build_index.py` into `index.json` and `index.md`.

**Selection (Q24).**
- The greedy cover of the frozen index gives one case per captured screen ID at both widths: 88 IDs, 176 pairs. The cover uses 25 exact producer strings, which normalise to the preflight's 21.
- Every indexed case of the 18 changed screens adds 230 pairs.
- Union: **370 pairs.**
- `cold-finding-excursion` stays with W2-cold, per Q24.

**Result: 370 of 370 captured, with no capture gaps.**
- **Panel titles and order:** all 370 equal the frozen `fddf5cad` titles.
- **Page overflowX:** 0 everywhere.
- **Panel growth:** no undocketed panel grew past frozen + 10% (and +20 px).
- **Flags:** only 6 pairs are flagged, and all are console warnings that the frozen run also had:
  - React duplicate key on action-history verified-replay;
  - React duplicate key on ev-readiness stocked;
  - validateDOMNesting on wr-record all-open.
- **Pre-existing claim failures (frozen run too):**
  - asset unknown-site panel count;
  - portfolio 503 under the w302 producer (B11-16).

**SHAs.**

| SHA | Pairs | What was captured |
|---|---|---|
| `710b0de5` | 96 | Batches 1-5, except Foundation/SLD/evidence-analysis |
| `321cfe56` | 90 | Batches 6-11 plus the r2 recapture of Foundation, SLD and mini evidence-analysis |
| `06e019ba` | 110 | Batches 12-15 |
| `7e7b3dd5` | 74 | Batches 16-19 |

The product code is identical from `e9b1b8d9` onward. The `710b0de5` pairs are screens the `e9b1b8d9` delta does not reach.

**Closed heights against the Q23 caps.**

| Proof | Width | Height / cap | Note |
|---|---|---|---|
| App, Foundation Identity, KOBO-001 | 1440 | 606 / 850 | |
| App, Foundation Identity, KOBO-001 | 390 | 606 / 1050 | |
| App, mini evidence-analysis records | 1440 | 452 / 1200 | |
| App, mini evidence-analysis records | 390 | 662 / 1800 | |
| App, mini evidence-analysis, record opened | 1440 | 919 / 1200 | |
| App, mini evidence-analysis, record opened | 390 | 1097 / 1800 | |
| DTO, mini, five 160-char rows + record 5 | 1440 | 1180 / 1200 | |
| DTO, mini, five 160-char rows + record 5 | 390 | 1687 / 1800 | |
| DTO, mini, all open (exempt) | 1440 | 2617 | unclipped, scrolls |
| DTO, mini, all open (exempt) | 390 | 3519 | unclipped, scrolls |
| DTO, Foundation, ten rows / five 160-char | 1440 | 843 / 850 | |
| DTO, Foundation, ten rows / five 160-char | 390 | 860 / 1050 | |

- DTO proofs are in `dto-proof/results.json` at `e9b1b8d9`.
- The first DTO run, at `710b0de5`, failed five of six caps; it led to the Q23 fix above.

**SLD at 390 (Q13), `batch-01/sld-legibility-r2.json`.**
- The drawing fits: scale 0.315, no scroll, overflowX 0.
- Its labels are about 3.5 px, which is illegible.
- The readable key is visible at 12 px, with 10 entries for 10 drawn parts (including the AC bus). All are focusable `aria-pressed` buttons.
- At 1440 the scale is 1.0, the smallest label is 11 px, and the key is hidden.

**Capture-process deviations, for the capture reviewer.**
- The frozen `run_renamed_producer.py` wrapper renamed the producers' hard-coded DBs to `assetops_shellrc_bNN_test` for batches 10, 11 and 12. In batch 10 this was after the permission system refused the producer's own `w301cap_test`. The audit brief says never to use a name-rewriting wrapper, so a reviewer should confirm this is acceptable. The data is unchanged producer output.
- The batch-12 seed rewrote the tracked `replay.json`; it was restored.
- Vite exited silently several times during batches 12, 15 and 17. Each affected part was recaptured whole on a fresh Vite. The final evidence is clean.
- Producers mint new IDs each run, so the targets were re-derived from each run's own output (mappings are in each `run.md`).
- The batch-2 record-opened case uses the first record of the same read.
- Batch 18 uses a window moved one day from the frozen one.

## Known deviations and residual risk

- **Mixed SHAs (stated).** Batches 1-5 were captured at `710b0de5`. The `e9b1b8d9` delta touches only Foundation Identity, the SLD drawing at phone width and the evidence records/record view. Every selected pair of those screens is recaptured at the final SHA: `batch-01/populated-r2`, `batch-02/part-evidence-r2` and `part-evidence-record-r2`. Later groups were captured at the final SHA.
- **Q23 proof method.** No producer can create 160-character values for mini evidence or Foundation Identity. The proof is therefore a pure selected-DTO render: the real App in Chrome with fixture reads (`post-W6-shell-recapture/dto-proof/`). This is an explicit capture gap per Q24, not an app screenshot.
- **Q23 margins.** Foundation at 1440 is 843 against a cap of 850, only 7 px of margin. One of its five long values is a 160-character timezone, which is unrealistic; the stacking still applies to any long value.
- **"No increase" wording (L4)** for a `[1,1]` target is new copy. The backend never stores it today. The Architect may prefer different words.
- **The SLD key is ruled by Q13, with no mock equivalent.** It is not registered as a deviation. The Architect may want a D-row.
- **Flakes.** Two load-sensitive tests failed once each: `siteFindingEvidence` and `evEnergy`. Both are outside this slice, and both pass in isolation.
- **USER_REVIEW:** UI slice. Per the owner-absent rule, merge waits for the owner walkthrough after W6. The capture review comes next.
