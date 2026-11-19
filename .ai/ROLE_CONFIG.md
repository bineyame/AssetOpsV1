# Role Configuration

Roles are responsibilities; agent bindings are configurable defaults. Change a
binding here, and record a material change as a decision. Ended exceptions,
the Codex-era history and the long rationale behind each rule below are in
`.ai/history/role-config-history-to-2026-11-18.md`.

## Bindings

| Role | Bound agent | Purpose |
| --- | --- | --- |
| Architect | Claude: a fresh `assetops-architect` subagent (owner, 2026-10-27) | Structure, rulings, sequencing, protected seams, specs |
| Planner | Codex, run by the coordinator with `codex exec` | Turns reviewed guidance into small, UI-verifiable task definitions |
| Implementer | Claude: a fresh `assetops-implementer` subagent per build or fix round | Builds the active unit, runs checks, writes the packet |
| Reviewer | Claude: a fresh `assetops-reviewer` subagent per slice review and re-review. Codex: one batched review per milestone, retrospective when quota allows; never block on Codex | Independent review |

The Reviewer is always a new instance, never the author and never the author
resumed. State in every review which reviewer produced it.

## Running a Codex-bound role

- The coordinator runs Codex itself:
  `codex exec "<brief>" < /dev/null`. Always close stdin; pass the prompt as an
  argument; background the call once, not twice.
- Resume a returning session rather than starting cold:
  `codex exec resume -c sandbox_mode="workspace-write" --skip-git-repo-check <session-id> "<prompt>" < /dev/null`
  (options before the id; `--sandbox` does not exist on `resume`).
- Codex quota is account-wide; changing model does not route around it. Batch
  questions into one call, and state in the brief what is already verified.
- A Claude subagent named for a Codex-bound role refuses that work and says
  the coordinator should run `codex exec`.

## Decision routing

- Decision requests go to the active Architect, which decides, records the
  decision with its reasoning, and informs the owner; it says when it wants
  the owner to weigh in. Owner acceptance of a slice is not a decision request.
- When the owner is away and has delegated, the Architect decides and each call
  is logged for owner review; reviews still gate merges.
- Options put to the owner include what the owner already asked for (check the
  `owner/` files first), and a workaround is called a workaround.
- A contest within 5% between the top two candidates goes back to the owner.

## Dispatch rules (coordinator)

- **Model by work.** Opus (session model): pre-flights, first builds of a unit,
  discovery reviews, Architect rulings. Sonnet: continuation builders working
  from a precise handoff, fix rounds against a written list, merge preparation,
  re-reviews of named findings, mechanical sub-steps.
- **One Architect per lane**, reused with SendMessage until its context is
  moderate; batch a lane's questions into one message.
- **Implementers are fresh per build and per fix round**, never resumed. Size a
  run to one to three commits; a phase ends with a commit and a handoff
  (`<unit>-handoff.md`: done, next, anchors, live DBs and processes). An
  implementer near 120k context commits, writes the handoff and stops.
- **Briefs point to files; they do not restate them.** Name the exact sections
  to read. All acceptance rules are in the brief from the start; none is added
  mid-build.
- **Do not write the review in the brief.** A reviewer brief gives the target
  (branch, commit, spec, packet, prior reviews), what has already been run with
  results, and the constraints (no merge, no fix, where to write). It never
  lists what to judge, argues a conclusion, or hints at an outcome.
- **Sort findings before forwarding them.** Block only for a defect expensive
  to reverse, a claim that would mislead an implementer, a decision only the
  owner can take, or a High/Medium finding. Everything else is carried, with
  the reason, not sent back as fix work.
- **No duplicate agents.** Check for a live agent on a worktree before
  dispatching; never reuse a worktree a reviewer is still using. Serialise
  units that edit the same shared UI files; parallelise disjoint work.
- **Short reports.** Builders reply in 10-15 lines; detail lives in the packet
  or handoff. Coordinator replies to the owner in a line or two on routine
  events.
- **Coordinator session restarts at natural pauses**, from a refreshed
  `.agent/coordinator-handoff.md` (one current block, replaced, not appended).

## Updating bindings

Change the table above; keep responsibilities stable. A Claude subagent's
brief must not hard-code a binding: it reads this table.
