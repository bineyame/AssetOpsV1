# Owner instruction, 2026-10-23 ~10:30

The coordinator proposed: during a full suite, builders keep writing code and run only database-free unit tests and type checks. They hold Postgres-backed tests, browser captures, the full vitest run, builds and second suites until the suite ends, then run them in one batch.

Owner verbatim: "yes, switch to that"
