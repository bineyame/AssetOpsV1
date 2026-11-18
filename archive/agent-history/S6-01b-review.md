# S6-01b slice review - Action, recommendation and change surfaces

Reviewer: fresh Claude reviewer (did not author S6-01b or its phase-1 review). Worktree `AssetOpsV1-review4`, branch `review/S6-01b-slice` at `48c96648`; slice diff `c341599b..48c96648` (stacked on unmerged S6-01a). Commits after the final code revision `15d156d1` were verified as docs only (`.agent/*`, `.ai/*`, `tasks/S6-01b-action-ui.md`).

## Verdict

**Accept.** No High or Medium findings. Three Lows below, none blocking. USER_REVIEW_REQUIRED stands: hold the merge for the owner walkthrough and the S6-01a merge.

## Phase-1 fold-in (M1, L1-L5): verified real

- **M1:** `SiteAction.tsx:147-149` routes 404 `ACTION_EVENT_NOT_FOUND` to `SelectionNotFound` (`:209-239`). It says "Selected event not found", states that the Action itself is fine, and links to the latest record. A test covers it on the recorded `unknown_event_404`.
- **L1:** an untouched default is re-derived at click as the next UTC midnight after max(read time, now) (`:395-401`, `:433`). The exact-value test pins the clock.
- **L2:** an exact-command grant test exists. The implementer mutation-proved it; I did not repeat the mutation.
- **L3:** with no `current_foundation_revision_id`, Apply is not offered and the reason is stated (`:476-480`).
- **L4/L5:** the derivations are declared, and the listed recorded cases are covered in `siteAction.test.tsx` (30 tests).

## Focus items

- **Foundation change and bare route.** Both are static segments under Foundation and rank above `:foundationView`. `FoundationSubtabs` and `foundationScreen.test.tsx` are untouched by the diff, and that file passes 49/49. The bare `/foundation/changes` route shows an explicit "No list of changes yet" with a link back. The change frame marks the Foundation tab as current and shows no view row.
- **Honest copy.**
  - The pending outcome reads "Nothing has been verified yet, and no effect or saving is claimed."
  - The Overview says "The Site's operation is not shown as changed".
  - The change page says the effect "is not judged here".
  - Money is a link only, with "The trial predicts no saving".
  - "Applied to the Site Foundation" describes the configuration publish, which is true.
  - The vocabulary substitutions are honest, and the IDs are exact: "Application" for `execution` (URL kept), and "Signal assignment versions" for the banned word "binding".
- **Controls.** `granted()` requires `allowed === true` and the exact command (`actionPresentation.tsx:84-86`). Accept additionally needs AVAILABLE and a proposal. Apply additionally needs a LATEST selection, PENDING, and a stated current Foundation version. Everything else is read-only with the server reason.
- **Walkthrough tool safety.** I probed the guards with six bad argument sets, and all six were refused:
  - `assetops`;
  - `assetops_s601b_test`;
  - `assetops_s601b;drop`;
  - `var\other`;
  - a `..` escape into `backend`;
  - the main checkout's `var\s601b_owner`.

  Grants: `fixture_grants` lists only this database's tenant and Site and the three manifest Findings. Ports: API 8961, web 5461, CDP 9461, all overridable. Isolation: the tool probes `assetops_backend.__file__` inside its own tree, and the probe passed.
- **Reproducibility.** I ran the tool on `assetops_s601b_rev` / `var\s601b_rev` and the ports below. It created `ACT-000001`, the change and 6 events.

  | Step | Result |
  | --- | --- |
  | `prepare` | Succeeded in 73 s; Performance cutover permitted |
  | `serve` (API 8971, web 5471) | API reads 200 |
  | `node tools/s601b-action-evidence.mjs` (CDP 9471) | 56/56 claims passed |
  | `drop` | Removed the database and the folder |

- **390 layout.** I viewed `app-change-narrow.png`. There is no page-level sideways scroll, and the dense tables scroll inside their own scroller. One cosmetic issue is described in L2.
- **"A newer Finding reopens the Recommendation".** The walkthrough's "Things to know" section states this plainly as a decision candidate. In the served run (`app-recommendation-latest-desktop.png`), the latest version reads `FOUNDATION_BASIS_STALE` and shows no accept control. That matches the packet's stated clock deviation.

## Findings (Low, non-blocking)

- **L1: walkthrough drop and recreate is not ownership-checked for the database.**
  - Where: `tools/s601b_action_walkthrough.py:154-156` (`prepare`) and `:217-221` (`drop`).
  - What is wrong: the docstring says the database is "dropped first if this tool made it". In fact, any `assetops_s601b*` database (other than `_test`) is dropped unconditionally. `drop` also removes the database before it checks the folder marker.
  - Why it matters: the blast radius is bounded by the prefix guard, so the risk is small. The docstring overstates the guard.
  - Fix: either correct the docstring, or record the database name in the marker file and refuse a mismatch.
- **L2: failure codes wrap mid-token at 390.**
  - Where: the `Attempts` list in `SiteFoundationChange.tsx` (`Ref` inside `li`).
  - What is wrong: the code breaks inside the token, as in "ACTION_FO / UNDATION_STALE".
  - Fix: apply the same no-wrap treatment already given to the dense-table references.
- **L3: a cleared effective-time field is still sent.**
  - Where: `SiteAction.tsx:433-438`.
  - What is wrong: if the operator empties the `datetime-local` field, the command is sent with `effective_from: ":00+00:00"`.
  - Why it matters: the server refuses it with a typed error, but this probably records a FAILED attempt (audit noise).
  - Fix: disable Apply while the field is empty.

## Checks run (this review)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | Passed (temporary `.venv` junction, removed afterwards) |
| `tools/check-agent-workflow.ps1` | Passed |
| `npx.cmd tsc --noEmit` | Exit 0 |
| Focused vitest: siteAction, siteFoundationChange, siteFinding, foundationScreen | 4 files, 119 passed |
| Full `npx.cmd vitest run` | 64 files, 1517 passed |
| `npm.cmd run build` | Built (chunk-size warning only) |
| Walkthrough `prepare` / `serve` / evidence / `drop` | See the table under Reproducibility above |

The expected esbuild sandbox failure did not occur in this session, so the frontend suite and build numbers are my own, not inferred.

**Backend.** The slice has no backend change. I did not rerun the backend suite. I cite the implementer's run on `15d156d1`, which is the code revision under review (later commits are docs only):
- command: `pytest backend/tests -n 2 --dist loadfile`;
- JUnit: 2209 cases, 0 skipped, 0 failed;
- wall time: 10:02.

The walkthrough `prepare` exercised the real S6-01a stores and API end to end against Postgres.

**Not run:** `tools/layout-evidence.mjs` (the packet records 327 PASS and 2 FAIL, both environment preconditions outside S6-01b), and mutation checks (I found no assertion I doubted).

## Residual risk

- The served walkthrough reads on the real clock, while the records carry the fixture clock. The owner will see `FOUNDATION_BASIS_STALE` on the latest-revision Recommendation, where the recorded contract reads AVAILABLE. The packet discloses this.
- `datetime-local` handling across browsers (seconds, locale) has not been exercised outside Chrome.
