"""Arithmetic checks for demo-site-scenario-manifest.yaml (Layer 4 design pack).

Design-pack tool, not product code. Every illustrative figure in the Layer 4 artifacts comes from the manifest;
this script proves the manifest reconciles to the cent: period identities, bridges, coverage, option economics,
remedy residuals, that the rejected cheapest EV schedule really is the cheapest bill, and that the Lakeside allocation is
the best subset under each budget x letter-of-intent case (brute force). Run:  python3 check_manifest.py demo-site-scenario-manifest.yaml
Exit code 0 = all checks pass.
"""
from __future__ import annotations

import sys
from decimal import Decimal as D

import yaml

failures: list[str] = []
passes = 0


def eq(label: str, a, b) -> None:
    global passes
    if a is None or b is None:
        failures.append(f"{label}: {a} != {b}"); return
    if D(str(a)).quantize(D("0.01")) != D(str(b)).quantize(D("0.01")):
        failures.append(f"{label}: {a} != {b}")
    else:
        passes += 1


def check(label: str, cond: bool) -> None:
    global passes
    if cond:
        passes += 1
    else:
        failures.append(label)


def lt(label: str, a, b) -> None:
    check(f"{label}: {a} < {b}", D(str(a)) < D(str(b)))


def le(label: str, a, b) -> None:
    global passes
    if D(str(a)) > D(str(b)):
        failures.append(f"{label}: {a} > {b}")
    else:
        passes += 1


def mini(t: dict) -> None:
    diesel = t["prices"]["diesel_usd_per_l"]
    tariff = t["prices"]["tariff_usd_per_kwh"]
    total_var = D(0)
    for s in t["sites"]:
        n, p = s["site"], s["period"]
        for k in ("plan", "actual"):
            r = p[k]
            eq(f"{n} {k} revenue", r["revenue"], D(str(r["billed_kwh"])) * D(str(tariff[n])))
            eq(f"{n} {k} diesel", r["diesel_cost"], D(str(r["diesel_l"])) * D(str(diesel[n])))
            eq(f"{n} {k} contribution", r["contribution"],
               D(str(r["revenue"])) - D(str(r["diesel_cost"])) - D(str(r["om"])) - D(str(r["staff"])))
        a = p["actual"]
        if "delivered_kwh" in a:   # value chain (main design 2.1): delivered -> metered -> billed
            loss = D(str(a.get("technical_loss_kwh", 0))) + D(str(a.get("expected_technical_loss_kwh", 0))) + D(str(a.get("unexplained_kwh", 0)))
            eq(f"{n} chain delivered->metered", D(str(a["delivered_kwh"])) - loss, a["metered_kwh"])
            eq(f"{n} chain metered->billed", D(str(a["metered_kwh"])) - D(str(a.get("adjustments_kwh", 0))) - D(str(a.get("unbilled_mapping_kwh", 0))), a["billed_kwh"])
        if "collected" in a:
            eq(f"{n} cash chain", D(str(a["collected"])) + D(str(a["in_transit"])) + D(str(a["outstanding"])), a["revenue"])
        eq(f"{n} variance", p["variance"], D(str(a["contribution"])) - D(str(p["plan"]["contribution"])))
        eq(f"{n} bridge", sum(D(str(b["amount"])) for b in p["bridge"]), p["variance"])
        total_var += D(str(p["variance"]))
    eq("mini portfolio variance", t["portfolio"]["variance"], total_var)
    ch = t["portfolio"]["chain"]; acts = [s_["period"]["actual"] for s_ in t["sites"]]; plans = [s_["period"]["plan"] for s_ in t["sites"]]
    for k in ("delivered_kwh", "metered_kwh", "billed_kwh", "revenue", "collected", "in_transit", "outstanding"):
        eq(f"mini portfolio chain {k}", ch[k], sum(D(str(a_[k])) for a_ in acts))
    eq("mini portfolio plan billed", ch["plan_billed_kwh"], sum(D(str(p_["billed_kwh"])) for p_ in plans))
    eq("mini portfolio plan revenue", ch["plan_revenue"], sum(D(str(p_["revenue"])) for p_ in plans))
    cost = lambda r: D(str(r["diesel_cost"])) + D(str(r["om"])) + D(str(r["staff"]))
    eq("mini portfolio cost to serve", ch["cost_to_serve"], sum(cost(a_) for a_ in acts))
    eq("mini portfolio plan cost", ch["plan_cost_to_serve"], sum(cost(p_) for p_ in plans))
    eq("mini revenue + cost variance", D(str(ch["revenue_variance"])) + D(str(ch["cost_variance"])), t["portfolio"]["variance"])
    eq("mini revenue variance", ch["revenue_variance"], D(str(ch["revenue"])) - D(str(ch["plan_revenue"])))
    eq("mini portfolio variance (plan-actual)", t["portfolio"]["variance"],
       D(str(t["portfolio"]["actual_contribution"])) - D(str(t["portfolio"]["plan_contribution"])))
    al = t["portfolio"]["allocation"]
    eq("mini spend", al["spend"], sum(D(str(v)) for v in al["spend_breakdown"].values()))
    le("mini budget", al["spend"], t["portfolio_constraints"]["budget_usd_nov_dec"])
    m = al["modelled_12m_change"]
    eq("mini modelled total", m["total"], D(str(m["KOB-STOPSOC"])) + D(str(m["MTO-HULLER"])) + D(str(m["MTO-INV-CLAIM"])))


