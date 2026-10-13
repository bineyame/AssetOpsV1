# V-01b review packet — Lab and Evidence visual fidelity

USER_REVIEW_REQUIRED: true — needs a fresh independent Claude review, then the owner's visual checkpoint (guide `.agent/V-01b-owner-walkthrough.md`).

## Task

`tasks/V-01b-evidence-lab-visual-fidelity.md` (status `in_review`). Branch `task/V-01b-evidence-lab-visual`, diff base `b1ac0a8` (`git diff b1ac0a8..HEAD`). Build history and exact copy: `.agent/V-01b-handoff.md` (phases a, b, c1). Questions with shipped fail-closed defaults: `.agent/V-01b-questions-1.md` (Q1-Q8). No backend change; no mock value used as product data. Neither the screen ledger nor the dependency registry is edited in this task: the coordinator updates registry caveats only after owner acceptance.

## Outcome

- Site Evidence Overview (`/sites/{id}/evidence`) follows mock `evidence`: status bar of window facts, `evidence:1` "What we can conclude now", `evidence:2` "Data sources · data quality, not equipment condition" beside `evidence:3` "Most useful next evidence", closing notice to Analysis; technical panels under closed "Advanced details — …".
- Evidence Analysis (`?view=analysis`) follows mock `evidence-analysis`: `evidence-analysis:1` "Accepted records behind the conclusions" with "Open record" → "Exact message as received"; `evidence-analysis:2` "How each limit is set".
- Refused readings show the conflicting reading's original taken time and link (S2-02 batch-4 carry closed).
- Lab run page opens on h2 "Gateway & Ingestion" (status strip, four flow boxes, `lab:1`-`lab:4` in two rows) above "Execution and recorded history"; seven technical disclosures closed.
- Lab shell gets the <640px layout (`app-frame--lab`); guard `shell-overflow.ps1` 2b amended to require it.
- Every unsupported mock portion is a visible "Not available yet: …" statement.

## Files materially changed

Product: `frontend/src/sites/LedgerSiteEvidence.tsx`, `frontend/src/shell/RunIngestionOverview.tsx` (new), `frontend/src/shell/runIngestion.css` (new), `frontend/src/shell/RunFrame.tsx`, `frontend/src/shell/RunCommitPanel.tsx` (optional `onRead`), `frontend/src/shell/GatewayLedgerView.tsx` (Q1 label), `frontend/src/shell/SimulatorLabShell.tsx` (`app-frame--lab`), `frontend/src/ui/primitives.css`.
Tests: `shell/__tests__/v01bEvidenceVisual.test.tsx`, `v01bLabIngestion.test.tsx` (new); updated `cockpitLayout`, `runExecution`, `simulatorLabGate`, `s2LedgerEvidence`, `runsInventory` (c2: Commit is now first in document order), `ui/__tests__/overflowContainment.test.tsx`.
Guards/tools: `tools/checks/shell-overflow.ps1`, `tools/layout-evidence.mjs`, `tools/v01b-lab-evidence-evidence.mjs` (new), `tools/v01b_lab_evidence_walkthrough.py` (new).

## Acceptance criteria (task file, one by one)

1. **Compare by manifest ID and panel portion** — met for `lab:1-4`, `evidence:1-3`, `evidence-analysis:1-2`; table below. Supported portions (`#a`) rendered from real reads; unsupported portions named.
2. **1440/390 app/mock pairs for populated, missing and late/contradictory states** — met for populated and missing (`node tools/v01b-lab-evidence-evidence.mjs`; the c1 101/101 is STALE after fix 3, see Fix round 4 for the measured fix-4 result (not 101/101); mock shots `mock-{lab,evidence,evidence-analysis}-{desktop,narrow}`). Late: Taken/Sent/Received columns on every accepted record (desc "Measured time is kept even when a report arrives late"). Contradictory: the "Original reading" column; the walkthrough data has **0 refused readings, so no stored conflict exists there**; it is proven by `v01bEvidenceVisual.test.tsx` "shows a conflicting reading beside the original reading's taken time and opens it", not by a screenshot.
3. **Hierarchy, density, labels** — panel titles in mock order and two-column/stacked rows measured at both widths; "Advanced details — …" closed by default and each opens; vocabulary tests pass. Density/look is the owner's call.
4. **Keyboard navigation** — partially evidenced: every new control is a native link, button or `<details>` summary (Tab/Enter); no dedicated keyboard measurement was added. Reviewer to spot-check.
5. **Site/window/selection and reload** — the window is in the address (`from`/`to`, `view=analysis`), so reload and Back keep it; empty window, empty store ("No such site") and a chosen source (50 per source) measured or tested. Selection from "Open record" is in-page.
6. **Follow an accepted value to its SourceEnvelope** — met by the evidence tool trace: the displayed row value ("STOPPED state") equals the read API record; the API `envelope.text` equals the displayed "Exact message as received"; `payload.value` equals `original.value`. S3-02 owns the positive claim-limit portion.
7. **Run checks** — see Checks run.

