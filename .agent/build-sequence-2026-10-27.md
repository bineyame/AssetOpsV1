# Build sequence, two lanes, 2026-10-27 to 3 November

Architect: Claude (`.ai/ROLE_CONFIG.md` line 9). Sources: owner answers `.agent/owner-answers-open-questions-1-2026-10-27.md` and `-2-2026-10-27.md` (verbatim, the authority), `.agent/owner-build-plan-depth-2026-10-27.md`, `.agent/architect-reply-owner-q2-q3-2026-10-27.md`, `.agent/parallel-feasibility-2026-10-27.md`, `.agent/implementer-parallel-confirmation-2026-10-27.md` (its four adjustments are folded into the specs), `.agent/telemetry-rulings-2026-10-27.md` (amendment 2).

This is the index. Builders are briefed from the lane specs, which carry, for every task, the implementation approach, module boundaries, interfaces and signatures, data shapes, contracts touched, fault semantics, test seams and rejected alternatives:

- **Lane T (telemetry):** `.agent/build-spec-telemetry-2026-10-27.md`
- **Lane C (commercial):** `.agent/build-spec-commercial-2026-10-27.md`

Each spec ends with "Implementer questions and resolutions". An Implementer reviews both specs before the first code; the Architect answers there, and builders read the answered spec.

## 1. PYTHONPATH per lane (also at the top of each spec and each first task file)

