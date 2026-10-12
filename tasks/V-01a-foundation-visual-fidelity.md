# V-01a — Site and Foundation visual fidelity

Status: in_review (selected 2026-10-12 by next-work tie-break, gap 6.97% notice in `.agent/coordinator-handoff.md`; built on `task/V-01a-foundation-visual`, packet `.agent/V-01a-review-packet.md`)
USER_REVIEW_REQUIRED: true
Depends on: merged S1-03 Site/Foundation/Readiness/SLD surfaces
Branch when activated: task/V-01a-foundation-visual

## Visible outcome and acceptance

Compare app and v6.9 `sites`, `foundation`, `readiness` and `sld` by manifest ID and supported panel portion. Capture 1440px desktop and 390px narrow app/mock pairs, or documented equivalents, for populated and missing states. Review hierarchy, density, labels, focus, keyboard navigation, selection, route and reload behavior. A selected Foundation revision and bound component must stay stable. Readiness distinguishes configuration from operational status, with PRE-S3-04 correction incorporated before acceptance.

Record the exact route, viewport, supported claim, deliberate gap, API/source and accepted visual differences for each panel. Run frontend tests, typecheck/build, layout evidence and ledger/registry checks. Independent Reviewer and owner inspect this gate; it supplies visual acceptance only, never technical closure or whole-screen Real by itself.

## Owner-directed fix round (2026-10-12)

The owner confirmed that the Sites comparison is `sites:1` Site inventory only, requested a denser inventory, a bus-bar SLD and topology icons, green/amber configuration Readiness, and an inferred persistent part selection. The Architect's exact ruling and implementation checklist are in `.agent/architect-V-01a-answers.md` and decision `D-2026-10-12-v01a-owner-visual-rulings`.

For `sites:1`, make Site identity, Type and Mode the compact primary row; keep location, lifecycle, configuration origin and template provenance accessible as separate, labelled secondary/detail facts. Explain the absent mock Assessment, Top issue, Evidence and Last analysed claims beside the panel: S2 Evidence and S3 assessment reads require a selected Site/window, S4-01 supplies Finding detail rather than a ranked Site FindingIndex, and S5/S7 own broader summary/health. Do not manufacture positive directory values, cross-Site totals or a timestamp. This visual change leaves the registry's `sites:1#a` technical boundary and status unchanged.

Readiness colour applies only to the selected Foundation/binding configuration: green for complete required configuration, amber for a known configuration gap, and neutral for Unknown. Use the same rule on role/table badges with text labels; colour never asserts evidence coverage, contact, asset condition or operational health. Keep “Foundation” as the page h1.

Draw the selected Foundation's supported electrical topology in a bus-bar grammar with source/load icons, preserving every declared node and connection. Draw breakers, meters, monitoring links, status dots and live values only where their own typed, selected-period source exists; otherwise omit them or mark them unavailable outside the connected topology. Label the drawing configured, not live. Topology-card icons follow declared component type and have visible names/accessibility text.

Add a selectable configured part linked by stable component ID in the address. Selection survives reload and Foundation/Readiness/SLD navigation; a period change retains it only if that ID exists in the newly selected version, otherwise clears it with an explicit explanation. The selected part's bindings always resolve from the selected effective period. Review the 1440px and 390px app/mock pairs, selection and missing states with the owner after independent fix re-review; no extra product choice is needed before that checkpoint.

## Owner-directed round 3 (2026-10-12)

The owner withheld visual acceptance after round 2 and asked for mock-shaped Readiness hierarchy, plain-language defaults with explicit advanced disclosures, denser Site model, and a compact chosen-part detail. The binding ruling and exact fix list are in `.agent/architect-V-01a-round3-answers.md` and `D-2026-10-12-v01a-round3-readiness-and-organization`.

Add four category cards and a plain Readiness/commissioning table derived from selected Foundation gaps, controls, topology, ratings and binding roles. “Confirmed” stays “Not recorded” without a commissioning source. Reuse the existing S2 gateway-health read for a separately time-labelled central contact summary, with unknown/unavailable/disabled states and no claim of device connection or accepted telemetry. This bounded read composition expands V-01a beyond a purely visual edit; independent review of the exact S2 read/UI path is required before noncore `readiness:2` registry portions can be marked delivered. Keep `readiness:1` W1 core mapping and whole-screen status unchanged.

Move raw role/binding/channel and revision/provenance records into clearly named, keyboard-operable Advanced details while keeping meaningful values, configuration gaps and access to binding changes visible. In Foundation, show typed first critical-load priority and named loads, but identify productive-use designation as undeclared; only link to existing Foundation record, Site Evidence or selected-window Dispatch destinations with exact scope labels. Keep Financials/Change/constraint-proof links unavailable until their records/routes exist. Move selected-part detail into a compact in-context strip with expandable channels at desktop and 390px, preserving `component` URL selection, focus and missing-part behavior. Refresh owner evidence and obtain fresh independent re-review before the standing owner visual checkpoint.
