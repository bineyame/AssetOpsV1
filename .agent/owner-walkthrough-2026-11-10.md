# Owner walkthrough feedback, 2026-11-10 (verbatim, in order)

## 1. Money in snapshots: decision on the Architect answer (architect-answer-money-snapshot-2026-11-10.md, D-MONEY.1-5)
"ok, i agree with the architect's recommendation, it should be addded to the backlog."

## 2. Evidence coverage, and the Portfolio screen layout
"My next point is about the evidence coverage aspect, i think it should be shared once somewhere in the screen since it applies for all instead of repeating it. ALso, i want the architect to consider a better screen organization for the rest of the content, perhaps a second menu with the cards being on the overview part and others("where management should act first","outcomes acorss the estates"...) in their own tabs (need to update the mockup, so i approve first).I still have more suggestions, so let the architect consider that as i continue my walkthough."

## 3. Wording of "checked"
"the user facing text for 'checked' should tell exactly what it means on the mock-up(perhaps use a better term to not imply the system failed to 'check' what is otherwise available). also '7 of 8 hours checked' doesn't make much sense."

## 4. Mockup layout: date selector and left menu
"also the date selection should be at the top of the screen and left side menu should be exactly as before in the new mock-up as well"

## 5. Owner answers to the proposal questions
"here is my response 1. tab set names are approved 2. yes 3. new term family accepted 4. this should be configurable per portfolio but is reasonable for now 5.yeah,let it is stay there for now, since the mapping is configurable(confirm) 6.I'm still doing my walkthrough and will say when i am done. SO, look out for more questions and comments"

What each answer refers to:
1. The tab set (Overview, Act first, Outcomes by site, Opportunity, What changed, Scope & coverage): approved.
2. Keep the top three "act first" items on the Overview: yes.
3. The new term family (complete readings / partial readings / too few readings / no readings received / still processing / not analysed yet): accepted.
4. The 80% "complete" threshold: reasonable for now, but it should be configurable per portfolio. At present it is a single global file, config/chain/coverage-policy-v1.json (bands complete 0.80, partial 0.25).
5. Unexplained fuel stays under Protect (MG-8) for now. The owner asked for confirmation that the mapping is configurable. The coordinator's answer: it is declarative and versioned (outcome-map/1), but it lives in code (backend/assetops_backend/outcomes/outcome_map.py ENTRIES). It is not a runtime config file, so changing it needs a reviewed code change.
6. The walkthrough is continuing.
