# W5-02b K3a/K3b pre-flight questions (builder, 2026-10-23)

Branch `task/W5-02b-K3-cold-cases` from main `f164c49d`. I dry-read the K3a/K3b cards (`.agent/W5-02-build-spec.md:101-102`), the Site-screens ruling `### K3a and K3b: cases` (:315-321), Shared Site UI (:68-78), Measurement (:38), Producer (:80-84), Registry (:86-90), K2 rulings 1-24, the register (R65-R73, R88-R91) and the v69 `cold-work-incidents`/`cold-work-maintenance` source (`index.html:333-342`), checking each against the code on main. Most of K3 is decided. The points below are not, and each one would otherwise be a builder decision. Each has a proposed default. No code is written yet.

## Q1 (blocking K3a) The cold "banner" is review metadata in the mock, and there is no component for it

P-K3a-4-6 says to render `Cold-room operating capabilities and consequence vocabulary within the stable Site shell.` on all three cold Work screens and `cold-action`, "using the existing cold shell/banner component".

- In v69 that string is the `adapted` field of the screen metadata: `extra` in `index.html:684`, passed to `add(...,extra)` at :207. It is rendered only in the reviewer drawer `Canonical basis & review` (:1190) and the print-book caption (:1146). Cold screens have `book:false`. `screen-manifest.json:893,911` holds it as `"adapted"`. No cold screen body renders it.
- `src/` has no banner component and no use of the string (`grep "consequence vocabulary" frontend/src` returns 0 hits).

Rendering it would add a reviewer annotation to the product page that the mock's screen does not show (a D3 addition under mock fidelity). Please choose one:
- **(a)** Do not render it. The mock screen body has no banner, so the P-K3a-6 banner sentence is withdrawn. **Proposed.**
- **(b)** Render it. Name the component (`Notice` tone blue with `info` icon?), the slot (after the Work subtabs and before the Window control, or after the Window control and before the strip?), its register ID and D-code. Also state whether K3a may edit merged K2 `SiteWorkActions.tsx` or place it in `SiteAnalyticsFrames.tsx` (in the K3a list) for `cold-work` Actions. `SiteWorkActions.tsx` and `test/panelStructure.ts` are not in the K3a file list.

## Q2 (K3a) Disclosure summaries for R70, R71 and R89

The rulings fix where the disclosures go but not their summary text.
- R70: the Activity cell has a state chip, and a disclosure holds the stored `activity`. Summary text? **Proposed:** `Activity recorded`.
- R71: the Outcome cell has the `Unverified` badge, and a disclosure holds `outcome_note`. Summary text? **Proposed:** `Outcome note`. When `outcome_note` is null: no disclosure, or a disclosure that says `No outcome recorded`? **Proposed:** no disclosure.
- R89: the selected asset ID "in a disclosure". The Asset cell already has the W4 `UTC and IDs` disclosure (`siteWorkCases.tsx:367-403`). **Proposed:** add an `Asset ID` fact there, with no second disclosure in the cell.
- Incident Linked findings (ruling 4 with R65/R66): each `Finding {id8}` is plain text on cold, because the cold Finding frame ignores `revision_id` and the W4 `Link` is dropped on cold only. **Proposed:** each code gets its own `Finding version` disclosure with the full revision UUID, the same as K2 ruling 12. Confirm.

## Q3 (K3a) Activity chip when the request is not completed

"Keep the mock Maintenance Activity cell as a `Completed` chip only when the selected request is completed." For OPEN or IN_PROGRESS, should the cell show the real W4 state chip (`Open` amber, `In progress` blue, as W4 does now) or no chip? **Proposed:** the real state chip, so `Completed` appears only for COMPLETED.

## Q4 (K3a) W4 in-panel extras on cold that the mock panel does not have

The mock panel is the table only. On cold, which of these existing W4 elements stay?
- (i) `CoverageLine` (`siteWorkCases.tsx:637-648`): an in-panel ProductStatus driven by `coverage`. The ruling sources the cold notice from `status`, so the two could repeat the same idea. **Proposed:** remove it on cold only.
- (ii) the `What this list is based on` disclosure (`Basis`, :337-364). Its W4 fields are real on cold. **Proposed:** keep it.
- (iii) the `Showing a–b of N` pager and `Scroll the table for more columns →` hint. **Proposed:** keep both, the same as W4.

