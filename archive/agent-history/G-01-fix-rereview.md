# G-01 fix round 1 - fresh re-review

Reviewer: fresh Claude Reviewer (did not author G-01 or its fix round). Date: 2026-10-13.
Branch `task/G-01-mock-gap-catalogue-and-guard`, HEAD `d067924`, diff `c249795..d067924`.
Scope: Findings 1 and 2 of `.agent/G-01-review.md`, the queue row, and the backlog carries. Narrow by dispatch.

## Verdict: ACCEPT

Finding 1 is closed. Finding 2 is recorded honestly, and the artefacts on disk corroborate it. No new findings.

## Finding 1 - duplicate placement: closed

The fix is in `tools/checks/missing-claim-scan.mjs:156-165`. Usage keys are now global (gapId + placement, across
all files). Any second use reports `ui_duplicate_placement` at the second location and names the first file:line.

### Probes on the real tree

Each probe was reverted with `git checkout` (or by deleting the probe file). The tree was clean afterwards.

| Probe | Result |
| --- | --- |
| P1. Same file (`ReadinessOverview.tsx`), `as="span"`, string child "Uptime not available yet: probe." | `ui_duplicate_placement ...:513 ... already used at ...ReadinessOverview.tsx:491`, exit 1 |
| P2. New file `ProbeB.tsx`, const expression child | `ui_duplicate_placement`, both locations named (file walk order puts ProbeB first) |
| P3. Existing other file (`SiteDetails.tsx`), self-closing element with no copy | `ui_duplicate_placement` |
| P4. Aliased import (`MissingClaim as MC`) wrapping the copy | Not seen as a usage, so the copy is `untagged_copy` and the scan fails. Not a bypass. |
| P5. Expression-valued `gapId={"..."}` / `placement={"..."}` | `ui_usage` error, exit 1 |
| P6. `.map` over a const array, with one syntactic element | `ui_duplicate_placement` plus `untagged_copy` |

Notes on the probes:

- The exit code was checked directly on P1. The value was 1.
- The original Finding 1 reproduction is now rejected (P1).

### The fixture fails without the fix

- I wrote the `c249795` version of `missing-claim-scan.mjs` over the current file and ran the fixtures.
- Result: the fixture `mutation: a catalogued placement used twice fails, naming both locations` failed (✖), with 10 of 11 passing.
- After restoring the file, 11 of 11 passed.

### Residual (carry, not a finding)

A single placement can still wrap extra copy. I tested this by appending "Uptime not available yet: probe." inside
the existing firmware `<MissingClaim>` children, and the scan passed.

- The scan cannot tell this apart syntactically.
- The original fix did not ask for it.
- The edit has to touch the catalogued element, so it is visible in diff review.
- On Readiness, the jsdom and evidence-tool exact-text assertions would catch it.

## Finding 2 - 1440/390 evidence: recorded honestly

I started no servers and sent nothing to any port.

### The artefacts match the packet

The run directory is `C:\Users\assef\AppData\Local\Temp\g01-evidence-run`.

- **Run log:** `run.log` ends with `113/113 claims passed` and contains no failure lines.
- **Ports:** `serve.log` shows APIs on 8898/8899 with `assetops_g01evwalk`/`assetops_g01evempty` and the Vite commands for 5398/5399. These match the packet.
- **Screenshots:** there are ten, one for each of 5 shapes × 2 widths, as the packet states.
- **Claim count:** the tool structure gives 113 claims:
  - 1 precondition;
  - 10 runs × (1 loaded + 10 checks);
  - 2 reload claims (stale, at each width).

  This total matches the reported count.
- **Screenshot inspection:** I viewed `g01-firmware-390-unknown.png`. The firmware line is the last line inside the Gateway status panel, it is not clipped, and it shows no value. This agrees with the packet.

### What the packet does not overclaim

- It says the current/unknown/503/404 shapes are in-browser substitutions that "prove only what the screen renders".
- It says `layout-evidence.mjs` was not run.
- It discloses the loose-pattern kill that ended unrelated processes.

### Cleanup

The packet says `drop` removed both databases, verified by a `pg_database` listing. I could not verify this without
connecting to Postgres, so the claim is unverified by me. It is consistent with the artefacts.

### Owner walkthrough

`.agent/G-01-owner-walkthrough.md:30` states the same result, says it was a coordinator run, and gives the repeat
command on the owner's own ports. It is consistent with the packet.

## Records

- `tasks/README.md`: the G-01 row reads "in review (fix round 1)". C8 is done.
- `.ai/MILESTONE_REVIEW_BACKLOG.md`: "G-01 carries (2026-10-13)" has C1-C7, matching the review.

## Checks run (my results)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run` (frontend) | 58 files, 1391 tests passed |
| `powershell -NoProfile -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python .venv/Scripts/python.exe` | All 9 guards passed, exit 0. The scan reports 1 tagged use and 16 baselined. |
| `node --test tools/checks/test_missing_claim_scan.mjs` | 11/11 pass; 10/11 against the pre-fix scan |

Not run:

- `npm run build`.
- Backend pytest. The fix round changes no backend code.
- The browser evidence. Per dispatch, no servers were started.

## Carries (non-blocking)

- **C9.** One catalogued placement can wrap additional missing-capability copy inside its own children (residual above).
  - G-02 reviewers should check that each `<MissingClaim>`'s children carry only that gap's claim.
  - Alternatively, the Architect could require one literal or one const child per element.
- **C10.** The optional check from Finding 1 was not carried into the backlog: each placement's first segment should match the screen that owns the file. Add it to the backlog if it is wanted.
- **C11.** The layout evidence lives only in `%TEMP%` (screenshots and `run.log`), not in the repo. Copy it somewhere durable if it should outlive the machine's temp cleanup.
