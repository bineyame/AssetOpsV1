# Owner direction 2026-11-19 (verbatim): review gate before build; Architect spec and reviewer guide; reviewer clarifies before coding

Context: the pack recreation lanes (specs, workflow and plans, go-to-market, mock-up) were running. The coordinator had asked whether to allow a local browser install for the mock-up audit; the owner did not answer that question in this message.

> once everything is ready shre teh file paths for my review after which work would promptly begin. Make sure when work beging , the architect specifies clearly to the implementer as well are reviwer guide and the reviwer asks and clarifies questions with the architect before coding begingsg to avoid mid-implementation back and forth. the execution should be efficent and we should make progress while keeping quality. We'll do another round of strategy conversation on test data and database build, to work efficently by using large data algorithms and stae of the art methods

## Owner addition: one combined handshake round, with the implementer's pre-flight

The owner asked:

> what if the implementer has questions?

The coordinator answered that two existing rules cover it: the builder's pre-flight (RULES §4) and "an implementer choice the spec did not fix is a spec defect" (RULES §7). The coordinator then proposed a refinement:
- The reviewer's questions and the implementer's pre-flight run together, as one handshake round.
- The Architect answers everything once, in the spec.
- Mid-build questions stop only the affected part; the Architect rules in `rulings.md`, and the reviewer guide is updated if the done criteria change.
- Keep a count of mid-build questions per unit, to improve the spec template.

The owner answered:

> yes, run it that way and add it to the rule
