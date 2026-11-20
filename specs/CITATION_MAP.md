# Citation map: old `.agent/` paths (declutter step 4, 2026-11-18)

Every file tracked under `.agent/` at `bae760425` (2,096 files) moved by these rules, in order
(`tools/declutter/step4_map.py` is the executable form; `move_step4.py --verify` proves the bytes).
Citations in live text and code comments were rewritten by `tools/declutter/rewrite_citations.py`;
this map resolves the rest: verbatim records (archived files, owner files, spec parts,
`.ai/history/`), data files read at run time, mocks, and branches that still hold old paths.

## Rules

1. Kept in `.agent/` (same path; the live list, which check-all enforces, is `AGENT_KEEP` in
   `tools/checks/tracked_evidence.py`):
- `.agent/coordinator-handoff.md`: tracked live coordination state (trimmed to one current block).
- `.agent/lane-rules-vps-2026-11-12.md`: live lane rules on this machine (cited by .ai/NOW.md).
- `.agent/architect-sequence-client-scope-2026-11-11.md`: live demo-sprint plan (cited by .ai/NOW.md).
- `.agent/backlog-post-demo.md`: live post-demo backlog; the owner picks items after the demo.
- `.agent/page-load-architecture-review-2026-11-14.html`: owner decisions D1-D6 still pending.
- `.agent/convertion_potential.html`: moved in step 5 to `Docs/demo-sprint/convertion_potential.html` (same bytes; see below).
- `.agent/decision-intelligence-mechanism-2026-11-14.html`: moved in step 5 to `Docs/demo-sprint/decision-intelligence-mechanism-2026-11-14.html` (same bytes; see below).
- `.agent/mock-departure-register.md`: read by tools/checks/mock-deviation-labels.mjs; RULES section 6 adds rows here.
- `.agent/W1-UX-combined-owner-walkthrough.md`: read by tools/checks/test_evidence_checks.mjs.
- `.agent/owner-walkthrough-notes-2026-11-01.md`: pending: uncommitted change in the main checkout; move after it is committed.
2. Build sheets and specs: the table below. A split sheet's `README.md` maps an old
   `file:line` to its part and line (`split_specs.py --verify` reassembles it).
3. `.agent/owner-<topic>.md` -> `owner/owner-<topic>.md` (verbatim; 186 files).
4. Anything else, `.agent/<path>` -> `archive/agent-history/<path>` (1,840 files: reviews,
   packets, rulings, handoffs, architect notes, questions, probes). Each has one header line
   ("Finished; historical.", "Superseded by X on 2026-11-18." or, for the 30 files whose decisions are
   still indexed live, "Finished work; its decisions remain live per `.ai/decisions/INDEX.md`."), so an old `:line` is +1.
   Superseded: `lane-rules-2026-11-12.md` by `.agent/lane-rules-vps-2026-11-12.md`, `current-plan-pointer.md` by `.ai/NOW.md`.
5. `.agent/coordinator-handoff.md` before 2026-11-18: `.ai/history/coordinator-handoff-to-2026-11-18.md`
   (verbatim after one header line, so an old `:line` is +1).
6. A `.agent/<ID>-evidence/...`, capture or log path: untracked in step 3; see
   `/opt/assetecon/evidence/repo-untracked-2026-11-18/` (`MANIFEST.tsv`).

## Specs

