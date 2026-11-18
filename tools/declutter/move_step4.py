"""Declutter step 4: `git mv` the tracked `.agent/` files per `step4_map.py` (verbatim moves).

Usage: python tools/declutter/move_step4.py owner|specs|archive [--dry-run]
       python tools/declutter/move_step4.py --verify
--verify checks, for every file tracked under `.agent/` at BASE, that its new location exists
and, for a move, holds the BASE bytes exactly (an archived file: BASE bytes after its one header
line; a split sheet: see split_specs.py --verify). Kept files are checked for presence, and the two
in UNCHANGED for identical bytes.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step4_map import ARCHIVE, BASE, SPECS, new_location  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
APPENDED = ("packet-declutter-03.md",)  # BASE bytes kept as a prefix; a step-4 lane addendum follows them
UNCHANGED = ("owner-walkthrough-notes-2026-11-01.md", "W1-UX-combined-owner-walkthrough.md")  # kept byte-identical


def git(*args: str, text: bool = True):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=text, check=True).stdout


def base_files() -> list[str]:
    return git("ls-tree", "-r", "--name-only", BASE, "--", ".agent").split("\n")[:-1]


def stage_of(new: str) -> str:
    if new.startswith("owner/"):
        return "owner"
    if new.startswith("specs/"):
        return "specs"
    if new.startswith(ARCHIVE + "/"):
        return "archive"
    return "keep"


def move(stage: str, dry: bool) -> int:
    n = 0
    for old in base_files():
        new = new_location(old)
        if stage_of(new) != stage or not (ROOT / old).exists():
            continue
        n += 1
        if dry:
            print(f"{old} -> {new}")
            continue
        (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
        git("mv", old, new)
    print(f"{stage}: {n} file(s) {'would move' if dry else 'moved'}")
    return 0


def verify() -> int:
    from archive_headers import strip_header  # noqa: E402
    bad, counts = [], {}
    split = {f"specs/{i}/spec.md" for i in SPECS.values() if (ROOT / f"specs/{i}/README.md").is_file()}
    for old in base_files():
        new = new_location(old)
        stage = stage_of(new)
        counts[stage] = counts.get(stage, 0) + 1
        if new in split:
            continue  # proven by split_specs.py --verify
        path = ROOT / new
        if not path.is_file():
            bad.append(f"missing {new} (from {old})")
            continue
        was = git("show", f"{BASE}:{old}", text=False)
        now = path.read_bytes()
        if stage == "archive":
            now = strip_header(new, now)
        if stage == "keep" and not old.endswith(UNCHANGED):
            continue  # kept in place and live: the handoff is trimmed (its BASE text is in .ai/history/),
            # the others had citations rewritten (rewrite_citations.py --verify)
        if old.endswith(APPENDED) and now.startswith(was):
            continue
        if now != was:
            bad.append(f"bytes differ: {new} vs {BASE}:{old}")
    for b in bad:
        print(f"FAIL {b}")
    print(f"step-4 moves: {sum(counts.values())} BASE files {counts}; "
          + ("all byte-identical" if not bad else f"{len(bad)} problem(s)"))
    return 1 if bad else 0


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(verify())
    sys.exit(move(sys.argv[1], "--dry-run" in sys.argv))
