"""Run the frozen batch-13 mk_targets.py unchanged, with __file__ placed here so its output lands in this folder
(REPO still resolves to this worktree), then keep only the selected cases and point them at localhost:5183."""
import json, sys
from pathlib import Path
here = Path(__file__).resolve()
frozen = here.parents[3] / "post-W6-audit" / "batch-13" / "tools" / "mk_targets.py"
phase = sys.argv[1]
sys.argv = [str(here.with_name("mk_targets.py")), phase]
exec(compile(frozen.read_text(encoding="utf-8"), str(frozen), "exec"), {"__name__": "__main__", "__file__": str(here.with_name("mk_targets.py"))})
part = {"one": "part-one", "stocked": "part-stocked", "late": "part-late"}[phase]
sel = json.loads((here.parents[2] / "selection.json").read_text(encoding="utf-8")); sel = sel if isinstance(sel, list) else sel["pairs"]
want = {(p["screen"], p["case"]) for p in sel if str(p["batch"]) == "13" and p["frozen_app"].split("/")[1] == part}
t = json.loads(here.with_name(f"targets-{phase}.json").read_text(encoding="utf-8"))
f = [dict(x, url=x["url"].replace("http://127.0.0.1:5183", "http://localhost:5183")) for x in t if (x["id"], x["case"]) in want]
(here.parents[1] / f"targets-{phase}.json").write_text(json.dumps(f, indent=1), encoding="utf-8")
print("selected", len(f), "of", len(want))
