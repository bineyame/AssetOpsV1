# T011B - Shell And Dense Content Overflow Containment

Status: planned
USER_REVIEW_REQUIRED: false

Intended branch: `task/T011B-shell-and-dense-content-overflow-containment`

Task id note: `T011B` keeps this correction beside the T011/T011A surfaces
that exposed the viewport defect, while still making it a shared shell and
vocabulary fix before T012.

## Feature

Site Foundation And Configuration-Only Site, viewport correction before the
remaining canonical fidelity slices.

## Read For This Task

- `.ai/FEATURE_MAP.md`, `## Canonical Screen Fidelity`,
  `### Viewport and overflow commitment`.
- `.ai/FEATURE_MAP.md`, `#### Guards that follow from this architecture` and
  the `Guard migration:` list below it.
- `.ai/CODE_STATE.md`, the T009, T011, and T011A entries.
- `tasks/T011A-foundation-naming-and-operator-site-tab-inventory.md`.
- `frontend/src/ui/primitives.css`, especially `.app-shell`, `.app-frame`,
  `.app-frame__content`, `.data-table`, and `.site-tabs`.

## UI-Verifiable Screen Behavior

The operator shell keeps its rail and workspace bar anchored to the viewport
while dense page content owns its own overflow.

The Sites index still renders its full nine-column milestone table, but its
horizontal overflow is contained inside the dense content region instead of
escaping to the document and moving shell chrome. The operator Site tab row
still renders all eight T011A labels and may scroll in its own region if it
does not fit.

The operator shell no longer double-counts viewport height when the Simulator
Lab gate is open. The standalone Simulator Lab shell still gets a full-height
frame when `SimulatorLabShell` renders `.app-frame` outside `.app-shell`.

## Why This Is Next

T011 shipped the densest table in the product, and T011A shipped the eight-item
operator Site tab row. Browser review found the Sites index taking both
scrollbars, with horizontal overflow moving the rail along with the rows.

This is a diagnosed shared-layout defect, not a new product behavior. It can
run before T012 and T013 so later fidelity slices build on the viewport policy
rather than reproducing the overflow.

## Acceptance Criteria

- The Sites index keeps the complete nine-column inventory from T011. No column
  is hidden, reordered, stacked into cards, moved behind an overflow menu, or
  dropped because the viewport is narrow.
- Dense table overflow is owned by the table/content region. At desktop-class
  widths and below, a wide table may scroll horizontally inside its own region;
  the document itself must not acquire horizontal scrolling that moves the rail
  or workspace bar.
- `.data-table` usage has an explicit scroll-owning container or equivalent
  shared primitive behavior. Tests or checks prove table markup still preserves
  headers, rows, actions, and accessible table semantics.
- The operator Site tab row keeps all eight T011A labels: Overview, Foundation,
  Health, Performance, Findings, Work, Financials, and Evidence. It may scroll
  within its own region when needed, but it must not collapse, hide labelled
  tabs, or move them into an overflow menu.
- The operator shell vertical sizing stops the nested `100vh` double-count:
  `.app-shell` may own viewport height and `.app-frame` may flex inside it, but
  an otherwise empty operator page is not at least the viewport plus the
  workspace bar.
- `SimulatorLabShell` continues to render `.app-frame` standalone outside
  `.app-shell` with full-height behavior. The fix must distinguish standalone
  frame usage from frame-inside-operator-shell usage.
- No operator rail item is added, removed, collapsed to icon-only, or moved into
  a drawer.
- No product copy, tab vocabulary, route, Site read model, Site table column
  inventory, or feature-gate behavior changes.
- Browser verification confirms the Sites index and at least one operator Site
  page keep shell chrome anchored while only the dense content region scrolls
  horizontally where needed. This exact visual fit is review-time evidence, not
  a layout snapshot test.

## Required Product And Domain Semantics

- M1 commits to desktop-class browser width, at least `1280px` CSS pixels. It
  does not claim a mobile, phone, or portrait-tablet product form.
- Below the committed width, the product degrades truthfully with internal
  scrolling or explicit unsupported-viewport treatment where needed. It does
  not introduce a reduced Site model, a different rail inventory, or a different
  tab vocabulary to fit.
- Page-level overflow is not an allowed density strategy. Dense content owns
  overflow; shell chrome stays chrome.

## Protected Seams

- Shell overflow containment: review-time plus focused tests/checks.
  Dense regions own horizontal overflow, rail/workspace chrome stay anchored,
  and standalone Lab full-height behavior is preserved without operator-shell
  double-counting.
- Sites index column inventory: CI guard.
  The nine-column milestone definition remains intact at all widths where the
  table renders.
- Operator Site tab inventory: CI guard.
  All eight labels render; destination tabs remain destinations and the six
  future aspects remain labelled in place only.
- Navigation truthfulness and simulator feature gate: CI guard.
  No rail, route, gate, or Lab chokepoint behavior changes.

## Focused Tests And Checks

- UI test or component test asserting the Sites index still renders the full
  nine-column inventory and retains table/header/action semantics inside the
  overflow treatment.
- UI test asserting the operator Site tab row still renders all eight labels
  and does not render an overflow menu, drawer, disabled fake destination, or
  hidden subset.
- Focused style or DOM test proving the table/tab overflow owner exists. Do
  not turn exact pixel fit into a brittle snapshot.
- Focused test or check covering the operator shell and standalone Lab frame
  sizing split, so the Lab's full-height frame is preserved while the operator
  shell avoids the `100vh` double-count.
- Browser verification at a desktop-class viewport and a narrower viewport for
  the Sites index and one operator Site page.
- Run `tools/check-architecture.ps1`.
- Run `tools/check-agent-workflow.ps1`.
- Existing frontend tests, typecheck, and production build stay green.

## Scope Limits

- Do not change Site data, backend contracts, routes, feature flags, task
  sequencing, or user-visible product vocabulary.
- Do not collapse rails, add drawers, introduce mobile navigation, stack Sites
  rows into cards, hide columns by viewport, or move Site tabs into an overflow
  menu.
- Do not implement T012 Site Details dressing, T013 Foundation dressing, or any
  topology/SLD/device work.
- Do not add layout snapshot tests for exact pixel positions.

## User Review

User review is not required. This fixes diagnosed layout defects under the
already-reviewed viewport policy and adds no product capability, domain
semantics, route, or user-visible vocabulary.
