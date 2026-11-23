"""DD2.3/DD2.4 (spec `specs/DD-demo-data/spec.md` §3; D-DD.24, D-DD.49): every cold and EV source profile passes 3A6
admission (steps 1 to 6: compile, status, lineage, the sample read and parsed, the expected records, the six probes)
on its own sample and expected file, through the real `SourceProfiles` on the in-memory store. The departure log's
`Block met` column is the `bool` type of DD2.2 (its residual risk: admitted end to end).

The files are read as data; nothing of the simulator is imported (dependency-direction guard).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assetops_backend.commercial.profiles import ProfileRefused
from test_3a6_source_profiles import make_world
from test_3c1a_person_work import People

PROFILES = Path(__file__).resolve().parents[1] / "conversions" / "profiles"
IDS = sorted(p.name.removesuffix(".profile.json") for p in PROFILES.glob("*.profile.json"))


def files(profile_id: str) -> tuple[bytes, bytes, bytes]:
    return tuple((PROFILES / f"{profile_id}.{suffix}").read_bytes()
                 for suffix in ("profile.json", "sample.csv", "expected.json"))


@pytest.fixture(scope="module")
def people() -> People:
    return People()


def test_a0_the_nine_profiles() -> None:
    assert IDS == ["cold-budget-illustrative", "cold-electricity-bill-illustrative",
                   "cold-storage-invoicing-illustrative", "cold-storage-ledger-illustrative",
                   "ev-budget-illustrative", "ev-departures-illustrative",
                   "ev-fleet-roster-illustrative", "ev-service-tickets-illustrative", "ev-utility-invoice-illustrative"]


@pytest.mark.parametrize("profile_id", IDS)
def test_a1_profile_is_admissible_on_its_sample(people, profile_id: str) -> None:
    w = make_world(people)
    report = w.profiles.check(w.tid, *files(profile_id))
    assert (report.profile_id, report.version, report.already) == (profile_id, 1, None)
    assert report.sample_rows == len(json.loads(files(profile_id)[2]))


def test_a2_admit_names_the_analyst_and_reads_block_met_as_boolean(people) -> None:
    w = make_world(people)
    profile, sample, expected = files("ev-departures-illustrative")
    row = w.profiles.admit(w.tid, w.ana, profile, sample, expected)
    assert (row.profile_id, row.version, row.admitted_by) == ("ev-departures-illustrative", 1, w.ana.person_id)
    assert [r["body"]["block_met"] for r in json.loads(expected)] == [True, False, True]


def test_a3_a_changed_expected_boolean_is_refused(people) -> None:
    w = make_world(people)
    profile, sample, expected = files("ev-departures-illustrative")
    wrong = json.loads(expected)
    wrong[1]["body"]["block_met"] = "false"  # text, not the JSON boolean the profile writes
    with pytest.raises(ProfileRefused) as refused:
        w.profiles.check(w.tid, profile, sample, json.dumps(wrong).encode())
    assert refused.value.code == "ADMIT_EXPECTED"
