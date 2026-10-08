# S1-03 review packet: Foundation organized as Site model, SLD and Readiness

- **Task:** `tasks/S1-03-foundation-organization.md`
- **Status:** `in_review`
- **USER_REVIEW_REQUIRED:** true. The owner performs the side-by-side UI check, and the S1 merge is held on it.
- **Authority:** `D-2026-10-08-s1-foundation-organization` (`.agent/architect-S1-ui-organization-2026-10-08.md`).
- **Branch:** `task/S1-03-foundation-organization`, from `f639990`, which is S1-02 `d8dd3e9` plus planning.
- **Commits:** `66227e9` views, `c6a4bcb` guard and layout, `247bf41` binding-period label, `eabf4ca` verdict wording and narrow rail, then the closeout records commit.

## Outcome delivered

An imported Site's Foundation is now three direct-linkable views in the v6.9 order:

| View | Address |
|---|---|
| Site model | `/sites/{code}/foundation` |
| Single line diagram | `/sites/{code}/foundation/sld` |
| Readiness | `/sites/{code}/foundation/readiness` |

- All three views read one stored Foundation and binding read for the `?at=` in the URL.
- Each view opens with a status strip: version, effective period, binding set, gap count, the current or historical label, and the period selector.
- Page lengths at 1440 px:

  | Page | Before | After |
  |---|---|---|
  | Single Foundation page | 12,723 px | — |
  | Site model | — | 1,762 px |
  | Single line diagram | — | 2,164 px |
  | Readiness | — | 3,068 px |

- Long audit material sits behind named disclosures.
- No backend, API, schema or data change was made.
- A legacy Site keeps its one page, with no view row.

## Files materially changed

- `frontend/src/sites/`:
  - `StoredFoundationViews.tsx` (new): composes the three views.
  - `FoundationSubtabs.tsx`: the view row and segment mapping.
  - `FoundationRevisionPanel.tsx`: the strip, controls panel, record details and sources panel.
  - `FoundationBindingsPanel.tsx`: the verdict, role coverage, bindings and acquisition details.
  - `SiteSingleLineDiagram.tsx`: adds `SiteSldPrimary` and `SiteSldDetails`.
  - `SiteConfiguration.tsx`: the legacy contents row is removed.
- `frontend/src/shell/`:
  - `SiteFoundationFrame.tsx`: view routing and the legacy view state.
  - `operatorSiteRoutes.ts`: view route and href.
  - `App.tsx`: registers the view route.
- `frontend/src/ui/primitives.css` and `tokens.css`: three attention tokens and the view styles, plus the ≤640 px shell stacking (question 1).
- Tests:
  - `shell/__tests__/siteFoundationRevision.test.tsx`: 9 new tests; the existing tests are retargeted to their views.
  - `sites/__tests__/foundationScreen.test.tsx`: the view-row and legacy tests replace the contents-row tests.
  - `siteConfiguration.test.tsx`: one helper.
- `tools/checks/navigation-truthfulness.ps1` and `tools/layout-evidence.mjs`.

## Acceptance criteria

