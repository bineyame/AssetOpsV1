"""Structure evaluator for the Layer 4 demonstration world (rev 13; owner, ninth to eleventh messages).

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
  M4 Choose   - `plans:` lists decisions. Protective and valued decisions are enumerated together (one product), judged jointly
                against the budget, the crew-visit limit, switch requirements and dated dependencies (requires_restore); the
                plan is the feasible combination with the least total violation of decisions on their least-violation fallback,
                then the highest value, then the lowest spend (structure-specification.md §6). Switch cases, sensitivities, the
                downside and owner-question variants re-run it.

Writes derived-values.json (every figure with its formula) and missing-records.json (the record behind every empty leaf,
structure-specification.md §3.1). Run:  python3 evaluate_structure.py [manifest]
"""
from __future__ import annotations

import ast
import datetime as dt
import copy
import itertools
import json
import math
import operator
import pathlib
import re
import sys
from decimal import Decimal as D

import yaml


class Missing(Exception):
    pass


NOTIFIED = ("NOTIFIED", "ACKNOWLEDGED", "ACCEPTED", "DENIED", "REJECTED")   # a notice has been given (brief l.430 claim states)


BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
FUNCS = {"min": min, "max": max, "ceil": lambda x: D(math.ceil(x)), "floor": lambda x: D(math.floor(x))}
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
            if node.func.id == "nights_listed":   # dated roster records: how many listed nights fall in [from, to)
                lst, a, b = self.path(node.args[0]), as_date(self.path(node.args[1])), self.path(node.args[2])
                b = as_date(b) if b is not None else None
                return D(sum(1 for x in lst if a <= as_date(x) and (b is None or as_date(x) < b)))
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


def observe_side(S, FM, vert, t, s_, record, obs, incident, entitlement, period_days, period_end, as_of):
    """M2 for one side of one site: leaf factors from the side's record, then every node bottom-up (P6, R2). Returns
    (result, ctx, factors); factors is None when the side is not decomposed. October and the history (DS1) both call it."""
    n = s_["site"]
    ctx = {"as_of": as_of, "record": record, "prices": t.get("prices", {}), "physical": s_.get("physical", {}), "tariff": s_.get("tariff", {}),
           "energy_model": t.get("energy_model", {}), "incident": incident, "entitlement": entitlement, "observations": obs,
           "tenant": t, "site": n, "period_days": period_days, "period_end": period_end}
    try:
        env = Env(S[vert], {}, ctx)
        fm = {**FM[vert], **(s_.get("factor_sources") or {})}   # a site may declare which of its records feeds a leaf
        factors = {f: env.expr(x) for f, x in fm.items()}
        env = Env(S[vert], factors, ctx)
        nodes = env.all_nodes()
        return {"status": "evaluated", "nodes": {nn: money(v) for nn, v in nodes.items()}}, ctx, factors
    except Missing as m:
        stated = record.get("contribution", record.get("total"))
        return {"status": f"not decomposed: stated total (missing leaf {m})", "stated_total": stated}, ctx, None


