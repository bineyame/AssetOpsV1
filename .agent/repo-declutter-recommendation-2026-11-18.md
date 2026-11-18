# Repo declutter recommendation (2026-11-18)

Author: independent Architect (Claude), read-only assessment. Request: `.agent/owner-repo-declutter-request-2026-11-18.md`, including the follow-up "agent context window and efficency is also a big factor to consider", which this document treats as a primary criterion alongside correctness and organisation.

Nothing has been moved, deleted or committed. Measurements were taken on `task/product-direction-layer4-design` at `0dd950ffd` on 2026-11-18. Token figures are bytes / 4, which is an approximation.

---

## 0. Summary

1. **The agent entry path points at a project state that is six weeks old.** `.ai/START_HERE.md` (last changed 2026-10-07) says "Current milestone: S1 Foundation. S1-01 is ready for implementation." `tasks/README.md` (2026-10-24) calls itself "the only executable queue" for S1–S7. All four role briefs send agents to the three Site-first documents and the v6.9 mock. None of them mentions the demo sprint, the SR/DATA/WALK work since 2026-11-01, or the Layer 4 direction (`Docs/demo-sprint/product-direction-layer4/`). An agent that follows the documented path reads stale authority first.
2. **The Architect brief contradicts the binding.** `.claude/agents/assetops-architect.md` and `.claude/skills/assetops-architect/SKILL.md` both say "Default binding is Codex"; `.ai/ROLE_CONFIG.md` says Claude (owner, 2026-10-27). The brief's "refuse and stop" control then depends on the agent reading 12k tokens of ROLE_CONFIG to find the right row.
3. **Default context is large and mostly stale.** If followed literally, each role's start path loads about 35k–60k tokens before the task itself, or about 135k–160k once the v6.9 mock and manifest are included (§1.2). Roughly 60–75% of the fixed portion is stale status, ended exceptions or superseded direction. Build sheets, which are the actual task specs since W2, are up to 684 KB (about 171k tokens) each, larger than an agent's working context.
4. **`.agent/` is 1.7 GB and 24,395 tracked files, even though `.gitignore` line 1 is `.agent/`.** Every file was force-added. 16,903 are PNG captures and 2,329 are `.log`/`.err`/`.pid` files. 104 raw `*-log.txt` session transcripts total 81 MB. It holds four different kinds of material: live state (coordinator handoff, owner feedback), the de facto spec and decision register (build sheets, architect answers containing D-E5.xx and D-SR.xx), review history, and bulk generated evidence. A grep of `.agent` returns hits from about 5.4M tokens of markdown.
5. **Decisions and specs have no single home.** `.ai/DECISIONS.md` (126k tokens) stops on 2026-10-31. Later decisions (D-E5.xx, D-SR.xx) exist only inside `.agent/architect-*.md`, build sheets, review files and `coordinator-handoff.md`. 28 files in `tasks/` are not listed in `tasks/README.md`, and no task file exists for any work after 2026-11-01.
6. **A source document for the current direction is untracked.** `.agent/AssetEcon_Product_Direction_Layers_1_to_3_and_Claude_Brief_REVISED.md` (108 KB) is cited by five Layer 4 pack files, but it is git-ignored and exists only in this checkout.
7. **Code and tests depend on `.agent/` in a few places**, so a blanket move would break them (§4.1). Code docstrings cite more than 580 `.agent/...` paths as design provenance.

**Recommendation in one line:** shrink the start path to a lean, current router (about 6–8k tokens per role), with one index per topic. Move live specs and decisions out of `.agent/` into tracked homes. Untrack bulk generated output (about 1.6 GB) and keep a manifest. Archive superseded planning documents behind a single "historical" pointer. Make `.agent/` a true scratch area governed by explicit write and retention rules. Do it in five reviewable PR steps, after the owner decides the direction questions in §6.

---

## 1. Findings, ranked by impact on agents

### 1.1 F1 (High): the entry path routes to superseded state

| File | Last changed | What it tells an agent | Reality |
|---|---|---|---|
| `AGENTS.md` | – | "For current S1-S7 work, use production-shaped-mvp*.md, site-first-execution-plan.md"; v69 mock | Work since November is the demo sprint (SR-, DATA-, WALK-, AP-, MB-, UP-), and the owner's direction is now Layer 4 |
| `.ai/START_HERE.md` | 2026-10-07 | "Current milestone: S1 Foundation"; "S1-01 is ready" | S1–S7 and W1–W6 have been built and merged |
| `.ai/ACTIVE_CONTEXT.md` (35 KB) | 2026-11-09 | 54 lines marked "`in_review`", from 2026-10-15 to 2026-11-09; "Next read" lists reviewer routes for S4-08, S6-02b, etc. | Most are merged; the latest coordinator state is in `.agent/coordinator-handoff.md` (2026-11-14), and the current Layer 4 work is not mentioned |
| `tasks/README.md` (42 KB) | 2026-10-24 | "This is the only executable queue" (S1–S7) | 28 task files are not listed; post-2026-11-01 work has no task files (build sheets in `.agent/`) |
| `.claude/agents/*.md`, `.claude/skills/*`, `.claude/commands/*` | – | v69 mock, S1–S7 docs; the Architect and Planner briefs say "Default binding is Codex" | The Architect is Claude (ROLE_CONFIG, 2026-10-27); v70, v71, v72 and the Layer 4 `interactive-mockup-vNEXT` exist |
| `.ai/ARTIFACT_INDEX.md` | 2026-09-27 | lists "Canonical" artifacts | Not maintained since September |

