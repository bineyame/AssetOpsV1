# S2-01c phase-3a design questions (Implementer, 2026-10-09)

Each has a fail-closed default that is implemented and committed. None blocks phase 3b.

## Q1. Which report is "the final in-interval sample" pending at completion?

Finding: the world observes at every boundary including its end instant (offset 720, source 15:00), and that reading is published like any other (phase 2's 293-envelope count includes it). The SOC cadence equals the 15-minute timestep. Any window that covers the 705 sample and ends after 720 therefore also covers the 720 sample: two reports held and released together, which `_refuse_a_delay_that_reorders` refuses (T026A, `PUBLICATION_DELAY_REFUSED`). A first attempt that counted only the in-interval part of the window exposed exactly that batch release, and was reverted.

Default (implemented): `kobo-daytime-post-run-publication` v1 holds the closing window over [710, 725). It holds only the run's final reading, the world's sample at its completion instant (source 15:00, due 15:05). The cadence rule is unchanged, and [705, 735) still refuses `PUBLICATION_DELAY_REFUSED` (tested). Alternative not taken: relaxing the cadence rule for the post-run tail, which would release two reports together.

Architect: confirm that the end-instant reading satisfies "a public reading sourced within the interval" for this demo. It is produced by the world run, which reaches 720 and makes no post-run source sample.

## Q2. The exact bound of the setup exception

Implemented in `service.py` `_post_run_release_window`: the exception applies only when the publication profile's `publication_clock == RUN_VIRTUAL`, the shape is WINDOW, the state is in `PUBLICATION_DELAY_STATES` and is declared with delays by the profile, `0 <= offset < length`, and `end <= length + timestep` (inclusive). Every other case keeps `INTERVAL_INVALID`, including forcings, `simulator-lab-publication` v5 (which declares the same delay state on GATEWAY_UTC), registered v1, an overrun of more than one timestep, and a window starting at the end instant. The `outside-the-interval` dispatch-rule statement names the exception, and `DISPATCH_RULES` keeps its count.

## Q3. A schedule read for an executed run with no stored schedule

Advance refuses `PUBLICATION_SCHEDULE_MISSING` when a stored execution artifact exists, no live session exists and no schedule exists (Q5, nothing reconstructed). The read route (`GET /runs/{id}/publication`) returns `status: NO_SCHEDULE` in that case and does not separate "never scheduled" from "missing after execution". Default: 3b renders NO_SCHEDULE as "no publication schedule recorded" and never as an empty queue. If the Architect wants a separate read status, it is a small port/API addition.

## Q4. Fault injection control

Default: fault injection stays fixture-only through the gateway IPC (`inject_fault`). `LabExecutionPort` gains no `inject` method, and the pinned absence test in `host/tests/test_lab_execution.py` still forbids one. Lab shows injected WARN/STOP/clock-offset only through the diagnostics read's `INJECTED_FAULT_FIXTURE` provenance. Packet AC5 does not require a UI control.
