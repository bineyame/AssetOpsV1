"""Declutter step 4: give every file archived from `.agent/` one header line (and nothing else).

Header: "Finished; historical.", "Superseded by X on 2026-11-18." (step4_map.SUPERSEDED) or, for a file whose
decisions are still indexed live (step4_map.DECISION_BEARING, step 5), "Finished work; its decisions remain live per
`.ai/decisions/INDEX.md`.", then
"Archived from .agent/<path> on 2026-11-18 (declutter step 4)." In the file's own comment form:
markdown `> ...`, html `<!-- ... -->`, python/shell `# ...`. The original bytes follow unchanged, so
`strip_header` (drop the first line) gives back the BASE file exactly; move_step4.py --verify checks it.

Usage: python tools/declutter/archive_headers.py [--dry-run]   # add the header where missing, or relabel a
       DECISION_BEARING file that still has the plain "Finished; historical." header (same line count)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step4_map import ARCHIVE, DECISION_BEARING, SUPERSEDED  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MARK = "on 2026-11-18 (declutter step 4)."


def header(rel: str) -> bytes:
    """`rel` is the path below `archive/agent-history/` (= below `.agent/`)."""
    status = f"Superseded by {SUPERSEDED[rel]} on 2026-11-18." if rel in SUPERSEDED else (
        "Finished work; its decisions remain live per `.ai/decisions/INDEX.md`." if rel in DECISION_BEARING
        else "Finished; historical.")
    text = f"{status} Archived from .agent/{rel} {MARK}"
    if rel.endswith(".html"):
        return f"<!-- {text} -->\n".encode()
    if rel.endswith((".py", ".sh")):
        return f"# {text}\n".encode()
    return f"> {text}\n".encode()


def strip_header(path: str, data: bytes) -> bytes:
    rel = path[len(ARCHIVE) + 1:]
    want = header(rel)
    return data[len(want):] if data.startswith(want) else data + b"\0(header missing)"


def main() -> int:
    dry = "--dry-run" in sys.argv
    n = 0
    for path in sorted((ROOT / ARCHIVE).rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT / ARCHIVE).as_posix()
        data = path.read_bytes()
        h = header(rel)
        if data.startswith(h):
            continue
        if rel in DECISION_BEARING:  # relabel: swap the plain header line for the decision-bearing one
            plain = f"> Finished; historical. Archived from .agent/{rel} {MARK}\n".encode()
            if data.startswith(plain):
                n += 1
                if not dry:
                    path.write_bytes(h + data[len(plain):])
                continue
        n += 1
        if not dry:
            path.write_bytes(h + data)
    print(f"archive headers: {n} file(s) {'would get' if dry else 'got'} a header line")
    return 0


if __name__ == "__main__":
    sys.exit(main())
