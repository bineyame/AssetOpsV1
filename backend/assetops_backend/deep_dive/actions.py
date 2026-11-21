"""5c (spec section 4.3; D-5C.8): the seam 3C2 fills. The deep-dive reads the agreed change through this port only.

Until 3C2's store is connected here (its unit 2 adds `StoreAgreedActions`, mapping its views to `AgreedAction`, and
replaces `NotConnectedActions()` in `deep_dive/composition.py`, one line), the panel reads "Not available yet".
"""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from assetops_backend.deep_dive.view import AgreedAction, AgreedActions


class AgreedActionsPort(Protocol):
    def for_tenant(self, tenant_id: UUID) -> AgreedActions: ...


class NotConnectedActions:
    """Until 3C2 merges into this seam: no agreed Action is read."""

    def for_tenant(self, tenant_id: UUID) -> AgreedActions:
        return AgreedActions(False, ())


__all__ = ["AgreedAction", "AgreedActions", "AgreedActionsPort", "NotConnectedActions"]
