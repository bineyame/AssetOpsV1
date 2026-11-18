# W5-04c independent review: V4a, V4b and V5

Reviewer: fresh Claude reviewer (did not author the slice). Date: 2026-10-24.
Branch `task/W5-04c-ev-action`, head `b1e8e999`. It includes main `7d8c3273` with W5-04b, merged at `12434612`.
Diff reviewed: `git diff 7d8c3273...b1e8e999 -- . ':!.agent'`, plus the register, the ledger and the evidence under `.agent/`.

## Verdicts

| Unit | Verdict | High | Medium | Low |
|---|---|---|---|---|
| V4a: EV Action detail, the shared shell, live EV links | **ACCEPT** | 0 | 0 | 2 (L1, L3) |
| V4b: captures and ledger | **ACCEPT** | 0 | 0 | 1 (L5) |
| V5: closeout lineage test | **ACCEPT** | 0 | 0 | 2 (L2, L4) |

No finding blocks a merge. The Low findings can be fixed on the branch, or carried, at the coordinator's choice.

## Checks I ran (all on `b1e8e999` in `AssetOpsV1-review6`)

- **`npx.cmd tsc --noEmit`:** exit 0.
- **Targeted vitest, 12 files** (`domainActionVerification`, `evWorkActions`, `evWorkCases`, `siteAction`,
  `siteActionVerification`, `w1f4ChangesWorkStructure`, `operatorRouteFrames`, `operatorRailInventory`,
  `coldWorkActions`, `coldWorkCases`, `w1f4ActionStructure`, `w1f4VerificationStructure`): **351/351 passed**, 29.8 s.
- **Cold byte identity, rerun independently.**
  - I ran the scratch probe (`cold-bytes/zzColdBytes.scratch.test.tsx`) at head `b1e8e999`. I also ran it at base
    `7d8c3273`, in a temporary detached worktree that has since been removed.
  - Head against base: **40/40 keys, 0 differences.**
  - Head against the committed `cold-base.json` (from `ad7b82f9`): also 40/40, 0 differences.
  - The probe is not vacuous. It has 36 distinct outputs, and its loaded states contain `Declared outcome criteria` and
    `Related activity`. Its state set covers every presentation field: currentness ×4, owner null, long, no revision,
    404, 409, 503, unreachable, loading, the bare and `/plan` redirects, and three real-client fallbacks.
  - The scratch file was removed from `src` afterwards. `git status` is clean.
- **My own non-vacuity mutations** (each reverted with `git checkout`):
  - The EV parser accepts any cold result value: 1 failure (the EV detail parser test).
  - `domainVerificationHref` drops the window: 10 failures across `domainActionVerification`, `evWorkActions` and
    `evWorkCases` (the Verification-link, redirect and reload tests).
- **Focused Postgres.**
  - Files: `test_w504_ev_intent_api.py` and `test_w504_ev_intent_postgres.py`, `-n 2`.
  - Database: private `assetops_w504crev_test`, with PYTHONPATH set to the review6 root, `backend`, `contracts`,
    `host`, `simulator` and `gateway`. Without those paths, the editable installs resolve to the main checkout and
    collection fails.
  - Result: JUnit **tests=21, failures=0, errors=0, skipped=0**, wall time 6 m 45 s. The V5 test took 39.8 s.
  - The database was dropped, and no `assetops_w504crev%` database remains.
- **`tools/check-all.ps1`:** **all 11 guards passed.** This includes the missing-claim orphan scan (merge-base
  `7d8c3273`), the dependency registry, navigation truthfulness and the screen ledger (110 screens, 258 panels).
- **Not run, by instruction:** captures, the full vitest suite, the production build and the full backend suite.
  - For the first three I rely on the implementer's post-merge run on `7ee032b8`/`b1e8e999`: vitest 126 files,
    2970/2970; build green.
  - The full backend suite was not run by anyone. See Architect item A4.

## Focus areas

1. **Mock fidelity, 1440 and 390.**
   - I viewed the `post-w504b/action-run2` captures for positive, historical (narrow), missing-intent (desktop),
     worst-text (narrow), forbidden-403 (desktop), invalid-422 (narrow) and not-found-404 (narrow). I compared them
     with v69 `ev-action` (`index.html:710-713`).
   - The breadcrumb, `{code} · {title}` heading, question subtitle, Open site, single Verification tab, amber `Open`
     and `{owner} · {full Site name}` status are as the mock shows. So are the sole `Declared verification plan` with
     three plain `Pending` cells and the blue closing literal.
   - Every visible departure is registered: R80/R104 notices, R109 wrap, R110 untitled state panel and R111 stored
     Site name.
   - At 390, the criteria table at 318/318 matches the mock's own 320/320 (`W5-02-04-mock-measurements.md`). It is not
     a departure, and judgment call 8 overstates it as one.
   - **No unlabelled departure.**
2. **Cold byte identity.**
   - Verified independently, as above.
   - Cold literals moved to `coldWorkPresentation.ts` (ruling 47) and are pinned exactly by the new presentation test.
   - The cold Work list href is identical (`COLD_WORK_PRESENTATION.actionHref` returns the server href unchanged; it
     has a test). The cold case href is identical too (`evCaseActionHref` returns undefined for `legacyCold`; it has a
     test).
