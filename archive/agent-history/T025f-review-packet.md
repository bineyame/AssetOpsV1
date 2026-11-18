# T025f review packet - Template versioning and site lineage staleness (S0)

Task: `tasks/T025f-template-versioning.md` (fast lane, `USER_REVIEW_REQUIRED: false`).
Branch `task/T025f-template-versioning` from `6dd4b96`. Implementer: Claude.
First review: discovery review under `.ai/ROLE_CONFIG.md` (Codex, or a fresh
Claude reviewer while the reset exception stands).

## Outcome delivered

- `kobo-mini-grid-60kw` is v2; a pinned fingerprint per shipped
  `(template_id, template_version)` fails on in-place edits.
- With the Lab gate open, a Site recorded at Kobo v1 shows, under "Created
  from template", `kobo-mini-grid-60kw v1` and a secondary line "Created from
  v1; current template is v2". This appears on the Sites index row, the Site
  Overview and the Foundation. A Site created now records v2 and shows no note.
- Nothing rewrites a Site; the comparison is computed on every read.

## Commits

- `2208961` template v2 and the pinned fingerprints
- `f71cb5b` gated lineage read (backend)
- `8a81fc7` advisory note in the site substrate and shell wiring
- `beef893` tests (frontend lineage, backend "created now is current")
- closeout commit (packet, CODE_STATE, ACTIVE_CONTEXT, task status)

## Files materially changed

- `config/site-templates/kobo-mini-grid-60kw.yaml`: version 2, four
  `source_version: 2`, header comment.
- `backend/tests/test_site_template_fingerprints.py` (new): the guard.
- `backend/assetops_backend/sites/lineage.py` (new): `assess_template_lineage`.
- `backend/assetops_backend/simulator_lab_api.py`:
  `SITE_TEMPLATE_LINEAGE_ROUTE` and its handler.
- `backend/tests/test_site_template_lineage.py` (new); `test_simulator_lab_gate.py`
  names the new gated path in both inventories rather than tolerating it.
- `frontend/src/sites/siteTemplateLineage.ts`, `TemplateProvenanceText.tsx` (new);
  `SitesIndex.tsx`, `SiteDetails.tsx`, `SiteConfiguration.tsx` take an
  optional `templateLineage` client.
- `frontend/src/shell/simulatorLabRoutes.tsx`: `SITE_TEMPLATE_LINEAGE_API_PATH`,
  `simulatorLabSiteTemplateLineage(flags)`. `App.tsx` and three frames
  pass it through.
- `frontend/src/shell/__tests__/siteTemplateLineage.test.tsx` (new).

## Acceptance criteria

1. **Met.** `template_version: 2`. From `git log --follow`:
   - `c0f49ce` created the first v1.
   - `2f076d3` (T025a) added `start-soc-threshold`, `stop-soc-threshold`,
     `start-delay` and `generator-rated-power` on `generator`. These now carry
     `source_version: 2`.
   - `0dc42c0` (T025b) added the `status` signal on `generator-controller` and
     the `generator-status` mapping.
   - Everything else keeps 1, including both `site_controls`. The diff against
     `HEAD~` is exactly five value lines plus comments.
   - The test `test_kobo_template_is_version_two_with_the_t025_additions_at_two`
     pins the set of properties at 2.
   - **Deviation:** signals and mappings have no `source_version` field in the
     strict Foundation schema (`foundation_parsing.py` allows it only on
     properties (:96) and site_controls (:139)). Adding one would change the
     schema, which is outside this slice. The template bump is what records them.
2. **Met.** `PINNED_TEMPLATE_FINGERPRINTS` maps `(template_id, template_version)`
   to a SHA-256 digest.
   - The digest is taken over the **parsed document**: `yaml.safe_load`, then
     JSON with `sort_keys`, compact separators and `default=str`.
   - Changed content at a pinned version fails with "shipped template 'X'
     changed content at unchanged template_version N. Bump template_version...".
   - An unpinned version fails asking for its pin and prints the digest to add.
   - A pin with no matching document is allowed.
   - Kobo v1 is deliberately left unpinned, because it named two contents.
3. **Met, gated.** `assess_template_lineage` returns one of five states:
   - `CURRENT`
   - `BEHIND`
   - `NOT_SHIPPED`, for a template that is no longer shipped
   - `NO_TEMPLATE`
   - `UNRECOGNISED_VERSION`, when the recorded version is above the shipped one
   It is computed on read and served at `GET /api/simulator-lab/site-template-lineage`. The tests assert that the records are unchanged after a read and that the operator `/api/sites/{id}` gained no field.
4. **Met, on gated surfaces only.** The note is a `span.cell-secondary`: plain
   text, with no badge, button or link (asserted).
   - The template catalog is gated: `main.create_app` builds it only when
     `simulator_lab_enabled`, and "a closed gate ... must not touch the
     catalog". So the lineage read is gated too.
   - The site surfaces get the client only from
     `simulatorLabSiteTemplateLineage(flags)`.
   - With the gate closed there is no read (the client is asserted not called)
     and no note. The gate was not widened.
   - The Sites index, Overview and Foundation are operator routes. They show
     the note only when the Lab gate is open, in the same way they show gated
     quick actions.
5. **Met.** Nothing writes a Site:
   - The lineage handler only reads.
   - The read-only fake repository raises on `create_site`.
   - Tests use in-process fixtures and the real shipped catalog read-only.
   - No file under `var/` was read or edited.
   - Templates still copy at creation, and no run reads a template.

## Checks run (serially)

- `backend` pytest: **1334 passed**.
- `simulator` pytest: **227 passed**.
- `host` pytest: **520 passed** (run after the template bump; the
  `contract9_gate` is unaffected because frozen runs carry their own values).
- `frontend` `npm.cmd test`: **1006 passed** (39 files).
- `tsc --noEmit`: clean. `npm.cmd run build`: built.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- **Mutation proofs**, each reverted with `git checkout --`:
  - The Kobo `start-soc-threshold` changed from 35 to 36. The fingerprint test
    failed with "changed content at unchanged template_version 2. Bump...".
  - `template_version` 3 with no pin. The test failed with "version 3 has no
    pinned fingerprint ... add ('kobo-mini-grid-60kw', 3): '9ce654a8...'".
  - `simulatorLabSiteTemplateLineage` made to return the client regardless of
    the gate. The test "does not read lineage and shows no note with the Lab
    gate closed" failed.
- **Layout evidence: not run.** `tools/layout-evidence.mjs` measures a running
  backend over the local Site store under `var/`, which this dispatch forbids
  reading. The change adds one wrapping block line, using the existing
  `.cell-secondary` class, inside one existing index cell and one `dd`. The
  claim that this adds no overflow at narrow widths is therefore unverified.

## Known deviations

- AC1: the signal and mapping cannot carry `source_version`. The schema has no
  such field (see above).
- AC4: the note shows only with the Lab gate open, by the AC's own rule.

## Residual risk

- A failed lineage read shows the recorded provenance alone and no "unknown"
  note. A stale site then reads exactly as it did before this slice.
- The Sites index makes one more gated GET when the gate is open. Overview and
  Foundation each re-read the lineage of every site. The list is small, but
  each read re-parses the catalog.
- The pin table lives in a test file. T025g's scenario pins will need the same
  shape, so they may want a shared helper.

## User-review focus

None required (fast lane). Owner-visible, with the Lab enabled:
- GONDAR-01 and KOBO-001 record v1, so both will show "Created from v1;
  current template is v2". For GONDAR-01 this is true of its record, per the
  decision.
- A newly created Kobo site shows `kobo-mini-grid-60kw v2` with no note.