| # | Criterion (task and decision section 3) | Status | Evidence |
|---|---|---|---|
| 1 | Three direct-linkable views in mock order. The old row is replaced, and Changes is not rendered. | Met | Routes and `FOUNDATION_SUBTABS`. Tests: "renders the view row…", "refuses … Changes". Behaviour §1. |
| 2 | All views share `at`; reload and share work. | Met | Behaviour §1–2: 16 checks pass, including reload of each view. Test: "keeps the selected period … across views". |
| 3 | Site model order: strip; topology beside identity and obligations; controls with the reserve edit; IDs, digests, import, superseded versions and inventory in disclosures. | Met | `app-foundation-1440-*.png`. Test: "states the stored version…" (IDs in `foundation-record` only). |
| 4 | Readiness order: verdict and missing roles or controls; then coverage, sources, bindings and the action; then a labelled acquisition area with hash and download. | Met | `app-readiness-*`, `app-gap-readiness-*`. Tests in the "S1-02 bindings…" group, now on `/readiness`. |
| 5 | SLD: the diagram is primary, followed by a part and channel explanation, with tables secondary. | Met | `app-sld-*`. Tests: D5 and bound-signals, now on `/sld`. Layout: 10 nodes and 9 connections. |
| 6 | The binding table is not repeated across views. | Met | Test: "places each action on its own view and repeats no binding table". Layout: the binding button shows 0, 0 and 1 across the views. |
| 7 | The period selector and historical label are on every view. | Met | Behaviour §1. A scheduled binding period is labelled (`247bf41` and its test). |
| 8 | Legacy Sites keep truthful behaviour. | Met | No view row. Their view addresses state "needs an imported Site". Layout MG-001: all 56 Foundation claims pass. |
| 9 | No API change and no invented data or mock values. | Met | The diff touches no backend code. Behaviour §5 finds none of the banned words or mock values at 1440 or 390. Gateway text is "registered, awaiting credentials". |
| 10 | Guard enforces three supported views and refuses unsupported or disabled ones. | Met, proven non-vacuous | These violations failed `check-architecture` and were reverted: added *Change & effect*, relabelled a view *Topology*, and `aria-disabled` on a link. |
| 11 | Side-by-side captures at 1440 and 390, first viewport and full page, keyed by manifest ID, with omissions listed. | Met | `.agent/S1-03-screens/` (32 PNGs) and `INDEX.md`. |
| 12 | Remove a binding at a new period, see Readiness and SLD change, and recover the earlier view. | Met (scratch DB) | Behaviour §4: Incomplete at 2026-11-01, SOC role named, the SLD shows it not bound, and *In effect now* restores it. |
| 13 | Keyboard focus and headings. | Met | Behaviour §3: Tab reaches all three view links, each with a solid outline. `select`, `input` and `summary` gained a focus-visible outline. |
| 14 | No horizontal overflow. | Met | Layout KOBO-001: 152 Foundation claims, 0 FAIL, at 1280, 1000, 640 and 390. Captures: scrollWidth equals clientWidth in all 16. |
| 15 | Owner can verify S1 by eye. | **Owner to decide** | `.agent/S1-03-owner-steps.md` |

## Checks run (actual results)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | Passed |
| `tools/check-agent-workflow.ps1` | Passed |
| Frontend `npx vitest run` | 49 files, 1170 tests passed |
| `npx tsc --noEmit -p .` | Clean |
| `npm run build` | Built; only the chunk-size warning |
| Backend `pytest backend` with the test DB | 1572 passed |
| `node tools/layout-evidence.mjs http://localhost:5183 KOBO-001` | `.agent/S1-03-layout-evidence.txt`: 200 PASS, 0 FAIL. It aborted at Lab run-setup (`.data-table__scroll never appeared`), the same Lab-unmeasured carry as S1-02. |
| Same, MG-001 (legacy) | `.agent/S1-03-layout-evidence-mg001.txt`: all Foundation claims pass. 6 FAILs, all in Lab ready-draft claims (Commit and release, optional inputs), because the Lab is served by the product backend rather than `lab_app`. These are not S1-03 surfaces. |
| `.agent/S1-03-screens/behaviour.mjs` on a scratch DB (`assetops_s103_scratch`, converted KOBO-001 plus one reserve split) | `.agent/S1-03-behaviour.txt`: 40 PASS, 0 FAIL |
| v6.9 ledger checker | Not run; the ledger is unchanged |

## Known deviations and ambiguity choices

See `.agent/S1-03-questions.md`. In brief:

1. The shell rail stacks at ≤640 px (a shell-wide change) so that 390 px can be verified at all.
2. Legacy view addresses show a named state rather than redirecting.
3. Three legacy-only panels are left off the imported Site model.
4. Unbound channels sit under the device's component.

Two truthfulness fixes go beyond pure reorganization:
- The strip no longer calls a scheduled binding set "the configuration in effect now".
- The verdict says "Not configured: Battery reserve" rather than "Not bound".

## Residual risk

- The Lab layout claims remain unmeasured.
- The ≤640 px shell rule also changes the Simulator Lab at phone width. It was not reviewed there.
- The topology cards assume one bus and walk upstream chains. A Site with no BUS node gets a stated absence rather than cards.

## User-review focus

- Hierarchy against the mock, side by side.
- Whether the omissions in `INDEX.md` are acceptable.
- The narrow layout.
