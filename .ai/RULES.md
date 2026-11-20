# Rules

Project rules, workflow and standing owner rules in one place, deduplicated on
2026-11-18 from the former PROJECT_RULES, WORKFLOW and ROLE_CONFIG (full text:
`.ai/history/`). Authority order and mock authority: `.ai/START_HERE.md`.
Bindings: `.ai/ROLE_CONFIG.md`.

## 1. Protected seams

- The simulator is not the product; private simulator truth never leaks into
  product evidence. AssetOps consumes Site and device evidence, not simulator
  internals. Scenario labels never become Site identity.
- Domain truth, published evidence, analytics and presentation stay separate.
- External and data contracts are strict at boundaries; dependency direction is
  deliberate and tested.
- Demo shortcuts never silently redefine product semantics. Data without a
  source is shown as "not available yet", never invented.
- If there is data in the selected range, every page shows output for that
  range, the same way for every Site type (owner, 2026-11-12).

## 2. Roles and lanes

- Planned lane: Architect or Planner -> Implementer -> Reviewer -> owner where
  required. Used for new behaviour, semantics, user-visible analytics,
  meaningful UI, contracts, boundaries, simulator or ingestion semantics.
- Fast lane: Implementer -> Reviewer, only inside an existing product and
  technical contract.
- Architect: structure, sequencing, seams, specs and rulings; it specifies
  schemas, APIs, rules, copy and fixtures up front, so implementers do not
  design. Planner: task definitions. Implementer: code, tests, checks, packet.
  Reviewer: independent review; never merges or fixes its own or reviewed work.
- Ambiguity: stop with `SPEC_AMBIGUITY` only when the choice changes product
  behaviour, semantics, a user-visible claim, a contract, a boundary, a seam or
  acceptance. Otherwise make the conservative local choice and note it.

## 3. Approvals and verdicts are controls

- No agent writes an owner approval anywhere (task file, packet, commit). Only
  the coordinator records owner words, against the named checkpoint, from a
  verbatim owner file.
- No agent records a review verdict; the coordinator does, after listing and
  reading every review file. Disagreement is reported, not resolved by
  preference.
- An implementer never commissions its own review. Nobody commits into a tree
  a reviewer is measuring.
- Owner text is relayed verbatim through a saved file, never paraphrased.

## 4. Workflow W1-W9 (D11, adopted by the owner 2026-11-18)

Source: rev 4.2 of `product-transition-and-roadmap.md` §5.2, kept at
`.ai/history/layer4-roadmap-rev4.2/product-transition-and-roadmap-rev4.2.md`.

- **W1 Structure first, owner-approved.** Per phase, the Architect writes the
  structure specification (factors and records, decisions and bounds, screens
  citing the mock, acceptance tests as questions the screens must answer)
  before any build or figure. The owner approves it in one sitting from a
  one-page summary and a figure. Figures are outputs, never targets.
- **W2 Independent checks first.** The phase's checker (independent model,
  golden records, anchors) is written and reviewed before the code or figures
  it checks, and shares no logic, list or expected figure with them.
- **W3 Decision queue with defaults.** Every open question gets the Architect's
  default, applied pending the owner's answer, in one queue. The owner answers
  in batches at structure approval and the phase-end walkthrough. No agent
  waits. New owner input during a round goes to the next round unless the
  owner says stop.
- **W4 Readiness dry-read, then small units in two lanes.** A fresh reviewer
  dry-reads the spec against the code before the build (every copy string,
  field, ID source, route, fixture producer, capture state, cap). Units are
  one to three commits. A slice over 6 units is split.
- **W5 Review depth matched to risk.** Discovery review (strongest fresh
  reviewer) for a new schema, mechanism, protected seam or any money figure.
  Verification re-review (lighter fresh reviewer) for named findings only.
  Mechanical check for merge preparation. A verification pass that finds
  something new is escalated to discovery.
- **W6 Fix classes, not instances.** Each finding is answered with its class,
  a recorded sweep over all code and documents, and the sweep's result.
  Reviewers check the sweep.
- **W7 Stop rule.** Two rounds in a row that each expected to be last and still
  find the same class: stop and take the pattern to the owner. More than two
  fix rounds on a slice: a fresh readiness pass before continuing.
- **W8 Human and real-data checkpoints where they decide something.** One owner
  walkthrough of computed screens per phase, not per slice. A replay on
  simulated data never stands in for the real-data checkpoint.
- **W9 Pilot calendar overlaps the build.** Data agreements start at M0; each
  step finishes before the pilot needs it.

Also standing: builders pre-flight a unit against `main` and the mock and batch
every open point into one Architect request before coding; after a ruling
round the Architect folds rulings into one current unit card.

## 5. Specs, slices and packets

- A slice delivers or directly unlocks a UI-verifiable outcome. A task spec
  states: outcome, why next, acceptance criteria, needed semantics, seams and
  exact checks, scope limits, `USER_REVIEW_REQUIRED`. It leaves factoring,
  helper names and test structure to the implementer. It cites durable
  documents instead of restating them. No minimum length; the binding part is
  at most 15k tokens, or the slice is split.
- Specs fix the known question classes before coding: identifier formats,
  fixture values, seams by path:symbol, guard allowlists, refusal codes, clocks
  (one per fixture), every user-visible string and its field, per-panel height
  caps sized from worst-case content, producible capture states.