## Q5 (K3a) Currentness notice copy, tone and panel guard on the case tabs

**Proposed:** reuse `coldCurrentnessNotice(body.status, body.known_at)` and `coldCurrentnessTone` from `coldWorkPresentation.ts` unchanged, with `data-cold-work-currentness`, between the strip and the panel, and absent on CURRENT.
- This places the R91 notice on `cold-work-incidents` and `cold-work-maintenance`. Register row R91 names only `cold-work`. Should I extend R91's screens column, or does the Architect add a new row?
- K2 ruling 15 admitted the optional element in `test/panelStructure.ts` for `cold-work` only. That file is not in the K3a list. May K3a extend it to the two case screens?

## Q6 (K3a) Strip detail text

"`WORK_STRIP_DETAIL_DOMAIN` with the mounted global Incidents/Maintenance list descriptions." **Proposed:** the mock literal `Same records and states as the global Incidents list` / `... Maintenance list` (`index.html:341`), with the Manage link text `Manage in Incidents →` / `Manage in Maintenance →`, on COLDCHAIN only. MINIGRID keeps `These are work records at this site` and its arrowless link. Confirm that "mounted global list descriptions" means this mock sentence and not copy from the global pages.

## Q7 (K3b) Worst-case case rows do not exist in the producer

The caps call for "five case rows" (spec :38: other Work page <=1400/1800, panel <=440/650) and a worst-case capture. The producer's `worstcase` mode (`tools/w502_cold_work_walkthrough.py:249-261`) adds only five long Actions. It has one INC and one WR.
- (a) Payloads. **Proposed:** `worstcase` adds four more SERVICE-attested INCs and four more WRs, each with a record, through the same W4 service, for five of each. Titles, narratives, activity and outcome notes are 160 code points, with occurred times inside `[D+16h,D+17h)` after the fixture cases. INCs link the same two selected Findings, and WRs use `generator-1`. Manifest-expected counts are 5/5.
- (b) The K3b card does not list `w502_cold_work_walkthrough.py`. Is it in scope? The dispatch gives me the tool and the :604 attest fix, so I assume yes.
- (c) The long-text rule for cases: reuse K2's `isLongText` threshold and `Read full text` disclosure (preview replaced while open, ruling 20) on Case title, narrative, activity text and outcome note? Or keep W4's `.work-cases-clamp` with a `title` attribute only? **Proposed:** reuse the K2 rule on cold only.
- (d) Zero capture. **Proposed:** the positive DB with a valid seven-day window ending before `D`, which reads a COMPLETE zero and shows the mock empty copy. A non-complete zero is a component test only.

## Q8 (K3b) 403/503 captures for the W4 case reads

The K2 tool gate (ruling 3, option b, and ruling 6) wraps only the domain-work router. The case tabs read the W4 `GET /api/sites/{site}/work/{incidents|maintenance}` (`work_api.py:100-147`, development access in `main.py:559`). **Proposed:** extend the tool-local `serve_entry.py` to prepend `build_work_router(..., access=access, lists=build_work_index_service(work_url))` in the `forbidden` and `unavailable` processes. That gives the real W4 403 and the W4 `WORK_STORE_UNAVAILABLE` 503 with the Site read healthy, captured with the preserved W4 refusal titles (`No access`, `Work records unavailable`). This is capture scaffolding only, with no product change, and it falls under ruling 6's future item. Confirm.

## Not questions (decided; recorded so the reviewer can check)

- Mounted Manage hrefs, `site` props, `generator-1 · backup generator` parsed from the final exact `GENERATOR` token (an unknown suffix is shown verbatim), and `asset_label` with no new fields (P-K3a-1-3, R89).
- `siteWindowText` follows the M5 literal formatter with the month pinned to the `Jan`…`Dec` table, for COLDCHAIN only. MINIGRID keeps `eatWindowText`. The three zone and date-boundary tests.
- `[data-work-status]` is removed on cold only. W4 refusal titles are kept on the case tabs. INC stays plain (R73). WR links to the W6 C2 Overview with `known_at` (R68). Next evidence shows `next_evidence_copy` or `No next evidence recorded` (R72).
- K3b promotes three ledger rows plus the panel contracts by the literals at :88-90. `A-cold-work-projections` and `P-work-cases` stay open.
- The attest gap at `w502_cold_work_walkthrough.py:604` is fixed with `failures.append` before `continue`.
