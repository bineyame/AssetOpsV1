"""Storage adapters for ScenarioDefinitions.

This is the only package in `scenarios/` allowed to know a storage technology.
`tools/check-architecture.ps1` permits imports that resolve in here from the
single scenario composition module only, so replacing the store stays one new
adapter module plus one composition change, with no change to any caller.

Nothing here writes. T017 ships no scenario creation flow, so neither store has
a write path and the shipped root could not acquire one by accident even if a
caller asked for it.
"""