3. **Correctness.**
   - **One shell.** `DomainActionShell` and `DomainActionRoute` take a `DomainActionPresentation` (header, subtitle,
     badge, status tail, disclosure, currentness, state and closing notice). `DomainActionVerification` takes a separate
     `DomainActionPanelPresentation`. This matches rulings 15 and 41.
   - **Presentation selection.** Before a read, the presentation follows the Site type. After a read, it follows
     `action.domain` (P-K2a-48).
   - **Parser.** COLDCHAIN or EV_CHARGING. An EV detail accepts only `PENDING` (`EV_DOMAIN_RESULTS`); misaligned or
     other values are refused. Cold keeps `DOMAIN_RESULTS`.
   - **Refusal copy.** The EV network and shape sentences pass through the optional `siteType` (ruling 64). The cold
     three-argument call is unchanged, and the test asserts that.
   - **Dispatch.** `DOMAIN_ACTION_SITE_TYPES = [COLDCHAIN, EV_CHARGING]`. The bare, `/plan` and `/history` addresses
     redirect to `/verification` and keep `from,to,known_at`. A W1 ID on an EV Site falls back to the W1 presenter
     (`siteAction.test.tsx`). An EV domain ID makes no W1 battery request.
   - **Live links.** `evActionHref` takes the server pathname only. It sets `from` and `to`, and sets `known_at` only
     when the scope has one. It never carries the cursor or the server query. It is used by the Work row
     (`SiteWorkActions.tsx`) and by both case-row `UTC and IDs` links (`siteWorkCases.tsx`).
     - The Work list scope is the request scope, so the cursor is never on it.
     - The case scope's `knownAt` is the explicit URL value.
     - Note: a list page reached by its pager carries a pinned `known_at` in its own URL, so its Action links carry
       that cutoff too. That is consistent with "explicit in the URL", and the detail reads at the same cutoff as that
       page.
   - **Leading notice.** `SCREEN_LEADING['ev-action'] = '[data-domain-action-currentness]'`. `expectV69Panels('ev-action')`
     runs in every currentness test, and the strip → notice → plan order is asserted.
   - **V5.** It asserts zero rows in the work tables before and after the Action and intent POSTs. It also asserts that
     the public session row is unchanged, three `PENDING` results citing nothing, no work link, and the
     Finding/revision/session/evidence lineage, at both the default read and `known_at`. Weaker points are in L2.
   - **Capture tool.** It stays capture-only. Its only process call is the scoped Chrome cleanup by profile command
     line. It makes no API writes. The `data:` blank page with a device-width viewport is a sound fix for the 980 px
     `about:blank` mobile default; cases-run5 passes 476/0.
   - **Ledger.** The `ev-action` `data_owner` and `supported_claim` match ruling 68 byte for byte. The row has
     `coverage:"partial"`, `task:"W5-04"`, `follow_on:null`, owner tier pending and `unresolved_panels:[]`, the same
     shape as V3b's rows. The panel contract is `reviewed selected Site read`. The registry is untouched, and
     `A-ev-work-projections` and its three predecessors are all `open`.
4. **Judgment calls.**
   - **1 (Q1):** decided by ruling 67, and the code follows it.
   - **2 (Q2):** decided by ruling 68; the strings match.
   - **3:** `evWorkActions.test.tsx` and `operatorRouteFrames` are V4a files (rulings 67 and 47, and the card).
     `w1f4ChangesWorkStructure.test.tsx` is not on the V4a list. The edit is forced by the switch and is minimal.
     Ratification needed (A1).
   - **4:** EV `PENDING`-only follows from pre-flight 45 and the backend's EV `initial_results`. Strictness on other
     values is a reasonable reading of the K4 precedent, but no ruling decides it (A2).
   - **5:** decided by P-K2a-48 and ruling 15.
   - **6:** not decided. Ruling 40 frames missing intent as UNKNOWN. The producer gives HISTORICAL; UNKNOWN is a pure
     vector, and the test is good (A3).
   - **7:** consistent with ruling 69 (the `.mjs` stays capture-only).
   - **8:** no departure at all (see focus area 1).
   - **9:** superseded. V3a's `evWorkCases.test.tsx` now exists, and ruling 71's tests are in it.
5. **Test strength.**
   - Strong. The tests cover the EV frame and status literals, plain `Pending` cells, absent Related/Inspect/disabled
     controls, all four currentness states with tone and order, the loading/404/409/403/422/503 untitled panel with a
     Retry that re-reads, the parser refusals, the client sentences for both domains, Work-click → detail → Verification
     link → reload, both case screens with and without a cutoff, and cold href parity.
   - Non-vacuity was confirmed by the implementer's mutations and by mine.

## Findings

**L1 (Low, V4a): dead `windowQuery` presentation field.**
- **Where:** `frontend/src/sites/DomainActionVerification.tsx:64`, `coldWorkPresentation.ts:133`,
  `evWorkPresentation.ts:111`.