def cold(t: dict) -> None:
    price, kwh_price = D("0.20"), D("0.20")
    total = D(0)
    for s in t["sites"]:
        n, p = s["site"], s["period"]
        for k in ("plan", "actual"):
            r = p[k]
            eq(f"{n} {k} revenue", r["revenue"], D(str(r["crate_days"])) * price)
            eq(f"{n} {k} energy", r["energy"], D(str(r["kwh"])) * kwh_price)
            eq(f"{n} {k} contribution", r["contribution"], D(str(r["revenue"])) - D(str(r["energy"])) - D(str(r["staff"]))
               - D(str(r["maint"])) - D(str(r.get("liability", 0))))
        a = p["actual"]
        eq(f"{n} kwh model", a["kwh_model"], D(1550) + D("0.25") * D(str(a["crate_days"])))
        eq(f"{n} variance", p["variance"], D(str(a["contribution"])) - D(str(p["plan"]["contribution"])))
        eq(f"{n} bridge", sum(D(str(b["amount"])) for b in p["bridge"]), p["variance"])
        total += D(str(p["variance"]))
    eq("cold portfolio variance", t["portfolio"]["variance"], total)
    ch = t["portfolio"]["chain"]; acts = [s_["period"]["actual"] for s_ in t["sites"]]; plans = [s_["period"]["plan"] for s_ in t["sites"]]
    for a_ in acts:
        eq("cold cash chain", D(str(a_["collected"])) + D(str(a_["outstanding"])), a_["revenue"])
    eq("cold capacity", ch["capacity_crate_days"], D(t["capacity_crate_days_oct"]) * len(acts))
    for k, src in (("occupied_crate_days", "crate_days"), ("revenue", "revenue"), ("collected", "collected"), ("outstanding", "outstanding")):
        eq(f"cold portfolio chain {k}", ch[k], sum(D(str(a_[src])) for a_ in acts))
    eq("cold plan crate-days", ch["plan_crate_days"], sum(D(str(p_["crate_days"])) for p_ in plans))
    cost = lambda r: D(str(r["energy"])) + D(str(r["staff"])) + D(str(r["maint"])) + D(str(r.get("liability", 0)))
    eq("cold cost to serve", ch["cost_to_serve"], sum(cost(a_) for a_ in acts))
    eq("cold plan cost", ch["plan_cost_to_serve"], sum(cost(p_) for p_ in plans))
    eq("cold revenue + cost variance", D(str(ch["revenue_variance"])) + D(str(ch["cost_variance"])), t["portfolio"]["variance"])
    al = t["portfolio"]["allocation"]
    eq("cold spend", al["spend"], sum(D(str(v)) for v in al["spend_breakdown"].values()))
    le("cold budget", al["spend"], t["portfolio_constraints"]["budget_usd_nov_dec"])


