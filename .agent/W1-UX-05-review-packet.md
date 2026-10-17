# W1-UX-05 review packet - Foundation, Readiness, SLD, Health and battery presentation

Task `tasks/W1-UX-05-foundation-health.md` (both phases). Branch `task/W1-UX-05`, base main `815888f0` (UX-01 + S7-01b merged). Frontend only. Reviewer diff: `git diff 815888f0..HEAD -- ':!.agent'`. USER_REVIEW_REQUIRED: owner sees it only in the combined W1 walkthrough; fresh independent review is the merge gate.

## Outcome

The five routes lead with a shared `HeadlineVisualCard` answering the v69 question only as strongly as the read allows. State sentence, scope (with the precise selected time) and "as of" sit outside the closed "How this was worked out" disclosure, which holds labelled exact values only. All five routes are on the W1 vocabulary set.

- **Foundation model:** "What is configured for this period?" Equipment counts by kind (`ValueBars`) and a five-setting strip (recorded / not recorded). The period words never use a positive tone: in effect now, earlier, scheduled, incomplete, no configuration.
- **Readiness:** "What needs connecting or confirming?" A step strip (equipment recorded, readings linked, gateway registered, commissioning confirmed = **Not known**) and a next-step list. "Set up to report" is `neutral` and says it does not mean connected or reporting.
- **SLD:** "How is the site connected, and which parts can report?" Bars for linked and unlinked devices; "Reporting now" draws as a hatched **not known** mark, never zero. The two catalogued SLD gap tags are kept.
- **Health:** "Which source needs attention?" Two separate lanes: contact (server receipt) and reported-fact age. The attention list links each gateway by its exact `?gateway=` URL. A gateway with fresh contact but old facts still needs attention. With no reporting gateway, no bars are drawn.
- **Battery:** the heading is "Battery condition: cannot yet be judged". The missing inputs are a step strip. Rating and charge stay separate metrics. No remaining life, warranty or replacement date is stated.
- **Refusals and empty states:** Health and battery refusals, the empty Foundation period and the unreadable store now carry the state line.
- **S7-01b Lows:**
  - L1: observed-after-receipt shows Unknown age with its reason.
  - L3: selected-gateway IDs move to the disclosure.
  - L4: `isBatteryDetail` refuses a condition other than UNKNOWN; 409 UI test added.
  - L2 is backend, see Deviations.

## Migrated call sites

- `frontend/src/sites/StoredFoundationViews.tsx:186` (model), `:526` (SLD), `:817` (Readiness). Cards are in `frontend/src/sites/foundationHeadlines.tsx`: words `:39`, `:89`; cards `:197`, `:252`, `:360`.
- `frontend/src/sites/SiteHealth.tsx`:
  - `:273` HealthHeadline
  - `:476`/`:498` selected-gateway state line and references (L3)
  - `:171`/`:176` refusal state line and references
  - `:104` L1
- `frontend/src/sites/SiteBattery.tsx:192` BatteryHeadline. Health and battery cards are in `frontend/src/sites/healthHeadlines.tsx`: words `:31`, `:76`, `:243`; cards `:142`, `:264`.
- `frontend/src/sites/healthClient.ts:213` (L4).
- `frontend/src/shell/SiteFoundationFrame.tsx:183` (empty period) and `:217` (unavailable store); `healthHref` is wired in the same file.
- Vocabulary pass (commit `c6fb4e1d`):
  - Components: `FoundationBindingsPanel.tsx`, `FoundationRevisionPanel.tsx`, `ReadinessOverview.tsx`, `SiteConfiguration.tsx`, `SiteSingleLineDiagram.tsx`, `siteViewModel.ts`.
  - New `exactValues.tsx`: `UserName` and `ExactRef` mark single values, never containers.
  - Wording: "binding" became "channel link", "digest" became "content reference", runtime/claim/simulated-run prose rewritten, type labels "Solar array" and "Supplied users".
  - Evidence-script literals updated in `tools/g01-*`, `g02-*` and `v01a-foundation-evidence.mjs`.
- Shared files: only `frontend/src/ui/primitives.css` (one additive `.foundation-headline__visuals` rule).

## Changed test assertions (all wording-only unless stated; intent kept)

`siteFoundationRevision.test.tsx`:

| Lines | Old | New |
| --- | --- | --- |
| :318, :1732 | Minimum generator runtime | Shortest generator operation |
| :325 | backend "No signal binding set..." | `NO_CHANNEL_LINKS_STATEMENT` (frontend wording shown only when `binding_set` is null) |
| :550, :621, :833, :1008, :1486 | Signal bindings | Reading-channel links |
| :585-586 | "...signal binding set" / `binding v1 (record bset-1)` | "...channel-link set" / `channel links v1 (record bset-1)` |
| :590 | Binding ID | Link reference ("not Mapping ID" kept) |
| :618 | claim readiness | what the readings can support |
| :621 | `^Binding v\d+$` | `^Channel links v\d+$` |
| :721, :743, :832, :1490, :1496 | Remove a binding | Remove a channel link |
| :724, :746 | Publish binding change | Publish channel-link change |
| :725, :736, :766-767, :900 | binding vN / Binding v / Scheduled binding period | channel links vN / Channel links v / Scheduled channel-link period |
| :1067, :1698, :1721 | Critical-load priority (three forms) | Critical service order |
| :1282-1283 | PV array / Load | Solar array / Supplied users |
| :1480, :1494 | Review or change bindings | Review or change channel links |
| :1617, :1807 | firmware "...a gateway runs." | "...a gateway has installed." (same gap ID and placement) |

