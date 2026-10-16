# S7-01b build - implementer brief

Work ONLY in worktree `C:/Users/assef/Bineyame/AssetOpsV1-review`, branch `task/S7-01b-health-ui` (from main `f3de235a`; S7-01a merged). Touch no other worktree. Ports: API 8947, web 5447 (packet), DB prefix `assetops_s701_owner*`.

Read: packet `tasks/S7-01b-health-ui.md` (incl. plan fix round 1 and R2 carry), umbrella `tasks/S7-01-site-health.md`, Architect `.agent/architect-W1-remaining-answers.md` (S7-01), `.agent/architect-W1-remaining-q-answers.md` (asset route by configured asset ID; NOT_CONFIGURED; out-of-basis asset 404), the S7-01a handoff `.agent/S7-01a-handoff.md` and review `.agent/S7-01a-review.md`, and the new ruling `D-2026-10-16-s701-clock` (`.agent/architect-S7-01-clock-answers.md`).

Small S7-01a backend follow-up (in this slice, with focused tests):
- Separate named constants for the 5000 ms clock-offset limit and the 5000 ms observed-after-receipt allowance (values unchanged, disclosed in the read).
- `summary.reason`: `NO_ENABLED_GATEWAY` when only disabled gateways exist, `NO_REGISTERED_GATEWAY` when none; status stays `NO_REGISTERED_SOURCE`.
- Null `fact_age_seconds` and `reported_contact_age_seconds` when the clock is UNTRUSTED, and any individual age whose timestamp is later than `read_at` (never a negative age).
- Optional, if cheap: review L6 (battery detail checks the binding set names the selected Foundation revision; fail closed).

UI, per the rulings: label the summary "Gateway contact" with an enabled-gateway count (never "Site health" or equipment health); queue, disk, source contact and battery condition in separately qualified sections; DISABLED shown beside disabled gateways and excluded from counts; Unknown age plus the clock reason, never a signed age; battery condition UNKNOWN with its named missing inputs, or NOT_CONFIGURED. Mockup screens: Health and Asset.

Walkthrough (review L1, L4): registering the eight case gateways on KOBO-001 breaks S1's one-gateway binding check for later binding publishes, so use the walkthrough's own private DB and register case gateways after bindings exist; on the real clock several cases go STALE about 120 s after publishing, so give a `deliver` step that refreshes every case meant to read CURRENT, run it just before viewing, and have `attest` assert the stale-cadence case only after 60 s. Second Site (KOBO-002 / without battery) with printed URLs.

Environment: `.venv` junction to the main venv; set `PYTHONPATH` = this worktree's `backend;contracts;gateway;simulator` yourself (do not use the shared scratchpad `env.sh`); `ASSETOPS_GUARD_PYTHON` = `C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe`; Docker Postgres 127.0.0.1:55432, test URL `postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/<your base>_test` (create the base DB first with `docker exec assetopsv1-postgres-1 createdb -U assetops <name>`; drop afterwards). Several agents share this Postgres (100-connection limit) and ~4 GB of free memory: run focused tests serially, close every engine/pool your tests open, and before your one full suite check that no other `pytest` process is running and free memory is above 2.5 GB, else wait and recheck every 5 minutes. Keep-awake is running. Copy `var/sites/*.yaml` from `C:\Users\assef\Bineyame\AssetOpsV1\var\sites\` for the full suite/walkthrough; remove afterwards. Main's migration head is `0019_verification_core`.

**Owner presentation direction (2026-10-16, applies now):** product screens are for the people the system is built for, not its builders. Follow the v69 mockup for the named screen closely for layout and plain language; keep internal analytics, rule IDs, enums, model versions and IDs out of the default reading and put them in a dig-deeper disclosure. Do not spend fix rounds on wording (a W1-conclusion mockup-fidelity pass refines it), but add no new drift.

Proof at final revision: focused tests, `npx.cmd tsc --noEmit`, full `npm.cmd test` once (rerun any timed-out file alone and report both), registry checker, `tools/check-all.ps1`, ONE full backend suite if backend code changed (`pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=<abs>`, cap 30 min, zero failed/skipped). Run the owner walkthrough end to end yourself once (with an evidence script at 1440/390), then drop. Commit in logical steps; do not merge; do not touch `.agent/coordinator-handoff.md`. Write the review packet and owner steps for a non-developer (exact `cd` into this worktree, commands, ports, URLs, what to look for) - git add -f. If you approach your context limit, stop at a clean commit and write a partial handoff naming the resume point. Report concisely.


Outputs: `.agent/S7-01b-review-packet.md`, `.agent/S7-01b-owner-walkthrough.md`.
