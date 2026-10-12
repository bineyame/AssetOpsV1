# V-01a round 2: independent review

Reviewer: a fresh Claude reviewer (Opus), independent of the Implementer. I did not fix, commit or merge anything.
Target: branch `task/V-01a-foundation-visual`, `git diff 13620b6..HEAD` (HEAD `da215d5`).
Authority: `.agent/architect-V-01a-answers.md`, `D-2026-10-12-v01a-owner-visual-rulings`, the owner's verbatim
feedback and both follow-ups, `tasks/V-01a-foundation-visual-fidelity.md`, and the packet's "Round 2" section.

## Verdict

**Accept, with findings fixed on the branch.** One small block, B1, should be fixed before the owner's
visual check. After that, V-01a is ready for that check.

The round does what the Architect ruled:
- Sites shows Site, Type and Mode, a "Setup details" disclosure, and the exact analysis-absent sentence.
- Readiness is green, amber or neutral for configuration only. It has a legend and a scope line, and the
  PRE-S3-04 sentence is intact.
- `component=` selection uses a stable ID, is independent of `at`, survives reload and view changes, and
  clears with a notice when the period does not declare the part.
- The SLD uses a bus-bar layout with type icons and is labelled "Configured, not live". It draws no
  invented breakers, meters, monitoring row, status dots or mock voltages. The 400 V on the AC bus is the
  declared rating.
- Tabs, type and colours are mock-aligned through shared tokens.
- The rail has decorative icons, and only built roots are live.

## Findings

### Block (fix before the owner's visual check)

**B1. The Sites analysis-absent sentence sits flush against the panel edge.**
- Where: `frontend/src/sites/SitesIndex.tsx` (the `p.panel__body.panel__note` after `DataTable`) and
  `frontend/src/ui/primitives.css` (the `.panel__note` block, about line 593).
- What I saw: in the 1440 px screenshot, the sentence starts at the panel's left border. It has no inner
  padding, and its bottom also sits on the panel edge. Every other text block in the panel is inset.
- Why it matters: this is the one panel the owner was told to compare (Directory > Site inventory). The
  owner's complaint was visual quality, so a visibly unpadded line will be the first thing they see.
- Fix: give the note the panel's inset, for example by wrapping it so `.panel__body` padding applies, or
  by finding the rule that overrides that padding. Then re-shoot `app-sites-desktop` and
  `app-sites-narrow`.
- Kind: acceptance gap (item 1, visual fidelity), not a preference.

### Carry

**C1. Required-role rows are amber under a neutral "Unknown" verdict.**
- Where: `frontend/src/sites/FoundationBindingsPanel.tsx`, `roleTone()`.
- What happens: when no binding set is in effect, the backend returns verdict `UNKNOWN` with every role
  `UNBOUND` (`binding_service.py` around line 729). `roleTone()` then paints every required row amber
  "Not bound" under a neutral "Unknown" verdict.
- The ruling says an absent basis stays neutral Unknown, and that role badges follow the same typed
  meanings. Amber rows under an Unknown verdict give a mixed message.
- The test "keeps Unknown neutral when no binding basis resolves" checks only the verdict badge, not the
  rows.
- Next step: either make the rows neutral when `readiness.state === "UNKNOWN"`, or get the Architect to
  confirm that "Not bound, because no set is in effect" is a known gap. Add a row assertion either way.

**C2. The legend wording does not match how the badges are used.**
- Where: `FoundationBindingsPanel.tsx`, `ReadinessLegend`.
- The green legend entry reads "Configured: required configuration complete for this version". On screen,
  the verdict's green word is "Ready to report". Role rows, including optional ones, are green
  "Configured", which means only that this role is configured.
- Fix: word the green entry to cover both, for example "Configured / Ready to report: configured for
  this version (verdict: every required role)". Low priority.

**C3. The Lab run interval drawing now uses the bus-bar geometry, and that has not been checked in a
browser.**
- `shell/IntervalDrawing.tsx` (inside `HistoryInspector`, on the Lab run screen) renders
  `ConfiguredSingleLineDrawing` with slot labels. So the redraw changes the Lab run drawing too, including
  the new fuel-run bracket, with value labels at run midpoints.
- The browser label-collision check (`layout-evidence.mjs` T025d, around line 908) is after the known
  Lab precondition, so it did not run for the Implementer or for me.
- The packet's residual risk mentions only that "Lab run sections are unverified". It does not say the
  drawing itself changed.
- Next step: name it in the packet, and run the T025d section once a Lab run can be created.

**C4. The guard widening for `RailIcon.tsx` is weaker than the packet describes.**
- Where: `tools/checks/shell-overflow.ps1`, the `$iconModules` allowance.
- For `componentIcons.tsx` the guard keys on `width={size}`, a real size declaration. For `RailIcon.tsx`
  it keys on the string `className="nav-rail__icon"`, which says nothing about size. The CSS width of
  `.nav-rail__icon` is not checked.