Contradictions an agent will hit:
- **Binding:** the Architect brief and skill say Codex; ROLE_CONFIG says Claude. The fresh Architect running this assessment had to resolve it by reading ROLE_CONFIG.
- **Mock authority:** the briefs say v69 and "Mock fidelity ... `frontend/mockups/v69/index.html`". v70 (2026-11-03, 13 MB) was used in DEMO-B ("v70 comparison"). The Layer 4 pack has its own `interactive-mockup-vNEXT` with a "mock-up approval gate" (`product-transition-and-roadmap.md` §2.7, D10). No document says which mock governs which work.
- **Architecture authority:** the three Site-first documents are called "accepted"/"current implementation authority". `product-transition-and-roadmap.md` describes a transition to an "economic decision loop" and a phased roadmap, but it does not state what it supersedes. This is owner decision O1 (§6).
- **Decisions:** `.ai/DECISIONS.md` is the documented decision log, yet ACTIVE_CONTEXT and code cite D-E5.29, D-E5.48, D-SR.80 and D-SR.81, which are found only in `.agent/` files.
- **Queue:** `tasks/README.md` says it is the only executable queue. The owner's later rule ("build everything; deferral list is a queue") and actual dispatch run through `.agent/coordinator-handoff.md` and build sheets.

### 1.2 F2 (High): default context per role is large and largely stale

These are the files each role is told to read before its task. The table has two parts: the fixed router and the S1–S7 architecture documents, then the v6.9 mock files, which the briefs say to "inspect".

| Item | Tokens (approx.) | Stale or duplicated share |
|---|---:|---|
| Auto-loaded: user MEMORY.md (outside repo, 50 memory files) | 2.0k | Several entries are sprint-era rules that have been superseded (e.g. "Batched S1 Codex review", "Story path before V-01", "Planner is Codex") |
| `AGENTS.md` | 0.35k | Its S1–S7 pointer is stale |
| `.ai/START_HERE.md` | 0.6k | Its status is 100% stale |
| `.ai/ACTIVE_CONTEXT.md` | 8.9k | About 90% stale (merged "in_review" lines, old reviewer routes) |
| `.ai/ROLE_CONFIG.md` | 12.0k | About 16% ended exceptions (lines 48–163). About 35% Codex invocation and reviewer routing, partly live. About 43% standing rules (token efficiency, build-spec gate, UI guidance), which are live but long-form |
| `.ai/PROJECT_RULES.md` | 1.3k | Mostly live |
| `tasks/README.md` (Planner) | 10.5k | About 90% historical S1–S7 gate narrative |
| 3 Site-first architecture documents | 21.9k | Superseded or still valid depending on owner decision O1 |
| `.claude/agents/<role>.md` | 0.4–2.2k | Its pointers are stale |
| **Fixed router subtotal** | **Architect ≈ 46k · Implementer ≈ 47k · Reviewer ≈ 35k · Planner ≈ 57k** | **≈ 60–75% stale or superseded** |
| v6.9 `index.html` + `screen-manifest.json` | 99k | Valid as a v69 reference; governing status unclear (O2) |
| **Subtotal including the mock** | **≈ 135k–160k** | |

Task-specific material comes on top of that:
- **Build sheets:** 54 files. The largest are `build-sheet-DIESEL-1.md` at 684 KB (≈171k tokens), `build-sheet-OWN-GAPS-2026-11-08.md` at 537 KB (≈134k), `build-sheet-DD-1.md` at 351 KB, and `W4-03-build-spec.md` at 259 KB. Rulings, pre-flight answers and closures accumulate in the same file, so later readers load every earlier round.
- **Built-state and decision logs:** `.ai/CODE_STATE.md` is 524 KB (≈131k tokens, 136 sections) and `.ai/DECISIONS.md` is 505 KB (≈126k, newest entries first and partly undated). The Implementer is told to read "the entries relevant to the active path" from CODE_STATE, but there is no index.
- **Layer 4 pack:** 2.45 MB of text. It includes `derivation-register.md` at 557 KB (≈139k), `REVIEW.md` at 309 KB (≈77k, 2,901 lines of review history), `REVIEW-response.md` at 121 KB, `layer4-transformation-design.md` at 174 KB (≈44k) plus the same content as HTML (188 KB), and a 235 KB traceability CSV. The pack has no short index that says which part a given task needs.
- **`.ai/MILESTONE_REVIEW_BACKLOG.md`** is 188 KB and `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` is 67 KB. Neither is on the path, but both are prominent in `.ai/` and agents grep them.

### 1.3 F3 (High): `.agent/` mixes four kinds of material and is force-tracked against its own ignore rule

- **Totals:** 24,395 tracked files and 1.72 GB in the working tree. 86 subdirectories hold 1.63 GB; the 2,280 root files hold 118 MB.
- **By type:** 16,903 png · 2,192 md · 2,012 json · 1,836 log · 459 err · 391 txt · 180 py · 124 mjs · 92 html · 74 sh · 34 pid.
- **Bulk generated evidence** (screenshots, capture JSON, run logs) accounts for about 1.6 GB. The largest directories are `post-W6-audit` (292 MB, 4,084 files, 2026-10-25), `post-W6-final-recapture` (272 MB, 4,191 files, 2026-11-07), `post-W6-W6-evidence` (253 MB, 3,915 files), `post-W6-shell-recapture` (84 MB), plus about 80 more `*-evidence`/`*-captures` directories. None is read by code except as noted in §4.1.
- **Raw agent session logs:** 104 `*-log.txt` files total 81 MB. Examples are `planner-W1-ux-log.txt` at 4.4 MB and `architect-W2-techdesign-amend-log.txt` at 4.1 MB. They are codex exec transcripts with no reference value beyond forensics.
- **Live specs and decisions** sit in the same root among 2,069 markdown files: 54 build sheets and specs, 520 `architect-*` files, 292 packets, 658 review files and 185 `owner-*` files. Code docstrings cite them. They are the de facto spec store, but `.gitignore` treats them as scratch.
- **Live coordination state:** `coordinator-handoff.md` (51 KB, multiple "RESUME STATE" blocks appended), `mock-departure-register.md` (read by a guard), the owner walkthrough notes (uncommitted change) and the owner request files.
- **The force-add pattern is fragile.** A new file is silently not committed unless someone uses `git add -f`. The Layer 1–3 brief is the proof: it was never committed (F6).

