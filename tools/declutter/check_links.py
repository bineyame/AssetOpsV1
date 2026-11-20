"""Declutter link check (steps 4 and 5): every `.agent/`, `specs/`, `owner/`, `Docs/`, `tasks/`, `tools/` and
`frontend/docs/` path cited in tracked text and code resolves to a file (or folder) or through the citation map.

A cited path resolves when:
- it exists now (file or folder); or
- it is `.agent/<p>` with <p> tracked at BASE: step4_map.new_location gives where it went (move_step4.py --verify
  proves those files); or
- it is `.agent/<p>` evidence untracked in step 3 and present under EVIDENCE (CITATION_MAP rule 6); or
- it is an old path in step5_map.MOVES whose new location exists (CITATION_MAP "Step 5").
Otherwise it is unresolved. An unresolved path that existed at the base (file or folder) was broken:
FAIL. One that did not exist at BASE either (a file never committed, deleted earlier, or written to an output
folder) is pre-existing and only counted, with examples.

Usage: python tools/declutter/check_links.py [--base REV] [--list-preexisting]
The base defaults to step 4's (`step4_map.BASE`); step 5 runs it with `--base step5_map.BASE` (d05bf668c).
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step4_map import BASE, new_location  # noqa: E402
from step5_map import MOVES as STEP5  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path("/opt/assetecon/evidence/repo-untracked-2026-11-18")
GREP = r"(^|[^A-Za-z0-9_./-])((\.agent|specs|owner|Docs|tasks|tools|frontend/docs)/[A-Za-z0-9_./-]*[A-Za-z0-9_/])([*<{$]?)"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def main() -> int:
    base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else BASE
    base_files = set(git("ls-tree", "-r", "--name-only", base).splitlines())
    step4_files = set(git("ls-tree", "-r", "--name-only", BASE).splitlines())  # what the step-4 map covers
    base_dirs = {str(Path(f).parent) for f in base_files}
    base_dirs |= {p for d in list(base_dirs) for p in (str(x) for x in Path(d).parents)}
    hits = git("grep", "-I", "-n", "-o", "-E", GREP, "--", ".")
    pat = re.compile(GREP)
    cited: dict[str, list[str]] = defaultdict(list)
    for line in hits.splitlines():
        where, _, rest = line.partition(":")
        num, _, text = rest.partition(":")
        m = pat.search(text)
        if not m or m.group(4):  # a glob or placeholder such as `.agent/owner-*.md`, `specs/<ID>/`
            continue
        cited[m.group(2).rstrip(".")].append(f"{where}:{num}")
    resolved = mapped = evidence = 0
    broken, pre = {}, {}
    for path, places in cited.items():
        if (ROOT / path).exists():
            resolved += 1
            continue
        if path in STEP5 and (ROOT / STEP5[path][0]).exists():
            mapped += 1
            continue
        if path.startswith(".agent/"):
            if path in step4_files:
                new = new_location(path)
                if (ROOT / new).exists() or (ROOT / new).parent.joinpath("README.md").is_file():
                    mapped += 1
                    continue
            elif path.rstrip("/") in base_dirs and (ROOT / new_location(path.rstrip("/") + "/x")).parent.is_dir():
                mapped += 1  # a cited `.agent/` folder whose files moved together (e.g. to archive/agent-history/)
                continue
            elif (EVIDENCE / path).exists():
                evidence += 1
                continue
        if path in base_files or path.rstrip("/") in base_dirs:
            broken[path] = places
        else:
            pre[path] = places
    for path, places in sorted(broken.items()):
        print(f"FAIL {path} (existed at {base}) cited in {', '.join(places[:3])}")
    if "--list-preexisting" in sys.argv:
        for path, places in sorted(pre.items()):
            print(f"pre-existing {path} cited in {', '.join(places[:2])}")
    by_root = defaultdict(int)
    for p in pre:
        by_root[p.split("/")[0]] += 1
    print(f"link check: {len(cited)} distinct cited paths; {resolved} exist, {mapped} resolve through the step-4/5 maps, "
          f"{evidence} are step-3 evidence; {len(broken)} broken since {base}; "
          f"{len(pre)} pre-existing unresolved (absent at {base} too) {dict(by_root)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