def main(path, variants=True) -> dict:
    doc = yaml.safe_load(open(path, encoding="utf-8")) if isinstance(path, (str, pathlib.Path)) else copy.deepcopy(path)
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
                                          "cover_value": e.get("cover_value"), "notice_deadline": e.get("notice_deadline"),
                                          "notice_term": e.get("notice_term")}
                    r_ = rights[e["asset"]]   # a deadline already passed at as_of with no notice given is a state, for every option
                    if r_["notice_deadline"] and r_["claim_state"] not in NOTIFIED and as_date(r_["notice_deadline"]) < as_of \
                            and r_["eligibility"] == "POTENTIALLY_COVERED":
                        r_["eligibility"], r_["lapsed_before_as_of"] = "LAPSED", r_["notice_deadline"]
        for s_ in t["sites"]:
            n = s_["site"]
            res = {}
            obs = s_.get("observations", {})
            sides = [("plan", s_["period"]["plan"]), ("actual", {**s_["period"]["actual"], **obs.get("october", {})})]
            if "november_to_date" in obs:
                sides.append(("november_to_date", obs["november_to_date"]))
            for k, record in sides:
                res[k], ctx, factors = observe_side(S, FM, vert, t, s_, record, obs, s_.get("incident", {}), s_.get("entitlement", {}),
                                                    EV["period_days"], record.get("period_end", EV["period_end"]), doc["as_of"])
                if k == "actual" and factors is not None:
                    site_ctx[n], site_struct[n], site_base[n], site_vert[n], site_tenant[n] = ctx, S[vert], factors, vert, t["tenant"]
                    site_ctx[n]["_rights"] = rights
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


    # M5 (rev 13): which options decide a right is derived, never keyed by hand: an option touches a right when a cost line is
    # covered by it, its restore is performed under it, or it voids, sets or files notice on it; every option in a plan decision
    # that contains a touching option decides that right too (the decision is about that asset).
    def touches(oid):
        sp = EV["options"][oid]
        t_ = {lv.get("covered_by") for lv in (sp.get("cost_lines") or {}).values() if isinstance(lv, dict) and lv.get("covered_by")}
        t_ |= {((sp.get("params") or {}).get("restore") or {}).get("performed_under")} - {None}
        t_ |= set(sp.get("voids_rights") or []) | set(sp.get("set_rights") or {}) | set(sp.get("files_notice") or {})
        return t_
    deciders = {}
    for oid in EV["options"]:
        for a in touches(oid):
            deciders.setdefault(a, set()).add(oid)
    for pl_ in doc["plans"].values():
        for d in pl_["decisions"]:
            for a in {a for o in d["options"] for a in touches(o)}:
                deciders.setdefault(a, set()).update(d["options"])
    out["deciders"] = {a: sorted(v) for a, v in deciders.items()}
    value_end = {t["tenant"]: (as_of.replace(year=as_of.year + int(t["portfolio_constraints"]["horizon_months"]) // 12) - dt.timedelta(days=1))
                 for t in doc["tenants"]}   # the money horizon: the tenant's declared horizon (12 months) from as_of
    out["horizons"] = {"protect_horizon_end": EV["horizon_end"], "value_horizon_end": {k: v.isoformat() for k, v in value_end.items()}}

    def run(oid, param_over=None, factor_over=None):
        spec = EV["options"][oid]
        site = spec["site"]
        ctx, struct, base, vert = site_ctx[site], site_struct[site], site_base[site], site_vert[site]
        row = rows.get(oid, {})
        params, deferred = {}, []
        for pn, ps in (spec.get("params") or {}).items():
            if pn == "restore":
                continue
            try:
                params[pn] = num((param_over or {})[pn]) if pn in (param_over or {}) else resolve(ps, ctx, row, params)
            except Missing:
                deferred.append((pn, ps))   # parameters that read the derived restore date are resolved after it
        rights = {a: dict(r) for a, r in ctx["_rights"].items()}
        for a, st in (spec.get("set_rights") or {}).items():
            rights[a]["eligibility"] = st
        lost, lapsed = D(0), []
        for a in spec.get("voids_rights") or []:
            lost += num(rights[a]["cover_value"]) if covered(rights[a]) else D(0)
            rights[a]["eligibility"] = "VOIDED"
        for a, r in rights.items():   # for the options deciding a right (derived): an open notice deadline lapses unless notice is filed by it
            if oid in deciders.get(a, ()) and r.get("notice_deadline") and r.get("claim_state") not in NOTIFIED and covered(r):
                filed = (spec.get("files_notice") or {}).get(a)
                filed_on = None if filed is None else resolve_date(filed, ctx, row, params)
                if filed_on is None or filed_on > as_date(r["notice_deadline"]):   # never filed, or filed too late: the right is lost
                    lost += num(r["cover_value"]); r["eligibility"] = "LAPSED"; lapsed.append(a)
        restore, restore_basis, restore_spec_crews = None, None, None
        if "restore" in (spec.get("params") or {}):
            rs = spec["params"]["restore"]
            if rs.get("performed_under") and not covered(rights.get(rs["performed_under"])):   # the supplier restores only under a live right
                rs, restore_basis = rs.get("if_not_covered", {"date": "none"}), f"{rs['performed_under']} not covered: supplier restore does not apply"
                restore_spec_crews = rs.get("crew_visits")
            restore = resolve_date(rs, ctx, row, params)
            vend = value_end[site_tenant[site]]
            # Protect effects are stated to the reporting horizon (end); money runs to the tenant's horizon (vend): rev 13, M2
            params["days_to_restore"] = D((end - as_of).days + 1) if restore is None else D((min(restore, end + dt.timedelta(days=1)) - as_of).days)
            params["value_days_to_restore"] = D((vend - as_of).days + 1) if restore is None else D((min(restore, vend + dt.timedelta(days=1)) - as_of).days)
        rctx = {**ctx, "restore_date": restore.isoformat() if restore else None}
        for pn, ps in deferred:
            params[pn] = num((param_over or {})[pn]) if pn in (param_over or {}) else resolve(ps, rctx, row, params)

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
        if restore_spec_crews is not None:   # the operator's own procurement replaces the supplier's work (spec §4.2)
            crews = int(resolve(restore_spec_crews, ctx, row, params))
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
        dec_of = {o: d for d in pl["decisions"] for o in d["options"]}

        def viol(o, d):
            return sum(D_(O[o]["violations"].get(b, 0)) for b in d.get("hard", []))

        def admissible(o, d):
            return viol(o, d) == 0

        def candidates(d, drops=()):
            """Options a decision may take: those meeting its hard bounds; if none can and it declares the fallback, all of them
            (violation is then minimised jointly with the rest of the plan)."""
            opts = [o for o in d["options"] if o not in drops and (d["kind"] == "protective" or O[o]["value_if_admissible"] is not None)]
            ok = [o for o in opts if admissible(o, d)]
            return (ok, False) if ok or d.get("fallback") != "least_violation" else (opts, True)

        def connectable(o, items, switches):
            """rev 13 (H1): a dependency evaluated from dates, not a rule. The option needs an asset restored (by whichever option of
            the named decision the plan takes) early enough that the declared lead still fits before the declared deadline."""
            rq = EV["options"][o].get("requires_restore")
            if not rq:
                return True, None
            dd = next(d for d in pl["decisions"] if d["name"] == rq["decision"])
            by_ = [x for x in items if x in dd["options"]]
            rd = O[by_[0]]["restore_date"] if by_ else None
            if rd is None:
                return False, f"{by_[0] if by_ else 'no option'}: never restored"
            row = rows.get(o, {})
            ctx = {**site_ctx[EV["options"][o]["site"]], "row": row}
            lead = int(Env({}, {}, ctx).expr(rq["plus_business_days"]))
            dl = rq["by"]
            for sw, alt in (rq.get("by_if_switch") or {}).items():
                if switches.get(sw):
                    dl = alt
            deadline = as_date(Env({}, {}, ctx).path(ast.parse(dl, mode="eval").body))
            ready = add_business_days(as_date(rd), lead)
            return ready <= deadline, f"{by_[0]} restores {rd}; +{lead} working days = {ready.isoformat()} vs {deadline.isoformat()}"

        prot_default = None
        valued = [d for d in pl["decisions"] if d["kind"] in ("protective", "valued")]

        def best(budget, switches, drops=(), sens=None):
            """rev 13 (M1): one enumeration over protective and valued decisions together, judged jointly against the budget and
            the visit limit. Rank: least total violation (decisions on the fallback), then plan value, then lower spend."""
            choice_sets, lvd = [], set()
            for d in valued:
                opts, lv = candidates(d, drops)
                if lv:
                    lvd.add(d["name"])
                if d["kind"] == "valued" and (d.get("optional", True) or not opts):
                    opts = [None] + opts
                choice_sets.append(opts)
            res, why_not = None, {}
            for combo in itertools.product(*choice_sets):
                items = [o for o in combo if o]
                if any(EV["options"][o].get("requires_switch") and not switches.get(EV["options"][o]["requires_switch"]) for o in items):
                    continue
                conn = {o: connectable(o, items, switches) for o in items}
                if any(not ok for ok, _ in conn.values()):
                    for o, (ok, w) in conn.items():
                        if not ok: why_not[o] = w
                    continue
                if any(not d.get("optional", True) and not (set(items) & set(d["options"])) for d in valued if d["kind"] == "valued"):
                    continue
                spend = sum(D_(O[o]["operator_one_off"]) for o in items)
                if any(O[o]["crew_visits"] is None for o in items):   # unknown visits are never defaulted (spec §5.7)
                    continue
                crews = sum(O[o]["crew_visits"] for o in items)
                if spend > budget or crews > crew_limit:
                    continue
                v = sum(D_((sens or {}).get(o, O[o]["value_if_admissible"])) for o in items if O[o]["money_changes"])
                pen = sum(viol(o, dec_of[o]) for o in items if dec_of[o]["name"] in lvd)
                key = (-pen, v, -spend)
                if res is None or key > res[0]:
                    res = (key, spend, items, crews, conn)
            if res is None:
                return {"value": None, "spend": None, "items": [], "valued_options": [], "valued_option_costs": None, "not_valued_in_money": None,
                        "crew_visits_used": None, "crew_visits_limit": crew_limit, "protective_choices": {},
                        "infeasible": "no plan satisfies the budget, the crew-visit limit, the bounds and the dated dependencies"}
            (pen, v, _), spend, items, crews, conn = res
            prot = {}
            for d in pl["decisions"]:
                if d["kind"] != "protective":
                    continue
                pick = next(o for o in items if o in d["options"])
                least_any = min(d["options"], key=lambda o: (viol(o, d), D_(O[o]["operator_one_off"])))
                prot[d["name"]] = {"chosen": pick, "admissible": [o for o in d["options"] if admissible(o, d)],
                                   "how": "meets its hard bounds" if admissible(pick, d) else f"least violation within the plan ({money(viol(pick, d))})"}
                if viol(least_any, d) < viol(pick, d):
                    prot[d["name"]]["trade_off"] = {"smaller_violation_option": least_any, "its_violation": money(viol(least_any, d)),
                                                    "its_one_off": O[least_any]["operator_one_off"], "its_crew_visits": O[least_any]["crew_visits"],
                                                    "why_not": "the plan cannot include it within the budget and the visit limit"}
            vo = [o for o in items if O[o]["money_changes"]]
            vc = sum(D_(O[o]["operator_one_off"]) for o in vo)
            return {"value": money(v), "spend": money(spend), "items": items, "valued_options": vo, "valued_option_costs": money(vc),
                    "not_valued_in_money": money(spend - vc), "crew_visits_used": crews, "crew_visits_limit": crew_limit, "protective_choices": prot,
                    "dependencies": {o: w for o, (ok, w) in conn.items() if w}, "not_connectable": why_not,
                    **({"least_violation_total": money(-pen)} if pen else {})}

        defaults0 = {k: v[0] for k, v in pl["switches"].items()}
        first = best(D_(defaults0.get("budget", pl["budget"])), defaults0)
        for d in pl["decisions"]:
            for o in d["options"]:
                O[o]["admissible"] = admissible(o, d)
                chosen = o in first["items"]
                O[o]["value"] = O[o]["value_if_admissible"] if (O[o]["admissible"] or (chosen and O[o]["money_changes"])) else None
                O[o]["valued_in_money"] = O[o]["value"] is not None
                O[o]["decision"] = d["name"]
                if not O[o]["admissible"]:
                    O[o]["bound_failure"] = ("least violation: " if chosen else "hard bound: ") + \
                        ", ".join(f"{b} exceeded by {O[o]['violations'][b]}" for b in d.get("hard", []) if O[o]["violations"].get(b))

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
    if variants:   # owner-question alternatives: each patch is run on a copy of the declared inputs (no hand-described effects)
        for q, spec_ in (doc.get("owner_question_variants") or {}).items():
            out.setdefault("owner_question_variants", {})[q] = qv = {"applied": spec_["applied"]}
            for name, v in spec_.items():
                if name == "applied":
                    continue
                d2 = copy.deepcopy(doc)
                for op in v["patch"]:
                    tgt, key = patch_target(d2, op["path"])
                    if "set" in op:
                        tgt[key] = op["set"]
                    if "remove" in op:
                        tgt[key] = [x for x in tgt[key] if x != op["remove"]]
                r = main(d2, variants=False)
                qv[name] = {tid: {"cases": {k: {f: c.get(f) for f in ("value", "spend", "items", "crew_visits_used")} for k, c in p_["switch_cases"].items()}}
                            for tid, p_ in r["plans"].items()}
            ap = qv[spec_["applied"]]
            for name in [n for n in qv if n != "applied"]:
                for tid, pv in qv[name].items():
                    for k, c in pv["cases"].items():
                        a_ = ap[tid]["cases"][k]
                        c["value_change_vs_applied"] = money(D_(c["value"]) - D_(a_["value"])) if c["value"] is not None and a_["value"] is not None else None
                        c["spend_change_vs_applied"] = money(D_(c["spend"]) - D_(a_["spend"])) if c["spend"] is not None and a_["spend"] is not None else None
    return out


# ---------------- Empty states: the record behind every "not available yet" (rev 16.13; structure-specification.md §3.1) --------
def leftmost(node):
    """The first alternative of `a | b | c`: the leaf's own record."""
    node = node.body if isinstance(node, ast.Expression) else node
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        node = node.left
    return node


def ancestors(struct, leaves):
    """Nodes whose value rests on any of `leaves`, nearest first (breadth-first up the declared structure)."""
    refs = {n: {x.id for x in ast.walk(ast.parse(str(e), mode="eval")) if isinstance(x, ast.Name)} for n, e in struct.items()}
    out, frontier = [], list(leaves)
    while frontier:
        nxt = [n for n in struct if n not in out and n not in leaves and any(f in refs[n] for f in frontier)]
        out += nxt
        frontier = nxt
    return out


def leaf_values(struct, fm, ctx):
    """Each leaf's value on one side (None when nothing fills it), and the leaves filled by their own record (leftmost)."""
    vals, own = {}, set()
    for f, x in fm.items():
        try:
            vals[f] = Env(struct, {}, ctx).expr(x)
        except Missing:
            vals[f] = None
        try:
            Env(struct, {}, ctx).ev(leftmost(ast.parse(str(x), mode="eval")))
            own.add(f)
        except Missing:
            pass
    return vals, own


def missing_entry(side, subject, row, cause, carried_as, blocks, **extra):
    e = {"side": side, **subject, "record_kind": row["kind"], "source_family": row["family"], "cause": cause,
         "carried_as": carried_as, "blocks": blocks, "slice": row["slice"]}
    if row.get("words"):
        e["record_words"] = row["words"]
    e.update(extra)
    return e


def unreceived_leaves(side, fm, vals, leaf_sources, struct):
    """An observed side's entries: a leaf whose record is absent and that nothing else fills (missing_records and history)."""
    return [missing_entry(side, {"leaf": f}, leaf_sources[f], "NOT_RECEIVED", None, ancestors(struct, [f])) for f in fm if vals[f] is None]


def target_side_entries(doc, vert, fm, vals, own):
    """The plan side's entries: not decomposed (RESIDUAL), or leaves without a target line of their own (ASSUMPTION).
    `vals`/`own` hold the plan and actual sides' leaf_values (missing_records and the history, MB5)."""
    S, ES = doc["structures"], doc["empty_states"]
    LS, TS = ES["leaf_sources"], ES["target_side"]
    row = {"kind": TS["kind"], "family": TS["family"], "slice": TS["slice"], "words": TS["words"]}
    gone = [f for f in fm if vals["plan"][f] is None]
    if gone:
        return [missing_entry("plan", {"leaves": gone}, row, "NOT_RECEIVED", "RESIDUAL", ancestors(S[vert], gone))]
    result = doc["chain_model"][vert]["result"]   # Protect and operations measures carry their own declared targets
    split = [f for f in fm if f not in own["plan"] and LS[vert][f]["absent"] not in ("OPTION_ONLY", "NEVER_EMPTY")
             and vals["actual"][f] is not None and vals["actual"][f] != vals["plan"][f] and result in ancestors(S[vert], [f])]
    return [missing_entry("plan", {"leaves": split}, row, "NOT_RECEIVED", "ASSUMPTION", ancestors(S[vert], split),
                          assumption=TS["assumption"])] if split else []


def field_assumption_entries(ES, s_):
    """Record fields marked as assumptions (actual side)."""
    out = []
    for path, ar in ES["assumptions"].items():
        head, field = path.split(".")
        if str((s_.get(head) or {}).get(field, "")).startswith("[assumption]"):
            out.append(missing_entry("actual", {"field": path, "label": ar["label"]}, ar, "NOT_RECEIVED", "ASSUMPTION", ar["blocks"],
                                     assumption=s_[head][field]))
    return out


def deferred_stage_entries(ES, vert):
    """Stages the structure names but no slice of the fortnight builds (actual side)."""
    return [missing_entry("actual", {"stage": st, "label": dr["label"]}, dr, dr["cause"], None, dr["blocks"], trigger=dr["trigger"])
            for st, dr in ES["deferred_stages"].items() if dr["vertical"] == vert]


def missing_records(doc) -> dict:
    """One entry per leaf, condition, assumption or stage that is not available, with the record that would fill it (factor_value
    `missing`, integration-source-to-canonical-design.md §6.2). Computed from empty_states and the records; holds no figure."""
    S, FM, EV, ES = doc["structures"], doc["factor_map"], doc["evaluation"], doc["empty_states"]
    LS, TS = ES["leaf_sources"], ES["target_side"]
    out = {"as_of": doc["as_of"], "method": "derived by evaluate_structure.py missing_records() from empty_states and the site records; "
           "slice and trigger are pack-only fields", "sites": {}}
    for t in doc["tenants"]:
        vert = "EV_DEPOT_CAPTIVE" if t["vertical"] == "EV_DEPOT" else t["vertical"]
        for s_ in t["sites"]:
            n, obs, ents = s_["site"], s_.get("observations", {}), []
            sides = [("plan", s_["period"]["plan"]), ("actual", {**s_["period"]["actual"], **obs.get("october", {})})]
            if "november_to_date" in obs:
                sides.append(("november_to_date", obs["november_to_date"]))
            fm = {**FM[vert], **(s_.get("factor_sources") or {})}
            vals, own = {}, {}
            for k, record in sides:
                ctx = {"as_of": doc["as_of"], "record": record, "prices": t.get("prices", {}), "physical": s_.get("physical", {}), "tariff": s_.get("tariff", {}),
                       "energy_model": t.get("energy_model", {}), "incident": s_.get("incident", {}), "entitlement": s_.get("entitlement", {}), "observations": obs,
                       "tenant": t, "site": n, "period_days": EV["period_days"], "period_end": record.get("period_end", EV["period_end"])}
                vals[k], own[k] = leaf_values(S[vert], fm, ctx)
            entry = missing_entry
            # observed sides: a leaf whose record is absent and that nothing else fills
            for k, _ in sides[1:]:
                ents += unreceived_leaves(k, fm, vals[k], LS[vert], S[vert])
            # the target side: not decomposed (residual), or leaves without a target line of their own (labelled assumption)
            ents += target_side_entries(doc, vert, fm, vals, own)
            # actual lines carried at target (coverage ESTIMATED)
            for line, state in (s_["period"].get("coverage") or {}).items():
                if state == "ESTIMATED":
                    ents.append(entry("actual", {"leaf": line}, LS[vert][line], "NOT_RECEIVED", "TARGET", ancestors(S[vert], [line]),
                                      **({"note": s_["period"]["coverage_note"]} if s_["period"].get("coverage_note") else {})))
            # rights condition evidence
            rights = ([s_["entitlement"]] if "entitlement" in s_ else []) + s_.get("entitlements", []) + \
                     ([s_["incident"]["entitlement"]] if isinstance(s_.get("incident", {}).get("entitlement"), dict) else [])
            for r in rights:
                for c, state in (r.get("evidence") or {}).items():
                    if state == "MISSING":
                        cr = ES["conditions"][c]
                        ents.append(entry("actual", {"right": r["asset"], "condition": c, "label": cr["label"]}, cr, cr["cause"], None,
                                          [r["asset"]]))
            # record fields marked as assumptions; stages the structure names but no slice of the fortnight builds
            ents += field_assumption_entries(ES, s_) + deferred_stage_entries(ES, vert)
            out["sites"][f"{t['tenant']}/{n}"] = ents
    return out


# ---------------- History: July to September (DS1 spec §8.1; D-DS1.4 to D-DS1.12) ----------------
MONTH_ABBR = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
              "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}   # R25b: never strftime


def load_history(path):
    """history.json beside the manifest at `path`, money leaves as Decimal (cents / 100); None when the file is absent."""
    hp = pathlib.Path(path).resolve().parent / "history.json"
    if not hp.exists():
        return None
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    hist = json.loads(hp.read_text(encoding="utf-8"))
    if hist["meta"]["anchor_period"] != doc["accounting_period"]:
        raise ValueError(f"HISTORY_STALE anchor_period {hist['meta']['anchor_period']} != {doc['accounting_period']}")
    want = {(t["tenant"], s_["site"]) for t in doc["tenants"] for s_ in t["sites"]}
    got = {(t, n) for t, ss in hist["tenants"].items() for n in ss}
    if want != got:
        raise ValueError(f"HISTORY_STALE sites {sorted(want ^ got)}")
    money_leaves = set(hist["meta"]["money_leaves"])
    for ss in hist["tenants"].values():
        for months in ss.values():
            for blk in months.values():
                for side in ("plan", "actual"):
                    blk[side] = {k: (D(v) / 100 if k in money_leaves else v) for k, v in blk[side].items()}
    return hist


def evaluate_history(doc, hist, out) -> dict:
    """M2 only, on each Site, history month and side, through observe_side; series of the actual side's outcome, July to
    October (October copied from `out`). Nodes resting on a leaf October takes from observations are not observed (D-DS1.12)."""
    S, FM, CM, ES = doc["structures"], doc["factor_map"], doc["chain_model"], doc["empty_states"]
    H = doc["history"]
    cause = H["missing_cause"]
    months = sorted(hist["meta"]["months"])
    allm = months + [doc["accounting_period"]]
    res = {}
    for t in doc["tenants"]:
        tid = t["tenant"]
        vert = "EV_DEPOT_CAPTIVE" if t["vertical"] == "EV_DEPOT" else t["vertical"]
        kind = "cost" if CM[vert].get("revenue") == "NOT_APPLICABLE" else "contribution"
        outcome = "cost_to_serve" if kind == "cost" else "contribution"
        sites = {}
        for s_ in t["sites"]:
            n = s_["site"]
            key = f"{tid}/{n}"
            fm = {**FM[vert], **(s_.get("factor_sources") or {})}
            obs_keys = set((s_.get("observations") or {}).get("october", {}))
            from_obs = [f for f, x in fm.items()
                        if {a.attr for a in ast.walk(leftmost(ast.parse(str(x), mode="eval")))
                            if isinstance(a, ast.Attribute) and isinstance(a.value, ast.Name) and a.value.id == "record"} & obs_keys]
            periods, series, gap = {}, [], []
            for mo in months:
                blk = hist["tenants"][tid][n][mo]
                periods[mo], seen, vals, own = {}, {}, {}, {}
                for side in ("plan", "actual"):
                    scope = f"{tid}/{n}/{mo}/{side}"
                    r, ctx, _ = observe_side(S, FM, vert, t, s_, blk[side], {}, {}, {}, blk["period_days"], blk["period_end"], doc["as_of"])
                    if r["status"] != out["sites"][key][side]["status"] or (r["status"] != "evaluated" and r["stated_total"] is None):
                        raise ValueError(f"HISTORY_NOT_EVALUATED {scope}")
                    seen[side] = r
                    vals[side], own[side] = leaf_values(S[vert], fm, ctx)
                for side in ("plan", "actual"):
                    scope, r = f"{tid}/{n}/{mo}/{side}", seen[side]
                    # (a) a leaf whose own record October takes from observations: missing, never 0 (shape and slice: missing_records')
                    unobserved = [missing_entry(side, {"leaf": f}, ES["leaf_sources"][vert][f], cause, None, ancestors(S[vert], [f])) for f in from_obs]
                    # (b) the entries October's same side gets, on the history records, less the October-only kinds (coverage
                    # ESTIMATED and rights conditions; review DS1p M1, MB5)
                    if side == "plan":
                        missing = target_side_entries(doc, vert, fm, vals, own)
                    else:
                        missing = [e for e in unreceived_leaves(side, fm, vals[side], ES["leaf_sources"][vert], S[vert]) if e["leaf"] not in from_obs]
                        missing += field_assumption_entries(ES, s_) + deferred_stage_entries(ES, vert)
                    missing += unobserved
                    not_obs = sorted({b for e in unobserved for b in e["blocks"]})
                    if {"contribution", "cost_to_serve"} & set(not_obs):
                        raise ValueError(f"HISTORY_OUTCOME_UNOBSERVED {scope}")
                    side_out = {"status": r["status"]}
                    if r["status"] == "evaluated":   # MB4: the observation leaves themselves leave `nodes` too
                        side_out["nodes"] = {k: v for k, v in r["nodes"].items() if k not in not_obs and k not in from_obs}
                    else:
                        side_out["stated_total"], side_out["nodes"] = money(D(str(r["stated_total"]))), {}
                    side_out["not_observed"], side_out["missing"] = not_obs, missing
                    periods[mo][side] = side_out
            for mo in allm:
                if mo in periods:
                    p_, a_ = periods[mo]["plan"], periods[mo]["actual"]
                else:
                    p_, a_ = out["sites"][key]["plan"], out["sites"][key]["actual"]
                pv, av = [D(str(x["nodes"][outcome] if x["status"] == "evaluated" else x["stated_total"])) for x in (p_, a_)]
                series.append({"m": MONTH_ABBR[mo[5:7]], "p": mo, "v": money(av)})
                gap.append({"m": MONTH_ABBR[mo[5:7]], "p": mo, "v": money(pv - av if kind == "cost" else av - pv)})
            sites[n] = {kind: series, "gap": gap, "periods": periods}
        portfolio = {k: [{"m": MONTH_ABBR[mo[5:7]], "p": mo, "v": money(sum((D(str(x[k][i]["v"])) for x in sites.values()), D(0)))}
                         for i, mo in enumerate(allm)] for k in (kind, "gap")}
        res[tid] = {"kind": kind, "evidence": H["label"]["evidence"], "months": allm, "portfolio": portfolio, "sites": sites}
    return res


def patch_target(doc, path):
    """Resolve 'a.b[key=val].c' to (container, last key) for an owner-question patch."""
    parts = path.split(".")
    cur = doc
    for i, part in enumerate(parts):
        m = re.fullmatch(r"([^\[]+)(?:\[(\w+)=([^\]]+)\])?", part)
        name, k, v = m.groups()
        if i == len(parts) - 1 and not k:
            return cur, name
        cur = cur[name]
        if k:
            cur = next(x for x in cur if str(x.get(k)) == v)
    raise KeyError(path)


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    path = sys.argv[1] if len(sys.argv) > 1 else str(here / "demo-site-scenario-manifest.yaml")
    res = main(path)
    hist = load_history(path)
    if hist is not None:   # DS1: the July to September history, evaluated through the same structures
        res["history"] = evaluate_history(yaml.safe_load(open(path, encoding="utf-8")), hist, res)
    (here / "derived-values.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"derived-values.json written: {len(res['sites'])} sites, {len(res['options'])} options, {len(res['plans'])} plans")
    mr = missing_records(yaml.safe_load(open(path, encoding="utf-8")))
    (here / "missing-records.json").write_text(json.dumps(mr, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"missing-records.json written: {sum(len(v) for v in mr['sites'].values())} entries over {len(mr['sites'])} sites")
