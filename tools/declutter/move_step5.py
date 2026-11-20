"""Declutter step 5: move the Docs generations, the retired guards and the finished one-off tools per
`step5_map.py`, then rewrite citations of the old paths (mechanical, language-aware, idempotent).

Usage: python tools/declutter/move_step5.py move [--dry-run]       # git mv + one header line where due
       python tools/declutter/move_step5.py rewrite [--dry-run] [--report <file>]
       python tools/declutter/move_step5.py --verify                # every moved file = BASE bytes (+ header)

Header placement: line 1, or line 2 when the file starts with a shebang (`#!`), so an archived script still
parses. An old `:N` therefore becomes `:N+1` (a shebang file's `:1` stays `:1`).

Rewrite: every `<old path>` (any `../` or repo prefix kept; `:line` adjusted) in tracked text becomes its new path.
Where: the same language-aware spans as step 4 (`rewrite_citations.allowed_spans`: anywhere in md/html/txt/sh/ps1/yml;
.py docstrings and comments; .ts/.tsx/.js/.mjs/.cjs/.css comments), so no runtime value changes; a match in a code
value is reported, not rewritten. Not touched: verbatim records (archive/, Docs/archive/, .ai/history/, owner/,
specs/*/*), mocks, these scripts, specs/CITATION_MAP.md (edited by hand), and `tasks/README.md` citations (the
file stays, shortened: its citations still mean the queue file).
"""
from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step5_map import BASE, MOVES, header  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE = [
    "archive/*", "Docs/archive/*", ".ai/history/*", "tools/declutter/*", "owner/*", "specs/*/*",
    "specs/CITATION_MAP.md", "frontend/mockups/*", "tasks/archive/site-first-2026-10/queue-tables.md",
    ".agent/W1-UX-combined-owner-walkthrough.md", ".agent/owner-walkthrough-notes-2026-11-01.md",
]
JSON_REWRITE = ["frontend/docs/architecture/v69-dependency-registry-pilot.json",
                "frontend/docs/architecture/v69-panel-contracts.json",
                "frontend/docs/architecture/v69-screen-ledger.json"]
ANYWHERE = (".md", ".html", ".txt", ".sh", ".ps1", ".yml", ".yaml")
CODE = (".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".css")
REWRITTEN = {old: new for old, (new, _) in MOVES.items() if old != "tasks/README.md"}


def git(*args: str, text: bool = True):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=text, check=True).stdout


def base_bytes(path: str) -> bytes:
    return git("show", f"{BASE}:{path}", text=False)


def with_header(old: str, data: bytes) -> bytes:
    h = header(old)
    if h is None:
        return data
    if data.startswith(b"#!"):
        first, nl, rest = data.partition(b"\n")
        return first + nl + h + rest
    return h + data


def shebang(old: str) -> bool:
    return base_bytes(old).startswith(b"#!")


def move(dry: bool) -> int:
    n = 0
    for old, (new, _) in MOVES.items():
        if not (ROOT / old).exists():
            continue
        n += 1
        if dry:
            print(f"would move {old} -> {new}")
            continue
        (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
        git("mv", old, new)
        p = ROOT / new
        p.write_bytes(with_header(old, p.read_bytes()))
    print(f"step 5 move: {n} file(s) {'would move' if dry else 'moved'}")
    return 0


def verify() -> int:
    bad = 0
    for old, (new, _) in MOVES.items():
        p = ROOT / new
        if (ROOT / old).exists() and old != "tasks/README.md":
            print(f"FAIL {old} still exists"); bad += 1  # noqa: E702
        if not p.is_file():
            print(f"FAIL {new} missing"); bad += 1; continue  # noqa: E702
        if p.read_bytes() != with_header(old, base_bytes(old)):
            print(f"FAIL {new}: not the {BASE} bytes of {old} plus its header"); bad += 1  # noqa: E702
    print(f"step 5 verify: {len(MOVES)} moves, {len(MOVES) - bad} hold the {BASE} bytes (+ one header where due)")
    return 1 if bad else 0


ALT = "|".join(re.escape(o) for o in sorted(REWRITTEN, key=len, reverse=True))
PATH = re.compile(r"(?<![A-Za-z0-9_.-])(?<!archive/)(" + ALT + r")(:\d+(?:-\d+)?)?(?![A-Za-z0-9_-])")


def target(old: str, lines: str | None) -> str:
    new = REWRITTEN[old]
    if not lines or header(old) is None:
        return new + (lines or "")
    first_kept = 1 if shebang(old) else 0
    nums = [int(x) for x in lines[1:].split("-")]
    return new + ":" + "-".join(str(n if n <= first_kept else n + 1) for n in nums)


def candidates() -> list[str]:
    out = []
    for f in git("ls-files").split("\n"):
        if not f or any(fnmatch.fnmatch(f, p) for p in EXCLUDE):
            continue
        if f.endswith(ANYWHERE + CODE) or f in JSON_REWRITE:
            out.append(f)
    return out


def rewrite(dry: bool, report: str | None) -> int:
    from rewrite_citations import allowed_spans  # step 4's language-aware spans (comments and docstrings)
    stats, left, changed = Counter(), [], 0
    for f in candidates():
        p = ROOT / f
        try:
            text = p.read_bytes().decode("utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        if not PATH.search(text):
            continue
        spans = allowed_spans(f, text)
        out, last = [], 0
        for m in PATH.finditer(text):
            if spans is not None and not any(a <= m.start() < b for a, b in spans):
                left.append(f"{f}:{text.count(chr(10), 0, m.start()) + 1}: {m.group(1)} (code value; not rewritten)")
                continue
            out.append(text[last:m.start()] + target(m.group(1), m.group(2)))
            last = m.end()
            stats[REWRITTEN[m.group(1)].split("/")[0]] += 1
        new = "".join(out) + text[last:]
        if new != text:
            changed += 1
            if not dry:
                p.write_bytes(new.encode("utf-8"))
    if report:
        Path(report).write_text("\n".join(left) + "\n", encoding="utf-8")
    for line in left:
        print("left:", line)
    print(f"step 5 rewrite: {sum(stats.values())} citation(s) in {changed} file(s) {dict(stats)}; "
          f"{len(left)} left in code values{' (dry run)' if dry else ''}")
    return 0


def main() -> int:
    if "--verify" in sys.argv:
        return verify()
    dry = "--dry-run" in sys.argv
    report = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
    if sys.argv[1:2] == ["move"]:
        return move(dry)
    if sys.argv[1:2] == ["rewrite"]:
        return rewrite(dry, report)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
