# T025f review - Template versioning and site lineage staleness (S0)

Reviewer: Claude. This is a fresh reviewer instance that did not author the slice.
Reviewer is bound to Claude until the Codex reset at 2026-10-03 21:23, under the
exception in `.ai/ROLE_CONFIG.md`. A later reader may send any judgement here
back to Codex.

Branch `task/T025f-template-versioning`, diff `main...HEAD` (base `6dd4b96`),
head `21057c3`. Read: task, packet, `D-2026-10-01-run-binds-scenario-to-site`
(Versioning), and architect guidance section 4 (S0).

## Verdict

**ACCEPT WITH CARRIES.**

All five acceptance criteria are met, and I verified each one independently. No
finding blocks the merge. The three findings are Low or Info. They can be fixed
on the branch or carried, at the Implementer's choice.

## Acceptance criteria, verified

1. **Met.** `git log --follow` on the template gives `c0f49ce` (the first v1),
   `2f076d3` (T025a) and `0dc42c0` (T025b), and `git diff c0f49ce 6dd4b96`
   confirms what the packet says those commits added: the four generator
   properties, the `status` signal and the `generator-status` mapping. The
   T025f diff to the template is `template_version: 2`, four
   `source_version: 2` on exactly those properties, and a comment. No other
   content changes.
   - The deviation is right: signals and mappings have no `source_version` in
     the strict schema.
2. **Met.** The pin is over the parsed document. I checked it in memory:
   - The Kobo v2 digest matches the pin.
   - Dropping one mapping at v2 produces the "changed content at unchanged
     template_version 2. Bump..." message.
   - The base v1 document digests differently (`ae6476b3...`).
   - Leaving v1 unpinned is guarded by
     `test_a_superseded_ambiguous_version_is_not_pinned`, so the "add a pin"
     message cannot be used to legitimise a rewound v1.
   - The guard globs `*.yaml`, the same files the catalog reads
     (`suffix == ".yaml"`).
3. **Met, gated.** `assess_template_lineage` has five states, is computed on
   read, and has no store write.
   - The operator `/api/sites/{id}` gains no field (tested).
   - A failure of either store gives a 503, never "current".
   - Exposing the comparison through a separate gated read model, rather than
     the operator Site read model, is the right reading: AC4 forbids widening
     the gate.
4. **Met.** The note is a plain `span.cell-secondary` on the Sites index row,
   Overview and Foundation. It is not a badge, button or link (asserted).
   - With the gate closed, `simulatorLabSiteTemplateLineage` returns
     `undefined`, no read happens (asserted), and nothing renders.
   - The client comes only from the gated module, and `frontend/src/sites/`
     does not name the Lab.
   - An answer about a different recorded lineage is ignored rather than
     applied.
5. **Met.**
   - The lineage handler only lists. The site repository port has only
     `create_site` as a write, and the test repository raises on it.
   - No path under `var/` is touched. The `.demo/` copies are untouched.
   - Templates still copy at creation, and no run reads a template.

## Findings

**F1 - Low, test gap.** `frontend/src/sites/siteTemplateLineage.ts:118`.

The `UNRECOGNISED_VERSION` note text ("Recorded vN is not a version this build
ships; current is vM") has no frontend test. `BEHIND`, `NOT_SHIPPED`, `CURRENT`,
the missing answer and the mismatched answer each have one.

This matters because it is user-visible copy on one of the five states. A
regression there would be silent.

Fix: one more case in the `templateLineageNote` describe block in
`frontend/src/shell/__tests__/siteTemplateLineage.test.tsx`.

This is not an acceptance gap.

**F2 - Low, test claims more than it proves.** `backend/tests/test_site_template_lineage.py:130,158-159`.

`before = list(records)` is a shallow copy of the same `SiteRecord` objects, so
the two equality assertions after the read are tautological. They cannot fail
whatever the handler does.

The real no-write proof is `ReadOnlyRepository.create_site` raising, and that
is sufficient, because `create_site` is the port's only write.

This matters because the comment "Computed on read: the recorded lineage is
exactly what was stored" reads as evidence it does not provide.

Fix: either assert against independently built expected values, for example
`[r.template for r in records] == [provenance("kobo-mini-grid-60kw", 1), ...]`,
or delete the two lines and let the read-only repository carry the claim. It is
not an acceptance gap.

**F3 - Info, preference.** `frontend/src/sites/siteTemplateLineage.ts:22-33`.

`SiteTemplateLineageState` is exported but unused, and
`SiteTemplateLineageReadModel.state` is typed `string`. It is harmless: an
unknown state falls through to `null`, which means no note. Either use the
union with a runtime check in `isLineage`, or drop the type. This is a
preference only.

## Observation for T025g or the Architect (not a finding against this slice)

`D-2026-10-01-run-binds-scenario-to-site` (Versioning) says a content change
bumps the version with "`supersedes` set, new valid-from". Shipped templates
have neither field. Neither the T020A `hybrid-mini-grid-100kw` v2 precedent nor
this task's AC1 asks for them, so T025f is consistent with its task.

The decision text reads as if it binds templates too. The packet does not
mention this. If the Architect means it for templates, that is a template
schema change and belongs to a later slice. If not, the decision wording could
say "scenario" for that clause.

## Checks I ran (serially, on `21057c3`)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `pytest backend/tests -q` | **1334 passed** |
| `pytest host/tests -q` (rerun because host fixtures read the shipped Kobo template) | **520 passed** |
| `npx.cmd tsc --noEmit` | clean |
| `npm.cmd test` | **1006 passed, 39 files** |
| `npm.cmd run build` | built |
| In-memory fingerprint check (see AC2) | pin matches; mutation fails with the bump message |

The sandbox esbuild failure the standing brief anticipates did not occur in
this session. The frontend suite and the build ran and passed for me. These
are my numbers, not the packet's.

Not rerun: the simulator suite (227 per the packet). Nothing under
`simulator/` references the site templates and the slice does not touch it.

## Could not verify

- **Layout evidence.** The packet correctly records `tools/layout-evidence.mjs`
  as **not run**, gives its blocking precondition (it measures a backend over
  `var/`, which the dispatch forbids reading), and does not claim a pass. That
  is the right form, so it is not a finding.
  - What remains unmeasured: the extra secondary line in the Sites index
    "Created from template" cell and in the Overview and Foundation `dd`.
  - Static reading lowers the risk. `.cell-secondary` is `display: block`, not
    `nowrap`. `tbody td` is not `nowrap`. The table owns its own `overflow-x`
    region. The fact list has `overflow-wrap: anywhere`.
- I did not see the note in a browser. My evidence for the rendered note is the
  component tests.

## Residual risk not already named in the packet

- If any single site record fails to parse, `list_sites` raises and the whole
  lineage read returns 503, so every site loses its note. This is consistent
  with "no note on a failed read", but the blast radius is all sites rather
  than one.
- The pin table can be edited in place: an author can change content and
  replace the pin at the same version. Review of the pin-line diff is the only
  defence. This is inherent to a pin, and T025g's scenario pins inherit it.
