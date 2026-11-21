# 0K3 review

## Round 1: discovery review (W5), 2026-11-21

Reviewer: Claude (fresh, not the author). Branch `task/0K3-replay-reader` at `dbe164f54` (commits `898ddae00`,
`afef9c26d`, `dbe164f54`), diffed against `git merge-base main HEAD` = `e9d6cdfb1`.

**Summary (verdict: ACCEPT WITH FIXES, all Low; none blocks merge)**

- The reader follows spec §2.2 and §2.3 and rulings D-0K3.1 to D-0K3.20. I checked it line by line and found no correctness defect.
- Nothing is filled. A gap, a non-GOOD part or an off-grid instant leaves `None`, never 0. The input class comes only from the source mode: RECORDED or SIMULATED. The study then stamps MODELLED on every result.
- The season matches 0K2's `observed_series` field by field (T1), and the study gives the same `Calibration` (T2). I re-ran both: 2 passed.
- The tests are strong. I wrote 15 plants of my own, different from the builder's 16, and every one failed at least one test. The clean control passed 33 of 33.
- The three declared deviations are all accepted. Each was forced by the spec's own text or by the envelope contract.
- Mid-build Q1: the builder's default is safe. The zone always comes from the Site, and KOBO-001 is configured as `Africa/Addis_Ababa`. 0K2's season uses the same zone, so the spec's Nairobi was a slip.
- Findings: L1 an uncaught zone error; L2 a looser import pin; L3 the spec text and the mid-build count to be amended.

### Checks run (this review, revision `dbe164f54`)

