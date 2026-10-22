# W6-01c review (C1 detail read, C2 Overview, C3 Maintenance record)

Reviewer: fresh independent Claude reviewer, 2026-10-23. Read-only review: no tests, servers or browsers were run, because a full suite was running on the machine.
Branch `task/W6-01c-request-overview`, head `675db0ae`. The diff was `git diff main...task/W6-01c-request-overview -- backend frontend tools`: 24 files, +3201/-109. No code changed after `33c4abb0`, because `ba8eaefc` and `675db0ae` touch only `.agent/`. The builder's test runs at `6a052f46`, `6c2b6424` and `33c4abb0` therefore cover the code under review.
Spec: `.agent/W6-01-build-spec.md`, which I read for the C1-C3 cards, §1 Detail DTO, §2 bounds, §3.1 CL3, the "C1-C3 pre-flight rulings" and the Codex retrospective. Handoff: `.agent/W6-01c-phase-handoff.md`, Run C1/C2/C3.

## Verdict

**REVISE.** The verdict is set by a small C2 fix round for M2–M4 below. M1 goes to the Architect.

Against the C1–C3 rulings as built, I found no correctness defect, no High finding and no unlabelled mock departure. On those rulings alone the verdict would be ACCEPT, conditional on M1.

Codex's later "C4 pre-flight rulings" put C2 obligations on this branch. They are in main's `.agent/W6-01-build-spec.md`, read at `AssetOpsV1-plan2/.agent/W6-01-build-spec.md:660`, "Prerequisite and ownership". The built C2 does not meet three of them (M2–M4). That spec says "If the reviewed C2 implementation places any shared part privately, its C2 owner fixes that seam before C4 starts." These three items are why the verdict is REVISE.

## Findings

**M2 (Medium, C4 prerequisite P-C4-1). The shared request shell parts are private in `workRequestShared.tsx`.**
- Exported today: `useWorkRequest`, `WorkRequestRead`, `WorkRequestFailure`, `WorkRequestFrame`, `WorkRequestTab`, `ownerOf`, `recordHeads`, `stateLabel` and the literals. Together these cover the load/result state and the page-query/no-fetch path.
- Not exported: the breadcrumb, `Open site`, date bar, refusal block, `mheader` and tab row. They are file-local functions at lines 137, 164, 240, 272, 342 and 226, as are `subtitleOf` (177), `LiveTab` (192), `TAB_LABEL` (187) and `TAB_SUFFIX` (189).
- C4 could reach all of them only through `WorkRequestFrame`, and the ruling names each part.
- Literal fix:
  - Prefix `export` on `function WorkRequestBreadcrumbs`, `function OpenSite`, `function subtitleOf`, `function LiveTab`, `function WorkRequestTabs`, `function WorkRequestBar`, `function RequestRefusal`, `function WorkRequestMHeader`, `const TAB_LABEL` and `const TAB_SUFFIX`.
  - Rename `RequestRefusal` to `WorkRequestRefusal` while exporting it, for a consistent public name. This is optional.
  - Keep `WorkRequestTab = "overview" | "record"`. C4 adds `"history"` when it promotes the tab; `workRequestShared.tsx` is on C4's Lane B list.
  - No behaviour change; the C2 and C3 tests stay green.

