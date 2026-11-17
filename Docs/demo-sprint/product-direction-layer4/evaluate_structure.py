"""Structure evaluator for the Layer 4 demonstration world (rev 9; owner, ninth message).

Design-pack tool, not product code. It illustrates the mechanics structurally instead of carrying hand-written results:

  M1 Define   - `structures:` in the manifest declares each vertical's outcome as node expressions over named factors.
  M2 Observe  - every site's October outcome is evaluated bottom-up from its leaf factors (actual and plan).
  M3 Evaluate - every valued option is evaluated by re-running the same structure with the option's factor changes against
                no action (valuation identity); sensitivities re-run it with overridden factors; Protect effects are derived
                from the option rows' restore dates, counted from `as_of`.
  M4 Choose   - each plan is chosen by enumerating every subset of candidate options under budget, fixed (must-do and
                protective) items, exclusivity and requirements; switch cases and downsides re-run the allocator.

Writes derived-values.json (every figure with its formula and inputs). check_manifest.py asserts that the figures stated in
the manifest and documents equal these evaluated values; the mock-up's fixtures take computed figures from this file.
Run:  python3 evaluate_structure.py [demo-site-scenario-manifest.yaml]
"""
from __future__ import annotations

import ast
import datetime as dt
import itertools
import json
import operator
import pathlib
import sys
from decimal import Decimal as D

import yaml

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul}


def evaluate(structure: dict, factors: dict) -> dict:
    """Evaluate every node of a declared structure bottom-up. Expressions may use + - * on factors, nodes and numbers."""
    values = {k: D(str(v)) for k, v in factors.items()}

    def ev(node):
        if isinstance(node, ast.BinOp):
            return OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.Constant):
            return D(str(node.value))
        if isinstance(node, ast.Name):
            if node.id not in values:
                values[node.id] = ev(ast.parse(structure[node.id], mode="eval").body)
            return values[node.id]
        raise ValueError(f"unsupported expression element {ast.dump(node)}")

    for name in structure:
        ev(ast.Name(id=name))
    return values


def money(x) -> float:
    return float(D(x).quantize(D("0.01")))