### 1.4 F4 (Medium-High): decisions and specs are fragmented

- **Decisions:** `.ai/DECISIONS.md` covers up to 2026-10-31. After that, the decision series (D-E5.xx, D-SR.xx, `DIESEL-1-R3*` rulings) lives in `.agent/architect-answer-*.md`, `architect-sequence-*.md`, build sheets, `*-ruling-*.md` and `coordinator-handoff.md`. No index maps decision IDs to files.
- **Task specs:** since W2, the binding spec is a `.agent/` build sheet, not a `tasks/` packet. `tasks/` has 112 root packets (newest 2026-11-01) and 14 archived. `tasks/completed/` is referenced but holds T-history.
- **Built state:** `.ai/CODE_STATE.md` is one 6,489-line file. Implementers append to it, and nobody summarises it.

### 1.5 F5 (Medium): `Docs/` holds superseded design generations without status markers

- **September design generations:** `Docs/simulator_design.md` through `_v4.md`, two `simulator-design-v*-alignment.md` files, three `multi-vertical-*` files, `mini-grid-demo-architecture-and-roadmap.md`, `lab-cockpit-proposal.md` and `queue-review-feedback-verbatim.md`, all dated 2026-09-11 to 09-30 (≈0.6 MB). None carries a "superseded" header.
- **Demo-sprint proposals:** `Docs/demo-sprint/*.html` holds 10 proposals from 2026-10-27 to 11-11 (≈1.6 MB). Two are versions of the same telemetry plan (`telemetry-integration-plan.html` and `-claude.html`). Their status (accepted, implemented, superseded) is not recorded.
- **v6.9 product PDF:** `Docs/Product/AssetOps_Integrated_Product_Experience_and_Canonical_Screens_v6_9.pdf` (1.3 MB) is the source of the v69 mock. It is legitimately historical.
- **Layer 4 pack:** this is the current direction. It has a working `__pycache__/` (untracked, fine), HTML twins of markdown documents (generated by `render_product_transition_html.py`; both tracked), and review history files that are larger than the documents they review.

### 1.6 F6 (Medium): a current source document is untracked

`.agent/AssetEcon_Product_Direction_Layers_1_to_3_and_Claude_Brief_REVISED.md` (108 KB) is cited by `product-transition-and-roadmap.md/.html`, `layer4-transformation-design.md/.html` and `REVIEW.md`. It is git-ignored (`.gitignore:1 .agent/`), so it exists only in this checkout. It is not in the 47 worktrees, any clone, or any backup.

### 1.7 F7 (Medium): `tools/` is half product guards and half one-off slice scripts

- **Live guards:** `tools/checks/` (501 files) is the live guard suite, and its 458 JSON files are fixtures. Keep it.
- **One-off scripts:** the 139 `tools/` root files include 49 one-off evidence, capture and probe scripts tied to finished slices (`s3-dispatch-evidence.mjs`, `s402b-fuel-cost-evidence.mjs`, `v01a-foundation-evidence.mjs`, `w1-ux-01-evidence.mjs`, ...). There are also slice-named subdirectories (`dd1a1/`, `dd1b2a/`, `w1/`, `w504/`, `s3/`, `s4/`, ...). Some are probably still used, such as `demo-combined-evidence.mjs` and `probe_kisiwa_fuel.py` (which feeds host tests). Usage needs a grep per file before anything moves.

### 1.8 F8 (Low-Medium): working-environment clutter

- **Worktrees:** there are 47 registered worktrees (`git worktree list`), many for merged fix branches (`fixboard`, `fixcoh`, `fixdd`, `fixe4`, `fixfr`, ...) and old `arch*` rulings. Each holds a full checkout, including its own 1.7 GB `.agent`. Agents searching `/opt/assetecon` see 47 near-copies.
- **Git history:** `.git` is 1.2 GB (pack 798 MB, 7,591 commits). Untracking files does not shrink history. Only a history rewrite does, and it carries high risk with 47 worktrees and running lanes (decision O5).
- **Mocks:** `frontend/mockups/v71` and `v72` are small (136 KB and 316 KB). Their purpose is not recorded next to them.

---

## 2. Target organisation

### 2.1 Principles

- **Router, not library.** The start path tells an agent where the current truth is, in fewer than 8k tokens. Everything else is read on demand, by pointer or ID.
- **One source of truth per topic**, each with a short index file (≤ 2k tokens) listing what exists, its status and its path.
- **History lives in git, not in the working tree's prominent places.** Superseded documents go to one `archive/` tree that agents are told not to read by default. Bulk generated output is untracked and kept outside the repo, with a manifest.
- **Size caps by file type** (§5), so no single file an agent must read can exceed a working context.

### 2.2 Proposed layout