- `USER_REVIEW_REQUIRED: true` when the slice affects direction, semantics,
  UI/UX, evidence interpretation, analytics or demo narrative. After a
  checkpoint, do not assume the next planned slice is still right.
- Review packet (at most 3k tokens; evidence by path): task, outcome, files
  changed, acceptance criteria one by one, checks run with real output, layout
  evidence when layout-sensitive (or `not run` with the blocking
  precondition), known deviations, residual risk, review focus.
- Closeout: the review outcome and status are recorded before merge, by the
  coordinator.

## 6. Mock fidelity

- The governing mock (`.ai/START_HERE.md`) is the layout spec. Every spec,
  ruling and review that touches a screen cites the mock element (screen,
  panel, row, column, chip) and keeps its form. A guard, file list or backend
  gap is never a reason to trim or redesign a mock element.
- An unavoidable departure is labelled `MOCK DEVIATION` with one category, and
  gets a row in `.agent/mock-departure-register.md`: D1 data or feature not
  available (honest gap inside the mock's structure); D2 improvement (flag to
  the owner); D3 structural oversight (a defect: fix before merge; High); D4
  mock placeholder content (real data or honest gap); D5 temporary, build
  order (name the resolving unit); D6 technical constraint (rare; list
  alternatives). An unlabelled departure is High.
- UI quality bar: current practice (WCAG 2.2 AA, Material 3, HIG, GOV.UK,
  Carbon, NN/g), strong 390 px behaviour, purposeful loading/empty/error
  states, plain client-facing copy without system vocabulary; within demo
  speed. Defaults: `frontend/docs/architecture/ui-ux-decision-guide.md`.

## 7. Tests, guards and the machine

- Tests: `backend/TESTING.md`. Focused and adjacent files while building;
  `python tools/select-tests.py --base main` picks the slice-end set. Full
  suites only when the owner asks (owner rule from the demo sprint, still
  applied): if asked, one at a time, on a quiet
  machine, with `tools/keep-awake-during-tests.ps1` started and a cap of twice
  the expected wall time (stop and report past the cap). Never a bare
  `docker compose up` for tests.
- Guards: `pwsh -NoProfile -File tools/check-all.ps1`, plus
  `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1`; never
  with an execution-policy override. A guard you add must be shown to fail on
  a real violation.
- Databases: only `*_test` and `<prefix>_audit*` databases in
  `assetopsv1-postgres-1`; never others. Drop your own when done.
- Walkthrough and demo (owner): never touch port 5490 (walkthrough server,
  `/opt/assetecon/AssetOpsV1-walk`) or Docker during task work; never write
  to the walkthrough DB except through its own serve; port 8990 (uvicorn
  `lab_app`) is not ours, leave it alone. Walkthroughs run only on a clean,
  good DB; no fallback DB.
- Keep `var/sites` and the Lab data intact. Do not switch branches in a
  checkout while an agent is working in it.
- A unit that touches shared code or schema is reviewed before the next unit
  builds on it. An implementer choice the spec did not fix is a spec defect:
  raise it, don't decide it.
- Processes: stop every process you start, by PID only; never kill by image
  name or a broad pattern, never all browsers. Long jobs: `setsid nohup`.
- Line endings: before a full suite, list LF-pinned files checked out as CRLF
  (`git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'`) and re-check
  them out.

## 8. Git

- Never work on `main`; one branch (and worktree) per slice. One agent edits a
  worktree at a time; evidence measured while another agent held the tree is
  not evidence.
- Focused commits; stage by explicit path. Never `git add -A`, `git add .` or
  `-f` on a directory; `git add -f` only on a named `.agent/` file. Check
  `git diff --cached --stat` before committing.
- Do not discard others' changes. Merge `main` into a branch; do not rebase
  published history.

## 9. Keep the repo tidy

- **Where agents write.** Agent scratch and session transcripts: the session
  scratchpad or `.agent/` (git-ignored). Packets, reviews, rulings and owner
  files stay where they are today until declutter steps 2 and 4 give them
  indexed homes; `.ai/NOW.md` will say when that changes.
- **Evidence (owner O3, 2026-11-18).** Generated evidence (screenshots,
  captures, audit JSON, logs) goes outside the repo, under
  `/opt/assetecon/evidence/<task>/<run>/`, and is kept for 2 weeks, then
  deleted. A packet cites the run by path with a 5-10 line summary. Evidence is
  never committed, except a deliberate test fixture under a fixtures folder.
  Existing in-repo evidence moves in declutter step 3; until then, files that
  code or tests read stay in place. To confirm: whether the 2 weeks run from
  capture or from slice acceptance.
- **Caps.** AGENTS, START_HERE, NOW: 1.5k tokens each. ROLE_CONFIG: 3k.
  RULES: 4k. A role brief: 1.5k. An index: 2k. A task spec's binding part: 15k.
  A packet: 3k. A review round: a summary of at most 15 lines plus findings.
  The coordinator handoff: one current block of at most 2k, replaced.
- **Find on demand.** Read the router, then open only the sections the task
  names, by ID or heading. Grep scoped to current homes, never `.agent/`,
  `archive/`, `history/` or evidence folders. No brief says "read X fully" for
  a file over 15k tokens.
- **Supersession.** Whoever supersedes a document adds a header ("Superseded by
  X, date") and moves it to an archive or history folder in the same change,
  and updates `.ai/START_HERE.md` if authority moved.
- **No new process artifacts** (guide, role, checklist, handoff category)
  unless the same need appeared in two tasks or the owner asks.
