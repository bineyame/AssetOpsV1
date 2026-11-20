"""Independent checks for the Layer 4 design pack (rev 13; owner, twelfth message, rule 3).

Design-pack tool, not product code. The checker never imports, copies or calls evaluate_structure.py, and holds no expected
figure. Every expected value comes from independent_model.py, which a separate helper wrote from structure-specification.md
and the manifest alone. Against that independent recomputation the checker compares:

  1. evaluator(): every value the independent model computes, against the evaluator's output file derived-values.json;
  2. stated(): every figure the manifest states as a copy (site periods, Protect and O2 tables, rows, allocations), and the
     manifest identities that need no model (bridges sum to variances, sites to portfolios);
  3. rights_terms(): every right without a notified claim carries a notice deadline or a notice term, and every open deadline
     has deciding options;
  4. narratives(): rendered manifest strings carry {fig:path} / {rec:path} placeholders that resolve, and state no evaluated
     figure as a literal;
  5. anchors(): every <!--fig:path--> figure in the documents equals the independent value at that path, signed; every
     <!--figx:expression--> figure equals that arithmetic (+ - * / and brackets) over {independent paths}, signed (the
     expression must use at least one path, its value must move when a path value moves, and its only number literals are
     round()'s places and the unit factor 100, so no expected figure can sit in a tag); record tags
     are manifest money records; headline paths are tagged; no untagged copy of an evaluated plan or option money figure
     (with or without cents) or of an O2 percentage appears in a figure-bearing document;
  6. documents(): untagged money figures in main §2-§10, the walkthroughs and the transition document's §1-§4 are
     independent values or declared inputs;
  7. workflow(): the demonstration workflow (demo_workflow) obeys the design's ownership, capital and release rules
     (OD-5, OD-16, OD-17; design §2.4 step 4);
  8. homes(): every node has exactly one named home category, measures take their objective's heading, no money sits under
     Protect or Assure, each decision's heading is its lever's home, and the snapshot record is well formed (design rev 16.11
     §2.0, §2.8; OD-21, OD-23);
  9. factor_map(): vertical-factor-map.md covers every lever of the brief's catalogues L2.2-L2.4, maps each in-scope lever to
     factors that exist in the registry (or a manifest measure or potential entry) with a heading equal to the registry's
     and a Site and a portfolio read; the traceability CSV's factor column uses the same IDs and its text passes the naming
     lint (OD-6). It proves itself on planted copies every run.
 10. empty_states(): every leaf names what fills it, what its absence means and the slice that makes its source reachable; no
     leaf declared MISSING has a numeric fallback, and every numeric fallback is a held-source zero or an option's identity
     (rule R4, "Unknown is not zero"); every value-chain stage and leak is carried by a node, a potential entry, a deferred stage
     with its slice and trigger, or a reconciled zero; every missing condition, assumption and estimated line has its record;
     missing-records.json names a record, a cause and a slice for each entry and covers every side derived-values.json leaves
     not decomposed (structure-specification.md §3.1, rev 16.13). It proves itself on planted copies every run.
Run:  python3 check_manifest.py [manifest]   Exit 0 = all pass.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys
from decimal import Decimal as D

import yaml

failures: list[str] = []
passes = 0


def eq(label, a, b):
    global passes
    if a is None or b is None:
        failures.append(f"{label}: {a} != {b}"); return
    try:
        same = D(str(a)).quantize(D("0.001")) == D(str(b)).quantize(D("0.001"))
    except Exception:
        same = a == b
    if same:
        passes += 1
    else:
        failures.append(f"{label}: {a} != {b}")


def check(label, cond):
    global passes
    if cond:
        passes += 1
    else:
        failures.append(label)


def get(tree, path):
    """Dotted path; keys match case-insensitively (case keys True/False); 'x.value' on a number returns the number."""
    cur = tree
    path = re.sub(r"\[([^\]]+)\]", r".\1", path)   # x[key] is x.key (placeholder syntax)
    for part in re.split(r"\.(?![^\[]*\])", path):
        if isinstance(cur, dict):
            if part in cur:
                cur = cur[part]; continue
            low = {str(k).lower(): k for k in cur}
            if part.lower() in low:
                cur = cur[low[part.lower()]]; continue
            return None
        if part == "value" and isinstance(cur, (int, float)):
            return cur
        return None
    return cur


# ---------------- 1. the evaluator's output against the independent recomputation ----------------
SCHEMA_ONLY_IN_MODEL = {"default_key", "protective_detail", "total_violation", "downside_drops", "tenant", "right_states", "lapsed_rights",
                        "site", "not_valued_in_money_items"}   # model-side bookkeeping with no evaluator counterpart
# The two programs name two option fields differently (a naming map only; no value is shared): the model's `valued_in_money`
# is the evaluator's `money_changes`; the model's `money_changes` (Δ ≠ 0) and `value` (the formula for every option) have no
# evaluator field, whose `value` is the plan-facing value (admissible or chosen). Statuses compare by their spec prefix.
RENAME = {"valued_in_money": "money_changes"}
NOT_COMPARED = {"money_changes", "value"}


def evaluator(ref, dv):
    def walk(r, path):
        if isinstance(r, dict):
            for k, v in r.items():
                if str(k) in SCHEMA_ONLY_IN_MODEL or (path.startswith("options.") and path.count(".") == 1 and str(k) in NOT_COMPARED):
                    continue
                k2 = RENAME.get(str(k), str(k)) if path.startswith("options.") and path.count(".") == 1 else k
                walk(v, f"{path}.{k2}" if path else str(k2))
        elif isinstance(r, list):
            got = get(dv, path)
            check(f"evaluator {path} = independent {r} (got {got})", isinstance(got, list) and [str(x) for x in got] == [str(x) for x in r])
        else:
            got = get(dv, path)
            if isinstance(got, dict) and "chosen" in got:   # protective choice: the evaluator reports {chosen, how, ...}
                got = got["chosen"]
            if isinstance(got, dict) and "value" in got and len(got) <= 2:   # sensitivity entry {value, valued_options}
                got = got["value"]
            if path.endswith(".status") and isinstance(r, str):
                check(f"evaluator {path} status {got!r} begins with independent {r!r}", isinstance(got, str) and got.startswith(r))
            elif isinstance(r, (int, float)) and not isinstance(r, bool):
                eq(f"evaluator {path}", got, r)
            else:
                check(f"evaluator {path} = independent {r!r} (got {got!r})", got == r or str(got) == str(r))
    walk(ref, "")


# ---------------- 2. stated copies in the manifest and model-free identities ----------------
def identities(t):
    total = D(0)
    for s in t["sites"]:
        p = s["period"]
        if "bridge" in p:
            eq(f"{s['site']} bridge sums to variance", sum(D(str(b["amount"])) for b in p["bridge"]), p["variance"])
        total += D(str(p["variance"]))
    eq(f"{t['tenant']} portfolio variance = Σ sites", t["portfolio"]["variance"], total)
    for m in t["portfolio"]["protect"]["measures"] + t["portfolio"].get("service_cost_lines", []):
        if "sites" in m and isinstance(m.get("portfolio"), (int, float)):
            eq(f"{t['tenant']} protect {m['id']} portfolio = Σ sites", m["portfolio"], sum(D(str(v)) for v in m["sites"].values()))
        if m.get("class") == "EXPOSURE":
            check(f"{t['tenant']} protect {m['id']}: at-stake values listed, never summed", m.get("portfolio") in (None, "LISTED") or "items" in m)
    for s_ in t["sites"]:
        for b in (s_.get("incident") or {}).get("batches", []):
            if "exposed_value" in b:
                eq(f"{s_['site']} {b['batch']} exposed value = crates x declared value per crate", b["exposed_value"], D(str(b["crates"])) * D(str(b["declared_value_per_crate"])))


def rows_of(t):
    rows = {o["id"]: o for s_ in t["sites"] for blk in ("decision", "entitlement") for o in (s_.get(blk) or {}).get("options", [])}
    for s_ in t["sites"]:
        for e in s_.get("entitlements", []):
            rows.update({o["id"]: o for o in e.get("options", [])})
    return rows


def stated(doc, ref):
    NODE_OF = {"billed_kwh": "billed_kwh", "metered_kwh": "metered_kwh", "revenue": "revenue", "collected": "collected", "diesel_l": "diesel_l",
               "diesel_cost": "fuel_cost", "kwh": "kwh", "energy": "energy", "contribution": "contribution", "energy_cost": "energy_cost",
               "total": "cost_to_serve", "departures_required": "departures_required", "departures_met": "departures_met"}
    EVO = doc["evaluation"]["options"]
    O = ref["options"]
    for t in doc["tenants"]:
        tid = t["tenant"]
        identities(t)
        for s_ in t["sites"]:
            for k in ("plan", "actual"):
                r, ev_ = s_["period"][k], ref["sites"][f"{tid}/{s_['site']}"][k]
                if ev_["status"] != "evaluated":
                    check(f"{tid}/{s_['site']} {k}: labelled not decomposed", ev_["status"].startswith("not decomposed"))
                    continue
                for field, node in NODE_OF.items():
                    if field in r and node in ev_["nodes"]:
                        eq(f"stated {tid}/{s_['site']} {k} {field}", r[field], ev_["nodes"][node])
        for m in t["portfolio"]["protect"]["measures"] + t["portfolio"].get("service_cost_lines", []):
            if "node" not in m:
                continue
            for side, key in (("actual", "sites"), ("november_to_date", "november_to_date")):
                for site, v in (m.get(key) or {}).items():
                    if site in ("portfolio", "detail") or not isinstance(v, (int, float)):
                        continue
                    node = ((ref["sites"][f"{tid}/{site}"].get(side) or {}).get("nodes") or {}).get(m["node"])
                    eq(f"stated Protect {tid}/{site} {side} {m['id']}", v, node)
        for m in t["portfolio"]["operations"]["measures"]:
            ev_ = (ref["operations"].get(tid) or {}).get(m["id"])
            if ev_ is None:
                continue
            eq(f"stated O2 {tid} {m['id']} portfolio", m.get("portfolio_pct", m.get("portfolio")), ev_["portfolio"])
            for s, v in (m.get("sites_pct") or {}).items():
                eq(f"stated O2 {tid} {m['id']} {s}", v, ev_["sites"][s])
        rows = rows_of(t)
        for oid, row in rows.items():
            e = O.get(oid)
            if e is None:
                continue
            econ = row.get("economics", {})
            for key in ("net_12m", "net_contract"):
                if key in econ and e["value"] is not None:
                    eq(f"stated {oid} value", econ[key], e["value"])
            if "net_12m" in row and e["value"] is not None:
                eq(f"stated {oid} value", row["net_12m"], e["value"])
            for key in ("net_monthly", "monthly", "saving_monthly"):
                if key in econ:
                    eq(f"stated {oid} monthly change", econ[key], e["monthly_or_horizon_change"])
            if "energy_cost_monthly" in econ and "energy_bill_option" in e:
                eq(f"stated {oid} monthly bill", econ["energy_cost_monthly"], e["energy_bill_option"])
            if "residual_cost" in row:
                if EVO.get(oid, {}).get("is_reference"):
                    eq(f"stated {oid} operator one-off (reference path)", row["residual_cost"], e["operator_one_off"])
                else:
                    eq(f"stated {oid} operator cost", row["residual_cost"],
                       D(str(e["operator_one_off"])) + max(-D(str(e["monthly_or_horizon_change"])) * D(str(e["months"])), D(0)))
            for f in ("restore_by", "restore_date"):
                if f in row and e["restore_date"]:
                    check(f"{oid} stated restore {row[f]} = independent {e['restore_date']}", e["restore_date"] == row[f])
            for sk, sv in (row.get("sensitivity") or {}).items():
                key = {"diesel_minus_20pct_net_12m": "diesel_minus_20pct", "feasible_fuel_160l_net_12m": "feasible_fuel_160l"}.get(sk)
                if key:
                    eq(f"stated {oid} sensitivity {key}", sv, (e.get("sensitivities") or {}).get(key))
            if "buses_short" in row:
                eq(f"stated {oid} buses short a night", row["buses_short"], e["bound"]["buses_short_per_night"])
            if "deliverable_kwh" in row and oid.startswith("RUI"):
                eq(f"stated {oid} deliverable a night", row["deliverable_kwh"], e["bound"]["deliverable_kwh_night"])
            if "avoided_capex" in row:
                eq(f"stated {oid} avoided purchase = RUI-4CHARGERS one-off", row["avoided_capex"], O["RUI-4CHARGERS"]["operator_one_off"])
            if "expected_penalties" in row:
                eq(f"stated {oid} penalties", row["expected_penalties"], -D(str(e["monthly_or_horizon_change"])))
        for pe in t["portfolio"].get("protect_effects", []):
            check(f"{pe['decision']}: horizon, measure, class declared", all(k in pe for k in ("horizon", "measure", "class", "options")))
            for o, v in pe["options"].items():
                if o not in O or not isinstance(v, (int, float)):
                    continue
                got = O[o]["protect"].get(pe["measure"])
                if got is None:
                    check(f"{pe['decision']} {o}: non-structure quantity only as a flagged design value or record count", bool(pe.get("design_value")) or pe.get("class") == "RECORDED")
                else:
                    eq(f"stated Protect effect {pe['decision']} {o}", v, got)
        if tid in ref["plans"]:
            pl, al = ref["plans"][tid], t["portfolio"]["allocation"]
            dflt = pl["default"]
            eq(f"stated {tid} plan spend", al["spend"], dflt["spend"])
            if "modelled_12m_change" in al:
                eq(f"stated {tid} plan value", al["modelled_12m_change"]["total"], dflt["value"])
                for o, v in al["modelled_12m_change"].items():
                    if o in O:
                        eq(f"stated {tid} plan item {o}", v, O[o]["value"])
            if "valued_option_costs" in al:
                eq(f"stated {tid} valued option costs", al["valued_option_costs"], dflt["valued_option_costs"])
                eq(f"stated {tid} not valued in money", al["unvalued_spend"], dflt["not_valued_in_money"])
            for o, v in (al.get("spend_breakdown") or {}).items():
                if o in O:
                    eq(f"stated {tid} spend line {o}", v, O[o]["operator_one_off"])
            used = al.get("crew_visits_used", al.get("technician_visits_used"))
            if used is not None:
                eq(f"stated {tid} crew visits used", used, dflt["crew_visits_used"])
            rec = set(al.get("recommended", []))
            for o in dflt["items"]:
                check(f"{tid}: plan item {o} is in the stated recommended set", o in rec)
            if "downside" in al:
                eq(f"stated {tid} downside", al["downside"]["value"], pl["downside"])
                for k, v in (al["downside"].get("others") or {}).items():
                    eq(f"stated {tid} sensitivity {k}", v, get(pl["sensitivity_values"], k))
            for sw in al.get("switches", []):
                for case, c in (sw.get("cases") or {}).items():
                    b, l = case.split("/")
                    got = get(pl["switch_cases"], f"{b}/{'True' if l == 'yes' else 'False'}")
                    if got is None:
                        check(f"stated {tid} case {case} exists independently", False); continue
                    eq(f"stated {tid} case {case} spend", c["spend"], got["spend"])
                    eq(f"stated {tid} case {case} value", c["value"], got["value"])
            # dispositions written on rows agree with the independent plan
            items_any = {o for c in pl["switch_cases"].values() for o in (c["items"] or [])}
            for d in doc["plans"][tid]["decisions"]:
                for o in d["options"]:
                    disp = (rows.get(o) or {}).get("disposition")
                    if d["kind"] == "comparator":
                        check(f"{tid}: comparator {o} {disp}: RECOMMENDED only if admissible", disp != "RECOMMENDED" or O[o]["admissible"])
                    elif disp == "RECOMMENDED":
                        check(f"{tid}: {o} RECOMMENDED is in the independent plan", o in dflt["items"])
                    elif disp == "CONDITIONAL":
                        check(f"{tid}: {o} CONDITIONAL is in some case and not the default", o in items_any and o not in dflt["items"])
                    elif disp in ("REJECTED", "DEFERRED", "ACCEPTABLE"):
                        check(f"{tid}: {o} {disp} is not in the independent plan", o not in dflt["items"])
                        if disp == "ACCEPTABLE":
                            check(f"{tid}: {o} ACCEPTABLE is admissible", O[o]["admissible"])
        pc, ch = ref["portfolio"][tid]["actual"]["sums"], t["portfolio"].get("chain", {})
        for field in ("metered_kwh", "billed_kwh", "revenue", "collected", "cost_to_serve", "departures_met"):
            if field in ch and field in pc:
                eq(f"stated portfolio composition {tid} {field}", ch[field], pc[field])
        for key, node in (("actual_contribution", "contribution"), ("actual_cost", "cost_to_serve")):
            if key in t["portfolio"] and node in pc:
                eq(f"stated portfolio composition {tid} {key}", t["portfolio"][key], pc[node])
        if "cost_per_departure_actual" in t["portfolio"]:
            eq(f"stated portfolio composition {tid} cost per departure", t["portfolio"]["cost_per_departure_actual"], pc["cost_per_departure_met"])
    # records consistent with the structure: energy delivered a night never above what the structure says was deliverable
    for key, site in ref["sites"].items():
        for side, ev_ in site.items():
            nd = ev_.get("nodes") or {}
            if "scheduled_kwh_night" in nd:
                check(f"{key} {side}: recorded kWh a night {nd['scheduled_kwh_night']} <= deliverable {nd['deliverable_kwh_night']}",
                      D(str(nd["scheduled_kwh_night"])) <= D(str(nd["deliverable_kwh_night"])))
    for tid, pl in ref["plans"].items():
        check(f"{tid}: the default plan is feasible", pl["default"]["value"] is not None)


# ---------------- 3. rights terms ----------------
NOTIFIED = {"NOTIFIED", "ACKNOWLEDGED", "ACCEPTED", "DENIED", "REJECTED"}   # spec §4.1 (read from the spec, not the evaluator)


def rights_terms(doc, ref):
    for t in doc["tenants"]:
        for s_ in t["sites"]:
            es = ([s_["entitlement"]] if "entitlement" in s_ else []) + s_.get("entitlements", []) + \
                 ([s_["incident"]["entitlement"]] if isinstance((s_.get("incident") or {}).get("entitlement"), dict) else [])
            for e in es:
                if "asset" not in e or e.get("claim_state") in NOTIFIED or e.get("eligibility") != "POTENTIALLY_COVERED":
                    continue
                check(f"right {e['asset']}: un-notified, so it declares notice_deadline or notice_term", bool(e.get("notice_deadline") or e.get("notice_term")))
                if e.get("notice_deadline"):
                    check(f"right {e['asset']}: open deadline has deciding options", bool(ref["deciders"].get(e["asset"])))


# ---------------- 4. rendered manifest strings ----------------
PLACEHOLDER = re.compile(r"\{(fig|rec):(-?)([^}]+)\}")


def manifest_get(doc, path):
    cur = doc
    for part in re.findall(r"[^.\[\]]+|\[[^\]]+\]", path):
        if part.startswith("["):
            key = part[1:-1]
            if isinstance(cur, list):
                cur = cur[int(key)] if key.isdigit() else next((x for x in cur if isinstance(x, dict) and key in (x.get("tenant"), x.get("site"), x.get("id"), x.get("batch"), x.get("asset"), x.get("item"))), None)
            elif isinstance(cur, dict):
                cur = cur.get(key)
        else:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def narratives(doc, ref):
    n = 0
    keys = key_figures(ref)

    def scan(o, path):
        nonlocal n
        if isinstance(o, dict):
            for k, v in o.items():
                scan(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan(v, f"{path}[{i}]")
        elif isinstance(o, str):
            for m in PLACEHOLDER.finditer(o):
                n += 1
                val = get(ref, m.group(3)) if m.group(1) == "fig" else manifest_get(doc, m.group(3))
                check(f"placeholder {m.group(0)} at {path} resolves", val is not None)
            bare = PLACEHOLDER.sub("", o)
            for m in re.finditer(r"(?<![\w.:/-])(\d{1,3}(?:,\d{3})*\.\d{2}|\d{1,3}(?:,\d{3})+)(?![\d%])", bare):
                v = D(m.group(1).replace(",", "")).quantize(D("0.01"))
                check(f"manifest string {path}: evaluated figure {m.group(1)} written as a literal (use a placeholder)", v not in keys)
    scan(doc["tenants"], "tenants")
    check(f"rendered manifest strings carry placeholders ({n})", n > 0)


# ---------------- 5. document anchors ----------------
FIG_DOCS = ("layer4-transformation-design.md", "worked-portfolios.md", "design-appendix.md", "economic-metric-and-effect-contracts.md", "domain-and-decision-models.md",
            "phase-plan-and-acceptance.md", "integration-source-to-canonical-design.md", "demo-build-cost-plan.md", "interactive-mockup-vNEXT/walkthroughs.md",
            "design-questions-and-decisions.md", "product-transition-and-roadmap.md")
REQUIRED = {"layer4-transformation-design.md": ["sites.lakeside-power/Kobo.plan.nodes.contribution", "sites.lakeside-power/Kobo.actual.nodes.contribution",
                                             # rev 16.2: Lakeside's plan figures live in worked-portfolios.md (required there)
                                             "portfolio.lakeside-power.actual.sums.contribution", "options.KOB-STOPSOC.value"],
            # rev 16: the three worked portfolios and the demonstration world moved to the companion file
            "worked-portfolios.md": [f"plans.{t}.default.{k}" for t in ("lakeside-power", "harvest-cold", "metro-bus")
                                                for k in ("spend", "value", "crew_visits_used")] +
            ["sites.lakeside-power/Kisiwa.actual.nodes.obligation_hours_without_redundancy", "sites.lakeside-power/Mto.actual.nodes.obligation_hours_without_redundancy",
             "sites.harvest-cold/Room B · Thika.actual.nodes.nights_without_backup_cover", "sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed",
             "sites.metro-bus/Kasarani.november_to_date.nodes.penalties"],
            "interactive-mockup-vNEXT/walkthroughs.md": [f"plans.{t}.default.{k}" for t in ("lakeside-power", "harvest-cold", "metro-bus") for k in ("spend", "value")] +
            ["sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed", "sites.metro-bus/Kasarani.november_to_date.nodes.penalties"],
            "design-questions-and-decisions.md": ["owner_question_variants.Q15.B.lakeside-power.cases.6500/True.value", "owner_question_variants.Q15.B.lakeside-power.cases.6500/True.value_change_vs_applied",
                                                  "owner_question_variants.Q15.C.lakeside-power.cases.5000/False.value"],
            "product-transition-and-roadmap.md": ["sites.lakeside-power/Kobo.plan.nodes.contribution", "sites.lakeside-power/Kobo.actual.nodes.contribution",
                                                  "plans.lakeside-power.default.spend", "plans.lakeside-power.default.value", "plans.lakeside-power.downside"]}
ANCHOR = re.compile(r"(?:(?<=[\s(=:*$|/,;])|^)((?:−|\+|-(?=\d))\s?)?\$?([\d,]*\d(?:\.\d+)?)(%?)(\**)<!--fig:(-?)([^>]+)-->", re.M)
FIGX = re.compile(r"(?:(?<=[\s(=:*$|/,;])|^)((?:−|\+|-(?=\d))\s?)?\$?([\d,]*\d(?:\.\d+)?)(%?)(\**)<!--figx:([^>]+)-->", re.M)
RECORDS: set = set()


def expr_value(ref, expr):
    """Arithmetic over {independent paths}: + - * /, brackets and round(x, places) only, in Decimal. Returns (value, None),
    or (None, reason) when a path is missing, the expression uses anything else, uses no path, does not depend on its paths,
    holds a number literal other than round()'s places or the unit factor 100, or fails to evaluate (e.g. division by zero).
    Values come from the independent model only; the tag can hold no expected figure."""
    import ast, decimal
    vals, names = {}, {}

    def sub(m):   # one name per distinct path, so {a}-{a} is seen as constant
        path = m.group(1).strip()
        if path not in names:
            v = get(ref, path)
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise KeyError(path)
            names[path] = f"v{len(names)}"; vals[names[path]] = D(str(v))
        return f" {names[path]} "
    try:
        tree = ast.parse(re.sub(r"\{([^}]+)\}", sub, expr.replace("−", "-")).strip(), mode="eval")
    except KeyError as e:
        return None, f"path {e} is not an independent number"
    except SyntaxError:
        return None, "not an expression"
    if not vals:
        return None, "uses no independent path"

    def ev(n, env, rounding=True):
        if isinstance(n, ast.Expression): return ev(n.body, env, rounding)
        if isinstance(n, ast.Name) and n.id in env: return env[n.id]
        if isinstance(n, ast.Constant) and type(n.value) in (int, float) and n.value == 100: return D(100)   # unit factor only
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub): return -ev(n.operand, env, rounding)
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "round" and len(n.args) == 2
                and isinstance(n.args[1], ast.Constant) and type(n.args[1].value) is int):   # round(x, places), half up
            x = ev(n.args[0], env, rounding)
            return x.quantize(D(1).scaleb(-n.args[1].value), rounding="ROUND_HALF_UP") if rounding else x
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left, env, rounding), ev(n.right, env, rounding)
            ops = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b, ast.Div: lambda: a / b}
            if type(n.op) in ops: return ops[type(n.op)]()
        raise ValueError(ast.dump(n)[:60])
    def has_path(n): return any(isinstance(x, ast.Name) and x.id in vals for x in ast.walk(n))

    def moves(n):   # some path, perturbed alone, changes this subexpression (unrounded)
        base = ev(n, vals, rounding=False)
        for k in vals:
            try:
                if ev(n, {**vals, k: vals[k] * D("1.1") + D("0.37")}, rounding=False) != base:
                    return True
            except (ArithmeticError, decimal.DecimalException):
                return True
        return False
    try:
        value = ev(tree, vals)
        for n in ast.walk(tree):
            for c in ast.iter_child_nodes(n):   # 100 only as a factor or divisor of a term that holds a path
                if isinstance(c, ast.Constant) and not (n is not tree and isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mult, ast.Div))
                                                         and has_path(n.right if c is n.left else n.left)) \
                        and not (isinstance(n, ast.Call) and c is n.args[1]):
                    return None, "a number literal stands outside a scaled path term"
            if isinstance(n, (ast.BinOp, ast.UnaryOp, ast.Call)) and not moves(n):
                return None, "a part of it does not depend on its paths"
    except ValueError as e:
        return None, f"uses something other than paths, + - * /, round(x, places) and 100: {e}"
    except (ArithmeticError, decimal.DecimalException) as e:
        return None, f"does not evaluate ({type(e).__name__})"
    return value, None
DOC: dict = {}


def key_figures(ref):
    """Money figures of plans, options and owner-question variants (abs >= 50), computed independently."""
    ks = set()

    def add(x):
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            ks.add(abs(D(str(x))))
    for pl in ref["plans"].values():
        for blk in [pl["default"], *pl["switch_cases"].values()]:
            for k in ("value", "spend", "valued_option_costs", "not_valued_in_money"):
                add(blk.get(k))
        for v in pl["sensitivity_values"].values():
            add(v)
        add(pl.get("downside"))
    for o in ref["options"].values():
        for k in ("value_if_admissible", "operator_one_off", "net_one_off", "monthly_or_horizon_change"):
            add(o.get(k))
        for v in (o.get("sensitivities") or {}).values():
            add(v)
    for q in ref.get("owner_question_variants", {}).values():
        for name, v in q.items():
            if isinstance(v, dict):
                for p_ in v.values():
                    for c in p_["cases"].values():
                        for k in ("value", "spend", "value_change_vs_applied", "spend_change_vs_applied"):
                            add(c.get(k))
    return {k.quantize(D("0.01")) for k in ks if k >= 50}


def o2_percentages(ref):
    return {D(str(v)).quantize(D("0.01")) for ops in ref["operations"].values() for m in ops.values()
            for v in [m.get("portfolio"), *(m.get("sites") or {}).values()] if isinstance(v, (int, float)) and v < 100.0 and v != int(v)}


def anchors(root, ref):
    n = 0
    keys, pcts = key_figures(ref), o2_percentages(ref)
    for fn in FIG_DOCS + derived_fig_docs(root):
        p = root / fn
        if not p.exists():
            check(f"{fn} exists", False); continue
        txt = p.read_text(encoding="utf-8")
        found = set()
        for m in ANCHOR.finditer(txt):
            n += 1
            sign = -1 if (m.group(1) or "").strip() in ("−", "-") else 1
            neg, path = m.group(5) == "-", m.group(6)
            found.add(path)
            val = get(ref, re.sub(r"^(options\.[^.]+)\.value$", r"\1.value_if_admissible", path))
            if val is None or isinstance(val, (dict, list, bool)):
                check(f"anchored figure in {fn}: {m.group(2)} -> {path} is independently computed", False); continue
            if isinstance(val, str):
                check(f"anchored figure in {fn}: {m.group(2)} -> {path} is a number", False); continue
            want = -D(str(val)) if neg else D(str(val))
            eq(f"anchored figure in {fn}: {(m.group(1) or '').strip()}{m.group(2)} = {'-' if neg else ''}{path} (signed)", sign * D(m.group(2).replace(",", "")), want)
            window = txt[max(0, m.start() - 90):m.start()].lower()
            if path.startswith("options.") and ("to date" in window or "so far" in window):
                check(f"anchored figure in {fn}: {m.group(2)} stated for a period to date is anchored to an option path {path}", False)
        for m in FIGX.finditer(txt):
            n += 1
            sign = -1 if (m.group(1) or "").strip() in ("−", "-") else 1
            want, why = expr_value(ref, m.group(5))
            if want is None:
                check(f"computed figure in {fn}: {m.group(2)} -> {m.group(5)} resolves over independent paths ({why})", False); continue
            eq(f"computed figure in {fn}: {(m.group(1) or '').strip()}{m.group(2)} = {m.group(5)} (signed)", sign * D(m.group(2).replace(",", "")), want)
        for m in re.finditer(r"([\d,]*\d(?:\.\d+)?)\**<!--rec-->", txt):
            check(f"{fn}: record-tagged figure {m.group(1)} is a manifest money record", round(abs(float(m.group(1).replace(",", ""))), 2) in RECORDS)
        for m in re.finditer(r"([\d,]*\d(?:\.\d+)?)\**<!--rec:([^>]+)-->", txt):   # record at an exact manifest path
            eq(f"{fn}: record {m.group(1)} = manifest {m.group(2)}", D(m.group(1).replace(",", "")), manifest_get(DOC, m.group(2)))
        for path in REQUIRED.get(fn, []):
            check(f"{fn}: headline figure {path} is anchored", path in found)
        body = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), txt)
        # A5: a computed table block (plan_model, or a go-to-market renderer's checked table) holds planning figures, not copies
        body = re.sub(r"<!--table:[\w-]+-->.*?<!--/table-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), body, flags=re.S)
        loose = []
        for m in re.finditer(r"(?<![\w.,/])(\d{1,3}(?:,\d{3})*\.\d{2}|\d{1,3}(?:,\d{3})+)(%?)(?!\d)(?!,\d)(?!\.\d)(?!\**<!--(?:fig:|figx:|rec))", body):
            v = D(m.group(1).replace(",", "")).quantize(D("0.01"))
            if (m.group(2) == "%" and v in pcts) or (m.group(2) == "" and v in keys):
                loose.append(m.group(1) + m.group(2))
        for m in re.finditer(r"(?<![\w.,/])(\d{1,2}\.\d{2})%(?!\**<!--)", body):   # O2 percentages
            if D(m.group(1)) in pcts:
                loose.append(m.group(1) + "%")
        check(f"{fn}: every evaluated plan/option money figure and O2 percentage is anchored (untagged: {sorted(set(loose))[:12]} x{len(loose)})", not loose)
    check(f"documents carry figure anchors ({n})", n > 50)


def documents(root, doc, ref):
    allowed = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            allowed.add(round(abs(float(o)), 2))
        elif isinstance(o, str):
            for m in re.findall(r"\d[\d,]*(?:\.\d+)?", o):
                try: allowed.add(round(abs(float(m.replace(",", ""))), 2))
                except ValueError: pass
    walk({k: v for k, v in doc.items() if k != "oracle"}); walk(ref)
    main_doc = (root / "layer4-transformation-design.md").read_text(encoding="utf-8")
    wp = (root / "worked-portfolios.md").read_text(encoding="utf-8")
    sections = [("main Parts 1-2", main_doc[main_doc.index("## Part 1."):main_doc.index("## Appendix")]),
                ("worked portfolios", wp[wp.index("## 1. The worked portfolios"):]),
                ("walkthroughs", (root / "interactive-mockup-vNEXT" / "walkthroughs.md").read_text(encoding="utf-8"))]
    tr = (root / "product-transition-and-roadmap.md").read_text(encoding="utf-8")
    sections.append(("transition §1-§4", tr[tr.index("## 1. Where we are"):tr.index("## 5. ")]))
    for name, body in sections:
        body = re.sub(r"[\d,]*\d(?:\.\d+)?%?\**<!--figx:[^>]*-->", "", body)   # recomputed by anchors() instead
        body = re.sub(r"`[^`]*`|<!--[^>]*-->", "", body)
        bad = [m.group(1) for m in re.finditer(r"(?<![\w.:/§-])(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+\.\d{2})(?![\d]| px)", body)
               if round(float(m.group(1).replace(",", "")), 2) not in allowed]
        check(f"{name}: figures are independent values or declared inputs (untraced: {sorted(set(bad))})", not bad)


# ---------------- 7. alignment (plan F A1-A6, rev 16.7; review G N1) ----------------
# The naming lint (OD-6) and the derived documents' alignment with the design live in check_alignment.py, which also
# proves itself on its planted fixtures every run. Each of its results is one check here, so one command checks the pack.
def workflow(doc, ref):
    """The demonstration workflow (manifest demo_workflow; worked-portfolios.md §1.5) obeys the design's rules (rev 16.8):
    OD-16 the item's owner is the person who chose its option or declared it; every person named is one of the tenant's
    people; version 1's items are the default plan's items plus the declared (proactive) ones; OD-17 a new connection is a
    capital item with no Action until the executive approves it; each Action's release is the design §2.4 step 4 rule
    recomputed from the item's whole one-off and crew visits against both thresholds; an item is Released only when its
    Actions were released at creation; OD-5 a declared item with no factor carries no value; a declared item's December
    crew visits fit the December limit; a dependency names an item of the same version."""
    wf = doc.get("demo_workflow", {})
    lim = {t["tenant"]: t.get("portfolio_constraints", {}) for t in doc.get("tenants", [])}
    for t in wf.get("tenants", []):
        tn, people = t["tenant"], {p["name"] for p in t["people"]}
        items = {i["item"]: i for i in t.get("items", [])}
        acts = t.get("actions", [])
        default = set(ref["plans"][tn]["default"]["items"])
        declared = {k for k, i in items.items() if i["kind"] == "PROACTIVE"}
        check(f"workflow {tn}: version 1's items are the default plan's items plus the declared ones", set(items) == default | declared)
        check(f"workflow {tn}: every reactive item is a chosen option of the default plan",
              all(k in default for k, i in items.items() if i["kind"] == "REACTIVE"))
        for k, i in items.items():
            check(f"workflow {tn} {k}: chooser and owner are the tenant's people", i["chosen_by"] in people and i["owner"] in people)
            check(f"workflow {tn} {k}: the item's owner is the person who chose it (OD-16)", i["owner"] == i["chosen_by"])
            if i["kind"] == "PROACTIVE":
                check(f"workflow {tn} {k}: a declared item names its factor or 'no factor (upkeep or compliance)' and then carries no value (OD-5)",
                      bool(i.get("factor")) and (i["factor"] != "no factor (upkeep or compliance)" or "value" not in i))
            if i.get("depends_on"):
                check(f"workflow {tn} {k}: its dependency is an item of the same version", i["depends_on"] in items)
            mine = [a for a in acts if a["item"] == k]
            if i.get("capital"):
                check(f"workflow {tn} {k}: a capital item has no Action before the executive approves it (OD-17)",
                      not mine and bool(i.get("actions_after_approval")))
            if i["kind"] == "PROACTIVE":
                spend, crew = i["planned_spend"], i["crew_visits"]
            else:
                spend, crew = ref["options"][k]["operator_one_off"] or 0, ref["options"][k].get("crew_visits") or 0
            at = (not i.get("capital")) and spend <= t["spend_threshold"] and crew <= t["crew_visit_threshold"]
            for a in mine:
                check(f"workflow {tn} {k}: '{a['action'][:40]}' release {a['release']} follows design §2.4 step 4",
                      a["release"] == ("AT_CREATION" if at else "AWAITS_APPROVAL"))
            want = "RELEASED" if (mine and at) else "CHOSEN"
            check(f"workflow {tn} {k}: item state {i['item_state']} is derived from its Actions and the proposed version ({want})", i["item_state"] == want)
        for a in acts:
            check(f"workflow {tn}: '{a['action'][:40]}' belongs to an item of version 1", a["item"] in items)
            check(f"workflow {tn}: '{a['action'][:40]}' creator and owner are the tenant's people", a["created_by"] in people and a["owner"] in people)
        dec = sum(i.get("crew_visits", 0) for i in items.values() if i["kind"] == "PROACTIVE" and i.get("crew_month") == "2026-12")
        if dec:
            check(f"workflow {tn}: December crew visits {dec} within the December limit", dec <= lim[tn].get("crew_visits_dec", 0))


# ---------------- 8. home categories and the snapshot (design rev 16.11 §2.0, §2.8; OD-21, OD-23) ----------------
HEAD_OF = {"G": "grow", "O": "optimize", "P": "protect", "A": "assure"}


def homes(doc):
    """Every node of every vertical is named once in home_categories (never inherited); objectives match headings; every
    measure takes its objective's heading and no money figure sits under Protect or Assure (At stake excepted); every bridge
    driver maps to a named node; each decision's heading is its origin Finding's factor's home, which its lever's home must equal; the snapshot
    names each portfolio once, and a pending recalculation names a trigger, the Sites and periods it affects."""
    hc = doc.get("home_categories") or {}
    reg = hc.get("nodes") or {}
    vert_of = {t["tenant"]: ("EV_DEPOT_CAPTIVE" if t["vertical"] == "EV_DEPOT" else t["vertical"]) for t in doc["tenants"]}
    for v in doc["structures"]:
        names = set(doc["structures"][v]) | set(doc["factor_map"][v]) | set(doc["evaluation"]["protect_nodes"].get(v, []))
        rows = reg.get(v) or {}
        check(f"homes {v}: every node is named once ({sorted(names - set(rows))[:6]} unnamed)", names <= set(rows))
        check(f"homes {v}: no row names an unknown node ({sorted(set(rows) - names)[:6]})", set(rows) <= names)
        bad = [k for k, r in rows.items() if not (r and (r[0] in ("above", "calendar") and len(r) == 1
                                                         or r[0] in HEAD_OF.values() and len(r) == 2 and HEAD_OF.get(str(r[1])[:1]) == r[0]))]
        check(f"homes {v}: each row is a heading with a matching objective, or above, or calendar ({bad[:4]})", not bad)
        outcome = doc["chain_model"][v]["result"]
        check(f"homes {v}: the outcome {outcome} sits above the headings", (rows.get(outcome) or [None])[0] == "above")
    drivers = hc.get("bridge_drivers") or {}
    for t in doc["tenants"]:
        v, rows = vert_of[t["tenant"]], reg.get(vert_of[t["tenant"]]) or {}
        for s_ in t["sites"]:
            for b in s_["period"].get("bridge", []):
                n = drivers.get(b["driver"])
                check(f"homes {t['tenant']}/{s_['site']}: bridge factor {b['driver']} maps to a named node ({n})", n in rows and rows[n][0] in ("grow", "optimize"))
        P = t["portfolio"]
        for blk, ms in (("protect", P["protect"]["measures"]), ("operations", P["operations"]["measures"]), ("rights", P["rights"]["measures"]),
                        ("service_cost_lines", P.get("service_cost_lines", []))):
            for m in ms:
                h = HEAD_OF.get(str(m.get("objective", ""))[:1])
                check(f"homes {t['tenant']} {blk} {m['id']}: has an objective with a heading ({m.get('objective')})", h is not None)
                if m.get("unit") == "USD" and m.get("class") != "EXPOSURE":
                    check(f"homes {t['tenant']} {blk} {m['id']}: a money figure is under Grow or Optimize, never Protect or Assure ({h})", h in ("grow", "optimize"))
                if blk == "protect":
                    check(f"homes {t['tenant']} protect {m['id']}: a Protect measure is a P objective", h == "protect")
                if blk == "operations":
                    check(f"homes {t['tenant']} operations {m['id']}: an operations measure is Optimize (O2)", m.get("objective") in ("O2",) or h == "assure" or h == "protect")
                if blk == "service_cost_lines":
                    check(f"homes {t['tenant']} {m['id']}: its node {m.get('node')} is an Optimize cost line", (rows.get(m.get("node")) or [None])[0] == "optimize")
                    pm = m.get("protect_measure")
                    check(f"homes {t['tenant']} {m['id']}: its Protect side is a Protect measure in its own unit ({pm})",
                          pm is None or any(x["id"] == pm and x.get("unit") != "USD" for x in P["protect"]["measures"]))
    sites = {s_["site"]: vert_of[t["tenant"]] for t in doc["tenants"] for s_ in t["sites"]}
    kinds = {d["name"]: d["kind"] for t in doc["plans"].values() for d in t["decisions"]}
    ids = [d["id"] for d in hc.get("decisions", [])]
    check(f"homes: each decision is listed once ({len(ids)})", len(ids) == len(set(ids)) and ids)
    pot = {v: {p_["name"] for p_ in ps} for v, ps in (hc.get("potential") or {}).items()}
    def home(v, n):   # a registry node's heading; a potential entry sits beside Grow (never Grow's actual)
        r = (reg.get(v) or {}).get(n)
        return r[0] if r else ("grow" if n in pot.get(v, set()) else None)
    for d in hc.get("decisions", []):
        v = sites.get(d["site"])
        lh, fh = home(v, d["lever"]), (home(v, d["finding_factor"]) if d.get("finding") else None)
        check(f"homes decision {d['id']}: its lever {d['lever']} is a named node of its Site's vertical", lh is not None)
        if d.get("finding"):
            check(f"homes decision {d['id']}: its Finding's factor {d.get('finding_factor')} is a named node or potential entry", fh is not None)
            check(f"homes decision {d['id']}: its heading {d['heading']} is its Finding's factor's home ({fh}) (owner, 19 Nov)", d["heading"] == fh)
            check(f"homes decision {d['id']}: its Finding's factor and its lever share a heading ({fh} / {lh}); a mismatch is ruled, never picked", fh == lh)
        else:
            check(f"homes decision {d['id']}: with no Finding, its heading {d['heading']} is its lever's home ({lh})", d["heading"] == lh)
        check(f"homes decision {d['id']}: its heading is Grow, Optimize or Protect (Assure holds no decision of its own)", d["heading"] in ("grow", "optimize", "protect"))
        check(f"homes decision {d['id']}: its chooser is one of the three choosing roles ({d.get('chooser')})", d.get("chooser") in ("SITE_MANAGER", "FINANCE_AND_COMMERCIAL_LEAD", "OPERATOR_EXECUTIVE"))
        if d.get("plan"):
            check(f"homes decision {d['id']}: names an allocator decision ({d['plan']})", d["plan"] in kinds)
            if kinds.get(d["plan"]) == "protective":
                check(f"homes decision {d['id']}: a protective decision sits under Protect", d["heading"] == "protect")
    res = hc.get("residuals") or {}
    for v, rows_ in res.items():
        for n, r in rows_.items():
            check(f"homes residual {v}/{n}: an explicit residual sits under Grow or Optimize ({r})", r and r[0] in ("grow", "optimize") and HEAD_OF.get(str(r[1])[:1]) == r[0])
    omf = hc.get("option_money_factors") or {}
    try:
        dv = json.loads((pathlib.Path(__file__).resolve().parent / "derived-values.json").read_text())["options"]
    except Exception:
        dv = {}
    opts = doc["evaluation"]["options"]
    vert_site = {s_["site"]: vert_of[t["tenant"]] for t in doc["tenants"] for s_ in t["sites"]}
    for k, o in dv.items():
        if o.get("valued_in_money"):
            check(f"homes option {k}: a valued option states its money factors", k in omf)
    site_of_opt = {}
    for t_ in doc["tenants"]:
        for s_ in t_["sites"]:
            for o_ in ((s_.get("decision") or {}).get("options") or []):
                if isinstance(o_, dict) and o_.get("id"):
                    site_of_opt[o_["id"]] = s_["site"]
    listed = {k for tp in doc["plans"].values() for k in (tp.get("listed_not_added") or {})}
    for k, ns in omf.items():
        in_eval = k in opts
        check(f"homes option {k}: an option with money factors is evaluated, or listed beside the plan and not added", in_eval or k in listed)
        v = vert_site.get((opts.get(k) or {}).get("site") or site_of_opt.get(k))
        scl = {l_.get("node") for t in doc["tenants"] for l_ in t["portfolio"].get("service_cost_lines", [])}
        for n in ns:
            r = (reg.get(v) or {}).get(n) or [None]
            check(f"homes option {k}: money factor {n} is one it changes (or a linked service cost line)", not in_eval or n in (opts.get(k) or {}).get("changes", {}) or n in scl)
            check(f"homes option {k}: money factor {n} sits under Grow or Optimize ({r[0]})", r[0] in ("grow", "optimize"))
    # every Finding the screens show names its own factor and heading; linked Findings keep their own (design §2.0, rev 16.12)
    fr = hc.get("findings") or []
    fids = [f_.get("id") for f_ in fr]
    check(f"homes: each Finding row is listed once ({len(fids)})", fids and len(fids) == len(set(fids)))
    decs = {d["id"]: d for d in hc.get("decisions", [])}
    for f_ in fr:
        v = sites.get(f_.get("site"))
        h = home(v, f_["factor"]) if f_.get("factor") else None
        check(f"homes Finding {f_.get('id')}: names a factor with a registry row or potential entry ({f_.get('factor')})", h is not None)
        check(f"homes Finding {f_.get('id')}: its heading {f_.get('heading')} is its own factor's home ({h})", h is not None and f_.get("heading") == h)
        check(f"homes Finding {f_.get('id')}: its decision {f_.get('decision')} exists, at its Site", f_.get("decision") in decs and decs[f_["decision"]]["site"] == f_.get("site"))
    for did, d in decs.items():
        org = [f_ for f_ in fr if f_.get("decision") == did and f_.get("origin")]
        check(f"homes decision {did}: exactly one origin Finding row, on its finding_factor ({[f_['factor'] for f_ in org]})", len(org) == 1 and org[0]["factor"] == d["finding_factor"])
    # the chooser of each plan item is a person holding its decision's chooser role (design §2.4 step 2; OD-16)
    dec_of_opt = {}
    for t_ in doc["tenants"]:
        for s_ in t_["sites"]:
            for blk in (s_.get("decision") or {}, *(s_.get("decisions") or [])):
                for o_ in (blk.get("options") or []) if isinstance(blk, dict) else []:
                    if isinstance(o_, dict) and o_.get("id"):
                        dec_of_opt[o_["id"]] = s_["site"]
    plan_dec = {d_["name"]: d_ for tp in doc["plans"].values() for d_ in tp["decisions"]}
    by_plan = {d["plan"]: d for d in hc.get("decisions", []) if d.get("plan")}
    for tw in doc["demo_workflow"]["tenants"]:
        role_of = {p_["name"]: p_["role"] for p_ in tw["people"]}
        for it in tw["items"]:
            if it.get("kind") != "REACTIVE":
                continue
            hd = next((by_plan[n_] for n_, pd in plan_dec.items() if n_ in by_plan and it["item"] in (pd.get("options") or [])), None)
            if hd:
                check(f"workflow {tw['tenant']} {it['item']}: chosen by the role its decision names ({role_of.get(it['chosen_by'])} = {hd['chooser']})", role_of.get(it["chosen_by"]) == hd["chooser"])
    sn = doc.get("snapshot") or {}
    tenants = [p_["tenant"] for p_ in sn.get("portfolios", [])]
    check(f"snapshot: an as-of time is recorded ({sn.get('as_of')})", bool(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", str(sn.get("as_of", "")))))
    check(f"snapshot: each portfolio once ({tenants})", sorted(tenants) == sorted(vert_of))
    check("snapshot: at least one portfolio current and one with a recalculation pending (demo cases)",
          any(p_.get("recalculation_pending") for p_ in sn.get("portfolios", [])) and any(not p_.get("recalculation_pending") for p_ in sn.get("portfolios", [])))
    tsites = {t["tenant"]: {s_["site"] for s_ in t["sites"]} for t in doc["tenants"]}
    for p_ in sn.get("portfolios", []):
        pe = p_.get("pending")
        check(f"snapshot {p_['tenant']}: pending flag and pending record agree", bool(p_.get("recalculation_pending")) == bool(pe))
        if pe:
            check(f"snapshot {p_['tenant']}: the pending trigger is one of the six ({pe.get('trigger')})", pe.get("trigger") in (sn.get("trigger_kinds") or {}))
            check(f"snapshot {p_['tenant']}: the pending Sites are the portfolio's ({pe.get('sites')})", pe.get("sites") and set(pe["sites"]) <= tsites[p_["tenant"]])
            check(f"snapshot {p_['tenant']}: the trigger fired after the snapshot was computed", str(pe.get("received", "")) > str(p_.get("as_of", "")))


def homes_selftest(doc):
    """Planted copies of the Finding rows: each must fail homes() (rev 16.12: a linked Finding keeps its own factor)."""
    import copy
    def row(d, i): return next(x for x in d["home_categories"]["findings"] if x["id"] == i)
    plants = {"a linked Finding with no factor": lambda d: row(d, "embakasi-import-limit").pop("factor"),
              "a linked Finding on a node with no registry row": lambda d: row(d, "ruiru-import-limit").update(factor="peak_import_kw"),
              "a linked Finding taking its decision's heading": lambda d: row(d, "embakasi-import-limit").update(heading="optimize"),
              "a decision with no origin Finding": lambda d: row(d, "kobo-candidate").update(origin=False)}
    for label, mut in plants.items():
        d = copy.deepcopy(doc); mut(d)
        keep, kp = list(failures), passes
        homes(d)
        caught = len(failures) > len(keep)
        failures[:] = keep
        globals()["passes"] = kp
        check(f"homes self-test: {label} is planted and fails", caught)


# ---------------- 9. the vertical factor map and the traceability file (owner, 19 Nov: vertical-factor-map.md) ----------------
BRIEF = pathlib.Path(__file__).resolve().parents[3] / ".agent" / "AssetEcon_Product_Direction_Layers_1_to_3_and_Claude_Brief_REVISED.md"
MAP_DOC = "vertical-factor-map.md"
TRACE = "outcome-lever-capability-traceability.csv"
CSV_VERT = {"MINI_GRID": "MINI_GRID", "COLD_CHAIN": "COLD_CHAIN", "EV_DEPOT": "EV_DEPOT_CAPTIVE"}
OUT_OF_SCOPE = re.compile(r"^(?:Not in scope now|Not applicable here|Later)\b")
HEAD_WORD = {"Grow": "grow", "Optimize": "optimize", "Protect": "protect", "Assure": "assure"}


def brief_levers(text):
    out = {}
    for v, sec in (("MINI_GRID", "L2.2"), ("COLD_CHAIN", "L2.3"), ("EV_DEPOT_CAPTIVE", "L2.4")):
        a = text.index(f"## {sec} ")
        b = text.index("\n## ", a + 5)
        out[v] = set(re.findall(r"^\| \*\*((?:MG|CC|EV)-L\d+) ", text[a:b], re.M))
    return out


def known_ids(doc):
    """Per vertical: registry node -> (heading, objective), plus manifest measures and potential entries."""
    hc = doc["home_categories"]
    vert_of = {t["tenant"]: CSV_VERT.get(t["vertical"], t["vertical"]) for t in doc["tenants"]}
    known = {v: {k: (r[0], r[1] if len(r) > 1 else None) for k, r in rows.items()} for v, rows in hc["nodes"].items()}
    for t in doc["tenants"]:
        P, v = t["portfolio"], vert_of[t["tenant"]]
        for blk in (P["protect"]["measures"], P["operations"]["measures"], P["rights"]["measures"], P.get("service_cost_lines", [])):
            for m in blk:
                o = str(m.get("objective", ""))
                known[v].setdefault(m["id"], (HEAD_OF.get(o[:1]), o))
    for v, ps in (hc.get("potential") or {}).items():
        for p_ in ps:
            known[v].setdefault(p_["name"], ("grow", p_["objective"]))
    return known


def parse_map(text):
    """{vertical: {"levers": {id: (scope, [factors])}, "factors": {id: (heading, objective, site, portfolio)}}}"""
    out = {}
    for m in re.finditer(r"<!--vertical:(\w+)-->(.*?)(?=^## |\Z)", text, re.S | re.M):
        v, body = m.group(1), m.group(2)
        lev, fac = {}, {}
        for row in re.finditer(r"^\| \*\*((?:MG|CC|EV)-L\d+)\*\*[^|]*\| ([^|]*) \| ([^|]*) \|", body, re.M):
            lev[row.group(1)] = (row.group(2).strip(), re.findall(r"`([a-z0-9_]+)`", row.group(3)))
        for row in re.finditer(r"^\| `([a-z0-9_]+)` \| (\w+) `(\w+)`[^|]*\| ([^|]*) \| ([^|]*) \|", body, re.M):
            fac[row.group(1)] = (HEAD_WORD.get(row.group(2)), row.group(3), row.group(4).strip(), row.group(5).strip())
        out[v] = {"levers": lev, "factors": fac}
    return out


def map_problems(map_text, csv_text, doc, brief_text):
    """Every reason the map or the traceability file fails, as a list of strings (empty = pass)."""
    import csv as _csv, io as _io
    bad, known, want = [], known_ids(doc), brief_levers(brief_text)
    want_dec = {d["id"]: (d["finding_factor"], d["lever"], d["heading"]) for d in doc["home_categories"].get("decisions", [])}
    got_dec = {r.group(1): (r.group(2), r.group(3), HEAD_WORD.get(r.group(4))) for r in
               re.finditer(r"^\| `([a-z]+-[a-z-]+)` \|[^|]*\|[^|]*\| `([a-z0-9_]+)` \| `([a-z0-9_]+)` \| (\w+) \|", map_text, re.M)}
    if got_dec != want_dec:
        bad.append(f"map: the decision headings differ from home_categories.decisions ({sorted(set(want_dec.items()) ^ set(got_dec.items()))[:2]})")
    M = parse_map(map_text)
    for v, ids in want.items():
        sec = M.get(v)
        if not sec:
            bad.append(f"map: no section for {v}"); continue
        for lid in sorted(ids - set(sec["levers"])):
            bad.append(f"map {v}: brief lever {lid} missing")
        for lid in sorted(set(sec["levers"]) - ids):
            bad.append(f"map {v}: {lid} is not a lever of the brief")
        for lid, (scope, fs) in sec["levers"].items():
            if not fs and not OUT_OF_SCOPE.match(scope):
                bad.append(f"map {v} {lid}: in scope but maps to no factor")
            for f in fs:
                if f not in known[v]:
                    bad.append(f"map {v} {lid}: factor {f} is not in the registry or manifest")
                elif f not in sec["factors"]:
                    bad.append(f"map {v} {lid}: factor {f} has no row in the factor table")
        for f, (h, o, site, port) in sec["factors"].items():
            k = known[v].get(f)
            if not k:
                bad.append(f"map {v}: factor row {f} is not in the registry or manifest"); continue
            if (h, o) != k:
                bad.append(f"map {v}: {f} heading {h} {o} differs from the registry's {k}")
            if not site or site in ("—", "-") or not port or port in ("—", "-"):
                bad.append(f"map {v}: {f} has no Site or portfolio read")
    rows = list(_csv.DictReader(_io.StringIO(csv_text)))
    if not rows or "factor_description" not in rows[0]:
        bad.append("csv: no factor_description column (the factor column must hold IDs)")
    ca = _ca()
    for r in rows:
        v = CSV_VERT.get(r["vertical"])
        toks = r["factor"].split()
        if toks == ["—"]:
            toks = []
        if v is None:
            if toks: bad.append(f"csv {r['row_id']}: a cross-vertical row names factors {toks}")
        else:
            for f in toks:
                if f not in known[v]:
                    bad.append(f"csv {r['row_id']}: factor {f} is not in the {v} registry or manifest")
            lev = M.get(v, {}).get("levers", {}).get(r["lever_id"])
            if r["row_kind"] in ("lever-objective", "lever-capability") and lev is not None and set(toks) != set(lev[1]):
                bad.append(f"csv {r['row_id']}: {r['lever_id']} factors {sorted(toks)} differ from the map's {sorted(lev[1])}")
        for k in ("factor_description", "declared_measure", "model_or_algorithm", "notes"):
            for ln, s in ca.naming_violations(r.get(k, "")):
                bad.append(f"csv {r['row_id']} {k}: 'plan' not the construct (OD-6): {s[:60]}")
            if re.search(r"\bM[1-5]\b", r.get(k, "")):
                bad.append(f"csv {r['row_id']} {k}: retired mechanic number")
    return bad


def _ca():
    spec = importlib.util.spec_from_file_location("check_alignment", pathlib.Path(__file__).resolve().parent / "check_alignment.py")
    ca = importlib.util.module_from_spec(spec); spec.loader.exec_module(ca)
    return ca


def factor_map(root, doc):
    if not BRIEF.is_file():
        check(f"factor map: the brief is readable ({BRIEF})", False); return
    brief = BRIEF.read_text(encoding="utf-8")
    mt, ct = (root / MAP_DOC).read_text(encoding="utf-8"), (root / TRACE).read_text(encoding="utf-8")
    want = brief_levers(brief)
    check(f"factor map: the brief's catalogues list 10, 9 and 9 levers ({[len(want[v]) for v in want]})", [len(want[v]) for v in want] == [10, 9, 9])
    bad = map_problems(mt, ct, doc, brief)
    check(f"factor map and traceability file agree with the registry ({bad[:4]} x{len(bad)})", not bad)
    # planted copies: each must fail
    first = next(iter(sorted(want["COLD_CHAIN"])))
    plants = {
        "a brief lever removed": (re.sub(r"^\| \*\*" + first + r"\*\*.*\n", "", mt, count=1, flags=re.M), ct),
        "an unknown factor": (mt.replace("`candidate_l` `necessary_l` `diesel_price`", "`candidate_l` `necessary_l` `diesel_prices`", 1), ct),
        "a blank Site read": (re.sub(r"^(\| `excess_kwh` \| [^|]*\| )[^|]*( \|)", r"\1—\2", mt, count=1, flags=re.M), ct),
        "a wrong heading": (re.sub(r"^(\| `penalties` \| )Optimize `O1`", r"\1Protect `P3`", mt, count=1, flags=re.M), ct),
        "a traceability row with another factor": (mt, re.sub(r"(,MG-L3,[^\n]*?,)(candidate_l[^,]*),", r"\1billed_kwh,", ct, count=1)),
        "a 'plan' for a target in the traceability text": (mt, ct.replace("target 100.0", "plan 100.0", 1)),
        "a decision under another heading": (re.sub(r"^(\| `kisiwa-genset` \|.*\| )Protect( \|)$", r"\1Optimize\2", mt, count=1, flags=re.M), ct),
    }
    for label, (m_, c_) in plants.items():
        changed = (m_, c_) != (mt, ct)
        check(f"factor map self-test: {label} is planted and fails", changed and bool(map_problems(m_, c_, doc, brief)))


def alignment(root):
    spec = importlib.util.spec_from_file_location("check_alignment", root / "check_alignment.py")
    ca = importlib.util.module_from_spec(spec); spec.loader.exec_module(ca)
    results, warnings, notes = ca.run(root)
    for label, ok in results:
        check(f"alignment: {label}", ok)
    for n_ in notes:
        print("note:", n_)
    print(f"note: {len(warnings)} C4 words left for the reviewer (check_alignment.py prints them)")


def derived_fig_docs(root):
    """Every derived document present joins the anchor scan, so each of its figures keeps a checked home (A5)."""
    spec = importlib.util.spec_from_file_location("check_alignment", root / "check_alignment.py")
    ca = importlib.util.module_from_spec(spec); spec.loader.exec_module(ca)
    return tuple(fn for fn in ca.derived_present(root) if fn not in FIG_DOCS)


# ---------------- 10. empty states: the record behind every "not available yet" (structure-specification.md §3.1) ----------------
FAMILIES = {"COMMERCIAL_RECORD", "READING", "OPERATIONAL_RECORD", "OBSERVER", "DECLARED", "DOCUMENT", "CALENDAR"}
ABSENT = {"MISSING", "ZERO_WHEN_HELD", "OPTION_ONLY", "NEVER_EMPTY"}
CAUSES = {"NOT_RECEIVED", "NOT_CONNECTED", "NOT_CALCULATED_YET"}
CARRIED = {None, "TARGET", "ASSUMPTION", "RESIDUAL"}


def plan_slice_ids(root):
    return set(re.findall(r'^\s+\("(\w+)", "', (root / "plan_model.py").read_text(encoding="utf-8"), flags=re.M))


def numeric_alternatives(expr):
    """The number literals that are whole alternatives of `a | b | 0` (or the whole expression)."""
    import ast
    out, stack = [], [ast.parse(str(expr), mode="eval").body]
    while stack:
        n = stack.pop()
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
            stack += [n.left, n.right]
        elif isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            out.append(n.value)
    return out


def observed_reads_literal(doc, v, f, x):
    """Sites of vertical v whose observed side (October, November to date) has none of the record alternatives before the
    leaf's number literal, so the literal would be read as an observed value."""
    import ast
    def alts(n):
        return alts(n.left) + alts(n.right) if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr) else [n]
    def fields(n):   # record.<field> paths an alternative reads
        return [a.attr for a in ast.walk(n) if isinstance(a, ast.Attribute) and isinstance(a.value, ast.Name) and a.value.id == "record"]
    seq = alts(ast.parse(str(x), mode="eval").body)
    first_lit = next((i for i, a in enumerate(seq) if isinstance(a, ast.Constant)), None)
    if first_lit is None:
        return []
    out = []
    for t in doc["tenants"]:
        if ("EV_DEPOT_CAPTIVE" if t["vertical"] == "EV_DEPOT" else t["vertical"]) != v:
            continue
        for s_ in t["sites"]:
            obs = s_.get("observations", {})
            for side, rec in [("actual", {**s_["period"]["actual"], **obs.get("october", {})})] + \
                             ([("november_to_date", obs["november_to_date"])] if "november_to_date" in obs else []):
                if not any(fields(a) and all(k in rec for k in fields(a)) for a in seq[:first_lit]):
                    out.append(f"{s_['site']} {side}")
    return out


