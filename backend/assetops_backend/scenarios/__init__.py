"""Product-side ScenarioDefinition package.

A `ScenarioDefinition` answers what happens during a simulated interval. Site
Foundation answers what the Site is. The two do not duplicate one another and
neither is derived from the other: a scenario declares which Site it needs, and
that is the whole of the relationship.

Everything in this package above `adapters/` is storage-agnostic and speaks
domain records and port errors only, exactly as `sites/` does, and
`tools/check-architecture.ps1` enforces it the same way: no yaml, pathlib or
sqlite3 module and no direct file opening outside `adapters/`, and imports of
`adapters/` from the single composition module only.

Scenario identity is its own identity space. A `scenario_id`, a scenario
version, a scenario display name and a timeline identity never become a
`site_id`, and nothing here allocates, renames, or implies a Site.

Scenarios live in one globally unique `scenario_id` space spread over two
stores: a shipped read-only store holding tracked definitions, and a user store
under gitignored `var/scenarios/`. There is no overlay and no precedence
between them. T017 has no scenario creation flow, so this package has no write
path at all: every method on the port reads.
"""

__all__ = [
    "identity",
    "models",
    "ports",
    "parsing",
    "service",
]
