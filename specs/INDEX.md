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
| 3C1 | Person on commands (3C1a, 3C1b) | rev 2; 3C1a merged | `3C1-person-on-commands/spec.md` | 15 KB |
| RC4-F1 | The database a URL really connects to: one resolver for every RC4 decision (0.5 unit; merges before 3A3) | in_review — spec rev 1, packet | `RC4-F1-database-name/spec.md` | 11 KB |
| ON1 | Operator tenant from one onboarding file; emulated roles granted automatically, real files refused until ON1b; served tenant; key erasure; runbook (2.0 units) | in_review — built on `task/ON1-operator-tenant`; mid-build Q1, Q2 open | `ON1-operator-tenant/spec.md` | 40 KB |
| 3B2 | Findings pinned to factors | live — spec | `3B2-findings-pinned/spec.md` | — |
| IA-1 | Menu, page organization, shape rebuild; IA-2a the plan shape (§5.1: four tab routes, stepper, meters; 3 units) | rev 4; IA-1a, IA-1b, IA-1c merged; G2 seen by the owner (21 Nov); IA-2a specified, handshake next | `IA-1-shape-rebuild/spec.md` | 64 KB |
| 5a | Targets per factor, declarer recorded; page P5 | rev 2; unit 1 merged; units 2-3 in review | `5a-targets/spec.md` | 24 KB |
| 3A6 | Source profiles as data: an operator's export (CSV or one-sheet XLSX) read through a JSON profile admitted against its sample by command, no code per layout; invisible characters, one source system per Site, coded paths mapped, S1 dynamic imports; migration 0067 (2.75 units) | live — spec rev 2, handshake answered | `3A6-source-profiles/spec.md` | 70 KB |
| 3A7 | One month reconciled against the operator's management accounts: money reads "not yet reconciled" until a closed month matches within 1%, saying what did not match; migration 0068 (1.75 units) | live — spec rev 2, handshake answered | `3A7-month-reconciled/spec.md` | 38 KB |
| 5c | The month, explained: the one deep-dive screen (Portfolio tab "The month", hub shape): the bridge's figures only, k of n, carried Sites, Kisiwa's disagreement, "not yet reconciled" at the snapshot's as of, every gap with its record, the agreed change as an Action (3.5 units) | live — spec rev 2, handshake round 1 answered | `5c-deep-dive-screen/spec.md` | 56 KB |
| DDR | The deep-dive rehearsed end to end on emulated exports by the runbook, the board budget through a new profile with no code change, and a checker that fails on any skipped step (1.25 units) | live — spec rev 2, handshake round 1 answered | `DDR-rehearsal/spec.md` | 21 KB |
| 3C2 | The agreed change recorded as an Action: an append-only record (migration next on the head, 0069 expected) with creator, owner and due date; only the executive agrees, the owner by role (executive and finance lead anywhere, a Site manager at their Site); `record_action` by command, idempotent; the read 5c shows, newest first, Open or Overdue; not valued (RC9) (1.5 units) | live — spec rev 2, handshake round 1 answered | `3C2-agreed-change-action/spec.md` | 20 KB |

Finished, merged or superseded (folder kept as the record): `3B7a-structure-snapshot/`, `5b-attribution/`, `4d-litre-split/`, `3A3-emulators-contract-test/`, `4b-money-leaves/`, `2a-canonical-format/`, `3A1-commercial-record-store/`, `3A2-commercial-file-intake/`, `3A4-amounts-by-month/`, `3B1-structure-registry/`, `3B3-structure-read/`, `DS1b-canonical-writers/`, `3C0a-operator-accounts/`, `CH-0/`, `CH-1a/`, `CH-1b/`, `CH-2/`, `CH-3/`, `CH-4/`, `CH-5a/`, `CH-5b/`, `CH-5c/`, `CH-5d/`, `CH-6/`, `CH-9/`, `CH-9b/`, `COV-PARTIAL/`, `DD-1/`, `DEMO-COMBINED/`, `DEMO-SPARSE/`, `FIX-COLD-DRAIN/`, `FUEL-1/`, `IDX-GAPS/`, `LINK-LINEAGE/`, `Lane-C/`, `Lane-T/`, `MD-0/`, `OUT-C/`, `OUT-D/`, `OUT-E/`, `OUT-W/`, `POLISH/`, `RECON-1/`, `SCN/`, `T1-heavy-tool-slot-pool/`, `TEST-drift/`, `W2-02/`, `W2-03/`, `W2-04/`, `W2-05a/`, `W2-05b/`, `W2-06/`, `W2-07/`, `W2-F/`, `W3-01/`, `W3-02/`, `W3-03/`, `W4-01/`, `W4-02/`, `W4-03/`, `W5-01/`, `W5-02/`, `W5-03/`, `W5-04/`, `W5-F1/`, `W6-01/`, `WALK1/`, `mockup-vnext-categories-snapshot/`, `mockup-vnext-demo-items/`, `mockup-vnext-professional/`.
