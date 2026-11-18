"""Decision, state, spec and owner indexes resolve (declutter step 2).

1. Every decision ID cited in tracked text resolves through `.ai/decisions/index-*.md`.
   Families: dated `D-YYYY-MM-DD-slug`, and lettered rulings `D-SR.12`, `D-E5.3`,
   `D-ANY.6a`, `D-W1-4`, `D-AW-2` ... (any `D-<LETTERS/DIGITS>` then `.n` or `-n`).
   A dated token also resolves when it is the start of an indexed ID: line-wrapped
   citations (`D-2026-10-09-pre-s3`) and bare dates (`D-2026-10-09`) are common.
   File names such as `.agent/D-SR63-67-review.md` are not citations.
2. Every file an index names exists; a `file:line` pointer's line holds the ID.

Usage: python tools/check-decision-index.py [--self-test]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATED = r"D-20\d\d-\d\d-\d\d(?:-[A-Za-z0-9]+)*"
FAMILY = r"D-[A-Z][A-Z0-9]*(?:\.\d+[a-z]?|-\d+[a-z]?)"
GREP = rf"(^|[^A-Za-z0-9_/.-])({DATED}|{FAMILY})([^ ]{{0,3}})"
INDEXES = {  # index glob -> folders a bare file name resolves against, in order
    ".ai/decisions/index-*.md": [".ai/decisions", ".agent"],
    ".ai/decisions/INDEX.md": [".ai/decisions"],
    ".ai/state/index-*.md": [".ai/state"],
    ".ai/state/INDEX.md": [".ai/state"],
    "specs/INDEX.md": [".agent"],
    "owner/INDEX.md": [".agent", "owner"],
    "owner/index-*.md": [".agent", "owner"],
}
ID_LINE = re.compile(r"^- `([^`]+)` .* · ([^ ·]+?)(?::(\d+))?$")
FILE_TOKEN = re.compile(r"`([A-Za-z0-9_.-]+\.(?:md|html|txt))`|· ([A-Za-z0-9_.-]+\.md)(?::\d+)?$")


def tracked_citations(root: Path) -> dict[str, set[str]]:
    out = subprocess.run(
        ["git", "-C", str(root), "grep", "-I", "-o", "-P", GREP, "--",
         ".", ":(exclude).ai/decisions/index-*.md"],
        capture_output=True, text=True, check=False)
    if out.returncode not in (0, 1):
        raise SystemExit(f"git grep failed: {out.stderr.strip()}")
    cites: dict[str, set[str]] = {}
    pat = re.compile(GREP)
    for line in out.stdout.splitlines():
        path, _, hit = line.partition(":")
        m = pat.search(hit)
        if not m:
            continue
        token, after = m.group(2), m.group(3)
        if after.startswith(".md") or re.match(r"[\w-]", after or " "):
            continue  # a file name, or a longer word such as D-SR63-67-review
        cites.setdefault(token, set()).add(path)
    return cites


def indexed(root: Path, planted: str = "") -> tuple[dict[str, tuple[str, str | None]], list[str]]:
    """`planted` is extra decision-index text, read as if it were one more index-*.md (self-test)."""
    ids: dict[str, tuple[str, str | None]] = {}
    problems: list[str] = []
    for glob, homes in INDEXES.items():
        files = [(p.relative_to(root).as_posix(), p.read_text(encoding="utf-8")) for p in sorted(root.glob(glob))]
        if not files:
            problems.append(f"no index matches {glob}")
        if planted and glob == ".ai/decisions/index-*.md":
            files.append(("(planted index)", planted))
        for rel, body in files:
            for n, line in enumerate(body.splitlines(), 1):
                names = [a or b for a, b in FILE_TOKEN.findall(line)]
                for name in names:
                    if not any((root / h / name).is_file() for h in homes) and not (root / name).is_file():
                        problems.append(f"{rel}:{n}: names a missing file `{name}`")
                m = ID_LINE.match(line) if glob.startswith(".ai/decisions/index-") else None
                if m:
                    ident, name, at = m.groups()
                    ids[ident] = (name, at)
                    target = next((root / h / name for h in homes if (root / h / name).is_file()), None)
                    if target is None:
                        continue
                    text = target.read_text(encoding="utf-8", errors="ignore")
                    stem = re.sub(r"[a-z]$", "", ident)
                    if at:
                        lines = text.splitlines()
                        held = int(at) <= len(lines) and (ident in lines[int(at) - 1] or stem in lines[int(at) - 1])
                        if not held:
                            problems.append(f"{rel}:{n}: `{ident}` is not on {name}:{at}")
                    elif ident not in text:
                        problems.append(f"{rel}:{n}: `{ident}` does not occur in {name}")
    return ids, problems


def check(root: Path, extra_cites: dict[str, set[str]] | None = None, planted: str = "") -> list[str]:
    ids, problems = indexed(root, planted)
    dated = [i for i in ids if i.startswith("D-20")]
    cites = tracked_citations(root)
    for k, v in (extra_cites or {}).items():
        cites.setdefault(k, set()).update(v)
    for token, paths in sorted(cites.items()):
        if token in ids:
            continue
        if re.fullmatch(DATED, token) and any(i.startswith(token) for i in dated):
            continue
        problems.append(f"unresolved decision ID `{token}` cited in {', '.join(sorted(paths)[:3])}"
                        + (f" (+{len(paths) - 3} more)" if len(paths) > 3 else ""))
    return problems


def self_test() -> int:
    """A planted dangling ID and a planted missing file must each fail."""
    problems = check(ROOT, {"D-ZZ.4242": {"(planted citation)"}},
                     "- `D-SR.9999` planted · live · no-such-file-selftest.md:1\n")
    want = ["`D-ZZ.4242`", "`no-such-file-selftest.md`"]
    missing = [w for w in want if not any(w in p for p in problems)]
    if missing:
        print(f"self-test FAILED: planted {missing} not reported")
        return 1
    for p in problems:
        print(f"  reported: {p}")
    print("self-test: planted dangling ID and missing file both reported (nothing is written)")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    problems = check(ROOT)
    for p in problems:
        print(f"FAIL {p}")
    if problems:
        print(f"decision/state/spec/owner indexes: {len(problems)} problem(s)")
        return 1
    ids, _ = indexed(ROOT)
    print(f"decision/state/spec/owner indexes: OK ({len(ids)} indexed decision IDs; every cited ID resolves; every named file exists)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
