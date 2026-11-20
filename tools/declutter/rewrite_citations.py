"""Declutter step 4: rewrite citations of moved `.agent/` files to their new paths (mechanical).

What is rewritten: every `.agent/<path>` (or `.agent\\<path>`, with any `../` or repo prefix kept) whose
<path> was tracked at BASE and moved (step4_map.new_location), and, in `.ai/decisions/index-*.md` only,
the bare file names those indexes resolve against `.agent/`. Never touched: files kept in `.agent/`.

Targets:
- a plain move: the new path; a `:line` on an archived file gets +1 (its one header line);
- a split spec (specs/<ID>/README.md): with `:line`, the part and part line from the README map; else
  the part named by the quoted section titles that follow on the same line, when they all agree;
  else the folder `specs/<ID>/` (its README maps sections to parts).

Where (language-aware, so no runtime value changes):
- .md .html .txt .sh .ps1 .yml .yaml and the three frontend/docs/architecture/*.json registries: anywhere;
- .py: comments and standalone string statements (docstrings) only;
- .ts .tsx .js .mjs .cjs: comments only; .css: comments only.
Excluded files (verbatim records, data read at run time, mocks, uncommitted elsewhere): EXCLUDE below.
Everything not rewritten is covered by specs/CITATION_MAP.md (same rules).

Usage: python tools/declutter/rewrite_citations.py [--dry-run] [--report <file>]
       python tools/declutter/rewrite_citations.py --verify <rewrite-commit>   # code changed only in comments
Re-running on the result changes nothing (idempotent): the new paths no longer match.
"""
from __future__ import annotations

import fnmatch
import io
import re
import subprocess
import sys
import tokenize
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step4_map import ARCHIVE, BASE, SPECS, new_location  # noqa: E402
from split_specs import line_map  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE = [
    "archive/*", ".ai/history/*", "tools/declutter/*",       # verbatim history; these scripts
    "owner/owner-*.md",                                       # owner words, verbatim (O4)
    "specs/*/*",                                              # moved/split spec text (verbatim) and split maps
    "specs/CITATION_MAP.md",
    ".agent/W1-UX-combined-owner-walkthrough.md",              # read by test_evidence_checks.mjs
    ".agent/owner-walkthrough-notes-2026-11-01.md",            # uncommitted change in the main checkout
    "frontend/mockups/*",                                     # mock pages (owner-reviewed artifacts)
]
JSON_REWRITE = ["frontend/docs/architecture/v69-dependency-registry-pilot.json",
                "frontend/docs/architecture/v69-panel-contracts.json",
                "frontend/docs/architecture/v69-screen-ledger.json"]
ANYWHERE = (".md", ".html", ".txt", ".sh", ".ps1", ".yml", ".yaml")
JS = (".ts", ".tsx", ".js", ".mjs", ".cjs")
PATH = re.compile(r"\.agent([/\\])([A-Za-z0-9_.\-]+(?:[/\\][A-Za-z0-9_.\-]+)*)(:\d+(?:-\d+)?)?")
QUOTED = re.compile(r"[\"“]([^\"”]{3,90})[\"”]")


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


BASE_FILES = {p[len(".agent/"):] for p in git("ls-tree", "-r", "--name-only", BASE, "--", ".agent").split("\n") if p}
MAPS = {i: line_map(i) for i in SPECS.values()}
TITLES: dict[str, list[tuple[str, str]]] = {}
for _i, _rows in MAPS.items():
    if _rows:
        readme = (ROOT / "specs" / _i / "README.md").read_text(encoding="utf-8").splitlines()
        TITLES[_i] = [(m.group(4), line.rsplit("|", 2)[-2].strip()) for line in readme
                      if (m := re.match(r"^\| (\d+) \| (\d+)-(\d+) \| `([^`]+)` \|", line))]


def known(rel: str) -> str | None:
    rel = rel.replace("\\", "/")
    while rel and rel not in BASE_FILES and rel[-1] in ".-_":
        rel = rel[:-1]
    return rel if rel in BASE_FILES else None