## Conditional-acceptance record (no owner acceptance is written here)

Evidence screenshots (`<dir>/` of the evidence tool): `-desktop` 1440x1000, `-narrow` 390x900. Column 5 is for the owner; an accepted panel would read "Owner visual acceptance conditional on these named data gaps; layout/copy accepted only".

| Panel | (1) Rendered from | (2) Exact visible missing-state copy | (3) Unfilled mock claim; owner/task trigger | (4) 1440/390 evidence | (5) Owner |
| --- | --- | --- | --- | --- | --- |
| `lab:1` Selected canonical envelope | Stage read (earliest stored envelope, projection) | "No envelope is stored for this run yet." | none (portion `#a` fully rendered) | `app-lab-run`, `app-lab-run-top`, `app-lab-run-not-committed` | pending |
| `lab:2` Truth versus observed | execution projection (private world, Lab only) + device reports | "Not available yet: the product consequence of each report (accepted, latency retained or indeterminate). These reads give central decisions per batch, not per device report." | Per-report product consequence (Q7; needs a per-report decision read) | `app-lab-run`, `app-lab-run-top` | pending |
| `lab:3` Release and ingestion | Commit read (`registered_release.delivery`, central receipts) + RunCommitPanel | "Not committed: nothing released, nothing accepted centrally." / "Nothing from this run has been received centrally." | none beyond Q1 (Stage upload line labelled, not fixed) | `app-lab-run`, `app-lab-run-not-committed`, `app-lab-run-advanced-open` | pending |
| `lab:4` What never crosses | static boundary text | "Not available yet: a link from this run's accepted records to the Dispatch analysis that used them. No run-to-analysis read exists here." | run→Dispatch analysis link (no run-to-analysis read; later S3 slice) | `app-lab-run` | pending |
| `evidence:1` What we can conclude now | `GET /api/sites/{id}/evidence` counts, outcomes, notes | "Not available yet: capability-by-capability conclusions (what can be said, what is missing and the next step for each). They need a reviewed capability assessment over accepted Evidence, which does not exist yet." | `evidence:1#b` capability assessment (R-capability / UI-capability / D-coverage-window) | `app-evidence-populated`, `app-evidence-empty` | pending |
| `evidence:2` Data sources | evidence read `sources` + `GET .../gateway-health` | "Not available yet: a status at the end of the period, a quality grade and which conclusions each source affects. No reviewed rule sets these."; zero source "No accepted reading in this period" | `evidence:2#b` outage/pressure health and per-source quality/"Affects" (no reviewed rule) | `app-evidence-populated`, `app-evidence-empty`, `app-evidence-gateway-unavailable` (intercepted 503) | pending |
| `evidence:3` Most useful next evidence | evidence read `sources` (silent-source facts only) | "Not available yet: ranking the next evidence needs a reviewed rule linking missing readings to conclusions." | `evidence:3#a` R-next-evidence ranking rule | `app-evidence-populated`, `app-evidence-empty` | pending |
| `evidence-analysis:1` Accepted records | `GET .../evidence/records` (10/page; 50 per source) and `.../records/{id}` | "No accepted reading in this period." | none for `#a`; conflict original time proven by test only (0 refused on this data) | `app-evidence-analysis-populated`, `-empty`, `-advanced-open`, `app-evidence-record-detail` | pending |
| `evidence-analysis:2` How each limit is set | evidence read notes (partial, conflict, outdated, analysis status, no conclusion) | "Not available yet: the rule that turns accepted readings into a positive capability conclusion and sets its limit (a later capability assessment)." | `evidence-analysis:2#b` positive claim-limit rule (core; S3-02 per the task) | `app-evidence-analysis-populated`, `-empty` | pending |

Also: empty store `app-evidence-no-site` ("No such site"), `app-lab-runs-empty`. Mock "Evidence limited" badge (Q3) and "Portfolio evidence →" (Q6, W3 route) are not shown.

