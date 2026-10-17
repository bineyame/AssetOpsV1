# W1-F1 re-review 2: fix round 2

- **Reviewer:** a fresh Claude Reviewer, not the author.
- **Revision:** `792ac263`, diff `d5d3343b..792ac263` excluding `.agent`, in worktree `AssetOpsV1-review5`.
- **Inputs:** `.agent/W1-F1-rereview.md` (finding A, Lows B and C), the packet's "Fix round 2" section, the 1440 captures in `.agent/W1-F1-evidence/`, and the v69 mock.

## Verdict: RETURN

One Medium blocks: A2 below. It is the unfinished part of finding A, on the Gateway panel. It is narrow: about four class names.

Everything else in the round is good:
- SLD and Sites are closed.
- Low B (the guard) is closed, and both plants fail.
- Low C is done.
- No assertion changed, and the remaining SLD/Gateway height is mostly data-driven (see below).

## 1. Is finding A closed?

| Screen | Status | What I saw at 1440 (app vs mock) |
| --- | --- | --- |
| SLD | **Closed** | The three paragraphs under the legend are now 10 px `v69-chart-note` lines (y ~1200-1275). The drawing labels outweigh them again. The mock has a legend only; three note lines is acceptable. |
| Sites | **Closed** | The "Assessment, top issue…" sentence is note-size. It sits as one scope note above the existing note. |
| Readiness, Gateway panel | **Partly closed** | The period note and the "Read at" line are now notes. **The diagnostic sentence that A named explicitly is still body size**, and so are three more sentences in the same panel. See A2. |

## Findings

### A2. Medium (blocking): body-size prose remains in the Gateway status panel
Capture: `readiness-now-1440-app.png`.

Finding A's Gateway fix said to "render the period/contact separation **and the diagnostic sentence** as `v69-chart-note` lines". The round converted the period note, the read-at line and the unavailable/none branches. It missed the loaded-state sentence, which is the one the owner sees:

- **`frontend/src/sites/ReadinessOverview.tsx:396`**, `<p data-gateway-contact-sentence="">`. It renders "The last gateway diagnostic reached the server longer ago than two reporting intervals…" at about 15 px (capture y ~1412). It is the largest text in the panel after the card values.
- **The same pattern in the Connected sources sub-panel (y ~1720-1790):**
  - `:593`, `<p data-gateway-sources="">` ("8 sources registered behind this gateway. Device connection not established here."), body size;
  - `:654-669`, the two `not-available-yet` paragraphs (signal strength, firmware), body-size italics.

  The mock has one 11 px identity line and a link row there. These three lines make that sub-panel read heavier than the chips it describes.

**Why it blocks.** This is the same drift the owner asked not to have to raise twice, and one line of it was explicitly named in the prior finding. F2-F5 inherit this panel pattern.

**Fix**
- Add `v69-chart-note` to the three `<p>` elements, and to the two `MissingClaim` paragraphs (`className="not-available-yet v69-chart-note"`, which the round-2 CSS already sizes at 10 px).
- Keep the wording. This is class-only, and no assertion should change.
- Recapture Readiness at 1440 and 390.

## 2. Taller panels: data-driven or drift?

- **Gateway, 845 vs 561 px:** acceptable once A2 is fixed.
  - The remainder is data: 8 source chips against the mock's 6, a 3-item effect list against 2, the key-value row, and one closed disclosure.
  - The mock's timeline strip is absent honestly.
- **SLD parts, 640 vs 287 px:** acceptable. There are 10 data rows against the mock's 4 grouped rows, at about the mock's row height, plus one closed disclosure.
  - Low E (F5): the description line is indented about 11 px further than the table (x ~276 vs ~265).
- **SLD drawing, 974 vs 596 px:** mostly data-driven. There are four vertical rows, because the fuel tank gets its own row. The owner may still notice it as airy. Three concrete things could shrink it, as **Low D (F5 or the SLD layout follow-up, non-blocking)**:
  1. The row pitch is about 143 px against the mock's ~106. Tightening it would recover about 110 px.
  2. "Readings not assessed here" is repeated in italics under all 9 parts and the bus. That adds a text line per part, and it duplicates the chip line "Configured, not live · Readings are not assessed in this view". One statement suffices; the per-part slot could be dropped or reduced to a dash.
  3. There is about 65 px of empty canvas below the last part and the bus foot (y ~1090-1155).

  Also minor: the "Readings are not assessed in this view." text beside the chip is body size.
- **Other body-size residue, Low (F5 / plain-language batch):**
  - the page-level `[data-readiness-scope]` note under Readiness is about 16 px, where the mock uses a small blue notice;
  - the Sites "In setup" italic "Setup progress not available…" line is body size.

## 3. Guard

Both plants were in the real product. Each was run against `src/shell/__tests__/siteFoundationRevision.test.tsx`, run separately, and reverted with `git checkout -- src`. The tree is clean.

1. **A `<p>` with two sentences inside the Readiness status strip**, inside `ReadinessVerdictLead`: **failed, as it should.** 6 tests failed with `blocks inside the status strip of v69 screen "readiness"`.
2. **A stray `<div><b>Stray</b> …</div>` between `ReadinessEvidenceTable` and `GatewayStatusPanel`**: **failed, as it should.** 6 failed, 101 passed, with `content blocks between panels of v69 screen "readiness"`.

Low F (non-blocking): `stripIntruders` exempts any element whose class starts with `status-strip__` (`frontend/src/test/panelStructure.ts`, the `continue` on the `status-strip__` test). So bulk wrapped in, for example, `<p class="status-strip__lead">` would pass. A cap on the strip's text length or line count would close this. The capture review backs it up meanwhile.

## Checks run (from `frontend/`, PowerShell)

- **`npx.cmd tsc --noEmit`:** exit 0.
- **`npx.cmd vitest run`** on 6 files:
  - `panelStructure.test.ts`
  - `siteFoundationRevision.test.tsx`
  - `siteFoundationRoute.test.tsx`
  - `sitesIndexRoute.test.tsx`
  - `foundationScreen.test.tsx`
  - `sitesIndex.test.tsx`

  Result: **6 files, 242 passed, 0 failed**, 43.8 s. That is the prior 238 plus the 4 new guard tests.
- **Guard plants:** 2 runs, both failed as expected, both reverted.
- **Not rerun:** the full `npm.cmd test`, `npm.cmd run build`, `tools/check-all.ps1` and the capture tool. For these I relied on the packet's numbers (1957 passed, 10 guards, 96/96 claims at `f95c9f41`). `792ac263` touches `.agent` only relative to `f95c9f41`.
