# PRE-S3-03 independent review — delivery checker and next-work report

Reviewer: fresh Claude reviewer (Opus), independent of the Implementer. 2026-10-11.
Target: `plan/pre-S3-startup`, commits `04122ae`, `c62ff9e`, `147fc45`, `663bde2`, `7300b3a`.
Spec: `tasks/PRE-S3-03-delivery-checker-report.md`; authority `D-2026-10-09-owner-delivery-strategy` ("Selection within the active wave"), owner W1 confirmation 2026-10-11, Architect bounded-portion table in `.agent/W1-owner-input-proposal.md`.

## Verdict

**Accept with findings fixed on the branch.** One block (F1, a small scoring-correctness fix in `delivery_next_work.cjs` plus a fixture). Everything else is carry. The 15 delivered S1/S2 portions and 14 `reviewed_mapping:true` panels hold up against the merged code; this review can be cited as the independent mapping review once F1 is fixed (see C1).

## Findings

### F1 — BLOCK: V-01 visual distance skips the panel's unresolved technical AND branches

`frontend/docs/architecture/delivery_next_work.cjs:254-259` (visual branch of the reach loop): for a visual candidate, `d = upstream.size` (only V-01's own open `requires`) and `closure_unlock: true`, regardless of whether the reached panel still has open technical core portions.

Probe, using the committed fixture with V-01 sized `M`: `site:1` has `site:1#b`/`#c` open on `I-S7-01`, yet V-01 reports `paths: [{key: "site:1", path: "visual", d: 0}]`, `ready_now: 1`, `B=1`, score 1.243. Closing V-01 does not make `site:1` ready: `I-S7-01` remains.

Why it matters: the strategy defines `d=0` as "closing c makes that panel ready" and says "a path cannot skip unresolved AND branches"; the task says distance counts "remaining closeouts after the candidate and unresolved AND branches". Today this has no effect (the report refuses and V-01 is unsized), but once V-01 is sized and `evidence-analysis:2#b` (or any later V-01 screen with an open core portion) gets a reviewed path, V-01's B/P and ready-now are overstated and it can win a ranking it should not.

Fix: for a visual path, `d = |upstream ∪ p.needed|` (the panel's open technical closure, which V-01 does not close), proof lists those gates, `closure_unlock` true only when `p.needed ⊆ upstream`. That still reports the visual gap separately and still never credits a technical candidate with the V-01 gap. Add a fixture assertion that V-01's `d` to the mixed panel is 1 and `ready_now` is 0. If the Implementer reads "report technical and V-01 visual gap/reach separately" as excluding technical branches from visual `d`, route that reading to the Architect rather than keeping the current behaviour silently; even then `ready_now` must not count a panel with an open core portion.

### C1 — CARRY: `mapping_review.by` still says "independent review pending"

Registry, all 14 `reviewed_mapping:true` rows. The flag was set on implementer self-verification, which the W1 proposal says should follow independent checking. My checks (below) support the 14 mappings, so the coordinator can record this review as that evidence (`mapping_review.by`/`evidence` → `.agent/PRE-S3-03-review.md`) when closing out. Carry because recording review outcomes is the coordinator's job, not the Implementer's.

### C2 — CARRY: delivered-portion `evidence` cites implementer packets, not reviewer verdicts

Registry `claim_portions[].evidence` for `foundation:1#a`, `foundation:3#a`, `readiness:1#a`, `sld:1#a`, `sld:2#a` (S1-02/S1-03) and `lab:1#a`, `lab:2#a`, `lab:4#a` (S2-01a/b) list only the task file and the `*-review-packet.md` (the Implementer's claims). The independent verdicts exist (`.agent/S1-02-fix-rereview.md`, `S1-03-review.md`, `S2-01a-codex-review.md`, `S2-01b-fix-rereview-2.md`) and the `delivered_by` nodes are resolved with their own evidence, so the delivery claim is sound; the citation is just weaker than the task's "reviewer/owner records". Add the verdict files at the next registry edit.

### C3 — CARRY: registry text contradictions in delivered rows

- `lab:3#a.boundary` still reads "ingestion receipt/reload awaits S2-02" while the portion is `delivered_by: I-S2-02`.
- `evidence:1#a` and `evidence-analysis:2#a` list `R-capability`, `UI-capability`, `D-coverage-window`, `R-claim-lineage` under `superseded_proposed_gates`, while sibling `#b` portions still carry the same IDs as live `proposed_gates`. They are not superseded; they belong to the open/unmapped portion. No code consumes `superseded_proposed_gates`, so this is documentation only.

### C4 — CARRY (already Q8): stale Readiness text on a W1 screen

Confirmed: `StoredFoundationViews.tsx:433-436` renders `foundation.evidence.statement`, hardcoded at `foundation_api.py:295-298` as "No accepted evidence is linked to this Foundation…", and `FoundationRevisionPanel.tsx:323-324` says each gateway is "registered, awaiting credentials, not sending data". Both are false for Kobo after S2-02. Recording `readiness:1#a` delivered with a caveat is defensible (the claim is configuration readiness only), and not recording `readiness:2#a/3#a` is correct. The truthfulness defect still needs an owner slice; the Architect owns Q8.

### C5 — CARRY: `delivery_plan.enables` is not read by the checker

`enables` is `[]` in the registry and nothing in `delivery_next_work.cjs` or the checker reads it. The strategy allows scoring through explicit `enables` edges. With an empty list this has no effect, but a future non-empty `enables` would be silently ignored rather than either used or refused. Either fail closed when it is non-empty, or implement it, before anyone populates it.

### Not findings (checked, sound)

- Q2/Q3/Q7 defaults are the restrictive readings and are the Architect's to decide; I did not adjudicate them.
- `d = |open AND closure of the panel's core portions| − 1` for technical paths matches the strategy (distinct remaining gates, AND branches not skipped, delivered nodes excluded because only `open` nodes enter the closure).
- Contest handling (`decide`): gap formula, ≤5% stop with recommendation, (5%,10%] tie-break selection with a coordinator-handoff notice, >10% top, single candidate without notice. Tie-break order matches the strategy. `user_review_required` is carried, never cleared.
- XL unscored, outside-ranking listed but ineligible, owner/review/active-task stops applied before decision, refusals typed and fail-closed.
- `tools/check-all.ps1`: missing tool or nonzero guard → FAIL and exit 1; each guard reported. No CI configuration exists in the repo (no `.github/workflows` or equivalent), so "local/CI" reduces to this script plus the README entry.

## S1/S2 delivered-portion verification

I checked each `anchors` entry against the files on this branch. `git diff 82ba6cd HEAD -- frontend/src backend` is empty, so this is the merged code.

| Panel | Anchor checked | Result |
| --- | --- | --- |
| `sites:1` | `SitesIndex.tsx:134` "Configured sites" panel; `sites_api.py:247` `GET` list_sites | matches |
| `foundation:1` | `StoredFoundationViews.tsx:258` ConfiguredTopologyPanel; `foundation_api.py:454` read_foundation `?at=` | matches |
| `foundation:2` | `StoredFoundationViews.tsx:282` IdentityPanel | matches; `#b` obligations correctly unmapped non-core |
| `foundation:3` | `foundation_api.py:490` publish_revision, `:586` publish_bindings; `FoundationRevisionPanel.tsx` controls panel | matches |
| `readiness:1` | `FoundationBindingsPanel.tsx:90` ReadinessVerdictPanel (configuration counts only) | matches, with C4 caveat |
| `sld:1–2` | `SiteSingleLineDiagram.tsx:748` bound/unbound marker, `:1067` SiteSldPrimary; `StoredFoundationViews.tsx:320` SldView, `:357` ConfiguredPartsPanel | matches |
| `lab:1` | `GatewayLedgerView.tsx:219` "The selected envelope, exactly as stored" | matches |
| `lab:2` | `RunFrame.tsx:876-880` "What the world holds" private-state panel | matches |
| `lab:3` | `RunCommitPanel.tsx:65` "Commit and release" | matches (C3 boundary text) |
| `lab:4` | `RunFrame.tsx:1351-1365` "What this run is not" | matches (static text, as claimed) |
| `evidence:1` | `LedgerSiteEvidence.tsx:212-219` state notes, `:293-296` no-conclusion limit | matches; `#b` capability unmapped non-core |
| `evidence:2` | gateway-health read per S2-02; `I-edge-diagnostics-store` resolved | matches; `#b` S7 outage open non-core |
| `evidence-analysis:1` | `LedgerSiteEvidence.tsx:704` Inspector | matches |
| `evidence-analysis:2#a` | `LedgerSiteEvidence.tsx:555-574` AnalysisStatus with explicit "no conclusion" | matches; panel correctly `reviewed_mapping:false` because `#b` is core and unmapped |

Every `delivered_by` node is resolved (the validator enforces it and passes); no delivered portion has `proposed_gates`; every panel is `partial`; none is `real`; V-01 is separate and `open`. The 14 reviewed rows plus `evidence-analysis:2` give 15 delivered portions, as the packet says.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs --next-work --out <scratch>`: **REFUSED**, `[unmapped_approved_panel]` 37 panels (counted: 37 + 14 reviewed = 51 approved core). The fingerprints are identical to the handoff's (`registry=cfeda7377485a4cd … owner_input=f902d15082e24067`).
- Probe script (scratchpad, not committed) running `nextWork` on the committed fixture with V-01 sized: reproduces F1.
- Code-anchor reads for all 15 portions (table above); `git diff 82ba6cd HEAD` over product code is empty.
- Not re-run, per dispatch, and not independently verified by me: `tools/check-all.ps1` (six guards), the 17 node:test fixtures, the six mutation proofs, backend pytest. Frontend `npm test`/build were not run (no product code changed; they are also blocked by the sandbox on this machine). Layout evidence: not applicable.

## Residual risk not in the packet

- F1-class issue: the fixture locks V-01 `visual_reach` but not V-01 `d`/`ready_now`, so the scoring for visual paths is under-tested.
- The 04122ae registry also carries the Codex Planner's S3 edits (`A-S3-dispatch` resolved citing `D-2026-10-11-s3-dispatch-interval-assessment`, which exists; `I-sim-dispatch-cases` requires). I checked these only for consistency with the checker, not as a Planner review.
