# C9 stop fix re-review (fresh Claude reviewer)

Produced by a fresh Claude reviewer. Target: f05686b on plan/pre-S3-startup (vs 56e3777).

## Verdict: reject C9 as closed (one block); (a), (b), (d) accept; (c) accept with a carry.

## Checks run
- node test_delivery_next_work.cjs: 23/23 pass. check_v69_dependency_registry.cjs exits 0. check-agent-workflow.ps1 passes. Live --next-work: ranked, select I-sim-dispatch-cases 3.018, second A-finding-episode 2.679, gap 11.2% (matches claim).
- Not run: the other check-all guards individually.

## Findings
**B1 (block) - V-01a and V-01b are still not read by the stop.** tasks/README.md lines 48-49 link them as `[V-01a Site/Foundation fidelity](V-01a-...md)` and `[V-01b Lab/Evidence fidelity](V-01b-...md)`. parseGateQueue only matches links whose text is the bare id, so on the real README it returns S1-01..S7-01, S2-02r, PRE-S3-03, PRE-S3-04 and V-01 only. The two packets that are the next-activated work (and the original subject of C9) are unmatched; if V-01a goes active or in_review, nothing stops selection. The new fixture 'visual-gate ... (C9)' feeds V-01a through a synthetic gate_queue, so it passes without exercising discovery on real input; the discovery fixture has no `[V-01a label](...)` case. Fix: key discovery on the link target filename (`(?:^|/)([A-Z][A-Za-z0-9]*(?:-[A-Z]\d)?-\d{2}[a-z]?)-[^/]*\.md`) or accept link text starting with the id, and add a fixture using the real labeled form; or add a README-wide assertion that every task-packet link (excluding docs and archive) is discovered. Note the knock-on: V-01a/b Status is "open W1 visual gate (L); activate after startup guards", which packetPhase returns `unknown`, so once discovered they would refuse with queue_mismatch. packetPhase needs `open` (anchored, not substring) as not_started, with a fixture.

**C1 (carry) - `umbrella` is a prefix match.** It is anchored at the start of Status, so it cannot match "active ... umbrella", and the active/in_review/done patterns are tested first. A packet author could still write `Status: umbrella ...` on a real packet and hide it; V-01 is currently the only one and the status is explicit. Acceptable; consider restricting to the literal "umbrella/index".

**C2 (carry) - dedupe is safe.** Registry task nodes (taskInfo) are each checked for missing/unknown status and included in the active/in_review stop, so filtering gateInfo by taskInfo.has drops no status. Only the two lists' packet paths are not compared; a differing path for the same id would be unchecked. Negligible.

## (a)-(d)
- (a) Accept. The queue_mismatch refusal from a missing or unknown gate packet is now returned early with status refused and exit 3 path intact; fixture 'missing' asserts it.
- (b) Accept with C1.
- (c) Accept with C2.
- (d) Accept. dispatch:3, finding:2, changes:1, recommendation:3 are the only registry lines touched (4 lines, matches the re-review's panel list); nothing else in the registry moved. Gate packets PRE-S3-03/04 are done, so no spurious stop.

## Residual
Reports are non-authoritative until B1 is fixed; the selection of I-sim-dispatch-cases should not be acted on as a clear-stop signal for visual gates until then.
