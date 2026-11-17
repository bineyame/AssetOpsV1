"""Checks for the Layer 4 design pack (rev 11).

Design-pack tool, not product code. evaluate_structure.py PRODUCES the illustration's figures from the manifest's inputs; this
checker asserts that everything stated equals what the structure produces, and that the documents agree:

  1. manifest identities that need no constants (bridges sum to variances, sites sum to portfolios, spend = valued + not valued);
  2. derived(): every stated figure in the manifest equals the evaluated one, at every layer (value chain, physical split, cost,
     outcome, Protect and O2 measures for plan, October and November to date; options, rights, restore dates, Protect effects;
     plans, protective choices, switch cases, sensitivities, downside; portfolio composition);
  3. anchors(): every figure in a document tagged <!--fig:path--> equals the evaluated value at that path;
  4. documents(): no superseded figure in any pack document or the manifest's own strings, and every money figure in the main
     document's figure-bearing sections and the walkthroughs is an evaluated value or a declared input;
  5. spikes(): the replay-dependent set shown on screen equals the calibration-spike enumeration plus the plan values.
It holds no prices, tariffs or quantities of its own. Run:  python3 check_manifest.py [manifest]   Exit 0 = all pass.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import subprocess
import sys
from decimal import Decimal as D

import yaml

failures: list[str] = []
passes = 0


def eq(label, a, b):
    global passes
    if a is None or b is None:
        failures.append(f"{label}: {a} != {b}"); return
    if D(str(a)).quantize(D("0.001")) != D(str(b)).quantize(D("0.001")):
        failures.append(f"{label}: {a} != {b}")
    else:
        passes += 1


def check(label, cond):
    global passes
    if cond:
        passes += 1
    else:
        failures.append(label)


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
    al = t["portfolio"]["allocation"]
    if "unvalued_spend" in al:
        eq(f"{t['tenant']} spend = valued option costs + not valued", al["spend"], D(str(al["valued_option_costs"])) + D(str(al["unvalued_spend"])))
    if "modelled_12m_change" in al:
        m = al["modelled_12m_change"]
        eq(f"{t['tenant']} plan value = Σ items", m["total"], sum(D(str(v)) for k, v in m.items() if k not in ("total", "class", "note")))
    if "spend_breakdown" in al:
        eq(f"{t['tenant']} spend = Σ breakdown", al["spend"], sum(D(str(v)) for v in al["spend_breakdown"].values()))


def get(dv, path):
    cur = dv
    for part in re.split(r"\.(?![^\[]*\])", path):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def derived(doc, dv):
    NODE_OF = {"billed_kwh": "billed_kwh", "metered_kwh": "metered_kwh", "revenue": "revenue", "collected": "collected", "diesel_l": "diesel_l",
               "diesel_cost": "fuel_cost", "kwh": "kwh", "energy": "energy", "contribution": "contribution", "energy_cost": "energy_cost",
               "total": "cost_to_serve", "departures_required": "departures_required", "departures_met": "departures_met"}
    EVO = doc["evaluation"]["options"]
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
        # H1: the period's Protect measures equal the observed structure's nodes (October and November to date)
        for m in t["portfolio"]["protect"]["measures"]:
            if "node" not in m:
                continue
            for side, key in (("actual", "sites"), ("november_to_date", "november_to_date")):
                vals = m.get(key) or {}
                for site, v in vals.items():
                    if site in ("portfolio", "detail") or not isinstance(v, (int, float)):
                        continue
                    node = dv["sites"][f"{tid}/{site}"].get(side, {}).get("nodes", {}).get(m["node"])
                    eq(f"evaluated Protect {tid}/{site} {side} {m['id']}", node, v)
        # O2
        for m in t["portfolio"]["operations"]["measures"]:
            ev_ = dv["operations"].get(tid, {}).get(m["id"])
            if ev_ is None:
                check(f"O2 {tid} {m['id']}: evaluated", False); continue
            stated = m.get("portfolio_pct", m.get("portfolio"))
            eq(f"evaluated O2 {tid} {m['id']} portfolio", ev_["portfolio"], stated)
            for s, v in (m.get("sites_pct") or {}).items():
                eq(f"evaluated O2 {tid} {m['id']} {s}", ev_["sites"][s], v)
            if "assets" in m:
                for s, a in m["assets"].items():
                    eq(f"O2 asset list length {s} = declared major assets", len(a), [x for x in t["sites"] if x["site"] == s][0]["observations"]["october"]["major_assets"])
        # options
        rows = {o["id"]: o for s_ in t["sites"] for blk in ("decision", "entitlement") for o in (s_.get(blk) or {}).get("options", [])}
        for s_ in t["sites"]:
            for e in s_.get("entitlements", []):
                rows.update({o["id"]: o for o in e.get("options", [])})
        for oid, row in rows.items():
            e = dv["options"].get(oid)
            if e is None:
                continue
            econ = row.get("economics", {})
            for key in ("net_12m", "net_contract"):
                if key in econ and e["value"] is not None:
                    eq(f"evaluated {oid} value", e["value"], econ[key])
            if "net_12m" in row and e["value"] is not None:
                eq(f"evaluated {oid} value", e["value"], row["net_12m"])
            for key in ("net_monthly", "monthly", "saving_monthly"):
                if key in econ:
                    eq(f"evaluated {oid} monthly change", e["monthly_or_horizon_change"], econ[key])
            if "energy_cost_monthly" in econ and "energy_bill_option" in e:
                eq(f"evaluated {oid} monthly bill", e["energy_bill_option"], econ["energy_cost_monthly"])
            if "residual_cost" in row:
                if EVO.get(oid, {}).get("is_reference"):
                    eq(f"evaluated {oid} operator one-off (reference path)", e["operator_one_off"], row["residual_cost"])
                else:
                    eq(f"evaluated {oid} operator cost", D(str(e["operator_one_off"])) + max(-D(str(e["monthly_or_horizon_change"])) * D(str(e["months"])), D(0)), row["residual_cost"])
            for f in ("restore_by", "restore_date"):
                if f in row and e["restore_date"]:
                    check(f"{oid} restore date from its drivers = stated {row[f]} (got {e['restore_date']})", e["restore_date"] == row[f])
            for sk, sv in (row.get("sensitivity") or {}).items():
                key = {"diesel_minus_20pct_net_12m": "diesel_minus_20pct", "feasible_fuel_160l_net_12m": "feasible_fuel_160l"}.get(sk)
                if key:
                    eq(f"evaluated {oid} sensitivity {key}", (e.get("sensitivities") or {}).get(key), sv)
            if "buses_short" in row:
                eq(f"evaluated {oid} buses short a night", e["bound"]["buses_short_per_night"], row["buses_short"])
            if "deliverable_kwh" in row and oid.startswith("RUI"):
                eq(f"evaluated {oid} deliverable a night", e["bound"]["deliverable_kwh_night"], row["deliverable_kwh"])
            if "avoided_capex" in row:
                eq(f"{oid} avoided purchase = evaluated RUI-4CHARGERS one-off", dv["options"]["RUI-4CHARGERS"]["operator_one_off"], row["avoided_capex"])
            if "expected_penalties" in row:
                eq(f"evaluated {oid} penalties", -D(str(e["monthly_or_horizon_change"])), row["expected_penalties"])
        for pe in t["portfolio"].get("protect_effects", []):
            check(f"{pe['decision']}: horizon, measure, class declared", all(k in pe for k in ("horizon", "measure", "class", "options")))
            for o, v in pe["options"].items():
                if o not in dv["options"] or not isinstance(v, (int, float)):
                    continue
                got = dv["options"][o]["protect"].get(pe["measure"])
                if got is None:
                    check(f"{pe['decision']} {o}: shown on a non-structure quantity only as a flagged design value or record count", bool(pe.get("design_value")) or pe.get("class") == "RECORDED")
                else:
                    eq(f"evaluated Protect effect {pe['decision']} {o}", got, v)
        # plans
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
            for o, v in (al.get("spend_breakdown") or {}).items():
                if o in dv["options"]:
                    eq(f"evaluated {tid} spend line {o}", dv["options"][o]["operator_one_off"], v)
            rec = set(al.get("recommended", []))
            for o in pl["default"]["items"]:
                check(f"{tid}: evaluated plan item {o} is in the stated recommended set", o in rec)
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
        # portfolio composition
        pc, ch = dv["portfolio"][tid]["actual"]["sums"], t["portfolio"].get("chain", {})
        for field in ("metered_kwh", "billed_kwh", "revenue", "collected", "cost_to_serve", "departures_met"):
            if field in ch and field in pc:
                eq(f"evaluated portfolio composition {tid} {field}", pc[field], ch[field])
        for key, node in (("actual_contribution", "contribution"), ("actual_cost", "cost_to_serve")):
            if key in t["portfolio"] and node in pc:
                eq(f"evaluated portfolio composition {tid} {key}", pc[node], t["portfolio"][key])
        if "cost_per_departure_actual" in t["portfolio"]:
            eq(f"evaluated portfolio composition {tid} cost per departure", pc["cost_per_departure_met"], t["portfolio"]["cost_per_departure_actual"])
    # oracle statements that quote plan figures (L1)
    for o in doc.get("oracle", []):
        if o["id"] == "OR-ALLOC-1":
            sp = dv["plans"]["lakeside-power"]["default"]["spend"]
            check(f"oracle OR-ALLOC-1 quotes the evaluated spend {sp}", sp is not None and f"{sp:,.0f}" in o["expect"])
    for tid, pl in dv["plans"].items():
        for name, pc in pl["protective_choices"].items():
            check(f"{tid} protective decision {name} is met ({pc['how']})", pc["chosen"] is not None)


def anchors(root, dv):
    files = [root / f for f in ("layer4-transformation-design.md", "economic-metric-and-effect-contracts.md", "domain-and-decision-models.md",
                                "phase-plan-and-acceptance.md", "integration-source-to-canonical-design.md", "demo-build-cost-plan.md")] + [root / "interactive-mockup-vNEXT" / "walkthroughs.md"]
    n = 0
    for f in files:
        txt = f.read_text(encoding="utf-8")
        for m in re.finditer(r"([\d,]+(?:\.\d+)?)<!--fig:([^>]+)-->", txt):
            n += 1
            val = get(dv, m.group(2))
            eq(f"anchored figure in {f.name}: {m.group(1)} = {m.group(2)}", abs(D(m.group(1).replace(',', ''))), abs(D(str(val))) if val is not None else None)
    check(f"documents carry figure anchors ({n})", n > 50)


SUPERSEDED = ["6,096", "6096", "2,556", "3,546", "5,670", "5,346", "3,880", "2,680", "360.00", "−360", "$360,", "$360 ", "98.51", "41.50%"]


def documents(root, doc, dv):
    skip = {"REVIEW.md", "REVIEW-response.md", "CHANGE-REGISTER.md", "browser-audit.md"}
    files = [f for f in list(root.glob("*.md")) + list(root.glob("*.csv")) + list((root / "interactive-mockup-vNEXT").glob("*.md")) if f.name not in skip]
    manifest_strings = json.dumps({k: v for k, v in doc.items() if k != "oracle"}, ensure_ascii=False)
    for name, txt in [(f.name, f.read_text(encoding="utf-8")) for f in files] + [("manifest strings", manifest_strings)]:
        for fig in SUPERSEDED:
            k = len(re.findall(r"(?<![\d,.])" + re.escape(fig) + r"(?![\d])", txt))
            check(f"superseded figure {fig!r} absent from {name} (found {k})", k == 0)
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
    walk({k: v for k, v in doc.items() if k != "oracle"}); walk(dv)
    main_doc = (root / "layer4-transformation-design.md").read_text(encoding="utf-8")
    sections = [("main §2-§10", main_doc[main_doc.index("## 2. The five mechanics"):main_doc.index("## 11.")]),
                ("walkthroughs", (root / "interactive-mockup-vNEXT" / "walkthroughs.md").read_text(encoding="utf-8"))]
    for name, body in sections:
        body = re.sub(r"`[^`]*`|<!--[^>]*-->", "", body)
        bad = [m.group(1) for m in re.finditer(r"(?<![\w.:/§-])(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+\.\d{2})(?![\d%]| px)", body)
               if round(float(m.group(1).replace(",", "")), 2) not in allowed]
        check(f"{name}: figures are evaluated values or declared inputs (untraced: {sorted(set(bad))})", not bad)


def spikes(root, doc):
    tool = root / "interactive-mockup-vNEXT" / "tools" / "replay_values.py"
    derived_set = json.loads(subprocess.run([sys.executable, str(tool)], capture_output=True, text=True, check=True).stdout)["figures"]

    def norm(x):
        x = str(x).replace("$", "")
        return str(float(x.replace(",", ""))) if re.fullmatch(r"[\d,]+(\.\d+)?", x) else re.sub(r"\s*\(.*\)$", "", x).replace("departures_missed", "departures missed")
    cs = doc["calibration_spikes"]
    listed = {norm(f) for k in ("K", "M", "E") for f in cs[k]["scanned"]} | {norm(f) for f in cs["plan_values"]}
    got = {norm(f) for f in derived_set}
    check(f"replay set on screen == spike enumeration + plan values (missing: {sorted(listed - got)}; not enumerated: {sorted(got - listed)})", listed == got)


def main(path):
    root = pathlib.Path(path).resolve().parent
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("ev", root / "evaluate_structure.py")
    evm = importlib.util.module_from_spec(spec); spec.loader.exec_module(evm)
    dv = evm.main(path)
    for t in doc["tenants"]:
        identities(t)
    derived(doc, dv)
    anchors(root, dv)
    documents(root, doc, dv)
    spikes(root, doc)
    print(f"{passes} checks passed, {len(failures)} failed")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent / "demo-site-scenario-manifest.yaml")))
