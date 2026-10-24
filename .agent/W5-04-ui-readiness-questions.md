# W5-04 UI readiness check: open points (V2a-V5)

Read-only check, 2026-10-24. Worktree `AssetOpsV1-review3`, branch `task/W5-04b-ev-work-ui`, at main `d9dfab85` (K4a/K4b/K5 merged).

The V1 backend was read with `git show` from `task/W5-04a-ev-work-backend` (head `1429a547`, unmerged).

Inputs:
- the task and build spec;
- pre-flight rulings 1-46 and readiness rulings 1-31;
- K4 rulings 1-22 and the W5-02 K2/K3 rulings;
- mock measurements, the register and the K4 evidence README;
- the ledger, panel contracts and registry;
- v69 `SITE_WORK.ev`/`WORK_COLS`/`WORK_EMPTY`/`siteWorkScreen` (index.html:337-343) and `ev-action` (:710-713).

No code was run and no product file was changed. Only new or still-open points are listed. Each point recommends option (a) unless it says otherwise.

## A. Gate and backend as built

1. **V1b is neither complete nor merged, and its producer cannot make fixtures yet.**
   - The questions file on the backend branch lists Q6-Q12 as "recorded, not decided".
   - `tools/w504_ev_work_cases.py:209-217` (`replay_shifted`) always raises `ProducerBlocked`. That blocks on Q8 (`POSITIVE_SCENARIO = "ev-fault"` at :47 has no fault-ended session) and Q9 (`scenarios/ev_parsing.py:179-189` pins `EV-LAB-001` and the 08:00-09:00 window).
   - As a result `prepare` exits 3, and `serve`/`attest` refuse at walkthrough :340 and :370.
   - The pending, stale and unknown modes are hard-coded `unavailable` (:212-215).
   - V2b, V3b and V4b consume this manifest. V2a, V3a and V4a parse a wire that has not been reviewed.
   - Options:
     - (a) V2a may start on pure component fixtures shaped from the as-built V1 wire once rulings 32+ confirm that wire is unchanged. V2b waits until `prepare` returns `positive` and `mock-zero` ready, and pending/stale/unknown either run or carry an explicit pure-vector limitation (build spec "EV producer").
     - (b) Hold every UI unit until W5-04a V1b is reviewed and merged.
   - Ruling 1 ("never implement against a provisional UI") does not address a provisional backend, so this needs an explicit word.

2. **EV detail read states that ruling 16 does not cover.**
   - Backend `work/domain_action_index.py:303-305` returns **409** `DOMAIN_INTENT_BASIS_CHANGED` / `The selected EV work basis changed; reload the Action.` on a *read* when the intent recheck fails. Ruling 16 lists only loading, 404 and 403/422/503.
   - On main, `domainActionClient.ts:396` maps only `WORK_BASIS_CHANGED` to its own state. Any other 409 falls into the generic refusal.
   - Backend Q7 as built: an EV detail with no intent returns 200 with `status` `UNKNOWN`. The missing-intent capture would therefore show the currentness notice above `No verification criteria have been declared for this Action.`
   - Options:
     - (a) Render the 409 in the same untitled state panel: `EV work unavailable`, the server message, and `Retry` (the retry re-reads). Extend R110 and the V4a/V4b state list (`403/409/422/503`). Accept the UNKNOWN notice on missing intent, as cold does.
     - (b) Give 409 its own copy or a reload control.
     - (c) Have the backend pin a no-intent read at the Action's `recorded_at` (Q7 alternative), removing the UNKNOWN notice.

## B. Contradictions with merged K4

3. **The status strip and state panel are not in `DomainActionVerification.tsx`.**
   - Ruling 15 places the EV status (`{owner ?? 'Not assigned'} · {full display_name}`, no Finding version disclosure) in a generalised `DomainActionVerification.tsx`.
   - On main, that file holds only the criteria and Related panels. Its props are `{detail, siteCode, knownAt}` (:70-80) with hard-coded `COLD_*` constants (:17-34) and no `action.domain` read.
   - The header, subtitle, badge, status line (the `shortName(...) · links.finding.label` concatenation), Finding version disclosure, currentness notice, untitled state panel and closing notice all live in `ColdDomainActionShell`, `shell/SiteAnalyticsFrames.tsx:1370-1494`. Their literals are in `sites/coldWorkPresentation.ts:24-42`.
   - Options:
     - (a) V4a generalises `ColdDomainActionShell` into a domain shell that takes an explicit presentation object, and generalises `DomainActionVerification` with an explicit panel-presentation input. Cold literals stay in `coldWorkPresentation.ts` and EV literals go in `evWorkPresentation.ts`. Add both presentation files to V4a's list (`evWorkPresentation.ts` is created by V2a). Cold must be byte-identical.
     - (b) Add a separate `EvDomainActionShell` beside the cold one. This duplicates code but leaves K4 untouched.

