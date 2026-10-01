# T025f - Template versioning and site lineage staleness (S0)

Status: complete
USER_REVIEW_REQUIRED: false

Map: A/B hardening; scenario-site contract S0. Depends on: T025b template
content. Next: T025g. Lane: fast (Implementer -> Reviewer).
Branch: task/T025f-template-versioning
Sizing: one focused change.
Planner: Claude under `D-2026-09-30-planner-claude-until-reset` (Planner bound
to Claude until the Codex reset 2026-10-03 21:23).

## Outcome

Open a Site created from the Kobo template before this slice: beside "Created
from template" it says the site was created from `kobo-mini-grid-60kw` v1 and
the current template is v2. A Site created after this slice says v2 with no
staleness note. Editing a shipped template without a version bump fails a test.

Why now: T025a and T025b edited `kobo-mini-grid-60kw` in place at v1, so two
sites with the same lineage hold different content
(`D-2026-10-01-run-binds-scenario-to-site`, Trigger). T025g freezes template
lineage on runs and is only honest once lineage means one content.

## Read for detail

- `D-2026-10-01-run-binds-scenario-to-site` (Versioning).
- `.agent/scenario-site-targeting-architect.md` section 4, S0.
- T020A's `hybrid-mini-grid-100kw` v2 bump as the precedent; shared checks in
  `tasks/README.md`.

## Acceptance criteria

1. `kobo-mini-grid-60kw` moves to `template_version: 2`. The properties, the
   generator status signal and its mapping added in T025a/T025b carry
   `source_version: 2`; content that was already in the first v1 keeps 1. Use
   git history of the template to decide which is which, and name the commits
   in the packet. No other template content changes.
2. A pinned fingerprint guard covers every shipped template: a table of
   `(template_id, template_version) -> digest` over the parsed document (or its
   bytes, if the implementer prefers; say which). Changed content at an
   unchanged version fails with a message naming the template and telling the
   author to bump the version. A new version adds a pin; old pins may stay.
3. A Site's read model exposes whether its recorded `template_version` is
   behind the current shipped template of the same `template_id`, computed on
   read and never stored on the Site. A site with no template, or whose
   template is no longer shipped, says so rather than "current".
4. Where the Site screens already show "Created from template", the label adds
   the advisory note, for example "created from v1; current v2". It is plain
   provenance text, not a status pill, a blocker or an action. If the current
   template catalog is reachable only behind the Lab gate, show the note only
   on gated surfaces and say so in the packet rather than widening the gate.
5. Existing Sites are untouched: nothing rewrites a site's recorded lineage or
   content (`Templates copy; they never migrate an existing Site`). Tests use
   in-process fixtures; no agent edits `var/sites` (KOBO-001, GONDAR-01).

## Protected seams and checks

Template provenance stays provenance only (`SiteTemplateProvenance`): never
lookup, routing or identity. No execution contract move: templates are copied
at site creation and no run reads them. Shared checks from `tasks/README.md`;
backend and frontend suites for the changed behaviour.

## Scope limits and review

No scenario change, no run-setup change and no picker (T025g). GONDAR-01 stays
as it is by owner decision: it holds v2 content but records v1, and its note
will truthfully say its record is stale.

Fast lane: no owner review. The first review is a discovery review under
`.ai/ROLE_CONFIG.md` (Codex, or a fresh Claude reviewer while the reset
exception stands).

## Review Outcome

Fast lane: `USER_REVIEW_REQUIRED: false`, so no owner review was required and the
slice merges on the reviewer's verdict.

- Claude review (`.agent/T025f-claude-review.md`, commit `24f53f2`), a fresh
  Claude reviewer under the temporary binding: ACCEPT WITH CARRIES.
- Under `D-2026-09-22-milestone-speed-over-purity` every finding is carried, not
  fixed. Carries (F1 no frontend test for UNRECOGNISED_VERSION, F2 the "records
  unchanged" assertion cannot fail, F3 unused state type), the decision-wording
  question routed to the Architect and two residual risks are in
  `.ai/MILESTONE_REVIEW_BACKLOG.md` under "Carried from T025f".

Next: T025g, then T026.
