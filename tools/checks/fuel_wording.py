"""DIESEL-1 H4 wording guard (K9, build sheet §8.4 row K9): client copy says "unexplained fuel". It never says
"theft", "stolen", "stole", "siphon" or "pilfer", and never implies them.

Scanned (tests and code comments excluded):
- `frontend/src/**/*.ts(x)`: comments stripped (block, JSX and `//` comments, the guard-12 rule), every remaining
  character scanned; test files (`__tests__/`, `*.test.*`, `src/test/`) are out of scope;
- `frontend/src/**/*.json` (not `__tests__/`, `__fixtures__/`, `src/test/`) and `frontend/index.html` (HTML comments
  stripped): bundled labels and page text;
- `backend/assetops_backend/**/*.py`: every string literal (f-string parts included) except docstrings and other bare
  string statements, read through `ast`, so comments never count;
- `config/**/*.json|yaml|yml`: every string key and value after parsing (YAML comments never count).

`served_hits(body)` applies the same words to a served JSON body (finish row KIS-8, run at E3).

    python tools/checks/fuel_wording.py          (exit 1 and one line per hit)
    python -m pytest tools/checks/test_fuel_wording.py   (self-test; `tools/check-all.ps1`)
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[2]
#: H4: the forbidden words, case-insensitive, whole words; "siphon" and "pilfer" with any ending.
#: H4 "never imply": also steal / steals / stealing and thief / thieves / thievery ("stealth" is a different word).
WORDS = re.compile(r"\b(?:thefts?|stolen|stole|steal(?:s|ing)?|thie(?:f|ves|very)|siphon\w*|pilfer\w*)\b",
                   re.IGNORECASE)
_HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")
_BLOCK = re.compile(r"/\*[\s\S]*?\*/")
_LINE = re.compile(r"(^|[^:\\])//[^\n]*")


def strip_ts_comments(source: str) -> str:
    """Block comments (JSX `{/* */}` included) and `//` comments not preceded by `:` (so `http://` survives) become
    spaces; newlines stay, so line numbers hold (the rule of `mock-deviation-labels.mjs` `stripComments`)."""
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))  # noqa: E731
    text = _BLOCK.sub(blank, source.replace("\r\n", "\n"))
    return _LINE.sub(lambda m: m.group(1) + re.sub(r"[^\n]", " ", m.group(0)[len(m.group(1)):]), text)


def ts_hits(path: str, source: str) -> list[str]:
    code = strip_ts_comments(source)
    return [f"{path}:{code.count(chr(10), 0, m.start()) + 1}: {m.group(0)!r}" for m in WORDS.finditer(code)]


def _bare_strings(tree: ast.AST) -> set[int]:
    """ids of the Constant nodes that are bare expression statements (docstrings and the like): not served copy."""
    return {id(n.value) for n in ast.walk(tree)
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}


def py_hits(path: str, source: str) -> list[str]:
    tree = ast.parse(source, filename=path)
    skip = _bare_strings(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in skip:
            out += [f"{path}:{n.lineno}: {m.group(0)!r}" for m in WORDS.finditer(n.value)]
    return out


def _strings(node: Any) -> Iterator[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(k)
            yield from _strings(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _strings(v)


def served_hits(body: Any) -> list[str]:
    """Every forbidden word in a parsed JSON body (keys and values)."""
    return [m.group(0) for s in _strings(body) for m in WORDS.finditer(s)]


def data_hits(path: str, source: str) -> list[str]:
    if path.endswith(".json"):
        docs = [json.loads(source)]
    else:
        import yaml

        docs = list(yaml.safe_load_all(source))
    return [f"{path}: {w!r}" for w in served_hits(docs)]


def _is_ts_test(rel: str) -> bool:
    return "/__tests__/" in f"/{rel}" or ".test." in rel or rel.startswith("frontend/src/test/")


def _is_fixture(rel: str) -> bool:
    return _is_ts_test(rel) or "/__fixtures__/" in f"/{rel}"


def html_hits(path: str, source: str) -> list[str]:
    code = _HTML_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), source.replace("\r\n", "\n"))
    return [f"{path}:{code.count(chr(10), 0, m.start()) + 1}: {m.group(0)!r}" for m in WORDS.finditer(code)]


def scan(root: Path = ROOT) -> tuple[list[str], int]:
    """(hits, files scanned) over the scopes under `root`."""
    hits, files = [], 0

    def rel(p: Path) -> str:
        return p.relative_to(root).as_posix()

    for p in sorted((root / "frontend" / "src").rglob("*")):
        if not p.is_file():
            continue
        if p.suffix in (".ts", ".tsx") and not _is_ts_test(rel(p)):
            files += 1
            hits += ts_hits(rel(p), p.read_text(encoding="utf-8"))
        elif p.suffix == ".json" and not _is_fixture(rel(p)):  # bundled client labels (presentationProfiles.json)
            files += 1
            hits += data_hits(rel(p), p.read_text(encoding="utf-8"))
    index = root / "frontend" / "index.html"
    if index.is_file():
        files += 1
        hits += html_hits(rel(index), index.read_text(encoding="utf-8"))
    for p in sorted((root / "backend" / "assetops_backend").rglob("*.py")):
        files += 1
        hits += py_hits(rel(p), p.read_text(encoding="utf-8"))
    for p in sorted((root / "config").rglob("*")):
        if p.suffix in (".json", ".yaml", ".yml") and p.is_file():
            files += 1
            hits += data_hits(rel(p), p.read_text(encoding="utf-8"))
    return hits, files


def main() -> int:
    hits, files = scan()
    for h in hits:
        print(h)
    if hits:
        print(f"fuel wording guard: {len(hits)} forbidden word(s) in served copy ({files} files scanned)")
        return 1
    print(f"fuel wording guard: clean ({files} files scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