`foundationScreen.test.tsx`:

| Lines | Old | New |
| --- | --- | --- |
| :442 | PV array | Solar array |
| :1174 | It claims nothing | It says nothing |

`siteConfiguration.test.tsx`:

| Lines | Old | New |
| --- | --- | --- |
| :412, :1506 | PV array | Solar array |
| :672 | device-to-signal mapping | device-to-signal link |

`siteHealthBoundary.test.tsx`: no existing assertion changed. New blocks were only added.

No fail-closed assertion was removed or loosened. "Not bound", "Unknown until bound", the pending-gateway, not-current and refusal checks, and the "no healthy" check are unchanged. A reviewer should still diff the S7-01b tests: `git diff 815888f0..HEAD -- frontend/src/sites/__tests__/siteHealthBoundary.test.tsx` shows additions plus one import line.

## New tests

- `siteFoundationRevision.test.tsx:1982`: W1 scan with closed and opened disclosures, three states per view.
- `siteFoundationRevision.test.tsx:2025`, six tests:
  - selected effective version with the selected time in scope
  - scheduled, incomplete and no-configuration periods
  - missing channel links, commissioning not known, and "Set up to report" as neutral
  - Unknown readiness, and a missing gateway as a next step
  - SLD "Reporting now" as not known, never zero, with gap tags kept
  - empty period and unavailable store
- `siteHealthBoundary.test.tsx:398`, seven tests:
  - lanes and attention, including old facts with a fresh receipt
  - KOBO-002 with no zero bars
  - selected never-received gateway (L3)
  - L1 observed-after-receipt
  - refusals (503, 403, 404)
  - battery card, missing inputs and separate facts
  - 409 `FOUNDATION_BASIS_UNAVAILABLE` and a non-UNKNOWN condition (L4)
- Non-vacuity, each injected and reverted after commit:
  - L1 revert and L4 revert: 2 failures.
  - READY_TO_REPORT tone set to `positive` and SLD reporting drawn as 0: 2 failures.
  - "binding" injected into the Readiness heading: the W1 scan fails.

## Checks (final revision `af9b6406`)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run` (full, once) | 74 files, **1755 passed**, 154 s, no timeouts |
| `node frontend/docs/architecture/check_v69_dependency_registry.cjs` | passed |
| `tools/check-all.ps1 -ExecutionPolicy Bypass` | All 9 guards passed, including the missing-claim orphan scan (31 placements) |

Backend: not run, because no backend code changed.

## Served evidence (`tools/w1-ux-05-evidence.mjs`, screenshots in `%TEMP%\w1ux05-shots`, not committed)

- **Health and battery:** `s701_health_walkthrough.py` prepare, serve, deliver and attest (`attest: ok`). Health on KOBO-001 and KOBO-002 passed 30/30; asset on KOBO-001 passed in the first pass.
- **Foundation, Readiness and SLD:** `v01a_foundation_walkthrough.py` prepare, links and serve, with the S4 producer DB present. The now and scheduled model views, Readiness now and imported, and SLD now and with a part selected all passed: 90 of 94 claims.
- **Not run:**
  - "Before any stored version": the empty period is shown on purpose with no card, so the script's card claims fail by design and no screenshot is taken. The state line is proven in jsdom (`siteFoundationRevision.test.tsx`, empty-period test).
- **Both walkthrough cases dropped afterwards** (DBs and work folders).
- **Address:** the tools print `127.0.0.1:<web>`, but Vite listens on `localhost` only. Captures used `localhost` with the same port and path.
- **390 px no-sideways-scroll claim:** the script measured at 1425 px for both widths. The inherited UX-01 script measures before the narrow override settles, so at 390 the claim is not established by measurement. The narrow screenshots (390 px wide) were inspected visually: Health at 390 shows the card stacked with no overflow, and the gateway table scrolls inside its own container.

## Known deviations

1. **S7-01b L2** (null a negative `receipt_lag_seconds` in `source_health.py:258`) is a backend change. The brief keeps this slice frontend-only, so it is not made here. The frontend already never shows a lag under 60 s, so a negative lag never renders. A backend owner should fix it.
2. **Shared helper:** `expectStateLineVisible` requires `^As of `, but the shared `asOfText(null)` returns "As of: time not recorded".
   - For refusals and the unreadable store, which have no read instant, the tests check the same visibility directly (`expectRefusedStateLine` in `siteHealthBoundary.test.tsx`).
   - The empty period uses the selected time as its bound.
   - The shared files were not edited; the UX-01 owner should reconcile them.
3. **Backend sentences:** three backend statements containing "binding" are replaced on screen by frontend wording, only when no channel-link set is in effect (`FoundationBindingsPanel.tsx` `NO_CHANNEL_LINKS_*`). Every other backend statement is shown as sent. A backend rewording is the proper fix.
4. **Two strings kept as they are:**
   - The existing green "Ready to report" verdict panel stays under the neutral Readiness card. S1 tests own its tone; the card above qualifies it.
   - The remove-a-channel-link `<option>` text shows a raw device and signal ID. An `<option>` cannot hold a marked child element.
5. **Health scope** uses the site code (`doc.site_code`), because the Health read has no display name.

## Residual risk and user-review focus

- **Readiness and gateway contact:** "Gateway registered: Done" is about registration only. A stale contact, such as `edge-kobo-001` in the v01a walkthrough, shows only in the Gateway status panel below the card. Check whether the owner wants contact summarised in the Readiness card.
- **Health lanes:** both lanes use the same bar colour. The meaning is carried in words.
- **Owner focus:** the five headlines and their honesty, at 1440 and 390.
