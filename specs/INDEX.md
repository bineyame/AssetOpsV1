# Specs index

Build sheets and specs, one folder each: `specs/<ID>/` (old `.agent/` paths:
`CITATION_MAP.md`). Status: live (governs current
work), finished (built and merged; the record), superseded (replaced). Notes name
partial replacements. A sheet over the 15k-token cap (about 60 KB) was split by its
own headings into spec and rulings parts; its README.md lists the parts and
maps old line numbers. Open by section, never whole. Review rounds and packets for
finished work are in `archive/agent-history/`.

| ID | Title | Status | File | Size |
| --- | --- | --- | --- | --- |
| DIESEL-1 | Diesel-hybrid example Site Kisiwa | live — Handoff cites rulings through 9v; K8c unmerged | `DIESEL-1/README.md` (split) | 668 KB |
| OWN-GAPS | Kisiwa add-day, diesel-night check, records | live — Demo sprint rulings in force (D-SR, D-E5, D-PRICE) | `OWN-GAPS/README.md` (split) | 524 KB |
| DECLUTTER | Repo declutter recommendation, packets and reviews | live — steps 4-5 | `DECLUTTER/repo-declutter-recommendation-2026-11-18.md` | 42 KB |
| DS1 | Generator core and the July-September history (spec, reviewer guide, rulings, handshake) | live — handshake closed, rev 2; DS1m in_review (MB7, MB8 open) | `DS1-history-generator/spec.md` | 94 KB |
| BW1 | Non-screen build start: re-cut, waves, re-cut 2 (D-BW1.1-12) | live | `BW1-build-wave1/rulings.md` | small |
| T2 | Neutral package tests (check-all) | live — rev 2 | `T2-neutral-package-tests/spec.md` | small |
| L4-OPS | Operations in the structure (OD-26, OD-28) | live — design rev 16.16 §2.10 | `L4-OPS/rulings.md` | 10 KB |
| mockup-vnext-categories-snapshot | Mock-up headings, as-of | finished | `mockup-vnext-categories-snapshot/packet.md` | small |
| mockup-vnext-demo-items | Mock-up demo items | finished | `mockup-vnext-demo-items/packet.md` | small |
| mockup-vnext-professional | Mock-up pass | superseded | `mockup-vnext-professional/packet.md` | small |
| 3C1 | Person on commands (3C1a, 3C1b) | rev 2; 3C1a merged; 3C1b in_review | `3C1-person-on-commands/spec.md` | 15 KB |
| RC4-F1 | The database a URL really connects to: one resolver for every RC4 decision (0.5 unit; merges before 3A3) | in_review — spec rev 1, packet | `RC4-F1-database-name/spec.md` | 11 KB |
| ON1 | Operator tenant from one onboarding file; emulated roles granted automatically, real files refused until ON1b; served tenant; key erasure; runbook (2.0 units) | in_review — built on `task/ON1-operator-tenant`; mid-build Q1, Q2 open | `ON1-operator-tenant/spec.md` | 40 KB |
| 3B2 | Findings pinned to factors | in_review — built on `task/3B2-findings-pinned`, packet | `3B2-findings-pinned/spec.md` | — |
| IA-1 | Menu, page organization, shape rebuild; IA-2a the plan shape (§5.1: four tab routes, stepper, meters; 3 units) | rev 4; IA-1a, IA-1b, IA-1c merged; G2 seen by the owner (21 Nov); IA-2a specified, handshake next | `IA-1-shape-rebuild/spec.md` | 64 KB |
| 5a | Targets per factor, declarer recorded; page P5 | rev 2; unit 1 merged; units 2-3 in review | `5a-targets/spec.md` | 24 KB |
| 3A6 | Source profiles as data (CSV, one-sheet XLSX), admitted by command; migration 0067 (2.75 u) | merged | `3A6-source-profiles/spec.md` | 70 KB |
| 3A7 | One month reconciled against management accounts within 1%; migration 0069 (1.75 u) | merged | `3A7-month-reconciled/spec.md` | 38 KB |
| 5c | The month, explained: the one deep-dive screen (Portfolio tab "The month", hub shape): the bridge's figures only, k of n, carried Sites, Kisiwa's disagreement, "not yet reconciled" at the snapshot's as of, every gap with its record, the agreed change as an Action (3.5 units) | live — spec rev 2, handshake round 1 answered | `5c-deep-dive-screen/spec.md` | 56 KB |
| DDR | The deep-dive rehearsed end to end on emulated exports by the runbook, the board budget through a new profile with no code change, and a checker that fails on any skipped step (1.5 units) | live — spec rev 3, handshake round 2 answered | `DDR-rehearsal/spec.md` | 21 KB |
| 3C2 | The agreed change as an Action with creator, owner, due date; `record_action`; migration 0070 (1.5 u) | merged | `3C2-agreed-change-action/spec.md` | 20 KB |
| SC-1 | The statement composer: every server sentence composed from typed facts by a data catalogue through the one renderer, checked at load and by a guard (case per variant, legacy ratchet, hand-built sentence scan); 3A7 and 5c adopt (SC-1a 3.5 units) | in_review — SC-1a r3 ACCEPT; owner approved the two check-all lines | `SC-1-statement-composer/spec.md` | 89 KB |
| SC-1f | "Declared" word, stated-figure basis, logger stems, P55 allow merge (1.0 unit) | in_review — rev 1 built, packet r1 | `SC-1f-declared-word/spec.md` | 10 KB |
| 0K1, 0K2, 0M | Spikes K, M: replay port (merged, `0K1-forward-replay-port/`); Kobo study (4.5 u); Mto headroom (4 u, after 0K2) | specs | `0K2-kobo-replay-study/`, `0M-mto-headroom-replay/` | 43, 30 KB |
| DS3 | Bulk loader: set-based admission in the ledger writer, MINIGRID only, parity with central ingestion (4 units) | merged | `DS3-bulk-loader/spec.md` | 36 KB |
| DS4 | Template ladder, world commands and check, re-benchmark (3.5 units) | in_review — unit 3 fix round D-DS4.33 | `DS4-template-ladder/spec.md` | 64 KB |
| 4a | Energy to cash: delivered, losses, billed kWh, tariff (4 units) | merged — review ACCEPT; Q1-Q2, F1-F3 follow | `4a-energy-to-cash/spec.md` | 48 KB |
| 3B6 | Cold, EV structures | spec | `3B6-cold-ev/spec.md` | 39 KB |
| 3B4 | Structure observer | in review | `3B4-observer/spec.md` | 40 KB |
| ENV1 | Upload parses under limits, per-host slots (1.35 units) | merged | `ENV1-parse-limits/spec.md` | 38 KB |
| 0K3 | Replay series from stored readings (2.5 units) | merged | `0K3-replay-series-reader/spec.md` | 25 KB |
| 0K4 | Dispatch model path (owner accepted 21 Nov): a 2.5 u, b 2, c 1, d 2.25, e 2.75 (11.25 u with 0K4m); 0K4f queued; one-figure list; operator request | live — b merged; a in review (packet), c in review; d, e rev 2, build-ready | `0K4-dispatch-model-review/rulings.md`; a-e: `0K4a-dispatch-v8/`, `0K4b-fuel-curve-taper/`, `0K4c-declared-season/`, `0K4d-rerun-restate/`, `0K4e-candidate-energy/` | 130 KB |
| 1a | Optimize card states its day and scope: SC-1 line on the face, pin first (1.75 u) | live — rev 2, build-ready; merge held for walkthrough | `1a-optimize-card-scope/spec.md` | 18 KB |
| WK | Walkthrough DB: checked L2 copied to `assetops_polish_walk<label>_test`, two statements, rebuild, W1-W7, serve 8991/5491, teardown (1.4 u) | in_review: tool built on `task/WK-walk-world`; coordinator run (spec §5) pending | `WK-walkthrough-database/spec.md` | 27 KB |
| OWNER-AWAY | Decisions made for the owner during a delegated absence (21 Nov, ~12 h), each with reason and reversal | live — owner reviews on return | `OWNER-AWAY/decisions-2026-11-21.md` | 1 KB |

