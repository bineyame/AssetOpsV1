# Codex handoff (kept current by the Claude coordinator)

Owner rule (23 Nov): when Claude's weekly usage reaches 99 %, Codex picks up implementation from this
file. The coordinator refreshes it after every merge and every owner decision. Last refreshed: 23 Nov.

## 1. The demo goal (read first)

- Audience: executives of mini-grid, EV-charging and cold-chain operators. Goal: convert them by
  showing value beyond monitoring tools: findings with money attached, decisions valued against
  doing nothing, and actions tracked and verified (`owner/owner-demo-objective-*.md`, memory
  "Demo objective").
- Four outcome categories frame every figure: Grow revenue; Optimize cost and efficiency; Protect
  asset and capital; Assure performance and returns.
- Honesty rules the owner enforces: one model-computed figure per quantity, loyal to the operating
  world, nothing fitted to a story; missing data reads "Not available yet", never 0; plain client
  language, no system vocabulary; the mockup (vNEXT) is the layout spec.
- The demo world: three operators (Lakeside Power mini-grids Kobo, Kisiwa, Mto; Harvest Cold rooms
  Mwea, Thika, Kirinyaga; Metro Bus depots Embakasi, Kasarani, Ruiru), readings 1 Jul to
  6 Nov 06:00, story date 6 Nov (story clock WK-SC approved, not built).

## 2. How to work (unchanged rules)

- Read `AGENTS.md`, then `.ai/START_HERE.md`, `.ai/NOW.md`, `.ai/ROLE_CONFIG.md`, `.ai/RULES.md`.
- One branch and worktree per part; never work on `main`'s checkout; merge only after review ACCEPT.
- Build from the part's build card (`specs/<lane>/cards/<part>.md`) and the code, test-first.
- Tests: `tools/heavy-slot.sh --db-lane -- pwsh tools/run-host-tests.ps1 -- <files>` from the worktree
  root; vitest only via `tools/heavy-slot.sh`; compare with `.agent/main-baseline/`.
- Before every merge: `python3 tools/check-decision-index.py`, `pwsh tools/check-agent-workflow.ps1`,
  `.venv/bin/python tools/checks/statement_catalogue.py` (exit 0), and for DD/simulator merges
  `simulator/tests/world` (PYTHONPATH=simulator:contracts:backend:host).
- Evidence under `/opt/assetecon/evidence/<slice>/`, never a shared scratch folder.
- Questions: BLOCKER, model or owner-level go to the Architect (rulings in
  `specs/<lane>/rulings.md`, index `.ai/decisions/index-*.md`); everything else keeps a default
  recorded in the packet.

## 3. State on 23 Nov

Merged: IA-P (all), 6a, 6c, 6h, DD1, DD2a, DD2b, DD3a, DD3c, DD4a, DD4b, DD4b follow-up, DD5a, DD3b, T1b (second DB lane),
main simulator fix (world tests 386/386).

In flight (branch, what is left):
- DD3b `task/DD3b-mini-plant`: fix round for D-DD.164/165 (fixed point: generate twice
  byte-identical), then merge. Known failures it may carry: 7 DDR rehearsal + ds4 t12 (closed by
  DD3d.4), six H5 (closed by DD3d.3).
- DD5a: merged 23 Nov.
- DD4b follow-up: merged 23 Nov.
- 6f1 `task/6f1-decisions`: U1 built (needs review); U2 (list, after IA-P3 and 6h, both merged) and
  U3 (decision page) remain; spec `specs/6f-decisions-screen/spec.md` rev 2, rulings D-P6.42-81.

## 4. Remaining work, in order (units)

1. DD3b: merged 23 Nov (owner accepted Kisiwa share 20.7/16.1/0/10.6 %).
2. DD5a: merged 23 Nov.
3. DD3d-a (2.75 u, card `specs/DD-demo-data/cards/DD3d.md`): floor, fuel records, H5. After DD3b.
4. DD3d-b (3.75 u, same card): fuel cost = burned x price (D-DD.163) and the owner-approved
   run-rate budget (D-DD.166). After DD3d-a.
5. DD5b (4.25 u, card `specs/DD-demo-data/cards/DD5b.md`) after DD5a, DD3b, DD3d-b, DD4b follow-up.
6. DD6 (5.25 u, card `specs/DD-demo-data/cards/DD6.md`): world built and served.
7. WK-SC story clock (3.0 u, `specs/DD-demo-data/spec-WK-SC.md`, card `cards/WK-SC.md`) after DD6.
8. 6f1 (5.25 u, spec rev 3): U1 review running, then fix round (D-P6.82/83), U1 merges first; U2 and U3
   then build in parallel from `specs/6f-decisions-screen/cards/6f1-U2.md` and `6f1-U3.md`; U3 merges
   before U2. Then 6f2 (choice on screen).
