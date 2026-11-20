"""3A2 (spec §3.4; D-3A2.5, D-3A2.14; R10, R11, R12, P5): pseudonyms for customer, meter and person identifiers.

- `pseudonym(key, cls, value)` is `<cls>-` plus the first 32 hex digits of HMAC-SHA256 over `<cls>\\x1f<value>` with
  the tenant's 32-byte key: deterministic per tenant, so a repeated file is UNCHANGED and one customer links across
  billing, payments and the meter register.
- `PERSONAL_FIELDS` is the literal per-kind table of spec §3.4; `pseudonymise` applies it, plus a reader's declared
  extra paths (only from `ALLOWED_EXTRA`), to one record object that 2a accepted. A refused record is never
  pseudonymised: it is dropped and kept only as its code and cut path (D-3A2.14).
- `cut_path` cuts a path that can echo a key the operator wrote (`CANONICAL_FORBIDDEN`, any `json.` path) to its
  longest known parent, so a refusal path never carries the operator's text.
- `PseudonymKeys` is the key port. Its file adapter, `adapters/file_key_store.py` (`FileKeyStore`, and the key
  command's `create_key_file`), reads `<dir>/<tenant_id>.key`; the key never sits in the database. Erasure is
  deleting the file. (The file I/O sits in an adapter, as rule 8 of the persistence guard requires.)

Nothing here logs or raises with a value: `ValueError` names the bad path or class only (a reader bug).
"""
from __future__ import annotations

import copy
import hashlib
import hmac
from typing import Mapping, Protocol
from uuid import UUID

CLASSES = frozenset({"C", "M", "P"})

#: Spec §3.4: per kind, (path, class, condition). A condition is (path, allowed values) or None.
PERSONAL_FIELDS: Mapping[str, tuple[tuple[str, str, tuple[str, frozenset[str]] | None], ...]] = {
    "CHARGE": (("subject.ref", "C", ("subject.kind", frozenset({"CUSTOMER"}))),
               ("subject.ref", "M", ("subject.kind", frozenset({"METER"}))),
               ("body.account_ref", "C", None)),
    "RECEIPT": (("subject.ref", "C", None),
                ("body.payer_ref", "C", None)),
    "ADJUSTMENT": (("subject.ref", "C", ("subject.kind", frozenset({"CUSTOMER"}))),
                   ("subject.ref", "M", ("subject.kind", frozenset({"METER"}))),
                   ("body.authorised_by_ref", "P", None)),
    "EXPENSE": (("body.counterparty_ref", "P", ("body.category", frozenset({"STAFF", "COLLECTION"}))),),
    "STORAGE_MOVEMENT": (("body.customer_ref", "C", None),),
    "CUSTOMER_METER_READ": (("subject.ref", "M", None),
                            ("body.meter_ref", "M", None)),
    "METER_ASSIGNMENT": (("subject.ref", "M", None),
                         ("body.meter_ref", "M", None),
                         ("body.customer_ref", "C", None)),
    "FLEET_ROSTER": (("body.tag_ref", "P", None),),
}

#: P5: the body fields 2a types `ref`, over every kind (service test 16 checks this literal against 2a's table).
REF_BODY_FIELDS = frozenset({
    "account_ref", "asset_ref", "authorised_by_ref", "band", "batch_ref", "block_ref", "commodity", "contract_ref",
    "correction_reason", "counterparty_ref", "customer_ref", "document_ref", "line_ref", "meter_ref", "payer_ref",
    "provider", "reason_code", "tag_ref", "tariff_code", "vehicle_ref", "version_ref",
})
ALLOWED_EXTRA = frozenset({"source_record_id", "subject.ref"} | {f"body.{n}" for n in REF_BODY_FIELDS})

#: D-3A2.14: the known parents a refusal path may be cut to.
CUT_PARENTS = ("json", "batch", "record", "record.subject", "record.clocks", "record.amount", "record.quantity",
               "record.body")


def cut_path(code: str, path: str) -> str:
    """For `CANONICAL_FORBIDDEN` and any `json.` path, the longest known parent equal to or prefixing the path with a
    dot; any other path unchanged."""
    if code != "CANONICAL_FORBIDDEN" and not path.startswith("json."):
        return path
    best = None
    for parent in CUT_PARENTS:
        if (path == parent or path.startswith(parent + ".")) and (best is None or len(parent) > len(best)):
            best = parent
    return best if best is not None else "json"


def pseudonym(key: bytes, cls: str, value: str) -> str:
    return f"{cls}-" + hmac.new(key, f"{cls}\x1f{value}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _get(obj: dict, path: str):
    node: object = obj
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _set(obj: dict, path: str, value: str) -> None:
    *parents, last = path.split(".")
    node = obj
    for part in parents:
        node = node[part]
    node[last] = value


def pseudonymise(record: object, key: bytes, extra: frozenset[tuple[str, str]] = frozenset()) -> object:
    """One kept record object in, a new object out (the input is not mutated). Each personal string value is replaced
    by its pseudonym; an absent or non-string value is left as it is (2a accepted the record, so a present ref is a
    string)."""
    for path, cls in extra:
        if path not in ALLOWED_EXTRA:
            raise ValueError(f"a reader may not declare the personal path {path!r}")
        if cls not in CLASSES:
            raise ValueError(f"unknown pseudonym class {cls!r}")
    out = copy.deepcopy(record)
    if not isinstance(out, dict):
        return out
    targets: list[tuple[str, str]] = []
    for path, cls, condition in PERSONAL_FIELDS.get(out.get("kind"), ()):
        if condition is not None and _get(out, condition[0]) not in condition[1]:
            continue
        targets.append((path, cls))
    targets.extend(sorted(extra))
    done: set[str] = set()
    for path, cls in targets:
        if path in done:
            continue
        value = _get(out, path)
        if isinstance(value, str):
            _set(out, path, pseudonym(key, cls, value))
            done.add(path)
    return out


# --- the key store --------------------------------------------------------------------------------------------------



class PseudonymKeyMissing(Exception):
    """No key file for the tenant: the organisation is not set up to receive exports."""


class PseudonymKeyErased(Exception):
    """ON1 (D-ON1.7): the tenant's key was erased (a tombstone stands); its exports are no longer received."""


class PseudonymKeyUnusable(Exception):
    """The key file is a symlink, not exactly 32 bytes, or readable by group or others."""


class PseudonymKeys(Protocol):
    def key(self, tenant_id: UUID) -> bytes:
        """The tenant's 32-byte key; `PseudonymKeyMissing` or `PseudonymKeyUnusable` otherwise."""
