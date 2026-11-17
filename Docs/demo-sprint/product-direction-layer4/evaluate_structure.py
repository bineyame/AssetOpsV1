"""Structure evaluator for the Layer 4 demonstration world (rev 10; owner, ninth to eleventh messages).

Design-pack tool, not product code. It produces the illustration's figures by running the five mechanics on declared inputs,
all the way down the structure, and holds no numbers of its own:

  M1 Define   - `structures:` declares every layer of each vertical's structure as node expressions over named factors: value
                chain stages and leaks, physical sub-structures, cost to serve and the outcome, Protect measures.
  M2 Observe  - `factor_map:` turns each site's source records (period record, tenant prices, site tariff and physical data,
                energy model, incident) into leaf factors; every node is evaluated bottom-up for actual and plan. A plan stated only
                as a total is reported as "not decomposed: stated total", never counted as evaluated.
  M3 Evaluate - `evaluation.options` gives each option's parameters (from its manifest row, or declared with provenance: design
                value of a calibration spike, assumption, quote) and its factor changes as expressions over those parameters and the
                observed factors. Restore dates are derived from their drivers (decision date + lead times, crew visit + repair
                days, notice + business days). The option is re-evaluated through the same structure against its reference; money
                value = (outcome under option - outcome under reference) x months - operator-borne one-off cost. Rights decide who
                bears each cost line (operator share 0 when the named right is POTENTIALLY_COVERED or ACCEPTED). Protect measures are
                structure nodes evaluated for the option and its reference.
  M4 Choose   - `plans:` gives budget, fixed (must-do and protective) items, candidates, exclusivity, requirements and switches;
                every subset is enumerated; switch cases, sensitivities and the downside re-run it.

Writes derived-values.json (every figure with its formula). check_manifest.py asserts that the stated figures in the manifest and
the documents equal these values. Run:  python3 evaluate_structure.py [demo-site-scenario-manifest.yaml]
"""
from __future__ import annotations

import ast
import datetime as dt
import itertools
import json
import math
import operator
import pathlib
import sys
from decimal import Decimal as D

import yaml


class Missing(Exception):
    pass


BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
FUNCS = {"min": min, "max": max, "ceil": lambda x: D(math.ceil(x))}


def num(x):
    if isinstance(x, D):
        return x
    if isinstance(x, (int, float)):
        return D(str(x))
    raise Missing(f"not a number: {x!r}")