9. IA-PD demo routes (0.5 u, D-IAP.36) before the next demo build; IA-P: rebuild the world rung
   once before the next WK run.
10. 0K4f, Q11 (cold/EV monthly figures), Q12 (31-day cap).
11. Design-doc and vNEXT mock alignment pass: one pass AFTER DD lands (owner, 22 and 23 Nov;
    `owner/owner-docs-refresh-2026-11-22.md`). It is a deliverable, not optional. Detail in section 6.
12. Refresh `.ai/NOW.md` and `owner/SUMMARY.md` to the 23 Nov state (both lag; SUMMARY since 22 Nov).
    Not blocked; may be done any time and must be done before the alignment pass starts.
Backlog after the demo: `.agent/backlog-post-demo.md`.

Warning: after 6f1 U2 the Decisions list, inbox and waiting columns are empty until WK-SC prepares the
ten decisions; do not rebuild a demo app from main in that gap without telling the owner.

## 5. Open owner questions

- none (D-DD.166 approved 23 Nov: budget run-rate rule built as DD3d.5)

## 6. Design and document alignment pass (specified for whoever picks it up)

State: NOT done. DD builders already swept moved figures from the design docs and most
go-to-market docs. The narrative documents and the mockup were deliberately left.
All Docs paths below are under `Docs/demo-sprint/product-direction-layer4/`.

- Narrative documents to realign (write-up, HTML versions regenerated after): `layer4-transformation-design`,
  `product-transition-and-roadmap`, `phase-plan-and-acceptance`, `demo-site-scenario-manifest.yaml`
  (manifest header notes are current to rev 16.23; the doc text around it is not).
- vNEXT mockup (`interactive-mockup-vNEXT/`), items recorded by builders for this pass:
  - Thika incident: chart series and "50-90 °C·min" in `screens.js` (71, 77-78; window text 51, 399,
    627; `portfolio.js` 18, 21). Use `/opt/assetecon/worlds/DD4a-0c5d5fab7b90/` readings: peak
    5.477 °C at 20:24, above 5 °C 20:08-20:32, 72 min without cooling, hand start 20:22.
  - Kobo kit strings (18 `screens.js`, 5 `screen-manifest`, plus 40 kW ×4 and 0.30 L/kWh ×3):
    declared kit is 36 kW generator, 42 Pylontech US5000 (191.5 kWh), 0.2917 L/kWh.
  - Kasarani: 7 missed departures, 840.00 penalties, 2 short a night, stopgap 225.00 (was 2 / 240 / 1 / 90).
  - Cold energy: 1304 kWh + 0.0554 kWh/crate-day model; October bills 315.26 / 354.27 / 422.72;
    Kirinyaga +14 %, repair +149.26 net over 12 months.
  - Kisiwa: 904 L October diesel becomes 903 L and 1,173.90 cost, result +1,696.10, candidate share
    20.7 / 16.1 / 0 / 10.6 % (owner-accepted); GEN-KS-02 evening load ~70 %, not 95 %; Mto 32 L.
  - Portfolio headline and fuel-vs-target literals: after DD3d-b (D-DD.163 and the owner-approved
    run-rate budget D-DD.166, about -$197 behind plan); do not align these before DD3d-b merges.
  - `gen_docs.cjs`, `CHANGE-REGISTER.md`, `fixture-mapping.md`, `derivation-register.md` rows, and
    the generated `index.html`/`screen-manifest` follow `tools/ia_gates.cjs` (110/110, ~95 min) and
    the two shot runs, with no NaN/undefined and "Not available yet" for missing figures.
- Order: (1) refresh NOW and SUMMARY, (2) after DD6, regenerate the docs' derived figures with the
  D-DD.30 chain, (3) realign the narrative docs, (4) the mockup with its gates, (5) owner walkthrough.
- Rules: `.ai/RULES.md` §10 (owner document brief: existing to new, mechanism to value, change on
  merit, person in loop, short and illustrated). Plain client language, no system vocabulary. Every
  figure tagged to its source path as the DD sweeps did. The check is `check_manifest.py`, at main's
  count.