def map_line(spec_id: str, n: int) -> tuple[str, int] | None:
    for a, b, part, p0 in MAPS[spec_id] or []:
        if a <= n <= b:
            return part, p0 + (n - a)
    return None


def target(rel: str, lines: str | None, tail: str) -> str | None:
    """New text for `.agent/<rel><lines>` (lines like ':12' or ':12-20'), or None to leave it."""
    new = new_location(".agent/" + rel)
    if new == ".agent/" + rel:
        return None
    nums = [int(x) for x in lines[1:].split("-")] if lines else []
    spec_id = new.split("/")[1] if new.startswith("specs/") else None
    if spec_id and MAPS.get(spec_id):
        if nums:
            hits = [map_line(spec_id, n) for n in nums]
            if all(hits) and len({h[0] for h in hits}) == 1:
                return f"specs/{spec_id}/{hits[0][0]}:" + "-".join(str(h[1]) for h in hits)
            if hits[0]:
                return f"specs/{spec_id}/{hits[0][0]}:{hits[0][1]}"
            return f"specs/{spec_id}/"
        parts = set()
        for q in QUOTED.findall(tail[:240]):
            q = q.strip().rstrip(".,;:")
            found = [p for p, t in TITLES[spec_id] if t.startswith(q) or (len(q) > 12 and q in t)]
            if found:
                parts.add(found[0])
        return f"specs/{spec_id}/{parts.pop()}" if len(parts) == 1 else f"specs/{spec_id}/"
    if nums and new.startswith(ARCHIVE + "/"):
        return new + ":" + "-".join(str(n + 1) for n in nums)
    return new + (lines or "")


def allowed_spans(path: str, text: str) -> list[tuple[int, int]] | None:
    """None = anywhere; else the (start, end) offsets where a rewrite may happen."""
    if path.endswith(".py"):
        return py_spans(text)
    if path.endswith(JS):
        return js_spans(text, line_comments=True)
    if path.endswith(".css"):
        return js_spans(text, line_comments=False)
    return None


def py_spans(text: str) -> list[tuple[int, int]]:
    bom = 1 if text.startswith("\ufeff") else 0  # a BOM would hide the module docstring from tokenize
    text = text[bom:]
    starts = [bom]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    off = lambda rc: starts[rc[0] - 1] + rc[1]  # noqa: E731
    spans, prev = [], tokenize.NEWLINE
    toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    for i, t in enumerate(toks):
        if t.type == tokenize.COMMENT:
            spans.append((off(t.start), off(t.end)))
        elif t.type == tokenize.STRING and prev in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL,
                                                     tokenize.ENCODING):
            nxt = next((u for u in toks[i + 1:] if u.type not in (tokenize.COMMENT,)), None)
            if nxt is None or nxt.type in (tokenize.NEWLINE, tokenize.ENDMARKER):
                spans.append((off(t.start), off(t.end)))
        if t.type not in (tokenize.COMMENT, tokenize.NL):
            prev = t.type
    return spans


def js_spans(text: str, line_comments: bool) -> list[tuple[int, int]]:
    spans, i, n, stack = [], 0, len(text), []  # stack: template-literal brace depths
    while i < n:
        c, nx = text[i], text[i + 1:i + 2]
        if c == "/" and nx == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            spans.append((i, j)); i = j; continue  # noqa: E702
        if line_comments and c == "/" and nx == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            spans.append((i, j)); i = j; continue  # noqa: E702
        if line_comments and c in "'\"`":
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":
                    j += 1
                elif c == "`" and text[j:j + 2] == "${":
                    depth, j = 1, j + 2
                    while j < n and depth:
                        depth += {"{": 1, "}": -1}.get(text[j], 0)
                        j += 1
                    continue
                elif c != "`" and text[j] == "\n":
                    break
                j += 1
            i = j + 1; continue  # noqa: E702
        i += 1
    return spans


