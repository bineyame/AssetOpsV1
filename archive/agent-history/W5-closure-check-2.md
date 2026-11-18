# W5 closure check, round 2 (R1-R7, V1-V6)

Checker: independent Claude reviewer, 2026-10-22, tree `main` 87701889. Read-only except this file.

## Verdicts

| Spec | Verdict | Open items |
| --- | --- | --- |
| W5-01 cold depth | READY | none blocking (one Low note) |
| W5-03 EV depth | READY | none |

## Registry (R1, V1)

Scratch copy of `frontend/` and `tasks/` in the scratchpad. A script applied every `registry nodes` and `panel rows` JSON block and every `ledger ... registry_dependencies` line from both specs, in order. There was no duplicate node, no unclassified block and no missing ledger screen. `check_v69_dependency_registry.cjs` exited 0 and listed all 7 screens at their expected panel counts (3, 1, 1, 3, 3, 1, 1). `check_v69_ledger.py` reported "valid: 110 screens, 258 panels". Real files untouched (git status clean).
The ledger file is now in the file lists of C3, C5, E3, E4 and E6. Node creation is single-owner: C3 creates the cold depth nodes, C5 the scenario nodes, E3 the depth nodes, E4 `I-W5-ev-health-ui`, E6 the scenario nodes (R7, V1).

## Item status

- R2/V2: closed. The S7 gateway panel is retained below `Condition and evidence` with cap 1900/2350 and 700/800 (same in both specs). Link targets are named (cold `ColdFoundationViews.tsx:646`, a live Link; EV `EvFoundationViews.tsx:631,688`, `UnavailableLinkEntry` today, which E4 makes live). The tests to update are named (`siteHealthBoundary`, `coldSiteViews`, `evFoundation`). These files and lines exist.
- R3/V3: closed. 422 in the C4/E5 text and refusal tables; matches `mini_decisions/model.py:34`.
- R4/V4: closed. A correction must equal revision 1's `from,to`, else 422 `*_SCENARIO_INVALID`; the list filters on revision 1's window.
- R5: closed. C1 reads door event kind and time from the Site-scoped evidence ledger, adding the read in `cold_depth.py`. The ambient reason now reads "not selected by the W2 assessment".
- R6: closed. `LIMITED` is in the Health enum; zero, one and two probes are covered.
- R7/V6: closed. C2 creates the client with both reads, and C3 may edit it. E2 creates `evDepthClient.ts` with all three reads, and E3/E4 may edit it.
- V5: closed. `weekly: []` gives `scheduled_seconds=0`, null ratios and `No service hours are declared in this window.`; the E1a assertion and the E2 literal are aligned. A missing schedule gives null and the separate "not established" literal.
- Spot-checked file:line claims: `model.py:34`, `cold_site_api.py:65` (nested `opened`), `ev_assessment_api.py:85` (`ev_gate`), `SiteHealth.tsx:313`, and the listed frontend and tool files all exist.

## New items

- Low, W5-01 C5 prose (line 109) says the panel row requires `[I-W5-cold-scenario-read, ...-ui]`, but the authoritative JSON also has `D-cold-domain` (it needs a data gate to pass the guard). The spec says the JSON is authoritative, so a builder following the JSON is fine. Optionally align the prose. The same pattern holds in the E6 prose (line 142). No fix is required.
- No undecided literal, missing unit-list file or W5-01/W5-03 contradiction found.

## Not verified

The "E1a/E2 builder injection" residual noted in round 1 (`EvReplayBuilder` accepting injected status rows or a swapped Foundation) is unchanged and is a risk, not an open item.