| Old path | New path |
| --- | --- |
| `.agent/W2-02-build-spec.md` | `specs/W2-02/` (spec.md) |
| `.agent/W2-03-build-spec.md` | `specs/W2-03/` (spec.md) |
| `.agent/W2-04-build-spec.md` | `specs/W2-04/` (split: README.md maps sections and old lines to parts) |
| `.agent/W2-05a-build-spec.md` | `specs/W2-05a/` (spec.md) |
| `.agent/W2-05b-build-spec.md` | `specs/W2-05b/` (split: README.md maps sections and old lines to parts) |
| `.agent/W2-06-build-spec.md` | `specs/W2-06/` (split: README.md maps sections and old lines to parts) |
| `.agent/W2-07-build-spec.md` | `specs/W2-07/` (split: README.md maps sections and old lines to parts) |
| `.agent/W2-F-build-spec.md` | `specs/W2-F/` (spec.md) |
| `.agent/W3-01-build-spec.md` | `specs/W3-01/` (split: README.md maps sections and old lines to parts) |
| `.agent/W3-02-build-spec.md` | `specs/W3-02/` (split: README.md maps sections and old lines to parts) |
| `.agent/W3-03-build-spec.md` | `specs/W3-03/` (split: README.md maps sections and old lines to parts) |
| `.agent/W4-01-build-spec.md` | `specs/W4-01/` (split: README.md maps sections and old lines to parts) |
| `.agent/W4-02-build-spec.md` | `specs/W4-02/` (split: README.md maps sections and old lines to parts) |
| `.agent/W4-03-build-spec.md` | `specs/W4-03/` (split: README.md maps sections and old lines to parts) |
| `.agent/W5-01-build-spec.md` | `specs/W5-01/` (split: README.md maps sections and old lines to parts) |
| `.agent/W5-02-build-spec.md` | `specs/W5-02/` (split: README.md maps sections and old lines to parts) |
| `.agent/W5-03-build-spec.md` | `specs/W5-03/` (split: README.md maps sections and old lines to parts) |
| `.agent/W5-04-build-spec.md` | `specs/W5-04/` (spec.md) |
| `.agent/W5-F1-build-spec.md` | `specs/W5-F1/` (spec.md) |
| `.agent/W6-01-build-spec.md` | `specs/W6-01/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-CH-0.md` | `specs/CH-0/` (spec.md) |
| `.agent/build-sheet-CH-1a.md` | `specs/CH-1a/` (spec.md) |
| `.agent/build-sheet-CH-1b.md` | `specs/CH-1b/` (spec.md) |
| `.agent/build-sheet-CH-2.md` | `specs/CH-2/` (spec.md) |
| `.agent/build-sheet-CH-3.md` | `specs/CH-3/` (spec.md) |
| `.agent/build-sheet-CH-4.md` | `specs/CH-4/` (spec.md) |
| `.agent/build-sheet-CH-5a.md` | `specs/CH-5a/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-CH-5b.md` | `specs/CH-5b/` (spec.md) |
| `.agent/build-sheet-CH-5c.md` | `specs/CH-5c/` (spec.md) |
| `.agent/build-sheet-CH-5d.md` | `specs/CH-5d/` (spec.md) |
| `.agent/build-sheet-CH-6.md` | `specs/CH-6/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-CH-9.md` | `specs/CH-9/` (spec.md) |
| `.agent/build-sheet-CH-9b.md` | `specs/CH-9b/` (spec.md) |
| `.agent/build-sheet-COV-PARTIAL.md` | `specs/COV-PARTIAL/` (spec.md) |
| `.agent/build-sheet-DD-1.md` | `specs/DD-1/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-DEMO-COMBINED.md` | `specs/DEMO-COMBINED/` (spec.md) |
| `.agent/build-sheet-DEMO-SPARSE.md` | `specs/DEMO-SPARSE/` (spec.md) |
| `.agent/build-sheet-DIESEL-1.md` | `specs/DIESEL-1/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-FIX-COLD-DRAIN.md` | `specs/FIX-COLD-DRAIN/` (spec.md) |
| `.agent/build-sheet-FUEL-1.md` | `specs/FUEL-1/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-IDX-GAPS.md` | `specs/IDX-GAPS/` (spec.md) |
| `.agent/build-sheet-LINK-LINEAGE.md` | `specs/LINK-LINEAGE/` (spec.md) |
| `.agent/build-sheet-MD-0.md` | `specs/MD-0/` (spec.md) |
| `.agent/build-sheet-OUT-C.md` | `specs/OUT-C/` (spec.md) |
| `.agent/build-sheet-OUT-D.md` | `specs/OUT-D/` (spec.md) |
| `.agent/build-sheet-OUT-E.md` | `specs/OUT-E/` (spec.md) |
| `.agent/build-sheet-OUT-W.md` | `specs/OUT-W/` (spec.md) |
| `.agent/build-sheet-OWN-GAPS-2026-11-08.md` | `specs/OWN-GAPS/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-POLISH.md` | `specs/POLISH/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-sheet-SCN-kobo-reserve.md` | `specs/SCN/` (spec.md) |
| `.agent/build-sheet-TEST-drift.md` | `specs/TEST-drift/` (spec.md) |
| `.agent/build-sheet-WALK1.md` | `specs/WALK1/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-spec-commercial-2026-10-27.md` | `specs/Lane-C/` (split: README.md maps sections and old lines to parts) |
| `.agent/build-spec-telemetry-2026-10-27.md` | `specs/Lane-T/` (split: README.md maps sections and old lines to parts) |
| `.agent/repo-declutter-recommendation-2026-11-18.md` | `specs/DECLUTTER/repo-declutter-recommendation-2026-11-18.md` |
| `.agent/review-declutter-01-start-path.md` | `specs/DECLUTTER/review-declutter-01-start-path.md` |
| `.agent/packet-declutter-02.md` | `specs/DECLUTTER/packet-declutter-02.md` |
| `.agent/review-declutter-02.md` | `specs/DECLUTTER/review-declutter-02.md` |
| `.agent/packet-declutter-03.md` | `specs/DECLUTTER/packet-declutter-03.md` |
| `.agent/review-declutter-03.md` | `specs/DECLUTTER/review-declutter-03.md` |

## Old paths deliberately not rewritten