4. **Ruling 16's test file is the wrong one.** `sites/__tests__/siteAction.test.tsx` covers the W1 battery `SiteAction.tsx`, which has no domain path. K4's untitled-panel tests (`COLD_ACTION_LOADING`, `COLD_WORK_UNAVAILABLE`) are in `domainActionVerification.test.tsx`, `operatorRouteFrames.test.tsx`, `w1f4VerificationStructure.test.tsx` and `coldWorkActions.test.tsx`.
   - (a) Move the EV non-loaded tests to `domainActionVerification.test.tsx` and `operatorRouteFrames.test.tsx`. Keep `siteAction.test.tsx` only to assert that an EV domain ID makes no W1 battery request.
   - (b) Keep ruling 16 as written.

5. **The Action route branch is cold-only.**
   - `SiteActionFrame` (`SiteAnalyticsFrames.tsx:1588-1590`) enters `ColdActionRoute` only when `site.site_type === "COLDCHAIN"`. Every EV Action, domain IDs included, goes to `renderW1` and the W1 battery client (:1609, :1655-1660).
   - `ColdActionRoute` redirects a loaded domain Action on a non-verification section to `/verification` (:1540-1541), and otherwise falls back to W1 (:1543).
   - (a) V4a widens the branch to `COLDCHAIN | EV_CHARGING` with the same redirect and W1-fallback rule. This keeps pre-flight 28's mixed W1 rows and E2, and needs no new route.
   - (b) Make EV verification-only, with no W1 fallback.

6. **Client fallback copy says "cold".** `domainActionClient.ts:25-26` hard-codes `The cold work read could not be reached.` and `The cold work read answered in an unexpected shape.` On an EV Site the network-error and malformed-200 refusal would show cold copy inside `EV work unavailable`. No EV literal has been ruled.
   - (a) Make the client copy depend on Site type: `The EV work read could not be reached.` / `The EV work read answered in an unexpected shape.` V2a owns the index path and V4a the detail path.
   - (b) Use a neutral `work read` sentence for both domains. This changes cold output.

7. **The K2 `Window` control and Actions list are cold-named.**
   - `ColdWorkWindow` (`SiteWorkActions.tsx:622-658`) renders `data-cold-work-window*` attributes and class `cold-work-window`.
   - `ColdSiteWorkActions` (:817) uses the `data-cold-work-*` family.
   - `WorkSubrow` (:2001), `useWorkCounts` (:1942-1967) and `SiteWorkCasesFrame` (:2089-2112) branch on `COLDCHAIN`.
   - Ruling 14 says to reuse the control, and ruling 18 sets the `data-domain-cases` precedent only for cases.
   - Options:
     - (a) Generalise to `data-domain-work-*` and a neutral component name. Keep the `data-cold-work*` attributes only on cold, as ruling 18 does for `data-cold-cases`, so the K2/K5 tests stay unchanged.
     - (b) Reuse the cold-named attributes on EV. This is misleading in tests and captures.

8. **The index parser rejects the whole EV Site list, and leaves a dead link until V4a.**
   - `domainActionClient.ts:217-221` parses any non-`COLDCHAIN` row as a W1 row (`title === null`, W1 state). An EV row (string title, `state:"OPEN"`) fails, and `rows.every(isRow)` (:243) turns the whole index into the unexpected-shape refusal. The types are fixed to `domain: "COLDCHAIN"` (:56, :95), and detail requires it (:280).
   - V2a fixes the index. However, `links.action` is `/sites/{code}/actions/{id}/verification` (backend `domain_action_index.py:468`). Until V4a merges (two merges later), that href on an EV Site reaches the W1 battery presenter with a domain ID, which breaks the build spec's no-dead-href rule.
   - Options:
     - (a) In V2a and V3, render EV Action codes as plain text until V4a makes them live. Record this as an interim register row that V4a resolves.
     - (b) V2a also takes the detail parser and the route widening from point 5, pulling them forward from V4a.
     - (c) Accept the transient dead link, since no owner walkthrough happens before W5-04c.

## C. File-list gaps

