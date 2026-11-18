"""SR-8 parity (after D-SR.62/68). Run from host/ with WT=<worktree> and PYTHONPATH incl. scratchpad common.py.
Gates: stored day == one-day all_hours_headroom_kw and missing_hours; all-missing day UNKNOWN one-day / NO_DATA range;
card high >= stored high; rows on == rows off; stored hit <= 2.0 s."""
import json
from decimal import Decimal
from urllib.parse import urlparse, parse_qs
from common import *
def oneday(s, d):
    q = parse_qs(urlparse(d["link"]).query)
    return get(f"/api/sites/{s}/performance/mini/renewable", **{"from": q["from"][0], "to": q["to"][0]})[0].json()
res = []; day_cmp = {}; nodata = {}; allok = True
for s in SITES:
    seen = {}
    for n in (7, 14, 31):
        p = f"/api/sites/{s}/renewable-range"; w = window(n)
        rows(False); r_off, t_off = get(p, **w)
        rows(True); rs = [get(p, **w) for _ in range(3)]
        on = rs[0][0].json()
        eq = mask(r_off.json()) == mask(on) == mask(rs[1][0].json()) == mask(rs[2][0].json())
        hits = [round(x[1], 2) for x in rs[1:]]
        res.append({"case": f"{s}/{n}", "status": rs[0][0].status_code, "rows_on_equals_rows_off": eq, "rows_off_seconds": round(t_off, 2),
                    "stored_first_seconds": round(rs[0][1], 2), "stored_hits_seconds": hits, "stored_hit_le_2s": max(hits) <= 2.0})
        for d in on["days"]: seen[d["local_day"]] = d
    mm = []; n_c = 0; hi_ok = 0; hi_n = 0; excl = []; nd = []
    for day, d in sorted(seen.items()):
        if d["state"] in ("COUNTED", "EXCLUDED"):
            j = oneday(s, d); c = j["cards"]; ah = c.get("all_hours_headroom_kw"); hr = c.get("headroom_kw")
            miss_range = round(d["operating_hours"] - d["covered_hours"], 2); miss_one = j.get("missing_hours")
            decs = [r["decision"] for r in j["rows"]]
            if d["state"] == "EXCLUDED":
                excl.append({"day": day, "stored": [d["low_kw"], d["high_kw"]], "one_day_status": j["status"], "all_hours": ah, "missing_one": miss_one, "missing_range": miss_range, "row_decisions": sorted(set(decs))}); continue
            n_c += 1
            ok = ah is not None and Decimal(str(ah["low"])) == Decimal(d["low_kw"]) and Decimal(str(ah["high"])) == Decimal(d["high_kw"]) \
                and miss_one is not None and Decimal(str(miss_one)) == Decimal(str(miss_range))
            if not ok: mm.append({"day": day, "stored": [d["low_kw"], d["high_kw"]], "all_hours": ah, "missing_one": miss_one, "missing_range": miss_range, "status": j["status"]})
            if hr is not None and ah is not None:
                hi_n += 1; hi_ok += hr["high"] >= Decimal(d["high_kw"]) if isinstance(hr["high"], Decimal) else float(hr["high"]) >= float(d["high_kw"])
            if day in ("2026-10-27", "2026-11-03", "2026-11-10") and s == "KOBO-001":
                day_cmp[day] = {"stored": [d["low_kw"], d["high_kw"]], "one_day_status": j["status"], "all_hours": ah, "missing_hours_one_day": miss_one,
                                "range_uncovered_hours": miss_range, "decisions": {k: decs.count(k) for k in sorted(set(decs))}, "equal": ok}
        elif d["state"] == "NO_DATA":
            j = oneday(s, d)
            nd.append({"day": day, "range_state": d["state"], "one_day_status": j["status"], "one_day_all_hours": j["cards"].get("all_hours_headroom_kw"), "counted": False})
    nodata[s] = {"days": nd, "all_unknown_one_day": all(x["one_day_status"] == "UNKNOWN" for x in nd), "none_counted": True}
    totals = {n: get(f"/api/sites/{s}/renewable-range", **window(n))[0].json()["totals"] for n in (7, 14, 31)}
    day_cmp.setdefault("_" + s, {"counted_days_compared": n_c, "mismatches": mm, "excluded_days": excl, "card_high_ge_stored_high": f"{hi_ok}/{hi_n}", "totals_by_window": totals})
gates = {"stored_day_equals_all_hours_and_missing_hours": all(not v["mismatches"] for k, v in day_cmp.items() if k.startswith("_")),
         "all_missing_day_unknown_one_day_no_data_range": all(v["all_unknown_one_day"] for v in nodata.values()),
         "card_high_ge_stored_high": all(v["card_high_ge_stored_high"].split("/")[0] == v["card_high_ge_stored_high"].split("/")[1] for k, v in day_cmp.items() if k.startswith("_")),
         "rows_on_equals_rows_off": all(r["rows_on_equals_rows_off"] for r in res),
         "stored_hit_le_2s": all(r["stored_hit_le_2s"] for r in res)}
out = {"branch": "task/SR-8-renewable-range", "db": "assetops_polish_vps1_test", "window_end_day": END, "builder_version": "mini-depth-rows-2",
       "results": res, "stored_day_vs_all_hours_headroom_kw": {k[1:]: v for k, v in day_cmp.items() if k.startswith("_")},
       "kobo_finding_days": {k: v for k, v in day_cmp.items() if not k.startswith("_")}, "all_missing_days": nodata, "gates": gates}
print(json.dumps({"gates": gates, "kobo_days": out["kobo_finding_days"], "cmp": out["stored_day_vs_all_hours_headroom_kw"], "timing": [(r["case"], r["stored_first_seconds"], r["stored_hits_seconds"]) for r in res]}, default=str)[:4000])
json.dump(out, open("/tmp/sr8-parity-new.json", "w"), default=str)
