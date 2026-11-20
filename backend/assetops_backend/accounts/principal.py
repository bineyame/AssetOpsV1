"""3C0a (D-3C0A.9): the seam `3C1` uses to turn a request into the signed-in person.

`person_from_request` reads the `assetops_session` cookie and resolves it; it never reads a header, query or body
value naming a person. Store errors propagate (the caller answers them as unavailable).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.requests import Request

from assetops_backend.accounts.model import COOKIE, PersonPrincipal

if TYPE_CHECKING:
    from assetops_backend.accounts.service import AccountService


def person_from_request(request: Request, accounts: "AccountService") -> PersonPrincipal | None:
    return accounts.resolve(request.cookies.get(COOKIE))
