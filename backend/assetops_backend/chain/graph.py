"""CH-5b1 (build sheet CH-5b R6, CH5b1-R Q1-Q3): the declared chain graph check and its generated diagram.

    python -m assetops_backend.chain.graph check          # exit 1 and the failed rule + key on a broken graph
    python -m assetops_backend.chain.graph dot [--svg]    # print the DOT text (or the SVG) to stdout
    python tools/chain_graph_render.py                    # writes Docs/demo-sprint/chain-graph.{dot,svg} from these

It validates what is declared today, before the CH-8 catalogue: the event register (`config/chain/event-register-v1.yaml`),
`chain/measures.py` `MEASURES` and the adapter keys, the thread-lifecycle `clean_day_measures`, and
`outcomes/outcome_map.py` `ENTRIES`. Pure: every input arrives in `GraphInputs`; `chain/composition.py`
`declared_graph_inputs()` loads them (only the composition reads files or imports the adapters).

Rules (each failure names its rule and key):
  reference         - a measure's adapter is a registered adapter key; an `ENTRIES` outcome key or alias resolves.
  measure_input     - every measure has an event-register input; every register input is a declared measure.
  lifecycle_measure - every lifecycle mechanism's clean-day measures are declared measures.
  entry_source      - a `FINDING:` key names a lifecycle mechanism; a `MEASURE:` key names a declared measure.
  orphan            - every lifecycle mechanism reaches an `ENTRIES` key through `thread_signal_key`.
  not_chain_sourced - CH5b1-R Q1: an `ENTRIES` key with no measure or mechanism must be a `NOT_CHAIN_SOURCED` row whose
                      producer resolves; a stale row (now chain-mapped), a row outside `ENTRIES` or an unlisted key fails.
"""
from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

#: The producer of every `WARNING:<kind>` row: `outcomes/warnings.py` `KINDS` must hold the kind.
WARNING_PRODUCER = "assetops_backend.outcomes.warnings.KINDS"

#: CH5b1-R Q1: each `ENTRIES` key with no measure and no lifecycle mechanism -> (producer, owner). A `SIGNAL:` producer
#: is the module that passes the key to `SignalFact(...)`. The other keys become chain nodes in CH-8.
NOT_CHAIN_SOURCED: dict[str, tuple[str | None, str]] = {
    "SIGNAL:EVIDENCE_GAP": ("assetops_backend.site_outcomes.mini", "CH-8"),
    "SIGNAL:EVIDENCE_READINESS": (None, "Architect ruling pending (CH-5b1 packet D1)"),
    "WARNING:REPEATED_MAINTENANCE_NO_RESULT": (WARNING_PRODUCER, "CH-8"),
    "WARNING:PLAN_OVERDUE": (WARNING_PRODUCER, "CH-8"),
    "WARNING:PLAN_DUE_SOON": (WARNING_PRODUCER, "CH-8"),
    "WARNING:BATTERY_NEAR_RESERVE": (WARNING_PRODUCER, "CH-8"),
    "WARNING:CHARGER_FAULT_OVERDUE_INSPECTION": (WARNING_PRODUCER, "CH-8"),
    "WARNING:CONNECTOR_OUT_OF_SERVICE": (WARNING_PRODUCER, "CH-8"),
    "WARNING:PEAK_NEAR_IMPORT_LIMIT": (WARNING_PRODUCER, "CH-8"),
    "WARNING:CHARGERS_MOSTLY_IDLE": (None, "CH-6a1"),
}
#: The only rows allowed `producer=None` ("known gap: no producer"). CH5b1-R allows CHARGERS_MOSTLY_IDLE (CH-6a1).
#: SIGNAL:EVIDENCE_READINESS has no emitter on main either; it is listed here as CH-5b1 Known Deviation D1.
KNOWN_GAPS = frozenset({"WARNING:CHARGERS_MOSTLY_IDLE", "SIGNAL:EVIDENCE_READINESS"})

_RULE_INPUT = {"by_role": "roles", "by_analytic": "analytics", "by_job_domain": "job_domains",
               "by_assumption_key": "assumption_keys"}


class ChainGraphError(ValueError):
    """The declared chain graph is broken. `rule` and `key` name the first failure."""

    def __init__(self, rule: str, key: str, message: str) -> None:
        super().__init__(f"chain graph {rule}: {key}: {message}")
        self.rule, self.key = rule, key


@dataclass(frozen=True)
class Problem:
    rule: str
    key: str
    message: str


@dataclass(frozen=True)
class GraphInputs:
    register: Any                                       # chain.events.EventRegister
    measures: Mapping[str, Any]                         # key -> chain.measures.MeasureSpec
    adapter_keys: frozenset[str]
    clean_day_measures: Mapping[str, tuple[str, ...]]   # lifecycle mechanism -> measures
    entries: Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]]
    outcome_keys: frozenset[str]
    aliases: Mapping[str, Mapping[str, str]]
    thread_signal_key: Callable[[str], str]
    warning_kinds: frozenset[str]
    module_source: Callable[[str], str | None]          # dotted module -> its source text (None: not found)
    not_chain_sourced: Mapping[str, tuple[str | None, str]] = None  # type: ignore[assignment]
    known_gaps: frozenset[str] = KNOWN_GAPS

    def table(self) -> Mapping[str, tuple[str | None, str]]:
        return NOT_CHAIN_SOURCED if self.not_chain_sourced is None else self.not_chain_sourced


