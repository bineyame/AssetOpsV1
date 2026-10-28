"""TEL-01 publisher against a fake IPC link (D4 item 5, Q-T28, Q-T29, Q-T32)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import FakeLink  # noqa: E402

from assetops_gateway.ipc import GatewayRequestRefused, GatewayUnavailable  # noqa: E402

from assetops_field.publish import ADMISSION_CHUNK, OPS_USED, GatewayPublisher, IdentityMismatch  # noqa: E402

EXPECTED = {
    "tenant_id": "11111111-1111-4111-8111-111111111111",
    "site_id": "22222222-2222-4222-8222-222222222222",
    "gateway_id": "33333333-3333-4333-8333-333333333333",
    "source_mode": "SIMULATED",
    "sequence_epoch": "epoch-1",
    "row_sources": {"pv-inverter-controller/ac-power": "aaaa", "battery-pcs-controller/state-of-charge": "bbbb"},
}
IDENTITY = {key: EXPECTED[key] for key in ("tenant_id", "site_id", "gateway_id", "source_mode", "sequence_epoch")}
IDENTITY["permitted_source_ids"] = ["aaaa", "bbbb", "cccc"]
RELEASED = {"released_batch_ids": ["b1"], "released_now": 1, "delivery": {"pending": 0}}
REF = "field:gx-system-illustrative-1:1:20261027T120000Z:0a1b2c3d"


def publisher(link: FakeLink) -> GatewayPublisher:
    return GatewayPublisher(link=link, snapshot_sha256="f" * 64, session_ref=REF, expected=EXPECTED)


def test_identity_matches():
    link = FakeLink({"identity": IDENTITY})
    assert publisher(link).check_identity() == IDENTITY
    assert link.ops == ["identity"]


@pytest.mark.parametrize(
    "change, named",
    [
        ({"tenant_id": "x"}, "tenant_id"),
        ({"site_id": "x"}, "site_id"),
        ({"gateway_id": "x"}, "gateway_id"),
        ({"sequence_epoch": "epoch-2"}, "sequence_epoch"),
        ({"source_mode": "PRODUCTION"}, "source_mode"),
        ({"permitted_source_ids": ["aaaa"]}, "row_sources.battery-pcs-controller/state-of-charge"),
    ],
)
def test_identity_mismatch_names_the_first_differing_key(change, named):
    link = FakeLink({"identity": IDENTITY | change})
    with pytest.raises(IdentityMismatch) as caught:
        publisher(link).check_identity()
    assert str(caught.value).startswith(named)
    assert "admit" not in link.ops


def test_admit_chunks_at_256_and_returns_admissions_verbatim_including_holds():
    def answer(body):
        return {"admissions": [{"status": "HELD" if i == 0 else "ADMITTED", "n": i} for i, _ in
                               enumerate(body["reports"])]}

    link = FakeLink({"admit": answer})
    texts = [f"r{i}" for i in range(ADMISSION_CHUNK * 2 + 3)]
    admissions = publisher(link).admit(texts)
    assert len(admissions) == len(texts) and admissions[0]["status"] == "HELD"
    bodies = [body for op, body in link.calls]
    assert [len(b["reports"]) for b in bodies] == [256, 256, 3]
    assert all(b["snapshot_sha256"] == "f" * 64 and b["lab_run_ref"] == REF for b in bodies)
    assert [r for b in bodies for r in b["reports"]] == texts


def test_admit_propagates_unavailable_and_whole_request_refusals():
    with pytest.raises(GatewayUnavailable):
        publisher(FakeLink({"admit": GatewayUnavailable("down")})).admit(["r"])
    with pytest.raises(GatewayRequestRefused):
        publisher(FakeLink({"admit": GatewayRequestRefused("NOT_PROVISIONED", None, "x")})).admit(["r"])


def test_seal_and_release_returns_the_defined_keys():
    link = FakeLink({"seal": {"batch_ids": ["b1"]}, "release_run": RELEASED})
    assert publisher(link).seal_and_release() == {"batch_ids": ["b1"], "seal_refused": None, **RELEASED}
    assert link.calls == [("seal", None), ("release_run", {"lab_run_ref": REF})]


def test_seal_and_release_survives_seal_refused_and_still_releases():
    link = FakeLink({"seal": GatewayRequestRefused("SEAL_REFUSED", None, "group g refused"),
                     "release_run": RELEASED})
    result = publisher(link).seal_and_release()
    assert result["seal_refused"] == "group g refused" and result["released_batch_ids"] == ["b1"]
    assert link.ops == ["seal", "release_run"]


def test_seal_and_release_propagates_other_refusals():
    link = FakeLink({"seal": GatewayRequestRefused("DISK_STOP", None, "x"), "release_run": RELEASED})
    with pytest.raises(GatewayRequestRefused):
        publisher(link).seal_and_release()
    assert link.ops == ["seal"]


def test_release_previous_seals_before_releasing_the_previous_reference():
    link = FakeLink({"seal": {"batch_ids": ["old"]}, "release_run": RELEASED})
    result = publisher(link).release_previous("field:old")
    assert link.calls == [("seal", None), ("release_run", {"lab_run_ref": "field:old"})]
    assert result == {"sealed_batch_ids": ["old"], "released_batch_ids": ["b1"], "released_now": 1}
    with pytest.raises(GatewayRequestRefused):
        publisher(FakeLink({"seal": GatewayRequestRefused("SEAL_REFUSED", None, "x")})).release_previous("o")


def test_the_link_sees_only_the_ops_used():
    link = FakeLink({"identity": IDENTITY, "admit": {"admissions": []}, "seal": {"batch_ids": []},
                     "release_run": RELEASED, "diagnostics": {"queue_count": 0}})
    p = publisher(link)
    p.check_identity()
    p.release_previous("field:old")
    p.admit(["r"])
    p.seal_and_release()
    assert p.diagnostics() == {"queue_count": 0}
    assert set(link.ops) == set(OPS_USED)
    with pytest.raises(ValueError):
        p._call("deliver")
    assert set(link.ops) <= set(OPS_USED)
