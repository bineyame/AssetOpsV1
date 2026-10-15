"""S4-05a phase 1: the server's authored fixture/spec registry, read from the shipped conversion specs.

An authored designation names a fixture/spec ID and version; this adapter answers what the server's own spec
file declares for that ID (or raises `PublicationRefused` when the file cannot be read). A fixture outside the
registry is unknown, never assumed authored.
"""

from __future__ import annotations

import json
from pathlib import Path

from assetops_backend.evidence.publication import PublicationRefused

_CONVERSIONS = Path(__file__).resolve().parents[3] / "conversions"
AUTHORED_FIXTURES: dict[str, Path] = {
    "assetops.s4-power-demo-cases": _CONVERSIONS / "s4-power-demo-cases-v1.json",
    "assetops.s4-power-late-demo-cases": _CONVERSIONS / "s4-power-late-demo-cases-v1.json",
}


class AuthoredFixtureSpecs:
    def __init__(self, registry: dict[str, Path] | None = None) -> None:
        self._registry = AUTHORED_FIXTURES if registry is None else registry

    def declared(self, fixture_id: str) -> tuple[str, str] | None:
        path = self._registry.get(fixture_id)
        if path is None:
            return None
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))["schema"]
            return str(schema["id"]), str(schema["version"])
        except (OSError, ValueError, KeyError, TypeError):
            raise PublicationRefused("FIXTURE_UNREADABLE", f"the {fixture_id} spec could not be read") from None
