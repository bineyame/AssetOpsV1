"""DIESEL-1 H4 wording guard (K9): self-tests for `tools/checks/fuel_wording.py`, plus the repository scan.

    python -m pytest tools/checks/test_fuel_wording.py   (a `tools/check-all.ps1` guard)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuel_wording as fw  # noqa: E402


def _tree(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


CLEAN = {
    "frontend/src/sites/A.tsx": ('// never say theft here\n/* stolen */\nexport const A = () => <p>{/* siphon */}'
                                 'Unexplained fuel. See http://x.test/a</p>;\n'),
    "frontend/src/sites/__tests__/a.test.tsx": 'expect(text).not.toContain("theft");\n',
    "frontend/src/sites/b.test.ts": 'const banned = "pilfer";\n',
    "frontend/src/test/helpers.ts": 'export const WORD = "stole";\n',
    "backend/assetops_backend/m.py": ('"""Module doc: never theft."""\n# a stolen comment\n'
                                      'def f():\n    """siphon in a docstring"""\n    return "unexplained fuel"\n'),
    "config/a.json": '{"text": "Unexplained fuel"}\n',
    "config/b.yaml": "# pilfer in a comment\ntext: Fuel accounted for\n",
    "frontend/src/sites/profiles.json": '{"labels": {"fuel": "Unexplained fuel", "mood": "stealth mode"}}\n',
    "frontend/src/shell/__fixtures__/f.json": '{"t": "thief"}\n',
    "frontend/src/shell/__tests__/t.json": '{"t": "thieves"}\n',
    "frontend/src/test/v.json": '{"t": "stealing"}\n',
    "frontend/index.html": "<!-- a thief comment -->\n<title>AssetOps</title>\n",
}


def test_clean_tree_passes(tmp_path: Path) -> None:
    hits, files = fw.scan(_tree(tmp_path, CLEAN))
    # A.tsx, m.py, a.json, b.yaml, profiles.json, index.html; the test files and fixtures are out of scope
    assert hits == [] and files == 6


@pytest.mark.parametrize("rel, text, word", [
    ("frontend/src/sites/A.tsx", 'export const A = () => <p>Possible theft</p>;\n', "theft"),
    ("frontend/src/sites/A.tsx", 'const t = `fuel was ${"Stolen"}`;\n', "Stolen"),
    ("frontend/src/x.ts", "export const W = 'pilferage';\n", "pilferage"),
    ("backend/assetops_backend/m.py", 'TEXT = "fuel siphoned overnight"\n', "siphoned"),
    ("backend/assetops_backend/m.py", 'def f(n):\n    return f"{n} L stole"\n', "stole"),
    ("config/a.json", '{"lines": ["Thefts"]}\n', "Thefts"),
    ("config/b.yml", "note: someone may siphon fuel\n", "siphon"),
    ("frontend/src/sites/A.tsx", 'export const A = () => <p>Someone steals fuel</p>;\n', "steals"),
    ("frontend/src/x.ts", "export const W = 'stealing';\n", "stealing"),
    ("frontend/src/x.ts", "export const W = 'steal';\n", "steal"),
    ("frontend/src/x.ts", "export const W = 'a thief';\n", "thief"),
    ("backend/assetops_backend/m.py", 'TEXT = "the thieves came"\n', "thieves"),
    ("backend/assetops_backend/m.py", 'TEXT = "thievery"\n', "thievery"),
    ("frontend/src/sites/profiles.json", '{"labels": {"fuel": "Possible theft"}}\n', "theft"),
    ("frontend/src/sites/profiles.json", '{"stolen": "x"}\n', "stolen"),
    ("frontend/index.html", "<title>Fuel thief tracker</title>\n", "thief"),
])
def test_each_scope_fails_on_a_forbidden_word(tmp_path: Path, rel: str, text: str, word: str) -> None:
    hits, _ = fw.scan(_tree(tmp_path, {**CLEAN, rel: text}))
    assert len(hits) == 1 and hits[0].startswith(rel) and repr(word) in hits[0], hits


def test_whole_words_only(tmp_path: Path) -> None:
    hits, _ = fw.scan(_tree(tmp_path, {**CLEAN, "config/a.json": '{"t": "stolemate theftless"}\n'}))
    assert hits == []


def test_line_numbers_survive_comment_stripping() -> None:
    assert fw.ts_hits("a.tsx", "/* one\ntwo */\n// three\nconst x = 'theft';\n") == ["a.tsx:4: 'theft'"]


def test_served_hits_walks_keys_and_values() -> None:
    assert fw.served_hits({"rows": [{"text": "ok"}, {"Theft": "fine"}], "n": 1, "x": ["was stolen"]}) == [
        "Theft", "stolen"]
    assert fw.served_hits({"rows": [{"text": "Unexplained fuel"}]}) == []


def test_repository_is_clean_and_every_scope_is_scanned() -> None:
    hits, files = fw.scan()
    assert hits == [], hits
    root = fw.ROOT
    assert any(not fw._is_ts_test(p.relative_to(root).as_posix()) for p in (root / "frontend" / "src").rglob("*.tsx"))
    assert any((root / "backend" / "assetops_backend").rglob("*.py"))
    assert any((root / "config").rglob("*.json")) and any((root / "config").rglob("*.yaml"))
    assert files > 300, files
    assert (root / "frontend" / "src" / "sites" / "presentationProfiles.json").is_file()
    assert (root / "frontend" / "index.html").is_file()
    served_json = [p for p in (root / "frontend" / "src").rglob("*.json") if not fw._is_fixture(p.relative_to(root).as_posix())]
    assert served_json, "no bundled client-label JSON in scope"
