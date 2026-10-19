# D-2026-10-19-w2-03-followup — cold assessment fidelity and chip tones

**Status:** Architect decision. **Scope:** W2-03 presentation follow-up after merge; implement in `frontend/src/sites/ColdAssessmentViews.tsx` and `frontend/src/sites/w2-cold-assessment.css`, with focused UI proof and captures. Do not change selected reads, findings, policy, bounds, provenance, links, panel order, titles, or the v69 mock. The stocked 1440 px comparison in `.agent/W2-03-review-packet.md` is the baseline; these are closed-panel limits, not guaranteed new measurements.

The v69 mock has one short claim-boundary paragraph, a causal strip beside a short next-step card, and a temperature chart beside a short next-step card. Keep those primary forms visible. Put the extra selected detail in the panel's **existing single** `ExactReferences` disclosure (`extra` accepts React content); do not nest a second `details` or add a fourth panel. Every moved fact remains keyboard reachable. For each populated, empty, pending, or refused state, retain its truthful gap in the same panel. Never substitute mock fixture numbers or a fabricated Action.

## Closed-panel rulings

| Route and v69 panel | Baseline → 1.3× ceiling | Closed panel, exact copy | Existing disclosure, exact label and moved content |
| --- | --- | --- | --- |
| `temperature`, panel 3, app title **How each limit is set** (approved mock **Claim boundary** title exception) | 225 / 120 px → **≤156 px** | Keep the current outcome-dependent first `p.prose` sentence(s) verbatim: the supported excursion, within-policy, or unknown conclusion and product-condition boundary. No separate status/currentness line here. | Keep one `ExactReferences name="cold-claim-references"`, summary **How this was worked out**. Move the whole `data-cold-claim-facts` line (usable/expected count and ratio, set-aside reasons, source classification, and, when selected, the exact `SIMULATION_SOURCE_SENTENCE`) and the complete `data-cold-limitations` list into `extra`, after the existing labelled exact references, as the component renders `extra`. Keep source IDs, assessment versions/basis, evidence time and excluded record IDs in the same disclosure. Empty lists still state **no records set aside**; do not drop source gating or a limitation because it is closed. |
| `cold-finding`, panel 2 **Operational context** | 348 / 253 px → **≤328 px** | Keep the complete eight-step `CausalTimeline` with observed/missing/conflicting step words and its exact accepted-record links. Beneath it keep one compact line: **Missing steps: {joined `stepLabel` values}** or **Missing steps: None**. If the companion backup read is unavailable, keep the existing refusal/chain gap instead of a timeline; do not show a false chain. | Keep one `ExactReferences name="cold-finding-references"`, summary **How this was worked out**. Move the `Versions` key-value row (`versionsLine(finding)`), the complete `EvidenceLine` (numbered accepted-record links and the labelled unavailable Analysis target), and the current `findingReferences(finding)` exact identifiers/history into it. The selected `finding.revisions` count/latest transition remains readable on expansion; all earlier revision IDs remain there. The moved EvidenceLine still uses only proved record links. |
| `cold-finding`, panel 3 **Recommended next step** | stretched 348 / 253 px → **≤328 px** | Keep the exact gap **No recorded next step. No Action or Recommendation record is linked to this Finding.** and **Open the Backup view →** link. No action instruction or recommendation is invented. | No disclosure is needed; this card has no extra selected detail. Stop the pair grid from stretching its height to panel 2. |
| `cold-finding-excursion`, panel 2 **Temperature** | 487 / 333 px → **≤432 px** | Keep `ColdTemperatureChart`, its policy band/points/gaps, and `gapNotes(t)` immediately below so missing intervals remain visible. If the temperature read is unavailable, keep the existing in-panel gap. | Keep one `ExactReferences name="cold-finding-references"`, summary **How this was worked out**. Move both selected `KeyValues` rows, **Peak observed** and **Exposure size**, and the complete `EvidenceLine` into `extra`, after `findingReferences(finding)` as the component renders `extra`. The full peak and degree-minute bounds, every accepted-record link, assessment limitation and Finding/episode/revision identifiers remain reachable. The bounded conclusion above already states the observed peak and duration; do not imply interpolation or spoilage. |
| `cold-finding-excursion`, panel 3 **Recommended next step** | stretched 487 / 333 px → **≤432 px** | Keep the same exact `NextStepPanel` gap sentence, **Open the Temperature view →**, and the proved **Related: backup start Finding →** link when selected. | No disclosure is needed; stop grid stretch as above. Do not render a related link without an exact selected Finding. |