**M3 (Medium, C4 prerequisite P-C4-1). `events[].payload` is not discriminated.**
- `globalWorkClient.ts` declares `WorkCaseDetailEvent { kind: string; payload: Record<string, unknown> }`.
- Literal fix: replace it with the discriminated union below. Keep the `WorkCaseDetailEvent` name, so `WorkCaseDetail.events: WorkCaseDetailEvent[]` is unchanged.
  ```ts
  interface WorkCaseDetailEventBase { id: string; occurred_at: string; recorded_at: string; actor_kind: string; actor_id: string }
  export type KnownWorkCaseEvent = WorkCaseDetailEventBase & (
    | { kind: "CREATED"; payload: Record<string, never> }
    | { kind: "ASSIGN"; payload: { assignee: string } }
    | { kind: "COMMENT"; payload: { text: string } }
    | { kind: "COMPLETE"; payload: { maintenance_record_id: string } }
    | { kind: "CLOSE" | "REOPEN" | "CANCEL"; payload: { reason: string } });
  export const KNOWN_WORK_CASE_EVENT_KINDS = ["CREATED", "ASSIGN", "COMMENT", "COMPLETE", "CLOSE", "REOPEN", "CANCEL"] as const;
  export type UnknownWorkCaseEvent = WorkCaseDetailEventBase & { kind: string; payload: Record<string, unknown> };
  export type WorkCaseDetailEvent = KnownWorkCaseEvent | UnknownWorkCaseEvent;
  export function isKnownWorkCaseEvent(e: WorkCaseDetailEvent): e is KnownWorkCaseEvent {
    return (KNOWN_WORK_CASE_EVENT_KINDS as readonly string[]).includes(e.kind);
  }
  ```
- The parser in M4 checks the payload shape for each known kind, so the guard is sound.
- `ownerOf` keeps working: narrow with `e.kind === "ASSIGN" && isKnownWorkCaseEvent(e)`, or keep its current runtime string check.
- `GlobalWorkDetailRevision` and `history.revisions` are already exported, so that part of the ruling is met.

**M4 (Medium, C4 prerequisite P-C4-1). The detail parser does not require `CREATED`, and it validates events and revisions only partly.**
- `isWorkDetail` checks events for `id`, `kind`, `payload` and `recorded_at` only.
- `isGlobalWorkDetailBody` checks revisions for `id`, `title` and `recorded_at` only.
- Neither requires at least one `CREATED`, so a 200 without one renders instead of giving the ruled 503 sentence.
- Literal fix in `globalWorkClient.ts`:
  - Event items: also require `isString(x.occurred_at)`, `isString(x.actor_kind)` and `isString(x.actor_id)`.
  - Per known kind:
    - `ASSIGN`: `isString(payload.assignee)`.
    - `COMMENT`: `isString(payload.text)`.
    - `COMPLETE`: `isString(payload.maintenance_record_id)`.
    - `CLOSE`, `REOPEN` and `CANCEL`: `isString(payload.reason)`.
    - `CREATED`: an object.
    - Unknown kinds: any object.
  - Add `&& (value.events as unknown[]).some((x) => isObject(x) && x.kind === "CREATED")`.
  - Revision items: also require `typeof x.revision_no === "number"`, `isNullableString(x.supersedes_revision_id)`, `isNullableString(x.reason)`, `isString(x.occurred_at)`, `isString(x.actor_kind)` and `isString(x.actor_id)`.
  - A failure maps to the existing malformed-200 path (`WORK_STORE_UNAVAILABLE`, which renders `Work records could not be read. Reload.`).
  - Add two cases to the `workRequestOverview.test.tsx` client test: a 200 without CREATED, and an ASSIGN without `assignee`. Both should read as `WORK_STORE_UNAVAILABLE`.
- C2 fixtures already include a CREATED event (for example `event(0, "CREATED")`), so existing tests should hold. The fix round should confirm this.

**M1 (Medium). Two unruled, user-visible styling choices that differ from the mock.** The builder labelled both in the evidence only.
- `frontend/src/work/globalWork.css` (`.work-request .panel-pair { align-items: start }`): the mock `.two-col` is a stretch grid, so Lifecycle is as tall as Work done. In the app, Lifecycle takes its own height; see `C2/screenshots/positive-1440.png` against `mock-wr-overview-1440.png`. The builder made this choice because the §2 Lifecycle cap of 350 px conflicts with a stretched Lifecycle beside the 422 px stress Work done. That is a contradiction in the spec, and the Architect should resolve it, not the implementer. Possible rulings:
  - keep stretch and lift the Lifecycle cap to the Work done cap;
  - or label this a MOCK DEVIATION.
