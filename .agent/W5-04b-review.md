# W5-04b review: V3a (EV case tabs) and V3b (cases, captures, ledger)

Independent Claude reviewer, 2026-10-24. Branch `task/W5-04b-ev-cases` at `bf7b0856`; diff `ad7b82f9..bf7b0856`, excluding `.agent`. Main was merged at `84e9a233`.

## Verdicts

| Unit | Verdict | Findings |
| --- | --- | --- |
| **V3a**: EV Incidents and Maintenance tabs | **ACCEPT** | 0 High, 0 Medium, 1 Low |
| **V3b**: walkthrough data, captures, ledger | **ACCEPT** | 0 High, 0 Medium, 2 Low |

None of the findings blocks a merge. The Lows can be fixed on the branch or carried forward.

## What I verified myself

- **Cold and mini-grid are unchanged.**
  - I rendered `SiteWorkCasesFrame` at base `ad7b82f9` and at head `bf7b0856`, using the same harness in a separate worktree.
  - That covered 40 snapshots: cold and mini-grid × Incidents and Maintenance × populated (long text, Finding link, W1 Action link and DOMAIN_ACTION link with an href) / HISTORICAL / PENDING_RECOMPUTE / complete zero / 403 × all disclosures closed and all opened.
  - After removing ` data-domain-cases="COLDCHAIN"`, the `main.outerHTML` at head is **byte-identical** to base.
  - Mini-grid has no `data-domain-cases` attribute.
  - The first run differed only in mini-grid's asynchronous decision-overlay timing. With extra settle passes, both sides are identical.
- **CSS.** The new block in `w1f4-changes-work.css` only adds rules, all scoped to `[data-domain-cases="EV_CHARGING"]`. After normalising the selectors, its rules are identical to the cold `[data-cold-cases]` rules at `w1f4-action.css:210-310`; only comment lines differ. No cold or W4 selector was edited.
- **One form (ruling 57).**
  - `SiteAnalyticsFrames.tsx` mounts `DomainWorkWindow` (`legacyCold` only on cold) and sets `windowForm={domainWorkPresentation(...) === null}` in the same edit.
  - Tests and captures both assert exactly one `form`, which is `form[data-domain-work-window]`, with `form[data-work-window]` absent.
- **Plain INC (R85) and WR → W6 Overview (R83).** The WR href includes `site_id` and the explicit `known_at` when one is set, and omits it otherwise. Both cases are tested.
- **Site-timezone times (R-10).** `siteWindowText(row.occurred_at, cells.site.timezone)` is used. The three spec vectors (Etc/UTC, Addis, date boundary) are asserted, both directly and through the rendered page.
- **Finding version disclosure (R74/R75, ruling 59).** The cell shows `Finding {id8}`, the revision and the exact R75 sentence. The sentence appears on EV only; cold is unchanged.
- **Asset cell (ruling 13).** It shows `asset_label` unchanged or `No asset linked`. There is no GENERATOR mapping and no asset-ID fact.
- **Currentness (R80/R104).** The notice uses the W4 `status`, the build-spec literals and tones, and sits between the strip and the panel. CURRENT shows no notice. `SCREEN_LEADING` gains both entries.
- **No interim dead link (R113).** A DOMAIN_ACTION link with a server href renders as `[data-work-action-plain]`. W1 `ACTION` links stay live. The captures show `Action 0f0f9e7d` as plain text and report zero `/actions/` hrefs.
- **Walkthrough worstcase.**
  - `_worstcase_cases` POSTs 5 INC, 5 WR and 5 records to the W4 routes `/api/sites/{code}/work/cases` and `/records`, with SERVICE attestation through the V1b body builders and 160-code-point values.
  - It refuses unless W lists exactly five of each kind.
  - The `.mjs` has no write calls: its only `fetch` is the CDP `/json/list` call, so it stays capture-only (pre-flight 23).