## Tests that fail before the change

`v01bEvidenceVisual.test.tsx` 10 tests: 8 failed before b1, all pass. `v01bLabIngestion.test.tsx` 9 tests: all 9 failed before b2, all pass. `overflowContainment.test.tsx` asserts `app-frame--lab` (fails on the bare `.app-frame`).

## Guard 2b non-vacuity (c2)

(a) Bare `.app-frame .nav-rail { display: none; }` in the 640px block → `check-architecture.ps1` exit 1: "'.app-frame .nav-rail' in a max-width:640px block of frontend/src/ui/primitives.css is not scoped to .app-frame--operator or .app-frame--lab. …". (b) Every `.app-frame--lab` part in that block renamed → seven "not scoped" lines and "No narrow-width .app-frame--lab rule was found in frontend/src/ui/primitives.css. The Simulator Lab shell at phone width gave its main column about 95px of 375px (S1-03 Q1 carry, closed by V-01b)." Both reverted with `git checkout`; tree clean.

## Checks run (c2, actual results)

- `npx vitest run` (first run): 1 failed | 1380 passed — `runsInventory.test.tsx` "offers exactly the three execution controls and nothing else" (V-01b order change; fixed `913de45`); re-run of that file 21/21. Full re-run: "Test Files 57 passed (57); Tests 1381 passed (1381)".
- `npx tsc --noEmit -p .`: exit 0. `npm.cmd run build`: "✓ built in 13.24s" (chunk-size warning only).
- `tools/check-architecture.ps1`: "Architecture check passed." `tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- `tools/check-all.ps1`: "All 6 guards passed." (architecture seams, navigation truthfulness, agent workflow, dependency registry, delivery checker fixtures, screen ledger "110 screens, 88 distinct models, 258 panels").
- Backend `pytest backend/tests -q -x` (not covered by check-all): "1771 passed, 127 skipped, 2 warnings in 349.43s".
- Layout: `ASSETOPS_CDP_PORT=9396 ASSETOPS_LAYOUT_CREATE_RUNS=1 ASSETOPS_LAYOUT_V01B_RELEASED_RUN=run-234889a36d0a4333a1e8877bf5015762 node tools/layout-evidence.mjs http://localhost:5384 KOBO-001` → **398 PASS / 5 FAIL**, all named preconditions: fuel-loss 430 L > KOBO tank ×1; Q8 drawing unbound (Foundation v10 ≠ frozen) ×3; legacy file Kobo Site absent ×1. The first c2 run (388/6) also failed "at least one table overflows here" for run setup at 640x700 (0 of 2): with the Lab rail now collapsing below 640px the summary fits, so the proof moved to an added 390x800 pass (2 of 2 overflow; `9ad6406`, precedent `16d1095`).
- Evidence tool: c1 recorded 101/101, stale after fix 3. Fix round 4 run did not complete cleanly (14/19 and 71/79, see below); the two Stage claims pass.

## Known deviations

- h1 kept "Draft run" / "Evidence" (Q2), "Gateway & Ingestion" is the first h2.
- `evidence-analysis:2` titled "How each limit is set" (Q4; vocabulary guard bans "claim").
- No "Portfolio evidence →" (Q6); status bar badge is neutral "No capability conclusion yet" (Q3).
- Q8: no runnable registered run can draw on current Foundation v10, so T025d label-collision claims are unmeasured (named precondition).
- Q1: Stage "Upload pending" line was labelled in earlier rounds; fixed in fix round 3 (the constant fields are no longer rendered). Backend retirement of the fields stays open.
- Guard `shell-overflow.ps1` 2b amended (S1-03 Q1 scoping widened to the Lab shell now that its phone layout is browser-verified) — reviewer note required.
- `layout-evidence.mjs` creates a Lab draft on the store it measures every run (backlog carry).

## Residual risk

`.action` cascade overrides `.action--primary` on other screens (backlog). Gateway "unavailable" state is an intercepted 503, not stored. Contradictory state has no stored instance on walkthrough data. Source · reading shows identical source and device ids on KOBO-001.

## User-review focus

Lab flow box 2 reads "321 reports published, 1 dropped / 329 admitted by the gateway": two reads' counts side by side, difference unexplained on screen. Density of the Evidence Overview two-column row at 1440. Q2 and Q4 wording.

## Fix round 1