def emits_signal(source: str, key: str) -> bool:
    """True when the module source passes `key` as the first argument of a `SignalFact(...)` call."""
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "SignalFact"
                and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == key):
            return True
    return False


def chain_keys(g: GraphInputs) -> set[str]:
    """The `ENTRIES` keys that a declared measure or lifecycle mechanism sources."""
    keys = {g.thread_signal_key(m) for m in g.clean_day_measures}
    keys |= {"MEASURE:" + k for k in g.measures}
    return keys & set(g.entries)


def _producer_problem(g: GraphInputs, key: str, producer: str | None) -> str | None:
    if producer is None:
        return None if key in g.known_gaps else "producer is None and the key is not a ruled known gap"
    if key.startswith("WARNING:"):
        if producer != WARNING_PRODUCER:
            return f"a warning's producer must be {WARNING_PRODUCER}"
        kind = key.split(":", 1)[1]
        return None if kind in g.warning_kinds else f"warning kind {kind} is not in warnings.KINDS"
    if key.startswith("SIGNAL:"):
        source = g.module_source(producer)
        if source is None:
            return f"producer module {producer} not found"
        return None if emits_signal(source, key) else f"{producer} does not emit SignalFact({key!r}, ...)"
    return "only WARNING: and SIGNAL: keys can be not chain-sourced"


def problems(g: GraphInputs) -> list[Problem]:
    out: list[Problem] = []
    add = lambda rule, key, msg: out.append(Problem(rule, key, msg))  # noqa: E731
    for key, spec in sorted(g.measures.items()):
        if spec.adapter not in g.adapter_keys:
            add("reference", key, f"adapter {spec.adapter} is not a registered measure adapter")
        if key not in g.register.inputs:
            add("measure_input", key, "measure has no event-register input")
    for key in sorted(set(g.register.inputs) - set(g.measures)):
        add("measure_input", key, "register input names no declared measure")
    for mech, measures in sorted(g.clean_day_measures.items()):
        for m in measures:
            if m not in g.measures:
                add("lifecycle_measure", mech, f"clean-day measure {m} is not declared")
        if g.thread_signal_key(mech) not in g.entries:
            add("orphan", mech, f"lifecycle mechanism has no outcome-map entry {g.thread_signal_key(mech)}")
    for key, (moves, checked) in sorted(g.entries.items()):
        for role, keys in (("moves", moves), ("checked", checked)):
            for k in keys:
                ok = (k in g.outcome_keys or k in g.aliases or (k == "@LINKED" and role == "checked"))
                if not ok:
                    add("reference", key, f"{role} outcome {k} does not resolve")
    sourced, table = chain_keys(g), g.table()
    for key in sorted(g.entries):
        if key in sourced:
            if key in table:
                add("not_chain_sourced", key, "stale row: the key is now chain-sourced")
        elif key.startswith("FINDING:"):
            add("entry_source", key, "Finding mechanism has no thread-lifecycle entry")
        elif key.startswith("MEASURE:"):
            add("entry_source", key, "measure is not declared")
        elif key not in table:
            add("not_chain_sourced", key, "no measure or mechanism, and no NOT_CHAIN_SOURCED row")
    for key, (producer, _owner) in sorted(table.items(), key=lambda kv: kv[0]):
        if key not in g.entries:
            add("not_chain_sourced", key, "row names a key that is not in ENTRIES")
            continue
        if key in sourced:
            continue
        msg = _producer_problem(g, key, producer)
        if msg is not None:
            add("not_chain_sourced", key, msg)
    return out


def check(g: GraphInputs) -> list[str]:
    """Raise `ChainGraphError` on the first problem; return the report lines (known gaps, not chain-sourced keys)."""
    found = problems(g)
    if found:
        p = found[0]
        raise ChainGraphError(p.rule, p.key, p.message)
    lines = [f"chain graph OK: {len(g.measures)} measures, {len(g.clean_day_measures)} lifecycle mechanisms, "
             f"{len(g.entries)} outcome-map entries ({len(chain_keys(g))} chain-sourced)"]
    for key, (producer, owner) in sorted(g.table().items()):
        if producer is None:
            lines.append(f"known gap: no producer: {key} (owner {owner})")
        else:
            lines.append(f"not chain-sourced: {key} <- {producer} (owner {owner})")
    return lines


# --- diagram ------------------------------------------------------------------------------------------------------

