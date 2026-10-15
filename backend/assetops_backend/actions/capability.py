"""The server-issued, scoped SYSTEM demonstration capability (S6-01a, Architect Q4).

A command runs only when the server holds a grant for that exact tenant, Site, command and fixture. The grant is
server configuration (`ASSETOPS_ACTION_DEMO_GRANTS`, read by an adapter); nothing a client sends grants it. Read
contracts expose the same decision as `system_demo_capability` so a client can render a read-only reason, and every
POST checks it again.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID

from assetops_backend.actions.lifecycle import COMMANDS, SYSTEM_DEMO

NO_GRANTS = "No SYSTEM demonstration capability is configured on this server."


@dataclass(frozen=True)
class Capability:
    allowed: bool
    command: str
    fixture_id: str | None
    unavailable_reason: str | None

    def wire(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "command": self.command, "fixture_id": self.fixture_id,
                "unavailable_reason": self.unavailable_reason, "actor_kind": SYSTEM_DEMO.actor_kind,
                "actor_id": SYSTEM_DEMO.actor_id, "label": SYSTEM_DEMO.label,
                "scope": "tenant, Site, command and fixture; granted by server configuration only"}


# (tenant_id, site_id, site_code, command) -> Capability
CapabilityCheck = Callable[[UUID, UUID, str, str], Capability]


def no_capability(tenant_id: UUID, site_id: UUID, site_code: str, command: str) -> Capability:
    return Capability(False, command, None, NO_GRANTS)


def from_grants(document: Mapping[str, Any] | None) -> CapabilityCheck:
    """A check over a parsed grants document:
    `{"schema": "assetops.action-demo-grants", "version": 1, "fixture_id": ..., "grants": [
       {"site_code": ..., "site_id": optional, "tenant_id": optional, "commands": [...]}]}`.
    A malformed document grants nothing."""
    valid = (isinstance(document, Mapping) and document.get("schema") == "assetops.action-demo-grants"
             and document.get("version") == 1 and isinstance(document.get("fixture_id"), str)
             and isinstance(document.get("grants"), list))
    if not valid:
        return no_capability
    fixture = str(document["fixture_id"])  # type: ignore[index]
    grants: Sequence[Mapping[str, Any]] = [g for g in document["grants"] if isinstance(g, Mapping)]  # type: ignore[index]

    def check(tenant_id: UUID, site_id: UUID, site_code: str, command: str) -> Capability:
        if command not in COMMANDS:
            return Capability(False, command, fixture, f"Unknown command {command!r}.")
        for grant in grants:
            if str(grant.get("site_code", "")).upper() != site_code.upper():
                continue
            if grant.get("site_id") not in (None, str(site_id)) or grant.get("tenant_id") not in (None, str(tenant_id)):
                continue
            if command in (grant.get("commands") or ()):
                return Capability(True, command, fixture, None)
            return Capability(False, command, fixture,
                              f"The SYSTEM demonstration grant for this Site does not include {command}.")
        return Capability(False, command, fixture, "No SYSTEM demonstration grant covers this Site.")

    return check
