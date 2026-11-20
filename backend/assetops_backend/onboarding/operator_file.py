"""ON1 (spec §2, §3.2; D-ON1.1, D-ON1.2, D-ON1.8, D-ON1.10): the operator onboarding file, `assetops.operator-onboarding/1`.

Pure: no I/O. `parse_operator_file(data)` reads the bytes strictly (an unknown, missing or duplicate key is refused at
every level) and answers an `OperatorFile`, or raises `OnboardRefused(code, where)`: `where` is a JSON path such as
`sites[2].code`, never a value. `roles_digest` is what the executive confirms (D-ON1.10). `site_document` and
`site_source` build the Site document the existing Site import takes (D-ON1.2).

Structure (D-ON1.18): `format` is read first; absent or not version 1 is `ONBOARD_FORMAT`. After that a container of
the wrong JSON type, an unknown or missing key, or a list outside its bounds (`sites` and `people` 1 to 50, `roles`
1 to 5) is `ONBOARD_STRUCTURE` at that object's path.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from assetops_backend.accounts import passwords
from assetops_backend.accounts.model import AccountRefused, EXECUTIVE, ROLES, SITE_ROLE
from assetops_backend.sites.foundation_records import TenantRef
from assetops_backend.sites.foundation_service import ImportSource, plan_import
from assetops_backend.sites.site_parsing import parse_site_document

FORMAT = "assetops.operator-onboarding/1"
MAX_BYTES = 262144
DOCUMENT_FORMAT = "ASSETOPS_ONBOARDING_JSON"
FINANCE = "FINANCE_AND_COMMERCIAL_LEAD"
ANALYST = "ANALYST"
_SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
_SITE_CODE = re.compile(r"[A-Z0-9][A-Z0-9-]{0,63}")
_TOP = ("format", "data", "operator", "sites", "people")
_OPERATOR = ("slug", "name", "vertical")
_SITE = ("code", "name", "timezone", "country", "locality", "lifecycle", "valid_from", "components")
_COMPONENT = ("id", "type", "name", "rating")
_PERSON = ("email", "name", "roles")
#: A placeholder tenant: `plan_import` is pure and only copies the tenant's id into the plan it builds.
_CHECK_TENANT = TenantRef(UUID(int=0), "check", "check")
_CHECK_NOW = datetime(2000, 1, 1, tzinfo=timezone.utc)


class OnboardRefused(Exception):
    """A refusal: its code and the place in the file (a JSON path, never a value). No other field."""

    def __init__(self, code: str, where: str | None = None) -> None:
        super().__init__(code, where)
        self.code = code
        self.where = where


@dataclass(frozen=True)
class Operator:
    slug: str
    name: str
    vertical: str


@dataclass(frozen=True)
class SiteEntry:
    index: int
    code: str
    entry: Any  # the file's own site object, as parsed (read only)


@dataclass(frozen=True)
class PersonEntry:
    index: int
    email: str
    email_key: str
    name: str
    roles: tuple[tuple[str, str | None], ...]  # (role, Site code or None), in file order

    @property
    def executive(self) -> bool:
        return any(role == EXECUTIVE for role, _ in self.roles)


@dataclass(frozen=True)
class OperatorFile:
    format: str
    data: str
    operator: Operator
    sites: tuple[SiteEntry, ...]
    people: tuple[PersonEntry, ...]

    @property
    def slug(self) -> str:
        return self.operator.slug

    @property
    def real(self) -> bool:
        return self.data == "real"


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise OnboardRefused("ONBOARD_FILE")
        out[key] = value
    return out


def _strict(value: Any, keys: tuple[str, ...], where: str | None, optional: tuple[str, ...] = ()) -> dict:
    if not isinstance(value, dict):
        raise OnboardRefused("ONBOARD_STRUCTURE", where)
    present = set(value)
    if not set(keys) <= present or not present <= set(keys) | set(optional):
        raise OnboardRefused("ONBOARD_STRUCTURE", where)
    return value


def _list(value: Any, low: int, high: int, where: str) -> list:
    if not isinstance(value, list) or not low <= len(value) <= high:
        raise OnboardRefused("ONBOARD_STRUCTURE", where)
    return value


def _name(value: Any, where: str) -> str:
    if not isinstance(value, str) or value != value.strip() or not 1 <= len(value) <= 120:
        raise OnboardRefused("ONBOARD_NAME", where)
    return value


def site_document(site: SiteEntry, *, real: bool) -> dict:
    """Spec §3.2: the Site document of one file Site."""
    e = site.entry
    return {
        "site_id": e["code"], "display_name": e["name"], "site_type": "MINIGRID",
        "location": {"country": e["country"], "locality": e["locality"]}, "timezone": e["timezone"],
        "lifecycle_status": e["lifecycle"], "origin": "USER", "source": {"mode": "LIVE" if real else "SIMULATED"},
        "foundation": {"version": 1, "valid_from": e["valid_from"],
                       "summary": "Onboarded from the operator's onboarding file.",
                       "components": [{"component_id": c["id"], "component_type": c["type"],
                                       "display_name": c["name"], "rating": c["rating"]}
                                      for c in e["components"]]},
    }


def site_source(f: OperatorFile, site: SiteEntry) -> ImportSource:
    """Spec §3.2: the Site's `ImportSource`; its sha256 depends on its own entry only."""
    document = site_document(site, real=f.real)
    path = f"onboarding:{f.slug}/{site.code}"
    digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=False).encode("utf-8")).hexdigest()
    return ImportSource(path=path, sha256=digest, record=parse_site_document(document, source=path),
                        document_format=DOCUMENT_FORMAT)