def edges(g: GraphInputs) -> tuple[list[list[str]], list[tuple[str, str, str]]]:
    """Columns (events, measures, mechanisms, map keys, outcomes) and edges (src, dst, style), sorted."""
    reg = g.register
    events = sorted(k for k, r in reg.events.items() if r.measures is not None)
    measures = sorted(g.measures)
    mechs = sorted(g.clean_day_measures)
    keys = sorted(g.entries)
    outcomes = sorted({k for mv, ck in g.entries.values() for k in (*mv, *ck)})
    out: list[tuple[str, str, str]] = []
    for ev in events:
        rule = reg.events[ev].measures
        for m in measures:
            inp = reg.inputs.get(m)
            if inp is None:
                continue
            if rule == "all_of_site" or (rule in _RULE_INPUT and getattr(inp, _RULE_INPUT[rule])):
                out.append((ev, "measure:" + m, "solid"))
    for mech in mechs:
        for m in g.clean_day_measures[mech]:
            out.append(("measure:" + m, "mech:" + mech, "solid"))
        out.append(("mech:" + mech, "key:" + g.thread_signal_key(mech), "solid"))
    for key in keys:
        mv, ck = g.entries[key]
        out += [("key:" + key, "out:" + k, "solid") for k in mv]
        out += [("key:" + key, "out:" + k, "dashed") for k in ck]
    cols = [events, ["measure:" + m for m in measures], ["mech:" + m for m in mechs],
            ["key:" + k for k in keys], ["out:" + k for k in outcomes]]
    return cols, sorted(set(out))


def _label(node: str) -> str:
    return node.split(":", 1)[1] if node.split(":", 1)[0] in ("measure", "mech", "key", "out") else node


def render_dot(g: GraphInputs) -> str:
    cols, es = edges(g)
    lines = ["// Generated by `python -m assetops_backend.chain.graph dot`. Do not edit.",
             "digraph chain {", "  rankdir=LR;", '  node [shape=box, fontname="Helvetica", fontsize=10];']
    for i, col in enumerate(cols):
        lines.append(f"  subgraph col{i} {{ rank=same;")
        for n in col:
            style = ', style=dashed' if n.startswith("key:") and _label(n) in g.table() else ""
            lines.append(f'    "{n}" [label="{_label(n)}"{style}];')
        lines.append("  }")
    for a, b, style in es:
        lines.append(f'  "{a}" -> "{b}"' + (" [style=dashed];" if style == "dashed" else ";"))
    lines.append("}")
    return "\n".join(lines) + "\n"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_svg(g: GraphInputs) -> str:
    """A deterministic column layout (no Graphviz): one column per node kind, edges as cubic curves."""
    cols, es = edges(g)
    heads = ["Register events", "Measures", "Lifecycle mechanisms", "Outcome-map keys", "Outcomes"]
    col_w, box_w, row_h, box_h, top = 260, 220, 26, 20, 50
    pos: dict[str, tuple[int, int]] = {}
    for i, col in enumerate(cols):
        for j, n in enumerate(col):
            pos[n] = (20 + i * col_w, top + j * row_h)
    width = 20 + len(cols) * col_w
    height = top + max(len(c) for c in cols) * row_h + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           'font-family="Helvetica, Arial, sans-serif" font-size="11">',
           "<!-- Generated by `python -m assetops_backend.chain.graph dot`. Do not edit. -->",
           f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
           f'<text x="20" y="{height - 12}" fill="#555">Solid: feeds / moves. Dashed: checked against. Dashed box: '
           'not chain-sourced yet (graph.NOT_CHAIN_SOURCED).</text>']
    for i, h in enumerate(heads):
        out.append(f'<text x="{20 + i * col_w}" y="28" font-weight="bold" fill="#222">{_esc(h)}</text>')
    for a, b, style in es:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        x1, y1, x2, y2 = x1 + box_w, y1 + box_h // 2, x2, y2 + box_h // 2
        mid = (x1 + x2) // 2
        dash = ' stroke-dasharray="4 3"' if style == "dashed" else ""
        out.append(f'<path d="M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}" fill="none" stroke="#8a94a6"{dash}/>')
    table = g.table()
    for n, (x, y) in pos.items():
        dash = ' stroke-dasharray="4 3"' if n.startswith("key:") and _label(n) in table else ""
        out.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="3" fill="#f4f6fa" stroke="#4a5568"'
                   f'{dash}/>')
        out.append(f'<text x="{x + 6}" y="{y + 14}" fill="#1a202c">{_esc(_label(n))}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m assetops_backend.chain.graph")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    d = sub.add_parser("dot")
    d.add_argument("--svg", action="store_true", help="print the SVG instead of the DOT text")
    args = p.parse_args(argv)
    from assetops_backend.chain.composition import declared_graph_inputs

    g = declared_graph_inputs()
    try:
        lines = check(g)
    except ChainGraphError as exc:
        print(f"FAIL {exc}")
        return 1
    if args.cmd == "dot":  # stdout only: the backend writes no files (tools/chain_graph_render.py writes the Docs copy)
        sys.stdout.write(render_svg(g) if args.svg else render_dot(g))
        return 0
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
