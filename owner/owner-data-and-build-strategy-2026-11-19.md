# Owner answers 2026-11-19 (verbatim): test data and database build strategy

## Coordinator's framing (summary)

**Today.** Public-data-grounded simulator packs → field gateway → central ingestion. The walkthrough DB build is slow and fragile.

**Layer 4 adds:**
- commercial records as emulated exports;
- a daily factor structure;
- daily snapshots with triggers (OD-23);
- plan, Action and role records;
- replays K, M, E.

**Needs:**
- consistent months that balance to the cent;
- fast, deterministic rebuilds;
- honest provenance;
- incremental snapshot recalculation;
- scale without redesign.

**Candidate approaches:**
- vectorised bulk generation into canonical shapes, then COPY into a template DB that is cloned per run, with a small contract-tested slice through the real pipeline;
- constraint-first generation from the factor structure down;
- incremental, dependency-keyed snapshot materialisation;
- one seed manifest driving the generator, the evaluator, the documents and the mock-up.

**Questions:**
1. Scale target?
2. Is a small real-path slice enough?
3. Plain Postgres, or TimescaleDB if it measurably helps?
4. One fixed seeded demo world, or a rolling world that advances a day at a time so recalculation triggers can be demonstrated live?
5. Keep the public-data grounding, or use statistically matched synthetic series?

The owner answered:

> here are the asnwers 1.regarding scale, it is a post pilot concern but a real concern that will be tackled after the demo but a good foundation has to be laid now 2.small contract tested slice is ok for onw to give speed of developemnt for the demo 3.explore both options and combination ...etc this should be dicted by the applicaiton current and future needs 4.yes 5.i'm open to whichever provides speed, and use one or the other via configuration