- **What:** `DomainActionPresentation.windowQuery` is declared and set, but never read. The real decision is
  `site.site_type === "EV_CHARGING"` at `frontend/src/shell/SiteAnalyticsFrames.tsx:1643`.
- **Why it matters:** `domainActionVerification.test.tsx:528-529` asserts the dead field, which suggests coverage that
  does not exist. That is two sources of truth for one rule.
- **Fix:** drive `window` from the presentation (`domainActionPresentation(site.site_type).windowQuery`), or delete the
  field and its assertions.
- **Kind:** preference/hygiene, not an acceptance gap.

**L2 (Low, V5): the lineage test's no-write check is narrower than it could be.**
- **Where:** `backend/tests/test_w504_ev_intent_api.py:299,313-317,349`.
- **What:**
  - `WORK_TABLES` covers opening an INC or WR (`work_case`, `incident`, `maintenance_work_request`) and the case link.
    It omits `work_case_action_link`, `work_case_finding_link`, `work_case_revision`, `verification_outcome` and
    `verification_evaluation_request`.
  - `session_rows()` compares only the cited session, not the whole selected session list. The task's acceptance
    names SES-011 and SES-012 as observations that stay unchanged.
  - `body["status"] in ("CURRENT", "HISTORICAL")` would accept the two reads swapping.
- **Fix:** add those tables, compare the full session item list, and assert CURRENT for the default read and
  HISTORICAL for the `known_at` read, if that is what the producer guarantees.
- **Kind:** test strength. The current assertions do meet acceptance 1 and 3 ("no automatic Incident, Maintenance
  request or verification success").

**L3 (Low, V4a): the R113 status cites the wrong ruling.**
- **Where:** `.agent/mock-departure-register.md:207`.
- **What:** it cites "(rulings 67, 69+)". The case-row closure is ruling **71**.
- **Fix:** cite "rulings 67, 71".

**L4 (Low, V5 packet): the handoff opens with superseded state.**
- **Where:** `.agent/W5-04c-handoff.md:3,98-101,121`.
- **What:** the opening still says "Not yet rebased on W5-04b". Judgment calls 1, 2 and 9 still read "open" or
  "skipped". Rulings 67, 68 and 71 and the post-merge batch resolved them in later sections.
- **Fix:** mark them resolved inline, so a merge reader does not act on stale text.

**L5 (Low, V4b evidence): superseded captures sit beside current evidence without a label.**
- **Where:** `.agent/W5-04c-evidence/`.
- **What:** the top-level `w504c-*.png`, `w504c-evidence.log`, `w504c-measurements.json` and `ev-work-recheck/` predate
  the ruling 67 tool change. They assert the bare server href. The current evidence is `post-w504b/`.
- **Fix:** add a README line marking them superseded, or delete them as was done with the other superseded run folders.

## Architect items

- **A1.** Ratify the V4a edit to `frontend/src/sites/__tests__/w1f4ChangesWorkStructure.test.tsx`, a V2a/V3a file. Its
  plain-code assertion now expects the live, scoped link. The edit was forced by flipping `EV_ACTION_LINK_LIVE`.
- **A2.** Confirm the strict EV detail parser.
  - Any EV result other than `PENDING` refuses the whole detail as "unexpected shape".
  - This is correct for the current contract.
  - A future evaluator that writes EV results must widen `EV_DOMAIN_RESULTS` and `EV_RESULT_LABELS` in the same
    change.
- **A3.** Confirm the pure-vector-only proof for three V4b states the producer cannot reach:
  - **409** `DOMAIN_INTENT_BASIS_CHANGED`. Build spec line 88 says "V4b captures 409". The handoff cites rulings
    54/55, which address pending/stale and the fixture clock, not 409.
  - **Missing intent with UNKNOWN** (ruling 40). The producer's missing-intent read is HISTORICAL.
  - **In-panel 503.** The W5-04a precedent accepted the Site-level refusal capture.

  All three have good component and route vectors.
- **A4.** Decide the full backend gate for W5-04c.
  - The task gate says "one real-Postgres full suite per sub-slice", and the V5 card says "same-revision real-Postgres
    suite".
  - This branch changes no backend product code, migration, composition or fixture; it adds one test only.
  - The focused w504 runs pass: the implementer's 53/0 across all five files, and my 21/0 across the two V5 files.
  - Whether the tiered policy waives the full suite here is the coordinator's or Architect's call. Nobody has run it.

## Residual risk not named in the packet

- **Tall mobile header on short pages at 390.** On short narrow pages (the 404, 403 and 422 captures), the dark mobile
  header band stretches to about 275-335 px.
  - The accepted cold K4 capture shows the same thing (`W5-02c-K4-evidence/w502c-k4-narrow-action-not-found.png`).
  - It is pre-existing shell behaviour, not introduced here. It is worth carrying to the post-wave UI/UX pass.
- **No browser capture of the historical Work-click path.** The browser capture of the Work-click path covers only the
  default window, with no explicit `known_at`. The historical click → detail path is proven by component tests, and the
  case captures prove an explicit-cutoff href.
