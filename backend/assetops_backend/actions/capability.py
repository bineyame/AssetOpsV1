"""The server-issued, scoped SYSTEM demonstration capability (S6-01a, Architect Q4; phase-1 review M1).

A command runs only when the server holds a grant for that exact tenant ID, Site ID, command and fixture, AND the
command's target is a record of that fixture's `D-action-records` manifest: an accept names a Finding listed in
the grant's `records`, and an apply or OBSERVED names an Action whose origin Finding is listed there. The grant is
server configuration (`ASSETOPS_ACTION_DEMO_GRANTS`, read by an adapter, written by the `D-action-records`
loader); nothing a client sends grants it. Read contracts expose the same decision as `system_demo_capability` so a
client can render a read-only reason, and every POST checks it again.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from uuid import UUID

from assetops_backend.actions.lifecycle import COMMANDS, SYSTEM_DEMO

SCHEMA, VERSION = "assetops.action-demo-grants", 2
NO_GRANTS = "No SYSTEM demonstration capability is configured on this server."
NOT_A_RECORD = "This Finding is not a record of the SYSTEM demonstration fixture, so no command can run on it."


@dataclass(frozen=True)
class Capability:
    allowed: bool
    command: str
    fixture_id: str | None
    unavailable_reason: str | None
    manifest_id: str | None = None

    def wire(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "command": self.command, "fixture_id": self.fixture_id,
                "manifest_id": self.manifest_id, "unavailable_reason": self.unavailable_reason,
                "actor_kind": SYSTEM_DEMO.actor_kind, "actor_id": SYSTEM_DEMO.actor_id, "label": SYSTEM_DEMO.label,
                "scope": "tenant, Site, command and fixture record; granted by server configuration only"}


# (tenant_id, site_id, site_code, command, target Finding ID or None) -> Capability
CapabilityCheck = Callable[..., Capability]


def no_capability(tenant_id: UUID, site_id: UUID, site_code: str, command: str,
                  finding_id: UUID | None = None) -> Capability:
    return Capability(False, command, None, NO_GRANTS)


def _uuid(value: Any) -> str | None:
    try:
        return str(UUID(str(value)))
    except ValueError:
        return None


def from_grants(document: Mapping[str, Any] | None) -> CapabilityCheck:
    """A check over a parsed grants document:
    `{"schema": "assetops.action-demo-grants", "version": 2, "fixture_id": ..., "grants": [
       {"tenant_id": ..., "site_id": ..., "site_code": ..., "commands": [...],
        "records": [{"manifest_id": ..., "finding_id": ...}]}]}`.
    A malformed document grants nothing; a grant without a valid tenant ID, Site ID or records list is ignored."""
    valid = (isinstance(document, Mapping) and document.get("schema") == SCHEMA
             and document.get("version") == VERSION and isinstance(document.get("fixture_id"), str)
             and isinstance(document.get("grants"), list))
    if not valid:
        return no_capability
    fixture = str(document["fixture_id"])  # type: ignore[index]
    grants = []
    for g in document["grants"]:  # type: ignore[index]
        if not isinstance(g, Mapping) or not isinstance(g.get("records"), list):
            continue
        tenant, site = _uuid(g.get("tenant_id")), _uuid(g.get("site_id"))
        if tenant is None or site is None:
            continue
        records = {_uuid(r.get("finding_id")): str(r["manifest_id"])
                   for r in g["records"] if isinstance(r, Mapping) and r.get("manifest_id")}
        grants.append((tenant, site, str(g.get("site_code", "")).upper(), tuple(g.get("commands") or ()),
                       {k: v for k, v in records.items() if k is not None}))

    def check(tenant_id: UUID, site_id: UUID, site_code: str, command: str,
              finding_id: UUID | None = None) -> Capability:
        if command not in COMMANDS:
            return Capability(False, command, fixture, f"Unknown command {command!r}.")
        for tenant, site, code, commands, records in grants:
            if (tenant, site, code) != (str(tenant_id), str(site_id), site_code.upper()):
                continue
            if command not in commands:
                return Capability(False, command, fixture,
                                  f"The SYSTEM demonstration grant for this Site does not include {command}.")
            manifest = None if finding_id is None else records.get(str(finding_id))
            if manifest is None:
                return Capability(False, command, fixture, NOT_A_RECORD)
            return Capability(True, command, fixture, None, manifest)
        return Capability(False, command, fixture, "No SYSTEM demonstration grant covers this Site.")

    return check