- `WorkRequestRecord.tsx` `Badge` and `.work-record-badge`: P-C3-1 rules the words `Recorded` and `Not established` but not their tones. The mock shows `Captured` in green. The app shows `Recorded` in neutral grey and `Not established` in amber, which matches the mock's amber for Missing. Neutral is the more honest choice for an unverified authored record, but it is still an implementer design choice (handoff C3 choice 5).
- Fix: a ruling and a spec line for each. No code change if both are ratified.

**L1 (Low). P-C1-3 premise.** See item (a) below. The code is right. The spec sentence "after the shared W4 selector returns" is factually wrong, because `m.reduce_state` raises inside the selector. The Architect should amend the sentence. No code change.

**L2 (Low). Tab list element.** See item (b) below. Amend the ruling literal from `<div>` to `<ol>`.

**L3 (Low). No backend vector for an unlineaged outer Finding or Action link.** The `href:null` branch of `links.findings` and `links.actions` in `global_detail.py` (`by_key.get(..., {"lineage": False})`) has no test, which the builder declared as choice C1 note 3. No service path produces such a pin, but a raw-SQL vector in a rollback, like `test_missing_created_is_503`, could cover it. The frontend side is covered by the typed test `workRequestOverview.test.tsx:428`. This is not an acceptance gap; P-C1-1's proof is "exact-pin/href test", which exists.

**L4 (Low, outside the slice). Shared-primitive differences from the mock.**
- The breadcrumb separator is `/` (`ui/primitives.css:233`) where the mock uses `›`.
- `Notice` (`ui/V69Layout.tsx:171`) has no info icon.

Both come from app-wide primitives on main, and the builder labelled both. They belong to the post-W6 UI/UX pass, not to this slice.

## Judgements on the named items

**(a) P-C1-3, the `ValueError` catch: in spec, plus L1.**
- `reduce_state` raises `ValueError("a work case has no CREATED event")` (`work/model.py:136`), so the selector can never return such a case.
- `global_detail.py` catches it, re-reads `rx.events` on the same snapshot, and raises `WorkStoreUnavailable` (503 `WORK_STORE_UNAVAILABLE`) only when CREATED is absent. Any other `ValueError` re-raises.
- The post-return check is kept as well.
- The Site route and the shared selector are unchanged, which is the ruling's intent.
- Negligible edge: an INCIDENT ID with no CREATED would answer 503 instead of 404. Production writes never create such a row.

**(b) `<ol className="site-tabs__list">` instead of the ruled `<div>`: in spec in substance, plus L2.**
- `UnavailableTab` renders an `li` (`ui/UnavailableEntry.tsx:15`), so a `div` parent would be invalid HTML.
- Every other tab row in `src/` uses `ol`, apart from one `ul`.
- The mock's `tabRow` uses neither element: it puts anchors directly inside the `nav`.
- The change is not visible, and the `navigation-truthfulness` multiset is unaffected.

**(c) Mock differences, classified:**

