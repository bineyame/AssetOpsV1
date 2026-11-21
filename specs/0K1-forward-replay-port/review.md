# 0K1 review

## Round 1: discovery review (W5), head `1b2c1ec90`

Reviewer: fresh Claude reviewer (not the author), 2026-11-21. Diff `main...1b2c1ec90`.

**Summary (verdict ACCEPT).**
- All five cases replay exactly to the kernel's own trajectory (Fraction equality per step: K-BASE under v5, v6 and v7,
  K-START, K-STOP, K-RES at 25 plus the no-setting anchor, and K-CLIP). My own probe also found the replay's whole
  trajectory (every stock and every interval measurement) equal to the kernel's on K-BASE v7.
- The Lab port is unchanged. `execution_ports.py`, `execution_adapter.py`, `simulator/` and `tools/` are not in the diff.
  The component ids are `pv-array`, `pv-inverter` and `battery-pcs` as printed. There is no database, route or served text.
- The adapter computes only the PV inversion, the tank identity and the totals. Settings go in as single whole-interval
  override forcings. The order of checks matches §2.4.
- Q1: T10's per-load check is a sound proof. No per-load projection field is needed (see below).
- Q2: T10's check is sound, but T4 cannot tell the reserve path from the start path at 25. One extra K-RES value (32)
  does tell them apart; I recommend adding it (Low, F1).
- No High or Medium findings. There are two Low findings, both optional.

### Checks run (this review)

- `heavy-slot.sh -- pwsh tools/run-host-tests.ps1 -- host/tests/test_0k1_forward_replay.py
  contracts/tests/test_0k1_forward_replay_contract.py backend/tests/test_0k1_replay_port_seam.py -q`: `65 passed in 4.89s`.
- `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): passed. `check-agent-workflow.ps1`: passed.
- `grep float(|round(` in the three new modules: none.
- `git diff --stat main...1b2c1ec90 -- simulator backend/assetops_backend/runs/execution_ports.py host/execution_adapter.py tools`: empty.
- I did not rerun the full suite. I cite the implementer's same-revision regression run (249 passed) and fast check-all
  (40 guards). The backend seam test ran on the host only, not in the container tier (packet §5 says the same).

### Probes (scratch script that imports the test module's reader; heavy slot; nothing committed)

| Probe | Result |
|---|---|
| K-RES reserve 25: kernel / correct replay / P4 (setting written to the start threshold) | running 0 / 0 (exact) / 0, **P4 equal to the kernel** |
| K-RES reserve 32 (`site_edit` 32 on reserve-trial): kernel / correct replay / P4 | running 46 / 46 (exact) / 0, **P4 differs** |
| P2 (loads matched by position) on K-BASE v7: projected step fields | equal to the kernel |
| P2: the replay trajectory's `load-served-power@<load>` series | **differ** from the kernel's |
| Correct adapter: per-load served, and every boundary's stocks and measurements | equal to the kernel's |

The minimum SOC on reserve-trial is 1315/38 (34.605 %). The kernel serves `min(total demand, supply)` and then allocates
it over the loads in sorted order (`mini_grid.py:706-719`). So total unserved energy, and with it dispatch, SOC and fuel,
depends on the loads only through their sum. This confirms the builder's Q1 analysis.

### Mid-build questions (recommendations for the Architect)

- **Q1 (P2).** I recommend accepting T10 as P2's test, with no type change. T10 checks that each `load-demand@<id>`
  forcing in the plan carries series `<id>`, matched by id. Since T1 shows the request equals the kernel's own recorded
  per-load demand, and the kernel is deterministic, a correct per-load input is enough to give correct per-load
  behaviour. My probe confirms this: per-load served power is equal when the mapping is right and differs under P2. A
  per-load projection field is not needed by 0K1's acceptance. Leave it to `0M` if headroom needs it. Optional
  strengthening is F2. One line for the Architect: "Q1: T10 is P2's test; guide row P2 reads T10."
- **Q2 (P4).** T10's check (one reserve forcing at the reserve address, with value 25, and the start threshold left
  unchanged) is sound and catches P4. But the guide named T4, and at 25 the two paths give the same trajectory. That
  matters because 0K2 values exactly this reserve option. A reserve setting strictly between 29.6 and 34.6 tells them
  apart, with no new fixture file: the same scenario and the same `_reserve` edit. My probe at 32 gives a correct replay
  that is exact (46 running steps) and a P4 replay with 0. I recommend adding it (F1). One line for the Architect:
  "Q2: T10 stands; add K-RES at 32 to T4 so P4 also fails T4."

### Findings

- **F1 (Low, preference with evidence; non-blocking).** `host/tests/test_0k1_forward_replay.py:282-296` (T4). K-RES at
  25 cannot tell the reserve forcing apart from a lowered start threshold, so T4 alone does not show that the setting
  works through the reserve. What would fix it: add a `res-32` kernel run (`_mini(TRIAL, site_edit=_reserve(32))`) and a
  replay of `recorded_request(kernel("res-30"), "reserve-32", ReplaySettings(reserve_soc_pct=Fraction(32)))`, with step
  parity, `running_steps > 0`, and the guide's P4 row updated to "T4 and T10". The cost is 2 kernel runs (the count
  goes from 20 to 22).
- **F2 (Low, optional).** T1 proves the per-load mapping only at the input level (T10). An output-level check needs no
  type change and no extra run: in one T1 case, wrap `execute` in a recording `execute_fn` and compare the replay
  trajectory's `load-served-power@<load>` series with the kernel's. This makes P2 fail T1 as D-0K1.10 intended.

Nothing else found. 7b: the docstring of `project` (`host/forward_replay.py:308-310`) carries the tank-bound note.
Unit 1's commit has the adapter without `project`; only the final state is judged, and it is complete.

### Residual risk not named in the packet

- The no-setting forcing check in T10 covers only K-BASE. The stop-60 replay at 70 drops the base run's own stop row,
  and the test asserts this, so P6 is covered.
- A load set read from forcings assumes every load has a `load-demand@` forcing in the base run. A load with no
  demand forcing would be invisible to the plant. No shipped scenario has one, and `0K2` reads real series.