For the two Finding pairs, add `className="cold-finding-pair"` to their existing `div.panel-pair`; do not wrap panels or change DOM order. The existing `ExactReferences` API already has `extra`; supply the moved React nodes to that prop and preserve its name and existing reference rows. The `Operational context` timeline is the mock's main content, so it stays closed; only the two detail rows and provenance line move. The excursion chart stays closed for the same reason. No accepted exception is granted for these heights. The separate `coldbackup` **Evidence by causal step** overage in the review table is outside this request and is not an exception decision here.

The claim panel's exact closed text variants remain the current selected-read strings: for an excursion, `The accepted probe readings support a {claimWord(x.claim_level).toLowerCase()} temperature excursion {limit.word} policy. Product quality or spoilage conclusions need product identity, an exposure policy and further evidence.`; for `NO_EXCURSION_OBSERVED`, `The accepted probe readings stay within policy for this window. This says nothing about product condition.`; otherwise, `The accepted probe readings do not support a temperature conclusion for this window.` The placeholders are the existing selected values/functions, never fixture copy. The closed Operational context line is exactly `Missing steps: None` or `Missing steps: {missing.map((s) => stepLabel(s)).join(", ")}`. Render it even when the selected list is empty; where the companion chain cannot be read, show the existing gap and this selected Finding missing-step list without implying observed events.

### Exact CSS to add in `w2-cold-assessment.css`

Use these route and panel scopes; no shared `.panel`, `.prose`, chart, timeline, or badge-token edit. The `ExactReferences` summary keeps its current visible label and focus outline.

```css
[data-cold-view="temperature"] .panel:has(#cold-claim-boundary-heading) .panel__body > .prose {
  margin-bottom: 0;
}
[data-cold-view="temperature"] [data-disclosure="cold-claim-references"],
[data-cold-view="cold-finding"] [data-disclosure="cold-finding-references"],
[data-cold-view="cold-finding-excursion"] [data-disclosure="cold-finding-references"] {
  margin-top: 8px;
}
[data-cold-view="temperature"] [data-disclosure="cold-claim-references"] > .disclosure__summary,
[data-cold-view="cold-finding"] [data-disclosure="cold-finding-references"] > .disclosure__summary,
[data-cold-view="cold-finding-excursion"] [data-disclosure="cold-finding-references"] > .disclosure__summary {
  padding: 4px 10px;
}
[data-cold-view="cold-finding"] .cold-finding-pair,
[data-cold-view="cold-finding-excursion"] .cold-finding-pair {
  align-items: start;
}
[data-cold-view="cold-finding"] .cold-operational-missing {
  margin: 6px 0 0;
  font-size: 11px;
  line-height: 1.4;
}
```

Render the missing-step line as `<p className="cold-operational-missing">…</p>`. The 1440 ceiling decides success; if the stocked panel still exceeds it, report the exact panel, selected text and measurement for a further Architect ruling instead of clipping, hiding, shrinking the shared font, or accepting drift. At 390 px, let disclosure content wrap and scroll naturally with the page, without horizontal viewport overflow.

## M5 W2-03 chip-tone checklist

This applies only to W2-03 badges in `ColdAssessmentViews.tsx`. Keep their visible words. In `w2-cold-assessment.css`, add exactly:

```css
.cold-temperature-tone--green.badge {
  background: #e3f4ed;
  color: #166b50;
  border-color: #b5dfcd;
}
.cold-temperature-tone--amber.badge {
  background: #fff1d9;
  color: #8e580c;
  border-color: #c9a24a;
}
```

| Component / badge | Selected value → class on that `Badge` | Existing treatment |
| --- | --- | --- |
| `TemperatureStatus`, first state badge | `Within policy` → `cold-temperature-tone--green`; `Outside policy` or `Readings disagree` → `cold-temperature-tone--amber`; `Not assessed` → none (`badge--neutral`) | The adjacent **Coverage: {known} / {expected} readings** badge remains neutral. |
| `BackupStatus`, first start-result badge | `Started` → `cold-temperature-tone--green`; `Start failed` → red; `Results disagree` → amber; `Not established` → neutral | Use the current `.cold-result--danger .badge` and `.cold-result--warning .badge` selectors by wrapping this badge in the corresponding result span. Keep their current CSS as M5 directs. `Evidence: {claim_level}` stays neutral. |
| `BackupPanels`, each **Backup event chains** Result-cell badge inside `.cold-result` | `Started` → `cold-temperature-tone--green`; `Start failed` → existing `.cold-result--danger`; `Results disagree` → existing `.cold-result--warning`; `Not established` → neutral | Keep the existing red/amber result selectors and values. Do not add a second red/amber badge class. The no-event badge stays neutral. |

