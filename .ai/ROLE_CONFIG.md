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

- **Token budget (owner, 2026-11-20: "it appears cladude usage is not efficient, fix that").**
  - At most 4 agents running at once; a new dispatch waits for a slot.
  - No agent is resumed past about 300k context: an Architect or builder that large hands
    off and the next task goes to a fresh agent with a short brief.
  - Opus only for first builds, discovery reviews and Architect rulings; Sonnet for
    handshake questions on units of 2 or fewer, fix rounds, verification re-reviews,
    bookkeeping and merges.
  - Briefs at most about 25 lines: the target, the files to read by path, the
    constraints. They never restate the spec or list what a reviewer should judge.
  - Reviewers cite the builder's gate run at the same commit and rerun only what a
    finding needs; screenshots only for screen work, a lean set.
  - Every hand-back at most 15 lines; detail goes in the packet or review file.
  - The coordinator does not answer "still waiting" notifications, and keeps owner
    updates to what changed and what is asked.

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

- **Usage rules from the 22 Nov audit (owner: "fix any usage issues and make sure they
  don't reappear via standing rules").** Each line is a failure that cost a round.
  - **Brief footer, pasted verbatim into every builder and reviewer brief:**
    "Run commands from the worktree ROOT with repo-relative paths. Postgres tests: ONE call
    `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <files>`; vitest only via
    `tools/heavy-slot.sh`; architecture guard with
    `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`, and `tools/checks/statement_catalogue.py` (exit 0, or output identical to main). A queued heavy slot is
    waited on, never a reason to stop. Delete only files you created, never a directory under
    /tmp/claude-1001. No background job or preview server left running at hand-back."
  - **Test scope before hand-back:** a builder runs the whole test directory or module its diff
    touches (frontend: all of each touched `src/<area>`; backend: every test file importing a
    touched module), and compares failures against main at the same time. "Pre-existing"
    must cite main's run, not memory.
  - **Rulings that change shared behaviour** (a service, role set, contract, shared UI part)
    name every Site type and role set it reaches and require a parity test (golden from main)
    for the ones meant to stay unchanged.
  - **Model coverage before design:** a spec Architect first checks that the model (levers,
    structures, factors, records) covers every Site type the work shows. A gap is fixed in the
    model, or put to the owner labelled WORKAROUND; it is never bridged in code silently.
  - **Coordinator merge check:** before every merge, run check-decision-index, check-agent-workflow and `statement_catalogue.py` on the merged tree (6c and 6h each broke the catalogue on main unseen).
  - **Coordinator housekeeping:** stop an agent's leftover background work (TaskStop) as soon
    as its hand-back is in; check `tools/heavy-slot.sh --status` before dispatching DB-heavy
    work alongside another; merge dependent branches in order and check a long-running agent's
    log at about 60 minutes instead of waiting blind.
  - **Briefs stay within the rules above:** at most about 25 lines plus the footer; a reviewer
    brief gives target, prior results and constraints, never a list of what to judge.

## Updating bindings

Change the table above; keep responsibilities stable. A Claude subagent's
brief must not hard-code a binding: it reads this table.