def ev(t: dict) -> None:
    plan_total, actual_total = D(0), D(0)
    for s in t["sites"]:
        n, p = s["site"], s["period"]
        for k in ("plan", "actual"):
            r = p[k]
            if "demand_cost" in r:
                eq(f"{n} {k} energy parts", r["energy_cost"], D(str(r["peak_cost"])) + D(str(r["offpeak_cost"])) + D(str(r["demand_cost"])))
            eq(f"{n} {k} total", r["total"], D(str(r["energy_cost"])) + D(str(r["maintenance"])))
        eq(f"{n} variance", p["variance"], D(str(p["plan"]["total"])) - D(str(p["actual"]["total"])))
        if "bridge" in p:
            eq(f"{n} bridge", sum(D(str(b["amount"])) for b in p["bridge"]), p["variance"])
        plan_total += D(str(p["plan"]["total"])); actual_total += D(str(p["actual"]["total"]))
    pf = t["portfolio"]
    eq("ev plan", pf["plan_cost"], plan_total)
    eq("ev actual", pf["actual_cost"], actual_total)
    eq("ev variance", pf["variance"], plan_total - actual_total)
    eq("ev chain delivered", pf["chain"]["delivered_kwh"], sum(D(str(s_["period"]["actual"]["kwh"])) for s_ in t["sites"]))
    eq("ev chain departures", pf["chain"]["departures_met"], sum(D(str(s_["period"]["actual"]["departures_met"])) for s_ in t["sites"]))
    eq("ev cost per departure", pf["cost_per_departure_actual"], (actual_total / D(pf["departures_met"])).quantize(D("0.01")))
    al = pf["allocation"]
    eq("ev spend", al["spend"], sum(D(str(v)) for v in al["spend_breakdown"].values()))
    le("ev budget", al["spend"], t["portfolio_constraints"]["budget_usd_nov_dec"])
    # option economics (M1: the rejected cheapest schedule must really be the cheapest bill)
    emb = t["sites"][0]; o = {x["id"]: x for x in emb["decision"]["options"]}
    ch, dl = o["EMB-CHEAPEST"]["economics"], o["EMB-DEADLINE"]["economics"]
    eq("emb cheapest energy", ch["energy"], D(ch["kwh_month"]) * D("0.09"))
    eq("emb cheapest kwh", ch["kwh_month"], D(o["EMB-CHEAPEST"]["deliverable_kwh"]) * 31)
    eq("emb cheapest unserved", ch["unserved_kwh_month"], (D(o["EMB-CHEAPEST"]["required_kwh"]) - D(o["EMB-CHEAPEST"]["deliverable_kwh"])) * 31)
    eq("emb cheapest cost", ch["energy_cost_monthly"], D(str(ch["energy"])) + D(str(ch["demand"])))
    eq("emb deadline cost", dl["energy_cost_monthly"], D(dl["kwh_2200_2400"]) * D("0.12") + D(dl["kwh_0000_0500"]) * D("0.09") + D(str(dl["demand"])))
    eq("emb deadline kwh", D(dl["kwh_2200_2400"]) + D(dl["kwh_0000_0500"]), D(o["EMB-DEADLINE"]["required_kwh"]) * 31)
    eq("emb deadline demand", dl["demand"], D(o["EMB-DEADLINE"]["max_kw"]) * D(12))
    na = o["EMB-NOACT"]["economics"]
    eq("emb no-action kwh", D(na["peak_kwh"]) + D(na["kwh_2200_2400"]) + D(na["kwh_0000_0500"]), emb["period"]["actual"]["kwh"])
    eq("emb no-action peak", na["peak_cost"], D(na["peak_kwh"]) * D("0.24"))
    eq("emb no-action 22-24", na["cost_2200_2400"], D(na["kwh_2200_2400"]) * D("0.12"))
    eq("emb no-action 00-05", na["cost_0000_0500"], D(na["kwh_0000_0500"]) * D("0.09"))
    eq("emb no-action bill", na["energy_cost_monthly"], D(str(na["peak_cost"])) + D(str(na["cost_2200_2400"])) + D(str(na["cost_0000_0500"])) + D(str(na["demand"])))
    eq("emb tariff windfall (not option value)", na["tariff_tier_windfall_monthly"], D(str(emb["period"]["actual"]["energy_cost"])) - D(str(na["energy_cost_monthly"])))
    eq("emb saving vs November no-action", dl["saving_monthly"], D(str(na["energy_cost_monthly"])) - D(str(dl["energy_cost_monthly"])))
    eq("emb 12m", dl["net_12m"], D(str(dl["saving_monthly"])) * 12 - D(str(dl["one_off"])))
    lt("cheapest bill below deadline bill", ch["energy_cost_monthly"], dl["energy_cost_monthly"])
    # N3: the cheapest bill is lower only because it buys less energy; per kWh delivered it is dearer
    lt("deadline cost per kWh below cheapest cost per kWh", D(str(dl["energy_cost_monthly"])) / (D(dl["kwh_2200_2400"]) + D(dl["kwh_0000_0500"])), D(str(ch["energy_cost_monthly"])) / D(ch["kwh_month"]))
    cov = pf["coverage"]
    eq("ev coverage total", cov["cost_total_usd"], actual_total)
    est = sum(D(str(s_["period"]["actual"][k])) for s_ in t["sites"] for k, v in s_["period"]["coverage"].items() if v == "ESTIMATED")
    eq("ev coverage recorded", cov["cost_recorded_usd"], actual_total - est)
    eq("ev coverage share", cov["cost_recorded_share"], (D(str(cov["cost_recorded_usd"])) / actual_total).quantize(D("0.0001")))


