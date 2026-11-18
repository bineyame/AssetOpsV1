# V-01a round 3 — independent review

Reviewer: a fresh Claude reviewer (did not author the work), 2026-10-12.
Target: `task/V-01a-foundation-visual`, `git diff b5a7a75..HEAD` (`5300c2a`, `8daa97a`, `a6725d5`, `0f46fd8`, `459e42a`).
Spec: `.agent/architect-V-01a-round3-answers.md` sections 1-4, fix list and Addendum; `D-2026-10-12-v01a-round3-readiness-and-organization`; owner feedback `.agent/owner-V-01a-round2-feedback-2026-10-12.md`; task `tasks/V-01a-foundation-visual-fidelity.md`; packet "Round 3".

## Verdict

**Accept, with carry findings.** No blocking finding. V-01a is **ready for the owner's visual check**. Owner visual acceptance is not given and is not written anywhere in the diff. Any acceptance of `sites:1`, `foundation:2-3`, `readiness:1-3` or `sld:1-2` remains conditional on the named data gaps (Addendum).

## Checks I ran (my results, not the packet's)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `pytest backend/tests -q` | 1771 passed, 127 skipped |
| `npm.cmd test` (frontend) | **ran in this session**: 55 files, 1362 passed. That includes the Dispatch, Finding, Site Evidence, Lab and history suites. The known esbuild sandbox failure did not occur this time. |
| `npm.cmd run build` | exit 0 (chunk-size warning only) |
| `npx.cmd tsc --noEmit` | exit 0 |
| `tools/v01a-foundation-evidence.mjs` on my own copy | **185/185**. Finding detail NOT RUN: the store has no Finding, which is the same precondition as before. |
| `tools/layout-evidence.mjs http://localhost:5390 KOBO-001` | **199 PASS, 0 FAIL**, then the known Lab precondition (`fuel-loss-event/run-setup` submit still disabled after 10 s). Lab sections after that point, including T025d, are unverified. |

Servers: API 8890/8891 and Vite 5390/5391, with databases `assetops_v01arvw3` and `assetops_v01arvw3empty` and work tree `v01a-round3-review`. All are stopped, the ports are confirmed free, the databases are dropped and the tree is removed. No owner server, port, database or `var/` was touched. The working tree is unchanged apart from the pre-existing `.agent/coordinator-handoff.md` modification and this file.

## What I verified

- **Cards** (`ReadinessOverview.tsx:52-117`). Each card is derived only from typed `configuration_gaps` codes, mapped exactly to the Architect's table. A card is green only when its category has no gap code. It shows Unknown (neutral) only on `NO_EFFECTIVE_REVISION`, which the backend emits for that case (`foundation_content.py:232`). The green notes say "declared, not field-verified" and "Configuration, not operating results". There is no healthy or commissioned wording.
- **Table** (`:153-292`). The columns are Area / Declared / Confirmed / What is needed / Next step. There are six rows. Confirmed is a neutral "Not recorded" on every row, and every row also lists "Commissioning confirmation not recorded". The Declared values are real, for example "Reserve 45%", "Binding v12; 5 of 5 required roles configured" and "Gateway registered (edge-kobo-001); 8 sources registered". Next-step links go only to existing routes. Commissioning shows the plain "No commissioning record available". There is no Owner column and no mock value.
- **Gateway** (`:296-501`).
  - I read `gateway_api.py:93-109` and `gateway_access.py:289-345`. The client's type guard and fields match the real document.
  - `UNKNOWN` is produced only when no diagnostic has been received, so "Contact unknown — no central diagnostic received" is true.
  - CURRENT is computed as `<= 2 × cadence`, which matches "within two reporting intervals".
  - A 404 or 503 response renders "Gateway contact unavailable" with registration only, and never falls back to Online.
  - Registration and contact are separate facts. The badges are neutral.
  - `read_at` and the last contact are labelled with the server clock.
  - The period note distinguishes CURRENT from PAST/scheduled ("it did not occur in that period").
  - The Addendum's not-available line and "Device connection not established here." are present.
  - Queue, clock, disk and per-source fields are under Advanced, labelled "reported" or "not proof of a connected device".
  - My copy's real read answered STALE, and the UI rendered it correctly.
- **Advanced details.** The Readiness, Foundation, SLD, part-channel and gateway disclosures are labelled "Advanced details — …". They hold the records that were previously in panels: role coverage, the binding form, sources, the acquisition snapshot, record IDs/digests, the control assumptions table and the full channel table. No audit content was dropped. "Review or change bindings" opens the disclosure and focuses the form select. Missing required roles stay visible in the verdict panel's "What is missing" and in the table.
- **Site model** (`StoredFoundationViews.tsx:396-467`).
  - It shows "First in critical-load priority: Health clinic" from the typed control, with the note "An order, not a service designation".
  - Configured loads come from stored LOAD components.
  - It shows "Productive-use designation: Not declared" and "Financial assumptions not available here".
  - The control links match the mock's positions (`index.html:421`): reserve → Published configuration, start/stop → "No proposed-change record here", runtime → "No linked constraint evidence", source → "Open Dispatch; choose an assessed day" with its scope note. Dispatch is the only real link. No mock values were copied.
