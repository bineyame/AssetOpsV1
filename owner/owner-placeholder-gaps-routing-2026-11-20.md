# Owner: route the placeholder-audit gaps (2026-11-20)

The owner asked:

> Regarding the mockup, are the content palceholders done in a manner that  the backend design is aligned to make them available ?

An independent read-only audit (coordinator's scratchpad `placeholder-audit.md`) grouped about 60 "not available yet" sites into 22 classes: 10 aligned, 7 partial, 1 not designed, 4 intentional. Main gaps:
1. Nothing carries "the record that would fill it" (release test "Unknown is not zero", delivery-plan.md:159): no field on `factor_value` or the snapshot node; the mock-up's missing-records table is typed by hand. Fix: a `missing` field fed by each leaf's source, plus a check that every empty state names its source and slice.
2. Trend slots can't fill in the wired shape (no designed emitter of the history, no month-series read contract, October not in the series, Site tiles wired to never fill). Routed to the DS1 Architect.
3. Recalculate now has no after-state (no Thika invoice amount anywhere; wall-clock time). Routed to the DS1 Architect.
4. Some placeholders already have data (Embakasi deliverable energy, Kasarani October; earlier boards on Kobo billing/target, Thika cooling energy, Ruiru roster). Fix: one mock-up pass reading the data, plus a check failing any empty state whose value exists.
5. Mini-grid usable capacity is named as the value chain's first stage but no node, evaluator value or slice delivers it; the mock-up blames a missing export, contradicting the integration design. Fix: add to scope or declare deferred and correct the copy.
Smaller: "compatibility per batch (assumed zero now)" treats unknown as zero (Rule 3); "not available yet" used where "nothing yet" / "not chosen yet" is meant; an earlier EV board asks for records ruled out for a captive fleet.

Proposed routing: gaps 2 and 3 already with the DS1 Architect; gaps 1 and 5 and the unknown-as-zero case to the design Architect (contract field, scope ruling, new check); gap 4, the wording fixes and the Site-tile wiring to the UI Architect after the Decision page.

The owner replied, verbatim:

> yes, send them as proposed
