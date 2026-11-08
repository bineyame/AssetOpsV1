"""CH-5b1 L0 (build sheet CH-5b R6, CH5b1-R Q1-Q3): the declared chain graph check, its startup hook and its diagram."""
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from assetops_backend import main
from assetops_backend.chain import composition
from assetops_backend.chain.graph import (
    KNOWN_GAPS, NOT_CHAIN_SOURCED, WARNING_PRODUCER, ChainGraphError, check, emits_signal, problems,
    render_dot, render_svg)

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "Docs" / "demo-sprint"  # written by tools/chain_graph_render.py


@pytest.fixture(scope="module")
def g():
    return composition.declared_graph_inputs()


def _rules(inputs) -> set[tuple[str, str]]:
    return {(p.rule, p.key) for p in problems(inputs)}


def test_main_config_passes(g) -> None:
    lines = check(g)
    assert lines[0].startswith("chain graph OK: 7 measures, 6 lifecycle mechanisms, 16 outcome-map entries")
    assert "known gap: no producer: WARNING:CHARGERS_MOSTLY_IDLE (owner BL-06)" in lines


def _measures_with(g, key, **change):
    return {**g.measures, key: replace(g.measures[key], **change)}


MUTATIONS = {
    "reference: unknown adapter": (
        lambda g: replace(g, measures=_measures_with(g, "productive_kwh", adapter="mini.nothing@1")),
        ("reference", "productive_kwh")),
    "reference: unknown outcome key": (
        lambda g: replace(g, entries={**g.entries, "FINDING:COLD_EXCURSION": (("CC-99",), ())}),
        ("reference", "FINDING:COLD_EXCURSION")),
    "measure_input: measure without register input": (
        lambda g: replace(g, register=replace(g.register, inputs={
            k: v for k, v in g.register.inputs.items() if k != "charging_kwh"})),
        ("measure_input", "charging_kwh")),
    "measure_input: register input without measure": (
        lambda g: replace(g, register=replace(g.register, inputs={
            **g.register.inputs, "ghost_kwh": g.register.inputs["charging_kwh"]})),
        ("measure_input", "ghost_kwh")),
    "lifecycle_measure: undeclared clean-day measure": (
        lambda g: replace(g, clean_day_measures={**g.clean_day_measures, "COLD_EXCURSION": ("chamber_temp_f",)}),
        ("lifecycle_measure", "COLD_EXCURSION")),
    "entry_source: Finding without lifecycle mechanism": (
        lambda g: replace(g, entries={**g.entries, "FINDING:PUMP_CAVITATION": (("MG-2",), ())}),
        ("entry_source", "FINDING:PUMP_CAVITATION")),
    "entry_source: unknown MEASURE source": (
        lambda g: replace(g, entries={**g.entries, "MEASURE:ghost_kwh": (("MG-2",), ())}),
        ("entry_source", "MEASURE:ghost_kwh")),
    "orphan: lifecycle mechanism without entry": (
        lambda g: replace(g, clean_day_measures={**g.clean_day_measures, "PUMP_CAVITATION": ("productive_kwh",)}),
        ("orphan", "PUMP_CAVITATION")),
    "not_chain_sourced (1): unlisted key": (
        lambda g: replace(g, entries={**g.entries, "WARNING:FUSE_BLOWN": (("MG-4",), ())}),
        ("not_chain_sourced", "WARNING:FUSE_BLOWN")),
    "not_chain_sourced (2): stale row": (
        lambda g: replace(g, not_chain_sourced={**NOT_CHAIN_SOURCED,
                                                "FINDING:COLD_EXCURSION": (WARNING_PRODUCER, "CH-8")}),
        ("not_chain_sourced", "FINDING:COLD_EXCURSION")),
    "not_chain_sourced (3): warning kind not in KINDS": (
        lambda g: replace(g, warning_kinds=g.warning_kinds - {"PLAN_OVERDUE"}),
        ("not_chain_sourced", "WARNING:PLAN_OVERDUE")),
    "not_chain_sourced (3): signal module does not emit the key": (
        lambda g: replace(g, not_chain_sourced={**NOT_CHAIN_SOURCED,
                                                "SIGNAL:EVIDENCE_GAP": ("assetops_backend.chain.graph", "CH-8")}),
        ("not_chain_sourced", "SIGNAL:EVIDENCE_GAP")),
    "not_chain_sourced (3): producer None outside the known gaps": (
        lambda g: replace(g, not_chain_sourced={**NOT_CHAIN_SOURCED, "WARNING:PLAN_DUE_SOON": (None, "CH-8")}),
        ("not_chain_sourced", "WARNING:PLAN_DUE_SOON")),
    "not_chain_sourced (4): row not in ENTRIES": (
        lambda g: replace(g, not_chain_sourced={**NOT_CHAIN_SOURCED, "WARNING:FUSE_BLOWN": (WARNING_PRODUCER, "CH-8")}),
        ("not_chain_sourced", "WARNING:FUSE_BLOWN")),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_each_rule_fails_on_its_mutation(g, name) -> None:
    mutate, expected = MUTATIONS[name]
    broken = mutate(g)
    assert expected in _rules(broken)
    with pytest.raises(ChainGraphError) as exc:
        check(broken)
    assert exc.value.rule in {r for r, _ in _rules(broken)}


def test_known_gaps_are_ruled_rows_only() -> None:
    # CH5b1-R Q1: CHARGERS_MOSTLY_IDLE (owner BL-06, SCOPE-1; CH6a1-R Q4).
    assert KNOWN_GAPS == {"WARNING:CHARGERS_MOSTLY_IDLE"}
    assert {k for k, (p, _) in NOT_CHAIN_SOURCED.items() if p is None} == KNOWN_GAPS
    assert NOT_CHAIN_SOURCED["WARNING:CHARGERS_MOSTLY_IDLE"][1] == "BL-06"


def test_evidence_gap_producer_emits_the_key() -> None:
    """CH5b1-R Q1: the named module passes the key to `SignalFact` (`site_outcomes/mini.py`)."""
    import assetops_backend.site_outcomes.mini as mini

    source = Path(mini.__file__).read_text(encoding="utf-8")
    assert emits_signal(source, "SIGNAL:EVIDENCE_GAP")
    assert not emits_signal(source, "SIGNAL:EVIDENCE_READINESS")  # a status input (outcomes/status.py), not a SignalFact
    assert not emits_signal("x = SignalFact(KEY, True)\n", "SIGNAL:EVIDENCE_GAP")
    ast.parse(source)


def test_startup_refuses_a_broken_graph(monkeypatch, g) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ASSETOPS_WORK_CURSOR_KEY_HEX", "a7" * 32)
    broken = MUTATIONS["orphan: lifecycle mechanism without entry"][0](g)
    monkeypatch.setattr(composition, "declared_graph_inputs", lambda: broken)
    with pytest.raises(ChainGraphError) as exc:
        main.create_app()
    assert (exc.value.rule, exc.value.key) == ("orphan", "PUMP_CAVITATION")


def test_startup_builds_without_database(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ASSETOPS_WORK_CURSOR_KEY_HEX", "a7" * 32)
    assert TestClient(main.create_app()).get("/api/health").status_code == 200


def test_committed_diagram_equals_a_fresh_render(g) -> None:
    """CH5b1-R Q3: the committed `.dot` and SVG are the generator's output (check-all never rewrites them)."""
    assert (DEFAULT_OUT / "chain-graph.dot").read_text(encoding="utf-8") == render_dot(g)
    assert (DEFAULT_OUT / "chain-graph.svg").read_text(encoding="utf-8") == render_svg(g)


def test_evidence_readiness_is_the_status_edge() -> None:
    """CH5b1-R2: SIGNAL:EVIDENCE_READINESS is the `@EVIDENCE` status input implemented by `outcomes/status.py`."""
    from assetops_backend.outcomes.catalogue import OUTCOME_BY_KEY
    from assetops_backend.outcomes.outcome_map import DOMAIN_ALIAS, ENTRIES
    from assetops_backend.outcomes.status import LIMITED_READINESS, WATCH, outcome_state

    assert NOT_CHAIN_SOURCED["SIGNAL:EVIDENCE_READINESS"] == ("assetops_backend.outcomes.status", "CH-5b1")
    assert ENTRIES["SIGNAL:EVIDENCE_READINESS"][0] == ("@EVIDENCE",)
    for domain, key in DOMAIN_ALIAS["@EVIDENCE"].items():
        other = next(o for o in OUTCOME_BY_KEY.values() if o.domain == domain and o.key != key and o.measured)
        for r in LIMITED_READINESS:
            got = outcome_state(OUTCOME_BY_KEY[key], settled=True, signals=[], readiness=r)
            assert got == (WATCH, "EVIDENCE_READINESS_" + r)
            assert outcome_state(other, settled=True, signals=[], readiness=r)[1] != "EVIDENCE_READINESS_" + r
