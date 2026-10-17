# W1-F1 re-review: fix round 1

- **Reviewer:** a fresh Claude Reviewer, not the author.
- **Revision:** `4a90ecb8`, diff `fe0295d7..4a90ecb8` excluding `.agent`, in worktree `AssetOpsV1-review5`.
- **Inputs:**
  - the prior review, `.agent/W1-F1-review.md` (RETURN);
  - the packet's "Fix round 1" section and its known deviations;
  - the new captures in `.agent/W1-F1-evidence/`;
  - the owner verdict of 2026-10-17;
  - the v69 mock.

## Verdict: RETURN

One Medium finding blocks: finding A below. It is narrow and cheap to fix.

The fix round itself is good:
- Both Highs are closed.
- All five prior Mediums are closed.
- Lows 9, 10 and 11 are closed.
- The guard now fails a planted leading card of any shape.
- The Readiness panel 1 bulk is gone, and the strip carries the verdict as the mock's does.

What is left is one style drift that recurs on three screens. The owner would name it on sight: explanatory prose set in body-size type inside v69 panels, where the mock has a one-line note or nothing. It is worst on the SLD screen, where the packet deferred it as Low 8. I am raising it, as the dispatch asked: the owner would still call this drift.

## Prior findings: status (PNG pairs at 1440 checked side by side)

| # | Prior | Status | What I saw |
| --- | --- | --- | --- |
| 1 | High: guard bypass | **Closed** | `leadingIntruders` and `strayOutsidePanels` are in `frontend/src/test/panelStructure.ts:78-106`, wired into `expectV69Panels` (`:143-144`), with 5 non-vacuity tests. My product plants are below. |
| 2 | High: Readiness bulk / strip | **Closed** | The strip now leads with `[Set up to report] Configuration readiness is distinct from what the readings can support`. The heading, banner, legend and paragraphs are gone from panel 1. What remains is three 10 px note lines and a closed disclosure. |
| 3 | Medium: assessment cards | **Closed** | 3 px tone top border and a 17 px state word. Matches the mock's `.metric.assessment`. |
| 4 | Medium: strip height | **Closed** (residual accepted, see below) | It went from about 160 px over 3 rows to about 73 px over 2 rows. The selector is chip-sized and the disclosure is link-styled. |
| 5 | Medium: Sites callout and toolbar | **Closed** | The callout and the second toolbar are gone. Search and filters sit in the chip row. The table starts directly under the panel head. |
| 6 | Medium: page heading | **Closed** | The h1 is the site name, with a provenance tag and the per-screen description, on all three Foundation views. |
| 7 | Medium: native controls | **Closed** | The reserve form uses `.field` inputs and a primary button. The refusal action uses `.button.primary`. |
| 9 | Low: SLD title | Closed | The title is the site name. The description states that the topology type is not stated. |
| 10 | Low: both lists | Closed | The In setup description notes the overlap. |
| 11 | Low: NO_EFFECTIVE_REVISION | Closed | Three skeleton panels with in-panel gaps. The test asserts no tiles, no tables and no reserve form. |
| 8 | Low: SLD prose | Not done | Superseded by finding A. |
| 12 | Low: refused Readiness cards | Not done | Still Low. Acceptable for F5. |

## Guard plants

All plants were in `ReadinessView` (`frontend/src/sites/StoredFoundationViews.tsx`) and were run against `siteFoundationRevision.test.tsx`. Each was reverted with `git checkout -- frontend/src`, and the tree is clean.

1. **h3 callout before panel 1.** I planted `<section className="callout"><h3>Is this site set up to report?</h3>…` before `ReadinessCards`.
   - Result: **failed, as it should.** 6 tests failed, all with `elements before panel 1 of v69 screen "readiness"`. The 6 are the S1-03 order test and the 5 W1-F1 readiness variants.
2. **My bypass attempt: a large plain `div` with a bold label before panel 1.** I planted `<div style={{padding:32,fontSize:24}}><b>Configuration readiness</b> Set up to report…</div>` with no heading and no class.
   - Result: **failed, as it should.** All 5 W1-F1 readiness variants failed. The allowlist catches any non-empty sibling.
