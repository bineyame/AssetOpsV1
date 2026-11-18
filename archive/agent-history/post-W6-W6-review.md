# Independent review: post-W6 W6-global-Work (fix card + caps fix round)

Reviewer: fresh Claude reviewer (not the author). Branch `task/post-W6-W6-global`, head `b41e56c6`, product `6f54ad1b`,
base `821ad6bf`. Diff reviewed: `git diff main...HEAD -- ':!.agent'` plus `.agent/mock-departure-register.md`.

## Verdict: ACCEPT-with-findings (two Medium findings to fix on the branch; no High)

The backend link changes, R352-R372 frontend work, R371 route + guard, caps rulings 1-4 and the register are implemented
as ruled, and the checks I ran pass. Two gaps stand against the rulings' explicit wording: one copy-truthfulness bug
in the pager (Q6), and a missing test for one basis member (Q1).

## Findings

### M1 (Medium, acceptance gap Q6/R354): a numeric range is printed after Next from a URL-opened later page
`frontend/src/work/globalWorkParts.tsx:246-251` (`Pager`). `unknownOffset = cursor !== null && trail.length === 0`.
Scenario: open `/incidents?...&cursor=C2` from a URL (trail `[]`) and you get "Later page · 25 of 80", which is correct.
Click Next. The trail becomes `[C2]` and the cursor C3, so the caption is `Showing 26–50 of 80`. C2 was any later page
(page 2 or later), so the true offset is still unknown, and if C2 was page 2 the rows are actually 51-75. Q6 says
"do not print a numeric range whose offset is unknown". Only a trail rooted at page one (`trail[0] === null`) has a
known offset. Fix: `unknownOffset = cursor !== null && (trail.length === 0 || trail[0] !== null)`. Add a test that
opens from a URL, clicks Next, and checks for "Later page", on one root (shared component). The existing test
(`globalIncidents.test.tsx:509-516`) covers only open-then-Previous. This affects all four lists.

### M2 (Medium, test gap Q1): Action-code basis membership is not tested
`backend/assetops_backend/work/global_index.py:352-353` adds `basis["action_codes"]`. Q1 says the selected basis must
include any newly read Action public code, and that this must be tested. Mutation proof: I replaced that line with
`pass` and ran `test_w601b_global_maintenance.py` and `test_w502_domain_work_links_postgres.py`. Result: 21 passed.
Grep shows no test reads `action_codes` from the basis; `test_action_without_a_stored_code_keeps_its_honest_label`
checks only the helper's return. The linked-request-ID member has a proper test
(`test_linked_request_ids_enter_the_basis`, monkeypatch, token must change). Fix: add the same monkeypatch test for
`GlobalReadTx.action_codes` on the `linked` seed: same rows and hrefs, a different code, so the selection token must
change. The code itself is correct.

### L1 (Low, residual): `site_domain` is not in the row basis
The rows and `links.site.href` read `site.site_type`, but the cursor basis does not bind it. The trigger
`site_type_fixed_after_evidence` (0005) blocks type changes only once evidence exists. A Site with work cases but no
evidence could in principle change type between page one and page two without a 409. Q1 asked only for linked request
IDs and Action codes, so this is not a ruling breach. It is noted for the Architect.

### L2 (Low, pre-existing pattern): membership and deviation lines use `var(--muted, #6b7a90)`
`frontend/src/work/globalWork.css` (new `.global-work-membership`, `.global-work-deviation`). `--muted` is not defined
in `ui/tokens.css`, so the fallback `#6b7a90` applies, about 4.4:1 on white at 12 px (under 4.5:1). Four existing rules in
the same file use the same fallback, and `tokens.css:70-74` explains why `--text-muted` is darker. This is preferable to
fix in the W1 UI/UX pass. It does not block.

### L3 (Low, residual): overflowed links in a clamped Findings / work cell stay in the tab order
Links past line 2 of a collapsed `CellDisclosure` (for example, several Finding, Action and request links) are
clipped but still focusable, so keyboard focus can land on an invisible link. This is the same behaviour as the earlier
three-line clamp and is not introduced here. The "Show full" toggle gives a visible route to them.

## Ruling-by-ruling check (verified in code)
- Q1 scope: only `work/{global_index,global_detail,operational_index}.py` and `adapters/postgres_global_read.py`.
  `site_index.py` is untouched. No migration or schema change, no cursor format or SELECTION_VERSION change, no
  access change. `linked_request_ids` and `action_codes` are added under their own keys, only when non-empty, so
  unlinked or Action-free rows keep their basis. The digest stays consistent (one `_digest` over row bases). Stable
  paging across linked requests is tested (`test_linked_request_destinations`).
- Q2: `site_domain` is on all four row kinds and on detail `selected`. It comes from the stored `site_type` (detail
  reads it in the same snapshot via `_SITE_TYPE`). The TS validator checks the enum on rows and detail.
  `findingLinks` and WR `sourceOf` render cold and EV Findings as plain text with no unavailable suffix; mini keeps its
  link. Tested on three domains (backend MINIGRID/COLDCHAIN/EV_CHARGING; frontend mutation below).
- Q3: `site_home_href` is used for every `links.site` (incident, corrective, preventive, operational, detail). Tab
  links stay on `_site_href`. The EV row test asserts `/sites/{code}/ev` on all four roots and the detail.
- Q4: `linked_requests` come from the same `_LINKED_REQUEST_CODES` selection, with `linked_request_codes` unchanged.
  The href carries `known_at` only when it is explicit. `LinkOrText` is used, and the D1 (R73) label is under Incident cases.
