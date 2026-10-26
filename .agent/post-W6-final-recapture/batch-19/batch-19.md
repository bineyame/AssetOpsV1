# Final recapture batch 19: W6 work request

Main SHA 89a11477. Pairs 194 (frozen 194). Counts: FIXED 156, PASS 32, REGRESSION-OPEN 6

Method: original capture tool and producers (unmodified), same ports, fresh DBs; each pair compared with the frozen evidence (panel titles, heights, rows, columns, links, chips, typography, overflow, header band, tab-row scroll, caps) and the frozen mock (unchanged). Classification derived from measured deltas plus register/rulings; standing D1/D2/D4 rows and ruled caps count as PASS. FIXED = a measured signal that a frozen D3 difference is gone.

## REGRESSION-OPEN (6)
- wr-record / cold-worstcase-wr-000004 / 1440: B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size as the frozen capture (unrecorded there); contradicts caps ruling 4/5 'never truncate a value without its full disclosure'. Cause: frontend/src/work/WorkRequestRecord.tsx:122 wraps the outcome in <Clamp> (globalWork.css:80 3-line clamp) without the LongText 'Full ... text' disclosure the activity gets (WorkRequestRecord.tsx:95-97) (evidence cold-worstcase/wr-record-cold-worstcase-wr-000004-1440-app.png)
- wr-record / cold-worstcase-wr-000004 / 390: B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size as the frozen capture (unrecorded there); contradicts caps ruling 4/5 'never truncate a value without its full disclosure'. Cause: frontend/src/work/WorkRequestRecord.tsx:122 wraps the outcome in <Clamp> (globalWork.css:80 3-line clamp) without the LongText 'Full ... text' disclosure the activity gets (WorkRequestRecord.tsx:95-97) (evidence cold-worstcase/wr-record-cold-worstcase-wr-000004-390-app.png)
- wr-record / cold-worstcase-all-open-wr-000004 / 1440: B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size as the frozen capture (unrecorded there); contradicts caps ruling 4/5 'never truncate a value without its full disclosure'. Cause: frontend/src/work/WorkRequestRecord.tsx:122 wraps the outcome in <Clamp> (globalWork.css:80 3-line clamp) without the LongText 'Full ... text' disclosure the activity gets (WorkRequestRecord.tsx:95-97) (evidence cold-worstcase/wr-record-cold-worstcase-all-open-wr-000004-1440-app.png)
- wr-record / cold-worstcase-all-open-wr-000004 / 390: B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size as the frozen capture (unrecorded there); contradicts caps ruling 4/5 'never truncate a value without its full disclosure'. Cause: frontend/src/work/WorkRequestRecord.tsx:122 wraps the outcome in <Clamp> (globalWork.css:80 3-line clamp) without the LongText 'Full ... text' disclosure the activity gets (WorkRequestRecord.tsx:95-97) (evidence cold-worstcase/wr-record-cold-worstcase-all-open-wr-000004-390-app.png)
- wr-record / ev-worstcase-160-wr-000004 / 390: B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size as the frozen capture (unrecorded there); contradicts caps ruling 4/5 'never truncate a value without its full disclosure'. Cause: frontend/src/work/WorkRequestRecord.tsx:122 wraps the outcome in <Clamp> (globalWork.css:80 3-line clamp) without the LongText 'Full ... text' disclosure the activity gets (WorkRequestRecord.tsx:95-97) (evidence ev-worstcase/wr-record-ev-worstcase-160-wr-000004-390-app.png)
- wr-record / ev-worstcase-160-all-open-wr-000004 / 390: B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size as the frozen capture (unrecorded there); contradicts caps ruling 4/5 'never truncate a value without its full disclosure'. Cause: frontend/src/work/WorkRequestRecord.tsx:122 wraps the outcome in <Clamp> (globalWork.css:80 3-line clamp) without the LongText 'Full ... text' disclosure the activity gets (WorkRequestRecord.tsx:95-97) (evidence ev-worstcase/wr-record-ev-worstcase-160-all-open-wr-000004-390-app.png)