def lakeside_options(t: dict) -> None:
    """rev 10: option values, residual costs and the allocation are derived by evaluate_structure.py and compared in derived()."""


def cold_options(t: dict) -> None:
    """rev 10: see derived()."""
    pf = t["portfolio"]["coverage"]
    tot = sum(D(str(s["period"]["actual"][k])) for s in t["sites"] for k in ("energy", "staff", "maint", "liability") if k in s["period"]["actual"])
    eq("cold coverage total", pf["cost_total_usd"], tot)
    est = sum(D(str(s["period"]["actual"][k])) for s in t["sites"] for k, v in s["period"]["coverage"].items() if v == "ESTIMATED")
    eq("cold coverage recorded", pf["cost_recorded_usd"], tot - est)
    eq("cold coverage share", pf["cost_recorded_share"], (D(str(pf["cost_recorded_usd"])) / tot).quantize(D("0.0001")))


def protect(t: dict) -> None:
    """H1 (rev 5): Protect is a declared structure of measured factors; portfolio = sum of sites for numeric measures."""
    pr = t["portfolio"]["protect"]
    for m in pr["measures"]:
        if "sites" in m and isinstance(m.get("portfolio"), (int, float)):
            eq(f"{t['tenant']} protect {m['id']} composition", m["portfolio"], sum(D(str(v)) for v in m["sites"].values()))
        check(f"{t['tenant']} protect {m['id']} has unit, objective, class", all(k in m for k in ("unit", "objective", "class")))
    al = t["portfolio"]["allocation"]
    if "unvalued_spend" in al:
        eq("plan spend = valued option costs + unvalued spend", al["spend"], D(str(al["valued_option_costs"])) + D(str(al["unvalued_spend"])))
        b = al["spend_breakdown"]
        if t["vertical"] == "MINI_GRID":
            eq("valued option costs", al["valued_option_costs"], D(str(b["KOB-STOPSOC"])) + D(str(b["MTO-INV-CLAIM"])) + D(str(b["MTO-HULLER"])))
        m = al.get("modelled_12m_change")
        if m:
            eq(f"{t['tenant']} plan value total", m["total"], sum(D(str(v)) for k, v in m.items() if k not in ("total", "class", "note")))


