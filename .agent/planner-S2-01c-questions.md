# S2-01c questions for Architect — 2026-10-09

## Q1 — Release clock for a delayed registered Lab report

`D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary` assigns S2-01c deferred local admission: retain the reading and its original `source_time`, set `published_at` when it is actually released/sealed, and keep the V3/Batch V2 bytes stable on retry. S2-01b currently rejects registered runs with a frozen publication-delay window; its host regenerates the whole public series on each step, and a run may finish before a delayed report's scheduled release. A real wall-clock wait would make a compact repeatable Lab fixture slow and restart timing variable. The gateway must not read private scenario causes.

Options:

1. Give the Lab's public-report scheduler a persisted, explicitly advanced simulation clock. It keeps a private pending report with its public reading and declared release instant; advancement past that instant submits it once to the gateway. The gateway stamps `published_at` from the release/seal operation. A completed run can advance publication time without advancing the world again.
2. Use wall-clock scheduling in the host. Persist pending reports and a real UTC due time; background delivery resumes after restart. The demo waits or uses an accelerated test clock.
3. Keep the delay within the run interval and release only on later execution steps. A report due after the final step remains pending until a separate later run/action, narrowing the planned fixture.

Recommendation: **1** for the simulated-only Lab, with a visible labelled publication-clock control or deterministic test harness and no private cause in gateway reports. The local diagnostic should distinguish source time, scheduled release and actual `published_at`; S2-02 still supplies server `received_at`. Please specify whether option 1 fits the registered Lab contract and how the release instant should be represented when the host is paused or restarted.

Can implementation proceed before the answer? **Yes for phase 1** (R1, diagnostic wire/ledger and counters) and the independent UI carry. Phase 2 delay integration should wait for this decision; the existing fail-closed delay refusal remains the default and must not be silently removed.
