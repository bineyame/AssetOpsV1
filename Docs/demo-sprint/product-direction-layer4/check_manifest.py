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
    kob, kis, mto = t["sites"]
    ko = {x["id"]: x for x in kob["decision"]["options"]}
    e = ko["KOB-STOPSOC"]["economics"]
    eq("stopsoc gross", e["gross_monthly"], D(ko["KOB-STOPSOC"]["forward_replay"]["avoidable_fuel_l"]) * D("1.25"))
    eq("stopsoc wear", e["wear_monthly"], D(ko["KOB-STOPSOC"]["forward_replay"]["added_battery_throughput_kwh"]) * D("0.08"))
    eq("stopsoc net", e["net_monthly"], D(str(e["gross_monthly"])) - D(str(e["wear_monthly"])))
    eq("stopsoc 12m", e["net_12m"], D(str(e["net_monthly"])) * 12 - D(str(e["one_off"])))
    mo = {x["id"]: x for x in mto["decision"]["options"]}
    h = mo["MTO-HULLER"]["economics"]
    eq("huller kwh", mo["MTO-HULLER"]["load"]["kwh_month"], D(mo["MTO-HULLER"]["load"]["kw"]) * 5 * D(mo["MTO-HULLER"]["load"]["days_per_month"]))
    eq("huller revenue", h["revenue_monthly"], D(mo["MTO-HULLER"]["load"]["kwh_month"]) * D("0.30"))
    eq("huller fuel", h["fuel_monthly"], D(mo["MTO-HULLER"]["forward_replay"]["extra_fuel_l"]) * D("1.25"))
    eq("huller net", h["net_monthly"], D(str(h["revenue_monthly"])) - D(str(h["fuel_monthly"])) - D(str(h["collection_cost_monthly"])))
    eq("huller 12m", h["net_12m"], D(str(h["net_monthly"])) * 12 - D(str(h["one_off"])))
    w = mo["MTO-WELDING"]["economics"]
    eq("welding net", w["net_monthly"], D(str(w["revenue_monthly"])) - D(str(w["fuel_monthly"])))
    b = mo["MTO-BILLING"]["economics"]
    eq("billing 12m", b["charges_12m"], D(str(b["charges_monthly"])) * 12)
    io = {x["id"]: x for x in mto["entitlement"]["options"]}
    eq("inverter claim residual", io["MTO-INV-CLAIM"]["residual_cost"], D(150) + D(80) + D(130))
    eq("inverter buy-now residual", io["MTO-INV-BUYNOW"]["residual_cost"], D(2600) + D(80) + D(150) + D(80))
    # allocation: brute force over the money options under each budget x letter-of-intent case
    must = D(str(kis["decision"]["options"][0]["cost"])) + D(430)   # KIS-REPAIR + BAT-EVIDENCE (no money, protective)
    opts = {"STOPSOC": (D(90), D(str(e["net_12m"]))), "CLAIM": (D(360), D(-360)), "BUYNOW": (D(2910), D(-2910)),
            "HULLER": (D(1200), D(str(h["net_12m"])))}
    import itertools
    def best(budget, loi_extends):
        res = None
        for r in range(len(opts) + 1):
            for c in itertools.combinations(opts, r):
                c = set(c)
                if len(c & {"CLAIM", "BUYNOW"}) != 1:   # the inverter must be restored by exactly one path
                    continue
                if "HULLER" in c and not (("BUYNOW" in c) or loi_extends):
                    continue                            # claim path restores 28 Nov, after the LOI lapses
                cost = must + sum(opts[k][0] for k in c)
                if cost > budget:
                    continue
                val = sum(opts[k][1] for k in c)
                if res is None or val > res[0]:
                    res = (val, cost, c)
        return res
    v, c, sset = best(D(5000), True)
    eq("alloc 5000 LOI-yes value", v, D(str(t["portfolio"]["allocation"]["modelled_12m_change"]["total"])))
    eq("alloc 5000 LOI-yes spend", c, t["portfolio"]["allocation"]["spend"])
    v2, c2, s2 = best(D(5000), False)
    eq("alloc 5000 LOI-no value", v2, D(2556)); check("alloc 5000 LOI-no claim path", "CLAIM" in s2)
    v3, c3, s3 = best(D(6500), True)
    eq("alloc 6500 LOI-yes value (claim still wins)", v3, D(6096)); check("alloc 6500 LOI-yes claim", "CLAIM" in s3)
    v4, c4, s4 = best(D(6500), False)
    eq("alloc 6500 LOI-no value", v4, D(3546)); eq("alloc 6500 LOI-no spend", c4, D(6430)); check("alloc 6500 LOI-no buy-now", "BUYNOW" in s4)


