# S6-01b reopen round handoff - `D-2026-10-15-s601-reopen` + review Lows

Branch `task/S6-01b-action-ui`; code `4603ceaf..07b6fa4a`. No backend change. Packet section "Reopen round" in `.agent/S6-01b-review-packet.md`; owner steps `.agent/S6-01b-owner-walkthrough.md` (new step 2).

- Recommendation (`frontend/src/sites/SiteRecommendation.tsx`; types `PriorAction`, `PriorActionBlock` in `actionClient.ts`):
  - "Actions on this Finding" lists `prior_actions.items` with the Action's own origin version.
  - On `state=PRIOR_ACTION_UNRESOLVED`, the "An earlier trial is still open" notice names and links the blocking Action, its origin version and its application/outcome. The live recomputation is shown as a separate reason. Accept is disabled with a stated reason.
  - A 409 `PRIOR_ACTION_UNRESOLVED` on accept is handled in `AcceptOutcome`.
  - The notice is decided from `state` only. A test covers ACCEPTED with a block.
- L1 `tools/s601b_action_walkthrough.py`:
  - The marker records `db=`.
  - `prepare` and `drop` act only on that recorded DB.
  - `drop` removes the work folder only for the recorded DB.
- L2: the `action-list--codes` no-wrap rule.
- L3: Apply is disabled while the effective-time field is empty.
- Disabled `.action-command` is now styled as unavailable.
- Proof:
  - tsc clean;
  - full frontend suite 1522 passed;
  - build passed;
  - `check-all` 9/9;
  - 5 mutations, each caught by a test;
  - browser 66/66 at 1440/390 (fresh private DB, then dropped; servers stopped);
  - L1 refusal shown by hand.
- Open:
  - The 409 path cannot be triggered in the walkthrough; it is tested on the recorded case.
  - S6-02 must define the resolved/closed transition that releases the hold.
- Next: a fresh Claude re-review of `4603ceaf..HEAD`, then the repeat owner walkthrough at 1440/390. The merge is held for owner acceptance and the S6-01a merge.
