"""Decision, state, spec and owner indexes resolve (declutter step 2).

1. Every decision ID cited in tracked text resolves through `.ai/decisions/index-*.md`.
   Families: dated `D-YYYY-MM-DD-slug`, and lettered rulings `D-SR.12`, `D-E5.3`,
   `D-ANY.6a`, `D-W1-4`, `D-AW-2` ... (any `D-<LETTERS/DIGITS>` then `.n` or `-n`).
   A dated token also resolves when it is the start of an indexed ID: line-wrapped
   citations (`D-2026-10-09-pre-s3`) and bare dates (`D-2026-10-09`) are common.
   File names such as `.agent/D-SR63-67-review.md` are not citations.
   Reserved example IDs (`D-EG.n`, `D-2099-...`, .ai/RULES.md §9) are skipped.
2. Every file an index names exists and holds the IDs indexed to it, as whole tokens.
   A `file:line` pointer whose line no longer holds the ID is a note (live files grow).
3. Every tracked `.agent/owner-*.md` and build sheet/spec has an index row, and every
   index file is under the 2k-token cap.

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
WARNINGS: list[str] = []
ID_LINE = re.compile(r"^- `([^`]+)` .* · ([^ ·]+?)(?::(\d+))?$")
FILE_TOKEN = re.compile(r"`([A-Za-z0-9_.-]+\.(?:md|html|txt))`|· ([A-Za-z0-9_.-]+\.md)(?::\d+)?$")


def tracked_citations(root: Path) -> dict[str, set[str]]:
    out = subprocess.run(
        ["git", "-C", str(root), "grep", "-I", "-o", "-P", GREP, "--",
         ".", ":(exclude).ai/decisions/index-*.md", ":(exclude)tools/check-decision-index.py"],
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


CAP_BYTES = 8000  # the 2k-token index cap (.ai/RULES.md §9) at 4 bytes per token
EXAMPLE = re.compile(r"D-(?:EG[.-]|2099-)")  # reserved example IDs (.ai/RULES.md §9); never indexed


def holds(text: str, ident: str) -> bool:
    """`ident` occurs as a whole token: `D-SR.2` is not held by `D-SR.20`."""
    return re.search(re.escape(ident) + r"(?![0-9A-Za-z])", text) is not None


def indexed(root: Path, planted: str = "", virtual: dict[str, str] | None = None
            ) -> tuple[dict[str, tuple[str, str | None]], list[str]]:
    """`planted` is extra decision-index text, read as one more index-*.md; `virtual` maps
    file names to texts they resolve to (both for the self-test; nothing is written)."""
    virtual = virtual or {}
    ids: dict[str, tuple[str, str | None]] = {}
    problems: list[str] = []
    for glob, homes in INDEXES.items():
        files = [(p.relative_to(root).as_posix(), p.read_text(encoding="utf-8")) for p in sorted(root.glob(glob))]
        if not files:
            problems.append(f"no index matches {glob}")
        if planted and glob == ".ai/decisions/index-*.md":
            files.append(("(planted index)", planted))
        for rel, body in files:
            size = len(body.encode("utf-8"))
            if size > CAP_BYTES:
                problems.append(f"{rel}: {size} bytes, over the index cap of {CAP_BYTES} (2k tokens); split it")
            for n, line in enumerate(body.splitlines(), 1):
                names = [a or b for a, b in FILE_TOKEN.findall(line)]
                for name in names:
                    if name not in virtual and not any((root / h / name).is_file() for h in homes) \
                            and not (root / name).is_file():
                        problems.append(f"{rel}:{n}: names a missing file `{name}`")
                m = ID_LINE.match(line) if glob.startswith(".ai/decisions/index-") else None
                if m:
                    ident, name, at = m.groups()
                    ids[ident] = (name, at)
                    if name in virtual:
                        text = virtual[name]
                    else:
                        target = next((root / h / name for h in homes if (root / h / name).is_file()), None)
                        if target is None:
                            continue
                        text = target.read_text(encoding="utf-8", errors="ignore")
                    stem = re.sub(r"[a-z]$", "", ident)
                    in_file = holds(text, ident) or holds(text, stem)
                    if not in_file:
                        problems.append(f"{rel}:{n}: `{ident}` does not occur in {name}")
                    elif at:
                        lines = text.splitlines()
                        here = lines[int(at) - 1] if int(at) <= len(lines) else ""
                        if not (holds(here, ident) or holds(here, stem)):
                            # the file grew above the line: a stale pointer, not a lost decision
                            WARNINGS.append(f"{rel}:{n}: `{ident}` moved off {name}:{at}")
    return ids, problems


def coverage(root: Path, extra_tracked: list[str] | None = None) -> list[str]:
    """Every tracked owner file and build sheet/spec has an index row."""
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", ".agent"],
                             capture_output=True, text=True, check=True).stdout.split() + (extra_tracked or [])
    owner = "".join(p.read_text(encoding="utf-8") for p in sorted(root.glob("owner/index-*.md")))
    specs = (root / "specs/INDEX.md").read_text(encoding="utf-8") if (root / "specs/INDEX.md").is_file() else ""
    problems = []
    for path in tracked:
        name = path.rsplit("/", 1)[-1]
        if re.fullmatch(r"owner-.*\.md", name) and f"`{name}`" not in owner:
            problems.append(f"{path} has no row in owner/index-*.md")
        if re.search(r"build-sheet|build-spec", name) and f"`{name}`" not in specs:
            problems.append(f"{path} has no row in specs/INDEX.md")
    return problems


def check(root: Path, extra_cites: dict[str, set[str]] | None = None, planted: str = "",
          virtual: dict[str, str] | None = None, extra_tracked: list[str] | None = None) -> list[str]:
    ids, problems = indexed(root, planted, virtual)
    problems += coverage(root, extra_tracked)
    dated = [i for i in ids if i.startswith("D-20")]
    cites = tracked_citations(root)
    for k, v in (extra_cites or {}).items():
        cites.setdefault(k, set()).update(v)
    for token, paths in sorted(cites.items()):
        if token in ids or EXAMPLE.match(token):
            continue
        if re.fullmatch(DATED, token) and any(i.startswith(token) for i in dated):
            continue
        problems.append(f"unresolved decision ID `{token}` cited in {', '.join(sorted(paths)[:3])}"
                        + (f" (+{len(paths) - 3} more)" if len(paths) > 3 else ""))
    return problems


def self_test() -> int:
    """Each planted fault must be reported, and the reserved example IDs must not be. Nothing is written."""
    planted = ("- `D-SR.9999` planted · live · no-such-file-selftest.md:1\n"
               "- `D-SR.2` prefix trap · live · prefix-trap-selftest.md:1\n"
               + "x" * (CAP_BYTES + 1) + "\n")
    problems = check(ROOT, {"D-ZZ.4242": {"(planted citation)"}, "D-EG.7": {"(example)"},
                            "D-2099-01-01-example": {"(example)"}},
                     planted, {"prefix-trap-selftest.md": "Only D-SR.20 and D-SR.21 are here.\n"},
                     [".agent/owner-selftest-unindexed-2099-01-01.md", ".agent/build-sheet-SELFTEST.md"])
    want = ["`D-ZZ.4242`", "`no-such-file-selftest.md`", "`D-SR.2` does not occur in prefix-trap-selftest.md",
            "(planted index): ", "owner-selftest-unindexed-2099-01-01.md has no row",
            "build-sheet-SELFTEST.md has no row"]
    missing = [w for w in want if not any(w in p for p in problems)]
    leaked = [p for p in problems if "D-EG.7" in p or "D-2099-01-01" in p]
    if missing or leaked:
        print(f"self-test FAILED: not reported {missing}; example IDs reported {leaked}")
        return 1
    for p in problems:
        print(f"  reported: {p}")
    print(f"self-test: {len(want)} planted faults reported, reserved example IDs skipped (nothing is written)")
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
    for w in sorted(set(WARNINGS)):
        print(f"note {w} (update the line number)")
    ids, _ = indexed(ROOT)
    print(f"decision/state/spec/owner indexes: OK ({len(ids)} indexed decision IDs; every cited ID resolves; every named file exists)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