## GAP (0)
- none

## Run notes
- Main HEAD 63f9f8e5, app code SHA 89a11477 (`git diff --stat 89a11477 HEAD -- frontend backend tools host simulator contracts` empty). Vite on localhost:5189 started plainly (`npm.cmd run dev -- --port 5189 --strictPort`, ASSETOPS_API_PORT per phase, no policy override), restarted per W5 phase, stopped by PID. CDP 9529 (capture), 9539 (scroller probe). Vite did not die mid-run.
- Producers unmodified: tools/w601_seed.py x5 (assetops_w601_b19f{detail,hist,linked,stress,maint}_test, fixtures detail/detail-history/detail-linked/stress/maintenance, frozen clock 2026-10-20T12:00:00Z) served by plain uvicorn assetops_backend.main:app on 18901; 403 and 503 from the reviewed TEST-ONLY .agent/W6-01-evidence/C2/api_403 and C4/api_503 over the detail DB. tools/w502_cold_work_walkthrough.py --work var/w502b_b19 --tag b19 prepare/serve/attest (ATTEST OK)/drop (hard-coded 8971-8977, checked free). W504_API_PORT_BASE=18900 tools/w504_ev_work_walkthrough.py --work var/w504a_b19 --tag b19 prepare/serve/attest/drop; attest ran BEFORE the EV capture (creates the EV WRs and stops the unavailable API on 18907). WR case IDs read with a read-only SELECT public_code,id FROM work_case WHERE kind='MAINTENANCE_REQUEST' (seed/cold-*.txt, seed/ev-*.txt). All b19 DBs dropped, var/w502b_b19 and var/w504a_b19 removed by the producers' own drop, no listeners left.
- Claims: detail 276/300, maint 154/156, forbidden 30/36, unavailable 30/36, cold-forbidden 30/36, ev-forbidden 30/36, ev-unavailable 30/36: every failed claim is 'same panel count' on a refusal page, which now renders no panels by ruling (W6 Q11, R367). hist 72/72, linked 36/36, stress 72/72, cold-positive 72/72, cold-worstcase 108/108, ev-positive 72/72, ev-worstcase 96/96.
- Fixed vs frozen (measured): B19-03 390 tab row wraps, no site-tabs__list scroller (R364); B19-07 refusals show header + one refusal with no Work done/Lifecycle/record/History shells, Reload only on 503 (R367), copy 'No access to this Site's work.' / 'Work records could not be read.' / 'Choose a request at a site.'; B19-08 validateDOMNesting console warning gone (R368); B19-05 History record UUID now 'maintenance record 1 · ...' with a Stored record ID disclosure, cold Linked action 'ACT-000001' (R366); B19-06 'c1 · EV_CONNECTOR' and 'generator-1 · GENERATOR' gone ('Backup generator · generator-1', Q18); B19-13 historical date bar with seconds ('11:59:04 UTC', '12:00:01 UTC', R372); B19-15 W5 forbidden principals (cold :8976, EV :18906) now refused 403 instead of reading the request (R373).
- Standing (not counted): MOCK DEVIATION D1 (R396), D2 (R363), D1 (R365), D2 (R369) labels visible (+12 px prose line, about +20 px panel height); date bar row R363; honest gaps R365; Finding id8 labels R65/R74; UTC on EAT Sites B2-21; shell B1-01/B1-04; breadcrumb still blue '/' links (B19-17, no register row; identical to batch 18 crumb).
- Caps: every closed panel against the ruled absolute caps (post-W6-W6-caps-rulings.md rulings 1-2: Work done 600/800, Lifecycle 500/250, History 650/690, Maintenance record · activity 700/900): no violation. Peaks (closed): Work done 442/442, Lifecycle 442/167, Maintenance record · activity 596/636, History 487/510 (stress WR-000007).
- Clipped cells: every clamp except the Outcome note carries its visible 'Full owner/narrative/activity/event/source text' disclosure; stress/worstcase 'clipped text changed' deltas are pixel-only (sh 73->70). The Outcome note clamp has no disclosure (B19F-01 below).
- Scroller probe (tools/probe-scrollers.mjs, port 9539, 8 s warm-up, 6 s settle) on all 194 pairs: every horizontal scroller is the labelled focusable data-table scroller; zero unfocusable scrollers, so no new keyboard-unreachable scroller.
- 390 screenshots opened by me: overview positive and worstcase-200char (stress), record cold worstcase all-open, history positive, record EV forbidden-403. No cut text except table-scroller edges (labelled 'Scroll table horizontally') and the Outcome note clamp (B19F-01).
- Cited, not recounted: EV Finding ev-id scroller (batch 08), cold depth refused-reversed raw-code card (B14-01), EV Work 'UTC and IDs' scrollers (B13-18 flag); none is on these WR pages.
- Not rerun (uncounted in the frozen index): link-check captures (unknown sub-tab addresses B19-12/R371, global Maintenance row link). VERIFICATION_WINDOW is still not producible (B19-10 capture gap, as W6 Q12/Q20 declared); unknown-event fall-through not reachable by the producers.