- Q5: `select_incidents` now passes `cutoff`. `_window_query` adds `known_at` only for an explicit cutoff, at its exact
  instant. Implicit, explicit and page-two forms are tested.
- Q6: copy is correct for the URL-opened page; see M1 for the Next case.
- Q7: `defaultGlobalWorkWindow` returns `[today-6d, tomorrow)`. The four membership sentences match verbatim.
- Q8: refusals use `role="alert"`; loading and EMPTY_SCOPE use `role="status"`.
- Q9: the tabs wrap at 760 px or less. `UnavailableTab` is untouched. R396 has a visible label inside the tab landmark.
- Q10: the COMPLETE label is verbatim, positioned by root order, and the "not in this read" fallback works. The UUID
  is in the `Stored record ID` disclosure. ACT codes come from `action` and `domain_action` (both NOT NULL in the
  schema). The `Action {id8}` fallback with a `Stored Action ID` disclosure is on the Overview.
- Q11: on a refusal the header and one refusal show, with no panels (mutation below). Reload appears only for a
  loaded body or a 503. The detail 503 sentence is verbatim. Open site is hidden without an href. The no-site
  subtitle and body are verbatim.
- Q12: "Verification open" with the summary suffix, "Verification opened · outcome not established", and
  "Unrecognised event · meaning not established" with the `Stored event code` disclosure.
- Q13/R371: the route sits before `*`, with a shelled panel "This address is not served" and "Open this request's
  overview" that keeps the validated `site_id`/`known_at`. It makes no API read. The guard rule plus two rail
  fixtures are in place, and the guard fails on mutation (below).
- Q14: historical lines show seconds; current lines show minutes.
- Q15/caps 1-2: the q15b table matches the ruled caps, 22/22 pass, and Preventive plan at 390 is exactly 690.
- Q16/caps 3: the widths are [90,110,150,130,120,270,125,90] = 1085, fixed layout. The 390 minimum is 1085.
  q15b R356 shows 1090/1090 with the scrollbar present.
- Caps 4 / guide §1: `CellDisclosure` is a native button that appears only on overflow (ResizeObserver plus
  MutationObserver). Its name is "Show full {column} for {code}" with `aria-expanded`/`aria-controls`. It is a
  sibling of the value (never inside a link), has a visible focus outline, and has no title or popover. The three
  extra lines (two correction lines and the Finding/Action line) use the same two-line-preview treatment that guide
  §1 prescribes for any clamped table cell, so no Architect question is needed.
- Q17: the R355/R358/R362/R363/R365/R369 labels have matching `data-mock-deviation`, and all are existing register
  rows. The manual form uses only response Sites (`coverage.sites`, since the backend `scope` carries no sites) with an
  empty `Event time` input.
- Q18: "1 request" pluralisation and the `EV connector c1` / `Backup generator · …` asset words are done.
- Q21/register: the only new row is R396. R65/R73/R74 are extended in place.

## Checks I ran (worktree `AssetOpsV1-review8`, head b41e56c6)
- Backend focused, real Postgres `assetops_test`: `test_w601a`, `test_w601b`, `test_w601c`, `test_w601e`,
  `test_w502_domain_work_links_postgres`, `test_r373_request_access`. **80 passed**, 0 failed, 873.9 s.
- Backend mutation (M2): with the `action_codes` basis line removed, w601b plus w502 links gave 21 passed (no test
  caught it). Restored.
- `npx.cmd tsc --noEmit`: rc 0.
- `npx.cmd vitest run src/work`: **9 files, 165 tests passed** (this ran here; it was not blocked by the sandbox).
- Frontend mutations (each restored, tree clean afterwards):
  - `findingLinks` made the identity: 2 failures (Incidents and Maintenance R352).
  - Children rendered on refusal: 22 failures.
  - `CellDisclosure` given a generic accessible name: 10 failures.
- `tools/check-all.ps1 -Python <plan2 .venv>`: **11/11 PASS**, including Architecture seams, Navigation truthfulness
  and Agent workflow.
- Guard mutation: with App's R371 element replaced by `<RouteNotAvailableFrame />`, `Invoke-NavigationTruthfulnessCheck`
  returned 1 failure naming R371. Restored.
- Evidence summaries: b18r revision 6f54ad1b, 186 indexed + 44 extra, titles 186/186 vs mock, 0 overflow, 0 console
  errors, 0 unexpected changes. b19r 194/194 + 12 links, 0 overflow, 0 errors, empty `changed_vs_previous`. q15b
  product 6f54ad1b, 136 assertions all verified.
- Stray files: none in this branch's diff. The three tracked `.pyc` files (including
  `.agent/W6-01-evidence/E2/__pycache__/api_empty_scope.cpython-312.pyc`) already exist on `main` and at the base
  `821ad6bf`. The branch did not add them, and their removal belongs to a separate cleanup.

## Not verified by me
- The full backend suite (I cite the coordinator's report: 4063 passed plus 1 environmental failure that was fixed).
  The packet does not reproduce the command, JUnit counts or wall time, which is an evidence gap to close in the
  coordinator record. Backend code is unchanged since `fe52c862`.
- The full vitest run, the production build and the captures (per the constraints). I did not view the screenshots;
  the capture claims rest on the summary JSON.
- Some b18r phases (inc, prev, op, hist, probe, linkmini) and b19r part-detail were captured just before 6f54ad1b.
  The packet says those screens are unchanged by 6f54ad1b, which touched only `GlobalMaintenance.tsx`. I confirmed
  that commit's scope from the packet only, not by diff.