- Finding 1 (`RunIngestionOverview.tsx` `receivedStatement`): "Nothing from this run has been received centrally." now only for a delivery with zero receipts or a loaded `NOT_COMMITTED` commit. Unread Commit says "The commit status could not be read, so what was received centrally is not known."; registered release with no delivery says "The gateway delivery could not be read, so what was received centrally is not known." Two tests added in `v01bLabIngestion.test.tsx` (Commit read resolves `not_found`; registered release `GATEWAY_UNAVAILABLE`, `delivery: null`). Both failed on the old code (2 failed | 9 passed) and pass now (11 passed).
- Carry C2: `registeredKoboLab` in `tools/layout-evidence.mjs` needs `ASSETOPS_LAYOUT_CREATE_RUNS=1` and refuses ports 5173, 5183, 5199, 5213, 5291, 5360-5363; otherwise prints `not run` with the reason and returns false (never PASS). The recorded layout command above now carries the opt-in. Layout evidence was not re-run (no live server touched); the gate is checked by `node --check` only.
- Carries C1, C3-C6 (C2 marked fixed) appended to `.ai/MILESTONE_REVIEW_BACKLOG.md`.
- Checks: `npx vitest run` Test Files 57 passed, Tests 1383 passed; `npx tsc --noEmit` clean; `tools/check-all.ps1` "All 6 guards passed."

## Fix round 2

Owner chose this after the second RETURN (`.agent/V-01b-fix-rereview.md`). Commit `b205486`.

- Finding A: `OWNER_PORTS` was a module-level const read from top-level await before its declaration (temporal dead zone). It is now declared inside `registeredRunGate()`. Observed, no server running, no owner port touched: `ASSETOPS_LAYOUT_V01B_ONLY=1 node tools/layout-evidence.mjs http://localhost:5399` printed
  `=== V-01b registered Kobo Lab run (create + execute) ===` then
  `  not run  run creation is opt-in: set ASSETOPS_LAYOUT_CREATE_RUNS=1 and point BASE at a private disposable store; its Draft, drawing and Gateway & Ingestion claims are unverified`,
  then `AT LEAST ONE CLAIM FAILED` (exit 1: not run is never a pass). The script continued to its summary instead of crashing. No private servers were needed, so none were started and no database created.
- Gate refusal on an owner port, via a harness that extracts and calls `registeredRunGate()` directly (no traffic sent): with `ASSETOPS_LAYOUT_CREATE_RUNS=1`, BASE 5173 returns "BASE http://localhost:5173 is a default/owner port (5173); run creation refused"; BASE 5399 returns null.
- Finding B: `receivedStatement` now returns "Reports were received centrally, but the run's execution could not be read, so no Site Evidence link is offered." when receipts exist and the execution read failed. One test added in `v01bLabIngestion.test.tsx`: before the fix 1 failed | 11 passed (`expected 'The commit status could not be read, ...' to match /execution could not be read/`); after, 12 passed.
- Checks: `npx.cmd vitest run` 57 files, 1384 tests passed; `npx.cmd tsc --noEmit` clean; `tools/check-all.ps1 -Python python` all 6 guards passed. Full (non-ONLY) layout evidence and the create-and-execute path with the opt-in were not run (no private store prepared).


## Fix round 3 (Architect Q1 ruling, carry D1)

Commit af67dc8.
- Q1: `GatewayLedgerView.tsx` no longer renders the Stage read's `upload_state`, `upload_statement` or "Receipts: None" (the replaced Upload row and the V-01b label). One row, "Upload and central receipt", says: "This Stage read does not establish upload or central receipt state. See Release and ingestion for what was released and received." Sealed-batch, queue, envelope and hold facts are unchanged. This is the only place the Stage text renders (also inside the Advanced details disclosure). `tools/layout-evidence.mjs` claim updated to match (not run; no servers).
- D1: `receivedStatement` takes `execution`; receipts present and execution still loading returns "Loading the execution of the persisted run."
- Tests: gatewayLedgerStage (fields absent, neutral copy present), v01bLabIngestion (registered run with central receipts: no "no receipt exists"/"Upload pending"/"Receipts None", neutral copy and "3 envelopes in 1 batches; 1 held reports" and Sealed batches present; new test with a never-resolving execution read).
- Fail-before: with the two source files restored from HEAD~1, 3 tests failed (gatewayLedgerStage 1, v01bLabIngestion 2: the Q1 test and the D1 loading test); after, all pass.
- Checks: `npx.cmd vitest run` 57 files, 1385 passed; `npx.cmd tsc --noEmit` clean; `check-all.ps1 -Python python` all 6 guards passed. Layout evidence: not run (no servers).
- Open: backend carry to retire/rename the obsolete Stage fields.



