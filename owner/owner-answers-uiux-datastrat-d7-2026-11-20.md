# Owner: answers to U7–U10, the data and build strategy's 8 questions, and D7 (2026-11-20)

Asked from the coordinator's list of open questions with context and defaults (U7–U10 from `Docs/design-system/uiux-guide.md`; questions 1–8 from §10 of `Docs/engineering/data-and-build-strategy.md` on `task/data-build-strategy`; D7 from `decisions-register.md` §5 in the frozen pack).

The owner replied, verbatim:

> u9- adopt, u10-yes, u8- keep the 6 groups u7- yes . Data and buils strategy: 1.default is OK 2.yes,if synthetic has an advantage, that defaults with possibilty to switch. 3.default is fine, a combination could also be considrerd for its merit if either or is not the only option but speed matters now 4.yes 5.yes 6. yes for now 7.once a day and on demand for now 8.default is fine. Design pack : D7- yes, default

Reading against the defaults (coordinator's note, for traceability):
- U9 adopted (load July–September history); U10 adopted (East Africa as the demo operators' starting pack, Neutral the product default); U8 keep the six rail groups; U7 adopted (RULES §6 cites the UI/UX guide).
- Q1, Q4, Q5, Q6, Q8: default. Q6 "for now".
- Q2: default (synthetic) with the possibility to switch, conditional on synthetic having an advantage.
- Q3: default (plain Postgres); a combination may be considered on merit, but speed matters now.
- Q7: **differs from the default** ("at once on a trigger"): recalculation runs once a day and on demand, for now.
- D7: default (vNEXT governs the Layer 4 screen slices once the pack is approved; until then a screen slice may build but does not merge without the owner's walkthrough).
