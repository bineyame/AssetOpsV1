# S6-01a reopen round handoff - `D-2026-10-15-s601-reopen`

Code `586d5fe1` on `task/S6-01a-action-store-read`. Packet section "Reopen round" in `.agent/S6-01a-review-packet.md`.

- Read: `ActionService.recommendation` reads `store.actions_for_finding` before the live rule; body adds `prior_actions.items` (origin revision ID/number, `is_selected_revision`, `application.state`, `outcome.state`, `unresolved`, `links.action`/`api_action`) and `prior_action_block`. When blocked: `state=PRIOR_ACTION_UNRESOLVED`, `proposal=null`, `unavailable` = typed reason, `live_status` = live rule (AVAILABLE or e.g. `FOUNDATION_BASIS_STALE`), `system_demo_capability.allowed=false`.
- Accept: 409 `PRIOR_ACTION_UNRESOLVED` (`blocking_action_id`, `origin_finding_revision_id`, `links`, `blocking_actions`, `live_status`). Checked in the service, then again in `PostgresActionStore.accept(..., guard=)` under `pg_advisory_xact_lock('action-trial:' site:finding:asset:field:rule)`; the identical-key replay still comes first.
- Every post-acceptance state blocks (no resolved/closed transition yet); S6-02 must add the release.
- Contract fixture regenerated: `recommendation:1#a.latest_revision_after_apply` (recorded clock, live AVAILABLE), `latest_revision_after_apply_served_clock_stale` (clock 2026-10-15, live stale), `accept_newer_revision_prior_action_unresolved`; NOTES `prior_actions`, `PRIOR_ACTION_UNRESOLVED`.
- S6-01b next: rebase onto this, render the notice/link and disabled Accept from these fields at 1440 and 390, repeat the owner walkthrough.
- Proof: 4 S6 files 81 passed; check-architecture passed; 4 mutations caught; full suite 2210 passed (546 s), JUnit 2210/0 skipped/0 failed. DB dropped.