3. **Bypass that passes: bulk inside an allowed leading pattern.** I appended a 28 px `div` holding a bold verdict and two paragraphs inside the strip slot, next to `ReadinessVerdictLead`.
   - Result: **all 107 tests passed.**
   - The strip is exactly where the Readiness verdict now lives, so this is the most likely place for bulk to grow back.
4. **Bypass that passes: an unpanelled block between panels.** I planted the same bold-label `div` between panel 1 and `GatewayStatusPanel`.
   - Result: **all 12 W1-F1 tests passed.** `strayOutsidePanels` matches only headings, sections, cards and callouts.

Should the guard catch 3 and 4? Yes, ideally. Both meet the contract's wording, though: "reject any extra leading card/panel before panel 1". The mandatory side-by-side capture review backs them up. So I file them as Low finding B, not as blocking.

## Remaining height deviations: judgement

| Deviation | Judgement | Why |
| --- | --- | --- |
| Foundation strip, 73 px vs 44 px | **Accept** | It is compact and reads as one strip. The second line carries the selector and links that the stored read needs: period choice, channel links and gaps, as-of time. The owner's complaint was bulk, and this is no longer bulky. |
| Readiness panel 1, 592 px vs 364 px | **Accept** | The extra height comes from four things: 6 data rows against the mock's 5, a taller row height, three 10 px note lines carrying the material limit (`-w1-ux-disclosure`), and one closed 36 px "Advanced details" bar. It reads as the mock's table panel. The bar is the same closed-disclosure pattern used on every Foundation view. |
| SLD panels taller | **Split** | The drawing (9 parts, a vertical bus) and the 10-row parts table are driven by the data, so that height is acceptable. The roughly 150 px of three body-size paragraphs under the legend is **not** acceptable. See finding A. |

## Findings

### A. Medium (blocking): explanatory prose in body-size type inside v69 panels
This finding is about the visual style the owner flagged ("styled inferior"). It is not a disagreement over content: every statement can stay.

**Where it appears, and what the mock shows instead**

- **SLD panel 1.** Source: `frontend/src/sites/StoredFoundationViews.tsx` (SLD view, around `:589-600`, `:682`) and `frontend/src/sites/SiteSingleLineDiagram.tsx` (around `:95`, `:1175`). Capture: `sld-now-1440-app.png`, y ≈ 1150-1300.
  - App: three paragraphs at the app body size (about 15 px) under the legend. They are the largest type in the panel apart from the title, and visually they outweigh the drawing's labels.
  - Mock: the legend only. The configured-not-live limit is one blue `notice` below the panels.
- **Readiness, Gateway status panel.** Source: `frontend/src/sites/ReadinessOverview.tsx` (around `:497`). Capture: `readiness-now-1440-app.png`, y ≈ 1265-1490.
  - App: between the metric cards and "Connected sources", about 230 px of material:
    - a body-size blue notice ("The period shown is Foundation v10…");
    - a body-size "Read at…" line;
    - a key-value row;
    - a body-size diagnostic sentence;
    - a full-width "Advanced details" bar.
  - Mock: a single timeline strip in that position.
- **Sites, Site inventory.** Source: `frontend/src/sites/SitesIndex.tsx:487`. Capture: `sites-stocked-1440-app.png`, y ≈ 498.
  - App: the "Assessment, top issue… not available in this directory" sentence is set in body size, directly above a 10 px `v69-chart-note` that says much the same thing.

**Why it blocks.** F1 settles the shared patterns that F2-F5 inherit. Body-size explanatory paragraphs inside panels are the residue of the W1-UX answer-card style, one level down. They make each screen read heavier than the mock. The owner asked not to have to comment on the same thing twice.

**Fix**

- **SLD.** Condense the three paragraphs to one `v69-chart-note` line under the legend, for example: "Configured, not live · channels bound in channel links v9 · protection and meter positions not declared · reporting not assessed here → Site Evidence". The full text can go into the closed disclosure.
- **Gateway panel.**
  - Render the period/contact separation and the diagnostic sentence as `v69-chart-note` lines, or as one small notice.
  - Keep the key-value row.
- **Sites.** Drop the body-size sentence, or merge it into the existing note line. The note already states the scope.
- **Tests.** Existing text assertions should keep passing wherever the text survives verbatim in a note or disclosure. Any changed assertion must be listed in the packet.
- **Evidence.** Recapture the three screens.

