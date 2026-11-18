# W5-02b part 1 (K2a + K2b) independent review: cold Site Action list and domain Action shell

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review3`, branch
`task/W5-02b-cold-site-screens`, head `b04353e3`, diff `1bfd74b2..HEAD` (55 files, backend untouched).
Authority: `.agent/W5-02-build-spec.md` "Shared Site UI and mock slots", "K2a/K2b exact Site and mock ruling" (U1-U4),
"W5-02 Site-screens pre-flight ruling (2026-10-23)"; `tasks/W5-02-cold-work.md`; register `.agent/mock-departure-register.md`.

## Verdict: REVISE

The client, the presentation module, the routing and the producer are sound, and the evidence is honest about what
it could not prove. Two High findings block merge. Both are visible 1440 layout departures from v69 that the capture
claims did not catch. The more serious is H1: at desktop width the cold table never wraps, so the K2b long-text proof
is not what it appears to be. One Medium is an unbuilt ruled item (Q6) that needs an Architect re-ruling before merge.

Counts: **High 2, Medium 2, Low 6.** There are 19 Architect items below.

## Checks run (this review, same head b04353e3)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| Targeted vitest: coldWorkActions, siteWorkActions, siteWorkCases, w1f4ChangesWorkStructure, siteAction, siteActionVerification, w1f4ActionStructure, w1f4VerificationStructure, operatorSiteTabs, operatorRouteFrames, siteDetailRoute, s404SiteFindingIndex | 12 files, 324 passed |
| Full vitest `--minWorkers=1 --maxWorkers=2` | **119 files, 2796 passed, 0 failed**, 257 s (vitest ran under this sandbox; the brief's esbuild denial did not occur) |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | both passed |
| `tools/check-all.ps1` | All 11 guards passed |
| Focused Postgres `test_w502_domain_intent_api.py`, `test_w502_domain_action_index_api.py`, `test_w502_domain_action_index_postgres.py`, `-n 4`, private `assetops_w502rv3_test` (dropped afterwards) | 9 passed. The backend is unchanged from `1bfd74b2`, so for the rest of the w502 suite I rely on the implementer's 34/34 at that revision |
| `tools/layout-evidence.mjs` / `w502-cold-work-evidence.mjs` | not run (needs the seven producer APIs, Vite and Chrome). I reviewed the 28 PNGs and the README instead |
| `npm.cmd run build` | not run by me; the implementer reports it green at `75abbaf3` |

**s404SiteFindingIndex flake:** it is not related to this slice. The file is untouched, it passed in both of my runs
(alone and in the full suite), and the failure mode is a race between the date-input change and the
default-window re-render. The only shared file in this slice is `test/settled.ts`, which gains one more alternative in
its loading regex and cannot change s404's timing.

## Findings

### High

**H1. At desktop width the cold Actions table never wraps. Long text is clipped in the preview, and the opened full text spills out of its cell.**
- Where: `frontend/src/sites/w1f4-changes-work.css:14-16` (`.w1f4-changes-work .panel .data-table td { white-space: nowrap; }`, specificity 0,3,1) overrides the slice's `.cold-work-actions .data-table td { white-space: normal; overflow-wrap: anywhere; }` at `:234` (specificity 0,2,1). The cold wrapper carries both classes (`SiteWorkActions.tsx`, `className="w1f4-changes-work cold-work-actions"`). The only reset is the W1 `@media (max-width: 760px)` rule at `:71-75`, so 390 wraps and 1440 does not.
- Evidence: `w502b-desktop-worstcase-expanded.png` shows each 160-code-point title as a single line, cut off at the 340 px cell edge (`…long title proof xxx`). The two-line preview is a one-line horizontal clip under `.work-cases-clamp`'s `overflow:hidden`. In `w502b-desktop-worstcase-disclosure.png` the opened `Read full text` body runs on one line from x≈279 to x≈1140, past the Action cell and under the Source, Owner and Due columns. At 390 (`w502b-narrow-worstcase-disclosure.png`) it wraps correctly.
- Why it matters: U4 and the spec say title, owner and source "wrap within their cells, with full text in a disclosure … no clipped status". This is K2b's core deliverable, and none of the 315 capture claims tests it. `w502-cold-work-evidence.mjs` checks one-line codes and summaries but not cell containment. It also invalidates the F1 numbers: once desktop rows really wrap to two lines, the worst-case panel will be taller than the measured 447 px.
- Fix: raise the cold rule's specificity (for example `.w1f4-changes-work.cold-work-actions .panel .data-table td { white-space: normal; }`, keeping the nowrap exceptions for codes, Due and State). In the evidence tool, add a containment claim for each visible row and for the open disclosure: `cell.scrollWidth <= cell.clientWidth + 1`, and preview lines ≤ 2 with no horizontal clip. Then recapture 1440 and re-measure F1.

**H2. Three unlabelled 1440/390 mock layout departures on the cold Work and Action pages.**
None has a D1–D6 label or a register row.
1. **The sticky header cell loses the header background.**
   - Where: `w1f4-changes-work.css:222-227` sets `th:first-child` and `td:first-child` to `background: var(--surface-raised)`. That turns the `ACTION` header white while the rest of the v69 header row stays sunken grey.
   - Evidence: visible in every row capture at both widths. The merged W4 precedent `w4-work-cases.css:135-146` restores the header colour (`th:first-child { background:#f8fafd }`).
2. **The notice icon sits on its own line above the text.**
   - Where: `SiteWorkActions.tsx:768` and `:812`, and `SiteAnalyticsFrames.tsx:1452` and `:1479`. They put `<RailIcon/><p>` inside `Notice` with no flex rule, so each notice is 66 px against the mock's 42 px, which has the icon inline (`mockups/v69/index.html:180`, preview `cold-work-incidents.png`).
   - Merged precedent: `coldScenarios.css:106-107` (`display:flex; gap:10px; align-items:flex-start`).
   - Being within the 110 px cap does not excuse the mismatch.
3. **`Open site` renders as a bare text link.**
   - Where: `SiteAnalyticsFrames.tsx:1417`. The v69 shell renders it as `btn(...)`, which is `class="button"` (`index.html:178`, `:1138`).
   - The W1 Alternatives frame uses the same bare-link form. Either use the mock's secondary `button` class, or have the Architect label it with a register row.
- Fix: items 1 and 2 are small CSS changes scoped to `.cold-work-actions` and the domain Action shell. Item 3 needs one class or an Architect label. Recapture after the fix.

### Medium

**M1. Ruled but unbuilt: the cold range control (P-K2a-39) and the topbar visibility assertions (U2). This is Q6.**
- Where: `SiteAnalyticsFrames.tsx` `coldWorkScope`. With the W1 form hidden on cold (U3), no control writes `from`/`to`. A cold user cannot leave the seven-day default except by editing the URL. Mini-grid keeps its form.
- The builder's diagnosis is correct. `OperatorShellLayout.tsx` has no topbar, Site switch or range picker, so the ruled "existing topbar date-range slot" does not exist. The builder was right not to invent shared shell plumbing.
- Why it matters: this is an observable acceptance gap against a ruled item, and the mock shows the range picker (`index.html:1138`).
- Fix: the Architect re-rules where the control goes (new shell topbar = shared plumbing and its own unit, or an in-page control labelled D-code) and what U2 asserts instead. Merge waits for that ruling. Building it is not a reviewer call.

**M2. The producer does not give the Incident the ruled source-window `occurred_at`. It affects K3b, and the tool is K2a-owned. This is Q4.**
- Where: `tools/w502_cold_work_walkthrough.py`, the BUILD `incident(...)` and `record(...)` calls. They use the W4 test-helper defaults (DB time minus 1 h / 20 min), not `[D+16h,D+17h)`. The Incident also gets no `finding_links`.
- Why it matters: the K3b card requires the capture of "the Site-local `Window` produced by `[D+16h,D+17h)` at `Africa/Addis_Ababa`". The mock Incident row shows linked findings `F-118 · F-119`. The shared producer would therefore give K3b the wrong Window and an empty Linked findings cell.
- It does not affect the K2 captures, and it is graded Medium only because it is K2a's tool.
- Fix: pass `occurred_at` inside the shifted window and the selected Finding link(s) to the INC. The Architect confirms the INC links (Architect item 4).

### Low

- **L1. The sticky column duplicates an existing primitive.**
  - Where: `w1f4-changes-work.css:219-232` re-implements what `DataTable stickyFirstColumn` already provides (`ui/DataTable.tsx:51-58`, `primitives.css:5405-5415`, merged with W5-03a E2 into this base). The pre-flight premise "DataTable has no sticky prop" (P-K2a-44) is now stale.
  - Prefer the prop and fix the header colour once (H2.1). This is a quality preference, not an acceptance gap.
- **L2. The detail validator does not check `links.work` keys.**
  - Where: `domainActionClient.ts:294`. It accepts any object as `links.work`. K1b defines exactly `{case_id,case_code,case_title,request_state,record_id,label,href}`, all present and nullable.
  - K4a renders it, so tighten the check there at the latest.
- **L3. A domain 404 on a bare W1 address falls back to W1.**
  - Where: `SiteAnalyticsFrames.tsx:1535`. On a cold Site a bare or legacy address probes the domain read, and any non-loaded result, including 403/503, renders W1.
  - This is the only way to satisfy U1's redirect. It still deserves an Architect confirmation against "never turn … a domain 404 into a W1 fallback" (Q8).
  - A domain-store outage also silently shows the W1 page for a domain ID that cannot be read. That is a residual risk.
- **L4. The 503 capture is honest but incomplete (Q17/F5).**
  - The README records it as FAIL with its cause, not as a pass. That is correct.
  - The spec's "if a mode cannot be produced … mark the browser capture unavailable" covers it.
  - Option (b) is cheap and still a real server failure: give only the domain-work router in `serve_entry.py` an unreachable URL while the Site read stays healthy. I recommend it.
- **L5. Q2 (Site-access check on domain-work reads): not a gap introduced by this slice.**
  - In `main.py:563-567` the domain-work `WorkGate` uses the default `development_access` (`finding_api.py:46-47` returns `None`).
  - Every other product read router does the same: W4 `build_work_router` (`:557-561`), estate (`:545-556`), global work (`:571-575`). The product has no authentication yet.
  - `create_app` exposes `domain_work_principal` but no `domain_work_access` seam, unlike `ev_access`. When access control lands, the domain-work and W4 work routers both need one.
  - The tool-local `serve_entry.py` route-prepend is acceptable as capture-only scaffolding. It sits outside the product app and edits no shared plumbing.
- **L6. The vocabulary-scan exclusion (Q14) is narrow and acceptable as an interim.**
  - The violation `text` is a single text node (`test/productVocabulary.ts:271-280`), so the filter in `coldWorkActions.test.tsx:275-279` sets aside only the server-sourced criterion literal, not a whole subtree.
  - The durable answer is a registry `cold-work` gloss (Architect item 14).

## Mock fidelity notes (no finding)

- Strip, six columns, the `1 actions` literal, the empty icon/h3/body, the domain notice first sentence (R01), the M4 strip (R02), the `Finding {id8}` plain source plus revision disclosure (R65/R66), the `Due dates are not yet set` subtitle (R67) and the interim Sites rail (R69) all match their rulings and register rows.
- The adapted cold banner is absent. That is correct for K2: P-K3a-6 gives it to K3a (Work) and K4a (Action).
- The narrow 503 capture shows a very tall dark shell header above `Site unavailable`. It comes from the existing shell/SiteScoped refusal layout, not from this slice. It is a residual risk for the W1 conclusion pass.

## Builder judgment calls, Q1–Q17

| Q | Does the spec decide? | Builder vs spec | Disposition |
|---|---|---|---|
| Q1 `GEN-CR-01` vs `generator-1` | Yes ("returned … `GEN-CR-01` ID"), but on a false premise: COLD-LAB-001 registers `generator-1` | Used the returned ID, never a free code: correct | Architect: fix the spec literal; decide the K3a label expectation |
| Q2 403 mechanism / access seam | P-G-5 decides "separate ungranted principal"; no seam is named | Tool-local gate; shared plumbing untouched | L5; Architect item on the future seam |
| Q3 Finding per mode | No | Reasonable (matches the existing Postgres tests) | Architect confirm |
| Q4 INC links / `occurred_at` | Partly: K3b requires the source-window Window | Diverges | M2 |
| Q5 `raised_at` | No ordering rule beyond K1a validation | Consistent with K1a | Architect confirm |
| Q6 topbar range / Site switch | Yes (P-K2a-39, U2), on a false premise | Unbuilt | M1 |
| Q7 subtitle field | Yes (stored subtitle, else fallback); no stored field exists | Fallback always: correct reading | Architect: confirm, or name a Foundation field |
| Q8 W1 ID on cold `/verification`; refused probe on bare | Later ruling decides no W1 fallback on `/verification`; bare-address 404 behaviour undecided | Matches the later ruling | L3; Architect confirm |
| Q9 refusal shape | Yes (`{detail:{code,message},intent:null,results:null}`), but merged `domain_work_api.py:98-119` nests the pair in `detail` | Accepts both and pins the merged shape: acceptable | Architect: correct the spec text |
| Q10 placeholder heading | P-K2a-45 defers the headings to K4a; U2 says "mock panel" | Untitled panel plus notice: consistent | Architect confirm |
| Q11 unknown-count literal | U3 decides "unknown count", gives no literal | `— actions` matches the subtab `—` | Architect confirm |
| Q12 revision disclosure summary | No literal | `Finding version` | Architect supply/confirm |
| Q13 preview / `Disclosure` | Yes (shared `Disclosure` = native details; no hidden/clip on sticky styling) | Matches; but see H1, where the preview clip is now a real horizontal clip at 1440 | Architect confirm after the H1 fix |
| Q14 vocabulary "runs" | No | Narrow scoped exception | L6; Architect/registry owner |
| Q15 `expectV69Panels` with a leading notice | No | Direct position assertions on non-current states | Architect: admit `[data-cold-work-currentness]` in `test/panelStructure.ts` or confirm |
| Q16 notice tones; fold removal | Tones: no. Fold: yes (U3 removes `Show the first 4`) | Fold matches the spec; tones follow the W4 strip | Architect: confirm the tones |
| Q17 503 capture | Yes (invalid-DB process; else mark unavailable) | Marked unproven, honestly | L4; Architect choose option (a) or (b) |

## Open items (handoff)

- **F1, 447 vs 440 px:** this cannot be judged yet. Once H1 is fixed, desktop rows will wrap to two lines and the panel will grow further. The Architect needs post-fix numbers to decide between the cap, the fold and a disclosure-only preview.
- **Q6:** see M1.
- **Q17/F5:** see L4.
- **Q2:** see L5.

## Items for the Architect

1. Q6/M1: rule where the cold range control lives (new shell topbar = shared plumbing and its own unit, or an in-page control with a D-label) and what U2 asserts instead of "topbar Site switch, range picker remain visible".
2. F1: after the H1 fix and recapture, rule the 1440 worst-case panel cap (raise it, or fold earlier, or keep only one preview line plus the disclosure).
3. Q17: choose (a) the Site-level 503 capture plus the jsdom test, or (b) a domain-work-only unreachable DB in `serve_entry.py`. The reviewer recommends (b).
4. Q4/M2: confirm the INC carries the selected Finding link(s) (the mock shows `F-118 · F-119`) and an `occurred_at` inside `[D+16h,D+17h)` for K3b.
5. Q1: correct the spec's `GEN-CR-01` to the Foundation's `generator-1`, or rule a display mapping. State K3a's expected asset label.
6. Q2/L5: record that no product read route has Site access yet, and name the future `domain_work_access` (and W4 work) seam in `create_app`.
7. Q9: correct the spec's refusal shape to the merged `{detail:{code,message,intent:null,results:null}}`.
8. Q8/L3: confirm a W1 ID on cold `/verification` shows not-found, and confirm that a refused or 404 domain probe on a bare address renders W1.
9. Q7: confirm the fallback subtitle is always shown (no stored subtitle field), or name the field.
10. Q10: confirm the untitled placeholder panel.
11. Q11: confirm `— actions`.
12. Q12: supply or confirm the `Finding version` summary literal (it is also used on the Action status strip).
13. Q13: confirm reuse of `.work-cases-clamp` (its `overflow:hidden`) for the two-line preview after H1.
14. Q14: add a `cold-work` gloss for the server criterion summary in the vocabulary registry, or keep the scoped exception.
15. Q15: whether `[data-cold-work-currentness]` becomes an admitted leading pattern in `test/panelStructure.ts`.
16. Q16: confirm the notice tones (blue for HISTORICAL/UNKNOWN, amber for PENDING_RECOMPUTE/STALE_SOURCE).
17. Q3/Q5: confirm the per-mode Finding mechanism and the `raised_at` placement between K0 and DB time.
18. H2.3 (reviewer): `Open site` as the mock secondary `button` class, or a D-label and register row for the bare-link form. It also applies to the existing W1 Alternatives precedent.
19. L1 (reviewer): P-K2a-44's premise "DataTable has no sticky prop" is stale. Allow K2a/K3a to use `stickyFirstColumn`.

## Residual risk not named in the packet

- The capture claims (315) have no cell-containment or horizontal-clip claim, so H1 passed every claim. The K3b/K4b captures reuse this tool and would have the same blind spot.
- Every W1 Action page on a cold Site now makes one domain read first, and an outage of that read shows W1 for a domain ID (L3).
- The worst-case panel height at 1440 is currently understated (H1 → F1).
