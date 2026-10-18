# Owner direction - mockup fidelity and Architect design ownership (2026-10-18)

Owner, verbatim: "as a side note: it is also exteremely important to 1- stay faithful to the mock-up in ui/ux and align technial desgin accordingly. there should not be drfit 2-the architect should not let important things be decided by the implementer by a vague guide"

Applied (binding for all waves):
1. The mockup drives the technical design, not the reverse: every Architect spec maps each mock panel/row/column/chip of every owned screen to its exact data source (read, field, gap). A panel the data cannot back keeps its mock slot with an honest gap; the design never trims, merges or redesigns a mock element to fit the backend.
2. Implementer-made decisions are defects, not deviations: any packet "choice/deviation/interpretation" that the spec did not fix must be ruled by the Architect before merge. Reviewers flag every unruled implementer decision as Medium (High if it changes what the user sees vs the mock). The coordinator batches them to the Architect in one call and the spec is amended, so the next slice never needs the same decision.