def main(path: str) -> dict:
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    S = doc["structures"]
    as_of = dt.date.fromisoformat(doc["as_of"])
    out: dict = {"as_of": doc["as_of"], "method": "derived by evaluate_structure.py from the declared structures and leaf factors",
                 "sites": {}, "options": {}, "protect_effects": {}, "plans": {}}
    for t in doc["tenants"]:
        tid, vert = t["tenant"], t["vertical"]
        skey = "EV_DEPOT_CAPTIVE" if vert == "EV_DEPOT" else vert
        struct = S[skey]
        # ---- M2: observe each site's outcome through the structure (actual and plan) ----
        for site in t["sites"]:
            n, p = site["site"], site["period"]
            res = {}
            for k in ("plan", "actual"):
                r = p[k]
                if vert == "MINI_GRID":
                    f = {"billed_kwh": r["billed_kwh"], "tariff": t["prices"]["tariff_usd_per_kwh"][n], "productive_kwh": 0,
                         "productive_tariff": t["prices"]["productive_tariff_usd_per_kwh"], "diesel_l": r["diesel_l"],
                         "diesel_price": t["prices"]["diesel_usd_per_l"][n], "battery_throughput_kwh": 0, "wear_rate": 0,
                         "om": r["om"], "staff": r["staff"], "collection_cost": 0}
                    node = "contribution"
                elif vert == "COLD_CHAIN":
                    base = D(1550) + D("0.25") * D(r["crate_days"])
                    f = {"crate_days": r["crate_days"], "rate": "0.20", "contract_crate_days": 0, "contract_rate": "0.18",
                         "base_kwh": 1550, "k_kwh_per_crate_day": "0.25", "excess_kwh": D(r["kwh"]) - base, "elec_price": "0.20",
                         "staff": r["staff"], "maint": r["maint"], "liability": r.get("liability", 0), "handling": 0}
                    node = "contribution"
                else:
                    tariff = site.get("tariff", {})
                    flat = tariff.get("type") == "FLAT"
                    price = D(str(tariff.get("usd_per_kwh", "0.12")))
                    if "peak_kwh" in r:
                        f = {"peak_kwh": r["peak_kwh"], "kwh_2200_2400": r["offpeak_kwh"], "kwh_0000_0500": 0, "max_kw": r["max_kw"],
                             "peak_price": "0.24", "offpeak_price": "0.12", "night_price": "0.12", "demand_rate": 12}
                    else:   # flat tariff or plan stated as a bill total: one kWh line at the flat price, no demand charge
                        kwh = D(str(r["energy_cost"])) / (price if flat else D(1))
                        f = {"peak_kwh": 0, "kwh_2200_2400": kwh, "kwh_0000_0500": 0, "max_kw": 0,
                             "peak_price": 0, "offpeak_price": price if flat else 1, "night_price": 0, "demand_rate": 0}
                    f.update({"maintenance": r["maintenance"], "penalties": 0})
                    node = "cost_to_serve"
                v = evaluate(struct, f)
                res[k] = {"outcome_node": node, "value": money(v[node]),
                          "nodes": {kk: money(vv) for kk, vv in v.items() if kk in struct}}
            out["sites"][f"{tid}/{n}"] = res
        # ---- M3: evaluate each valued option against no action through the same structure ----
        ofc = doc["option_factor_changes"].get(tid, {})
        node = "contribution"
        for oid, spec in ofc.get("options", {}).items():
            base = dict(ofc["base_site_factors"][spec["site"]])

            def value_of(overrides=None, delta=None, spec=spec, base=base):
                b = dict(base); b.update(overrides or {})
                changed = dict(b)
                if "factor_set" in spec:
                    changed.update(spec["factor_set"])
                for k, dv in (delta if delta is not None else spec.get("monthly_delta", {})).items():
                    changed[k] = D(str(changed[k])) + D(str(dv))
                v0, v1 = evaluate(struct, b)[node], evaluate(struct, changed)[node]
                monthly = v1 - v0
                return monthly, monthly * D(spec["months"]) - D(str(spec["one_off"])), v0, v1

            monthly, total, v0, v1 = value_of()
            entry = {"monthly_change": money(monthly), "months": spec["months"], "one_off": money(spec["one_off"]),
                     "value": money(total), "no_action_month": money(v0), "option_month": money(v1),
                     "formula": f"({money(v1)} - {money(v0)}) x {spec['months']} - {money(spec['one_off'])}",
                     "design_value": spec.get("design_value"), "assumption": spec.get("assumption"),
                     "bound_failure": spec.get("bound_failure")}
            if vert == "EV_DEPOT":
                entry["no_action_bill"] = money(-v0); entry["option_bill"] = money(-v1)
            sens = {}
            for sname, sp in (spec.get("sensitivities") or {}).items():
                ov = {k: v for k, v in sp.items() if k != "monthly_delta"}
                sens[sname] = money(value_of(ov, sp.get("monthly_delta"))[1])
            if sens:
                entry["sensitivities"] = sens
            out["options"][oid] = entry
        # ---- M3: Protect effects derived from restore dates ----
        end = dt.date(2026, 11, 30)
        rows = {o["id"]: o for s_ in t["sites"] for blk in ("decision", "entitlement") for o in (s_.get(blk) or {}).get("options", [])}
        for e in t["portfolio"].get("protect_effects", []):
            if "restore_from" not in e:
                continue
            per = D(e.get("hours_per_evening", e.get("hours_per_day", e.get("per_day"))))
            vals = {}
            for opt, ref in e["restore_from"].items():
                if ref is None:
                    days = (end - as_of).days + 1
                elif ref == "as_of":
                    days = 0
                else:
                    oid, field = ref.split(".")
                    days = (dt.date.fromisoformat(rows[oid][field]) - as_of).days
                vals[opt] = int(D(days) * per - D(str((e.get("minus") or {}).get(opt, 0) if days else 0)))
            out["protect_effects"][e["decision"]] = {"measure": e["measure"], "values": vals,
                                                     "rule": f"days from as_of ({doc['as_of']}) to the day before restore x {per} h"}
        # ---- M4: choose each plan by enumeration, for every switch case, and its downside ----
        pl = doc["plans"].get(tid)
        if pl:
            def best(budget, switches, drops=(), sens=None):
                vals = {o: D(str(out["options"][o]["value"])) for o in pl["candidates"]}
                if sens:
                    for o, sv in sens.items():
                        vals[o] = D(str(sv))
                fixed = sum(D(str(v)) for v in pl["fixed"].values())
                cand = [o for o in pl["candidates"] if o not in drops]
                res = None
                for r in range(len(cand) + 1):
                    for c in itertools.combinations(cand, r):
                        c = set(c)
                        if any(len(c & set(g)) != 1 for g in pl["exactly_one_of"]):
                            continue
                        ok = True
                        for o, req in pl["requires_any"].items():
                            if o in c and not any((q.startswith("switch:") and switches.get(q[7:])) or q in c for q in req):
                                ok = False
                        if not ok:
                            continue
                        cost = fixed + sum(D(str(out["options"][o]["one_off"])) for o in c)
                        if cost > budget:
                            continue
                        val = sum(vals[o] for o in c)
                        if res is None or val > res[0]:
                            res = (val, cost, sorted(c))
                return {"value": money(res[0]), "spend": money(res[1]), "valued_options": res[2],
                        "valued_option_costs": money(res[1] - fixed), "not_valued_in_money": money(fixed)}

            names = list(pl["switches"])
            cases = {}
            for combo in itertools.product(*[pl["switches"][k] for k in names]):
                sw = dict(zip(names, combo))
                budget = D(str(sw.get("budget", pl["budget"])))
                sens = None
                for k, mapping in (pl.get("switch_sensitivity") or {}).items():
                    sname = mapping.get(sw[k])
                    if sname:
                        sens = {o: out["options"][o]["sensitivities"][sname] for o in pl["candidates"]
                                if sname in out["options"][o].get("sensitivities", {})}
                cases["/".join(str(v) for v in combo)] = best(budget, sw, sens=sens)
            default_sw = {k: v[0] for k, v in pl["switches"].items()}
            default = best(D(str(default_sw.get("budget", pl["budget"]))), default_sw)
            downs = {}
            for dname, drop in (pl.get("downside_drops") or {}).items():
                downs[dname] = best(D(str(default_sw.get("budget", pl["budget"]))), default_sw, drops=drop)["value"]
            for o in default["valued_options"]:
                for sname, sv in out["options"][o].get("sensitivities", {}).items():
                    if sname in downs:
                        continue
                    sens = {oo: out["options"][oo]["sensitivities"][sname] for oo in default["valued_options"]
                            if sname in out["options"][oo].get("sensitivities", {})}
                    downs[sname] = money(sum(D(str(sens.get(oo, out["options"][oo]["value"]))) for oo in default["valued_options"]))
            for k, mapping in (pl.get("switch_sensitivity") or {}).items():
                for swv, sname in mapping.items():
                    downs[sname] = cases["/".join(str(swv if kk == k else default_sw[kk]) for kk in names)]["value"]
            out["plans"][tid] = {"default": default, "switch_cases": cases, "sensitivity_values": downs,
                                 "downside": min(downs.values()) if downs else default["value"]}
    return out


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    path = sys.argv[1] if len(sys.argv) > 1 else str(here / "demo-site-scenario-manifest.yaml")
    res = main(path)
    (here / "derived-values.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"derived-values.json written: {len(res['sites'])} site outcomes, {len(res['options'])} options, "
          f"{len(res['protect_effects'])} Protect effects, {len(res['plans'])} plans")
