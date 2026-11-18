# W6-01 closure check 2 (OI-1 to OI-10)

Fresh reviewer, `AssetOpsV1-plan2` at af242a82, read-only. Spec: `.agent/W6-01-build-spec.md`. No tests run; literals spot-checked against merged code.

## Verdict: NOT READY (1 small open item, NEW; OI-1 to OI-10 all closed)

## Closure of OI-1..OI-10
- OI-1 closed: section 1 gives incident/maintenance sort `(root occurred_at|created_at desc, site_code_key, site_id, case_id)` and the full cursor tuple; consistent with `work/site_index.py:199-210` (time desc, id asc via stable sort).
- OI-2 closed in substance: A2 and B2 give strip text, both `WORK_CONTEXT_NOTICE` literals, `siteWorkCases.tsx`, `siteWorkCases.test.tsx` (pins at :175,:211,:388,:452 exist) and `missing-claim-scan.mjs` (exemptions at :70-82 exist) in their lists. But see OI-11.
- OI-3 closed: nested `work_detail` keeps six digits (matches `work/model.py:192`), outer `selected.known_at` whole seconds, `history.*_at` six digits; the literal example is consistent.
- OI-4 closed: Preventive card is plain text `Preventive plans open in a later unit.`; B2 adds exactly one `UnavailableTab` multiset entry; B3 removes it. No hit for the phrase in `tools/checks` or `frontend/src`.
- OI-5 closed: header block 380/860 and `mheader` 150/400 hold against measure-2 (block 363/844, mheader 137/394). Measure-2 still prints the old 250/390 as the spec's cap, which is its historical comparison, not a contradiction.
- OI-6 closed: occurrence offsets (-2d3h, -2d2h, -2d1h, -2d; correction -1d from `--clock`), page query contract, explicit capture window. All sit inside the 10-15 to 10-22 window.
- OI-7 closed: empty-scope precedence, provenance selected IDs (`[head_id]`, evidence `[]`), cursor-key README (A1 lists `backend/README-db.md`; estate key doc is at :40-44) and key tests.
- OI-8 closed: new detail route stated (merged is `work_api.py:174`), 401 text per route (`work_api.py:74` "Sign in to read work.").
- OI-9 closed: section 4 names capture dirs, packets per unit, and the conditional owner merge under the Architect recommendation.
- OI-10 closed: chip row 40/80; new elements 180/300, status line 70/130, first capture measures.

## Open items
- OI-11 (NEW, small, A2/B2): the replacement strip `linked Manage in Incidents` / `Manage in Maintenance` has no literal href. `siteWorkCases.tsx:259-260` renders a plain span; no helper exists for the global page URL. Say what the link targets, e.g. `/incidents` and `/maintenance` with the Site window `from`, `to`, `known_at` carried over, and which helper builds it. Related wording: A2 says "update ... the strip exemption" but the `WORK_MANAGE_UNAVAILABLE_STATUS` constant and exemption are shared with the maintenance strip, so A2 must keep them until B2 removes them. Say so.
- Minor (not blocking): the section 1 example `occurred_at` values for request, plan and operational rows (09:10, 09:20, 09:30) differ from the section 4 offsets (10:00, 11:00, 12:00). The examples are marked illustrative, but a builder pinning fixtures to them would mismatch.
