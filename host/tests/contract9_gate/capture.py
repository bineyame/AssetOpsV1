"""Capture the contract-9 merge-gate baseline (T025a criterion 10).

The gate's fixtures are GENERATED stand-ins, never copies of owner data
(owner decision 2026-09-29). This script builds them from the shipped
templates and scenarios through the product's own setup and Lab execution,
and records what that code produced: the Drafts (`runs/`), the expected
identities, digests and counts (`expected.json`), the rendered execution
artifacts (`pre-change-artifacts/`), and the stored artifacts and their
status (`stored-executions/`, `stored_expected.json`).

It must run on the code BEFORE any T025a change (commit 96618d9, in a
temporary worktree), from that worktree's `host/`, with
`gate.py` beside it:

    python tests/contract9_gate/capture.py [output-dir]

Nothing is read from or written to `var/`. Rerunning it on changed code would
overwrite the baseline with the change's own behaviour, which is the one thing
it must never do.
"""
import copy, json, shutil, sys, tempfile
from dataclasses import replace
from pathlib import Path
HERE = Path(__file__).resolve().parent
HOST = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HOST), str(HOST / "tests"), str(HOST.parent/"backend"), str(HOST.parent/"simulator"/"assetops_simulator"/".."), str(HOST.parent/"contracts")]
import assetops_backend, assetops_simulator
print(assetops_backend.__file__, assetops_simulator.__file__)
from assetops_backend.runs.adapters.yaml_run_documents import read_run_record, serialize_run_document
from assetops_backend.runs.parsing import render_run_document
from assetops_backend.sites.site_parsing import parse_site_document, render_site_document
import fixtures, kobo
from kobo import kobo_draft, kobo_document, component
from gate import execute_through_the_lab
from lab_execution import HostLabExecution, YamlExecutionArtifacts
from source_stages import JsonSourceStages

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE

def _status(path):
    import yaml
    return {"status": yaml.safe_load(path.read_text(encoding="utf-8"))["status"]}

def fuel(site_template=None, site_edit=None, **kw):
    site = fixtures.site_from_template(site_template or fixtures.HYBRID_TEMPLATE, site_id="MG-001")
    if site_edit:
        d = copy.deepcopy(render_site_document(site)); site_edit(d)
        site = parse_site_document(d, source="edited")
    return fixtures.draft(site=site, **kw)

def rm_prop(cid, key):
    return lambda d: kobo.remove_property(d, cid, key)
def rm_fuel_prop(cid, key):
    def f(d): kobo.remove_property(d, cid, key)
    return f
def dup_pv(d):
    f = d["foundation"]
    twin = copy.deepcopy(kobo.component(d, "pv-array")); twin["component_id"] = "pv-array-2"
    f["components"].append(twin)
    f["topology"]["nodes"].append({"node_id": "pv-array-2", "component_id": "pv-array-2", "node_role": "GENERATION"})
    f["topology"]["connections"].append({"connection_id": "pv-array-2-to-inverter", "from_node": "pv-array-2", "to_node": "pv-inverter", "medium": "DC"})
    for c in f["site_controls"]:
        if c["control_key"] == "source-priority": c["members"].append("pv-array-2")
def offgrid(offset, dur, ev="evening-reserve-override"):
    def f(doc):
        for e in doc["timeline"]:
            if e["event_id"] == ev:
                e["offset_minutes"] = offset; e["timing"]["duration_minutes"] = dur
    return f

CASES = {
 # fuel
 "0101": lambda: fuel(),
 "0102": lambda: fuel(seed=20260101, timestep_minutes=5),
 "0103": lambda: fuel(start_time="2026-09-21T00:00:00Z", end_time="2026-09-23T00:00:00Z", timestep_minutes=15, seed=7),
 "0104": lambda: fuel(site_edit=rm_fuel_prop("fuel-tank","tank-capacity")),
 "0105": lambda: fuel(site_edit=rm_fuel_prop("generator","specific-fuel-consumption")),
 # daytime
 "0201": lambda: kobo_draft("kobo-daytime"),
 "0202": lambda: kobo_draft("kobo-daytime-overcast"),
 "0203": lambda: kobo_draft("kobo-daytime-larger-mill", seed=11),
 "0204": lambda: kobo_draft("kobo-daytime", timestep_minutes=15, seed=3),
 "0205": lambda: kobo_draft("kobo-daytime-overcast", timestep_minutes=5),
 "0206": lambda: kobo_draft("kobo-daytime-overcast", document_edit=offgrid(607, 90)),
 "0207": lambda: kobo_draft("kobo-daytime-overcast", document_edit=offgrid(0, 37)),
 "0208": lambda: kobo_draft("kobo-daytime", site_edit=rm_prop("battery","battery-energy-capacity")),
 "0209": lambda: kobo_draft("kobo-daytime", site_edit=rm_prop("pv-array","pv-rated-power")),
 "0210": lambda: kobo_draft("kobo-daytime", site_edit=dup_pv),
}
def main():
    for d in ("runs","stored-executions","pre-change-artifacts"): (OUT/d).mkdir(parents=True, exist_ok=True)
    expected={}; stored={}
    for k, make in CASES.items():
        rid=f"run-c9{'0'*26}{k}"
        try:
            run = replace(make(), run_id=rid)
        except Exception as e:
            print("CASE", k, "SETUP FAILED", type(e).__name__, str(e)[:200]); continue
        path = OUT/"runs"/f"{rid}.yaml"
        path.write_bytes(serialize_run_document(render_run_document(run)))
        run = read_run_record(path)
        with tempfile.TemporaryDirectory() as s:
            s=Path(s)
            res = execute_through_the_lab(run, s)
            art = res.pop("artifact_text")
            (OUT/"pre-change-artifacts"/path.name).write_text(art, encoding="utf-8")
            expected[rid]=res
            print(k, res.get("status"), res.get("model_profile"), res.get("outcome"), res.get("failure"), res.get("boundaries"))
            if res.get("status") is None:
                if k in ("0101","0201","0202","0210","0203"):
                    shutil.copyfile(s/"executions"/path.name, OUT/"stored-executions"/path.name)
                    stored[rid]=_status(OUT/"stored-executions"/path.name)
    # RUNNING artifacts: started, never run to the end
    for k in ("0102","0204"):
        rid=f"run-c9{'0'*26}{k}"
        run=read_run_record(OUT/"runs"/f"{rid}.yaml")
        with tempfile.TemporaryDirectory() as s:
            s=Path(s)
            lab=HostLabExecution(artifacts=YamlExecutionArtifacts(s/"executions"), stages=JsonSourceStages(s/"stages"))
            p=lab.start(run)
            print(k,"started terminal?",p.is_terminal)
            f=s/"executions"/f"{rid}.yaml"
            shutil.copyfile(f, OUT/"stored-executions"/f.name)
            stored[rid]=_status(OUT/"stored-executions"/f.name)
    (OUT/"expected.json").write_text(json.dumps(expected,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (OUT/"stored_expected.json").write_text(json.dumps(stored,indent=2,sort_keys=True)+"\n",encoding="utf-8")
main()
