# Pre-flight: post-W6 W5-cold-Work (cold depth and Work)

2026-10-25. Read-only pre-flight. No code, tests, builds, captures or DB work.

**Base.** Anchors are on main `14696fda` (`AssetOpsV1-plan2`) unless marked **[W2c]**, which means branch `task/post-W6-W2-cold` @ `e2d83bd5`. W4 changes are on `task/post-W6-W4-mini` @ `a068e5c7`.

**Sources read.** The W5-cold card and cap docket in `post-W6-audit/fix-slices.md`; classification rows B14-03…B14-17 and B15-01…B15-13; ledgers `batch-14.md` and `batch-15.md`; register rows R25, R88, R101, R102 and R334–R345; `post-W6-W6-rulings.md` Q7/Q19; `post-W6-W4-rulings.md` Q1/Q2/Q8/Q10/Q14/Q17/Q21/Q22; `post-W6-W4-build-rulings.md` 2/7; `post-W6-W2-cold-rulings.md` (cross-card 3, Q13); `ui-ux-decision-guide.md`.

**Backend facts.** These come from an Explore survey of `backend/assetops_backend`. No backend change is planned.
- **Domain Action index.** Cold/EV rows are windowed on `domain_action.raised_at` (`work/adapters/postgres_domain_action_index.py:70-75`). The window allows at most 31 days and requires `from < to`. A future `to` is accepted (`work/domain_action_index.py:41,91-92`). Only a future `known_at` is refused, with 422 `INVALID_KNOWN_AT` (:380).
- **Site Work cases.** Incidents are windowed on `occurred_at` and maintenance on `created_at` (`work/adapters/postgres_work_read.py:62-73`). Maintenance rows display `occurred_at` (`work/site_index.py:263`); that mismatch is the cause of B15-06.
- **Cold Action detail.** The linked state is `links.work.request_state` (`work/domain_action_index.py:354-372`). States that can actually appear are OPEN, IN_PROGRESS, COMPLETED and CANCELLED (`work/model.py:101-107`).
  - **VERIFICATION_WINDOW is unreachable.** No transition leads into it, because `OPEN_VERIFICATION` is reserved (`model.py:112`). The K4 copy for it is therefore test-only, and the gap is structural rather than a missing producer mode.
  - **Refusal codes.** `INVALID_KNOWN_AT` (422, `work/detail.py:27-36`), `SITE_SCOPE_FORBIDDEN` (403, `work_api.py:78`) and `WORK_STORE_UNAVAILABLE` (503, `work_api.py:82`, `domain_work_api.py:89,97`).
  - **Client parsing.** `domainActionClient.ts:326` accepts any nullable string for `request_state`.

## (a) Build plan per D3 item

Units follow the card: (1) structure/routing, (2) selected data/copy, (3) refusals/long content, (4) focused tests, (5) paired recapture and cap proof.

### R334 (B14-03): `1 actions` plural on the cold-work strip
- **Change.** `coldActionCount` (`sites/coldWorkPresentation.ts:62-65`) uses the guide §4 local plural: `count === 1 ? "1 action" : \`${count} actions\``. This matches `evActionCount` (`evWorkPresentation.ts:67-69`). Update the stale U3 comment to cite R334. The loading/refusal `— actions` at `SiteWorkActions.tsx:1070-1071` stays.
- **Tests.** In `coldWorkActions.test.tsx:359`, change the expectation to `· 1 action`. Add 0/1/2 checks.
- **Recapture.** The cold-work one-Action and positive states.

### R336 (B14-07): UNKNOWN notice above populated content on cooling and cold-health
- **Change.** `COLD_DEPTH_STATE_NOTICE.UNKNOWN` (`sites/ColdCooling.tsx:33-38`) is rendered at `ColdCooling.tsx:159` and `ColdHealthDepth.tsx:124`. When `selection.state === "UNKNOWN"` and the body shows selected rows, the notice will read: **"No selected cold assessment covers this window. The rows below are accepted records only, not an assessed conclusion."**
  - "Rows" means cooling `selected_points` or context rows with `Observed`, or any health row.
  - The existing sentence stays when there are no rows.
  - Claim meaning is unchanged: there is still no assessment. This is a planned choice (b3).
- **Tests.** `coldDepth.test.tsx` and `coldHealthDepth.test.tsx`: UNKNOWN with rows, UNKNOWN without rows, and CURRENT with no notice.
- **Recapture.** The cooling and cold-health unknown cases at both widths.

