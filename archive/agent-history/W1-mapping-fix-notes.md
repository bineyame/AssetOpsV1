# W1 mapping fix round notes

Fixes against `.agent/W1-mapping-review.md`. Registry: `frontend/docs/architecture/v69-dependency-registry-pilot.json`.

## Changes
- B1 `dispatch:3#a`: removed `I-capability-read` (S3-02); gated on S3-01 nodes only.
- B2 `finding:2#a`, `recommendation:3#a`: removed `I-evidence-analysis-claim-limit-ui` and `I-capability-read` (kept their S4/S6 gates). Architect note: I judged no real technical prerequisite on S3-02 for the bounded portion; if a positive capability limit is wanted in these panels, add a separate positive portion.
- B3 `changes:1`: split `#a` (applied change: S6-01 nodes, no verification/dispatch nodes) and `#b` (later-window effect: adds `A-S6-verification`, `I-S6-02`, verification read/ui, `I-dispatch-*`). S6-02 packet now names `changes:1#b`; S6-01 packet says `changes:1#a`.
- Global stop: `delivery_next_work.cjs` `parseGateQueue` reads every `[PRE-S3-NN](packet)` link in `tasks/README.md`; `nextWork(ctx.gate_queue)` adds them to the active/in-review global stop and refuses on a missing/unknown Status. The CLI passes them and fingerprints their status. `done (...)` parses as done.
- Fixtures: `test_delivery_next_work.cjs` adds "a PRE-S3 gate packet in review or active stops selection" and gate discovery. With the code change stashed, 2 tests failed (19 pass); with it, 21/21 pass.
- V-01a now requires `I-PRE-S3-04` (new resolved node, layer projection, evidence = packet) besides `I-S1-03`, matching its packet.
- 33 panels set `reviewed_mapping:true` with `mapping_review` citing `.agent/W1-mapping-review.md` (fresh Claude reviewer). The 4 fixed panels stay false for a separate re-review. Carries C1-C7 untouched.

## Checks
- `tools/check-all.ps1 -ExecutionPolicy Bypass`: all 6 guards passed (architecture, navigation, agent workflow, dependency registry, delivery fixtures, ledger 110 screens/258 panels).

## Live `--next-work` (exact)
```
next-work report (assetops.next-work.v1) wave W1 K=10: refused
Authority: Non-authoritative until mapped paths and scoring are independently reviewed; never clears USER_REVIEW_REQUIRED.
Input fingerprints: registry=872fc9d6523288c9 queue=60aa58d30bc6be52 packet_status=5e225ed3b9498bb2 panel_contracts=37fd1252dfc006b5 manifest=468bd0cf06b26749 owner_input=f902d15082e24067
REFUSED (fail closed, no task selected):
- [unmapped_approved_panel] 4 approved core panel(s) lack a reviewed claim-portion path: dispatch:3, finding:2, changes:1, recommendation:3
```
PRE-S3-03/04 are done, so no stop from them; the refusal is only the 4 unreviewed panels.
