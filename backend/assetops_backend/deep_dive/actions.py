"""5c (spec section 4.3; D-5C.8): the seam 3C2 fills. The deep-dive reads the agreed change through this port only.

Unit 2 of 3C2 connects the store here (`StoreAgreedActions`); `NotConnectedActions` stays for the in-memory tests.
"""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from assetops_backend.actions.agreed import AgreedActionService
from assetops_backend.deep_dive.view import AgreedAction, AgreedActions


class AgreedActionsPort(Protocol):
    def for_tenant(self, tenant_id: UUID) -> AgreedActions: ...


class NotConnectedActions:
    """Until 3C2 merges into this seam: no agreed Action is read."""

    def for_tenant(self, tenant_id: UUID) -> AgreedActions:
        return AgreedActions(False, ())


class StoreAgreedActions:
    """3C2 unit 2 (spec section 3): the agreed-action store through the port, newest first as the service gives them."""

    def __init__(self, service: AgreedActionService) -> None:
        self._service = service

    def for_tenant(self, tenant_id: UUID) -> AgreedActions:
        return AgreedActions(True, tuple(
            AgreedAction(str(v.action_id), v.title, v.site_code, v.factor_id, v.owner_name, v.created_by_name,
                         v.created_at, v.due_on, v.state_words)
            for v in self._service.for_tenant(tenant_id)))


__all__ = ["AgreedAction", "AgreedActions", "AgreedActionsPort", "NotConnectedActions", "StoreAgreedActions"]
