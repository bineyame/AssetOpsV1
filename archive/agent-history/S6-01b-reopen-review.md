# S6-01b reopen round - independent re-review

Reviewer: fresh Claude reviewer (not the author). Worktree `AssetOpsV1-review4`, branch `review/S6-01b-reopen` at `4aeaa781`. Diff `4603ceaf..4aeaa781`. Scope: the targeted checks in the dispatch, against ruling `D-2026-10-15-s601-reopen` (S6-01b part) and slice review L1-L3.

## Verdict

**Accept.** No High or Medium findings. Two Lows and one note follow; none of them blocks. The merge stays held for the repeat owner walkthrough at 1440 and 390, and for the S6-01a merge. This review does not give or imply owner acceptance.

## Checks run here

- `npx.cmd tsc --noEmit` in `frontend`: exit 0.
- `npx.cmd vitest run src/sites/__tests__/siteAction.test.tsx src/sites/__tests__/siteFoundationChange.test.tsx`: 2 files and 43 tests passed (35 + 8). It ran in this worktree, so the sandbox esbuild failure did not occur.
- The full `npm.cmd test`, the build and `check-all` were not rerun. I cite the implementer's results instead:
  - Full suite: 64 files, 1522 passed, on the working tree at `85dd5fa4`. That tree holds every TSX change; the later commits change only CSS, the evidence script and docs.
  - Build passed at `07b6fa4a`.
  - `check-all`: 9/9.
  - Browser: 66/66 claims at 1440 and 390.
- I did not rerun the browser evidence. I viewed one screenshot: `scratchpad/s601b-evidence-reopen/app-recommendation-latest-narrow.png` (390).

## Checks against the ruling

- **Prior Actions are listed with honest origins and never relabelled.**
  - `PriorActionList` (`SiteRecommendation.tsx` ~303-336) takes the origin version and link from `origin.revision_no` and `origin.finding_revision_id`.
  - "(this version)" and "(not the version on this page)" come from the server's `is_selected_revision`, not from client logic.
  - Each item shows the application state, the failed-attempt count, the outcome words and the exact Action link.
  - Tests cover both sides: "this version" on `accepted_snapshot_live_status`, and "not the version on this page" on both newer-revision cases.
- **The held notice depends only on `state`.**
  - `held = body.state === "PRIOR_ACTION_UNRESOLVED"` (~127).
  - When the body is `ACCEPTED` and also carries `prior_action_block`, the `accepted` branch renders and the notice does not. A test covers this case.
- **The live reason is separate.** `LivePanel` is a second panel beside the notice, with the note "a separate reason, shown for information". On the recorded clock it shows `AVAILABLE`; on the served clock it shows `FOUNDATION_BASIS_STALE`. Both cases are tested at 1440 and 390 respectively.
- **Accept is disabled and the reason is stated.** The button has `disabled` and `aria-describedby` pointing to a sentence that links the blocking Action. No proposal panel is rendered, so nothing is offered for acceptance.
- **The 409 copy is truthful.**
  - Checked against the recorded `accept_newer_revision_prior_action_unresolved` detail (`blocking_action_code`, `origin_revision_no: 1`, `links.action`, `live_status.state: AVAILABLE`).
  - The page says "Not accepted ... no new Action was recorded", links "Open ACT-000001", gives "(accepted on Finding version 1)" and the code, and shows the live state separately.
  - The test asserts exactly one POST and no "done" outcome.
- **L1 (walkthrough tool) is fixed.** Read in `tools/s601b_action_walkthrough.py`:
  - The marker records `db=`.
  - `prepare` refuses an existing DB unless the marker records it, and the guard runs before the marker is rewritten.
  - `drop` refuses to drop an existing DB the marker does not record, and removes the folder only when the marker records `self.db`.
  - The docstring matches the code.
- **L2 is fixed.** The `action-list--codes` no-wrap rule is scoped to `.action-ref` inside that list. A unit test checks the class; a browser claim checks one client rect per code.
- **L3 is fixed.** `noTime` disables Apply, the click handler also guards against it, and the stated reason is shown. A test shows that no POST is sent and that Apply is enabled again once a time is entered.
- **The disabled-button style does not break existing controls.**
  - The only `.action-command` buttons are Apply and the two Accept buttons, and none was ever `disabled` before.
  - The busy state uses `aria-busy`, not `disabled`, so it is unaffected.
  - `:disabled:hover` has higher specificity than the base `:hover`, and the tokens it uses exist in `tokens.css`.
- **The narrow screenshot looks right.** The panels stack cleanly and there is no sideways overflow. The notice, the separate live panel, the greyed Accept with its reason, and the "Actions on this Finding" item all read correctly.
- **Owner walkthrough step 2 is accurate.** It matches the rendered copy: "Applied to the Site Foundation", pending outcome, `FOUNDATION_BASIS_STALE` on the served clock, greyed Accept, "(not the version on this page)". It states that the 409 path cannot be triggered in the walkthrough.

## Findings

**L-a (Low, test strength).** `siteAction.test.tsx`, test "shows no held notice when state is ACCEPTED, even if a prior_action_block is present".
- What is wrong: because `accepted` renders first, this test cannot detect a regression that derives `held` from the block's presence. It also does not cover a body with `state` `AVAILABLE` or `UNAVAILABLE`, no accepted record, and a `prior_action_block` present. In that case a block-presence regression would show the notice and disable Accept.
- Context: the packet already admits that this weaker mutation is invisible to the test.
- Fix (optional): add a derived case with `pre_accept_available` plus a block, and assert that no notice appears and Accept is enabled.
- Classification: preference, not an acceptance gap.

**L-b (Low, cosmetic, 390).** The `LivePanel` reason `FOUNDATION_BASIS_STALE` breaks mid-token at 390 (`FOUNDATION_` / `BASIS_STALE`) in the screenshot. This is the same class as L2, but in the live panel.
- Context: this is existing `LivePanel` styling, not new in this round. It is legible.
- Fix (optional): extend the L2 no-wrap treatment to that line. Note that a long token without breaks could cause overflow at 390, so check the width after the change.

**Note (residual, not a finding).**
- A work folder prepared before this round has the old marker, which has no `db=` line.
  - `drop` refuses to remove such a folder or its DB, and `prepare` refuses to rebuild it.
  - Recovery: the owner would need to drop the DB and delete the folder by hand.
  - I found no leftover `var/s601b*` folders in any `AssetOpsV1*` worktree, so this is unlikely to bite.
- Re-running `prepare` with a different `--db` on the same `--work` rewrites the marker and orphans the earlier DB. The `assetops_s601b` name prefix keeps the damage contained.

## Residual risk

- The 409 path is proven only on the recorded fixture. It cannot be reached in the walkthrough.
- The rule that releases the hold depends on the resolved/closed transition, which S6-02 has not yet defined. The copy "a new trial waits until it is settled" does not promise anything beyond that.
