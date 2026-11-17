"""Structure evaluator for the Layer 4 demonstration world (rev 12; owner, ninth to eleventh messages).

Design-pack tool, not product code. It produces the illustration's figures by running the five mechanics on declared inputs,
all the way down the structure, and holds no numbers of its own:

  M1 Define   - `structures:` declares every layer of each vertical as node expressions over named factors: value-chain stages
                and leaks, physical sub-structures and capacity, cost to serve and the outcome, Protect measures and O2 measures.
  M2 Observe  - `factor_map:` turns each site's source records (period record + period observations, tenant prices and capacity,
                site tariff and physical data, energy model, incident) into leaf factors; every node is evaluated bottom-up for the
                plan, October and, where recorded, November to date. Date leaves (failure, fault, unproven backup) are counted with
                days_incl / days_between. A plan stated only as a total is reported as "not decomposed", never as evaluated.
  M3 Evaluate - `evaluation.options`: parameters (from records, or declared with provenance), factor changes applied in order
                as expressions, cost lines (amounts may be expressions) and the right that could bear each, rights the option sets
                or voids, and restore dates derived from their drivers. The option is re-evaluated through the same structure
                against its reference. Rights decide who bears each cost line and give claimable, unclaimable and lost cover.
                Declared bounds (`evaluation.bounds`) are evaluated absolutely on every option.
                Rights with an open notice deadline lapse for any option that files no notice by it (cover lost). Value nets
                the reference path's operator-borne one-off: (option - reference) x months - (option one-off - reference one-off).
                No option carries a typed admissibility: every rejection is a declared bound measured on the option's nodes.
  M4 Choose   - `plans:` lists decisions: protective decisions choose the cheapest affordable option meeting their hard bounds (or,
                if declared, the least violation among the affordable options, reporting the trade-off when a smaller violation is
                unaffordable); valued decisions are enumerated among their admissible options under the budget, the crew-visit
                limit, requirements and switches (a valued decision may declare the same least-violation fallback). Switch cases,
                sensitivities and the downside re-run it, protective choices included.

Writes derived-values.json (every figure with its formula). Run:  python3 evaluate_structure.py [manifest]
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
DATE_FUNCS = {"days_incl": lambda a, b: D((b - a).days + 1), "days_between": lambda a, b: D((b - a).days)}


def num(x):
    if isinstance(x, D):
        return x
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return D(str(x))
    raise Missing(f"not a number: {x!r}")


def as_date(x):
    if isinstance(x, (dt.date, dt.datetime)):
        return x if isinstance(x, dt.date) and not isinstance(x, dt.datetime) else x.date()
    if isinstance(x, str):
        try:
            return dt.date.fromisoformat(x[:10])
        except ValueError:
            pass
    raise Missing(f"not a date: {x!r}")


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
        if isinstance(node, ast.Constant):
            return node.value
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
            if node.func.id in DATE_FUNCS:
                return DATE_FUNCS[node.func.id](*[as_date(self.path(a)) for a in node.args])
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
        out = {n: self.expr(n) for n in self.structure}
        out.update({k: v for k, v in self.values.items() if isinstance(v, D)})
        return out


def money(x):
    return None if x is None else float(D(x).quantize(D("0.01")))


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
    out = {"as_of": doc["as_of"], "method": "derived by evaluate_structure.py from declared structures, factor map, option inputs, bounds and plans",
           "sites": {}, "options": {}, "plans": {}, "operations": {}, "portfolio": {}}
    site_ctx, site_struct, site_base, site_vert, site_tenant = {}, {}, {}, {}, {}

    # ---------------- M2 Observe ----------------
    for t in doc["tenants"]:
        vert = "EV_DEPOT_CAPTIVE" if t["vertical"] == "EV_DEPOT" else t["vertical"]
        rights = {}
        for s_ in t["sites"]:
            for e in ([s_["entitlement"]] if "entitlement" in s_ else []) + s_.get("entitlements", []) + \
                     ([s_["incident"]["entitlement"]] if isinstance(s_.get("incident", {}).get("entitlement"), dict) else []):
                if "asset" in e:
                    rights[e["asset"]] = {"site": s_["site"], "eligibility": e.get("eligibility"), "claim_state": e.get("claim_state"),
                                          "cover_value": e.get("cover_value"), "notice_deadline": e.get("notice_deadline")}
        for s_ in t["sites"]:
            n = s_["site"]
            res = {}
            obs = s_.get("observations", {})
            sides = [("plan", s_["period"]["plan"]), ("actual", {**s_["period"]["actual"], **obs.get("october", {})})]
            if "november_to_date" in obs:
                sides.append(("november_to_date", obs["november_to_date"]))
            for k, record in sides:
                ctx = {"record": record, "prices": t.get("prices", {}), "physical": s_.get("physical", {}), "tariff": s_.get("tariff", {}),
                       "energy_model": t.get("energy_model", {}), "incident": s_.get("incident", {}), "entitlement": s_.get("entitlement", {}), "observations": obs,
                       "tenant": t, "site": n, "period_days": EV["period_days"], "period_end": record.get("period_end", EV["period_end"])}
                try:
                    env = Env(S[vert], {}, ctx)
                    factors = {f: env.expr(x) for f, x in FM[vert].items()}
                    env = Env(S[vert], factors, ctx)
                    nodes = env.all_nodes()
                    res[k] = {"status": "evaluated", "nodes": {nn: money(v) for nn, v in nodes.items()}}
                    if k == "actual":
                        site_ctx[n], site_struct[n], site_base[n], site_vert[n], site_tenant[n] = ctx, S[vert], factors, vert, t["tenant"]
                        site_ctx[n]["_rights"] = rights
                except Missing as m:
                    stated = record.get("contribution", record.get("total"))
                    res[k] = {"status": f"not decomposed: stated total (missing leaf {m})", "stated_total": stated}
            out["sites"][f"{t['tenant']}/{n}"] = res

    # ---------------- M3 Evaluate ----------------
    rows = {}
    for t in doc["tenants"]:
        for s_ in t["sites"]:
            for blk in ("decision", "entitlement"):
                for o in (s_.get(blk) or {}).get("options", []):
                    rows[o["id"]] = o
            for e in s_.get("entitlements", []):
                for o in e.get("options", []):
                    rows[o["id"]] = o

    def resolve(spec, ctx, row, params, nodes=None):
        if isinstance(spec, dict) and "value" in spec:
            return resolve(spec["value"], ctx, row, params, nodes)
        if isinstance(spec, (int, float)):
            return num(spec)
        if isinstance(spec, str):
            if spec in params:
                return params[spec]
            env = Env({}, {**params, **(nodes or {})}, {**ctx, "row": row})
            return env.expr(spec)
        raise Missing(str(spec))

    def resolve_date(spec, ctx, row, params):
        d = spec.get("date")
        if d == "none":
            return None
        if d == "as_of":
            base = as_of
        else:
            base = as_date(Env({}, {}, {**ctx, "row": row}).path(ast.parse(d, mode="eval").body))
        days = sum(int(resolve(p, ctx, row, params)) for p in spec.get("plus", []))
        base = base + dt.timedelta(days=days)
        if "business_days" in spec:
            base = add_business_days(base, int(resolve(spec["business_days"], ctx, row, params)))
        return base

    def covered(r):
        return r and r["eligibility"] == "POTENTIALLY_COVERED" and r.get("claim_state") not in ("DENIED", "REJECTED")

    def rights_nodes(site, rights, lost=D(0)):
        mine = {a: r for a, r in rights.items() if r["site"] == site and r.get("cover_value") is not None}
        unclaim = sum((num(r["cover_value"]) for r in mine.values() if r["eligibility"] == "INSUFFICIENT_EVIDENCE"), D(0))
        return {"claimable_cover": sum((num(r["cover_value"]) for r in mine.values() if covered(r)), D(0)),
                "unclaimable_cover": unclaim, "cover_lost": lost, "cover_not_claimable": unclaim + lost}

    NOTIFIED = ("NOTIFIED", "ACKNOWLEDGED", "ACCEPTED", "DENIED", "REJECTED")   # a notice has been given (brief l.430 claim states)

    def run(oid, param_over=None, factor_over=None):
        spec = EV["options"][oid]
        site = spec["site"]
        ctx, struct, base, vert = site_ctx[site], site_struct[site], site_base[site], site_vert[site]
        row = rows.get(oid, {})
        params = {}
        for pn, ps in (spec.get("params") or {}).items():
            if pn == "restore":
                continue
            params[pn] = num((param_over or {})[pn]) if pn in (param_over or {}) else resolve(ps, ctx, row, params)
        rights = {a: dict(r) for a, r in ctx["_rights"].items()}
        for a, st in (spec.get("set_rights") or {}).items():
            rights[a]["eligibility"] = st
        lost, lapsed = D(0), []
        for a in spec.get("voids_rights") or []:
            lost += num(rights[a]["cover_value"]) if covered(rights[a]) else D(0)
            rights[a]["eligibility"] = "VOIDED"
        for a, r in rights.items():   # for the options deciding an asset: an open notice deadline lapses unless notice is filed by it
            if a == spec.get("asset") and r.get("notice_deadline") and r.get("claim_state") not in NOTIFIED and covered(r):
                filed = (spec.get("files_notice") or {}).get(a)
                filed_on = None if filed is None else resolve_date(filed, ctx, row, params)
                if filed_on is None or filed_on > as_date(r["notice_deadline"]):   # never filed, or filed too late: the right is lost
                    lost += num(r["cover_value"]); r["eligibility"] = "LAPSED"; lapsed.append(a)
        restore, restore_basis = None, None
        if "restore" in (spec.get("params") or {}):
            rs = spec["params"]["restore"]
            if rs.get("performed_under") and not covered(rights.get(rs["performed_under"])):   # the supplier restores only under a live right
                rs, restore_basis = rs.get("if_not_covered", {"date": "none"}), f"{rs['performed_under']} not covered: supplier restore does not apply"
            restore = resolve_date(rs, ctx, row, params)
            params["days_to_restore"] = D((end - as_of).days + 1) if restore is None else D((restore - as_of).days)

        fwd = {k: Env(struct, dict(base), ctx).expr(x) for k, x in (EV.get("forward_baseline", {}).get(vert) or {}).items()}

        def evaluate(ref_factors, changes, extra, rts, lost_=D(0)):
            f = {**base, **fwd}   # options look forward from as_of: period-observation leaves reset to the declared forward baseline
            for k, x in (ref_factors or {}).items():
                f[k] = Env(struct, dict(f), ctx).expr(x)
            for k, x in (changes or {}).items():   # applied in order; each sees the nodes produced by the earlier ones
                e = Env(struct, dict(f), ctx); e.values.update(extra)
                f[k] = e.expr(x)
            for k, x in (factor_over or {}).items():
                f[k] = Env(struct, dict(f), ctx).expr(x)
            nodes = Env(struct, f, ctx).all_nodes()
            nodes.update(rights_nodes(site, rts, lost_))
            return nodes

        if spec.get("reference_option"):
            ref_run = run(spec["reference_option"], param_over, factor_over)
            ref, ref_one_off = ref_run["_nodes"], D(str(ref_run["operator_one_off"]))
        else:
            ref, ref_one_off = evaluate(spec.get("reference_factors"), {}, {}, ctx["_rights"]), D(0)
        opt = evaluate(spec.get("reference_factors"), spec.get("changes"), params, rights, lost)
        months = num(spec.get("months", 1))
        dmoney = opt["contribution"] - ref["contribution"]
        lines, one_off = {}, D(0)
        for ln, lv in (spec.get("cost_lines") or {}).items():
            amt = resolve(lv["amount"] if isinstance(lv, dict) else lv, ctx, row, params, opt)
            cov = lv.get("covered_by") if isinstance(lv, dict) else None
            share = D(0) if cov and covered(rights.get(cov)) else D(1)
            lines[ln] = {"amount": money(amt), "covered_by": cov, "right_eligibility": rights.get(cov, {}).get("eligibility") if cov else None,
                         "claim_state": rights.get(cov, {}).get("claim_state") if cov else None, "operator_share": float(share)}
            one_off += amt * share
        # declared bounds, evaluated absolutely on the option's counterfactual
        violations = {}
        for b in EV["bounds"].get(vert, []):
            if b["node"] in opt:
                limit = Env(struct, dict(opt), ctx).expr(b["max"])
                violations[b["id"]] = money(max(opt[b["node"]] - limit, D(0)))
        try:   # crew visits: from the option row, or declared on the option with its basis; never defaulted
            crews = int(resolve(spec["crew_visits"], ctx, row, params)) if "crew_visits" in spec else int(row["crew_visits"])
        except (KeyError, Missing):
            crews = None
        PROTECT = EV["protect_nodes"][vert]
        res = {"site": site, "monthly_or_horizon_change": money(dmoney), "months": float(months), "operator_one_off": money(one_off),
               "reference_one_off": money(ref_one_off), "net_one_off": money(one_off - ref_one_off), "crew_visits": crews,
               "cost_lines": lines, "money_changes": dmoney != 0 and "comparator" not in spec and not spec.get("is_reference"),
               "formula": f"(contribution under option {money(opt['contribution'])} - under reference {money(ref['contribution'])}) x {months} - (operator-borne one-off {money(one_off)} - reference path's {money(ref_one_off)})",
               "protect": {k: money(opt[k]) for k in PROTECT if k in opt}, "reference_protect": {k: money(ref[k]) for k in PROTECT if k in ref},
               "rights": {"claimable_cover": money(opt["claimable_cover"]), "unclaimable_cover": money(opt["unclaimable_cover"]), "cover_lost": money(lost),
                          "lapsed": lapsed, "states": {a: r["eligibility"] for a, r in rights.items() if r["site"] == site}},
               "violations": violations, "restore_basis": restore_basis,
               "restore_date": restore.isoformat() if restore else None, "params": {k: float(v) for k, v in params.items()},
               "design_values": sorted({ps["design_value"] for ps in (spec.get("params") or {}).values() if isinstance(ps, dict) and "design_value" in ps}),
               "assumptions": [ps["assumption"] for ps in (spec.get("params") or {}).values() if isinstance(ps, dict) and "assumption" in ps] + ([spec["assumption"]] if "assumption" in spec else []),
               "_nodes": opt}
        res["value_if_admissible"] = money(dmoney * months - (one_off - ref_one_off)) if res["money_changes"] else None
        det = EV.get("option_detail", {}).get(vert) or {}   # per-vertical detail nodes shown with an option (declared, not coded)
        if det:
            res["bound"] = {k: money(opt[k]) for k in det.get("capacity", [])}
            for k, nn in (det.get("option_nodes") or {}).items():
                res[k] = money(opt[nn])
            for k, nn in (det.get("reference_nodes") or {}).items():
                res[k] = money(ref[nn])
        return res

    for oid, spec in EV["options"].items():
        r = run(oid)
        sens = {}
        for sn, sp in (spec.get("sensitivities") or {}).items():
            rs = run(oid, sp.get("params"), sp.get("factors"))
            sens[sn] = money(D(str(rs["monthly_or_horizon_change"])) * D(str(rs["months"])) - D(str(rs["net_one_off"])))
        if sens:
            r["sensitivities"] = sens
        r.pop("_nodes")
        out["options"][oid] = r

    # ---------------- M4 Choose ----------------
    O = out["options"]
    D_ = lambda x: D(str(x))
    for o, r in O.items():   # options outside any plan decision: admissible (they are listed, not chosen)
        r["admissible"] = True
        r["value"] = r["value_if_admissible"]
        r["valued_in_money"] = r["value"] is not None
    for tid, pl in doc["plans"].items():
        tenant = next(t for t in doc["tenants"] if t["tenant"] == tid)
        crew_limit = int(tenant["portfolio_constraints"][pl["crew_limit"]])

        def viol(o, d):
            return sum(D_(O[o]["violations"].get(b, 0)) for b in d.get("hard", []))

        def admissible(o, d):
            return viol(o, d) == 0

        def protect_choice(d, budget):
            """Cheapest affordable option meeting the hard bounds; else, if declared, the least violation among affordable options."""
            afford = lambda o: D_(O[o]["operator_one_off"]) <= budget and (O[o]["crew_visits"] or 0) <= crew_limit
            ok = [o for o in d["options"] if admissible(o, d) and afford(o)]
            how, trade = "meets its hard bounds", None
            if not ok and d.get("fallback") == "least_violation":
                aff = [o for o in d["options"] if afford(o)]
                if aff:
                    least = min(viol(o, d) for o in aff)
                    ok = [o for o in aff if viol(o, d) == least]
                    how = f"least violation among affordable options ({money(least)}) - no affordable option meets the hard bound"
                    best_any = min(d["options"], key=lambda o: (viol(o, d), D_(O[o]["operator_one_off"])))
                    if viol(best_any, d) < least:
                        trade = {"smaller_violation_option": best_any, "its_violation": money(viol(best_any, d)), "its_one_off": O[best_any]["operator_one_off"],
                                 "its_crew_visits": O[best_any]["crew_visits"], "why_not": "over the budget or the crew-visit limit"}
            if not ok:
                return {"chosen": None, "how": "unmet: no affordable option meets the hard bound and no fallback is declared", "admissible": []}
            pick = min(ok, key=lambda o: (D_(O[o]["operator_one_off"]), -D_(O[o]["value_if_admissible"] or 0)))
            return {"chosen": pick, "how": how, "admissible": ok, **({"trade_off": trade} if trade else {})}

        prot_default = {d["name"]: protect_choice(d, D_(pl["budget"])) for d in pl["decisions"] if d["kind"] == "protective"}
        for d in pl["decisions"]:
            for o in d["options"]:
                O[o]["admissible"] = admissible(o, d)
                chosen = d["kind"] == "protective" and o == prot_default[d["name"]]["chosen"]
                O[o]["value"] = O[o]["value_if_admissible"] if (O[o]["admissible"] or (chosen and O[o]["money_changes"])) else None
                O[o]["valued_in_money"] = O[o]["value"] is not None
                O[o]["decision"] = d["name"]
                if not O[o]["admissible"]:
                    O[o]["bound_failure"] = ("hard bound: " if d["kind"] != "protective" or not chosen else "least violation: ") + \
                        ", ".join(f"{b} exceeded by {O[o]['violations'][b]}" for b in d.get("hard", []) if O[o]["violations"].get(b))
                if d.get("advisory"):
                    O[o]["advisory"] = {b: O[o]["violations"].get(b) for b in d["advisory"]}
        valued = [d for d in pl["decisions"] if d["kind"] == "valued"]

        def best(budget, switches, drops=(), sens=None):
            prot = {d["name"]: protect_choice(d, budget) for d in pl["decisions"] if d["kind"] == "protective"}
            fixed = [p["chosen"] for p in prot.values() if p["chosen"]]
            choice_sets, lv = [], set()
            for d in valued:
                cands = [o for o in d["options"] if O[o]["value_if_admissible"] is not None and o not in drops]
                opts = [o for o in cands if admissible(o, d)]
                if not opts and d.get("fallback") == "least_violation":   # valued least violation: violation is minimised before value
                    opts, _ = cands, lv.add(d["name"])
                if d.get("optional", True) or not opts:
                    opts = [None] + opts
                choice_sets.append(opts)
            res = None
            for combo in itertools.product(*choice_sets):
                c = {o for o in combo if o}
                if any(o in c and not any((q.startswith("switch:") and switches.get(q[7:])) or q in c for q in req) for o, req in pl.get("requires_any", {}).items()):
                    continue
                if any(not d.get("optional", True) and not (c & set(d["options"])) for d in valued):
                    continue
                items = fixed + sorted(c)
                spend = sum(D_(O[o]["operator_one_off"]) for o in items)
                crews = sum(O[o]["crew_visits"] or 0 for o in items)
                if spend > budget or crews > crew_limit:
                    continue
                v = sum(D_((sens or {}).get(o, O[o]["value_if_admissible"])) for o in items if O[o]["money_changes"])
                pen = sum(viol(o, d) for d in valued if d["name"] in lv for o in c if o in d["options"])
                key = (-pen, v)
                if res is None or key > res[0]:
                    res = (key, spend, items, crews)
            if res is None:
                return {"value": None, "spend": None, "items": fixed, "valued_options": [], "valued_option_costs": None, "not_valued_in_money": None,
                        "crew_visits_used": None, "crew_visits_limit": crew_limit, "protective_choices": prot,
                        "infeasible": "no plan satisfies the budget, the crew-visit limit, the protective choices and the required decisions"}
            (pen, v), spend, items, crews = res
            vo = [o for o in items if O[o]["money_changes"]]
            vc = sum(D_(O[o]["operator_one_off"]) for o in vo)
            return {"value": money(v), "spend": money(spend), "items": items, "valued_options": vo, "valued_option_costs": money(vc),
                    "not_valued_in_money": money(spend - vc), "crew_visits_used": crews, "crew_visits_limit": crew_limit, "protective_choices": prot,
                    **({"least_violation_valued": money(-pen)} if pen else {})}

        names = list(pl["switches"])
        defaults = {k: v[0] for k, v in pl["switches"].items()}
        bud = lambda sw: D_(sw.get("budget", pl["budget"]))
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
                downs[sn] = {"value": money(sum(D_(sens.get(oo, O[oo]["value_if_admissible"])) for oo in default["valued_options"])), "valued_options": default["valued_options"]}
        for k, mp in (pl.get("switch_sensitivity") or {}).items():
            for swv, sn in mp.items():
                c_ = cases["/".join(str(swv if kk == k else defaults[kk]) for kk in names)]
                downs[sn] = {"value": c_["value"], "valued_options": c_["valued_options"]}
        out["plans"][tid] = {"protective_choices": default["protective_choices"], "default": default, "switch_cases": cases, "sensitivity_values": downs,
                             "downside": min((v["value"] for v in downs.values() if v["value"] is not None), default=None) if downs else default["value"]}

    # ---------------- portfolio composition and O2 ----------------
    for t in doc["tenants"]:
        comp = {}
        for k in ("plan", "actual", "november_to_date"):
            sites = [(s_["site"], out["sites"][f"{t['tenant']}/{s_['site']}"].get(k)) for s_ in t["sites"]]
            sites = [(n, x) for n, x in sites if x is not None]
            if not sites:
                continue
            ev_ = [x for _, x in sites if x["status"] == "evaluated"]
            names = sorted({nn for x in ev_ for nn in x["nodes"]})
            sums = {nn: money(sum(D(str(x["nodes"].get(nn, 0))) for x in ev_)) for nn in names}
            if len(ev_) < len(sites):
                stated = sum(D(str(s_["period"][k].get("contribution", s_["period"][k].get("total")))) for s_ in t["sites"])
                sums = {"outcome_total_with_stated_totals": money(stated)}
                dep = sum(D(str(s_["period"][k].get("departures_required", 0))) for s_ in t["sites"])
                if dep:
                    sums["cost_per_departure_required"] = money(D(str(stated)) / dep)
            elif "departures_met" in sums and "cost_to_serve" in sums and sums["departures_met"]:
                sums["cost_per_departure_met"] = money(D(str(sums["cost_to_serve"])) / D(str(sums["departures_met"])))
            comp[k] = {"sums": sums, "not_decomposed": [n for n, x in sites if x["status"] != "evaluated"]}
        out["portfolio"][t["tenant"]] = comp
        ops = {}
        for m in t["portfolio"].get("operations", {}).get("measures", []):
            if "numerator" not in m:
                continue
            per = {}
            for s_ in t["sites"]:
                nd = out["sites"][f"{t['tenant']}/{s_['site']}"]["actual"]["nodes"]
                per[s_["site"]] = (D(str(nd[m["numerator"]])), D(str(nd[m["denominator"]])) if "denominator" in m else None)
            scale = D(str(m.get("scale", 1))); q = D(1).scaleb(-int(m.get("decimals", 2)))
            num_ = sum(v[0] for v in per.values())
            if "denominator" in m:
                den_ = sum(v[1] for v in per.values())
                ops[m["id"]] = {"numerator": {k: float(v[0]) for k, v in per.items()}, "denominator": {k: float(v[1]) for k, v in per.items()},
                                "sites": {k: float((v[0] / v[1] * scale).quantize(q)) for k, v in per.items() if v[1]},
                                "portfolio": float((num_ / den_ * scale).quantize(q))}
            else:
                ops[m["id"]] = {"sites": {k: float(v[0]) for k, v in per.items()}, "portfolio": float(num_)}
        out["operations"][t["tenant"]] = ops
    return out


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    path = sys.argv[1] if len(sys.argv) > 1 else str(here / "demo-site-scenario-manifest.yaml")
    res = main(path)
    (here / "derived-values.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"derived-values.json written: {len(res['sites'])} sites, {len(res['options'])} options, {len(res['plans'])} plans")
