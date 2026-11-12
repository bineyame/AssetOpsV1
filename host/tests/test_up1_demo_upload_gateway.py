"""UP-1 D-UP.2, no database: the demo upload gateway's files (`tools/demo_upload_gateway.py`) and the host's
delivery after a send (`host/reading_upload_process.deliver_now`)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import demo_upload_gateway as ug
import reading_upload_process as up

SNAPSHOT = json.dumps({
    "tenant_id": "t", "site": {"site_id": "s"}, "gateway": {"gateway_id": "g", "mode": "SIMULATED",
                                                            "gateway_external_id": "kobo-gw"},
    "sources": [{"source_id": "u1", "source_external_id": "pv"}, {"source_id": "u2", "source_external_id": "clinic"},
                {"source_id": "u3", "source_external_id": "genset"}]})


def _per_day_state(work: Path, folder: str, epoch: str) -> None:
    state = work / folder / f"gw-{epoch}"
    state.mkdir(parents=True)
    (state / "gateway.json").write_text(json.dumps({"provisioning": {"sequence_epoch": epoch}}), encoding="utf-8")


def test_the_switch_is_off_unless_sites_are_named():
    assert not ug.upload_switched_on({})
    assert not ug.upload_switched_on({ug.SITES_ENV: "  "})
    assert ug.upload_switched_on({ug.SITES_ENV: "KOBO-001"})


def test_the_per_day_epochs_are_read_from_every_kobo_build_folder(tmp_path):
    _per_day_state(tmp_path, "kobo-replay-abc", "day-1")
    _per_day_state(tmp_path, "kobo-add-day-xyz", "day-9")
    (tmp_path / "cold-replay-1" / "gw-day-5").mkdir(parents=True)
    assert ug.per_day_epochs(tmp_path) == {"day-1", "day-9"}


def test_the_edge_epoch_is_minted_once_and_kept(tmp_path):
    state = ug.state_dir(tmp_path)
    minted = iter(["kobo-edge-1", "kobo-edge-2"])
    first = ug.ensure_epoch(state, {"day-1"}, mint=lambda: next(minted))
    again = ug.ensure_epoch(state, {"day-1"}, mint=lambda: next(minted))
    assert first == again == "kobo-edge-1"
    assert (state / ug.EPOCH_FILE).read_text(encoding="utf-8") == "kobo-edge-1"


def test_the_edge_epoch_never_equals_a_per_day_epoch(tmp_path):
    state = ug.state_dir(tmp_path)
    with pytest.raises(ug.GatewayPrepareRefused):
        ug.ensure_epoch(state, {"day-1"}, mint=lambda: "day-1")
    assert not (state / ug.EPOCH_FILE).exists()
    ug.ensure_epoch(state, set(), mint=lambda: "day-2")
    with pytest.raises(ug.GatewayPrepareRefused):  # a later per-day stream took the stored epoch
        ug.ensure_epoch(state, {"day-2"})


def test_the_activation_window_is_the_latest_prepared_kobo_day():
    doc = {"days": [{"site": "kobo", "start": "2026-11-01T06:00:00Z", "end": "2026-11-01T18:00:00Z"},
                    {"site": "kobo", "start": "2026-11-03T06:00:00Z", "end": "2026-11-03T18:00:00Z"},
                    {"site": "kobo", "start": None, "end": None},
                    {"site": "cold", "start": "2026-11-05T06:00:00Z", "end": "2026-11-05T18:00:00Z"}]}
    assert ug.latest_kobo_window(doc) == ("2026-11-03T06:00:00Z", "2026-11-03T18:00:00Z")
    with pytest.raises(ug.GatewayPrepareRefused):
        ug.latest_kobo_window({"days": [{"site": "cold", "start": "a", "end": "b"}]})


def test_the_gateway_uploads_over_tls_every_60_seconds(tmp_path):
    state = ug.state_dir(tmp_path)
    config = ug.gateway_config(state, {"sequence_epoch": "kobo-edge-1"}, ca_file=tmp_path / "tls" / "server.crt",
                               upload_credential_file=state / "upload.credential.v1")
    upload = config["upload"]
    assert upload["server_url"] == "https://127.0.0.1:8443"
    assert upload["interval_seconds"] == 60
    assert upload["ca_file"] == str(tmp_path / "tls" / "server.crt")
    assert config["provisioning"] == {"sequence_epoch": "kobo-edge-1"}
    assert config["address"] == ug.gateway_address(state)


def test_tls_is_generated_once(tmp_path):
    calls: list = []

    def run(argv, **kw):
        calls.append(argv)
        Path(argv[argv.index("-keyout") + 1]).write_text("key", encoding="ascii")
        Path(argv[argv.index("-out") + 1]).write_text("cert", encoding="ascii")

    protected: list = []
    cert, key = ug.ensure_tls(tmp_path, run=run, protect=protected.append)
    assert (cert, key) == ug.tls_files(tmp_path) and protected == [key]
    assert "subjectAltName=IP:127.0.0.1,DNS:localhost" in calls[0]
    ug.ensure_tls(tmp_path, run=run, protect=protected.append)
    assert len(calls) == 1  # the gateway already trusts the existing certificate


def test_the_credential_enables_only_the_profile_sources():
    assert ug.profile_sources(SNAPSHOT, {"pv-inverter/ac": "u1", "clinic/kw": "u2"}) == ["clinic", "pv"]


def test_the_credential_is_issued_through_the_provisioning_command(tmp_path):
    state = ug.state_dir(tmp_path)
    seen: list = []

    def run(argv, **kw):
        seen.append(argv)
        return SimpleNamespace(returncode=0, stdout=f"Issued ...\nCredential file: {state / 'upload.credential.v1'}\n",
                               stderr="")

    path = ug.issue_credential(state, "kobo-gw", ["clinic", "pv"], run=run)
    assert path == state / "upload.credential.v1"
    argv = seen[0]
    assert argv[argv.index("--actor") + 1] == "service:demo-upload"
    assert argv[argv.index("--site") + 1] == "KOBO-001" and argv[argv.index("--gateway") + 1] == "kobo-gw"
    assert [argv[i + 1] for i, a in enumerate(argv) if a == "--enable-source"] == ["clinic", "pv"]


def test_a_refused_issue_is_reported(tmp_path):
    def run(argv, **kw):
        return SimpleNamespace(returncode=2, stdout="", stderr="Refused; nothing was written")

    with pytest.raises(ug.GatewayPrepareRefused, match="Refused"):
        ug.issue_credential(ug.state_dir(tmp_path), "kobo-gw", [], run=run)


def test_the_credential_is_reused_while_its_file_exists(tmp_path):
    state = ug.state_dir(tmp_path)
    state.mkdir(parents=True)
    credential = state / "upload.credential.v1"
    config = ug.gateway_config(state, {}, ca_file=tmp_path / "c", upload_credential_file=credential)
    ug.write_json(state / ug.CONFIG_FILE, config)
    assert ug.existing_credential(state) is None  # named but missing: reissue
    credential.write_text("aog1.x.y", encoding="ascii")
    assert ug.existing_credential(state) == credential


def test_the_host_reads_the_gateway_file_the_activation_writes(tmp_path):
    state = ug.state_dir(tmp_path)
    config = ug.gateway_config(state, {}, ca_file=tmp_path / "c", upload_credential_file=tmp_path / "u")
    path = tmp_path / ug.GATEWAY_FILE
    ug.write_json(path, ug.host_gateway_doc(state, config, "a" * 64))
    read = up.gateway_from_environment({up.GATEWAY_ENV: str(path)})
    assert read == {"gateway_address": config["address"], "ipc_credential": str(state / "gateway.credential"),
                    "snapshot_sha256": "a" * 64, "expect_identity": str(state / ug.EXPECT_FILE)}


def test_waiting_stops_when_the_process_exits(tmp_path):
    with pytest.raises(ug.GatewayPrepareRefused, match="exited"):
        ug.wait_for_line(tmp_path / "gw.log", "READY", alive=lambda: False, pause=lambda s: None)
    (tmp_path / "gw.log").write_text("READY gateway\n", encoding="utf-8")
    ug.wait_for_line(tmp_path / "gw.log", "READY", alive=lambda: False, pause=lambda s: None)
    with pytest.raises(ug.GatewayPrepareRefused, match="exited"):
        ug.wait_for_port("127.0.0.1", 9, alive=lambda: False, pause=lambda s: None)


def _serve(tmp_path, monkeypatch, switch: str | None) -> dict:
    """`demo_combined.serve` with every process faked: what the API gets and what serve started and stopped."""
    import urllib.request

    import demo_combined as dc

    seen: dict = {"popen": [], "py": [], "killed": []}

    class Proc:
        def __init__(self, argv, **kw):
            self.argv, self.env, self.pid = argv, kw.get("env") or {}, len(seen["popen"]) + 1
            seen["popen"].append(self)

        def poll(self):
            return 0 if self.argv[2] == "uvicorn" else None  # the API "exits" at once; the helpers keep running

    if switch is None:
        monkeypatch.delenv(ug.SITES_ENV, raising=False)
    else:
        monkeypatch.setenv(ug.SITES_ENV, switch)
    monkeypatch.setattr(dc.subprocess, "Popen", Proc)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: SimpleNamespace(read=lambda: b"ok"))
    monkeypatch.setattr(dc, "_kill_tree", seen["killed"].append)
    monkeypatch.setattr(ug, "wait_for_port", lambda *a, **k: None)
    monkeypatch.setattr(ug, "wait_for_line", lambda *a, **k: None)
    demo = object.__new__(dc.Demo)
    demo.work = demo.tree = tmp_path
    demo.story = lambda: {}
    demo.write_prebuilt_routes = lambda: None
    demo.serve_env = lambda: {"DATABASE_URL": "x"}
    demo.env = lambda **kw: {}
    demo.links = lambda web: None
    demo.py = lambda *argv, **kw: seen["py"].append(argv)
    with pytest.raises(SystemExit):  # the faked API exits before it answers health
        demo.serve(8000, 5000)
    return seen


def test_serve_starts_no_gateway_when_the_switch_is_off(tmp_path, monkeypatch):
    seen = _serve(tmp_path, monkeypatch, None)
    assert [p.argv[2] for p in seen["popen"]] == ["uvicorn"] and seen["py"] == []
    assert "ASSETOPS_READING_UPLOAD_GATEWAY" not in seen["popen"][0].env


def test_serve_starts_the_central_and_the_edge_gateway_before_the_api(tmp_path, monkeypatch):
    seen = _serve(tmp_path, monkeypatch, "KOBO-001")
    assert [p.argv[2] for p in seen["popen"]] == ["assetops_backend.serve_tls", "assetops_gateway", "uvicorn"]
    tls, gateway, api = seen["popen"]
    assert tls.argv[tls.argv.index("--port") + 1] == "8443"
    assert gateway.argv[-1] == str(ug.state_dir(tmp_path) / ug.CONFIG_FILE)
    assert [argv[1] for argv in seen["py"]] == ["prepare", "activate"]
    assert api.env["ASSETOPS_READING_UPLOAD_GATEWAY"] == str(tmp_path / ug.GATEWAY_FILE)
    assert seen["killed"] == [tls.pid, gateway.pid]  # stopped with serve


class _Link:
    def __init__(self, attempts, fail=False):
        self.attempts, self.fail, self.calls = list(attempts), fail, []

    def __call__(self, address, credential):
        self.opened = (address, credential)
        return self

    def call(self, op, body):
        self.calls.append((op, body))
        if self.fail:
            raise OSError("pipe closed")
        return {"batches": {"attempted": self.attempts.pop(0) if self.attempts else 0}}


GATEWAY = {"gateway_address": r"\\.\pipe\x", "ipc_credential": "c", "snapshot_sha256": "s", "expect_identity": "e"}


def test_delivery_runs_until_a_pass_attempts_nothing():
    link = _Link([3, 2])
    assert up.deliver_now(GATEWAY, link_factory=link) == 5
    assert link.calls == [("deliver", {"max_batches": 50})] * 3
    assert link.opened == (r"\\.\pipe\x", Path("c"))


def test_delivery_is_bounded_and_never_raises():
    ticks = iter([0.0, 10.0, 20.0, 31.0])
    link = _Link([1] * 10)
    assert up.deliver_now(GATEWAY, link_factory=link, clock=lambda: next(ticks)) == 2
    assert up.deliver_now(GATEWAY, link_factory=_Link([], fail=True)) == 0  # the 60 s backstop delivers it
