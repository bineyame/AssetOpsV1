"""The committed extract of 0K4d's two v8 replay studies (0K4m spec §2.1; D-0K4.31, D-0K4.34, D-0K4.38).

Design-pack tool, stdlib only. Reads the two study files 0K4d wrote and writes replay-studies.json beside the manifest: each
study's identity, its assumptions (and Kobo's admission rule) verbatim, and exactly the case fields the pack reads. A value
stays the study's {"exact": "<p>/<q>", "reading": "<str>"} pair; an integer, a boolean or a null stays as it is. A field
the study lacks is a KeyError, never a blank. A study file whose sha256 is not the one 0K4d produced is refused (exit 2).

Run:  python3 extract_replay_studies.py --kobo <kobo-61d/study.json> --mto <mto-61d/study.json> [--check]
      --check rewrites nothing, exits 1 on any difference and names the first one.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

OUT = pathlib.Path(__file__).resolve().parent / "replay-studies.json"
# The two study files 0K4d produced (spec header, rev 2 R6), in full.
SHA256 = {"K8": "c52e475554e6d4e2c713b7d8face961426c8d27b991315cb95bb974eccc78b61",
          "M8": "69a7b9bd8964d054c901c70422c637320eccf230b72e738994f0e5a0a5a2707d"}
SOURCE_FILE = {"K8": "kobo-61d/study.json", "M8": "mto-61d/study.json"}
MONTH_BASIS = {"K8": "window figure x 30 / 61",
               "M8": "rates only (litres per customer kWh, litres per day); no window figure is scaled"}
K8_CASES = ("stop-70-reserve-30", "stop-90-reserve-25")
K8_CASE_FIELDS = ("scaled_to_30_days.avoided_l", "scaled_to_30_days.added_throughput_kwh", "scaled_to_30_days.added_starts",
                  "dawn_days_below", "new_dawn_days_below", "worst_dawn_soc_pct", "min_soc_pct", "max_starts_in_a_day",
                  "longest_days_without_full_charge", "admission.admitted", "admission.first_failing_part")
K8_BASELINE_FIELDS = ("dawn_days_below", "worst_dawn_soc_pct", "min_soc_pct", "max_starts_in_a_day",
                      "longest_days_without_full_charge")
M8_DEMAND = ("mto-huller", "mto-welder")
M8_DEMAND_FIELDS = ("litres_per_customer_kwh", "days_without_headroom", "extra_starts", "dawn_days_below")
M8_CAPACITY_FIELDS = ("extra_fuel_l_per_day", "inverter_limit_kw", "extra_generator_kwh", "extra_unserved_kwh")
LENGTH_FIELDS = ("new_dawn_days_below", "days_without_headroom")   # a list of dates: the pack reads its length


def at(tree, dotted):
    cur = tree
    for part in dotted.split("."):
        cur = cur[part]   # KeyError on a field the study lacks
    return cur


def value(tree, dotted):
    v = at(tree, dotted)
    if dotted.split(".")[-1] in LENGTH_FIELDS:
        if not isinstance(v, list):
            raise TypeError(f"{dotted} is not a list")
        return len(v)
    if isinstance(v, dict):
        if set(v) != {"exact", "reading"}:
            raise TypeError(f"{dotted} is not an exact/reading pair: {sorted(v)}")
        return {"exact": v["exact"], "reading": v["reading"]}
    if v is None or isinstance(v, (bool, int, str)):
        return v
    raise TypeError(f"{dotted} has type {type(v).__name__}")


def put(row, dotted, v):
    *head, last = dotted.split(".")
    for part in head:
        row = row.setdefault(part, {})
    row[last] = v


def identity(sid, study, sha):
    out = {"source_file": SOURCE_FILE[sid], "source_sha256": sha}
    for k in ("commit", "model", "season", "season_inputs_digest"):
        out[k] = study[k]
    out["trajectory_digest_site"] = study["trajectory_digests"]["site"]
    for k in ("input_class", "evidence_class", "status", "days"):
        out[k] = study[k]
    out["month_basis"] = MONTH_BASIS[sid]
    out["assumptions"] = list(study["assumptions"])
    return out


def load(sid, path):
    raw = pathlib.Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != SHA256[sid]:
        print(f"REFUSED {path}: sha256 {sha} is not 0K4d's {SHA256[sid]}", file=sys.stderr)
        sys.exit(2)
    return json.loads(raw.decode("utf-8")), sha


def build(kobo_path, mto_path):
    k, ks = load("K8", kobo_path)
    m, ms = load("M8", mto_path)
    K8 = identity("K8", k, ks)
    K8["admission_rule"] = list(k["admission_rule"])
    K8["basis"] = {"fuel_l": value(k, "baseline.fuel_l"), "days": k["days"]}
    cases = {"baseline": {f: value(k["baseline"], f) for f in K8_BASELINE_FIELDS}}
    by_id = {c["case_id"]: c for c in k["cases"]}
    for cid in K8_CASES:
        c = by_id[cid]
        row = {}
        for f in K8_CASE_FIELDS:
            put(row, f, value(c, f))
        row["admission_parts_failed"] = sum(1 for p in c["admission"]["parts"] if p["passed"] is False)
        cases[cid] = row
    K8["cases"] = cases
    M8 = identity("M8", m, ms)
    M8["basis"] = {"fuel_l": value(m, "baseline_fuel_l"), "days": m["days"]}
    dem = {c["case_id"]: c for c in m["demand"]}
    cases = {cid: {f: value(dem[cid], f) for f in M8_DEMAND_FIELDS} for cid in M8_DEMAND}
    if m["capacity"]["case_id"] != "reduced":
        raise KeyError("capacity case is not 'reduced'")
    cases["reduced"] = {f: value(m["capacity"], f) for f in M8_CAPACITY_FIELDS}
    M8["cases"] = cases
    return {"K8": K8, "M8": M8}


def first_difference(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in list(a) + [x for x in b if x not in a]:
            if key not in a or key not in b:
                return f"{path}.{key}: present on one side only"
            d = first_difference(a[key], b[key], f"{path}.{key}")
            if d:
                return d
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_difference(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    return None if (a == b and type(a) is type(b)) else f"{path}: {a!r} != {b!r}"


def main(argv):
    ap = argparse.ArgumentParser(prog="extract_replay_studies.py")
    ap.add_argument("--kobo", required=True)
    ap.add_argument("--mto", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    text = json.dumps(build(args.kobo, args.mto), indent=1, ensure_ascii=False) + "\n"
    if args.check:
        found = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if found == text:
            print(f"replay-studies.json matches the two study files")
            return 0
        try:
            d = first_difference(json.loads(text), json.loads(found)) or "formatting (bytes differ, content equal)"
        except json.JSONDecodeError as e:
            d = f"replay-studies.json does not parse: {e}"
        print(f"REPLAY_EXTRACT_DIFF {d}")
        return 1
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
