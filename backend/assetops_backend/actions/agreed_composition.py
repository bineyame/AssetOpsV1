"""3C2: re-exports the agreed-change composition, which lives in `actions/composition.py` (D-3C2.15). Imports no adapter."""
from assetops_backend.actions.composition import AgreedActionsService, build_agreed_actions

__all__ = ["AgreedActionsService", "build_agreed_actions"]