- The widening itself is legitimate and narrow: two named modules, and a stale allowance fails.
- Fix: also assert the CSS size for `.nav-rail__icon`, or put a fixed `width`/`height` on the svg.

**C5. The record says the store "holds no Finding". That is not accurate.**
- Where: packet line 121 and `.ai/CODE_STATE.md` around line 5234.
- The v01a store copy holds 11 Finding rows (30 revisions). The global index is empty, and the detail
  read answers `PERFORMANCE_CUTOVER_CLOSED` because the v01a prepare step does not run the file-backed
  comparison.
- The existing `tools/s4_finding_walkthrough.py prepare` does run it, so the regression could have been
  run.
- I ran it on a private copy (details below). Finding detail renders correctly at 1440 px. At 390 px,
  `scrollWidth 375 = clientWidth 375`, with no element outside a scroll region. So the regression itself
  is now checked.
- Fix: correct the wording in the packet and CODE_STATE.

### Checked and found sound

- **`component=` semantics** (`SiteFoundationFrame.tsx`, `operatorSiteRoutes.ts`):
  - The key is `component_id`. It is checked against the loaded period's declared components.
  - An undeclared part is cleared with `replace` and a period-scoped notice, and no other part is chosen
    in its place.
  - `at` is carried independently, and view hrefs carry both.
  - A loading period yields `partDeclared === null`, so there is no premature clear.
  - Channels always come from the selected binding set (`partChannels`).
- **Updated tests and layout expectations:**
  - `svg:not(.nav-rail__icon)` only excludes the decorative, `aria-hidden` rail icon from "no drawing"
    assertions.
  - The column set follows the ruling, with no fact dropped (they moved into the disclosure).
  - The Readiness 390 px non-vacuity change is justified: the tables now fit at 640 px.
  - None of these weakens a truth check.
- **Navigation:** the operator rail lists only Sites and Findings. The Lab rail lists only Simulator Lab,
  Site Templates, Scenarios and Runs. The navigation-truthfulness guard passes.
- **Accessibility:**
  - Rail icons are `aria-hidden` beside visible labels.
  - Card icons are `role="img"` named by type, next to the visible name.
  - SLD parts are `role="button"` with `aria-pressed`, Enter/Space and `tabIndex=0`, inside a named
    `group`. The packet's evidence shows visible focus.
  - The parts table has toggle buttons in the first column.
- **SLD against the mock** (I viewed the screenshots): the left supplies, the vertical bus and the right
  loads follow the mock's grammar. The omissions are the right ones.
- **Residual visual note** (not a finding): at 390 px the parts-table Channels column is very narrow and
  wraps hard. This is accepted difference C2, but the owner may notice it.

## Checks I ran (results as I saw them)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd test` (vitest) | 55 files, 1341 passed, exit 0. It ran in this environment; the sandbox esbuild failure did not occur. |
| `npm.cmd run build` | exit 0, chunk-size warning only |
| `tools/check-all.ps1` | all 6 guards passed |
| `v01a-foundation-evidence.mjs` on my private servers | 105/105. Finding detail was NOT RUN by the tool (see C5). |
| `layout-evidence.mjs` on my private servers | 199 PASS, 0 FAIL, then the known Lab precondition ("run-setup submit still disabled after ten seconds"). Lab run and Scenario sections are unverified, including T025d (C3). |
| Finding detail regression (manual, private S4 copy) | 1440 px renders with no overflow (screenshot viewed). 390 px via CDP: scrollWidth = clientWidth = 375, no element wider. |
| `s4-finding-evidence.mjs` on the private S4 copy | 12/36. This is not a regression: the tool reads Finding IDs from the fixed `s4-finding-walkthrough` directory, so it opened IDs that are absent from my copy. Recorded as a tooling limitation. |
| Backend pytest | Not run. The diff has no backend change, and the walkthrough tool change is limited to link output. |

## Isolation

- Databases:
  - `assetops_v01arv` and `assetops_v01arvempty`: a copy of `assetops_s4cases`, plus an empty database.
  - `assetops_s4rv`: a copy of `assetops_s4cases`, with the comparison run and the staged day.
- Work trees: `%LOCALAPPDATA%/AssetOps/v01a-round2-reviewer` and `s4-finding-rv`.
- Ports: API 8870, 8871 and 8872; Vite 5370, 5371 and 5372; CDP 9361 and 9377.
- How: wrapper scripts in the session scratchpad that patch the walkthrough modules' constants. No repo
  file was edited.
- Clean-up: all servers stopped, and none of those ports is listening. The three databases were dropped
  and both work trees deleted. No stray headless Chrome is left.
- I did not touch 8860, 8861, 5360 or 5361 (none was listening at clean-up), the owner's servers,
  `assetops_v01awalk`, or `var/` (read only, to copy `kobo-001.yaml` into private trees).

## Ready for the owner's visual check?

**Yes, once B1 (the unpadded Sites note) is fixed and re-shot.** C1 to C5 can be carried. C1 is worth an
Architect answer before closure, and C3 needs a Lab-run browser pass when the Lab precondition is lifted.