class Env:
    """Evaluates an expression over: structure nodes, factors, parameters, and dotted paths into the record context."""

    def __init__(self, structure: dict, values: dict, ctx: dict):
        self.structure, self.values, self.ctx = structure, dict(values), ctx

    def path(self, node):
        if isinstance(node, ast.Name):
            if node.id in self.ctx:
                return self.ctx[node.id]
            raise Missing(node.id)
        if isinstance(node, ast.Attribute):
            base = self.path(node.value)
            if isinstance(base, dict) and node.attr in base:
                return base[node.attr]
            raise Missing(node.attr)
        if isinstance(node, ast.Subscript):
            base = self.path(node.value)
            key = node.slice
            k = self.ctx["site"] if isinstance(key, ast.Name) and key.id == "site" else ast.literal_eval(key)
            try:
                return base[k]
            except (KeyError, IndexError, TypeError):
                raise Missing(str(k))
        raise Missing(ast.dump(node))

    def ev(self, node):
        if isinstance(node, ast.Expression):
            return self.ev(node.body)
        if isinstance(node, ast.Constant):
            return num(node.value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            try:
                return self.ev(node.left)
            except Missing:
                return self.ev(node.right)
        if isinstance(node, ast.BinOp):
            return BIN[type(node.op)](self.ev(node.left), self.ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self.ev(node.operand)
        if isinstance(node, ast.Call):
            return FUNCS[node.func.id](*[self.ev(a) for a in node.args])
        if isinstance(node, ast.Name):
            if node.id in self.values:
                return self.values[node.id]
            if node.id in self.structure:
                self.values[node.id] = self.ev(ast.parse(self.structure[node.id], mode="eval"))
                return self.values[node.id]
            return num(self.path(node))
        return num(self.path(node))

    def expr(self, text):
        return self.ev(ast.parse(str(text), mode="eval"))

    def all_nodes(self):
        return {n: self.expr(n) for n in self.structure}


def money(x) -> float:
    return float(D(x).quantize(D("0.01")))


def add_business_days(d: dt.date, n: int) -> dt.date:
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def main(path: str) -> dict:
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    S, FM, EV = doc["structures"], doc["factor_map"], doc["evaluation"]
    as_of = dt.date.fromisoformat(doc["as_of"])
    end = dt.date.fromisoformat(EV["horizon_end"])
    out = {"as_of": doc["as_of"], "method": "derived by evaluate_structure.py from declared structures, factor map and option inputs",
           "sites": {}, "options": {}, "plans": {}, "operations": {}}
    site_ctx, site_struct, site_base = {}, {}, {}
    for t in doc["tenants"]:
        vert = "EV_DEPOT_CAPTIVE" if t["vertical"] == "EV_DEPOT" else t["vertical"]
        rights = {}
        for s_ in t["sites"]:
            for e in ([s_["entitlement"]] if "entitlement" in s_ else []) + s_.get("entitlements", []):
                rights[e["asset"]] = e.get("eligibility", e.get("claim_state"))
        for s_ in t["sites"]:
            n = s_["site"]
            res = {}
            for k in ("plan", "actual"):
                ctx = {"record": s_["period"][k], "prices": t.get("prices", {}), "physical": s_.get("physical", {}),
                       "tariff": s_.get("tariff", {}), "energy_model": t.get("energy_model", {}), "incident": s_.get("incident", {}),
                       "entitlement": s_.get("entitlement", {}), "site": n, "period_days": EV["period_days"]}
                try:
                    env = Env(S[vert], {}, ctx)
                    factors = {f: env.expr(x) for f, x in FM[vert].items()}
                    env = Env(S[vert], factors, ctx)
                    nodes = env.all_nodes()
                    res[k] = {"status": "evaluated", "nodes": {nn: money(v) for nn, v in nodes.items()}}
                    if k == "actual":
                        site_ctx[n], site_struct[n], site_base[n] = ctx, S[vert], factors
                        site_ctx[n]["_tenant"], site_ctx[n]["_rights"] = t, rights
                except Missing as m:
                    stated = s_["period"][k].get("contribution", s_["period"][k].get("total"))
                    res[k] = {"status": f"not decomposed: stated total (missing leaf {m})", "stated_total": stated}
            out["sites"][f"{t['tenant']}/{n}"] = res

    def param_value(spec, ctx, row, params):
        if isinstance(spec, dict) and "value" in spec:
            return num(spec["value"])
        if isinstance(spec, (int, float)):
            return num(spec)
        if isinstance(spec, str):
            if spec in params:
                return params[spec]
            root, _, rest = spec.partition(".")
            src = row if root == "row" else ctx.get(root, {})
            env = Env({}, {}, {"x": src, "site": ctx["site"]})
            return num(env.path(ast.parse("x" + ("." + rest if rest else ""), mode="eval").body))
        raise Missing(str(spec))

    def resolve_date(spec, ctx, row, params):
        d = spec.get("date")
        if d == "none":
            return None
        if d == "as_of":
            base = as_of
        else:
            root, _, rest = d.partition(".")
            src = row if root == "row" else ctx.get(root, {})
            raw = Env({}, {}, {"x": src, "site": ctx["site"]}).path(ast.parse("x." + rest, mode="eval").body)
            base = dt.date.fromisoformat(str(raw)[:10])
        days = sum(int(params[p] if p in params else param_value(p, ctx, row, params)) for p in spec.get("plus", []))
        base = base + dt.timedelta(days=days)
        if "business_days" in spec:
            base = add_business_days(base, int(param_value(spec["business_days"], ctx, row, params)))
        return base

    rows = {}
    for t in doc["tenants"]:
        for s_ in t["sites"]:
            for blk in ("decision", "entitlement"):
                for o in (s_.get(blk) or {}).get("options", []):
                    rows[o["id"]] = o
            for e in s_.get("entitlements", []):
                for o in e.get("options", []):
                    rows[o["id"]] = o

    PROTECT = {"obligation_hours_without_redundancy", "nights_without_backup_cover", "departures_missed"}

    def run(oid, param_over=None, factor_over=None):
        spec = EV["options"][oid]
        site = spec["site"]
        ctx, struct, base = site_ctx[site], site_struct[site], site_base[site]
        row = rows.get(oid, {})
        params = {}
        for pn, ps in (spec.get("params") or {}).items():
            if pn == "restore":
                continue
            params[pn] = num((param_over or {})[pn]) if pn in (param_over or {}) else param_value(ps, ctx, row, params)
        restore = resolve_date(spec["params"]["restore"], ctx, row, params) if "restore" in (spec.get("params") or {}) else None
        if "restore" in (spec.get("params") or {}):
            params["days_to_restore"] = D((end - as_of).days + 1) if restore is None else D((restore - as_of).days)

        def apply(ref_factors, changes, extra_params):
            f = dict(base)
            env0 = Env(struct, dict(f), {**ctx, **{k: v for k, v in extra_params.items()}})
            for k, x in (ref_factors or {}).items():
                f[k] = env0.expr(x)
            env1 = Env(struct, dict(f), ctx)
            env1.values.update(extra_params)
            newf = dict(f)
            for k, x in (changes or {}).items():
                newf[k] = env1.expr(x)
            for k, x in (factor_over or {}).items():
                newf[k] = Env(struct, dict(newf), ctx).expr(x)
            return Env(struct, newf, ctx).all_nodes()

        if spec.get("reference_option"):
            ref = run(spec["reference_option"], param_over, factor_over)["_nodes"]
        else:
            rf = dict(spec.get("reference_factors") or {})
            ref = apply(rf, {}, {})
        opt = apply(spec.get("reference_factors"), spec.get("changes"), params)
        months = num(spec.get("months", 1))
        dmoney = opt["contribution"] - ref["contribution"]
        lines, one_off = {}, D(0)
        for ln, lv in (spec.get("cost_lines") or {}).items():
            amt = num(lv["amount"] if isinstance(lv, dict) else lv)
            cov = lv.get("covered_by") if isinstance(lv, dict) else None
            share = D(0) if cov and ctx["_rights"].get(cov) in ("POTENTIALLY_COVERED", "ACCEPTED") else D(1)
            lines[ln] = {"amount": money(amt), "covered_by": cov, "right_state": ctx["_rights"].get(cov) if cov else None,
                         "operator_share": float(share)}
            one_off += amt * share
        # M3 hard bounds: an option whose counterfactual pushes a hard Protect measure above its reference (departures missed), or
        # that carries a declared bound failure from a calibration spike, is rejected before valuation and is never valued in money.
        bound_failed = bool(spec.get("bound_failure")) or ("departures_missed" in opt and opt["departures_missed"] > ref["departures_missed"])
        valued = dmoney != 0 and "money" not in spec and "comparator" not in spec and not spec.get("is_reference") and not bound_failed
        res = {"site": site, "monthly_or_horizon_change": money(dmoney), "months": float(months), "operator_one_off": money(one_off),
               "cost_lines": lines, "valued_in_money": bool(valued),
               "value": money(dmoney * months - one_off) if valued else None,
               "formula": f"(contribution under option {money(opt['contribution'])} - under reference {money(ref['contribution'])}) x {months} - operator-borne one-off {money(one_off)}",
               "protect": {k: money(opt[k]) for k in PROTECT if k in opt},
               "reference_protect": {k: money(ref[k]) for k in PROTECT if k in ref},
               "restore_date": restore.isoformat() if restore else None,
               "params": {k: float(v) for k, v in params.items()},
               "design_values": sorted({ps["design_value"] for ps in (spec.get("params") or {}).values() if isinstance(ps, dict) and "design_value" in ps}),
               "assumptions": [ps["assumption"] for ps in (spec.get("params") or {}).values() if isinstance(ps, dict) and "assumption" in ps] + ([spec["assumption"]] if "assumption" in spec else []),
               "_nodes": opt}
        if "deliverable_kwh_night" in opt:
            res["bound"] = {"required_kwh_night": money(opt["required_kwh_night"]), "supplied_kwh_night": money(opt["supplied_kwh_night"]),
                            "deliverable_kwh_night": money(opt["deliverable_kwh_night"]), "buses_short_per_night": int(opt["buses_short_per_night"])}
            res["cost_per_departure_met"] = money(opt["cost_per_departure_met"])
            res["energy_bill_option"] = money(opt["energy_cost"]); res["energy_bill_reference"] = money(ref["energy_cost"])
        if bound_failed:
            res["bound_failure"] = spec.get("bound_failure") or f"departures missed {money(opt['departures_missed'])} against {money(ref['departures_missed'])} under the reference (hard bound)"
            res["rejected_by_bound"] = True
        return res

    for oid, spec in EV["options"].items():
        r = run(oid)
        sens = {}
        for sn, sp in (spec.get("sensitivities") or {}).items():
            rs = run(oid, sp.get("params"), sp.get("factors"))
            sens[sn] = money(D(str(rs["monthly_or_horizon_change"])) * D(str(rs["months"])) - D(str(rs["operator_one_off"])))
        if sens:
            r["sensitivities"] = sens
        r.pop("_nodes")
        out["options"][oid] = r

    for tid, pl in doc["plans"].items():
        O = out["options"]

        def best(budget, switches, drops=(), sens=None):
            val = {o: D(str((sens or {}).get(o, O[o]["value"] if O[o]["value"] is not None else 0))) for o in O}
            fixed = pl["fixed"]
            cand = [o for o in pl["candidates"] if o not in drops]
            res = None
            for r_ in range(len(cand) + 1):
                for c in itertools.combinations(cand, r_):
                    c = set(c)
                    if any(len(c & set(g)) != 1 for g in pl["exactly_one_of"]):
                        continue
                    if any(o in c and not any((q.startswith("switch:") and switches.get(q[7:])) or q in c for q in req)
                           for o, req in pl["requires_any"].items()):
                        continue
                    items = list(fixed) + sorted(c)
                    spend = sum(D(str(O[o]["operator_one_off"])) for o in items)
                    if spend > budget:
                        continue
                    v = sum(val[o] for o in items if O[o]["valued_in_money"])
                    if res is None or v > res[0]:
                        res = (v, spend, items)
            if res is None:   # no subset satisfies budget, must-do items and exclusivity: a result, not an error
                return {"value": None, "spend": None, "items": list(fixed), "valued_options": [], "valued_option_costs": None,
                        "not_valued_in_money": None, "infeasible": "no plan satisfies the budget, the must-do items and the required choices"}
            v, spend, items = res
            valued = [o for o in items if O[o]["valued_in_money"]]
            vc = sum(D(str(O[o]["operator_one_off"])) for o in valued)
            return {"value": money(v), "spend": money(spend), "items": items, "valued_options": valued,
                    "valued_option_costs": money(vc), "not_valued_in_money": money(spend - vc)}

        names = list(pl["switches"])
        defaults = {k: v[0] for k, v in pl["switches"].items()}
        bud = lambda sw: D(str(sw.get("budget", pl["budget"])))
        cases = {}
        for combo in itertools.product(*[pl["switches"][k] for k in names]):
            sw = dict(zip(names, combo))
            sens = None
            for k, mp in (pl.get("switch_sensitivity") or {}).items():
                if mp.get(sw[k]):
                    sens = {o: O[o]["sensitivities"][mp[sw[k]]] for o in O if mp[sw[k]] in O[o].get("sensitivities", {})}
            cases["/".join(str(v) for v in combo)] = best(bud(sw), sw, sens=sens)
        default = best(bud(defaults), defaults)
        downs = {}
        for dn, drop in (pl.get("downside_drops") or {}).items():
            b_ = best(bud(defaults), defaults, drops=drop)
            downs[dn] = {"value": b_["value"], "valued_options": b_["valued_options"]}
        for o in default["valued_options"]:
            for sn in O[o].get("sensitivities", {}):
                if sn in downs or any(sn in mp.values() for mp in (pl.get("switch_sensitivity") or {}).values()):
                    continue
                sens = {oo: O[oo]["sensitivities"][sn] for oo in default["valued_options"] if sn in O[oo].get("sensitivities", {})}
                downs[sn] = {"value": money(sum(D(str(sens.get(oo, O[oo]["value"]))) for oo in default["valued_options"])),
                             "valued_options": default["valued_options"]}
        for k, mp in (pl.get("switch_sensitivity") or {}).items():
            for swv, sn in mp.items():
                c_ = cases["/".join(str(swv if kk == k else defaults[kk]) for kk in names)]
                downs[sn] = {"value": c_["value"], "valued_options": c_["valued_options"]}
        out["plans"][tid] = {"default": default, "switch_cases": cases, "sensitivity_values": downs,
                             "downside": min((v["value"] for v in downs.values() if v["value"] is not None), default=None) if downs else default["value"]}

    # Portfolio composition (M1 identity): sums of eligible site nodes; ratios as Σ numerator / Σ denominator; sites whose record
    # is not decomposed are named, never zero.
    out["portfolio"] = {}
    for t in doc["tenants"]:
        comp = {}
        for k in ("plan", "actual"):
            sites = [out["sites"][f"{t['tenant']}/{s_['site']}"][k] for s_ in t["sites"]]
            ev_ = [x for x in sites if x["status"] == "evaluated"]
            names = sorted({n for x in ev_ for n in x["nodes"]})
            sums = {n: money(sum(D(str(x["nodes"][n])) for x in ev_)) for n in names}
            if len(ev_) < len(sites):
                stated = sum(D(str(s_["period"][k].get("contribution", s_["period"][k].get("total")))) for s_ in t["sites"])
                sums = {"outcome_total_with_stated_totals": money(stated)}
            if "departures_met" in sums and "cost_to_serve" in sums:
                sums["cost_per_departure_met"] = money(D(str(sums["cost_to_serve"])) / D(str(sums["departures_met"])))
            if k == "plan" and "outcome_total_with_stated_totals" in sums:
                dep = sum(D(str(s_["period"]["plan"].get("departures_required", 0))) for s_ in t["sites"])
                if dep:
                    sums["cost_per_departure_required"] = money(D(str(sums["outcome_total_with_stated_totals"])) / dep)
            comp[k] = {"sums": sums, "not_decomposed": [s_["site"] for s_, x in zip(t["sites"], sites) if x["status"] != "evaluated"]}
        out["portfolio"][t["tenant"]] = comp
    # O2 operations measures, composed from the site structures and declared asset lists (Σ numerator / Σ denominator)
    for t in doc["tenants"]:
        ops = {}
        for m in t["portfolio"].get("operations", {}).get("measures", []):
            if "assets" in m:
                out_days = {k: v for k, v in [(x["id"], x) for x in t["portfolio"]["protect"]["measures"]]}["asset_days_out_of_service"]["sites"]
                den = {s: len(a) * EV["period_days"] for s, a in m["assets"].items()}
                numr = {s: den[s] - out_days[s] for s in den}
                ops[m["id"]] = {"numerator": numr, "denominator": den, "portfolio_pct": money(D(sum(numr.values())) / D(sum(den.values())) * 100)}
            if m["id"] == "deliverable_energy_used":
                numr, den = {}, {}
                for s_ in t["sites"]:
                    nd = out["sites"][f"{t['tenant']}/{s_['site']}"]["actual"]["nodes"]
                    numr[s_["site"]], den[s_["site"]] = nd["scheduled_kwh_night"], nd["deliverable_kwh_night"]
                ops[m["id"]] = {"numerator": numr, "denominator": den,
                                "sites_pct": {s: money(D(str(numr[s])) / D(str(den[s])) * 100) for s in numr},
                                "portfolio_pct": money(D(str(sum(numr.values()))) / D(str(sum(den.values()))) * 100)}
        if ops:
            out["operations"][t["tenant"]] = ops
    return out


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    path = sys.argv[1] if len(sys.argv) > 1 else str(here / "demo-site-scenario-manifest.yaml")
    res = main(path)
    (here / "derived-values.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"derived-values.json written: {len(res['sites'])} sites, {len(res['options'])} options, {len(res['plans'])} plans")
