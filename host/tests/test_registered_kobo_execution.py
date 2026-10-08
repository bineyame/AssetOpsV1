"""S2-01a phase 2: the kernel runs a registered KOBO-001 Draft unchanged.

A Draft set up from the registered Foundation and SignalBinding snapshot
freezes its component links from the binding rows (ten for the converted
KOBO-001, including `generator-controller/status`), never from the legacy
Foundation's `signal_mappings`. These tests confirm the host consumes exactly
those links, that the same scenario run from a legacy YAML Draft and from the
registered Draft produces the same public reports, and that the public report
boundary carries no private Lab cause or oracle.

The registered Draft is built by the backend's own S2-01a fixtures, which
import and convert KOBO-001 into an in-memory Foundation store; `backend/tests`
is put on the path for that, exactly as those fixtures are used there.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from execution_adapter import _component_carrying, reporting_inputs  # noqa: E402
from kobo import kobo_draft  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts, render_projection  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

#: Legacy KOBO-001 links the converted binding set does not bind.
LEGACY_ONLY = {
    ("battery-pcs-controller", "discharge-capability"),
    ("pv-inverter-controller", "available-power"),
}
#: Keys of a projection that name the run rather than describe what happened.
RUN_IDENTITY = {"run_id", "inputs_identity", "content_digest"}


def lab(root: Path) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(root), stages=JsonSourceStages(root / "stages")
    )


@pytest.fixture(scope="module")
def drafts():
    store, _, outcome = registered.converted()
    run = registered.setup_service(store).create_draft_run(registered.request())
    legacy = kobo_draft(start_time=registered.START, end_time=registered.END)
    return run, legacy, outcome.published.changed


def links(run) -> dict[tuple[str, str], str]:
    return {
        (m.device_id, m.signal_id): m.component_id
        for m in run.deterministic_identity.signal_mappings
    }


class TestFrozenLinks:
    def test_the_draft_carries_the_ten_binding_links_not_the_legacy_list(self, drafts) -> None:
        run, legacy, pinned = drafts
        assert run.registered_basis is not None
        frozen = links(run)
        assert len(frozen) == 10
        assert ("generator-controller", "status") in frozen
        bound = {str(b.id) for b in pinned.bindings}
        assert {m.mapping_id for m in run.deterministic_identity.signal_mappings} <= bound
        assert not LEGACY_ONLY & set(frozen), "a legacy-only mapping link was frozen"
        assert set(links(legacy)) - set(frozen) == LEGACY_ONLY

    def test_the_host_resolves_each_link_exactly_as_frozen(self, drafts) -> None:
        run, _, _ = drafts
        for (device, signal), component in links(run).items():
            assert _component_carrying(run, device, signal) == component
        for device, signal in LEGACY_ONLY:
            assert _component_carrying(run, device, signal) is None

    def test_reporting_paths_come_only_from_the_frozen_links(self, drafts) -> None:
        run, _, _ = drafts
        frozen = links(run)
        for spec in reporting_inputs(run).signals:
            assert spec.address.endswith("@" + frozen[(spec.device_id, spec.signal_id)])


class TestExecution:
    def test_registered_and_legacy_drafts_report_the_same_readings(self, drafts, tmp_path) -> None:
        run, legacy, _ = drafts
        rendered = {}
        for name, draft in (("registered", run), ("legacy", legacy)):
            port = lab(tmp_path / name)
            port.start(draft)
            projection = port.run_to_end(draft)
            assert projection.status == "COMPLETED"
            rendered[name] = render_projection(projection)
        differing = {
            key for key in rendered["registered"]
            if rendered["registered"][key] != rendered["legacy"][key]
        }
        assert differing <= RUN_IDENTITY, differing
        assert rendered["registered"]["observations"], "nothing was reported; the comparison is empty"

    def test_a_reloaded_execution_reads_back_the_same_and_public_reports_hold_no_causes(
        self, drafts, tmp_path
    ) -> None:
        run, _, _ = drafts
        port = lab(tmp_path)
        port.start(run)
        finished = render_projection(port.run_to_end(run))
        reread = render_projection(lab(tmp_path).projection(run))
        assert reread == finished
        public = json.dumps(
            {key: finished[key] for key in ("signals", "observations", "recent_reports")}
        ).lower()
        assert finished["observations"]
        for private in ("cause", "oracle", "intent", "private"):
            assert private not in public, private
