# Coordinator handoff (2026-10-02)

The previous coordinator session ended here to save Claude usage. A fresh
coordinator starts from this file; do not re-derive what it states.

## Where things stand

- `main` has T025e, T025f and T025g merged (last merge `3bbcf65`). Nothing is
  pushed.
- Branch `task/T026-dispatch-capable-evidence` is checked out. It holds the T026
  refresh (`37a0e1e`), the Architect rulings (`bcdbbe5`) and the owner's
  sign-off on `D-2026-10-02-template-bump-record`, plus this file.
- T026 is planned and ready to build. The build has not started.

## Next action: start T026 phase 1

Dispatch a **fresh `assetops-implementer`** for **phase 1 only** (contract and
gateway, AC1-9 and AC11-12), on `task/T026-dispatch-capable-evidence`. Brief it
to read:

- the task file's Preconditions, Named stops and Phases sections, and AC1-9 and
  AC11-12;
- `D-2026-10-02-delay-is-a-reporting-path-cause`;
- `D-2026-10-02-template-bump-record`.

Phase 1 ends with committed work and `.agent/T026-phase-1-handoff.md`. That
handoff states the contract-version reading and the measured stage size and
per-step write cost at the 8 h window. Then dispatch phase 2, then phase 3,
each with a fresh implementer working from the previous handoff.

## Owner rulings in force (do not re-ask)

- **No review waits for Codex.** A fresh Claude reviewer reviews now. Codex
  reviews retrospectively after its reset: T025e, T025f, T025g and T026 so far.
- **Contract stays at 9.** Each move-forcing item listed in Named stops is a
  stop for the Architect and owner.
- **Template v3.** `kobo-mini-grid-60kw` goes to v3 in T026 for the PV and BMS
  capability signals. `supersedes` and valid-from apply to scenarios only
  (signed off 2026-10-02).
- **Delayed publication** is a scenario cause the publication profile must be
  able to model. If it can't, run setup blocks and names the profile. A delay
  that would reorder publications is refused at setup.
- **Append-only stage is not pre-decided.** If phase 1 measures the stage over
  budget, the fallback is fewer writes. Only if that still misses does it stop
  for the owner.
- **The owner's hands-on site.** The T026 hands-on check needs a site the owner
  creates from template v3. GONDAR-01 (v2) and KOBO-001 (pre-T025a) cannot
  show it. No agent creates or edits anything in `var/`.

## Claude usage rules (owner priority)

Follow `.ai/ROLE_CONFIG.md`, "Using The Claude Implementer Efficiently":

- a fresh agent per phase and per fix round, never a resumed one;
- fix rounds run on Sonnet;
- bounded reads;
- suites run serially;
- briefs state the facts already verified;
- reviewer briefs never enumerate what to judge.

Sort review findings into block or carry before forwarding anything to the
owner. Keep reports to the owner short.

## Scheduled

- **2026-10-03 21:23, Codex reset.** Revert the three temporary Claude rows in
  `.ai/ROLE_CONFIG.md` (Architect, Planner, Reviewer) back to Codex. Then queue
  the retrospective Codex reviews listed in its "Nothing waits for Codex"
  paragraph and add T026 to that list.