Lane T, worktree `C:\Users\assef\Bineyame\AssetOpsV1-tel`:
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel\host;C:\Users\assef\Bineyame\AssetOpsV1-tel\field;C:\Users\assef\Bineyame\AssetOpsV1-tel"
```
Lane C, worktree `C:\Users\assef\Bineyame\AssetOpsV1-cc`:
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-cc\backend;C:\Users\assef\Bineyame\AssetOpsV1-cc\contracts;C:\Users\assef\Bineyame\AssetOpsV1-cc\simulator;C:\Users\assef\Bineyame\AssetOpsV1-cc\gateway;C:\Users\assef\Bineyame\AssetOpsV1-cc\host;C:\Users\assef\Bineyame\AssetOpsV1-cc"
```
Python for both: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`. Without the line, tests silently run the main checkout through the venv's editable installs.

## 2. Lane T, telemetry (first claim on the heavy-job queue until 30 Oct 23:59)

| # | Task | Scope | Main files | Acceptance gate | Stop | Est. |
|---|---|---|---|---|---|---|
| 1 | TEL-00 | Pre-flight, card corrections, port table | none | "no open questions" | ruling contradicts spec | 0.25 d |
| 2 | TEL-01 | Profile, decode, clock, aggregate, report, publish; the two checks | `field/assetops_field/*`, `field/tests/*`, two `.ps1` | vectors; D10 cases; round trip; checks green | a check needs an existing rule changed | 0.75 d |
| 3 | TEL-02 | Read-only Modbus TCP client | `modbus_tcp.py` | writes refused before any byte; exception map | any write FC needed | 0.5 d |
| 4 | TEL-03 | GX-shaped emulator, profile `-1`, pinned daytime JSONL | `field/tests/emulators/gx_server.py`, `field/profiles/gx-system-illustrative-1.json`, `host/tests/field_observation_fixtures.py` | every value reads back (at register resolution); writes 0; freshness | private value needed; range overflow | 0.75 d |
| 5 | TEL-04 | Poller CLI, focused E2E through a real gateway | `modbus_poller.py`, `host/tests/test_field_modbus_tcp_proof.py` | card list incl. pause → no report; restart → no stranded batch | gateway change needed; unexpected hold | 0.75 d |
| 6 | TEL-05 | Postgres acceptance, profile `-1` (heavy, alone, twice) | `host/tests/test_field_modbus_tcp_acceptance_postgres.py` | COMPLETED; evidence per role; UNKNOWN; assess completes; no consequence | central refusal; non-UNKNOWN provenance | 0.5 d |
| 7 | TEL-08 | BeagleBone Black stage 2 (TCP), real `serve_tls` (owner Q6) | `host/tests/field_bench.py` | TEL-05 gates on the board; uplink pull drains | Linux needs code change; no NTP; board unreachable | 0.75 d + owner 30 min |
| 8 | TEL-05b | Money-affecting Finding, money withheld (owner Q5) | profile `-2`, prolonged JSONL, second Postgres test | Finding cites only field IDs; UNKNOWN; `current_amount_shown` false with `MIXED_OR_UNKNOWN_SOURCE` | no Finding; any current amount shown | 0.75 d |
| 9 | TEL-07 | Claim records and terminal runbook | `.agent/TEL-*-review-packet.md`, `.agent/TEL-demo-runbook-2026-10-30.md` | reviewer reruns from runbook | demo DB or UI needed | 0.25 d |
| 10 | TEL-06a/b | Illustrative CSV collector (owner Q7 = c) | `export_csv.py`, CSV profile and fixture | card list | vendor naming requested | 0.75 d |

TEL-05b's focused parts (profile `-2`, prolonged JSONL, emulator unit 101) are light and may be built while the owner prepares the board; only its Postgres run waits for the queue after TEL-08.

**Owner actions for TEL-08 (coordinator flags them today):** confirm or buy a microSD card (8 GB or larger) and a 5 V 2 A barrel supply (about $16; nothing else is bought); flash Debian 13 IoT to the card and boot the board on the laptop's LAN by Ethernet; give the builder SSH key access; allow inbound TCP 8443 and 5020 on the laptop's Windows firewall (admin). Needed by **29 Oct 12:00**.

## 3. Lane C, commercial

| # | Task | Scope | Main files | Acceptance gate | Stop | Est. |
|---|---|---|---|---|---|---|
| 1 | CC-00 | Pre-flight | none | "no open questions" | — | 0.25 d |
| 2 | CC-R1 | Links, claim labels, beneficiary key (owner Q9), no-double-count check | `estate/financials.py`, `estate/money_invariants.py`, `actionPresentation.tsx`, `ClaimLabel.tsx` | beneficiary partitions; invariant `[]` on existing bodies; labels render | exact-key test outside w303 breaks | 1 d |
| 3 | CC-R2 | Placement (D5), combined estate producer; MG-C stand-in (owner Q11) | `estate/placement.py`, `coverage.py`, `portfolio.py`, `scope.py`, `tools/cc_estate_seed.py` | Appendix C D5 criteria | needs a fact not on the row | 1.5 d |
| 4 | CC-M | Combined schema slice, two revisions 0036 + 0037 (owner Q14); one full suite | `backend/migrations/versions/0036_*`, `0037_*` | up/down/up; trigger; full suites | existing migration needs editing | 0.5 d + suite |
| 5 | CC-D2 | Post-trial reassessment (owner Q10, Q12 wording) | `financials/trial_fuel_comparison.py`, store, routes, `SiteActionVerification.tsx`, s602b cases | 16/375; each reason; route walk; revision 2 | `plan_sha256` would change | 1.5 d |
| 6 | CC-D1 | Productive-use contribution (owner Q10) | `scenario_rules.py`, opportunity reads, estate line, `MiniScenarios.tsx`, w403 cases | 1.7, 3/25, 71; estate SINGLE_LINE | an existing `calculate()` case changes | 1.5 d |

EV and cold decisions appear as labelled declared illustrations (owner Q13); cold lots stay Site-only (Q15); the planning vocabulary is adopted (Q16); AI stays out of the demo (Q17). None of these needs a build task in this sprint. The battery-stress approximation is recommended for the next sprint (commercial spec, "Next sprint").

## 4. Calendar and checkpoints

| When | Lane T | Lane C |
|---|---|---|
| Tue 27 Oct | TEL-00, TEL-01 | CC-00, CC-R1 |
| Wed 28 Oct | TEL-02, TEL-03; review T1 (TEL-01..03); merge TEL-01 group first | CC-R1 review and merge (after TEL-01 group, merging `main` first) |
| Thu 29 Oct | TEL-04 (am); TEL-05 twice (pm, alone); review T2; TEL-05b focused parts (evening) | CC-R2 build; tier 0-1 only while TEL-05 runs |
| Fri 30 Oct | TEL-08 (am); TEL-05b Postgres twice (pm); TEL-07; review T3 | CC-R2 tier 2-3 in queue gaps; review |
| Sat 31 Oct | TEL-06a/b; Codex batched review of Lane T | CC-M (full suites, Lane C now has priority); CC-D2 starts |
| Sun 1 - Tue 3 Nov | — | CC-D2 review and merge; CC-D1; Codex batched review of Lane C |

**Checkpoint 29 Oct 12:00.** TEL-01..03 merged; TEL-04 green; owner board actions done; CC-R1 merged. If TEL-04 is not green, TEL-05b's focused work stops and the builder stays on TEL-04/05.

**Checkpoint 29 Oct 20:00.** TEL-05 green on two consecutive runs. If not, 30 Oct morning finishes TEL-05 and the slip rules below apply in order.

**Checkpoint 30 Oct 12:00.** TEL-08 green on the board, or slipped by rule. TEL-05b focused tests green.

**Checkpoint 30 Oct 18:00.** TEL-05b green twice; TEL-07 runbook rehearsed once end to end; claim records written.

## 5. What slips first if late

Lane T (TEL-05 is protected and never slips; nothing is rushed past a stop condition):
1. TEL-06a/b (already after 30 Oct).
2. TEL-08's stretch run on profile `-2`.
3. TEL-08 itself, to 31 Oct, if the board is not reachable by 30 Oct 09:00. The 30 Oct showing then uses the laptop result and says the board run follows.
4. TEL-05b, to 31 Oct, if it is not green twice by 30 Oct 16:00. The claim record then says the Finding proof follows; no Finding is shown on 30 Oct.
5. If TEL-05 itself is not green by 30 Oct 12:00, TEL-08 and TEL-05b both move to 31 Oct and the showing is TEL-04's focused result plus TEL-05 status.

Lane C (no fixed date; R1 is protected):
1. CC-D1 (to the next sprint; CC-M then carries only the trial table, numbered 0036).
2. CC-R2's combined estate, to per-vertical databases if the producer hits `INSTALL_CLOCK_CONFLICT` (pre-decided fallback).
3. CC-D2's `price_split` producer case, after the `verified` route walk is accepted.

## 6. Merge order and reviews

- Merge order: TEL-01 group first (the only shared guard change); then by readiness, each merge followed by a `main` merge into the other lane's open branch and a scoped regression; CC-M merges before CC-D2 and pays the full suites; safety-net full suite on `main` every 2-3 merges, in the queue.
- Reviews (fresh Claude reviewer per group, never the builder, never the other lane's builder): T1 TEL-01+02+03; T2 TEL-04+05; T3 TEL-08+05b+07; T4 TEL-06. C1 R1; C2 R2; C3 CC-M+D2; C4 D1. Codex: one batched review per lane at its milestone end.
- Coordination files (`.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md`, `tasks/README.md`): each lane edits its own section only.
