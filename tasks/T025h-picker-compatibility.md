# T025h - Compatibility status per site in the run-setup picker (S1b)

Status: parked
USER_REVIEW_REQUIRED: true

Map: A/B hardening; scenario-site contract S1b. Depends on: T025g, T026.
Parked under `D-2026-10-02-demo-led-recommendation` (recommendation 6.3,
6.5): not before T029, or in a Lab-ergonomics bucket with the carried delta
p95 task. Gates nothing.
Branch: task/T025h-picker-compatibility
Sizing: one focused boundary-changing slice (one shared resolution step, one
gated read-only route, its client, the picker rows); no phases.
Planner: Claude under `D-2026-09-30-planner-claude-until-reset` (Planner bound
to Claude until the Codex reset 2026-10-03 21:23).

## Outcome

Open run setup for a shipped scenario and choose both profiles: every row of
the site picker now says what Create would give for that site with the form as
it stands - Ready, Blocked with the reasons on expand, or cannot be set up with
the refusal statement. With `mini-grid` v3 and publication profile 5, a site
built from Kobo template v3 reads Ready and a site built from v2 reads Blocked,
with the same reasons a Draft created against it records. Nothing is
preselected, every row stays selectable, and no Draft exists until Create.

Why now: since T025g the user only learns a site cannot honour a scenario after
creating a BLOCKED Draft; with three template versions in the field after T026
that is guesswork per site. Rule: `D-2026-10-01-run-binds-scenario-to-site`
("T025h ... a dry-run of the same setup resolution, never a second matcher").

## Read for detail

- `D-2026-10-01-run-binds-scenario-to-site`; `.agent/scenario-site-targeting-architect.md`
  section 3, "The site picker when nothing is pre-selected", and section 4, S1b.
- CODE_STATE `T025g` (picker, run setup) and `T026` (template v3, profile 5).
- `backend/assetops_backend/runs/service.py` `RunSetupService.create_draft_run`;
  `frontend/src/shell/RunSetupFrame.tsx` `SitePicker`.

## Acceptance criteria

1. **One resolution.** Run setup's existing path from request to decision
   (parse, resolve, refusals, freeze, decide) is one step that both Create and
   the dry-run call. Create is that step plus run-id allocation and the write;
   the dry-run is that step alone. No compatibility rule exists anywhere else,
   backend or frontend: the screen never derives a status from site, template
   or profile data.
2. **Same answer.** For the same request, the dry-run's outcome equals what
   Create gives: READY, or BLOCKED with the same blocking reasons in the same
   order, or the same refusal code and statement. Proven by tests that run both
   on the T025g join fixtures (current Kobo READY, pre-T025a content BLOCKED),
   on a T026 case (a pre-v3 site under `mini-grid` v3 and publication profile 5,
   whatever Create gives there), and on a no-topology site (refused).
3. **No side effects.** A dry-run allocates no run id, writes nothing to the run
   store, the stage or Lab history, and leaves the run inventory unchanged.
   Proven by a test against the run store, not by inspection.
4. **Gated, read-only route.** The dry-run is served under the Lab gate (closed
   gate: route absent, as for the other Lab routes) and takes the setup request
   without the site, or per site; the shape is the Implementer's. Malformed
   requests are refused as Create refuses them. One site that cannot be read or
   evaluated yields a per-site "could not be checked" answer and does not hide
   the other sites' answers. The route lands in the same commit as the client
   that validates its payload.
5. **Status per row.** With both profiles chosen and the form complete enough
   to be a request, each picker row shows one of: Ready; Blocked (n) with the
   blocking statements on expand; cannot be set up, with the refusal statement;
   could not be checked. Before both profiles are chosen, or while the form is
   not yet a request, rows show no status and one line says what is missing.
   Status text reads as a preview of Create ("if you create the draft now"),
   not as a property of the site.
6. **Honest while inputs move.** A shown status always belongs to the current
   scenario version, profiles, interval, seed and run inputs. When any of them
   changes, earlier statuses are withdrawn (or marked as checking) until the
   new answers arrive; a late answer for older inputs is never shown as
   current.
7. **No choice made for the user.** Nothing is preselected, no row is disabled
   (Blocked and refused rows stay selectable, per T025g), and rows keep the
   store order (see open question 1). Create re-runs setup and never reuses a
   dry-run answer; if the outcome differs (the site changed meanwhile), the
   Draft is what it is.
8. **Existing row content stays.** Foundation version, template lineage and
   T025f's staleness note remain on each row; the picker still works, without
   status, when the dry-run route fails as a whole, and says so once.

## Protected seams and proof

- The run is the only join; the dry-run joins nothing durable
  (`D-2026-10-01-run-binds-scenario-to-site`). The scenario domain and the
  scenario detail screen still read no site (T025g AST guard unchanged);
  compatibility appears only in run setup, where profiles are chosen.
- **Contract stays 9.** Nothing that is frozen, hashed into
  `frozen_inputs_identity` or replayed changes; `host/tests/contract9_gate` is
  unedited and green.
- Persisted runs and Lab history are not re-resolved on read
  (`D-2026-09-30-lab-cockpit-history`).
- Proof: the shared checks in `tasks/README.md`, the backend, host and frontend
  suites (serially, per T025e's C9 note), AC2/AC3 tests, and populated layout
  evidence for run setup at the supported widths with at least one Ready, one
  Blocked (expanded) and one refused row, against an isolated or copied `var/`
  holding a v3-template site, a v2-template site and a no-topology site.
  Record the time from the last input change to all rows answered on that
  store in the packet.

## Scope limits, stops and review

Not here: purpose assumptions and their label (T025i); ranking or filtering
by template lineage (rejected by the decision); a site summary field to avoid
one site read per row (backlog, T025g); the AC15 performance carry. No edit to
`var/` data.

Stop and report to the Architect if:

- the dry-run cannot share Create's step without changing what is frozen or
  its identity (that would move the contract);
- equivalence (AC2) needs a second code path for any refusal or reason;
- a full picker evaluation on the owner's store is too slow to be usable and
  only caching or memoisation would fix it (cache invalidation is a seam
  question, not a local choice).

Open questions for the owner (defaults in force until answered; neither
blocks starting):

1. **Order.** The Architect allowed "compatible sites first; ordering is
   presentation". Default here: store order, so rows do not jump while
   statuses load. Owner may ask for Ready-first at review.
2. **Status words.** "Ready", "Blocked (n)", "Cannot be set up", "Could not be
   checked" are working copy; the third and fourth are not in the Architect's
   list (it named Ready and Blocked only) but are real outcomes of setup. Owner
   reviews the copy hands-on.

Pending ruling, parked with the task: does the picker status depend on the
whole form, or only on scenario and profile? It waits until this task is
scheduled, and is the owner's or Architect's to make then, not the Planner's.
The recommendation's view (6.3): "the whole-form reading is the honest one: a
preview of Create must depend on everything Create reads".

Review: planned lane. A fresh Claude reviewer reviews when ready (Codex
retrospectively after its reset, `.ai/ROLE_CONFIG.md`). The owner then checks
hands-on that the picker's status for each site matches the Draft Create
gives, with nothing chosen for them.
