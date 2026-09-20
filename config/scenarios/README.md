# The shipped, read-only scenario store.

It does not ship empty, and that is the difference from `config/sites/`.

T017 ships no scenario creation flow, so a fresh checkout needs a tracked
definition for the catalog to show. `fuel-loss-event.yaml` is it: a directly
selectable `ScenarioDefinition`, not a template something is instantiated from.
A future `ScenarioTemplateCatalog`, if one is ever needed, stays in a separate
identity space, exactly as `SiteTemplateCatalog` stays separate from
`SiteRepository`.

Shipped definitions and user-authored ones share one globally unique
`scenario_id` space. There is no overlay and no precedence between the two
stores: the same identity in both, including as a case variant, is a
configuration conflict that fails loudly rather than resolving to either
document.

Nothing writes here. The user scenario store lives at `var/scenarios/`, outside
every shipped configuration root and outside version control, and in this slice
nothing writes there either - neither adapter has a write path at all.

A scenario says what happens during a simulated interval. Site Foundation says
what the Site is. A scenario declares which Site it needs and never allocates,
renames, clones, or implies one.