#
#
 
F
i
x
 
r
o
u
n
d
 
4
 
(
F
1
 
t
o
o
l
i
n
g
,
 
F
2
 
c
o
m
m
e
n
t
)


-
 
T
o
o
l
 
n
o
w
 
w
a
i
t
s
 
f
o
r
 
a
n
d
 
a
s
s
e
r
t
s
 
`
[
d
a
t
a
-
g
a
t
e
w
a
y
-
d
e
l
i
v
e
r
y
-
n
e
u
t
r
a
l
]
`
 
c
o
n
t
a
i
n
i
n
g
 
"
d
o
e
s
 
n
o
t
 
e
s
t
a
b
l
i
s
h
 
u
p
l
o
a
d
 
o
r
 
c
e
n
t
r
a
l
 
r
e
c
e
i
p
t
 
s
t
a
t
e
"
 
a
n
d
 
a
s
s
e
r
t
s
 
`
[
d
a
t
a
-
g
a
t
e
w
a
y
-
u
p
l
o
a
d
]
`
/
`
[
d
a
t
a
-
g
a
t
e
w
a
y
-
r
e
c
e
i
p
t
s
]
`
 
a
b
s
e
n
t
 
(
t
h
o
s
e
 
s
e
l
e
c
t
o
r
s
 
n
o
 
l
o
n
g
e
r
 
e
x
i
s
t
 
i
n
 
t
h
e
 
c
o
m
p
o
n
e
n
t
;
 
t
h
e
 
a
b
s
e
n
c
e
 
c
l
a
i
m
 
i
s
 
t
h
e
r
e
f
o
r
e
 
w
e
a
k
 
b
y
 
c
o
n
s
t
r
u
c
t
i
o
n
)
.
 
F
2
 
d
o
c
s
t
r
i
n
g
 
r
e
w
o
r
d
e
d
.
 
C
o
m
m
i
t
 
e
f
d
e
4
0
3
.


-
 
R
u
n
:
 
p
r
i
v
a
t
e
 
`
a
s
s
e
t
o
p
s
_
v
0
1
b
f
i
x
4
`
/
`
a
s
s
e
t
o
p
s
_
v
0
1
b
f
i
x
4
e
m
p
t
y
`
,
 
w
o
r
k
 
`
v
0
1
b
-
f
i
x
4
`
,
 
p
o
r
t
s
 
8
8
9
6
/
8
8
9
7
/
5
3
9
6
/
5
3
9
7
;
 
`
n
o
d
e
 
t
o
o
l
s
/
v
0
1
b
-
l
a
b
-
e
v
i
d
e
n
c
e
-
e
v
i
d
e
n
c
e
.
m
j
s
 
h
t
t
p
:
/
/
l
o
c
a
l
h
o
s
t
:
5
3
9
6
 
<
s
c
r
a
t
c
h
>
 
h
t
t
p
:
/
/
l
o
c
a
l
h
o
s
t
:
5
3
9
7
`
.


-
 
R
e
s
u
l
t
,
 
u
n
m
o
d
i
f
i
e
d
 
t
o
o
l
:
 
`
1
4
/
1
9
 
c
l
a
i
m
s
 
p
a
s
s
e
d
`
 
(
e
x
i
t
 
1
)
.
 
I
t
 
a
b
o
r
t
e
d
 
a
t
 
`
e
v
i
d
e
n
c
e
A
n
a
l
y
s
i
s
`
:
 
`
G
E
T
 
/
a
p
i
/
s
i
t
e
s
/
K
O
B
O
-
0
0
1
/
a
n
a
l
y
t
i
c
s
`
 
r
e
t
u
r
n
s
 
4
0
9
 
`
A
W
A
I
T
I
N
G
_
E
V
I
D
E
N
C
E
_
M
I
G
R
A
T
I
O
N
`
 
o
n
 
t
h
e
 
p
r
i
v
a
t
e
 
s
t
o
r
e
 
(
l
e
g
a
c
y
 
s
u
r
f
a
c
e
;
 
t
h
e
 
E
v
i
d
e
n
c
e
 
a
n
a
l
y
s
i
s
 
p
a
g
e
 
s
h
o
w
s
 
"
S
i
t
e
 
u
n
a
v
a
i
l
a
b
l
e
"
)
,
 
s
o
 
t
h
a
t
 
p
a
g
e
'
s
 