def operations(t: dict) -> None:
    """LY-1 (rev 6): O2 measures compose as Σ/Σ; downside never above the plan value."""
    pf = t["portfolio"]
    for m in pf["operations"]["measures"]:
        if "numerator_asset_days_available" in m:
            n = sum(D(str(v)) for v in m["numerator_asset_days_available"].values()); d = sum(D(str(v)) for v in m["denominator_asset_days"].values())
            eq("O2 asset availability Σ/Σ", m["portfolio_pct"], (n / d * 100).quantize(D("0.01")))
            out = {k: D(str(m["denominator_asset_days"][k])) - D(str(v)) for k, v in m["numerator_asset_days_available"].items()}
            pm = {x["id"]: x for x in pf["protect"]["measures"]}["asset_days_out_of_service"]
            for k, v in out.items():
                eq(f"O2 availability agrees with Protect asset-days {k}", v, pm["sites"][k])
        if "numerator_kwh_per_night" in m:
            n = sum(D(str(v)) for v in m["numerator_kwh_per_night"].values()); d = sum(D(str(v)) for v in m["denominator_kwh_per_night"].values())
            eq("O2 charger utilisation Σ/Σ", m["portfolio_pct"], (n / d * 100).quantize(D("0.01")))
            for k, v in m["numerator_kwh_per_night"].items():
                eq(f"O2 kWh per night {k}", v, D(str({s_["site"]: s_ for s_ in t["sites"]}[k]["period"]["actual"]["kwh"])) / 31)
        if m["id"] == "crate_days_without_excursion":
            eq("O2 crate-days without excursion", m["portfolio"], sum(D(str(v)) for v in m["sites"].values()))
        if m["id"] == "delivered_kwh_per_field_visit":
            eq("O2 kWh per visit", m["portfolio"], (D(str(pf["chain"]["delivered_kwh"])) / D(3)).quantize(D("0.01")))
        if "binding_limit" in m:
            byname = {s_["site"]: s_ for s_ in t["sites"]}
            for k, d in m["denominator_kwh_per_night"].items():
                ph = byname[k]["physical"]; hours = {"Embakasi": 12, "Kasarani": 7, "Ruiru": 8}[k]
                eq(f"O2 deliverable {k} = min(chargers x kW, import) x window", d, min(D(ph["chargers"]) * D(ph["charger_kw"]), D(ph["import_limit_kw"])) * hours)
            eq("Ruiru deliverable agrees with RUI-ABSORB6", m["denominator_kwh_per_night"]["Ruiru"], {o["id"]: o for o in byname["Ruiru"]["decision"]["options"]}["RUI-ABSORB6"]["deliverable_kwh"])
    al = pf["allocation"]
    if "downside" in al and "modelled_12m_change" in al:
        le("downside <= plan value", al["downside"]["value"], al["modelled_12m_change"]["total"])


def protect_effects(t: dict) -> None:
    """CP-2 / rev 10: each declared per-option Protect effect states horizon, measure and class; its values are compared with the
    evaluator's Protect nodes in derived()."""
    for e in t["portfolio"].get("protect_effects", []):
        check(f"{e['decision']}: horizon, measure, class declared", all(k in e for k in ("horizon", "measure", "class", "options")))


AS_OF = "2026-11-06"


def spikes(doc: dict, path: str) -> None:
    """R8-L2 (rev 9): the replay-derived set used on screen equals the spike enumeration plus the plan values."""
    import json, re, subprocess, pathlib
    tool = pathlib.Path(path).resolve().parent / "interactive-mockup-vNEXT" / "tools" / "replay_values.py"
    if not tool.exists():
        failures.append("replay_values.py missing"); return
    derived = json.loads(subprocess.run([sys.executable, str(tool)], capture_output=True, text=True, check=True).stdout)["figures"]
    def norm(x):
        x = str(x).replace("$", "")
        m = re.fullmatch(r"[\d,]+(\.\d+)?", x)
        return str(float(x.replace(",", ""))) if m else re.sub(r"\s*\(.*\)$", "", x).replace("departures_missed", "departures missed")
    cs = doc["calibration_spikes"]
    listed = {norm(f) for k in ("K", "M", "E") for f in cs[k]["scanned"]} | {norm(f) for f in cs["plan_values"]}
    got = {norm(f) for f in derived}
    check(f"derived replay set == spike enumeration + plan values (missing on screen: {sorted(listed - got)}; not enumerated: {sorted(got - listed)})", listed == got)