### R337 (B14-08): cold-scenarios notice and Placeholder literals
- **Notice change.** `SCENARIOS_STATE_NOTICE.PENDING_RECOMPUTE` (`sites/ColdScenarios.tsx:31-36`, rendered at :303) becomes count-aware:
  - With zero scenarios: **"Underlying evidence is being reassessed. No authored scenario exists for this window."**
  - With one or more: keep "…the authored scenario remains separate", pluralised for two or more ("…authored scenarios remain separate").
- **Subtitle change.** `SCENARIOS_PANEL_SUBTITLE` "Placeholder · to be designed with the owner" (:24, used at :304) is false copy on a built page. Under the register's D4 rule (existing R25 row), replace it with **"Labelled what-ifs authored for this site; never measured results."** Remove `Placeholder` from the file header comment (:5) so the literal scan is clean.
- **Register.** Update the R25 row text in place. No new number is needed.
- **Tests.** `coldScenarios.test.tsx`: pending with 0, 1 and 2 scenarios; a subtitle literal; and an absence assertion for `Placeholder` made after `settledScreen`.
- **Recapture.** All cold-scenarios cases. The populated authored state stays a producer gap (fix-slices producer table, B14-16) and is covered by selected-DTO tests.

### R338 (B14-09, plus merged B15-06): Site Work default window, empty copy and membership line
- **Default window.** `defaultWorkWindow` (`sites/workClient.ts:183-189`) becomes `[today−6d 00:00Z, tomorrow 00:00Z)`, seven UTC days including today, matching W6 Q7.
  - It feeds `domainWorkScope` (`shell/SiteAnalyticsFrames.tsx:1937-1942`; cold/EV Actions) and `workCasesScope` (:2203-2208; every Site's cases, including mini).
  - Update the comments at :1932-1936 and :2196-2201. Reach and basis go to **Q1**.
- **Empty copy.** `COLD_WORK_EMPTY` (`coldWorkPresentation.ts:22`) becomes `["No actions at this site", "No Action was raised here in the selected window."]` (guide §3; the current "has been raised here yet" is false). `EV_WORK_EMPTY` (`evWorkPresentation.ts:24`) is left to W5-EV-Work, as in the Q1 default.
- **Membership line.** One 12 px muted line under the cold/EV `DomainWorkWindow` (`SiteWorkActions.tsx:767ff`; mounted at SAF ~2066 for Actions and ~2269 for cases):
  - Actions: **"Listed by the time each Action was raised."**
  - Incidents: **"Listed by incident start time."**
  - Maintenance: **"Listed by the time each request was opened."**
  - The Incidents and Maintenance lines repeat W6 Q7 verbatim. This is the B15-06 fix; the copy goes to **Q1**.
- **Tests.**
  - `coldWorkActions.test.tsx:417,632` and `evWorkActions.test.tsx:385`, which assert via `defaultWorkWindow()`, still hold. Add a pinned-clock test that a row raised today is inside the default window.
  - `siteWorkCases.test.tsx:440` gets a today-membership case.
  - Add a zero-Action empty-copy test (`coldWorkActions.test.tsx:486`), an invalid-window test (reversed range, kept selection, no new read) and an explicit-window preservation test.
- **Recapture.** The cold-work current-day default and zero cases. Add regression pairs for the cold-work-incidents/maintenance defaults, ev-work, ev-work-* and the mini sitework-incidents/maintenance defaults, because the shared helper reaches them.

### R339 (B14-10): Site main tabs keep `from`/`to`/`known_at` on cooling, cold-health, cold-scenarios and cold-work
- **Mechanism.** W2-cold's `coldTabSearch(site, params)` ([W2c] `shell/coldSiteRoutes.tsx:23-29`) through the W2-EV `OperatorSiteTabs` `search` override. W5-cold rebases onto W2-cold first.
- **Cooling.** Mounted inside `ColdPerformanceFrame`. It gets `search={coldWindowSearch(window)}` from W2-cold ([W2c] SAF:292). Verify only.
- **Cold-health.** Add `search={coldTabSearch(site, params)}` at `shell/SiteHealthFrames.tsx:71`; the frame needs `useSearchParams`. Also add it to the Health mounts at :122 and :170 if they serve COLDCHAIN; they are a no-op for other Site types.
- **Cold-scenarios.** Add it at the SAF Financials > Scenarios mount ([W2c] :1316; main ~:1301).
- **Cold-work.** Add it at the SAF Work mounts (main :2002 and :2069 for Actions, :2269 for cases). Cases also serve cold-work-incidents/maintenance, which is acceptable and inherits the change.
- **Out of scope.** The cold-action shell has no Site tab row. Ruled K4/EV-14 keeps `known_at` only for cold, so there is no change there.
- **Tests.** Extend `coldRoutes.test.tsx` or `operatorSiteTabs.test.tsx`: each of the four screens' tab hrefs carries the URL triple; the default (no-query) Work URL yields bare tabs; mini and EV are unchanged.
- **Recapture.** All indexed pairs for the four screens, plus one tab-href probe per screen.

### R344 (B15-10): cold-action Related activity copy for exact linked states (K4)
- **Change.** In `relatedSentence` (`sites/DomainActionVerification.tsx:85-100`), add two branches that apply only to a linked case:
  - `VERIFICATION_WINDOW` with `record_id !== null` → "Work was recorded; verification is open and no outcome is established."
  - `CANCELLED` → "The linked request was cancelled; no completed work or verified outcome is established."
  - Both use new exported constants beside `COLD_RELATED_NOT_LINKED` (:24), with kinds `verification-window` and `cancelled`.
  - Any other combination keeps the existing fallback.
- **Reach.** The function is shared, so EV inherits the copy. Serialized ownership of `DomainActionVerification.tsx` goes W5-cold first, then W5-EV verifies; that is ordering only.
- **Tests.** `domainActionVerification.test.tsx`: selected-DTO cases for VERIFICATION_WINDOW with and without a record, CANCELLED with and without a record, OPEN/IN_PROGRESS/COMPLETED regressions, and unlinked.
- **Capture gap.** Record it in the packet. CANCELLED-linked has no producer mode. VERIFICATION_WINDOW is unreachable in backend state today (`model.py:112`).

### Carried, owned here by W4 rulings Q1/Q10 (no new D3 ID)
- **B14-04 cold tones (closes the cold instance of R309).** Use W4 Q2's shared badge tokens after rebasing onto W4. In `ColdCooling.tsx:157`, map `recovery_state` LIMITED/CONTRADICTORY → amber and UNKNOWN → neutral, and Confidence Low → amber, Unknown → neutral. The context Match `Not established` at :212 becomes amber; the mock shows Limited and Not excluded as amber. Health `NEEDS_INVESTIGATION` amber already exists (`ColdHealthDepth.tsx:131-136`). Scenario pills Defined/Historical stay neutral because they are fixed labels.
  - **Cold-work strip.** Apply the mock tone only where it encodes a stored status. Confirm the exact v69 strip element against the B14-04 pairs at build time.
  - **Contrast and tests.** Check 4.5:1 chip text contrast. Add tone tests.
- **B15-04 cold-action refusal (cites R322).**
  - **Location correction.** The mount is `DomainActionShell` in `shell/SiteAnalyticsFrames.tsx:1563-1581`, which prints `p.unavailable`, the raw `state.message` and Retry for every refusal. It is not in `SiteWorkActions.tsx` as W4 Q10 states.
  - **Copy by code.** Add a cold presentation map (`coldWorkPresentation.ts`, `COLD_ACTION_PRESENTATION`):
    - `INVALID_KNOWN_AT` → "Choose a valid evidence cutoff."
    - `SITE_SCOPE_FORBIDDEN` → "You do not have access to this site."
    - `WORK_STORE_UNAVAILABLE` → "Cold work is unavailable right now. Try again."
    - Unknown → "The attempt was refused." (guide §3)
  - **Rules.** Retry only for 503 and unreachable. Never print raw `known_at` or the Site code. `role="alert"`. EV keeps its ruling-44 copy through its own presentation.
  - **Tests.** Component tests for 422, 403, 503, unknown and unreachable.
  - **Recapture.** The cold-action forbidden, unavailable and bad-cutoff cases.

**Recapture total.** All 116 indexed pairs for `cold-work`, `cooling`, `cold-health`, `cold-scenarios` and `cold-action` at 1440 and 390, plus the R338 regression pairs above. After W4 lands, add one 390 cold Site tab row with the R453 label as regression. Record the SHA, producer, pinned clock and gaps.

## (b) Planned guide-covered choices
1. **Plural helper, local** (§4): `count === 1` in `coldActionCount`, checked at 0, 1 and 2. No shared module.
2. **Empty-state copy** (§3): `No Action was raised here in the selected window.` with `role="status"`, unchanged heading.
3. **R336 notice wording** (§4/§5, small copy with unchanged meaning): it still states there is no assessment, and adds that the rows are records only.
4. **R337 count-aware notice and D4 subtitle replacement under the existing R25** (§5 D4 rule). No new register number.
5. **Tone mapping from stored enums only** (§4; W4 Q2): amber for limited/contradictory/not-established, neutral for unknown and fixed labels. The word always accompanies the colour.
6. **Refusal copy by exact code** (§3; W4 Q10 copy): no Reload on 422/403; Retry kept for 503 and unreachable; one `role="alert"`.
7. **Membership line** as a 12 px muted line under the Window control (§4 hierarchy; W6 Q7 pattern). The copy itself is part of Q1.
8. **Tab search override reuse** (§2 navigation; W2-cold cross-card 3). No new mechanism.
9. **Caps.**
   - Ruled caps apply as written: cold-work Actions 550/800; cooling Recovery curves 390 → 800; cold-health Condition and evidence 1440 → 400; cold-action Related activity 390 → 350.
   - Unruled sides use the guide §1 formula `50 × ceil(peak × 1.15 / 50)` from the final-SHA worst closed peak, with the calculation recorded. These are cold-health 390, cold-action 1440, cooling 1440, Context normalization, Declared outcome criteria and cold-scenarios Financial scenarios at both widths.
   - The stress fixture is five rows with every variable field at 160 characters, as a capture-only DOM clone where producers cannot make it. All-disclosures-open is exempt.
   - On a miss: wrap, then page, then a labelled inner scroll region. Escalate only if a ruled cap is still exceeded.
10. **Tests settle with `settledScreen`**: selected-DTO tests for unproducible states, with gaps named in the packet (Q-free test approach, §5).

## (c) Escalation-only Architect questions (2)

**Q1 — R338 reach and membership copy (cross-card scope and product meaning).** `defaultWorkWindow` is shared. Changing it moves the default for cold/EV Actions and for every Site's Work cases, including mini (W4 surface, Site-local form after W4 Q8/build-7). The membership line states the backend listing basis.

*Recommended default:*
- (i) Change the shared helper to `[today−6d 00:00Z, tomorrow 00:00Z)` UTC for all Site Work, matching W6 Q7. Add regression captures for EV and mini.
- (ii) Add the membership line on the cold/EV `DomainWorkWindow` only: Actions "Listed by the time each Action was raised.", plus the W6 Q7 Incidents and Maintenance lines verbatim.
- (iii) The mini cases form gets no line, and `EV_WORK_EMPTY` is aligned by W5-EV-Work.

*Alternatives:*
- (b) A cold-only default via a domain-specific helper, leaving EV and mini excluding today.
- (c) Site-local seven calendar days for the mini cases form, matching its Site-local inputs, with UTC for cold/EV, whose controls are UTC-dated per R77/R88.

**Q2 — Serialized shared files and W4 Q10 anchor (cross-card ownership).** The card's file list omits `shell/SiteAnalyticsFrames.tsx` and `shell/SiteHealthFrames.tsx`. R338 (`domainWorkScope`/`workCasesScope`), R339 (Scenarios and Work tab mounts) and B15-04 (the `DomainActionShell` refusal at :1563-1581, not `SiteWorkActions.tsx` as W4 Q10 says) all live there. B14-04 also needs W4's tokens.

*Recommended default:* W5-cold owns only those named cold hunks. It branches or rebases after both W2-cold and W4-mini merge, keeping the serial order shell → … → W2-cold → W4 → W5-cold for SAF. It reads W4 Q10's file reference as `SiteAnalyticsFrames.tsx` DomainActionShell, with EV copy untouched. The W5-EV-Work SAF and `DomainActionVerification.tsx` edits follow W5-cold.

## (d) Register numbering
Likely rows:
- R25 updated in place (no number).
- A possible D1 if a mock tone cannot be shown truthfully. For example, the mock shows `Matched` green, but the app never establishes a match, so it can never show green.
- A possible D2 for the Site Work membership line, if the Architect wants it registered. W6 Q7's global lines were not registered.
- A spare.

**Proposed block:** 10 numbers, **R460–R469**. The next free number is after W4's R450–R459, so W5-EV-Work can take R470+. The coordinator should confirm the range is disjoint at rebase. Add only used rows.