## All pairs
| Screen | Case | Width | Class | Why |
|---|---|---|---|---|
| wr-overview | cold-forbidden-principal | 1440 | FIXED | h1 text changed; W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373); refusal: header + one refusal, no empty shell panels (B19-0 |
| wr-overview | cold-forbidden-principal | 390 | FIXED | h1 text changed; 390 tab row wraps; History tab no longer cut (B19-03, R364); W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373) |
| wr-record | cold-forbidden-principal | 1440 | FIXED | h1 text changed; W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373); refusal: header + one refusal, no empty shell panels (B19-0 |
| wr-record | cold-forbidden-principal | 390 | FIXED | h1 text changed; 390 tab row wraps; History tab no longer cut (B19-03, R364); W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373) |
| wr-history | cold-forbidden-principal | 1440 | FIXED | h1 text changed; W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373); refusal: header + one refusal, no empty shell panels (B19-0 |
| wr-history | cold-forbidden-principal | 390 | FIXED | h1 text changed; 390 tab row wraps; History tab no longer cut (B19-03, R364); W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373) |
| wr-overview | cold-wr-000002 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-overview | cold-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-record | cold-wr-000002 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | cold-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | cold-wr-000002 | 1440 | FIXED | record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-history | cold-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-overview | cold-all-open-wr-000002 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-overview | cold-all-open-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-record | cold-all-open-wr-000002 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | cold-all-open-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | cold-all-open-wr-000002 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | cold-all-open-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | cold-worstcase-wr-000002 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-overview | cold-worstcase-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-record | cold-worstcase-wr-000002 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | cold-worstcase-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | cold-worstcase-wr-000002 | 1440 | FIXED | record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-history | cold-worstcase-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-overview | cold-worstcase-wr-000004 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | cold-worstcase-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18) |
| wr-record | cold-worstcase-wr-000004 | 1440 | REGRESSION-OPEN | B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size |
| wr-record | cold-worstcase-wr-000004 | 390 | REGRESSION-OPEN | B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size |
| wr-history | cold-worstcase-wr-000004 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | cold-worstcase-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | cold-worstcase-all-open-wr-000004 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | cold-worstcase-all-open-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18) |
| wr-record | cold-worstcase-all-open-wr-000004 | 1440 | REGRESSION-OPEN | B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size |
| wr-record | cold-worstcase-all-open-wr-000004 | 390 | REGRESSION-OPEN | B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size |
| wr-history | cold-worstcase-all-open-wr-000004 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | cold-worstcase-all-open-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | positive-wr1-in-progress | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | positive-wr1-in-progress | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | all-open-wr1 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | all-open-wr1 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | cancelled-wr2 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | cancelled-wr2 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | not-found-404 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-overview | not-found-404 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-overview | no-site-id | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | no-site-id | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | bad-known-at | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | bad-known-at | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | positive-wr1-in-progress | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | positive-wr1-in-progress | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | all-open-wr1 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | all-open-wr1 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | cancelled-wr2 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-record | cancelled-wr2 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-record | not-found-404 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-record | not-found-404 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-record | no-site-id | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | no-site-id | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | bad-known-at | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | bad-known-at | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | positive-wr1-in-progress | 1440 | FIXED | record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-history | positive-wr1-in-progress | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-history | all-open-wr1 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | all-open-wr1 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | cancelled-wr2 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | cancelled-wr2 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | not-found-404 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-history | not-found-404 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-history | no-site-id | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | no-site-id | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | bad-known-at | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | bad-known-at | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | page2-wr1 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | page2-wr1 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | page2-all-open-wr1 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | page2-all-open-wr1 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | historical-1159-04-wr1 | 1440 | FIXED | record UUID out of History text, Stored record ID disclosure (B19-05, R366); historical date bar shows seconds (B19-13, R372) |
| wr-history | historical-1159-04-wr1 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); record UUID out of History text, Stored record ID disclosure (B19-05, R366); historical date bar sh |
| wr-overview | historical-1159-04-wr1-completed | 1440 | FIXED | historical date bar shows seconds (B19-13, R372) |
| wr-overview | historical-1159-04-wr1-completed | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); historical date bar shows seconds (B19-13, R372) |
| wr-overview | wrong-site-kobo002 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-overview | wrong-site-kobo002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-overview | malformed-case-id | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | malformed-case-id | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | before-created-known-at | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-overview | before-created-known-at | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-overview | ev-forbidden-403 | 1440 | FIXED | h1 text changed; W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373); refusal: header + one refusal, no empty shell panels (B19-0 |
| wr-overview | ev-forbidden-403 | 390 | FIXED | h1 text changed; 390 tab row wraps; History tab no longer cut (B19-03, R364); W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373) |
| wr-record | ev-forbidden-403 | 1440 | FIXED | h1 text changed; W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373); refusal: header + one refusal, no empty shell panels (B19-0 |
| wr-record | ev-forbidden-403 | 390 | FIXED | h1 text changed; 390 tab row wraps; History tab no longer cut (B19-03, R364); W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373) |
| wr-history | ev-forbidden-403 | 1440 | FIXED | h1 text changed; W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373); refusal: header + one refusal, no empty shell panels (B19-0 |
| wr-history | ev-forbidden-403 | 390 | FIXED | h1 text changed; 390 tab row wraps; History tab no longer cut (B19-03, R364); W5 forbidden principal now refused 'No access to this Site's work.' (B19-15, R373) |
| wr-overview | ev-wr-000002 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-overview | ev-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-record | ev-wr-000002 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | ev-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | ev-wr-000002 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | ev-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | ev-all-open-wr-000002 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-overview | ev-all-open-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18); Action label uses ACT- code (B19-05, R366) |
| wr-record | ev-all-open-wr-000002 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | ev-all-open-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | ev-all-open-wr-000002 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | ev-all-open-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | ev-api-stopped-503 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | ev-api-stopped-503 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | ev-api-stopped-503 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | ev-api-stopped-503 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | ev-api-stopped-503 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | ev-api-stopped-503 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | ev-worstcase-160-wr-000004 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | ev-worstcase-160-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18) |
| wr-record | ev-worstcase-160-wr-000004 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | ev-worstcase-160-wr-000004 | 390 | REGRESSION-OPEN | B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size |
| wr-history | ev-worstcase-160-wr-000004 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | ev-worstcase-160-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | ev-worstcase-160-all-open-wr-000004 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | ev-worstcase-160-all-open-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18) |
| wr-record | ev-worstcase-160-all-open-wr-000004 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | ev-worstcase-160-all-open-wr-000004 | 390 | REGRESSION-OPEN | B19F-01: Outcome note cut at 3 lines with no full-text disclosure, even with all disclosures open (clipped global-work-clamp sh 70 > ch 53). Same clamp and size |
| wr-history | ev-worstcase-160-all-open-wr-000004 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | ev-worstcase-160-all-open-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | ev-worstcase-wr-000002 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | ev-worstcase-wr-000002 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | ev-worstcase-wr-000006 | 1440 | FIXED | raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | ev-worstcase-wr-000006 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); raw asset label code · TYPE gone (B19-06, Q18) |
| wr-overview | forbidden-403 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-overview | forbidden-403 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-record | forbidden-403 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-record | forbidden-403 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-history | forbidden-403 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-history | forbidden-403 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-overview | historical-120001-rev2 | 1440 | FIXED | historical date bar shows seconds (B19-13, R372) |
| wr-overview | historical-120001-rev2 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); historical date bar shows seconds (B19-13, R372) |
| wr-overview | historical-current-rev3 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | historical-current-rev3 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-record | historical-120001-rev2 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368); historical date bar shows seconds (B19-13, R372) |
| wr-record | historical-120001-rev2 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368); historical date bar shows seconds (B19-13,  |
| wr-record | historical-current-rev3 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | historical-current-rev3 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | historical-120001-rev2 | 1440 | FIXED | record UUID out of History text, Stored record ID disclosure (B19-05, R366); historical date bar shows seconds (B19-13, R372) |
| wr-history | historical-120001-rev2 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); record UUID out of History text, Stored record ID disclosure (B19-05, R366); historical date bar sh |
| wr-history | historical-current-rev3 | 1440 | FIXED | record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-history | historical-current-rev3 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-overview | linked-source-wr5 | 1440 | FIXED | Action label uses ACT- code (B19-05, R366) |
| wr-overview | linked-source-wr5 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); Action label uses ACT- code (B19-05, R366) |
| wr-record | linked-source-wr5 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-record | linked-source-wr5 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | linked-source-wr5 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | linked-source-wr5 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | open-wr-000001 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | open-wr-000001 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-record | open-wr-000001 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-record | open-wr-000001 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | open-wr-000001 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | open-wr-000001 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | cancelled-from-open-wr-000004 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | cancelled-from-open-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-record | cancelled-from-open-wr-000004 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-record | cancelled-from-open-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | cancelled-from-open-wr-000004 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | cancelled-from-open-wr-000004 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | in-progress-assigned-wr-000005 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | in-progress-assigned-wr-000005 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-record | in-progress-assigned-wr-000005 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-record | in-progress-assigned-wr-000005 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | in-progress-assigned-wr-000005 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | in-progress-assigned-wr-000005 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | completed-wr-000006 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | completed-wr-000006 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-record | completed-wr-000006 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | completed-wr-000006 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | completed-wr-000006 | 1440 | FIXED | record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-history | completed-wr-000006 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); record UUID out of History text, Stored record ID disclosure (B19-05, R366) |
| wr-overview | other-tenant-wr8-404 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 refusal (B19-07) |
| wr-overview | other-tenant-wr8-404 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367); false Reload gone on non-503 r |
| wr-overview | worstcase-200char-wr7 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | worstcase-200char-wr7 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | worstcase-all-open-wr7 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-overview | worstcase-all-open-wr7 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-record | worstcase-200char-wr7 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | worstcase-200char-wr7 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | worstcase-all-open-wr7 | 1440 | FIXED | validateDOMNesting console warning gone (B19-08, R368) |
| wr-record | worstcase-all-open-wr7 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); validateDOMNesting console warning gone (B19-08, R368) |
| wr-history | worstcase-200char-wr7 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | worstcase-200char-wr7 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-history | worstcase-all-open-wr7 | 1440 | PASS | no measured difference from the frozen capture beyond standing/ruled rows |
| wr-history | worstcase-all-open-wr7 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364) |
| wr-overview | store-unavailable-503 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-overview | store-unavailable-503 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | store-unavailable-503 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-record | store-unavailable-503 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | store-unavailable-503 | 1440 | FIXED | refusal: header + one refusal, no empty shell panels (B19-07, R367) |
| wr-history | store-unavailable-503 | 390 | FIXED | 390 tab row wraps; History tab no longer cut (B19-03, R364); refusal: header + one refusal, no empty shell panels (B19-07, R367) |