The result wrapper must map `OBSERVED_SUCCESS` to green, `OBSERVED_FAILURE` to danger, `CONTRADICTORY` to warning and other values to neutral. For the green result use `cold-temperature-tone--green` on the result `Badge` itself. Only the selected state/result badge changes colour; provenance, lifecycle, origin, configuration, coverage and claim-level badges stay on their existing tokens. Colours do not create a health or evidence classification. W2-04 owns its separate Contact/Quality/capability/strip tones.

## Implementer dry-read

1. In `ColdAssessmentViews.tsx`, move the exact existing fact/list/link nodes listed above into the corresponding `ExactReferences.extra` without altering their underlying selected-read expressions or link targets. Leave each panel with at most one `details[data-exact-references]`. Add the one closed missing-step line and `cold-finding-pair` class. The two right cards become content height through scoped `align-items: start`.
2. Apply only the CSS above, checking the claim-panel selector against the rendered DOM. No chart height/axis change is authorized. Map the three specified state/result badge sites; keep the two existing red/amber result tone rules unchanged.
3. On the stocked selection, the closed visual order remains mock-like: conclusion → claim sentence/disclosure; eight-step strip → missing-step line/disclosure; chart → gap note/disclosure. Expanded details contain all former coverage, exclusions, source, limits, peak, exposure, versions, IDs and record links.

## Copy dry-read

- Claim panel: the selected conclusion and product boundary stay visible; **How this was worked out** reveals usable count, expected count/ratio, set-aside reasons, source classification/registered-test sentence, all limitations and exact references.
- Start Finding: **Missing steps: None** or **Missing steps: {step labels}** appears below the full chain; expansion reveals **Versions**, numbered **Accepted records**, **Analysis view not available for this cold record**, and exact history. The next-step card states **No recorded next step. No Action or Recommendation record is linked to this Finding.**
- Excursion Finding: chart and actual gaps stay visible; expansion reveals **Peak observed**, **Exposure size**, the same accepted-record/Analysis limitation and exact references. The next-step card uses the same gap sentence, Temperature link and proved related Finding link.
- Temperature chips read **Within policy**, **Outside policy**, **Readings disagree**, **Not assessed**; result chips read **Started**, **Start failed**, **Results disagree**, **Not established**. Only the M5 mapping changes their tones.

## Required proof and recapture

- Extend `frontend/src/sites/__tests__/coldRoutes.test.tsx` for all four routes and the stocked, empty/unknown, pending and refused variants already represented there: exact panel count/order/title, one closed disclosure per affected panel, all moved facts and exact links found after opening it, the closed chain/chart/gap content, no fabricated next step, and the pair not stretched in browser evidence. Assert the M5 class on the exact state/result badge for every value, with coverage and claim-level badges neutral. Preserve the existing eight-step and link-target assertions.
- Run the focused `coldRoutes.test.tsx` suite, `frontend` typecheck, and the applicable workflow/navigation/architecture guards. Presentation-only edits do not require a backend full suite.
- Recapture app versus v69 mock at **1440 and 390 px** for the four routes `temperature`, `coldbackup`, `cold-finding`, `cold-finding-excursion` on the same stocked Site/window/cutoff/revisions as the W2-03 packet. `coldbackup` is included for chip-tone proof. Include meaningful empty/refused captures at both widths to confirm honest gaps. Record mock hash, selection, screenshot paths and measured app/mock heights with disclosures **closed**. Explicitly remeasure temperature panel 3 at **≤156 px**, both `cold-finding` pair panels at **≤328 px**, both excursion pair panels at **≤432 px** at 1440; check no horizontal viewport overflow and readable expanded detail at 390. Measure actual DOM heights after fonts load; do not infer success from CSS values or pair-row height. Report any failure with the selected text for Architect reruling.
