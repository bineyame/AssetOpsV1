"""Declutter step 4: give every file archived from `.agent/` one header line (and nothing else).

Header: "Finished; historical." or "Superseded by X on 2026-11-18." (step4_map.SUPERSEDED), then
"Archived from .agent/<path> on 2026-11-18 (declutter step 4)." In the file's own comment form:
markdown `> ...`, html `<!-- ... -->`, python/shell `# ...`. The original bytes follow unchanged, so
`strip_header` (drop the first line) gives back the BASE file exactly; move_step4.py --verify checks it.

Usage: python tools/declutter/archive_headers.py [--dry-run]   # add the header where missing
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step4_map import ARCHIVE, SUPERSEDED  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MARK = "on 2026-11-18 (declutter step 4)."


def header(rel: str) -> bytes:
    """`rel` is the path below `archive/agent-history/` (= below `.agent/`)."""
    status = f"Superseded by {SUPERSEDED[rel]} on 2026-11-18." if rel in SUPERSEDED else "Finished; historical."
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
        n += 1
        if not dry:
            path.write_bytes(h + data)
    print(f"archive headers: {n} file(s) {'would get' if dry else 'got'} a header line")
    return 0


if __name__ == "__main__":
    sys.exit(main())