9. **Files the cards will need but do not list:**
   - **V2a:** `sites/__tests__/coldWorkActions.test.tsx` (the cold regression for points 6-8; K2 tests live there). A new EV fixture module beside `sites/__tests__/coldWorkFixtures.ts`, for example `evWorkFixtures.ts`. `sites/coldWorkPresentation.ts` if shared constants move.
   - **V3a:** `sites/__tests__/coldWorkCases.test.tsx`, which retains `data-cold-cases` per ruling 18, and the EV fixture module.
   - **V4a:** `sites/coldWorkPresentation.ts`, `sites/evWorkPresentation.ts` (point 3) and `sites/__tests__/coldWorkActions.test.tsx`. That file imports the cold Action constants and asserts the cold shell (K4 merge diff).
   - **Register:** no UI card lists `.agent/mock-departure-register.md` (point 10).
   - Recommend adding these to the cards. All other listed files exist except the planned new `evWorkActions.test.tsx`, `evWorkCases.test.tsx`, `evWorkPresentation.ts` and `tools/w504-ev-work-evidence.mjs`.

## D. Register

10. **R77 and R78 do not match rulings 14 and 20, and there is no EV equivalent of R88.**
    - R77 (register :132) still describes a fixed-EAT topbar swap. R78 (:133) still says "when stored subtitle is null"; cold R90 already says "Site read has no subtitle".
    - The page-local `Window` control (ruling 14, D1 R88 extended) has no EV row.
    - Options:
      - (a) The Architect rewords R77/R78 and adds the R88-equivalent EV row (R111) before V2a.
      - (b) V2a makes those edits and adds the register to its file list.

11. **R104 overlaps R80 (Low).** R104 (:186), "currentness notice, blue/amber, cold R91", repeats R80's placement wording. Ruling 23 meant R104 to cover tone.
    - (a) Narrow R104 to "tone only; placement is R80".
    - (b) Leave both as they are.

## E. Caps (lesson 15) and expanded-state exemption

12. **Three measured states have no cap.**
    - The ruling 25 caps match their cold equivalents:
      - Work main 1600/2000, Actions 650/850, strip 100/150 and notice 110/160 equal K2.
      - Case 650/650 (680 with one preview open) equals K3.
      - Action main 1500/1900, status 140/200 and notice 110/160 equal K4 ruling 7.
    - EV criteria 360/590 is tighter than cold's 500/760. It is still adequate because the three EV criterion texts are fixed server literals (backend `domain_action.py:55-59`) that never carry 160-character text. K4 measured four cold rows at 292/433 and the mock measures three EV rows at 243/401.
    - Uncapped states:
      - the untitled non-loaded state panel (K4 measured 220-315 / 266-384 px at 1440/390);
      - the missing-intent `Declared verification plan` panel;
      - the successful-zero Actions panel (only the positive Actions panel is capped).
    - Options:
      - (a) Cap the state panel and the missing-intent panel at the criteria cap 360/590, and the zero Actions panel at the empty-case cap 460/560. Same miss rule as ruling 25.
      - (b) Measure and report these states without gating them.

13. **Exemption gap (Low).** Ruling 26 lists the disclosures. It does not say whether an open validation error under the `Window` control (`role="alert"`, `SiteWorkActions.tsx:658`) counts toward the strip/page caps.
    - (a) Treat the open error as a user-triggered state: exempt, but measured.
    - (b) Gate it.

## F. Departures

14. **No unlabelled departure found, with one dependency.**
    - The detail and index carry no Site fields, so the EV status and scope strip take `display_name` from the Site read.
    - `shortName("Depot Charging Hub")` returns `Depot` (`siteWorkCases.tsx:269`), which matches mock `Scoped to Depot`.
    - The backend has no `short_name` (Q12), and the producer stores it only in the manifest.
    - If rulings 32+ add a stored short name, V2a must switch to it. Otherwise this point holds.
    - The other literals checked match the mock or a labelled row: `origin.label` `Finding <8>` (R74), `all_due_dates_unset` (R76), the EV criteria and `Pending`, and the `ev-action` closing notice (build spec E-closure).

## Readiness rulings that still hold

- **1-12 and 27-31:** backend only; not changed by this check.
  - Ruling 1's K4/K5 precondition is now met.
  - Its "fresh readiness check" is this file, and point 1 adds the V1b merge and producer gate.
- **13, 17, 19, 21, 22, 24 and 25:** hold as written.
- **14 and 18:** hold, with point 7's attribute naming and point 8's interim link.
- **15:** holds in substance. The location moves per point 3.
- **16:** holds with points 2, 4 and 6.
- **20:** holds; the register needs point 10.
- **23:** holds. R104-R110 are already registered (:186-192); see point 11.
- **26:** holds, with point 13.

Count: 14 points. Highs: 1, 3, 8. Mediums: 2, 4, 5, 6, 7, 9, 10, 12. Lows: 11, 13, 14.
