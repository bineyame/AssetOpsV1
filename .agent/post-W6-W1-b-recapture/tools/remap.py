"""Build a filtered, ID-remapped targets file: python remap.py <frozen-targets> <frozen-links-log> <new-links-log> <batch> <out> [port]
UUIDs are mapped positionally (first-appearance order) between the frozen producer links log and this run's log.
Only targets whose (screen, case) are in selection.json for <batch> are kept; host port rewritten to 5186."""
import json, re, sys, pathlib
here = pathlib.Path(__file__).resolve().parents[1]
ft, fl, nl, batch, out = sys.argv[1:6]
port = sys.argv[6] if len(sys.argv) > 6 else "5186"
U = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
def ids(p):
    seen = []
    for m in re.findall(U, open(p, encoding="utf-8").read()):
        if m not in seen: seen.append(m)
    return seen
a, b = ids(fl), ids(nl)
assert len(a) == len(b), (len(a), len(b))
m = dict(zip(a, b))
sel = {(p["screen"], p["case"]) for p in json.load(open(here / "selection.json"))["pairs"] if p["batch"] == int(batch)}
res = []
for t in json.load(open(ft, encoding="utf-8")):
    if (t["id"], t["case"]) not in sel: continue
    url = re.sub(U, lambda x: m.get(x.group(0), x.group(0)), t["url"])
    url = re.sub(r"localhost:\d+", f"localhost:{port}", url)
    res.append(dict(t, url=url))
json.dump(res, open(out, "w"), indent=1)
print(len(res), "targets;", len(m), "ids mapped")