def derived(doc: dict, path: str) -> None:
    """Owner, ninth to eleventh messages (rev 10): every figure stated in the manifest must equal the value evaluate_structure.py
    derives by evaluating the declared structures all the way down: value-chain stages, physical splits, cost to serve and outcome
    for every site (actual and plan), every option's value, residual cost and Protect effect, every plan, switch case and downside,
    and the O2 measures. The evaluator is the source; stated figures are the illustration's expected values."""
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location("ev", pathlib.Path(path).resolve().parent / "evaluate_structure.py")
    evm = importlib.util.module_from_spec(spec); spec.loader.exec_module(evm)
    dv = evm.main(path)
    global EVS
    EVS = doc["evaluation"]
    NODE_OF = {"billed_kwh": "billed_kwh", "metered_kwh": "metered_kwh", "revenue": "revenue", "collected": "collected", "diesel_l": "diesel_l",
               "diesel_cost": "fuel_cost", "kwh": "kwh", "energy": "energy", "contribution": "contribution", "energy_cost": "energy_cost",
               "total": "cost_to_serve", "departures_required": "departures_required", "departures_met": "departures_met"}
    for t in doc["tenants"]:
        tid = t["tenant"]
        for s_ in t["sites"]:
            for k in ("plan", "actual"):
                r, ev_ = s_["period"][k], dv["sites"][f"{tid}/{s_['site']}"][k]
                if ev_["status"] != "evaluated":
                    check(f"{tid}/{s_['site']} {k}: labelled not decomposed", ev_["status"].startswith("not decomposed"))
                    continue
                for field, node in NODE_OF.items():
                    if field in r and node in ev_["nodes"]:
                        eq(f"evaluated {tid}/{s_['site']} {k} {field}", ev_["nodes"][node], r[field])
        rows = {o["id"]: o for s_ in t["sites"] for blk in ("decision", "entitlement") for o in (s_.get(blk) or {}).get("options", [])}
        for s_ in t["sites"]:
            for e in s_.get("entitlements", []):
                for o in e.get("options", []):
                    rows[o["id"]] = o
        for oid, e in dv["options"].items():
            if oid not in rows:
                continue
            row, econ = rows[oid], rows[oid].get("economics", {})
            if e["value"] is not None:
                for key in ("net_12m", "net_contract"):
                    if key in econ:
                        eq(f"evaluated {oid} value", e["value"], econ[key])
                if "net_12m" in row:
                    eq(f"evaluated {oid} value", e["value"], row["net_12m"])
            for key in ("net_monthly", "monthly", "saving_monthly"):
                if key in econ:
                    eq(f"evaluated {oid} monthly change", e["monthly_or_horizon_change"], econ[key])
            if "energy_cost_monthly" in econ and "energy_bill_option" in e:
                eq(f"evaluated {oid} monthly bill", e["energy_bill_option"], econ["energy_cost_monthly"])
            if "residual_cost" in row and EVS["options"][oid].get("is_reference"):
                eq(f"evaluated {oid} operator one-off (reference path)", e["operator_one_off"], row["residual_cost"])
            elif "residual_cost" in row:   # operator-borne cost of the path: one-off lines it bears + any operating cost it adds
                eq(f"evaluated {oid} operator cost", D(str(e["operator_one_off"])) + max(-D(str(e["monthly_or_horizon_change"])) * D(str(e["months"])), D(0)), row["residual_cost"])
            if "restore_by" in row and e["restore_date"]:
                check(f"{oid} restore date derived from its drivers equals the stated date", e["restore_date"] == row["restore_by"])
            if "restore_date" in row and e["restore_date"]:
                check(f"{oid} restore date derived from its drivers equals the stated date", e["restore_date"] == row["restore_date"])
            for sk, sv in (row.get("sensitivity") or {}).items():
                key = {"diesel_minus_20pct_net_12m": "diesel_minus_20pct", "feasible_fuel_160l_net_12m": "feasible_fuel_160l"}.get(sk)
                if key:
                    eq(f"evaluated {oid} sensitivity {key}", e["sensitivities"][key], sv)
            if "buses_short" in row:
                eq(f"evaluated {oid} buses short per night", e["bound"]["buses_short_per_night"], row["buses_short"])
            if "deliverable_kwh" in row and "bound" in e and oid.startswith("RUI"):
                eq(f"evaluated {oid} deliverable a night", e["bound"]["deliverable_kwh_night"], row["deliverable_kwh"])
            if "expected_penalties" in row:
                eq(f"evaluated {oid} penalties", -e["monthly_or_horizon_change"] if e["value"] is None else 0, row["expected_penalties"])
        for pe in t["portfolio"].get("protect_effects", []):
            for o, v in pe["options"].items():
                if o in dv["options"] and dv["options"][o]["protect"]:
                    got = dv["options"][o]["protect"].get(pe["measure"])
                    if got is None:   # shown on a bound's own quantity from a calibration spike (design value): must be flagged
                        check(f"{pe['decision']} {o}: non-structure Protect value is a flagged design value or a record count", bool(pe.get("design_value")) or pe.get("class") == "RECORDED")
                    elif isinstance(v, (int, float)):
                        eq(f"evaluated Protect effect {pe['decision']} {o}", got, v)
            if "penalties" in pe:
                for o, v in pe["penalties"].items():
                    if o in dv["options"] and dv["options"][o]["value"] is not None:
                        eq(f"evaluated penalties avoided {o}", dv["options"][o]["monthly_or_horizon_change"], pe["penalties"]["KAS-OEM-WAIT"] - v)
        if tid in dv["plans"]:
            pl, al = dv["plans"][tid], t["portfolio"]["allocation"]
            eq(f"evaluated {tid} plan spend", pl["default"]["spend"], al["spend"])
            if "modelled_12m_change" in al:
                eq(f"evaluated {tid} plan value", pl["default"]["value"], al["modelled_12m_change"]["total"])
                for o, v in al["modelled_12m_change"].items():
                    if o in dv["options"]:
                        eq(f"evaluated {tid} plan item {o}", dv["options"][o]["value"], v)
            if "valued_option_costs" in al:
                eq(f"evaluated {tid} valued option costs", pl["default"]["valued_option_costs"], al["valued_option_costs"])
                eq(f"evaluated {tid} not valued in money", pl["default"]["not_valued_in_money"], al["unvalued_spend"])
            if "spend_breakdown" in al:
                for o, v in al["spend_breakdown"].items():
                    if o in dv["options"]:
                        eq(f"evaluated {tid} spend line {o}", dv["options"][o]["operator_one_off"], v)
            if "downside" in al:
                eq(f"evaluated {tid} downside", pl["downside"], al["downside"]["value"])
                for k, v in (al["downside"].get("others") or {}).items():
                    eq(f"evaluated {tid} sensitivity {k}", (pl["sensitivity_values"].get(k) or {}).get("value"), v)
            for sw in al.get("switches", []):
                for case, c in (sw.get("cases") or {}).items():
                    b, l = case.split("/")
                    got = pl["switch_cases"][f"{b}/{'True' if l == 'yes' else 'False'}"]
                    eq(f"evaluated {tid} case {case} spend", got["spend"], c["spend"])
                    eq(f"evaluated {tid} case {case} value", got["value"], c["value"])
        pc, ch = dv["portfolio"][tid]["actual"]["sums"], t["portfolio"].get("chain", {})
        for field, node in {"metered_kwh": "metered_kwh", "billed_kwh": "billed_kwh", "revenue": "revenue", "collected": "collected",
                            "cost_to_serve": "cost_to_serve", "departures_met": "departures_met"}.items():
            if field in ch and node in pc:
                eq(f"evaluated portfolio composition {tid} {field}", pc[node], ch[field])
        for key, node in (("actual_contribution", "contribution"), ("actual_cost", "cost_to_serve")):
            if key in t["portfolio"] and node in pc:
                eq(f"evaluated portfolio composition {tid} {key}", pc[node], t["portfolio"][key])
        if "cost_per_departure_actual" in t["portfolio"]:
            eq(f"evaluated portfolio composition {tid} cost per departure", pc["cost_per_departure_met"], t["portfolio"]["cost_per_departure_actual"])
        for mid, m in dv["operations"].get(tid, {}).items():
            st = {x["id"]: x for x in t["portfolio"]["operations"]["measures"]}[mid]
            eq(f"evaluated O2 {tid} {mid} portfolio %", m["portfolio_pct"], st["portfolio_pct"])
            for k in ("numerator_asset_days_available", "numerator_kwh_per_night"):
                if k in st:
                    for s, v in st[k].items():
                        eq(f"evaluated O2 {tid} {mid} numerator {s}", m["numerator"][s], v)
            for k in ("denominator_asset_days", "denominator_kwh_per_night"):
                if k in st:
                    for s, v in st[k].items():
                        eq(f"evaluated O2 {tid} {mid} denominator {s}", m["denominator"][s], v)


