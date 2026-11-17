"""Checks for the Layer 4 design pack (rev 12).

Design-pack tool, not product code. evaluate_structure.py PRODUCES the illustration's figures from the manifest's inputs; this
checker asserts that everything stated equals what the structure produces, and that the documents agree:

  1. manifest identities that need no constants (bridges sum to variances, sites sum to portfolios, spend = valued + not valued);
  2. derived(): every stated figure in the manifest equals the evaluated one, at every layer (value chain, physical split, cost,
     outcome, Protect and O2 measures for plan, October and November to date; options, rights, restore dates, Protect effects;
     plans, protective choices, switch cases, sensitivities, downside; portfolio composition);
  3. anchors(): every figure in a document tagged <!--fig:path--> equals the evaluated value at that path, SIGNED (the sign written
     before the figure is part of it; <!--fig:-path--> marks a figure written as the negative of the path, e.g. a cost subtracted);
     a figure stated for a period to date may not be anchored to an option's horizon path; the headline figures listed in
     REQUIRED must be anchored in each document named; and every occurrence of an evaluated plan or option money figure in the
     figure-bearing documents must carry an anchor (an unanchored copy could drift unseen);
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
            used = al.get("crew_visits_used", al.get("technician_visits_used"))
            if used is not None:
                eq(f"evaluated {tid} crew visits used", pl["default"]["crew_visits_used"], used)
            for o in pl["default"]["items"]:
                check(f"{tid}: plan item {o} declares its crew visits", dv["options"][o]["crew_visits"] is not None)
            # L7: row dispositions agree with the evaluation (no hand disposition contradicts it)
            items_any = {o for c in pl["switch_cases"].values() for o in (c["items"] or [])}
            for o in {o for d in doc["plans"][tid]["decisions"] for o in d["options"]}:
                disp = (rows.get(o) or {}).get("disposition")
                if dv["options"][o].get("decision") and next(d for d in doc["plans"][tid]["decisions"] if o in d["options"])["kind"] == "comparator":
                    check(f"{tid}: comparator {o} {disp}: RECOMMENDED only if admissible", disp != "RECOMMENDED" or dv["options"][o]["admissible"])
                elif disp == "RECOMMENDED":
                    check(f"{tid}: {o} RECOMMENDED is in the evaluated plan", o in pl["default"]["items"])
                elif disp == "CONDITIONAL":
                    check(f"{tid}: {o} CONDITIONAL is in some evaluated case and not the default", o in items_any and o not in pl["default"]["items"])
                elif disp in ("REJECTED", "DEFERRED", "ACCEPTABLE"):
                    check(f"{tid}: {o} {disp} is not in the evaluated plan", o not in pl["default"]["items"])
                    if disp == "ACCEPTABLE":
                        check(f"{tid}: {o} ACCEPTABLE is admissible under its decision's bounds", dv["options"][o]["admissible"])
            for sw in al.get("switches", []):
                for case, c in (sw.get("cases") or {}).items():
                    b, l = case.split("/")
                    got = pl["switch_cases"].get(f"{b}/{'True' if l == 'yes' else 'False'}")
                    if got is None:
                        check(f"evaluated {tid} case {case} exists", False); continue
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
    # L6: records consistent with the structure: energy delivered a night never exceeds what the structure says was deliverable
    for key, site in dv["sites"].items():
        for side, ev_ in site.items():
            nd = ev_.get("nodes") or {}
            if "scheduled_kwh_night" in nd:
                check(f"{key} {side}: recorded kWh a night {nd['scheduled_kwh_night']} <= deliverable {nd['deliverable_kwh_night']}",
                      D(str(nd["scheduled_kwh_night"])) <= D(str(nd["deliverable_kwh_night"])))
    for t in doc["tenants"]:   # computed record fields carry their factors and are checked (no typed product)
        for s_ in t["sites"]:
            for b in (s_.get("incident") or {}).get("batches", []):
                if "exposed_value" in b:
                    eq(f"{s_['site']} {b['batch']} exposed value = crates x declared value per crate", b["exposed_value"], D(str(b["crates"])) * D(str(b["declared_value_per_crate"])))
    # oracle statements that quote plan figures (L1)
    for o in doc.get("oracle", []):
        if o["id"] == "OR-ALLOC-1":
            sp = dv["plans"]["lakeside-power"]["default"]["spend"]
            check(f"oracle OR-ALLOC-1 quotes the evaluated spend {sp}", sp is not None and f"{sp:,.0f}" in o["expect"])
    for tid, pl in dv["plans"].items():
        for name, pc in pl["protective_choices"].items():
            check(f"{tid} protective decision {name} is met ({pc['how']})", pc["chosen"] is not None)


FIG_DOCS = ("layer4-transformation-design.md", "economic-metric-and-effect-contracts.md", "domain-and-decision-models.md",
            "phase-plan-and-acceptance.md", "integration-source-to-canonical-design.md", "demo-build-cost-plan.md", "interactive-mockup-vNEXT/walkthroughs.md",
            "design-questions-and-decisions.md")
# headline figures that must be anchored in the named documents (M4): plan spend, value and crew visits for every tenant, and the
# period's Protect statement in main §10
REQUIRED = {"layer4-transformation-design.md": [f"plans.{t}.default.{k}" for t in ("lakeside-power", "harvest-cold", "metro-bus")
                                                for k in ("spend", "value", "crew_visits_used")] +
            ["sites.lakeside-power/Kisiwa.actual.nodes.obligation_hours_without_redundancy", "sites.lakeside-power/Mto.actual.nodes.obligation_hours_without_redundancy",
             "sites.harvest-cold/Room B · Thika.actual.nodes.nights_without_backup_cover", "sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed",
             "sites.metro-bus/Kasarani.november_to_date.nodes.penalties"],
            "interactive-mockup-vNEXT/walkthroughs.md": [f"plans.{t}.default.{k}" for t in ("lakeside-power", "harvest-cold", "metro-bus") for k in ("spend", "value")] +
            ["sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed", "sites.metro-bus/Kasarani.november_to_date.nodes.penalties"]}
ANCHOR = re.compile(r"(?:(?<=[\s(=:*$|/,;])|^)((?:−|\+|-(?=\d))\s?)?\$?([\d,]*\d(?:\.\d+)?)(\**)<!--fig:(-?)([^>]+)-->", re.M)


def key_figures(dv):
    """Evaluated money figures of plans and options (abs >= 50): every written occurrence must be anchored."""
    ks = set()
    for pl in dv["plans"].values():
        for blk in [pl["default"], *pl["switch_cases"].values()]:
            for k in ("value", "spend", "valued_option_costs", "not_valued_in_money"):
                if blk.get(k) is not None: ks.add(abs(D(str(blk[k]))))
        for v in pl["sensitivity_values"].values():
            if v["value"] is not None: ks.add(abs(D(str(v["value"]))))
    for o in dv["options"].values():
        for k in ("value_if_admissible", "operator_one_off", "net_one_off"):
            if o.get(k) is not None: ks.add(abs(D(str(o[k]))))
        for v in (o.get("sensitivities") or {}).values():
            if v is not None: ks.add(abs(D(str(v))))
    return {k.quantize(D("0.01")) for k in ks if k >= 50}


RECORDS: set = set()
n_rec = [0]


def anchors(root, dv):
    n = 0
    keys = key_figures(dv)
    for fn in FIG_DOCS:
        txt = (root / fn).read_text(encoding="utf-8")
        found = set()
        for m in ANCHOR.finditer(txt):
            n += 1
            sign = -1 if (m.group(1) or "").strip() in ("−", "-") else 1
            neg, path = m.group(4) == "-", m.group(5)
            found.add(path)
            val = get(dv, path)
            if val is None or isinstance(val, (dict, list, str)):
                check(f"anchored figure in {fn}: {m.group(2)} -> {path} resolves to a number", False); continue
            want = -D(str(val)) if neg else D(str(val))
            eq(f"anchored figure in {fn}: {(m.group(1) or '').strip()}{m.group(2)} = {'-' if neg else ''}{path} (signed)", sign * D(m.group(2).replace(",", "")), want)
            window = txt[max(0, m.start() - 90):m.start()].lower()
            if path.startswith("options.") and ("to date" in window or "so far" in window):
                check(f"anchored figure in {fn}: {m.group(2)} stated for a period to date is anchored to an option's horizon path {path}", False)
        for path in REQUIRED.get(fn, []):
            check(f"{fn}: headline figure {path} is anchored", path in found)
        # every occurrence of an evaluated plan/option money figure carries an anchor
        body = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), txt)
        loose = []
        for m in re.finditer(r"([\d,]*\d(?:\.\d+)?)\**<!--rec-->", txt):   # record figures: must be values recorded in the manifest
            n_rec[0] += 1
            check(f"{fn}: record-tagged figure {m.group(1)} is a manifest record value", round(abs(float(m.group(1).replace(",", ""))), 2) in RECORDS)
        for m in re.finditer(r"(?<![\w.,])(\d{1,3}(?:,\d{3})*\.\d{2})(?![\d])(?!\**<!--(?:fig:|rec-->))", body):
            v = D(m.group(1).replace(",", ""))
            if v in keys:
                loose.append(m.group(1))
        check(f"{fn}: every evaluated plan/option money figure is anchored (unanchored: {sorted(set(loose))[:12]}{' ...' if len(set(loose)) > 12 else ''} x{len(loose)})", not loose)
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
                ("walkthroughs", (root / "interactive-mockup-vNEXT" / "walkthroughs.md").read_text(encoding="utf-8"))]   # the other documents carry worked arithmetic; their evaluated figures are covered by the anchor rule
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

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k not in ("oracle", "evaluation", "plans", "calibration_spikes"): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, float):   # money records are written with cents (floats); counts and days are integers
            RECORDS.add(round(abs(o), 2))
    walk(doc)
    anchors(root, dv)
    documents(root, doc, dv)
    spikes(root, doc)
    print(f"{passes} checks passed, {len(failures)} failed")
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent / "demo-site-scenario-manifest.yaml")))
