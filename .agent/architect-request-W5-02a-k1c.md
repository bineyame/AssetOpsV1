# Architect request: W5-02a K1c open questions (global_detail, and the item-29 producer)

You are the AssetOps Architect (Codex). Read the latest Run entry and open questions in `MSYS_NO_PATHCONV=1 git show task/W5-02a-cold-action-root:.agent/W5-02a-phase-handoff.md` (head `3a3dedc4`), then the K1c card, the pre-flight rulings and readiness item 29 in `.agent/W5-02-build-spec.md`, and `.agent/W5-02-04-readiness-review.md` (item 29). Lesson: check every literal against the real code.

1. **`global_detail.py` (merged with W6-01c).** A domain Action link shows with no link there, while the Site and global rows show `/verification`. Give K1c the one-line fix at about line 98 plus a `test_w601c` test, as literal text, and add both files to K1c's list.
2. **The run-5 generated-scenario producer (item 29) cannot be built with the named files:**
   - the store is really `scenarios/adapters/yaml_user_scenario_store.py`;
   - the cold parser accepts only `COLD-LAB-001`, and the ruling does not say what to validate a test Site against;
   - the cold replay installs its setup only for `COLD-LAB-001` (`sites/cold_lab.py`);
   - the Lab lists only fixed scenario IDs (`simulator_lab_api.py:235`).

   Read those files and rule a buildable producer: the exact file list, the registration path, the Site validation rule, how the shifted setup reaches a test Site, the clocks, and the test. If a cleaner test-only producer (for example a direct SQL or fixture seed in the test DB) meets the STALE/PENDING/UNKNOWN proof needs, prefer it, and say what product code it avoids.

Append "W5-02a build rulings (K1c)" to `.agent/W5-02-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item, plus the file list.