def cold_options(t: dict) -> None:
    by = {s["code"]: s for s in t["sites"]}
    mo = {x["id"]: x for x in by["COLD-MWEA"]["decision"]["options"]}["MWEA-AGG"]["economics"]
    eq("mwea revenue", mo["revenue_monthly"], D(mo["crate_days_month"]) * D("0.18"))
    eq("mwea energy", mo["energy_monthly"], D(mo["crate_days_month"]) * D("0.25") * D("0.20"))
    eq("mwea net", mo["net_monthly"], D(str(mo["revenue_monthly"])) - D(str(mo["energy_monthly"])) - D(str(mo["handling_monthly"])))
    eq("mwea contract", mo["net_contract"], D(str(mo["net_monthly"])) * mo["months"] - D(str(mo["one_off"])))
    ko = {x["id"]: x for x in by["COLD-KIRI"]["decision"]["options"]}
    excess = D(by["COLD-KIRI"]["period"]["actual"]["kwh"]) - D(by["COLD-KIRI"]["period"]["actual"]["kwh_model"])
    r = ko["KIRI-REPAIR"]
    eq("kiri repair monthly", r["economics"]["monthly"], excess * D(str(r["recovery_share"])) * D("0.20"))
    eq("kiri repair 12m", r["economics"]["net_12m"], D(str(r["economics"]["monthly"])) * 12 - D(str(r["cost"])))
    rp = ko["KIRI-REPLACE"]
    eq("kiri replace monthly", rp["economics"]["monthly"], excess * D("0.20") + D(by["COLD-KIRI"]["period"]["actual"]["kwh_model"]) * D("0.05") * D("0.20"))
    eq("kiri replace 12m", rp["economics"]["net_12m"], D(str(rp["economics"]["monthly"])) * 12 - D(str(rp["capex"])))
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
    if t["vertical"] == "MINI_GRID":
        kob, kis, mto = t["sites"]
        h = {o["id"]: o for o in mto["decision"]["options"]}["MTO-HULLER"]
        huller_lo = (D(str(h["economics"]["revenue_monthly"])) - D(h["forward_replay"]["extra_fuel_l"]) * D("1.00") - D(str(h["economics"]["collection_cost_monthly"]))) * 12 - D(str(h["economics"]["one_off"]))
        stop_lo = D(str({o["id"]: o for o in kob["decision"]["options"]}["KOB-STOPSOC"]["sensitivity"]["diesel_minus_20pct_net_12m"]))
        eq("diesel -20% applied to the whole plan", al["downside"]["others"]["diesel_minus_20pct"], stop_lo + huller_lo - D(360))
    if "downside" in al and "modelled_12m_change" in al:
        le("downside <= plan value", al["downside"]["value"], al["modelled_12m_change"]["total"])


def protect_effects(t: dict) -> None:
    """CP-2 (rev 8): per-option Protect effects are declared and reconcile with the options they describe."""
    for e in t["portfolio"].get("protect_effects", []):
        check(f"{e['decision']}: horizon, measure, class declared", all(k in e for k in ("horizon", "measure", "class", "options")))
        if "penalties" in e:
            for o, n in e["options"].items():
                eq(f"{e['decision']} {o} penalties = missed x rate", e["penalties"][o], D(n) * D(str(e["penalty_per_missed_block"])))
        if e["decision"] == "Kisiwa generator 1 failed":
            eq("Kisiwa no action = 30 evenings x 5 h", e["options"]["KIS-NOACT"], 150)
            eq("Kisiwa repair = 3 evenings x 5 h", e["options"]["KIS-REPAIR"], 15)
        if e["decision"] == "Embakasi charging schedule":
            o = {x["id"]: x for x in t["sites"][0]["decision"]["options"]}["EMB-CHEAPEST"]
            eq("Embakasi cheapest missed departures = buses short x 31", e["options"]["EMB-CHEAPEST"], D(o["buses_short"]) * 31)
        if e["decision"] == "Kobo generator stop setting":
            o = {x["id"]: x for x in t["sites"][0]["decision"]["options"]}["KOB-RESERVE"]
            eq("Kobo reserve dawn days agree with the replay", e["options"]["KOB-RESERVE"], o["forward_replay"]["soc_0500_below_35_days"])
    k = [x for x in t["sites"] if x["site"] == "Kasarani"]
    if k:
        w = {o["id"]: o for o in k[0]["entitlement"]["options"]}["KAS-OEM-WAIT"]
        e = [x for x in t["portfolio"]["protect_effects"] if x["decision"].startswith("Kasarani")][0]
        eq("Kasarani wait penalties agree with the option row", e["penalties"]["KAS-OEM-WAIT"], w["expected_penalties"])


def main(path: str) -> int:
    doc = yaml.safe_load(open(path, encoding="utf-8"))
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