| Screen | Difference | Class |
| --- | --- | --- |
| C2/C3 | Date bar with As known at / Historical as of and Reload | Ruled (P-C2-4, R6) |
| C2 | `Latest activity` line | Ruled (P-C2-6) |
| C2/C3 | Owner/Source two-line previews; Full narrative/activity/owner/source disclosures | Ruled (§2 bounds table) |
| C2 | Lifecycle not equal-height | Labelled, unruled: **M1** |
| C2/C3 | Breadcrumb `/` separator | Labelled; shared primitive (L4) |
| C2/C3 | ` · Not available yet` on unmounted tabs | Ruled (F4, P-C2-5, P-C1-6) |
| C2 | Due `Not set`, State `· outcome not established`, Success `Not recorded`, Warranty `Warranty not recorded`, Asset without diagram link, Verified never done, new chart-note | Ruled (CL3-5, P-C2-6/7/8); also labelled MOCK DEVIATION in the code header |
| C2 | `ol` instead of `div` | (b), L2 |
| C3 | `Record {n} · {UTC}` group row | Ruled (P-C3-1) |
| C3 | Clamp, disclosure and Outcome note inside Technician notes | Ruled (P-C3-1, §2) |
| C3 | Status and Basis words; four gap rows; Time on site as an instant | Ruled (P-C3-1) |
| C3 | Badge tones (neutral Recorded) | Labelled, unruled: **M1** |
| C3 | Footer `What was recorded on site; ...` as the Panel sub-line | Ruled (§2 record row, A2Q7). The mock `panel(title, body, sub)` also renders it as the sub-line. |
| C3 | REC code as plain text plus `The Operational records page is being prepared.` | Ruled MOCK DEVIATION (P-C3-4); labelled in the code header |
| C3 | No notice icon | Labelled; shared primitive (L4) |
| C3 | 390: `Scroll table horizontally` and a 960 px table that scrolls, where the mock wraps four columns | Ruled (§2 panel-local scroll rule; P-B2-7 width pattern) |

I found no unlabelled departure when comparing `C2/positive`, `linked-source` and `stress`, and `C3/positive`, `empty-rec` and `stress`, at 1440 and 390, side by side with `mock-wr-overview-*` and `mock-wr-record-*`. In both screens the panel order, headings, tab labels and order, mheader slots, the Work done key-value rows, the six Lifecycle steps, the six record rows and the notice position all match the mock.

**(d) Builder choices from the Run entries:**
- C1:
  - `detail-history` third revision and its texts: in spec (P-C2-11 requires only a write at +2s).
  - `detail-linked` titles and the clock minus 1 minute start: in spec.
  - No `lineage:false` vector: L3.
- C2:
  - `ol`: (b).
  - Empty `site_id` uses the no-site copy; a repeated one uses the 404 copy with `Request details could not be shown.`: in spec. Both give the ruled refusal sentence, and a repeated `site_id` is an "invalid query" under P-C2-1.
  - Reload after any fetched answer, including a refusal: in spec ("repeats the same route/query").
  - `{label} · Link unavailable at this cutoff`: in spec (P-C2-10).
  - Lifecycle Finding is done for any `work_detail.finding_links` pin: in spec. Each pin is an exact revision pin, as P-C2-7 requires. The Architect may want lineage-true only; I do not raise a finding.
  - `links.detail.label` is the WR code: in spec. The label is not rendered.
  - Overview href carries the API six-digit cutoff: in spec (P-C1-8).
- C3:
  - (1) Outcome note as a line in the cell, not a seventh row, and (2) cell order activity, outcome, earlier: in spec. "Each group repeats the six rows" rules out a seventh row.
  - (3) Earlier versions newest first: in spec; the ruling is silent.
  - (4) Kind labels taken from the §2 chips: in spec.
  - (5) Badge tones: **M1**.
  - (6) The `wr-overview` interaction grammar for History alone: in spec (P-X-2).
  - (7) Group heading as `th scope=rowgroup`: in spec.
  - (8) The test imports the Lane A constant: in spec.

## Checks requested in the brief

- **Every changed file is on a card.** C1 Lane A/B and `tools/w601_seed.py`; C2 Lane A/B plus the extras ruled in P-C2-12 (`global_index.py`, `test_w601b_global_maintenance.py`, `GlobalMaintenance.tsx`, `globalMaintenance.test.tsx`); C3 Lane A/B plus `workRequestOverview.test.tsx`. All 24 files are accounted for. `missing-claim-scan.mjs`, `operatorRouteFrames.test.tsx`, `OperatorShellLayout.tsx` and the rails are untouched (CL3-7).
- **Links are scoped and lineage-checked.**
  - Finding and Action links use `rx.link_selections(rev, None, None, K)` with the `site_index._finding_link`/`_action_link` rules, in pinned order.
  - The source incident is non-null only for a scoped INCIDENT with a revision at K, and its href is the root-occurrence day window.
  - The Site label is `rx.site_name()` from the same snapshot.
  - Request, record, history and incident URLs carry `known_at` only when the request supplied one, at the exact instant `m.iso`.
  - The list `links.detail` cutoff applies only when the list request named one (`test_detail_href_after_c2`, page two included).