- **Part strip.**
  - The global Selected part panel is removed.
  - The strip is inside the topology panel and the SLD panel, below the drawing and outside `.sld__scroll`. It is an `aria-live="polite"` region referenced by `aria-controls` from the topology-card and parts-table choices.
  - Clear returns focus to the part's choice. `component=` and `at` semantics are unchanged.
  - The Readiness chip links back to Site model and SLD.
  - At 390 px the strip is inside the viewport (screenshot `app-sld-selected-narrow`).
- **Sites.** There is one Operating view cell, "Not available yet" plus a secondary line. The aggregate/setup note is shown once. At 390 px the cell is in the first viewport.
- **Layout-evidence expectation changes (`0f46fd8`).** These are legitimate. The header count went from 5 to 6 because the Operating view column was added. "Review or change bindings" is excluded from the action count by a narrow `data-review-bindings` selector, the same way `.part-choice` is excluded; Publish binding change is still counted. Neither change weakens a check for anything else.
- **Conditional-acceptance record** (packet "Round 3"). There is a row for each of the four panels with the five columns. Column 5 says "pending". The ledger and registry are not edited. No owner acceptance is written, and the `readiness:2#a/2#b/3#a` registry portions are not marked delivered.

## Findings

All of the findings below are **carry**: none blocks the owner's visual check. None is an acceptance gap against the Architect's exact text, except C1, which is an omission from the packet's deviations.

- **C1 — Readiness table at 390 px hides "What is needed" and "Next step" behind a sideways scroll.**
  - Where: `ReadinessOverview.tsx:259` (`DataTable`); screenshot `app-readiness-gateway-unknown-narrow`.
  - What: on a phone only Area / Declared / Confirmed are visible. The gap list and the "Review or change bindings" action need a sideways scroll in the table's own region. This is the plain first layer the owner asked for.
  - Why it matters: the packet's "Known deviations" names only the Sites table scroll, not this one. Missing roles do remain visible in the verdict panel, so no gap is hidden outright.
  - Fix: either stack the rows at narrow widths, or record this as a known deviation for the owner to judge.
- **C2 — The verdict statement still says "operational status is not assessed here" directly above the Gateway status panel.**
  - Where: backend `binding_service.py:83-88` (`READINESS_STATEMENT`), rendered at `FoundationBindingsPanel.tsx:183`.
  - What: round 3 removed `foundation.evidence.statement` for exactly this tension ("Known deviations") but kept this one. Gateway contact is not condition, so the sentence is defensible, but a reader may see a contradiction.
  - Fix: adjust the copy, for example "equipment condition is not assessed here". Either the backend constant needs reviewed copy, or the frontend replaces it as it did for the evidence statement.
- **C3 — Screenshot name clash.**
  - Where: `tools/v01a-foundation-evidence.mjs`.
  - What: the in-effect-now period note and the CURRENT contact variant both write `app-readiness-gateway-current`. The in-effect-now note therefore has no retained screenshot, only a passing claim. The packet discloses this.
  - Fix: rename one of the files, for example `app-readiness-gateway-period-now`.
- **C4 — SLD drawing part choices have no `aria-controls` to the strip.**
  - Where: `StoredFoundationViews.tsx` `SldView`, the `selection` passed to `SiteSldPrimary`.
  - What: the parts-table and topology-card choices carry `aria-controls`; the drawn nodes do not. Changes are still announced through the polite live region, so this is minor accessibility parity only.

None of C1-C4 needs to be fixed before the owner looks. C1 and C2 are worth fixing in the next fix round, or naming to the owner.

## Residual risk not already named in the packet

- **"Review or change bindings" can only remove a binding.** It leads to the existing S1 form, which is a remove-only form (`FoundationBindingsPanel.tsx:406`). For a missing required role, this affordance cannot add the binding. This is pre-existing S1 capability, not a V-01a regression, but the label "change" slightly over-promises.
- **The Unknown card state is reachable in tests only.** In practice a missing effective revision is handled by the Foundation-missing view before Readiness renders. This is harmless.
- **Gateway states other than STALE rest on DevTools interception.** CURRENT, UNKNOWN, DISABLED, no gateway, 503, 404 and loading are proven at the render level only (the packet discloses this). The client and response shape match the backend source, and the vitest suites cover each state. I consider that adequate for the UI path. The coordinator should still note that a stored DISABLED or UNKNOWN case was never exercised end to end before marking `readiness:2#a/2#b/3#a` delivered.
- **Not verified:** the Lab sections of layout-evidence after the precondition (including T025d), Finding detail regression screenshots, and screen-reader behaviour of the nested disclosures.

## Ready for the owner's visual check?

Yes. Copy and states are truthful against the Architect's rulings and the Addendum. No mock percentage, uptime, signal, firmware, Online or productive-use value appears as product data. Advanced content is retained and keyboard-operable. The owner should judge the narrow Readiness table (C1) during the walkthrough.
