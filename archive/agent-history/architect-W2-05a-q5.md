# Architect request - W2-05a commit-4 questions (2026-10-18). Owner: mockup leads UI/UX and the technical design aligns to it; no drift; implementer decides nothing. Brief rulings; edit `.agent/W2-05a-build-spec.md` in place; amend `D-2026-10-18-w2-05-buildspec`. No code.

From the commit-4 implementer (branch task/W2-05a-ev-foundation; screens ev-foundation, ev-readiness, ev-sld; captures `.agent/W2-05a-evidence` on that branch):
1. W1 vocabulary forbids `mapping`, `scenario`, `load`, but the spec binds mock label "Session identity mapping", gap copy "No scenario tariff in use" and part name "load manager". Implementer added exact-phrase W1 exceptions in `productVocabulary.json` (guard change). Rule: keep mock wording with the exact exceptions, or give plain wording.
2. `ev-sld`: implementer drew the declared AC feed as the bus; grid supply, load manager and breakers as dashed "Not declared" slots; the import meter in the charger feeder's kWh slot, because the configured topology is feed -> meter -> charger, while the v69 mock draws the meter upstream of the bus. The mock leads: rule the exact drawing (and whether the Foundation topology/fixture must change to match the mock instead).
3. Readiness messages with no mock row (meter, session-event, Site import gaps) shown as extra rows under the four mock rows (cold precedent). Confirm or specify.
4. The mock Action link in panel 4 row 2 shown as "Investigation action · Not available yet" (no Action exists). Confirm label.
Also note: ev-sld "What each part does" table is 1.51x the mock (5 rows incl. per-connector roles vs mock 4) - rule whether that is acceptable or how to compact it to the mock.
Print a 4-line summary.