- **Maintenance-only route and the single `known_at` rule.** An INCIDENT ID answers 404 (`test_incident_id_is_404`). The refusal order is authenticate, then one non-empty `site_id`, then access, then scope, then UUID and cutoff (`global_work_api.py`). The effective cutoff is chosen once inside the snapshot; a future cutoff is 422 and a repeated one is 422. The page applies the zero-fetch rules for `site_id`, UUID and `known_at` (P-C2-14).
- **Restored Overview elements.** Work done (prose, `Latest activity`, Type/Asset/Warranty/Linked action), the six-step `ol.lifecycle` with the P-C2-7 rules, the chart-note inside the Lifecycle body, empty Panel descriptions, the Source chain, the breadcrumb `Maintenance › {WR} › Overview · site:` and the `Open site` anchor or text are all present and visible in the captures.
- **C3.** The four-column table repeats six rows per head, ordered `(occurred_at,id)`. The earlier-versions disclosure is in place, the empty panel is present, and the notice sentence and plain-text REC code follow the P-C3-4 MOCK DEVIATION, with no `/operational-records` anchor (asserted in tests and in `build_manifest.py`). The ledger `wr-record` interaction text is exact.
- **K4a preserve note holds.** `operatorRouteFrames.test.tsx` and `OperatorShellLayout.tsx` have no diff. The rail's Maintenance item is current through the nested route, as both App-mount tests show.
- **Captures.** C2 has 8 states and C3 has 6, each at 1440 and 390. They include the 403 from the test-only `api_403.py` (`deny_fixture_site`), labelled as not a production grant outcome. The historical capture at `known_at=2026-10-20T12:00:01Z` shows revision 2, and the current capture shows revision 3; the change is asserted. The R8 manifest sentence is the corrected Codex text. The builder reports caps and document width equal to the viewport. I did not remeasure.

## Checks and evidence

- **Not run by me** because of the read-only brief: no pytest, `npm.cmd test`, `npm.cmd run build`, `tsc`, `check-architecture.ps1` or `check-agent-workflow.ps1`. Separately, `npm.cmd test` and `npm.cmd run build` cannot run under this sandbox anyway, because esbuild cannot read the ancestor directories.
- **Builder results I cite, all unverified by me:**
  - Backend `test_w601c_request_detail.py`: 15 passed (166 s).
  - Adjacent `test_w601b`, `test_w401_work_api` and `test_w401_work_read_postgres`: 29 passed.
  - `test_w601b_global_maintenance.py`: 15 passed after C2.
  - Frontend `src/work src/shell src/sites src/estate src/ui`: 2576 passed at `33c4abb0`.
  - `tsc --noEmit` clean.
  - check-all 11/11 at `33c4abb0`.
  - Guard negative proofs for `$expectedTabs`.
- **Unverified:**
  - The full backend suite has no evidence on this revision; the coordinator's run is in progress.
  - The full `npm test` (beyond the five directories) and the production build are not reported in the packet.

## Residual risk not named in the packet

- `test_w601c_request_detail.py` was not rerun after C2 changed `global_index.py`. The coverage holds, because `global_detail.py` does not import `global_index.py`, but the full suite is the only proof on the head.
- The cleanup command `taskkill //F //IM node.exe` may have stopped unrelated node processes on the machine. It was recorded, and it did not affect the code.
