"""3A7 M1 to M5 (spec §5, §6.1's JSON shapes, §7 "Command, no database"; D-3A7.5, D-3A7.15): the `reconcile_month`
command over injected services (3A7's in-memory world and a stand-in account service). No URL here names a reachable
database. Every expected value is a hand literal (W2)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest

from assetops_backend import reconcile_month as command
from assetops_backend.accounts.permissions import FINANCE
from assetops_backend.database_target import PG_TARGET_ENV
from test_3a7_reconciliation import ANA, FIONA, OWNER_REF, S1_AT, load, t2_world, two_sites_world

URL = "postgresql+psycopg://u:p@rc4.invalid:1/assetops_test"
T2_FUEL = ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $505.00 and the records say $512.50, $7.50 "
           "more (1.49%), beyond the $5.05 allowed (1%).")


@pytest.fixture(autouse=True)
def database_url(monkeypatch):
    for variable in PG_TARGET_ENV:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)


@dataclass(frozen=True)
class Person:
    person_id: UUID
    tenant_slug: str
    active: bool
    roles: tuple[tuple[str, UUID | None], ...]


class Accounts:
    """The two reads the command makes of the account service (3A6's `tenant_by_slug`, 3A3's `onboard_person`)."""

    def __init__(self, tid: UUID) -> None:
        self.tid = tid
        self.people = {"fiona@lakeside.example": Person(FIONA.person_id, "lakeside-power", True, ((FINANCE, None),)),
                       "ana@lakeside.example": Person(ANA.person_id, "lakeside-power", True, (("ANALYST", None),))}

    def tenant_by_slug(self, slug: str) -> UUID | None:
        return self.tid if slug == "lakeside-power" else None

    def onboard_person(self, email: str) -> Person | None:
        return self.people.get(email)


def run(capsys, w, *argv, owner_root: Path | None = None) -> tuple[int, list[dict], str]:
    code = command.main(list(argv), reconciliation=w["recon"], accounts=Accounts(w["tid"]), owner_root=owner_root)
    out, err = capsys.readouterr()
    return code, [json.loads(line) for line in out.splitlines()], err


RECORD = ["record", "--tenant", "lakeside-power", "--period", "2026-10", "--currency", "USD", "--revenue", "755.00",
          "--fuel-cost", "505.00", "--source-ref", "Management accounts, October 2026"]


def test_m1_record_prints_the_statement(capsys) -> None:
    w = two_sites_world()
    load(w, "A", "B")
    w["clock"].now = S1_AT
    code, (line,), _ = run(capsys, w, *RECORD, "--as", "fiona@lakeside.example")
    assert code == 0 and len(w["store"].statement_rows) == 1
    assert list(line) == ["statement_id", "site_code", "period", "currency", "tolerance", "state", "opens", "headings",
                          "recorded_by", "recorded_at", "recorded_by_script", "source_ref", "text"]
    assert (line["site_code"], line["period"], line["currency"], line["tolerance"], line["state"], line["opens"]) == (
        None, "2026-10", "USD", "0.01", "MATCHED", True)
    assert (line["recorded_by"], line["recorded_at"], line["recorded_by_script"]) == (
        str(FIONA.person_id), "2026-11-05T10:00:00+00:00", True)
    assert line["text"] == "Revenue and fuel bought for October 2026 (the organisation) match the management accounts within 1% (Declared)."
    fuel = line["headings"][1]
    assert list(fuel) == ["heading", "state", "reason", "accounts", "recorded", "difference", "allowed",
                          "record_currencies", "sources", "origins", "text"]
    assert {k: fuel[k] for k in ("heading", "state", "reason", "accounts", "recorded", "difference", "allowed")} == {
        "heading": "fuel_bought", "state": "MATCHED", "reason": None, "accounts": "505.00", "recorded": "500.00",
        "difference": "-5.00", "allowed": "5.0500"}
    assert (fuel["record_currencies"], fuel["origins"]) == (["USD"], ["source-emulated"])
    assert fuel["text"] == ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $505.00 and the records "
                            "say $500.00, $5.00 less, within the $5.05 allowed (1%).")


def test_m2_the_analyst_is_refused_before_anything_is_written(capsys) -> None:
    w = two_sites_world()
    load(w, "A", "B")
    code, lines, err = run(capsys, w, *RECORD, "--as", "ana@lakeside.example")
    assert (code, lines, err.strip()) == (2, [], "PERSON_ROLE_REQUIRED")
    code, lines, err = run(capsys, w, *RECORD, "--as", "nobody@lakeside.example")
    assert (code, lines, err.strip()) == (2, [], "PERSON_NOT_FOUND")
    assert w["store"].statement_rows == []


def test_m3_a_refused_amount_prints_its_sentence(capsys) -> None:
    w = two_sites_world()
    load(w, "A", "B")
    argv = [a if a != "755.00" else "755" for a in RECORD]
    code, (line,), _ = run(capsys, w, *argv, "--as", "fiona@lakeside.example")
    assert code == 3 and w["store"].statement_rows == []
    assert line == {"state": "REFUSED", "code": "RECON_AMOUNT", "params": {"heading": "revenue"},
                    "text": "Write the revenue as digits with a decimal point and no separators, like 1200.00."}


def test_m4_show_prints_the_standing_and_reads_at_an_instant(capsys) -> None:
    w = t2_world()
    code, (line,), _ = run(capsys, w, "show", "--tenant", "lakeside-power", "--period", "2026-10", "--site",
                           "KOBO-001")
    assert code == 0
    assert list(line) == ["site_code", "period", "known_at", "reconciled", "reason", "tolerance", "this_month",
                          "cited", "text", "details"]
    assert (line["site_code"], line["known_at"], line["reconciled"], line["reason"], line["cited"]) == (
        "KOBO-001", None, False, "THIS_MONTH_NOT_MATCHED", None)
    assert line["text"] == ("Not yet reconciled: October 2026 (the organisation) does not match the management "
                            "accounts within 1% (Declared).")
    assert line["details"] == [T2_FUEL]
    assert line["this_month"]["statement_id"] == str(w["s1"].statement_id)
    code, (line,), _ = run(capsys, w, "show", "--tenant", "lakeside-power", "--period", "2026-10", "--site",
                           "KOBO-001", "--known-at", "2026-11-06T00:00:00+00:00")  # R9's instant
    assert (code, line["reason"], line["known_at"], line["details"]) == (0, "RECONCILED", "2026-11-06T00:00:00+00:00",
                                                                         [])
    assert line["text"] == ("Reconciled: revenue and fuel bought for October 2026 (the organisation) match the management accounts within 1% "
                            "(Declared).")
    for bad in ("2026-11-06", "2026-11-06T00:00:00", "yesterday"):
        code, lines, err = run(capsys, w, "show", "--tenant", "lakeside-power", "--period", "2026-10",
                               "--known-at", bad)
        assert (code, lines, err.strip()) == (2, [], "KNOWN_AT_INVALID")


def test_m4_show_for_the_organisation_and_an_unknown_site(capsys) -> None:
    w = two_sites_world()
    load(w, "A", "B")
    code, (line,), _ = run(capsys, w, "show", "--tenant", "lakeside-power", "--period", "2026-10")
    assert (code, line["site_code"], line["reason"]) == (0, None, "NO_STATEMENT")
    assert line["text"] == "Not yet reconciled: no closed month has been compared with the management accounts."
    code, lines, err = run(capsys, w, "show", "--tenant", "lakeside-power", "--period", "2026-10", "--site", "NOPE")
    assert (code, lines, err.strip()) == (2, [], "RECON_SITE_UNKNOWN")


def owner(root: Path, text: str, name: str = OWNER_REF) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def tolerance(capsys, w, root: Path, value: str, ref: str = OWNER_REF):
    return run(capsys, w, "set-tolerance", "--tenant", "lakeside-power", "--tolerance", value, "--owner-ref", ref,
               owner_root=root)


def test_m5_set_tolerance(capsys, tmp_path) -> None:
    w = two_sites_world(tmp_path)  # the injected service reads this owner root
    path = owner(tmp_path, "lakeside-power 2%\n")
    assert tolerance(capsys, w, tmp_path, "0.06")[0::2] == (2, "TOLERANCE_INVALID\n")
    assert tolerance(capsys, w, tmp_path, "0.02", "owner/nope.md")[0::2] == (2, "OWNER_REF_INVALID\n")
    code, (line,), _ = tolerance(capsys, w, tmp_path, "0.02")
    assert (code, line) == (0, {"state": "SET", "tolerance": "0.02",
                                "owner_ref_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    owner(tmp_path, "the tolerance is 2%\n")  # no slug
    assert tolerance(capsys, w, tmp_path, "0.02")[0::2] == (2, "OWNER_REF_INVALID\n")
    owner(tmp_path, "lakeside-power 3%\n")  # another figure
    assert tolerance(capsys, w, tmp_path, "0.02")[0::2] == (2, "OWNER_REF_INVALID\n")
    owner(tmp_path, "lakeside-power-north 2%\n")  # a longer slug does not cite this one (review L2)
    assert tolerance(capsys, w, tmp_path, "0.02")[0::2] == (2, "OWNER_REF_INVALID\n")
    assert len(w["store"].tolerance_rows) == 1


def test_m5_the_command_reads_an_owner_root_through_the_port(tmp_path) -> None:
    path = owner(tmp_path, "lakeside-power 2%\n")
    read = command.owner_reader(tmp_path)
    assert read(OWNER_REF) == path.read_bytes()
    assert read("owner/owner-absent.md") is None
    (tmp_path / "owner" / "owner-link.md").symlink_to(path)
    assert read("owner/owner-link.md") is None


def test_m5_the_owner_root_defaults_to_the_repository() -> None:
    assert command.OWNER_ROOT == Path(command.__file__).resolve().parents[2]
    assert (command.OWNER_ROOT / "owner").is_dir()


def test_before_any_connection(capsys, monkeypatch) -> None:
    w = two_sites_world()
    monkeypatch.delenv("DATABASE_URL")
    code, lines, err = run(capsys, w, "show", "--tenant", "lakeside-power", "--period", "2026-10")
    assert (code, lines, err.strip()) == (2, [], "DATABASE_URL_REQUIRED")
    monkeypatch.setenv("DATABASE_URL", URL)
    code, lines, err = run(capsys, w, "show", "--tenant", "nope", "--period", "2026-10")
    assert (code, lines, err.strip()) == (2, [], "TENANT_NOT_FOUND")
    monkeypatch.setenv("ASSETOPS_REAL_OPERATOR_DATA", "on")  # a real-data run on a test database
    code, lines, err = run(capsys, w, "show", "--tenant", "lakeside-power", "--period", "2026-10")
    assert (code, lines, err.strip()) == (2, [], "CONFIGURATION")
