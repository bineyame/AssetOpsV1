"""DD-1b2a M3 (fix round): add the whole-list days the probe list omitted (S-3 late-as-normal, then S-1 normal) on a
clone, tick after each, and sample the mill thread, studies and boards. Development only; measures, never tunes.

    python tools/dd1b2a_m3.py --db assetops_demo3_dd1b2r_test --work var/demo3_dd1b2r --out .agent/DD-1b2a-m3.json

It reuses `dd1b2a_probe.py`'s `sample` and `boards` children (run inside the work folder's private tree).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

STEPS = (("S-3", {"site_code": "KOBO-001", "kind": "late", "day": "S-3d", "as_kind": "normal"}),
         ("S-1", {"site_code": "KOBO-001", "kind": "normal", "day": "S-1d", "as_kind": None}))
MAX_TICKS = 4


def run(db: str, work_name: str, out: Path) -> None:
    from demo_combined import Demo

    probe = "dd1b2a_probe.py"

    class Sampling(Demo):
        def child(self, *argv: str) -> None:
            done = self.py(str(self.tree / "tools" / probe), *argv, cwd=self.tree / "backend" / "tests",
                           label=f"probe-{argv[0]}", check=False)
            print(done.stdout.strip().splitlines()[-1][:300] if done.stdout.strip() else "(no output)", flush=True)
            if done.returncode:
                print(done.stdout[-1500:], flush=True)

    demo = Sampling(db, work_name)
    read = lambda name: json.loads((demo.work / name).read_text(encoding="utf-8"))  # noqa: E731
    samples: dict = {}
    steps: list = []

    def take(name: str) -> dict:
        demo.child("sample", demo.url, str(demo.work), name)
        samples[name] = read(f"sample-{name}.json")
        return samples[name]

    take("start")
    for label, kw in STEPS:
        record: dict = {"step": label, "add": None, "refused": None, "ticks": []}
        try:
            record["add"] = demo.add_day(**kw)
        except BaseException as exc:  # a refusal is recorded exactly, then the next step goes on
            record["refused"] = f"{type(exc).__name__}: {exc}"
            steps.append(record)
            continue
        take(f"after-add-{label}")
        for n in range(1, MAX_TICKS + 1):
            demo.tick(times=1)
            s = take(f"after-add-{label}-tick-{n}")
            record["ticks"].append(f"after-add-{label}-tick-{n}")
            if s["pending_snapshots_count"] == 0 and s["snapshot_dirty"] == 0:
                break
        steps.append(record)
    demo.child("boards", demo.url, str(demo.work))
    doc = {"db": db, "story": {k: read("story.json").get(k) for k in ("S", "code", "sites")},
           "steps": steps, "samples": samples, "boards": read("boards.json")}
    out.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.db, args.work, Path(args.out))