SUPERSEDED = ["6,096", "6096", "2,556", "3,546", "5,670", "5,346", "3,880", "2,680", "360.00", "−360", "$360,", "$360 ", "98.51", "41.50%"]


def documents(doc: dict, path: str) -> None:
    """R9-M4 (rev 10): the documents are checked too. (1) No superseded figure appears in any pack document (review history and
    the mock-up's revision log excepted). (2) Every money or quantity figure in the main document's figure-bearing sections
    (§2 to §10) is either an evaluated value (derived-values.json) or a declared input in the manifest."""
    import json, pathlib, re
    root = pathlib.Path(path).resolve().parent
    skip = {"REVIEW.md", "REVIEW-response.md", "CHANGE-REGISTER.md", "browser-audit.md"}
    files = [f for f in list(root.glob("*.md")) + list(root.glob("*.csv")) + list((root / "interactive-mockup-vNEXT").glob("*.md")) if f.name not in skip]
    for f in files:
        txt = f.read_text(encoding="utf-8")
        for fig in SUPERSEDED:
            n = len(re.findall(r"(?<![\d,.])" + re.escape(fig) + r"(?![\d])", txt))
            check(f"superseded figure {fig!r} absent from {f.name} (found {n})", n == 0)
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
    walk({k: v for k, v in doc.items() if k != "oracle"})
    walk(json.loads((root / "derived-values.json").read_text(encoding="utf-8")))
    main_doc = (root / "layer4-transformation-design.md").read_text(encoding="utf-8")
    body = main_doc[main_doc.index("## 2. The five mechanics"):main_doc.index("## 11.")]
    body = re.sub(r"`[^`]*`", "", body)
    bad = []
    for m in re.finditer(r"(?<![\w.:/§-])(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+\.\d{2})(?![\d%]| px)", body):
        v = round(float(m.group(1).replace(",", "")), 2)
        if v not in allowed:
            bad.append(m.group(1))
    check(f"main document §2-§10 figures are evaluated values or declared inputs (untraced: {sorted(set(bad))})", not bad)


def main(path: str) -> int:
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    derived(doc, path)
    documents(doc, path)
    global AS_OF
    AS_OF = doc["as_of"]
    spikes(doc, path)
    for t in doc["tenants"]:
        {"MINI_GRID": mini, "COLD_CHAIN": cold, "EV_DEPOT": ev}[t["vertical"]](t)
        {"MINI_GRID": lakeside_options, "COLD_CHAIN": cold_options, "EV_DEPOT": lambda _t: None}[t["vertical"]](t)
        protect(t)
        operations(t)
        protect_effects(t)
    print(f"{passes} checks passed, {len(failures)} failed")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "demo-site-scenario-manifest.yaml"))
