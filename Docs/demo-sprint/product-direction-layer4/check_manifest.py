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
     independent values or declared inputs.
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
    for m in t["portfolio"]["protect"]["measures"]:
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
        for m in t["portfolio"]["protect"]["measures"]:
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
                cur = cur[int(key)] if key.isdigit() else next((x for x in cur if isinstance(x, dict) and key in (x.get("tenant"), x.get("site"), x.get("id"), x.get("batch"), x.get("asset"))), None)
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
    for fn in FIG_DOCS:
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
                if k not in ("oracle", "evaluation", "plans", "calibration_spikes", "owner_question_variants"): walk(v)
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
    print(f"{passes} checks passed, {len(failures)} failed")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent / "demo-site-scenario-manifest.yaml")))