```
AGENTS.md                      # 30-40 lines: what the product is, the 4 start reads, the "do not read by default" list
.ai/
  START_HERE.md                # router: current direction, current work pointer, authority order (<= 1.5k tokens)
  NOW.md                       # replaces ACTIVE_CONTEXT: active lanes only, one line each, each linking its spec (<= 1.5k tokens; history in git)
  ROLE_CONFIG.md               # bindings table + live rules only (<= 3k tokens); ended exceptions -> .ai/history/
  RULES.md                     # PROJECT_RULES + WORKFLOW + standing owner rules, deduplicated (<= 4k tokens)
  decisions/INDEX.md           # one line per decision ID: date, title, status, file
  decisions/<period>.md        # DECISIONS.md split by month; new D-E5/D-SR items get recorded here
  state/INDEX.md               # CODE_STATE table of contents: slice -> section/file, one-line summary
  state/<area>.md              # CODE_STATE split by product area (shell, sites, estate, work, data, host...)
  history/                     # FEATURE_MAP, ARCHITECT_DEMO_RECOMMENDATION, PLANNING_HANDOFF_*, MILESTONE_REVIEW_BACKLOG, ended ROLE_CONFIG exceptions
direction/                     # (or keep Docs/demo-sprint/product-direction-layer4/ and point at it; owner decision O1)
  README.md                    # the one product-direction index: current direction, what it supersedes, reading order by task type
specs/                         # build sheets moved out of .agent/ (live and finished), plus specs/INDEX.md
  <ID>/spec.md, rulings.md, review.md   # split per spec: the spec, then accumulated rulings, then review rounds
tasks/README.md                # short live queue; tasks/archive/ keeps the S1-S7 narrative
owner/                         # owner-*.md feedback, verbatim, tracked, plus owner/INDEX.md (date, topic, status)
Docs/                          # client- and product-facing documents; Docs/archive/ for superseded design generations
.agent/                        # scratch only: git-ignored, never force-added; per-session working files
  coordinator-handoff.md       # exception: tracked live coordination state (or move to .ai/coordinator.md)
evidence/ (untracked)          # or outside the repo, e.g. /opt/assetecon/evidence/<task>/; manifest in specs/<ID>/
```

Folder names are a proposal. The essential parts are:

1. A short router.
2. Tracked, indexed homes for owner feedback, decisions, specs and built state, outside the ignored scratch folder.
3. A separate archive.
4. Untracked evidence.

### 2.3 One source of truth per topic

| Topic | Single home | Index | Replaces |
|---|---|---|---|
| Product direction | the Layer 4 pack (if O1 = yes), with a 1-page `README.md` | pack README | Site-first documents as authority; `.ai/PRODUCT.md` (keep it as a glossary only, or archive it) |
| Architecture / platform contract | technical-design files named by O1; `.ai/ARCHITECTURE.md` boundaries if still valid | `START_HERE` authority list | conflicting "accepted" labels |
| Active work | `.ai/NOW.md` | itself | ACTIVE_CONTEXT, the coordinator-handoff resume blocks, the tasks/README narrative |
| Specs | `specs/<ID>/` | `specs/INDEX.md` | `.agent/build-sheet-*`, `*-build-spec.md` |
| Decisions | `.ai/decisions/` | `decisions/INDEX.md` | DECISIONS.md plus the decisions scattered in `.agent/architect-*` |
| Built state | `.ai/state/` | `state/INDEX.md` | CODE_STATE.md as one file |
| Owner feedback | `owner/` | `owner/INDEX.md` | `.agent/owner-*.md` (185 files, force-added) |
| Mock authority | one line in START_HERE per work type: which mock governs | – | "v69" hard-coded in 4 briefs |
| Role rules | ROLE_CONFIG (bindings) + RULES.md | – | the long ROLE_CONFIG, PROJECT_RULES and WORKFLOW together |

### 2.4 Where history lives: archive folder vs. deletion

| Option | For | Against | Use for |
|---|---|---|---|
| **Archive folder in the tree** (`.ai/history/`, `Docs/archive/`, `tasks/archive/`) | Visible and greppable; existing links can be repointed; low risk | Still in the tree, and agents will grep it unless told not to | Superseded planning and design text that people still cite (S1–S7 documents if superseded, FEATURE_MAP, simulator designs v1–v3, review histories) |
| **Delete, with git history as the record** | Cleanest tree; zero agent noise | Harder to find (requires `git log`); breaks citations unless redirected | Raw session logs, pid/err files, duplicate HTML twins of markdown, one-off probe scripts with no references |
| **Untrack and keep outside the repo** (git-ignored `evidence/` or `/opt/assetecon/evidence/`) with a manifest | Removes 1.6 GB from the tree; the files stay available | Not in clones or backups unless backed up separately | Screenshots, captures, audit JSON, recapture runs |
| **History rewrite** (filter-repo) | Shrinks `.git` by roughly 1 GB | Breaks every worktree, every open branch and every SHA cited in documents; needs all lanes stopped | Only if the owner wants the disk and clone speed back (O5); not needed for agent efficiency |

Default recommendation:
- Archive the text that people still cite.
- Untrack the generated bulk, with a manifest.
- Delete the raw logs (git keeps them).
- Do not rewrite history now.

### 2.5 `.gitignore` additions

```
# .agent/ stays ignored; stop force-adding into it (guard: tools/check-agent-workflow.ps1)
evidence/
**/*-captures/
**/*-evidence/
**/*-recapture/
*.pid
*.err
**/__pycache__/          # already covered; keep
Docs/**/*.html.tmp
```

Also add a guard check: fail if any tracked path under `.agent/` exists other than an allow-list such as `coordinator-handoff.md`, if that file stays there. Fail if a tracked PNG lies outside `frontend/mockups/`, `frontend/public/`, `Docs/` or test fixture directories.

