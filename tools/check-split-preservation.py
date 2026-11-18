"""Proof that the declutter step-2 split moved text verbatim.

Takes the original `.ai/DECISIONS.md` and `.ai/CODE_STATE.md` from git (default: the
commit before `.ai/decisions/2026-09.md` was added; or --rev REV) and the parts as committed
by the split (default: the commit that added them; or --parts REV, or --worktree for the
files on disk), and checks:

- decisions: the four parts, each minus its 2-line header, concatenate in the order
  `.ai/decisions/INDEX.md` gives to the original, byte for byte;
- state: each area file minus its 2-line header is a concatenation of whole `## `
  sections of the original in their original relative order, and every original
  section is in exactly one area file (so all bytes are kept, none added).

The proof is of the split commit. After it the parts changed by design: declutter steps 4 and 5
rewrote citation paths in them (`tools/declutter/rewrite_citations.py`, `move_step5.py`; old paths
resolve through `specs/CITATION_MAP.md`), and the state area files take new entries (RULES 9).
So `--worktree` is expected to FAIL now; it is kept for re-proving a future verbatim move.

Usage: python tools/check-split-preservation.py [--rev REV] [--parts REV | --worktree]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEC_PARTS = ["2026-10-late.md", "old-index-2026-10.md", "2026-09.md", "2026-10-early.md"]
AREAS = ["overview", "tools", "shell", "lab", "data", "findings-money", "work", "cold-ev",
         "estate", "demo", "sites"]
HEADER = b"> Moved verbatim from the former "


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


PARTS_REV: str | None = None  # None = read the files on disk (--worktree)


def body(path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    data = path.read_bytes() if PARTS_REV is None else git("show", f"{PARTS_REV}:{rel}")
    first, _, rest = data.partition(b"\n")
    if not first.startswith(HEADER) or not rest.startswith(b"\n"):
        raise SystemExit(f"FAIL {path}: missing the 2-line header")
    return rest[1:]


def sections(data: bytes) -> list[bytes]:
    out, cur = [], []
    for line in data.splitlines(keepends=True):
        if line.startswith(b"## ") and cur:
            out.append(b"".join(cur))
            cur = []
        cur.append(line)
    out.append(b"".join(cur))
    return out


def main() -> int:
    if "--rev" in sys.argv:
        rev = sys.argv[sys.argv.index("--rev") + 1]
    else:
        added = git("log", "--diff-filter=A", "--format=%H", "--", ".ai/decisions/2026-09.md").split()
        rev = (added[-1].decode() + "^") if added else "HEAD"
    global PARTS_REV
    if "--worktree" not in sys.argv:
        PARTS_REV = sys.argv[sys.argv.index("--parts") + 1] if "--parts" in sys.argv else rev[:-1]
    print(f"parts read from {PARTS_REV or 'the working tree'}")
    bad = 0
    dec = git("show", f"{rev}:.ai/DECISIONS.md")
    joined = b"".join(body(ROOT / ".ai/decisions" / p) for p in DEC_PARTS)
    ok = joined == dec
    bad += not ok
    print(f"{'OK  ' if ok else 'FAIL'} decisions: {len(DEC_PARTS)} parts, {len(joined)} bytes vs original {len(dec)} bytes at {rev}")

    st = git("show", f"{rev}:.ai/CODE_STATE.md")
    pending = {a: sections(body(ROOT / ".ai/state" / f"{a}.md")) for a in AREAS}
    for a in AREAS:  # a body that is only a header-free empty string yields one empty section
        pending[a] = [s for s in pending[a] if s]
    placed = 0
    for sec in sections(st):
        home = next((a for a in AREAS if pending[a] and pending[a][0] == sec), None)
        if home is None:
            print(f"FAIL state: original section not found in order: {sec[:70]!r}")
            bad += 1
            break
        pending[home].pop(0)
        placed += 1
    left = {a: len(v) for a, v in pending.items() if v}
    if left:
        print(f"FAIL state: sections not in the original: {left}")
        bad += 1
    total = sum(len(body(ROOT / ".ai/state" / f"{a}.md")) for a in AREAS)
    if total != len(st):
        print(f"FAIL state: {total} bytes vs original {len(st)}")
        bad += 1
    if not bad:
        print(f"OK   state: {placed} sections in {len(AREAS)} area files, {total} bytes vs original {len(st)} bytes at {rev}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