def rewrite_text(path: str, text: str, stats: Counter, left: list[str]) -> str:
    spans = allowed_spans(path, text)
    inside = (lambda k: True) if spans is None else (lambda k: any(a <= k < b for a, b in spans))  # noqa: E731
    out, last = [], 0
    for m in PATH.finditer(text):
        rel = known(m.group(2))
        if rel is None:
            continue
        end = m.start(2) + len(rel)
        lines = m.group(3) if end == m.end(2) else None
        stop = m.end() if lines else end
        new = target(rel, lines, text[stop:text.find("\n", stop) if "\n" in text[stop:] else len(text)])
        if new is None:
            continue
        if not inside(m.start()):
            line_no = text.count("\n", 0, m.start()) + 1
            left.append(f"{path}:{line_no}: .agent/{rel} (runtime value; not rewritten)")
            stats["left in code values"] += 1
            continue
        stats[new.split("/")[0]] += 1
        if m.group(1) == "\\":
            new = new.replace("/", "\\")
        out.append(text[last:m.start()] + new)
        last = stop
    if path.startswith(".ai/decisions/index-"):
        text2 = "".join(out) + text[last:]
        return rewrite_bare(text2, stats)
    return "".join(out) + text[last:]


ROOT_NAMES = sorted((r for r in BASE_FILES if "/" not in r and new_location(".agent/" + r) != ".agent/" + r),
                    key=len, reverse=True)
BARE = re.compile(r"(?<![\w./\\-])(" + "|".join(re.escape(r) for r in ROOT_NAMES) + r")(:\d+(?:-\d+)?)?(?![\w-])")


def rewrite_bare(text: str, stats: Counter) -> str:
    def sub(m: re.Match) -> str:
        new = target(m.group(1), m.group(2), "")
        if new is None:
            return m.group(0)
        stats["bare names in decision indexes"] += 1
        return new
    return BARE.sub(sub, text)


def candidates() -> list[str]:
    files = git("ls-files").split("\n")
    out = []
    for f in files:
        if not f or any(fnmatch.fnmatch(f, p) for p in EXCLUDE):
            continue
        if f.endswith(".json") and f not in JSON_REWRITE:
            continue
        if f.endswith(ANYWHERE + JS + (".py", ".css")) or f in JSON_REWRITE:
            out.append(f)
    return out


def strip_spans(path: str, text: str) -> str:
    spans = allowed_spans(path, text) or []
    out, last = [], 0
    for a, b in sorted(spans):
        out.append(text[last:a])
        last = max(last, b)
    return "".join(out) + text[last:]


def verify(commit: str) -> int:
    """Every code file the rewrite commit changed differs only inside comments and docstrings."""
    names = git("diff", "--name-only", f"{commit}^", commit).split()
    code = [n for n in names if n.endswith(JS + (".py", ".css"))]
    bad = []
    for n in code:
        old = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}^:{n}"], capture_output=True,
                             check=True).stdout.decode("utf-8")
        new = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{n}"], capture_output=True,
                             check=True).stdout.decode("utf-8")
        if strip_spans(n, old) != strip_spans(n, new):
            bad.append(n)
    for n in bad:
        print(f"FAIL {n}: changed outside comments/docstrings")
    print(f"rewrite verify: {len(names)} files changed in {commit}, {len(code)} code files, "
          f"{len(code) - len(bad)} changed only in comments/docstrings")
    return 1 if bad else 0


def main() -> int:
    if "--verify" in sys.argv:
        return verify(sys.argv[sys.argv.index("--verify") + 1])
    dry = "--dry-run" in sys.argv
    stats, left, changed = Counter(), [], 0
    for f in candidates():
        p = ROOT / f
        try:
            text = p.read_bytes().decode("utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        if ".agent" not in text and not f.startswith(".ai/decisions/index-"):
            continue
        new = rewrite_text(f, text, stats, left)
        if new != text:
            changed += 1
            if not dry:
                p.write_bytes(new.encode("utf-8"))
    if "--report" in sys.argv:
        Path(sys.argv[sys.argv.index("--report") + 1]).write_text("\n".join(left) + "\n", encoding="utf-8")
    total = sum(v for k, v in stats.items() if k != "left in code values")
    print(f"citation rewrite: {total} rewritten in {changed} file(s) {dict(stats)}; "
          f"{len(left)} left in code values{' (dry run)' if dry else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