- **`W504_API_PORT_BASE`.** The default of 8980 reproduces the previous ports exactly (8981/8982/8983/8985/8986/8987), and the producer test still asserts `PORTS["worstcase"] == 8983`.
- **Ledger and panel contracts (ruling 68).**
  - I diffed by row ID. Only `ev-work`, `ev-work-incidents` and `ev-work-maintenance` changed in each file.
  - `data_owner` and `supported_claim` match the ruling-68 literals exactly.
  - The other promoted fields are set as the rulings require: coverage `partial`, task `W5-04`, `follow_on` null, `to_candidate` null, `unresolved_panels` [], tier `Real with honest gaps` (the cold precedent), approval pending.
  - `remaining_work` and `acceptance` are byte-preserved.
  - The panel rows match the build-spec line-72 literals, with status `reviewed selected Site read` and the exact `claim_limit`.
- **Mock fidelity, 32 PNGs.** I inspected submitted, ids-open, historical, zero, 403, worst and worst-one-open at 1440, and worst, historical and one-open at 390.
  - The order is subtabs → Window (R112) → strip → [notice, R80] → panel (v69 title, subtitle in the panel head) → R03 notice.
  - The strip uses the mock sentence and `Manage in {kind} →`. The mock columns and the exact mock empty card are used.
  - Every visible departure from `siteWorkScreen('ev', …)` (`index.html:340-342`) has a register row: R03, R74, R75, R77, R80–R85, R104–R107, R111–R113.
  - At 390 the first column is sticky, the table scrolls inside its panel, and there is no document overflow.
  - I found no unlabelled departure. The one gap in a register row's screen list is L1.

## Findings

### L1 (Low, V3a, register scope; an acceptance-adjacent gap, not a preference)
`.agent/mock-departure-register.md:207`: the R113 row lists screens `ev-work`, `ev-action` only. V3a applies R113's plain-code departure on `ev-work-incidents` and `ev-work-maintenance` too (`frontend/src/sites/siteWorkCases.tsx:514-517`, `:762`, `:792`). The owner column already says "V2a/V3a interim".
- **Why it matters:** V4a closes R113 by screen. If these two screens are missing, the case-row link may be left out when R113 closes, and that is exactly the open question in judgment call 8.
- **Fix:** add the two case screens to R113's screen column. This is a register-only edit, and ruling 47 gives V3a the register.

### L2 (Low, V3b, evidence disclosure)
`tools/w504_ev_work_cases.py:310` (the V1b body builder) posts the Incident with `finding_links: []`, and every walkthrough row has an asset. As a result:
- The Incident `Linked findings` cell, with its `Finding version` disclosure and R75 sentence, is never shown with producer-backed data. Every Incident capture reads `No linked finding`.
- The `No asset linked` fallback is never captured.

Both are pure-vector proof only (`evWorkCases.test.tsx`), and the tests are good. The handoff lists pending, stale, unknown and the in-panel 503 as unavailable captures, but it does not name these two cells or the "late" state in the V3b card.
- **Why it matters:** the packet reads as if every populated cell were captured. Under the project's honest-gap rule an uncaptured state should be named.
- **Fix:** add one line to the handoff naming the two cells as pure-vector only. Optionally see Architect item A3.

### L3 (Low, V3b, capture claim strength; a preference-level hardening)
`tools/w504-ev-work-evidence.mjs:537`: the submitted Maintenance asset claim `(row.asset !== null || row.assetGap)` passes for any value. The submitted row's actual asset (`c1 · EV_CONNECTOR`) is recorded in the measurements, but the claim does not compare it with the walkthrough's returned `asset_label`.
- **Fix:** compare `row.asset` with the manifest's returned label. This is optional; ruling 13's presentation is already proven by the pure tests and their two mutations.

## Test strength and guard mutations

I re-ran the six handoff mutations and six of my own on a scratch worktree at head. Each run covered `evWorkCases`, `coldWorkCases` and `evWorkActions` (71 tests). Every mutation was reverted, and the worktree was clean afterwards.