c
l
a
i
m
s
 
f
a
i
l
 
a
n
d
 
t
h
e
 
r
u
n
 
t
h
r
o
w
s
 
(
`
r
e
a
d
i
n
g
 
'
i
d
'
`
)
.
 
S
t
a
g
e
 
c
l
a
i
m
s
 
w
e
r
e
 
n
o
t
 
r
e
a
c
h
e
d
.


-
 
S
e
c
o
n
d
 
r
u
n
,
 
a
 
t
e
m
p
o
r
a
r
y
 
u
n
t
r
a
c
k
e
d
 
c
o
p
y
 
w
i
t
h
 
t
h
e
 
`
e
v
i
d
e
n
c
e
A
n
a
l
y
s
i
s
`
 
c
a
l
l
 
s
k
i
p
p
e
d
 
(
n
o
t
 
c
o
m
m
i
t
t
e
d
)
:
 
`
7
1
/
7
9
 
c
l
a
i
m
s
 
p
a
s
s
e
d
`
.
 
B
o
t
h
 
n
e
w
 
S
t
a
g
e
 
c
l
a
i
m
s
 
P
A
S
S
 
a
t
 
d
e
s
k
t
o
p
 
a
n
d
 
n
a
r
r
o
w
 
(
4
 
o
f
 
4
)
.
 
T
h
e
 
8
 
f
a
i
l
u
r
e
s
 
w
e
r
e
 
n
o
t
 
c
a
u
s
e
d
 
b
y
 
t
h
i
s
 
d
i
f
f
:
 
E
v
i
d
e
n
c
e
 
o
v
e
r
v
i
e
w
 
p
a
n
e
l
-
o
r
d
e
r
/
s
i
d
e
-
b
y
-
s
i
d
e
 
(
t
h
e
 
s
a
m
e
 
c
l
a
i
m
s
 
p
a
s
s
e
d
 
i
n
 
r
u
n
 
1
,
 
s
o
 
t
h
e
 
s
o
u
r
c
e
s
 
p
a
n
e
l
 
i
s
 
f
l
a
k
y
 
o
r
 
l
a
t
e
 
h
e
r
e
)
,
 
"
A
d
v
a
n
c
e
d
 
d
e
t
a
i
l
s
"
 
l
o
o
k
u
p
s
 
(
m
y
 
c
o
p
y
 
w
a
s
 
r
e
-
e
n
c
o
d
e
d
 
b
y
 
P
o
w
e
r
S
h
e
l
l
,
 
m
a
n
g
l
i
n
g
 
t
h
e
 
e
m
 
d
a
s
h
)
,
 
a
n
d
 
"
n
o
 
s
t
o
r
e
d
 
R
E
A
D
Y
 
d
r
a
f
t
"
 
i
n
 
t
h
e
 
f
i
x
t
u
r
e
.
 
N
o
t
 
i
n
v
e
s
t
i
g
a
t
e
d
 
f
u
r
t
h
e
r
.
 
1
0
1
/
1
0
1
 
i
s
 
N
O
T
 
c
l
a
i
m
e
d
;
 
t
h
e
 
p
r
e
-
e
x
i
s
t
i
n
g
 
e
v
i
d
e
n
c
e
-
a
n
a
l
y
s
i
s
 
f
a
i
l
u
r
e
 
n
e
e
d
s
 
a
 
t
o
o
l
/
f
i
x
t
u
r
e
 
d
e
c
i
s
i
o
n
.


-
 
C
l
e
a
n
u
p
:
 
a
l
l
 
f
o
u
r
 
p
o
r
t
s
 
s
t
o
p
p
e
d
,
 
`
d
r
o
p
`
 
r
e
m
o
v
e
d
 
b
o
t
h
 
d
a
t
a
b
a
s
e
s
 
a
n
d
 
`
%
L
O
C
A
L
A
P
P
D
A
T
A
%
/
A
s
s
e
t
O
p
s
/
v
0
1
b
-
f
i
x
4
`
,
 
t
e
m
p
 
t
o
o
l
 
c
o
p
y
 
d
e
l
e
t
e
d
,
 
t
o
o
l
 
C
h
r
o
m
e
 
c
l
o
s
e
d
.
 
N
o
 
o
w
n
e
r
/
s
h
a
r
e
d
 
d
a
t
a
b
a
s
e
,
 
p
o
r
t
 
o
r
 
`
v
a
r
/
`
 
w
a
s
 
t
o
u
c
h
e
d
.

