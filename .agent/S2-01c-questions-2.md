# S2-01c phase 2 — design choices the packet and decisions do not fix

Implementer, 2026-10-09. Each item is built with the stated fail-closed default; none blocks phase 3. All are local to the host schedule, the v2 profile or the new gateway ops.

## Q1 — Which runs use the virtual publication clock

The decision says "per registered Lab run"; AC4 also says keep S2-01b's refusal for unsupported profiles and preserve old runs' bytes.
Options: (a) every registered run; (b) only runs whose frozen profile declares it.
**Built: (b).** `PublicationProfile.publication_clock` (`GATEWAY_UTC` default, `RUN_VIRTUAL` on the new `registered-kobo-publication` v2). v1 and Lab v3 registered runs keep gateway-UTC `published_at` and the delay refusal; their historical bytes are untouched. Gateway: `admit` stays real UTC; new op `admit_at_run_clock` stamps from the run clock.

## Q2 — Explicit advancement while the world run is still executing

Decision: "a world step may advance the publication clock through its reached instant; after world execution completes, the operator may advance further".
Options: (a) refuse an explicit target beyond the world's reached instant until the world completes; (b) allow it at any time.
**Built: (a)** (`PUBLICATION_AHEAD_OF_WORLD`). Under (b), every later world step would publish ordinary, undelayed readings with `published_at` after their source time, i.e. a fabricated delay the scenario never declared. Consequence: before completion, a delayed report is released by the world step that reaches or passes its due instant (the 07:00 sample due 07:10 is stamped 07:15 by the 07:15 step).

## Q3 — No report can still be pending after the world run

Run setup refuses a scenario entry whose window outlasts the interval (`INTERVAL_INVALID`), and a delay window is half-open, so the run's last sample cannot be held. The fixture therefore releases its second report exactly at its due instant, the run's last instant (14:45 sample, due and stamped 15:00). Advancing past the end is proven (clock moves, nothing released, no kernel step, bytes unchanged) but releases nothing.
Options: (a) accept; (b) allow a delay window, for `RUN_VIRTUAL` profiles only, to end after the interval (a run-setup change), so a report is pending after completion; (c) let a world step not advance the clock (operator-driven only).
**Built: (a).** (b) is the smallest change if the owner wants the "released after the world run" demo; (c) contradicts the decision's world-step rule.

## Q4 — Where the Lab-private schedule lives

**Built:** `host/publication_schedule.py`, one JSON document per run under `var/publication-schedules` (beside the Stage root when one is injected), atomic replace. It holds the Lab clock, world reached instant/complete flag and each delayed report (key, source time, scheduled release, delay event id, exact public text, state, release clock, message ID). Phase 3 serves it through the Lab API; it is never sent to the gateway.

## Q5 — Explicit advancement after a host restart

With no live session the host cannot regenerate the series without re-executing the world. **Built:** advancement then releases only the schedule's due delayed reports (the undelayed series stays as admitted). With a live session it re-drives the whole series too, which is the retry after a link loss. An interrupted (non-terminal) run cannot be advanced past its reached instant (Q2).
