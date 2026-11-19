# Owner instruction, 2026-10-22 ~19:30

The owner asked "should all tests run diring slice or regression test should be specifically scoped?". The coordinator proposed tiered testing:
- each unit runs its focused tests;
- each slice merge runs a scoped regression: tests for the changed areas, tests for any shared file touched, the full frontend suite and check-all;
- the full backend suite is required for slices with a schema/migration change or a shared-plumbing change (main.py/composition, guards, seed tools, test fixtures/conftest);
- a safety-net full suite runs on main after every 2-3 merges, off the critical path;
- try 3 pytest workers once.

Owner verbatim: "yes, adopt that"
