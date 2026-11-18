# Architect request: W5-01 C1 builder questions

You are the AssetOps Architect.

The C1 builder built and committed the Cooling read on `task/W5-01a-cold-selected-depth`. The per-unit review ACCEPTs it with Lows. The builder held the Health read. Read:
- `.agent/W5-01a-phase-handoff.md`, which has the Architect questions and six Cooling shape choices;
- `.agent/W5-01a-C1-review.md`;
- `.agent/W5-01-build-spec.md`, especially C1.

Rule with literal artifacts verified against merged code:
1. **Health read.** Name the exact read on the snapshot connection that gives the selected Foundation's asset IDs, and how the generator, compressor and probe assets are identified (asset type and role literals from merged code). Give the full Health payload key table, including `NOT_CONFIGURED`.
2. **Cooling choices.** The review says the spec decides #4 and #5; confirm #5 in one line and fix the wording for #6. Rule #1 (the payload key), #2 (the context row keys), #3 (several door pairs), and whether to add a public `cooling_response_on` method instead of calling the private W2 method.
3. **Review Lows.** Rule whether each is fixed in the C1 follow-up:
   - door_pairs with a zero-length CLOSE, where the code and docstring disagree;
   - a weak replay assertion;
   - the missing-ID case tested only in memory;
   - `links.health` pointing to a route that is not built yet.

Also check C2-C5 for the same class of gap: unnamed source reads, asset-role selection, payload keys, and guard or composition files. Amend them in place.

Update the C1 card and any other affected cards in place, add rows to the closure table, and append an amendment line to `D-2026-10-22-w5-01-w5-03-buildspec`. Write nothing else. Do not commit.