- Runtime values in code (a rewrite would change output or a model card): `backend/assetops_backend/financials/fuel_cost.py`
  (`source`, `reviewer`), `financials/fuel_cost_v2.py` (`source`, `reviewer`), `tools/probe_kisiwa_fuel.py`,
  `tools/probe_kisiwa_nights.py` (ruling text in probe output), `tools/w502_cold_work_walkthrough.py`.
- Data read at run time or frozen ("never edited to pass"): `backend/conversions/*.json`,
  `config/chain/perf-budgets-any-range-v1.json`, `host/fixtures/diesel-*/*.json`,
  `frontend/src/test/productVocabulary.json`.
- Mocks: `frontend/mockups/v71/*.html`, `frontend/mockups/v72/*.html`.
- `.agent/W1-UX-combined-owner-walkthrough.md` (read by `tools/checks/test_evidence_checks.mjs`) and
  `.agent/owner-walkthrough-notes-2026-11-01.md` (pending; uncommitted change in the main checkout).

## Branches that still hold old paths

`task/product-direction-layer4-design` and `task/gtm-documents` (and any other branch cut before
step 4): their text keeps `.agent/...` citations until they merge `main`; this map resolves them.
Merge instructions: `specs/DECLUTTER/packet-declutter-04.md`.

## Step 5 (Docs and tools, 2026-11-18)

Base `d05bf668c`. `tools/declutter/step5_map.py` is the executable form; `move_step5.py --verify` proves
every moved file is its base bytes plus at most one header line. Citations in live text and code comments were
rewritten by `move_step5.py rewrite`; verbatim records (archive, owner files, spec parts, `.ai/history/`) keep
old paths and resolve here. A file with a header has old `:N` at `:N+1`, except a shebang script's line 1
(the header is line 2 there); files with no header (owner words, owner draft, JSON, the two live HTML
documents) keep their line numbers.

| Old path | New path | Header |
| --- | --- | --- |
| `Docs/simulator_design.md`, `_v2.md`, `_v3.md`, `Docs/simulator-design-v2-alignment.md`, `-v3-alignment.md`, `Docs/multi-vertical-capability-read.md`, `Docs/multi-vertical-build-plan.md`, `Docs/mini-grid-demo-architecture-and-roadmap.md`, `Docs/declared-capability-and-what-checks-it.md` | `Docs/archive/2026-09/<same name>` | Superseded by X |
| `Docs/multi-vertical-brief-verbatim.md`, `Docs/queue-review-feedback-verbatim.md`, `Docs/lab-cockpit-proposal.md` | `Docs/archive/2026-09/<same name>` | none (owner words or draft; status in `Docs/archive/README.md`) |
| `.agent/convertion_potential.html`, `.agent/decision-intelligence-mechanism-2026-11-14.html` | `Docs/demo-sprint/<same name>` | none (live) |
| `frontend/docs/architecture/check_v69_dependency_registry.cjs`, `delivery_next_work.cjs`, `test_delivery_next_work.cjs`, `check_v69_ledger.py` | `archive/frontend/docs/architecture/<same name>` | Retired guard |
| `frontend/docs/architecture/v69-subject-area-briefs.json`, `v69-model-homes.json` | `archive/frontend/docs/architecture/<same name>` | none (JSON) |
| `tasks/README.md` before step 5 (the S1-S7 tables) | `tasks/archive/site-first-2026-10/queue-tables.md` | Superseded by X; `tasks/README.md` is now a short pointer |
| `tools/<name>` for the 28 names in `step5_map.TOOLS_FINISHED` (`ap1_parity_probe.py`, `dd1a1_*`, `dd1a2_addday_l2.py`, `dd1b1_coh3_probe.py`, `dd1b2a_*`, `lr01-money-evidence.mjs`, `pr2a-`/`pr3-` price evidence, `s405-provenance-evidence.mjs`, `s5-overview-evidence.mjs`, `v01b-*`/`v01b_*`, `w1-fidelity-audit-index.mjs`, `w502-`/`w504-` work evidence, `w5f1-d3-evidence.mjs`) | `archive/tools/<name>` | Finished; historical |

## Later moves (20 Nov 2026)

| Old path | New path | Note |
| --- | --- | --- |
| `.agent/owner-assure-per-brief-2026-11-19.md`, `.agent/owner-design-regeneration-request-2026-11-19.md`, `.agent/owner-recreate-document-packs-2026-11-19.md`, `.agent/owner-summary-confirmations-2026-11-19.md` | `owner/<same name>` | Duplicates removed; the `owner/` copy is the record (summary-confirmations: the `owner/` copy is the superset) |
| `.agent/owner-design-intro-and-motivation-request-2026-11-18.md`, `.agent/owner-grounded-transition-request-2026-11-18.md` | `owner/<same name>` | Moved; rows in `owner/index-6.md` |