### B. Low: the guard has two remaining routes
Source: `frontend/src/test/panelStructure.ts:51-55`, `:96-106`

The two routes are plants 3 and 4 above:
- bulk inside `.status-strip`, `.v69-cards` or `.v69-chips`;
- an unpanelled text block between panels.

**Suggested hardening**

- Inside `.status-strip`, fail on any `p`, `h3`-`h6` or block `div` carrying more than one sentence. Alternatively, cap the strip at two text lines.
- Flag any non-empty visible element that is a sibling of a panel, between panels, unless it is an allowed trailing note (`.note`, `[data-readiness-scope]`, the mock's `notice`).

This is non-blocking. It can go with the F2 handoff.

### C. Low: polish in the no-version refusal page
Capture: `foundation-no-version-1440-app.png`

- **Duplicated Site ID.** The provenance tag shows "KOBO-001" next to the h1 "KOBO-001". The packet says refusal branches carry no badge.
- **Raw timestamps in product copy.** The refusal sentence shows machine ISO timestamps: `2026-09-01T00:00:00+00:00` and `2026-10-17T07:06:51.011160+00:00`.
- **No breadcrumbs.** The refusal page has none, while the stocked views do.

All three are non-blocking and fit the F5 sweep or the W1 plain-language batch.

### D. Low (residual, not new): Identity panel key-value styling
The app's values are set at body size, left-aligned and wrapping. The mock's are 11 px, right-aligned, with row dividers. The worst case is the "Critical service order" value, which runs over five lines.

This styling predates the fix round and was not flagged before. It is noted for F5.

## Honest state and changed assertions

I reviewed every changed assertion in:
- `siteFoundationRevision.test.tsx`;
- `siteFoundationRoute.test.tsx`;
- `foundationScreen.test.tsx`;
- `sitesIndex.test.tsx`.

All of them are justified by the structural move. The packet's account of them is accurate.

**Where the checks moved**

- The verdict badge and tone checks moved to `verdictLead()`, with the same states and tones: configured, config-gap, Incomplete, and not recognised.
- The legend test now asserts that the legend is absent, and that the scope line still names all three colours together with "Green does not mean a device is connected…".
- The separation sentence is split. "Distinct from what the readings can support" is asserted in the strip, and "central server contact only" in the page note. Nothing is lost.
- Card checks read the value word and the tone class.
- The h1 checks expect the site name, the provenance and the subtitle.
- Finding 11's fail-closed path is now stronger: per-panel gap text, no tiles, no tables and no form.

**What still holds**

- No honest-state check was weakened.
- The "Not recorded" commissioning row and the "configuration only; not connection or condition" limit remain visible.
- The provenance tag shows the read's evidence mode ("Demonstration data").

## Checks I ran (from `frontend/`, PowerShell)

- **`npx.cmd tsc --noEmit`:** exit 0.
- **Focused tests:** I ran `npx.cmd vitest run` on 6 files:
  - `src/test/__tests__/panelStructure.test.ts`
  - `src/shell/__tests__/siteFoundationRevision.test.tsx`
  - `src/shell/__tests__/siteFoundationRoute.test.tsx`
  - `src/shell/__tests__/sitesIndexRoute.test.tsx`
  - `src/sites/__tests__/foundationScreen.test.tsx`
  - `src/sites/__tests__/sitesIndex.test.tsx`

  Result: **6 files, 238 passed, 0 failed**, 45.7 s. This matches the packet's focused count.
- **Guard plants:** 4 runs, results as above, all reverted.
- **Not rerun:**
  - full `npm.cmd test`: the packet cites 76 files and 1953 passed on `ce42ef17`. `d7f544d3` is CSS only, and `4a90ecb8` touches `.agent` only;
  - `npm.cmd run build`;
  - `tools/check-all.ps1`;
  - the capture tool, which needs Chrome, the backend and a dev server.

  For these I relied on the packet's numbers, which I could not verify.

## Captures

- I opened the 1440 app/mock pairs for Readiness, Foundation, Sites and SLD, and the Foundation no-version pair.
- `evidence.json`, `run.log` and `index.html` are present and regenerated at `d7f544d3`.
- The packet records 96/96 claims and overflow 0. I did not re-measure pixel positions; the heights above are the packet's numbers, which agree with what the PNGs show.