---

## 3. Action list

Before any move, run `grep -rn '<path>'` across the whole tree, including code docstrings, `frontend/src`, `tools`, `host/tests`, `backend/tests`, `.claude`, `.ai`, `Docs` and `tasks`. Moved files keep their name, and a one-line redirect stub stays where a code citation points (see §4.3).

### 3.1 Keep (do not touch)

- **Owner and walkthrough files:** every `.agent/owner-*.md` file (185), verbatim. They may be relocated later (step 4) with `git mv` only, and never edited. The uncommitted `.agent/owner-walkthrough-notes-2026-11-01.md` and `.agent/owner-repo-declutter-request-2026-11-18.md` must not be touched until the coordinator commits them.
- **The walkthrough worktree** `/opt/assetecon/AssetOpsV1-walk` and its `var/` data, plus every other worktree's working state.
- **Active branch work:** `Docs/demo-sprint/product-direction-layer4/**` (an Architect is committing there now) and `.agent/coordinator-handoff.md`.
- **Runtime and test dependencies on `.agent/`** (§4.1): `mock-departure-register.md`, `W1-UX-combined-owner-walkthrough.md`, `DIESEL-F0/`, `DIESEL-D0/`, `W3-02-evidence/` (written and read by the frontend estate tests) and `W5-F1-evidence/`.
- **Product code and guards:** `tools/checks/**` (guards and fixtures), `tools/check-all.ps1`, `tools/select-tests.py`, `tools/validate-test-selection.py`, `tools/check-agent-workflow.ps1`, and all of `backend/`, `frontend/src/`, `host/`, `simulator/`, `gateway/`, `config/`, `contracts/`, `contract-fixtures/`, `field/`.
- **Mocks and source PDF:** `frontend/mockups/v69`, `v70`, `v71` and `v72` stay in place. Record their status instead (O2). `Docs/Product/*v6_9.pdf` stays as the mock's source.

### 3.2 Update (content edits, small)

| Path | Change |
|---|---|
| `AGENTS.md` | Rewrite to about 35 lines: product in one line, four reads (START_HERE, NOW, ROLE_CONFIG, the active spec), a "do not read by default" list (`.ai/history/`, `archive/`, `.agent/`, evidence), and "find on demand" pointers (decisions, state and specs indexes) |
| `.ai/START_HERE.md` | Replace the S1 status with: current direction (per O1), authority order, which mock governs which work (O2), pointers to NOW and the indexes. Budget ≤ 1.5k tokens |
| `.ai/ACTIVE_CONTEXT.md` | Replace with `.ai/NOW.md` (or rewrite in place): active lanes only. Remove the 54 historical "in_review" lines and the old "Next read" routes; git keeps them |
| `.ai/ROLE_CONFIG.md` | Keep the bindings table and live rules. Move the ended exceptions (lines 48–163) and the Codex-era history to `.ai/history/role-config-history.md`. Condense "Using Codex Efficiently", "Using The Claude Implementer Efficiently" and "Token Efficiency" into rules of ≤ 1 page. Target ≤ 3k tokens |
| `.claude/agents/assetops-architect.md`, `assetops-planner.md`, `.claude/skills/*/SKILL.md`, `.claude/commands/*.md` | Fix the binding text to match ROLE_CONFIG, or remove binding text from briefs and say "check ROLE_CONFIG bindings table". Replace hard-coded S1–S7 and v69 pointers with "follow START_HERE". Keep the mock-fidelity rule, worded per O2 |
| `.claude/agents/assetops-implementer.md`, `assetops-reviewer.md` | Same pointer fix. Move the sandbox/Windows troubleshooting (reviewer lines about `Access is denied`) into a referenced note if it is still relevant on the VPS |
| `tasks/README.md` | Short live queue (or a pointer to NOW + `specs/INDEX.md`). Move the S1–S7 narrative to `tasks/archive/site-first-2026-10/README.md` |
| `.ai/ARTIFACT_INDEX.md` | Delete it, or regenerate it as the master index of indexes |
| `Docs/demo-sprint/*.html` (10 proposals) | Add a one-line status banner (accepted / implemented / superseded by X) via a small `Docs/demo-sprint/INDEX.md` rather than editing each file |
| User memory `MEMORY.md` (outside repo) | Owner/coordinator review: retire superseded sprint-era entries. It is auto-loaded into every coordinator session |

### 3.3 Consolidate

