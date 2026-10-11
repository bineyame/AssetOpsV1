# V-01a — Site and Foundation visual fidelity

Status: open W1 visual gate (L); activate after startup guards
USER_REVIEW_REQUIRED: true
Depends on: merged S1-03 Site/Foundation/Readiness/SLD surfaces
Branch when activated: task/V-01a-foundation-visual

## Visible outcome and acceptance

Compare app and v6.9 `sites`, `foundation`, `readiness` and `sld` by manifest ID and supported panel portion. Capture 1440px desktop and 390px narrow app/mock pairs, or documented equivalents, for populated and missing states. Review hierarchy, density, labels, focus, keyboard navigation, selection, route and reload behavior. A selected Foundation revision and bound component must stay stable. Readiness distinguishes configuration from operational status, with PRE-S3-04 correction incorporated before acceptance.

Record the exact route, viewport, supported claim, deliberate gap, API/source and accepted visual differences for each panel. Run frontend tests, typecheck/build, layout evidence and ledger/registry checks. Independent Reviewer and owner inspect this gate; it supplies visual acceptance only, never technical closure or whole-screen Real by itself.