def empty_state_problems(doc, slices, mr, dv):
    bad = []
    ES = doc.get("empty_states") or {}
    LS, CN, DS_, CO, AS = (ES.get(k) or {} for k in ("leaf_sources", "chain_nodes", "deferred_stages", "conditions", "assumptions"))
    ok_slices = slices | set(ES.get("queued_slices") or {})
    vert_of = {t["tenant"]: ("EV_DEPOT_CAPTIVE" if t["vertical"] == "EV_DEPOT" else t["vertical"]) for t in doc["tenants"]}
    pot = {v: {p_["name"] for p_ in ps} for v, ps in ((doc.get("home_categories") or {}).get("potential") or {}).items()}
    for v, fm in doc["factor_map"].items():
        rows = LS.get(v) or {}
        if set(rows) != set(fm):
            bad.append(f"leaf_sources {v}: rows {sorted(set(rows) ^ set(fm))[:4]} differ from the factor map")
        exprs = {f: [x] for f, x in fm.items()}
        for t in doc["tenants"]:
            if vert_of[t["tenant"]] == v:
                for s_ in t["sites"]:
                    for f, x in (s_.get("factor_sources") or {}).items():
                        exprs.setdefault(f, []).append(x)
        for f, r in rows.items():
            r = r or {}
            if r.get("family") not in FAMILIES or r.get("absent") not in ABSENT or not r.get("kind"):
                bad.append(f"leaf_sources {v}/{f}: family, kind and absent must be named ({r})")
            if r.get("slice") not in ok_slices:
                bad.append(f"leaf_sources {v}/{f}: slice {r.get('slice')} is not a slice of plan_model.py or a queued slice")
            if (r.get("absent") == "NEVER_EMPTY") != (r.get("family") == "CALENDAR"):
                bad.append(f"leaf_sources {v}/{f}: only a calendar leaf is never empty")
            for x in exprs.get(f, []):
                lits = numeric_alternatives(x)
                if lits and r.get("absent") == "MISSING":   # the literal may serve only the target side, under its labelled assumption
                    for where in observed_reads_literal(doc, v, f, x):
                        bad.append(f"leaf_sources {v}/{f}: declared MISSING but {where} reads {lits} for an absent record (unknown as zero, R4)")
                if r.get("absent") == "ZERO_WHEN_HELD" and any(l_ != 0 for l_ in lits):
                    bad.append(f"leaf_sources {v}/{f}: a held-source zero falls back to {lits}, not 0")
                if lits and r.get("absent") not in ("ZERO_WHEN_HELD", "OPTION_ONLY", "NEVER_EMPTY", "MISSING"):
                    bad.append(f"leaf_sources {v}/{f}: a numeric fallback with no declared meaning")
    for v, cm in doc["chain_model"].items():
        want = set(cm["stages"]) | set(cm.get("leaks") or {})
        got = CN.get(v) or {}
        if set(got) != want:
            bad.append(f"chain_nodes {v}: {sorted(set(got) ^ want)} differ from chain_model's stages and leaks")
        names = set(doc["structures"][v]) | set(doc["factor_map"][v]) | pot.get(v, set())
        for k, m in got.items():
            if isinstance(m, list):
                if not m or not set(m) <= names:
                    bad.append(f"chain_nodes {v}/{k}: {m} are not all nodes, leaves or potential entries")
            elif isinstance(m, dict) and "deferred" in m:
                d_ = DS_.get(m["deferred"]) or {}
                if d_.get("vertical") != v:
                    bad.append(f"chain_nodes {v}/{k}: deferred stage {m['deferred']} is not declared for {v}")
            elif isinstance(m, dict) and "reconciled" in m:
                if not m["reconciled"] or m.get("absent") != "ZERO_WHEN_HELD" or m.get("slice") not in ok_slices or not m.get("note"):
                    bad.append(f"chain_nodes {v}/{k}: a reconciled zero names its records, ZERO_WHEN_HELD, a slice and its note")
            else:
                bad.append(f"chain_nodes {v}/{k}: carried by nothing")
    for st, d_ in DS_.items():
        need = ("vertical", "label", "family", "kind", "cause", "words", "blocks", "slice", "trigger")
        if any(not d_.get(k) for k in need) or d_.get("cause") not in CAUSES or d_.get("family") not in FAMILIES or d_.get("slice") not in ok_slices:
            bad.append(f"deferred stage {st}: names {need} with a known cause, family and slice")
        names = set(doc["structures"].get(d_.get("vertical"), {})) | pot.get(d_.get("vertical"), set())
        if not set(d_.get("blocks") or []) <= names:
            bad.append(f"deferred stage {st}: blocks {d_.get('blocks')} are not nodes or potential entries")
        if not any(isinstance(m, dict) and m.get("deferred") == st for m in (CN.get(d_.get("vertical")) or {}).values()):
            bad.append(f"deferred stage {st}: no chain stage is carried by it")
    for v, ps in ((doc.get("home_categories") or {}).get("potential") or {}).items():
        for p_ in ps:
            if "shown" in p_:
                bad.append(f"potential {v}/{p_['name']}: free-text empty state; name its deferred stage instead")
            if "deferred" in p_ and p_["deferred"] not in DS_:
                bad.append(f"potential {v}/{p_['name']}: deferred stage {p_['deferred']} is not declared")
    want_entries = []   # (site key, side, subject) the manifest itself says are missing
    for t in doc["tenants"]:
        for s_ in t["sites"]:
            key = f"{t['tenant']}/{s_['site']}"
            for line, state in (s_["period"].get("coverage") or {}).items():
                if state == "ESTIMATED":
                    want_entries.append((key, "actual", ("leaf", line)))
            rights = ([s_["entitlement"]] if "entitlement" in s_ else []) + s_.get("entitlements", []) + \
                     ([s_["incident"]["entitlement"]] if isinstance(s_.get("incident", {}).get("entitlement"), dict) else [])
            for r in rights:
                for c, state in (r.get("evidence") or {}).items():
                    if state == "MISSING":
                        cr = CO.get(c) or {}
                        if not all(cr.get(k) for k in ("family", "kind", "cause", "slice", "label", "words")) or cr.get("slice") not in ok_slices:
                            bad.append(f"condition {c} ({key}): names its record, cause, slice and words")
                        want_entries.append((key, "actual", ("condition", c)))
            for head, blk in s_.items():
                if isinstance(blk, dict):
                    for field, val in blk.items():
                        if isinstance(val, str) and val.startswith("[assumption]"):
                            if f"{head}.{field}" not in AS:
                                bad.append(f"assumption {key} {head}.{field}: no record that would confirm it")
                            want_entries.append((key, "actual", ("field", f"{head}.{field}")))
            for side, r in (dv["sites"].get(key) or {}).items():
                if r["status"] != "evaluated":
                    want_entries.append((key, side, ("not decomposed", side)))
    sites = mr.get("sites") or {}
    for key, side, (kind, what) in want_entries:
        es = [e for e in sites.get(key, []) if e.get("side") == side]
        hit = {"leaf": lambda e: e.get("leaf") == what, "condition": lambda e: e.get("condition") == what,
               "field": lambda e: e.get("field") == what, "not decomposed": lambda e: e.get("carried_as") == "RESIDUAL" or e.get("cause") == "NOT_RECEIVED" and e.get("leaf")}[kind]
        if not any(hit(e) for e in es):
            bad.append(f"missing-records {key} {side}: no entry for {kind} {what}")
    for key, es in sites.items():
        v = vert_of.get(key.split("/")[0])
        for e in es:
            if not e.get("record_kind") or e.get("source_family") not in FAMILIES or e.get("cause") not in CAUSES \
                    or e.get("carried_as", "x") not in CARRIED or e.get("slice") not in ok_slices or not isinstance(e.get("blocks"), list):
                bad.append(f"missing-records {key}: entry {e.get('leaf') or e.get('leaves') or e.get('condition') or e.get('stage') or e.get('field')} lacks a record, cause, carried-as or slice")
            if "leaf" in e and e["leaf"] not in (LS.get(v) or {}):
                bad.append(f"missing-records {key}: leaf {e['leaf']} is not a registry leaf")
            if "stage" in e and e["stage"] not in DS_:
                bad.append(f"missing-records {key}: stage {e['stage']} is not a deferred stage")
            if e.get("carried_as") is None and "leaf" in e and (dv["sites"].get(key) or {}).get(e["side"], {}).get("status") == "evaluated":
                bad.append(f"missing-records {key}: {e['leaf']} is shown as not available on a side that is evaluated (stale empty state)")
    return bad


