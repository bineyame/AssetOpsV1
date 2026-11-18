# V-01a round 3 handoff: phases 3a and 3b landed; 3c (evidence, walkthrough, packet, checks) to do

Branch `task/V-01a-foundation-visual`. Round-3 base `b5a7a75`; build commit `5300c2a`.
Authority: `.agent/architect-V-01a-round3-answers.md` (sections 1-4, fix round 1-5, Addendum table),
`D-2026-10-12-v01a-round3-readiness-and-organization`, owner text `.agent/owner-V-01a-round2-feedback-2026-10-12.md`.

## Landed in `5300c2a` (all UI; no backend change)

- **Readiness** (`frontend/src/sites/ReadinessOverview.tsx`, new):
  - `readinessCards()` / `ReadinessCards`: Definition, Topology, Specifications, Controls from typed
    `configuration_gaps` codes (`SITE_*`; `COMPONENT_MISSING|TOPOLOGY_*|AC_BUS_PATH_MISSING`; `COMPONENT_RATING_MISSING`;
    `BATTERY_RESERVE_MISSING|SITE_CONTROL_MISSING`). Unknown (neutral) only when `NO_EFFECTIVE_REVISION` is present.
    `[data-readiness-card][data-card-state]`. Rendered inside `ReadinessVerdictPanel` (`FoundationBindingsPanel.tsx`),
    which lost its old metric row; separation sentence reworded (gateway contact is now on the page).
  - `ReadinessEvidenceTable`: "Readiness and commissioning evidence", columns Area/Declared/Confirmed/What is needed/Next step,
    rows definition, topology, controls, roles, gateway, commissioning (`[data-readiness-row]`). Confirmed is neutral
    "Not recorded" on every row; every row lists "Commissioning confirmation not recorded". Roles row's Next step is the
    "Review or change bindings" button, which opens `details[data-disclosure="readiness-advanced"]` and focuses the binding select.
  - `GatewayStatusPanel`: composes `GatewayHealthClient` (S2 `/gateway-health`). States: loading, unavailable/not_found
    ("Gateway contact unavailable." + registration-only line), none (`gateways: []`), CURRENT/STALE/UNKNOWN (neutral badges),
    DISABLED registration, `[data-gateway-period-note]` (CURRENT vs PAST/FUTURE wording: "checked now on the server clock;
    it did not occur in that period"), "Device connection not established here.", the exact addendum
    "Not available yet: uptime trend, …" line, and a closed "Advanced details — gateway diagnostic records" disclosure.
  - Plumbing: `App.tsx` passes `siteEvidence.gatewayHealth` → `SiteFoundationFrame` `gatewayHealth` → `StoredFoundationViews`.
  - `ReadinessView` (`StoredFoundationViews.tsx`): strip, compact `[data-selected-part-chip]`, verdict+cards, table, gateway,
    then one Disclosure "Advanced details — roles, channels and records" holding Role coverage, Signal bindings (+ form),
    Registered gateway and sources (sentence reworded), Acquisition details; scope note no longer renders
    `foundation.evidence.statement` (it said contact is "not assessed here", now false on this view; record as a deviation).
- **Site model**: `panel-pair--balanced`; `IdentityPanel` shows "First in critical-load priority: X" or
  "Critical-load priority not configured", "Configured loads" (stored LOAD components), "Productive-use designation: Not declared",
  "Financial assumptions not available here". `FoundationControlsPanel` (`FoundationRevisionPanel.tsx`) gains an
  "Evidence / change" column: Published configuration · vN (reserve, critical), "No proposed-change record here",
  "No linked constraint evidence", and the Dispatch link "Open Dispatch; choose an assessed day" (`dispatchHref` from the frame).
  Audit material is under Disclosure "Advanced details — Foundation records" (`foundation-advanced`).
- **SLD**: the parts table shows channel counts only; full lists under "Advanced details — diagram records" (`sld-advanced`,
  with new `sld-part-channels`). `[data-sld-missing]` carries the addendum's exact protection/meter sentence + Site Evidence link.
- **Part strip**: the global Selected part panel is gone. `SelectedPartStrip` sits in the topology panel and in
  `SiteSldPrimary` (new `strip` prop, after the drawing, outside `.sld__scroll`): name, type · rating, "N bound; M not bound",
  Clear (focus returns to `[data-part-choice]`), closed "Advanced details — selected part channels". Region
  `#selected-part-strip-{model|sld}` is `aria-live="polite"`; `PartChoice` has `aria-controls`.
- **Sites**: "Operating view" column (`[data-operating-view]`: "Not available yet" + "Assessment · top issue · evidence limit ·
  last analysed"), and `[data-testid=sites-aggregate-absent]` ("N registered Sites listed." + aggregate/setup-progress gap).
- CSS appended to `frontend/src/ui/primitives.css` (readiness-cards, not-available-yet, gateway-facts, part-strip, part-chip).

## Proofs so far

- 20 new round-3 tests plus 9 updated ones in `shell/__tests__/siteFoundationRevision.test.tsx`, `sites/__tests__/sitesIndex.test.tsx`,
  `ui/__tests__/overflowContainment.test.tsx`. With the seven source files restored to `b5a7a75` (tests kept): **29 failed / 88 passed**;
  restored with `git checkout HEAD -- frontend/src`.
- `vitest run src/sites src/shell src/ui`: 54 files, 1334 passed. `tsc --noEmit` clean.
- Not yet run: full vitest, `npm run build`, `tools/check-all.ps1`, layout evidence, the V-01a evidence tool.

## Phase 3c to do

1. Servers: only 8880/8881 (API) and 5380/5381 (Vite) with own DB copies (e.g. `assetops_v01ar3walk` / `assetops_v01ar3empty`);
   `tools/v01a_foundation_walkthrough.py` currently hardcodes `assetops_v01awalk`/8860 — parametrize ports/DB names, do not
   touch 8860/8861/5360/5361 or owner servers. Stop everything started.
2. Refresh `tools/v01a-foundation-evidence.mjs` (446 lines; Readiness claims ~324-340, part claims ~295-316, Sites ~176): cards,
   table (Not recorded), gateway panel states (loaded on real DB; unavailable via a stopped/absent API or route interception;
   historical `at` via `CURRENT`/`IMPORTED` constants ~120), Advanced disclosures closed/open, part strip inside topology/SLD
   panels and within 390 px, SLD missing note, Sites Operating view cell at 390 px.
3. `.agent/V-01a-owner-walkthrough.md`: plain-language round-3 steps with app/mock pairs at 1440/390.
4. Packet `.agent/V-01a-review-packet.md` "Round 3" section with per-panel conditional-acceptance rows exactly per the addendum
   (sites:1, foundation:2-3, readiness:1-3, sld:1-2: read, missing-state copy, unfilled mock claim + trigger, 1440/390 evidence,
   and the caveat text left for the owner — do not write acceptance). Known deviations: dropped `evidence.statement` from the
   Readiness scope note; gateway contact badges are neutral (colour stays configuration-only on Readiness).
5. `.ai/CODE_STATE.md` short entry, `.ai/ACTIVE_CONTEXT.md` pointer; task Status stays `in_review`.
6. Full vitest, `tsc`, `npm run build`, `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1`, bounded layout evidence
   (record the known Lab precondition).

## Open risks

- Gateway panel on a real Site depends on the S2 read returning 200 for the imported Site; a 404 renders "Gateway contact unavailable".
- `.readiness-cards` collapses to 2 columns under 900 px and 1 under 480 px; unmeasured until layout evidence.
- Nested `<details>` (Advanced Foundation records holds inner disclosures); layout-evidence opens every `[data-disclosure]`.
