# Owner decision: full test suite policy (2026-10-20)

Owner question, verbatim: "is the full test required all the time?"

Recommendation given:
1. Run the full suite alongside the first review, not before it. A failure still blocks the merge.
2. Skip it for slices that change no shared code and no database tables. Focused tests plus the code checks are enough, and merges to main still get the full run.
3. Queue a tooling task to run the suite inside the Docker container. It is estimated to cut the run from about 57 minutes to about 30.

Owner decision, verbatim: "yes, adopt both and queue the container task"

Applied: `.ai/ROLE_CONFIG.md` (backend tests rule), and the OPS-03 queue row in `tasks/README.md`.