def empty_states(root, doc):
    import copy
    try:
        mr = json.loads((root / "missing-records.json").read_text(encoding="utf-8"))
    except Exception:
        check("empty states: missing-records.json is readable (run evaluate_structure.py)", False); return
    dv = json.loads((root / "derived-values.json").read_text(encoding="utf-8"))
    slices = plan_slice_ids(root)
    bad = empty_state_problems(doc, slices, mr, dv)
    check(f"empty states: every leaf, stage, condition and missing record names its source and its slice ({bad[:4]} x{len(bad)})", not bad)
    n = sum(len(v) for v in (mr.get("sites") or {}).values())
    check(f"empty states: missing-records.json covers every Site ({n} entries)", set(mr.get("sites") or {}) == set(dv["sites"]))

    def planted(edit, on="doc"):
        d2, m2 = copy.deepcopy(doc), copy.deepcopy(mr)
        edit(d2 if on == "doc" else m2)
        return bool(empty_state_problems(d2, slices, m2, dv))
    first_site = next(iter(mr["sites"]))
    plants = {
        "a leaf with no source row": lambda d: d["empty_states"]["leaf_sources"]["MINI_GRID"].pop("om"),
        "a zero fallback declared MISSING and read on an observed side (unknown as zero)": lambda d: d["empty_states"]["leaf_sources"]["MINI_GRID"]["unexplained_loss_kwh"].update(absent="MISSING"),
        "an observed side losing the record a MISSING leaf reads": lambda d: d["tenants"][0]["sites"][0]["observations"]["october"].pop("major_assets"),
        "a leaf with an unknown slice": lambda d: d["empty_states"]["leaf_sources"]["COLD_CHAIN"]["crate_days"].update(slice="99z"),
        "a chain stage carried by nothing": lambda d: d["empty_states"]["chain_nodes"]["MINI_GRID"].pop("usable_capacity"),
        "a free-text empty state on a potential entry": lambda d: d["home_categories"]["potential"]["MINI_GRID"][0].update(shown="needs an export"),
        "a missing condition with no record": lambda d: d["empty_states"]["conditions"].pop("temperature"),
        "an entry with no slice": (lambda m: m["sites"][first_site][0].pop("slice"), "mr"),
        "an estimated line with no entry": (lambda m: m["sites"].update({k: [e for e in v if e.get("carried_as") != "TARGET"] for k, v in m["sites"].items()}), "mr"),
    }
    for label, p_ in plants.items():
        fn_, on = p_ if isinstance(p_, tuple) else (p_, "doc")
        check(f"empty states self-test: {label} is planted and fails", planted(fn_, on))


def main(path):
    root = pathlib.Path(path).resolve().parent
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    DOC.update(doc)
    spec = importlib.util.spec_from_file_location("independent_model", root / "independent_model.py")
    im = importlib.util.module_from_spec(spec); spec.loader.exec_module(im)
    ref = im.compute(str(path))
    dv = json.loads((root / "derived-values.json").read_text(encoding="utf-8"))

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k not in ("oracle", "evaluation", "plans", "calibration_spikes", "owner_question_variants", "empty_states"): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, float):   # money records are written with cents (floats); counts and days are integers
            RECORDS.add(round(abs(o), 2))
    walk(doc)
    evaluator(ref, dv)
    stated(doc, ref)
    rights_terms(doc, ref)
    narratives(doc, ref)
    anchors(root, ref)
    documents(root, doc, ref)
    workflow(doc, ref)
    homes(doc)
    homes_selftest(doc)
    factor_map(root, doc)
    empty_states(root, doc)
    alignment(root)
    print(f"{passes} checks passed, {len(failures)} failed")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent / "demo-site-scenario-manifest.yaml")))