| Command | Result |
|---|---|
| `heavy-slot.sh -- pytest test_0k3_replay_series.py test_0k1_replay_port_seam.py test_0k2_replay_study.py` | 62 passed, 4.4 s |
| `heavy-slot.sh -- pwsh tools/run-host-tests.ps1 -- host/tests/test_0k3_series_equivalence.py` | 2 passed (T1, T2), 17.9 s |
| `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_0k3_replay_series_postgres.py` | 6 passed (G1/G1b, G2, G3, G4, G4a, G4b), 160 s; afterwards no `%0k3%` database remained (read-only `pg_database` listing) |
| `pwsh tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set) | Architecture check passed |
| `pwsh tools/check-agent-workflow.ps1` | Agent workflow check passed |
| Reviewer plants (below) | 15 of 15 caught; control 33 passed |

I did not re-run `check-all`, `contracts/tests` or any full suite. For those I cite the packet's same-code run at `afef9c26d`; `dbe164f54` adds only the packet, the state and index lines, and the spec status line.

### Reviewer plants (my own; `replay_series.py` swapped in through a pytest plugin, the worktree untouched)

| Plant | Failed |
|---|---|
| A: spec §2.3 step 1 read literally (an instant at `t_0` skipped) | B1, B2, B5 x6, B6 x2, B6b, B8, B10 x2, B11 (15) |
| B: input class counted over non-GOOD readings too | B8 |
| C: off-grid instants floored onto a step (a tolerance) | B6 x3 |
| D: an untiled step becomes `Fraction(0)` instead of `None` | B2, B5[unit] |
| E: overlap check removed | B4 |
| F: loads in descending code order | B1, B7, B10 |
| G: crossing-the-edge refusal removed | B3 |
| H: naive `knowledge_at` accepted | B10[knowledge_at] |
| I: `READER_BINDING_CHANGED` removed | B7 |
| J: unit check removed | B5[unit] |
| K: `DECIMAL` check removed (Fraction parses `1e3`) | B5 x3 |
| L: a mean ending at `window.end` skipped | B1, B3, B10 x2 |
| M: a non-GOOD reading still sets its value | B2, B5 x2, B9 |
| N: window at UTC midnight, the zone ignored | B10 x5, B11 |
| O: duplicate instants at one step allowed | B4 |

I also checked how the expected values are made (W2). B1 and G1 use literal tuples written in the tests. T1 compares with `kobo_season.observed_series`, never with a reader helper. The S8 writer spells out its own addresses and quanta.

### The honesty rules

- **A missing value is never 0.** A step gets a value only when its means tile it exactly and are all GOOD (`replay_series.py:264-268`). An instant is read only at a step start (`:245-253`). Anything else stays `None`. Plants D, C and M prove it.
- **Every result says what it is.** `input_class` comes only from the source mode, counted over GOOD placed readings (`replay_series.py:282-288`). A mix or an unknown mode is refused. The study adds `EVIDENCE_CLASS = "MODELLED"` to every result (`replay_study.py:57`). B11 and T2 show `input_class` passing through to the study result unchanged.
- **No value is moved.** `pv_power` is never read as available PV: B7b, G1b and G4a fail if it is. The load is `feeder_demand` by asset code, and `load_role` is stated on every read.

### Deviations (each judged on its own)

1. **`types` added to the import set: accepted.** Spec §2.1 defines `UNITS` and `INPUT_CLASS_BY_MODE` as `MappingProxyType`, which lives only in `types`. Its own import list therefore cannot be met. The spec is wrong here, not the code (see L3).
2. **Instants skipped only outside `[start, end)`: accepted, and needed.** Read literally, §2.3 step 1 (`COALESCE(interval_end, source_time) <= window.start`) skips every instant at `t_0`. That includes the start fuel, so every read would refuse `READER_START_FUEL_UNKNOWN`, against the spec's own B1, G1 and T1. Plant A confirms 15 tests catch the literal reading. The builder's rule also skips an instant at `window.end`, which is right: it is the next day's `t_0`. The rule for means is unchanged.
3. **G1 stores canonical decimals: accepted.** The envelope contract refuses trailing zeros (`contracts/assetops_contracts/source_envelope_v3.py:85,137`, used by v4 at `:247,295`). The values are numerically R0's, and G1 asserts R0's literal tuples. R0 itself still feeds `"12.50"`, `"3.00"` and `"24.000"` to the reader, so non-canonical text is still covered.

The packet's deviations 4 and 5 are also sound: `readings_used` follows B1's 2,017, and an empty interval is refused. They are part of L3.

### Mid-build Q1 (Kobo's zone)

The builder's default is safe. The reader never assumes a zone: it takes `site.timezone` (`replay_series.py:326`) and returns it as `SeriesRead.timezone`. KOBO-001's configured zone is `Africa/Addis_Ababa` (`backend/conversions/mechanism-v1.json:17`). 0K2's season and frame use the same zone (`host/tests/kobo_season.py:40-41`), so Addis Ababa is the right answer and the spec's Nairobi was a slip. Both zones are UTC+3 with no clock change, so G4b's window and subject are the same either way. G4b's assertion `zone == "Africa/Addis_Ababa"` (`test_0k3_replay_series_postgres.py:239`) will catch a later configuration change. For `6c`, the only remaining point is to build its `StudyFrame` from `read.timezone`, never from a literal.

### Findings

**L1 (Low, acceptance gap against §2.2 step 2): an unresolvable zone can escape as an OSError.**
`replay_series.py:128` catches `ZoneInfoNotFoundError`, `ValueError` and `TypeError`. `ZoneInfo("Africa")` raises `IsADirectoryError`, so the read throws a raw error instead of `READER_WINDOW_INVALID` `timezone`; I reproduced this. It matters little, because Site zones are checked against `available_timezones()` when they are written (`sites/foundation_content.py:228`). But the reader's contract is "not resolvable by `ZoneInfo`", and `SiteRecords` is a protocol. Fix: also catch `OSError`, and add `"Africa"` to B10's zone cases.

**L2 (Low, a weaker test): the import pin admits any `from assetops_backend.analytics import X`.**
`replay_series.py:29` imports `from assetops_backend.analytics import dispatch_v3`. B10's AST pin (`test_0k3_replay_series.py:423-435`) records only `node.module`, which is `assetops_backend.analytics`. A later `from assetops_backend.analytics import adapters` would pass, against §2.1's "no adapter import". Fix: import `from assetops_backend.analytics.dispatch_v3 import ON_STATES, OFF_STATES`, or have the pin record `module.name` for `ImportFrom`.

**L3 (Low, process and spec text): the spec should say what was built, and the mid-build count is understated.**
Deviations 1, 2 and 5 are implementer decisions on points the spec got wrong or did not fix. Under `.ai/RULES.md` §4 (handshake, item 7) and §7 ("raise it, don't decide it"), they are mid-build questions, so the count is 3 to 4, not 1. Deviation 2 matters most: it corrects the core edge rule. Fix: the Architect amends spec §2.1 (add `types`), §2.3 step 1 (instants outside `[start, end)`), §2.3 step 4 (the empty or reversed interval) and §0 (c) (Kobo's zone), and the packet's count is corrected. No code change.

Not findings: the branch is named `task/0K3-replay-reader` rather than the spec's `task/0K3-replay-series` (immaterial). `READER_INPUT_CLASS` also counts GOOD means in a step that ends up untiled; the spec's "(GOOD and placed)" allows this, and it can only refuse more, never mislabel.

### What I could not verify

- The builder's plants P1, P4, P4b, P14 and P16 on the Postgres tests (G1, G1b, G2, G4a). I did not re-plant on the database. On the unit side, plants A, L and N cover the same rules.
- The packet's pre-flight print. Its file has been deleted; the facts it states agree with G1, G4 and G4b passing.
- check-all and the contracts suite (cited from the packet, as above).

### Residual risk the packet does not name

- **Only half-open, strictly tiled means are read.** A real EMS feed with jittered interval edges, for example `[t_k, t_k + 4:59.9)`, will leave every step `None`, and the study will refuse `INPUT_GAP`. This is honest, but it means the first real feed may produce no series at all. A ruling on tolerance (queue Q3's sibling for means) will probably be needed when the first feed lands.
- **`readings_used` counts non-GOOD readings,** and `off_grid` counts only instants. A caller reading coverage from these two numbers alone could over-read how much was usable. `6c` should take coverage from the series' `None`s.