| Mutation | Failed tests |
| --- | --- |
| 1. EV removed from `DOMAIN_CASE_SITE_TYPES` | 13 |
| 2. Both `SCREEN_LEADING` case entries removed | 8 |
| 3. W4 form left on for EV | 3 |
| 4. EV given cold attribute and class names | 12 |
| 5. R113 switch off (Incidents) / (Maintenance) | 1 / 1 |
| 6. Cold GENERATOR mapping applied to EV | 1 |
| 7. R75 sentence dropped (mine) | 1 |
| 8. Site zone ignored, fixed `Etc/UTC` (mine) | 2 |
| 9. WR href drops the cutoff (mine) | 2 |
| 10. Cold loses `data-domain-cases` (mine) | 1 |
| 11. EV currentness uses the cold attribute (mine) | 8 |
| 12. Domain R84 fallback `?? ""` (mine) | **0 (survives)** |

Mutation 12 survives because `evRequest` always supplies `next_evidence_copy`. That is not a finding: W4 always sends `NEXT_EVIDENCE_COPY` (`backend/assetops_backend/work/site_index.py:47,276`), so the client fallback is defensive and unreachable on the wire. The cold tests share the same blind spot.

My counts differ from the handoff's (for example 8 against 4, and 3 against 2) only because I ran three files and removed both leading entries. All six handoff mutations are killed.

## Checks I ran (head `bf7b0856`)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | Clean, no output |
| Targeted vitest: 10 files (`coldWorkActions`, `coldWorkCases`, `evWorkActions`, `evWorkCases`, `siteWorkActions`, `siteWorkCases`, `w1f4ChangesWorkStructure`, `operatorRouteFrames`, `operatorSiteTabs`, `siteDetailRoute`), `--maxWorkers=2` | **257 passed**, 37 s |
| `tools/check-all.ps1` | **All 11 guards passed**, including navigation truthfulness, the dependency registry, the missing-claim scan, the evidence width check and the screen ledger (110 screens, 258 panels) |
| Postgres: `test_w504_ev_work_producer_postgres.py` and `test_w504_ev_work_cases.py`, `-n 2`, private base `assetops_w504brev_test`, `PYTHONPATH` = review3 backend/gateway/simulator/contracts/host/tools | **22 passed**. JUnit: tests=22, skipped=0, failures=0, errors=0. 88 s (wall 90 s) |

Vitest ran under this session, so the sandbox esbuild failure did not occur here. Afterwards I dropped `assetops_w504brev_test` and its clones (0 remaining).

**Not rerun:**
- The full vitest suite and `vite build`. I cite the implementer's run instead: 126 files, 2930 passed, 505 s on `ff302700`. `git diff ff302700..bf7b0856 -- . ':!.agent'` touches only the ledger JSON and one `.mjs` line, so `frontend/src` is identical to the revision that run covered.
- The captures, as instructed. I checked the logged totals in `w504b-cases-measurements.json`: 484 claims, 472 PASS, 0 FAIL, 12 INFO, `failed: 0`.

## Judgment calls

