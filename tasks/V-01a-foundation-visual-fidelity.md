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