def roles_digest(f: OperatorFile) -> str:
    """D-ON1.10: SHA-256 of the canonical JSON of the slug and each person's email key, name and sorted roles."""
    people = sorted(([p.email_key, p.name, sorted([role, site or ""] for role, site in p.roles)] for p in f.people),
                    key=lambda entry: entry[0])
    text = json.dumps({"operator": f.slug, "people": people}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sites(value: Any, operator: Operator, data: str) -> tuple[SiteEntry, ...]:
    sites: list[SiteEntry] = []
    seen: set[str] = set()
    for i, entry in enumerate(_list(value, 1, 50, "sites")):
        where = f"sites[{i}]"
        _strict(entry, _SITE, where)
        code = entry["code"]
        if not isinstance(code, str) or _SITE_CODE.fullmatch(code) is None or code.lower() in seen:
            raise OnboardRefused("ONBOARD_SITE_CODE", f"{where}.code")
        seen.add(code.lower())
        components = entry["components"]
        if not isinstance(components, list):
            raise OnboardRefused("ONBOARD_STRUCTURE", f"{where}.components")
        for j, component in enumerate(components):
            _strict(component, _COMPONENT, f"{where}.components[{j}]")
        sites.append(SiteEntry(i, code, entry))
    probe = OperatorFile(FORMAT, data, operator, tuple(sites), ())
    for site in sites:
        refused = False
        try:  # the parser's and the planner's messages may quote a value: neither is kept (spec §2)
            plan_import(_CHECK_TENANT, site_source(probe, site), _CHECK_NOW)
        except Exception:  # noqa: BLE001 - any refusal of the Site document is the one plain code
            refused = True
        if refused:  # raised outside the handler, so no message travels as context
            raise OnboardRefused("ONBOARD_SITE_INVALID", f"sites[{site.index}]")
    return tuple(sites)


def _people(value: Any, site_codes: set[str]) -> tuple[PersonEntry, ...]:
    people: list[PersonEntry] = []
    keys: set[str] = set()
    for i, entry in enumerate(_list(value, 1, 50, "people")):
        where = f"people[{i}]"
        _strict(entry, _PERSON, where)
        email = entry["email"]
        bad = not isinstance(email, str)
        if not bad:
            try:
                email, key = passwords.normalise_email(email)
            except AccountRefused:
                bad = True
        if bad:
            raise OnboardRefused("ONBOARD_EMAIL", f"{where}.email")
        if key in keys:
            raise OnboardRefused("ONBOARD_EMAIL_DUPLICATE", f"{where}.email")
        keys.add(key)
        name = _name(entry["name"], f"{where}.name")
        roles: list[tuple[str, str | None]] = []
        for j, grant in enumerate(_list(entry["roles"], 1, 5, f"{where}.roles")):
            at = f"{where}.roles[{j}]"
            _strict(grant, ("role",), at, optional=("site",))
            role = grant["role"]
            if role not in ROLES:
                raise OnboardRefused("ONBOARD_ROLE", f"{at}.role")
            site = grant.get("site")
            if (role == SITE_ROLE) != ("site" in grant) or (site is not None and site not in site_codes):
                raise OnboardRefused("ONBOARD_ROLE_SITE", at)
            if (role, site) in roles:
                raise OnboardRefused("ONBOARD_ROLE_DUPLICATE", at)
            roles.append((role, site))
        people.append(PersonEntry(i, email, key, name, tuple(roles)))
    if sum(p.executive for p in people) != 1:
        raise OnboardRefused("ONBOARD_EXECUTIVE_COUNT", "people")
    held = [{role for role, _ in p.roles} for p in people]
    if not any(FINANCE in r for r in held) or not any(ANALYST in r for r in held):
        raise OnboardRefused("ONBOARD_ROLES_MISSING", "people")
    for p, roles_held in zip(people, held):
        if ANALYST in roles_held and roles_held & {FINANCE, EXECUTIVE}:
            raise OnboardRefused("ONBOARD_ROLES_SEPARATE", f"people[{p.index}]")
    return tuple(people)


def parse_operator_file(data: bytes) -> OperatorFile:
    if not isinstance(data, (bytes, bytearray)) or len(data) > MAX_BYTES:
        raise OnboardRefused("ONBOARD_FILE")
    unreadable = False
    try:
        doc = json.loads(bytes(data).decode("utf-8"), object_pairs_hook=_object_pairs)
    except OnboardRefused:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError):
        unreadable = True
    if unreadable or not isinstance(doc, dict):
        raise OnboardRefused("ONBOARD_FILE")
    if doc.get("format") != FORMAT:
        raise OnboardRefused("ONBOARD_FORMAT", "format")
    _strict(doc, _TOP, None)
    if doc["data"] not in ("emulated", "real"):
        raise OnboardRefused("ONBOARD_DATA", "data")
    op = _strict(doc["operator"], _OPERATOR, "operator")
    if not isinstance(op["slug"], str) or _SLUG.fullmatch(op["slug"]) is None or op["slug"] == "demo":
        raise OnboardRefused("ONBOARD_SLUG", "operator.slug")
    operator = Operator(op["slug"], _name(op["name"], "operator.name"), op["vertical"])
    if op["vertical"] != "MINI_GRID":
        raise OnboardRefused("ONBOARD_VERTICAL", "operator.vertical")
    sites = _sites(doc["sites"], operator, doc["data"])
    people = _people(doc["people"], {s.code for s in sites})
    return OperatorFile(FORMAT, doc["data"], operator, sites, people)
