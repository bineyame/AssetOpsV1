"""Arithmetic checks for demo-site-scenario-manifest.yaml (Layer 4 design pack).

Design-pack tool, not product code. Every illustrative figure in the Layer 4 artifacts comes from the manifest;
this script proves the manifest reconciles to the cent. Run:  python3 check_manifest.py demo-site-scenario-manifest.yaml
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
        if "collected" in a:
            eq(f"{n} cash chain", D(str(a["collected"])) + D(str(a["in_transit"])) + D(str(a["outstanding"])), a["revenue"])
        eq(f"{n} variance", p["variance"], D(str(a["contribution"])) - D(str(p["plan"]["contribution"])))
        eq(f"{n} bridge", sum(D(str(b["amount"])) for b in p["bridge"]), p["variance"])
        total_var += D(str(p["variance"]))
    eq("mini portfolio variance", t["portfolio"]["variance"], total_var)
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
    al = t["portfolio"]["allocation"]
    eq("cold spend", al["spend"], sum(D(str(v)) for v in al["spend_breakdown"].values()))
    le("cold budget", al["spend"], t["portfolio_constraints"]["budget_usd_nov_dec"])


def ev(t: dict) -> None:
    plan_total, actual_total = D(0), D(0)
    for s in t["sites"]:
        n, p = s["site"], s["period"]
        a = p["actual"]
        if "demand_cost" in a:
            for k in ("plan", "actual"):
                r = p[k]
                if "demand_cost" in r:
                    eq(f"{n} {k} cost parts", r["energy_cost"], D(str(r["peak_cost"])) + D(str(r["offpeak_cost"])) + D(str(r["demand_cost"])))
            eq(f"{n} variance", p["variance"], D(str(p["plan"]["energy_cost"])) - D(str(a["energy_cost"])))
            plan_total += D(str(p["plan"]["energy_cost"])); actual_total += D(str(a["energy_cost"]))
            if "bridge" in p:
                eq(f"{n} bridge", sum(D(str(b["amount"])) for b in p["bridge"]), p["variance"])
        else:
            plan_total += D(str(p["plan"]["total"])); actual_total += D(str(a["total"]))
    pf = t["portfolio"]
    eq("ev plan", pf["plan_cost"], plan_total)
    eq("ev actual", pf["actual_cost"], actual_total)
    eq("ev variance", pf["variance"], plan_total - actual_total)
    eq("ev cost per departure", pf["cost_per_departure_actual"], (actual_total / D(pf["departures_met"])).quantize(D("0.01")))
    al = pf["allocation"]
    eq("ev spend", al["spend"], sum(D(str(v)) for v in al["spend_breakdown"].values()))
    le("ev budget", al["spend"], t["portfolio_constraints"]["budget_usd_nov_dec"])


def main(path: str) -> int:
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    for t in doc["tenants"]:
        {"MINI_GRID": mini, "COLD_CHAIN": cold, "EV_DEPOT": ev}[t["vertical"]](t)
    print(f"{passes} checks passed, {len(failures)} failed")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "demo-site-scenario-manifest.yaml"))