Finished, merged or superseded (folder kept as the record): `3B7a-structure-snapshot/`, `5b-attribution/`, `4d-litre-split/`, `3A3-emulators-contract-test/`, `4b-money-leaves/`, `2a-canonical-format/`, `3A1-commercial-record-store/`, `3A2-commercial-file-intake/`, `3A4-amounts-by-month/`, `3B1-structure-registry/`, `3B3-structure-read/`, `DS1b-canonical-writers/`, `3C0a-operator-accounts/`, `CH-0/`, `CH-1a/`, `CH-1b/`, `CH-2/`, `CH-3/`, `CH-4/`, `CH-5a/`, `CH-5b/`, `CH-5c/`, `CH-5d/`, `CH-6/`, `CH-9/`, `CH-9b/`, `COV-PARTIAL/`, `DD-1/`, `DEMO-COMBINED/`, `DEMO-SPARSE/`, `FIX-COLD-DRAIN/`, `FUEL-1/`, `IDX-GAPS/`, `LINK-LINEAGE/`, `Lane-C/`, `Lane-T/`, `MD-0/`, `OUT-C/`, `OUT-D/`, `OUT-E/`, `OUT-W/`, `POLISH/`, `RECON-1/`, `SCN/`, `T1-heavy-tool-slot-pool/`, `TEST-drift/`, `W2-02/`, `W2-03/`, `W2-04/`, `W2-05a/`, `W2-05b/`, `W2-06/`, `W2-07/`, `W2-F/`, `W3-01/`, `W3-02/`, `W3-03/`, `W4-01/`, `W4-02/`, `W4-03/`, `W5-01/`, `W5-02/`, `W5-03/`, `W5-04/`, `W5-F1/`, `W6-01/`, `WALK1/`, `mockup-vnext-categories-snapshot/`, `mockup-vnext-demo-items/`, `mockup-vnext-professional/`.
