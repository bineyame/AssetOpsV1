# S4-01 registry closeout review

Reviewer: fresh Claude reviewer (did not author the closeout). Target: branch closeout/S4-01-registry, commit e2c190c. Not fixed, merged or committed.

Verdict: ACCEPT. Findings: 0 block, 1 carry (informational).

## Verified
- Diff is 2 files: the registry JSON (3 lines) and the closeout notes. Only finding:1#a, finding:2#a, finding:4#a changed: state open->delivered, added delivered_by ["I-S4-01"], evidence (task, packet, owner acceptance; all three files exist), anchors, panel_status gap->partial. Claim, boundary, mapping_target, requires, mapping_review and line formatting preserved.
- Anchors resolve: SiteFinding.tsx:286 WhatHappened, :397 WhatLimits, :468 WhereToLook, :619 RecordsSummary; finding_api.py:95 finding-windows route, :104 findings route; finding_read.py and migrations/versions/0009_finding_store.py exist.
- Claims match the packet acceptance table: detail at canonical route with reload, limitations and joined gaps, accepted-record and Dispatch-day drill-downs (day plus interval revision). finding:4 stays bounded to "exact Finding, assessment and accepted-source drill-downs"; history, money and actions remain "Not yet available" in the packet.
- Untouched: finding:3 (unmapped/gap), finding-evidence:1/2, financials, money, History/Evidence tabs, Site list, finding-history, sitefindings. No panel Real; V-01 not edited.
- tools/check-all.ps1: all 6 guards PASS (architecture, navigation, agent workflow, dependency registry, delivery fixtures, screen ledger).
- Live --next-work: ranked. V-01a 2.655 (eligible) vs V-01b 2.47 (eligible); gap (2.655-2.47)/2.655 = 6.97%, in the 5-10% band, so select V-01a with owner notice (user_review_required true). Third is D-financial-basis 2.415, technically blocked (A-S4-financial, I-financial-store). Ranking facts are consistent with the notes.

## Carry
- C1 (carry, non-blocking): the decision is a tie-break within 5-10%, so owner notice is required before V-01a starts; the next-work report is non-authoritative until mapped paths and scoring are independently reviewed.

## Not verified
Frontend test/build and live app behaviour not rerun; the portions rest on the merged S4-01 owner acceptance and packet evidence.
