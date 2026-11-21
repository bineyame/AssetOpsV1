"""3C1a (`specs/3C1-person-on-commands/spec.md` §2-§3; D-3C1.1, .2, .6, .10, .12; R5, R6, R9-R11): the person step.

`person_step` runs after a command route's own Site-scope check and decides, for one command, whether the request
is today's unsigned path (None), the signed-in person's path (a `PersonGrant` naming the admitting role), or refused
(`PersonRefused`, which each route answers with its own envelope and codes, R9):

1. Find the person from the session cookie when an account service is composed; with none composed nobody is
   signed in (R10). An account-store error is `UNAVAILABLE`, even with the switch off. An expired or revoked
   cookie resolves to no person (R11).
2. No person: `PERSON_REQUIRED` when `ASSETOPS_REQUIRE_PERSON` is on, else today's path.
3. A person: another tenant is `TENANT` (the route's unknown-Site 404, D-3C1.6); a closed feature switch or absent
   gate principal is `FEATURE_OFF` (the route's own 403, D-3C1.12); a person without one of the command's roles is
   `PERSON_ROLE_REQUIRED`. Only a Site manager's grant is bound to a Site (R5e). The admitting role is the first of
   the command's roles, in `COMMAND_ROLES` order, that the person holds.

The tenant check precedes the feature check, as the unknown-Site 404 precedes the write refusals on every route
today, so a person of another tenant never learns more than "not found".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

from starlette.requests import Request

from assetops_backend.accounts.principal import person_from_request

if TYPE_CHECKING:
    from assetops_backend.accounts.service import AccountService

SITE_MANAGER = "SITE_MANAGER"
FIELD_TECHNICIAN = "FIELD_TECHNICIAN"
FINANCE = "FINANCE_AND_COMMERCIAL_LEAD"
ANALYST = "ANALYST"
EXECUTIVE = "OPERATOR_EXECUTIVE"

#: D-3C1.2 as amended (R5, D-3C1.10): one literal table, command key -> roles in admitting order.
COMMAND_ROLES: dict[str, tuple[str, ...]] = {
    "work.case_create": (SITE_MANAGER, FIELD_TECHNICIAN),
    "work.case_event.COMPLETE": (SITE_MANAGER, FIELD_TECHNICIAN),
    "work.case_event.COMMENT": (SITE_MANAGER, FIELD_TECHNICIAN),
    "work.case_event.ASSIGN": (SITE_MANAGER,),
    "work.case_event.CLOSE": (SITE_MANAGER,),
    "work.case_event.REOPEN": (SITE_MANAGER,),
    "work.case_event.CANCEL": (SITE_MANAGER,),
    "work.case_revision": (SITE_MANAGER,),
    "work.maintenance_record": (FIELD_TECHNICIAN, SITE_MANAGER),
    "work.maintenance_plan": (SITE_MANAGER,),
    "work.operational_record": (FIELD_TECHNICIAN, SITE_MANAGER),
    "work.operational_entry": (FIELD_TECHNICIAN, SITE_MANAGER),
    "domain.create": (SITE_MANAGER, FINANCE),
    "domain.intent": (SITE_MANAGER, FINANCE),
    "domain.case_link": (SITE_MANAGER,),
    # 3A2 (spec §3.1, D-3A2.9): commercial uploads; always a signed-in person (the routes pass required=True).
    "commercial.upload": (ANALYST, FINANCE),
    "commercial.upload_decision": (FINANCE, EXECUTIVE),
    "commercial.upload_read": (ANALYST, FINANCE, EXECUTIVE, SITE_MANAGER),
    "commercial.profile_admit": (ANALYST, FINANCE),  # 3A6 (spec §2.7; queue Q2)
}
#: §3: a case event kind not listed above (any other kind) admits the Site manager only.
OTHER_EVENT_ROLES: tuple[str, ...] = (SITE_MANAGER,)
EVENT_PREFIX = "work.case_event."


def case_event_command(body: Any) -> str:
    """The case-event command key, by the body's event kind (§3); a missing or unknown kind is an "other kind"."""
    kind = body.get("kind") if isinstance(body, dict) else None
    return f"{EVENT_PREFIX}{kind}" if isinstance(kind, str) else f"{EVENT_PREFIX}?"


def roles_of(command: str) -> tuple[str, ...]:
    roles = COMMAND_ROLES.get(command)
    if roles is not None:
        return roles
    if command.startswith(EVENT_PREFIX):
        return OTHER_EVENT_ROLES
    raise KeyError(f"no roles for command {command!r}")


@dataclass(frozen=True)
class PersonGrant:
    """The admitted person and the role that admitted them, for the server-composed actor."""
    person_id: UUID
    session_id: UUID
    role: str


class PersonRefused(Exception):
    """`reason` is UNAVAILABLE, PERSON_REQUIRED, TENANT, FEATURE_OFF or PERSON_ROLE_REQUIRED; each route answers it
    with its own codes and envelope (R9)."""

    def __init__(self, reason: str, params: dict[str, Any] | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.params = dict(params or {})


def person_step(request: Request, accounts: "AccountService | None", *, required: bool,
                unavailable: tuple[type, ...], tenant_id: UUID, site_id: UUID | None, command: str,
                enabled: bool) -> PersonGrant | None:
    roles = roles_of(command)  # an unknown command is a programming error, before any store read
    person = None
    if accounts is not None:
        try:
            person = person_from_request(request, accounts)
        except unavailable as error:
            raise PersonRefused("UNAVAILABLE") from error
    if person is None:
        if required:
            raise PersonRefused("PERSON_REQUIRED")
        return None
    if person.tenant_id != tenant_id:
        raise PersonRefused("TENANT")
    if not enabled:
        raise PersonRefused("FEATURE_OFF")
    for role in roles:
        if person.has_role(role, site_id):
            return PersonGrant(person.person_id, person.session_id, role)
    raise PersonRefused("PERSON_ROLE_REQUIRED", {"roles": list(roles)})
