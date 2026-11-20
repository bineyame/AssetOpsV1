"""ON1 (spec `specs/ON1-operator-tenant/spec.md` §2, §3.2, §6 "File, no database"; D-ON1.10): the onboarding file.

Pure: no database, no settings. One planted refusal per rule of §2, each code once with its `where`; the roles digest
pinned as a literal.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from assetops_backend.onboarding.operator_file import (FORMAT, MAX_BYTES, OnboardRefused, parse_operator_file,
                                                      roles_digest, site_document, site_source)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "on1" / "lakeside-power.onboarding.json"
#: Computed once from the fixture (spec §6) and pinned.
DIGEST = "cfdfc54bf41514ef011e36de3da1734fbd5ae11a00a7bf76df0c23cbb6ab22a3"


def raw() -> dict:
    return json.loads(FIXTURE.read_bytes())


def data(doc: dict) -> bytes:
    return json.dumps(doc).encode("utf-8")


def refused(doc_or_bytes, code: str, where: str | None) -> OnboardRefused:
    payload = doc_or_bytes if isinstance(doc_or_bytes, bytes) else data(doc_or_bytes)
    with pytest.raises(OnboardRefused) as caught:
        parse_operator_file(payload)
    assert (caught.value.code, caught.value.where) == (code, where)
    return caught.value


def test_the_fixture_parses() -> None:
    f = parse_operator_file(FIXTURE.read_bytes())
    assert (f.format, f.data, f.slug, f.operator.name, f.operator.vertical) == (
        FORMAT, "emulated", "lakeside-power", "Lakeside Power", "MINI_GRID")
    assert [s.code for s in f.sites] == ["KISIWA-001", "KOBO-001", "MTO-001"]
    assert [p.name for p in f.people] == ["Amina", "Joseph", "Wanjiru", "Peter", "Halima", "David", "Musa"]
    assert f.people[3].roles == (("SITE_MANAGER", "KOBO-001"),)
    assert f.people[0].email_key == "amina@lakeside-power.example"


def _set(path, value):
    def plant(doc):
        target = doc
        for step in path[:-1]:
            target = target[step]
        target[path[-1]] = value
    return plant


def _people(*entries):
    def plant(doc):
        doc["people"] = [copy.deepcopy(e) for e in entries]
    return plant


def _person(index, **fields):
    def plant(doc):
        doc["people"][index].update(fields)
    return plant


AMINA = {"email": "amina@x.example", "name": "Amina", "roles": [{"role": "OPERATOR_EXECUTIVE"}]}
JOSEPH = {"email": "joseph@x.example", "name": "Joseph", "roles": [{"role": "FINANCE_AND_COMMERCIAL_LEAD"}]}
WANJIRU = {"email": "wanjiru@x.example", "name": "Wanjiru", "roles": [{"role": "ANALYST"}]}

#: One planted refusal per rule of spec §2 (each code once), with its `where`.
PLANTS = [
    ("format", _set(["format"], "assetops.operator-onboarding/2"), "ONBOARD_FORMAT", "format"),
    ("data", _set(["data"], "maybe"), "ONBOARD_DATA", "data"),
    ("slug", _set(["operator", "slug"], "demo"), "ONBOARD_SLUG", "operator.slug"),
    ("name", _set(["operator", "name"], " Lakeside"), "ONBOARD_NAME", "operator.name"),
    ("vertical", _set(["operator", "vertical"], "COLD_CHAIN"), "ONBOARD_VERTICAL", "operator.vertical"),
    ("site code", _set(["sites", 2, "code"], "kobo-001"), "ONBOARD_SITE_CODE", "sites[2].code"),
    ("site invalid", _set(["sites", 1, "lifecycle"], "SLEEPING"), "ONBOARD_SITE_INVALID", "sites[1]"),
    ("email", _person(4, email="not an email"), "ONBOARD_EMAIL", "people[4].email"),
    ("email duplicate", _person(5, email="PETER@lakeside-power.example"), "ONBOARD_EMAIL_DUPLICATE",
     "people[5].email"),
    ("role", _person(6, roles=[{"role": "JANITOR"}]), "ONBOARD_ROLE", "people[6].roles[0].role"),
    ("role site", _person(6, roles=[{"role": "FIELD_TECHNICIAN", "site": "KOBO-001"}]), "ONBOARD_ROLE_SITE",
     "people[6].roles[0]"),
    ("role duplicate", _person(6, roles=[{"role": "FIELD_TECHNICIAN"}, {"role": "FIELD_TECHNICIAN"}]),
     "ONBOARD_ROLE_DUPLICATE", "people[6].roles[1]"),
    ("executive count", _person(1, roles=[{"role": "OPERATOR_EXECUTIVE"}]), "ONBOARD_EXECUTIVE_COUNT", "people"),
    ("roles missing", _people(AMINA, JOSEPH), "ONBOARD_ROLES_MISSING", "people"),
    ("roles separate", _person(2, roles=[{"role": "ANALYST"}, {"role": "FINANCE_AND_COMMERCIAL_LEAD"}]),
     "ONBOARD_ROLES_SEPARATE", "people[2]"),
]


@pytest.mark.parametrize("plant,code,where", [p[1:] for p in PLANTS], ids=[p[0] for p in PLANTS])
def test_each_rule_refuses_with_its_place(plant, code, where) -> None:
    doc = raw()
    plant(doc)
    refused(doc, code, where)


def test_each_code_is_planted_once() -> None:
    codes = [p[2] for p in PLANTS]
    assert len(codes) == len(set(codes)) == 15


def test_a_site_manager_without_a_site_and_a_site_of_no_file_site() -> None:
    doc = raw()
    doc["people"][3]["roles"] = [{"role": "SITE_MANAGER"}]
    refused(doc, "ONBOARD_ROLE_SITE", "people[3].roles[0]")
    doc["people"][3]["roles"] = [{"role": "SITE_MANAGER", "site": "NOWHERE-001"}]
    refused(doc, "ONBOARD_ROLE_SITE", "people[3].roles[0]")


def test_the_analyst_is_never_the_executive() -> None:
    doc = raw()
    doc["people"][0]["roles"].append({"role": "ANALYST"})
    refused(doc, "ONBOARD_ROLES_SEPARATE", "people[0]")


def test_wanjiru_given_the_finance_role_is_refused_and_each_submitter_differs_from_every_accepter() -> None:
    doc = raw()
    doc["people"][2]["roles"].append({"role": "FINANCE_AND_COMMERCIAL_LEAD"})
    refused(doc, "ONBOARD_ROLES_SEPARATE", "people[2]")
    f = parse_operator_file(FIXTURE.read_bytes())
    submit = {p.email_key for p in f.people if any(r == "ANALYST" for r, _ in p.roles)}
    accept = {p.email_key for p in f.people
              if any(r in ("FINANCE_AND_COMMERCIAL_LEAD", "OPERATOR_EXECUTIVE") for r, _ in p.roles)}
    assert submit and accept and not submit & accept


def test_site_invalid_prints_no_value() -> None:
    doc = raw()
    doc["sites"][1]["components"][0]["type"] = "Secret-Value-42"
    error = refused(doc, "ONBOARD_SITE_INVALID", "sites[1]")
    assert "Secret" not in str(error) and "Secret" not in repr(error.args)
    assert error.__cause__ is None and error.__context__ is None


@pytest.mark.parametrize("level,where", [
    ([], ""), (["operator"], "operator"), (["sites", 0], "sites[0]"), (["sites", 0, "components", 1],
                                                                       "sites[0].components[1]"),
    (["people", 2], "people[2]"), (["people", 2, "roles", 0], "people[2].roles[0]"),
])
def test_an_unknown_key_at_each_level(level, where) -> None:
    doc = raw()
    target = doc
    for step in level:
        target = target[step]
    target["extra"] = 1
    refused(doc, "ONBOARD_FORMAT", where or None)


def test_a_missing_key_is_refused() -> None:
    doc = raw()
    del doc["sites"][0]["locality"]
    refused(doc, "ONBOARD_FORMAT", "sites[0]")


def test_a_duplicate_json_key_is_refused() -> None:
    text = FIXTURE.read_text(encoding="utf-8").replace('"data": "emulated",', '"data": "emulated", "data": "real",', 1)
    assert text.count('"data"') == 2
    refused(text.encode("utf-8"), "ONBOARD_FILE", None)


def test_size_limit_and_unreadable_files() -> None:
    body = data(raw())
    padded = body[:-1] + b" " * (MAX_BYTES - len(body)) + b"}"
    assert len(padded) == MAX_BYTES and parse_operator_file(padded).slug == "lakeside-power"
    over = body[:-1] + b" " * (MAX_BYTES + 1 - len(body)) + b"}"
    assert len(over) == 262145
    refused(over, "ONBOARD_FILE", None)
    refused(b"{not json", "ONBOARD_FILE", None)
    refused(b"[1, 2]", "ONBOARD_FILE", None)
    refused(b"\xff\xfe{}", "ONBOARD_FILE", None)


def test_the_roles_digest_is_pinned() -> None:
    assert roles_digest(parse_operator_file(FIXTURE.read_bytes())) == DIGEST


@pytest.mark.parametrize("change", ["role", "role site", "name", "email"])
def test_the_digest_changes_with_any_role_name_or_email(change) -> None:
    doc = raw()
    if change == "role":
        doc["people"][6]["roles"] = [{"role": "SITE_MANAGER", "site": "MTO-001"}]
    elif change == "role site":
        doc["people"][3]["roles"] = [{"role": "SITE_MANAGER", "site": "MTO-001"}]
    elif change == "name":
        doc["people"][6]["name"] = "Musa K"
    else:
        doc["people"][6]["email"] = "musa.k@lakeside-power.example"
    assert roles_digest(parse_operator_file(data(doc))) != DIGEST


def test_the_digest_ignores_site_components_and_email_case() -> None:
    doc = raw()
    doc["sites"][1]["components"][0]["rating"]["value"] = 61.0
    doc["people"][0]["email"] = "Amina@Lakeside-Power.example"
    assert roles_digest(parse_operator_file(data(doc))) == DIGEST


def test_the_site_document_and_its_source() -> None:
    f = parse_operator_file(FIXTURE.read_bytes())
    kobo = f.sites[1]
    document = site_document(kobo, real=False)
    assert document["site_id"] == "KOBO-001" and document["site_type"] == "MINIGRID"
    assert document["source"] == {"mode": "SIMULATED"} and document["origin"] == "USER"
    assert site_document(kobo, real=True)["source"] == {"mode": "LIVE"}
    assert [c["component_id"] for c in document["foundation"]["components"]] == [
        "pv-array", "inverter", "battery", "generator"]
    source = site_source(f, kobo)
    assert source.path == "onboarding:lakeside-power/KOBO-001"
    assert source.document_format == "ASSETOPS_ONBOARDING_JSON"
    assert source.record.site_id == "KOBO-001"
    # A Site's digest depends on its own entry only.
    doc = raw()
    doc["sites"].append(copy.deepcopy(doc["sites"][2]) | {"code": "NEW-001"})
    later = parse_operator_file(data(doc))
    assert site_source(later, later.sites[1]).sha256 == source.sha256
