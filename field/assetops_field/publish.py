"""The field adapter's side of the gateway channel (ruling D4 item 5, Q-T28, Q-T29, Q-T32).

Only the ops in `OPS_USED` are called. Activation is a provisioning act and
upload is the gateway's background uploader, so neither is reachable here.
`HELD` admissions are data and are returned verbatim; a whole-request refusal
propagates to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from assetops_gateway.ipc import GatewayLink, GatewayRequestRefused

OPS_USED = ("identity", "admit", "seal", "release_run", "diagnostics")
ADMISSION_CHUNK = 256  # below the gateway's 1024; a smaller chunk is always accepted
SOURCE_MODE = "SIMULATED"
_COMPARED = ("tenant_id", "site_id", "gateway_id", "sequence_epoch")


class IdentityMismatch(RuntimeError):
    """The gateway is not the one this adapter was configured for; nothing is admitted."""


@dataclass
class GatewayPublisher:
    link: GatewayLink
    snapshot_sha256: str
    session_ref: str
    expected: Mapping[str, Any]

    def _call(self, op: str, body: dict[str, Any] | None = None) -> Any:
        if op not in OPS_USED:
            raise ValueError(f"a field adapter never calls {op!r}")
        return self.link.call(op, body)

    def check_identity(self) -> dict[str, Any]:
        identity = self._call("identity")
        for key in _COMPARED:
            if identity.get(key) != self.expected.get(key):
                raise IdentityMismatch(f"{key}: gateway {identity.get(key)!r}, expected {self.expected.get(key)!r}")
        if identity.get("source_mode") != SOURCE_MODE:
            raise IdentityMismatch(f"source_mode: gateway {identity.get('source_mode')!r}, expected {SOURCE_MODE!r}")
        permitted = set(identity.get("permitted_source_ids") or ())
        for signal, source_id in sorted(self.expected["row_sources"].items()):
            if source_id not in permitted:
                raise IdentityMismatch(f"row_sources.{signal}: {source_id!r} is not a permitted source")
        return identity

    def admit(self, texts: Sequence[str]) -> list[dict[str, Any]]:
        admissions: list[dict[str, Any]] = []
        for first in range(0, len(texts), ADMISSION_CHUNK):
            body = {
                "snapshot_sha256": self.snapshot_sha256,
                "lab_run_ref": self.session_ref,
                "reports": list(texts[first:first + ADMISSION_CHUNK]),
            }
            admissions.extend(self._call("admit", body)["admissions"])
        return admissions

    def seal_and_release(self) -> dict[str, Any]:
        seal_refused = None
        batch_ids: list[str] = []
        try:
            batch_ids = list(self._call("seal")["batch_ids"])
        except GatewayRequestRefused as refused:
            # SEAL_REFUSED is raised after the gateway committed every other
            # group, so what did seal is still released below.
            if refused.kind != "SEAL_REFUSED":
                raise
            seal_refused = refused.detail
        released = self._call("release_run", {"lab_run_ref": self.session_ref})
        return {
            "batch_ids": batch_ids,
            "seal_refused": seal_refused,
            "released_batch_ids": released["released_batch_ids"],
            "released_now": released["released_now"],
            "delivery": released["delivery"],
        }

    def release_previous(self, previous_ref: str) -> dict[str, Any]:
        """Seal first, then release the previous session, before any new admission (Q-T28)."""
        sealed = list(self._call("seal")["batch_ids"])
        released = self._call("release_run", {"lab_run_ref": previous_ref})
        return {
            "sealed_batch_ids": sealed,
            "released_batch_ids": released["released_batch_ids"],
            "released_now": released["released_now"],
        }

    def diagnostics(self) -> dict[str, Any]:
        return self._call("diagnostics")