| # | Decided by a ruling? | Assessment |
| --- | --- | --- |
| 1. Walkthrough edited outside the V3b list | Partly. Pre-flight 23 keeps the `.mjs` capture-only and gives data to the walkthrough. The V2b re-review M1 recommended exactly this `worstcase` walkthrough mode. No ruling adds the file to V3b's list. | Correct choice. **Architect item A1** (ratify ownership). |
| 2. `evWorkActions.test.tsx` 4-line flip | Yes, in effect. Ruling 57 and the V2a review's Low-3 make V2a's interim assertion false once V3a mounts the Window, so the flip is forced. | Accept. There is a merge-conflict risk with V4a, which owns this file under ruling 67. V4a should rebase after the W5-04b merge. |
| 3. Vite port = API port − 3500 | No ruling needed. This is the tool's documented convention (`.mjs` header lines 9–10), and the default ports are unchanged. | Accept. |
| 4. Case 403 panel measured against the 650/650 cap | No. Ruling 25 names populated/empty case caps, and ruling 50's 360/590 is for the untitled Action-detail state panel. | The measured 145/153 passes either cap. **Architect item A2** (name the cap). |
| 5. Strip noun `1 incidents` / `1 maintenance` | Yes, by default. The mock literal is `${rows.length} ${kind.toLowerCase()}` (`index.html:340`). R79 and ruling 19 cover only `ev-work` Actions. Keeping the mock needs no departure. | Accept. A grammar fix would need its own R-row (optional, A4). |
| 6. R75 sentence in the Incident `Finding version` | Yes. The R75 register row covers `ev-work-incidents`, ruling 59 sets the sentence-in-disclosure form, and pre-flight 24 names the linked Incident Finding cells. | Accept. |
| 7. Ledger `interaction` / `unknown_or_empty` untouched; tier set | Yes, by precedent. Rulings 21/43/68 list the fields to set. The cold promoted rows keep identical `interaction` / `unknown_or_empty` text and use `Real with honest gaps`. | Accept. |
| 8. Case-row DOMAIN_ACTION link when `EV_ACTION_LINK_LIVE` flips | **No.** Ruling 67 covers only the `ev-work` Actions list link. The case-row link in `UTC and IDs` (`siteWorkCases.tsx:514`) would become the bare server href, without `from` / `to` / `known_at`. | **Architect item A3.** |

## Items for the Architect

- **A1 (judgment call 1).** Ratify `tools/w504_ev_work_walkthrough.py` and `backend/tests/test_w504_ev_work_producer_postgres.py` as V3b-owned for the `_worstcase_cases` mode and the `W504_API_PORT_BASE` variable. **Recommendation: ratify.** It follows the V2b M1 precedent, keeps the `.mjs` capture-only, posts only through W4 commands, and leaves the default ports unchanged.
- **A2 (judgment call 4).** Name the closed-state cap for a refused W4 case panel. **Recommendation:** use 360/590, mirroring ruling 50's untitled state panel, or explicitly confirm the populated 650/650. The measured 145/153 passes both, so no recapture is needed.
- **A3 (judgment call 8, with L1 and L2).** Decide how the EV case-row DOMAIN_ACTION link behaves when V4a flips `EV_ACTION_LINK_LIVE`. **Recommendation:**
  - Extend ruling 67 to this link: append the case page's selected `from`, `to` and explicit `known_at` to `links.action`, with no cursor.
  - Give V4a `siteWorkCases.tsx`, the RowDetail action link only, and an EV case-row href test.
  - Add the two case screens to R113 (L1).
  - Separately, decide whether a producer Incident Finding link should be added. It would be a V1b body-builder change, and it would give the R74/R75 Incident cell a capture (L2).
- **A4 (optional, presentation).** These follow the mock or the rulings exactly, but a client would see them during the W1-conclusion UI pass:
  - `1 incidents` (mock grammar; judgment call 5).
  - The raw `c1 · EV_CONNECTOR` asset label (ruling 13 / pre-flight 39 forbid enum expansion).

  **Recommendation:** batch both into the post-wave UI/UX pass. No W5-04 change.

## Residual risk not named in the packet

- **Midnight UTC.** `_worstcase_cases` backdates occurrences by up to 11 minutes inside the current UTC day W. A `prepare` started just after 00:00 UTC refuses honestly ("W does not list the five"). It does not produce wrong data, so it needs a retry, not a fix.
- **Captures and later tool edits.** The captures (`ff302700`) predate `ae58f4d1`, which adds only an about:blank width check, and were not rerun. The walkthrough manifest records `revision 81fcbc5a`, `dirty: true`, but `tools/w504_ev_work_walkthrough.py` and `w504_ev_work_cases.py` are unchanged from `81fcbc5a` to head. Rendered output is unaffected.