- **`.ai/DECISIONS.md`:** split it into `.ai/decisions/<YYYY-MM>.md` and add `decisions/INDEX.md`. Extract the D-E5.xx, D-SR.xx and ruling IDs from `.agent/architect-*`, `*-ruling-*`, build sheets and the coordinator handoff into index lines that point at their source (no rewriting).
- **`.ai/CODE_STATE.md`:** split it by area into `.ai/state/`, with `state/INDEX.md` (slice → file#section, one-line summary).
- **`.ai/PROJECT_RULES.md` + `.ai/WORKFLOW.md` + standing ROLE_CONFIG rules:** merge into `.ai/RULES.md` and remove duplication.
- **Build sheets** (`.agent/build-sheet-*.md`, `*-build-spec.md`, 54 files): move each to `specs/<ID>/` and split large ones into `spec.md` (the current binding text), `rulings.md` (pre-flight and closure history) and `review.md`. Add `specs/INDEX.md` with status. Code citations stay valid through redirect stubs or a citation map (§4.3).
- **Layer 4 pack:** add a pack `README.md` (≤ 1.5k tokens) giving reading order by task type: the owner reads the roadmap, a builder reads the structure spec plus the specific contract file, a reviewer reads `REVIEW.md` latest round only. Split `REVIEW.md` and `REVIEW-response.md` into `reviews/round-NN.md`, keeping the latest round summary at top. Treat `derivation-register.md` (139k tokens) and `outcome-lever-capability-traceability.csv` as lookup files: say so in the README and never list them as reads. Mark the `.html` twins as generated (rebuildable from the `.md` with `render_product_transition_html.py`). Coordinate this with the pack's author after the current branch merges.
- **Telemetry plans:** reduce the two telemetry integration plans to one current file plus an archived one.

### 3.4 Archive (git mv to an archive folder, with a header line "Superseded by X on date")

- **From `.ai/`:** `FEATURE_MAP.md`, `ARCHITECT_DEMO_RECOMMENDATION.md`, `PLANNING_HANDOFF_LAB_COCKPIT.md`, `PLANNING_HANDOFF_T020A_T023.md`, `MILESTONE_REVIEW_BACKLOG.md` (if no open items remain; check first), `COORDINATOR_LOOP.md` (if replaced by RULES), and `PLANNING_GUIDANCE.md` (the briefs already call it "historical method"). All go to `.ai/history/`.
- **From `Docs/`:** `simulator_design.md` to `_v3.md`, the two alignment documents, the three `multi-vertical-*` documents, `mini-grid-demo-architecture-and-roadmap.md`, `lab-cockpit-proposal.md` and `queue-review-feedback-verbatim.md` go to `Docs/archive/2026-09/`. Keep `simulator_design_v4.md` and `simulator-scenario-authoring-and-runtime.md` in place if the simulator still follows them (check `simulator/` docstrings first).
- **Conditional on O1:** the three Site-first documents and `s1-01-foundation-contract-addendum.md` go to `frontend/docs/architecture/archive/`. The `v69-*.json`/`.cjs` registries stay, because guards use them (`check_v69_*`, `mock_gaps.cjs`, `delivery_next_work.cjs`).
- **Tasks:** packets in `tasks/` whose slices are merged go to `tasks/completed/` or `tasks/archive/`, leaving only open packets at the root.
- **Review, packet and handoff markdown:** `.agent/*-review*.md`, `*-packet*.md`, `*-handoff*.md` and `architect-*` answer files whose slice is merged move to an archive tree. The proposed target is `specs/<ID>/` if consolidated, otherwise `archive/agent-history/`, which is tracked but excluded from default reads. Archiving here means relocating them out of the default grep path.

### 3.5 Delete or untrack

| What | Count / size | Action | Reason |
|---|---|---|---|
| `.agent/**/*.png` and capture/evidence/recapture dirs (except the §3.1 test dependencies) | ≈ 16.9k files, ≈ 1.6 GB | `git rm --cached`, after copying them to `/opt/assetecon/evidence/` (outside the repo, backed up) and writing `evidence/MANIFEST.md` (dir, task, date, commit, file count) | Generated output; never read by agents as text; the size dominates checkouts |
| `.agent/*-log.txt` (codex exec transcripts) | 104 files, 81 MB | Untrack (keep the local copy if wanted) | Raw transcripts; the packets and reviews hold the conclusions |
| `.agent/**/*.log`, `*.err`, `*.pid` | 2,329 files, ≈ 12 MB | Untrack and ignore | Process debris |
| `.agent/**/*.ps1`, `*.sh`, `*.py`, `*.mjs` one-off scripts | ≈ 400 | Review by reference grep; untrack those not referenced | Session scripts |
| One-off `tools/*-evidence.mjs` / `*_probe.py` for finished slices | up to 49 | Move to `tools/archive/` when grep shows no reference in check-all, package.json, tests or docs; delete later | Reduces tool-surface noise |
| `.ai/ARTIFACT_INDEX.md` | 1 | Delete or regenerate | Stale since 2026-09-27 |

### 3.6 Add to git (fix F6)

- Commit `.agent/AssetEcon_Product_Direction_Layers_1_to_3_and_Claude_Brief_REVISED.md`, moving it to the direction home (e.g. `Docs/demo-sprint/product-direction-layer4/sources/`). Update the five citing files in the same commit. Coordinate with the active Layer 4 author, because this is their branch.

---

## 4. Safety and sequencing

### 4.1 Known runtime and test references into `.agent/` (do not move without updating)

| Consumer | Reads |
|---|---|
| `tools/checks/mock-deviation-labels.mjs:94` | `.agent/mock-departure-register.md` |
| `tools/checks/test_evidence_checks.mjs:191` | `.agent/W1-UX-combined-owner-walkthrough.md` |
| `host/tests/test_k0_kisiwa_actions.py:114`, `test_k1_registered_kisiwa.py:34`, `test_k3_fuel_balance_parity.py:36` | `.agent/DIESEL-F0/probe-result.json` |
| `tools/probe_kisiwa_fuel.py:58-60,252`, `tools/probe_kisiwa_nights.py:37-38` | `.agent/DIESEL-F0/*`, `.agent/DIESEL-D0/*` |
| `frontend/src/estate/__tests__/estateEvidence.test.tsx:658`, `estateFinancials.test.tsx:628` | `../.agent/W3-02-evidence/*.json` |
| `tools/w5f1-d3-evidence.mjs:23` | `.agent/W5-F1-evidence` |
| `tools/select-tests.py:51`, `tools/validate-test-selection.py:40`, `tools/check-agent-workflow.ps1:138` | path patterns over `.agent/` |
| `frontend/docs/architecture/delivery_next_work.cjs:376` | message text pointing at the coordinator handoff |
| Many `tools/*-evidence.mjs` | write captures into `.agent/<ID>-evidence/` (an output location, changed by rule 5.1) |
| ≈ 580 docstring and comment citations in `backend/`, `frontend/src/`, `tools/`, `host/` | `.agent/<spec>.md` (provenance only, not runtime) |

The safe pattern is to move the data dependencies into a tracked fixtures location, such as `host/tests/fixtures/diesel-f0/` and `tools/checks/fixtures/`, update the reading code in the same commit, and run that consumer's focused test.

### 4.2 Steps (each on its own branch from main, each reviewed, each merged before the next)

0. **Prerequisites.**
   - The owner decides O1–O6.
   - The Layer 4 branch merges, or its author agrees to the pack-side changes.
   - The coordinator commits the pending owner files.
   - No DB build or walkthrough is running.
   - Snapshot: `git tag pre-declutter-2026-11-xx` on main, plus an `rsync` of the full `.agent/` to `/opt/assetecon/evidence-backup-2026-11-xx/`.
1. **`chore/declutter-1-router`** (text only, small, highest value). Rewrite AGENTS.md, START_HERE, NOW (ACTIVE_CONTEXT), ROLE_CONFIG trim, the `.claude/` briefs, skills and commands, and the tasks/README shortening. Verify: grep for stale strings (`S1 Foundation`, `Default binding is Codex`, `only executable queue`) returns nothing on the path. Then a fresh agent smoke test: give a fresh Architect, Implementer and Reviewer the standard brief, ask "what is the current work and where is its spec?", and check the answers and the tokens they used.
2. **`chore/declutter-2-indexes`**. Add the decisions, state, specs, owner and Layer 4 pack indexes. Split DECISIONS and CODE_STATE, moving content without rewriting it. Verify: every decision ID cited in code and docs (grep `D-20..`, `D-E5.`, `D-SR.`) resolves through the index (scripted check).
3. **`chore/declutter-3-untrack-evidence`**. Copy, then `git rm --cached` the evidence, logs and pid/err files. Add the `.gitignore` entries. Move the §4.1 data dependencies to tracked fixtures. Verify:
   - `tools/check-all.ps1` (the guard set, not the full suite)
   - focused `host/tests/test_k0/k1/k3`
   - the two estate frontend tests
   - `tools/checks/test_evidence_checks.mjs` and `mock-deviation-labels.mjs`
   - the file count (`git ls-files | wc -l` ≈ 3k–7k)
   - the demo serve smoke test on the walkthrough worktree, read-only, only if idle
4. **`chore/declutter-4-specs-and-history`**. `git mv` the build sheets to `specs/`, owner files to `owner/` (or leave them, per O4), and review/packet/handoff history to the archive. Leave redirect stubs or a citation map (§4.3). Verify: a scripted link check, in which every `.agent/...`, `Docs/...` and `tasks/...` path cited in tracked text and code resolves to a file or a stub.
5. **`chore/declutter-5-docs-tools`**. Archive the Docs generations and the one-off tools. Verify: grep for references, run check-all, run `select-tests.py` on a sample diff.
6. **Optional (O5): worktree pruning.** List the worktrees whose branch is merged into main and have no uncommitted changes. The owner or coordinator removes them. This is outside the repo diff and never touches `AssetOpsV1-walk` or a running lane.

### 4.3 Citations from code

There are about 580 docstring and comment citations. Options:
- **(a)** Leave stubs at the old `.agent/<file>.md` paths. This is not possible, because `.agent/` will be ignored.
- **(b)** Rewrite the citations in code with a scripted `sed` (mechanical, reviewable, touches about 150 files).
- **(c)** Keep a tracked `specs/CITATION_MAP.md` (old path → new path) and rewrite code citations opportunistically.

The recommendation is (b), in step 4, as a separate mechanical commit with a script that the reviewer re-runs. Fall back to (c) if lanes are active in those files, to avoid merge conflicts.

### 4.4 Lane interaction

47 worktrees branch off main. Untracking and moving files on main causes conflicts only where a lane touched the same files: `.agent/` packets, `ACTIVE_CONTEXT` and `CODE_STATE` appends. Run steps 3 and 4 at a quiet point, and tell lanes to rebase or merge main afterwards. `CODE_STATE` and `DECISIONS` appends after the split go to the new files (rule 5.3).

---

## 5. Rules to keep it decluttered (add to `.ai/RULES.md` and the role briefs)

### 5.1 Where agents write

- **Specs, rulings, decisions:** `specs/<ID>/` and `.ai/decisions/`. These are tracked and indexed in the same commit.
- **Review findings:** `specs/<ID>/review.md`. Each round is appended as a section with a ≤ 15-line summary at the top. The full review text goes in the round section.
- **Owner words:** `owner/<date>-<topic>.md` (verbatim, never edited), plus one line in `owner/INDEX.md`.
- **Generated evidence** (screenshots, capture JSON, logs): the git-ignored `evidence/<ID>/<run>/`, or `/opt/assetecon/evidence/`. A packet cites the run by path and adds a 5–10-line summary. Evidence is never committed, except a test fixture that is deliberately placed under a fixtures folder.
- **Agent scratch and session transcripts:** `.agent/` (ignored) or the session scratchpad. Never force-add into `.agent/`, and enforce this with a guard.

### 5.2 Retention

- Evidence: keep the latest run per task until the owner accepts the slice. After acceptance, keep the final run for 60 days, then delete it. The manifest line stays.
- Scratch in `.agent/`: purge at milestone close.
- Worktrees: remove within a day of the branch merging, unless the walkthrough or demo uses it.

### 5.3 Size and shape caps (context budget)

| Artifact | Cap | When exceeded |
|---|---|---|
| Router files (AGENTS, START_HERE, NOW) | 1.5k tokens each | Move detail to an indexed file |
| ROLE_CONFIG | 3k tokens | Ended items go to `.ai/history/` |
| Role brief (`.claude/agents/*.md`) | 1.5k tokens | Point at RULES.md instead of repeating it |
| Index files | 2k tokens | Split by period or area |
| Task spec (the binding part an implementer must read) | 15k tokens | Split the task (this matches the owner's "split slices > 6 units") |
| Rulings, pre-flight answers | Separate file from the spec; the spec is updated in place with the outcome, and the rulings file keeps the reasoning | – |
| Review round | ≤ 15-line summary + findings list; no restating the brief | – |
| Packet | ≤ 3k tokens; evidence is cited by path | – |
| Coordinator handoff | One current block ≤ 2k tokens, replaced rather than appended; history in git | – |
| Design documents | Have a ≤ 1-page summary/README at the top of their folder, saying which section serves which task type | – |

### 5.4 Find on demand, not up front

Briefs say: "Read the router. Then use the indexes (`decisions/INDEX.md`, `state/INDEX.md`, `specs/INDEX.md`, `owner/INDEX.md`, the direction README) to open only the sections your task names. Search with `grep` scoped to the current homes, never `.agent/`, `archive/` or `evidence/`."

A dispatch brief names the exact sections. Briefs must not say "read X fully" for any file over 15k tokens.

### 5.5 Commit hygiene guard

Extend `tools/check-agent-workflow.ps1` (or a new check in check-all) so that it fails on:
- tracked files under `.agent/`, except an allow-list;
- tracked `*.log`, `*.pid` or `*.err` files;
- PNG files outside the allowed folders;
- any tracked text file over 300 KB outside fixtures and mocks;
- router files over their caps.

### 5.6 Supersession discipline

Whoever supersedes a document adds a header ("Superseded by X, date") and moves it to the archive in the same PR. START_HERE's authority list is updated in that PR.

### 5.7 Estimated default context per role after the change (router plus role rules, before the task's own spec)

| Role | Before: fixed path (with mock) | After: fixed path | After: typical task total |
|---|---:|---:|---:|
| Architect | ≈ 46k (≈ 145k) | ≈ 6–7k (AGENTS 0.5, START 1.5, NOW 1.5, ROLE_CONFIG 3, brief 0.5–1) | + direction README 1.5k + named sections ≈ 20–40k |
| Implementer | ≈ 47k (≈ 146k) | ≈ 7–8k (+ RULES excerpt) | + spec ≤ 15k + state/decision entries by index ≈ 25–35k |
| Reviewer | ≈ 35k (≈ 134k) | ≈ 6k | + spec + packet ≤ 3k + diff |
| Planner | ≈ 57k (≈ 156k) | ≈ 7k | + spec INDEX + direction sections ≈ 20–30k |

The mock is read by the named screen section, never as the whole 77k-token `index.html`. A per-screen extract index is suggested; `extract_v69_panels.mjs` and `v69-rendered-panels.json` already exist and could serve it.

---

## 6. Decisions the owner must make

- **O1. Does the Layer 4 direction supersede the S1–S7 planning documents as current authority?**
  - Documents affected: `production-shaped-mvp.md`, `production-shaped-mvp-technical-design.md`, `site-first-execution-plan.md`, `s1-01-foundation-contract-addendum.md`, `tasks/README.md`, and `.ai/PRODUCT.md`/`ARCHITECTURE.md`.
  - Options:
    - (a) Layer 4 supersedes them; archive them, keeping the platform contracts that the built code still implements as "built-state reference".
    - (b) Both stand: Site-first documents for the built platform, Layer 4 for new product direction, with START_HERE stating the boundary.
    - (c) Defer until the Layer 4 owner decisions (Q1–Q16 and the D-items in `product-transition-and-roadmap.md` §5) close. In the meantime, step 1 only removes the stale status lines and says "direction under owner review".
  - I have not decided this.
- **O2. Which mock governs which work?** The candidates are v69, v70, v71, v72 and the Layer 4 `interactive-mockup-vNEXT` (approval gate pending). This determines the mock-fidelity rule text in all briefs.
- **O3. Evidence storage.**
  - Options:
    - (a) Untrack and keep outside the repo, with a manifest (recommended).
    - (b) Git LFS.
    - (c) Keep as is.
  - Also: how long finished-slice evidence is retained (proposal: 60 days after acceptance).
- **O4. Owner feedback location.** Move `.agent/owner-*.md` to a tracked `owner/` folder with an index (recommended, `git mv` only, verbatim), or leave the files in `.agent/` as an allow-listed exception.
- **O5. Git history and worktrees.** Rewrite history to reclaim about 1 GB (not recommended now)? Should the coordinator prune worktrees of merged branches (recommended, excluding `AssetOpsV1-walk` and active lanes)?
- **O6. Timing.**
  - When to run it: now (step 1 is text-only and safe to do now), or after the Layer 4 pack merges and the next walkthrough. Steps 3 and 4 touch many paths, so they should run at a quiet point.
  - Whether the user memory (`MEMORY.md`, auto-loaded into coordinator sessions) should be pruned of sprint-era rules in the same pass.
- **O7. Whether the Layer 1–3 brief may be committed.** It is cited by the pack and currently untracked. Note that it contains the original "Claude Brief".
