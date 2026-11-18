# Owner instruction, 2026-10-22 ~16:15

The owner asked "why is the progress slow". The coordinator proposed:
1. A builder pre-flight: before any code, each builder dry-reads its unit cards against the code and sends every question in one batch, so there is one Architect round.
2. Full suites only on a quiet machine: each run is scheduled when no builds or captures run, and the waiting time is used for spec work.
3. (Not adopted) fewer per-unit review stops.

Owner verbatim: "yes, adopt 1 and 2"
