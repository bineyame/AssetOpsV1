"""DIESEL-1-R3f §9f.2 (5): the file adapter behind `OperationalActionLogPort`.

A Site's operational-action log is a versioned, Lab-private YAML file read by run setup only, by an exact
`{log_id}-v{log_version}.yaml` name and never as "latest". This module is the only place under the backend package
that names the directory. The product never reads the log: operator records reach the product through the Work
API, and the unrecorded removal stays private world truth.

`kisiwa-001-operational-actions-v1.yaml` is F0's pre-registered draft log promoted byte-for-byte, so its header
comment (which still says "DRAFT" and names the file `kisiwa-001-v1.yaml`) predates ruling DIESEL-1-R3c §9c.3 L1's
file name and is kept verbatim.

The hash is taken over the text read as UTF-8 and re-encoded, so a CRLF checkout hashes as its LF blob (the F0e
rule, DIESEL-1-R3e); `.gitattributes` keeps the directory LF on every host as well. YAML is read with libyaml's
`CSafeLoader`, the run domain's one loader policy (D-2026-09-29-run-store-libyaml).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from assetops_backend.runs.adapters.yaml_run_documents import CSafeLoader
from assetops_backend.runs.ports import (
    OperationalActionLogSource,
    OperationalActionLogUnavailable,
)

REPO_ROOT = Path(__file__).resolve().parents[4]

#: Where shipped operational-action logs live. Read-only at runtime.
DEFAULT_OPERATIONAL_ACTIONS_ROOT = REPO_ROOT / "config" / "operational-actions"

#: A log is small; a larger file is not one this build wrote.
MAX_LOG_BYTES = 1_000_000


class YamlOperationalActionLog:
    """Reads `{root}/{log_id}-v{log_version}.yaml`; any failure is `OperationalActionLogUnavailable`."""

    def __init__(self, root: Path = DEFAULT_OPERATIONAL_ACTIONS_ROOT) -> None:
        self._root = root

    def read_log(self, log_id: str, log_version: int) -> OperationalActionLogSource:
        name = f"{log_id}-v{log_version}.yaml"
        path = self._root / name
        try:
            if path.stat().st_size > MAX_LOG_BYTES:
                raise OperationalActionLogUnavailable(f"Operational-action log {name} is above {MAX_LOG_BYTES} bytes.")
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise OperationalActionLogUnavailable(f"Operational-action log {name} is not valid UTF-8.") from error
        except OSError as error:
            raise OperationalActionLogUnavailable(
                f"Operational-action log {name} could not be read: there is no such log version.") from error
        try:
            document = yaml.load(text, Loader=CSafeLoader)
        except yaml.YAMLError as error:
            raise OperationalActionLogUnavailable(f"Operational-action log {name} is not valid YAML.") from error
        if not isinstance(document, dict):
            raise OperationalActionLogUnavailable(f"Operational-action log {name} is not a mapping.")
        return OperationalActionLogSource(sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), document=document)
