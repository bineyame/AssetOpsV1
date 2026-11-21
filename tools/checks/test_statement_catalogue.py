"""SC-1 spec section 3.8: the statement catalogue guard's rules on source strings, its run on the real tree and its
self-test (every guard plant fails with its code, N1 to N13 pass).

    python -m pytest tools/checks/test_statement_catalogue.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import statement_catalogue as guard  # noqa: E402

ROOT = HERE.parents[1]
UNSERVED = ("ValueError", "TypeError", "KeyError", "LookupError", "RuntimeError", "AssertionError",
            "NotImplementedError", "StatementError", "CatalogueError", "WireError")

#: Spec section 6, P13a to P13q, each alone in an `ADOPTED` file.
ADOPTED_PLANTS = {
    "P13": 'def f(x):\n    return f"The gap is {x}."\n',
    "P13a": 'X = "Not available"\n',
    "P13b": 'def f(xs):\n    return " ".join([x for x in xs])\n',
    "P13c": 'X = "".join(["Not ", "available"])\n',
    "P13d": 'def f(x):\n    return "a" if x else "an"\n',
    "P13e": 'import string\nT = string.Template("$x")\n',
    "P13f": 'import textwrap\ndef f(s):\n    return textwrap.fill(s)\n',
    "P13g": 'def f(x, unit):\n    return str(x) + unit\n',
    "P13h": 'def f(s):\n    s += "x"\n    return s\n',
    "P13i": 'M = {"A": "Recorded", "B": "Measured"}\n',
    "P13j": 'def f(x):\n    raise HTTPException(409, detail=f"{x}")\n',
    "P13k": 'def f(x):\n    return _refuse(409, "X", f"{x}")\n',
    "P13l": 'def f(g):\n    try:\n        g()\n    except Exception as e:\n        return dict(detail=str(e))\n',
    "P13m": 'def f(code):\n    return code.replace("_", " ")\n',
    "P13n": 'def f(code):\n    return code.capitalize()\n',
    "P13o": 'def f(x):\n    return "%s left" % x\n',
    "P13p": 'def f(x):\n    return "{} left".format(x)\n',
    "P13q": 'def f(word):\n    if word == "below":\n        return 1\n',
}
NEGATIVE = {
    "N1": 'import logging\nlogger = logging.getLogger(__name__)\ndef f(x):\n    logger.info(f"read {x} rows")\n',
    "N2": 'def f(x):\n    raise ValueError(f"bad value {x}")\n',
    "N3": 'from assetops_backend.i18n import Evidence, Money, message\n\n\ndef f(d):\n'
          '    """The headline of the deep dive."""\n'
          '    return message("deep_dive.headline", gap=Money(d, "USD", Evidence("DERIVED", "source-emulated")))\n',
}


@pytest.mark.parametrize("name", sorted(ADOPTED_PLANTS))
def test_adopted_plant_is_hand_built(name):
    hits = guard.adopted_hits("x.py", ADOPTED_PLANTS[name], UNSERVED)
    assert hits and all(h.startswith("HAND_BUILT x.py:") for h in hits), hits


@pytest.mark.parametrize("name", sorted(NEGATIVE))
def test_adopted_negative_plant_passes(name):
    assert guard.adopted_hits("x.py", NEGATIVE[name], UNSERVED) == []


def test_ratchet_rules():
    assert guard.ratchet_hits("x.py", 'def f(x):\n    return f"the gap is {x} today"\n', UNSERVED)[0][0].startswith("a:f:")
    assert guard.ratchet_hits("x.py", 'def f(p):\n    return f"SELECT id FROM site WHERE code = {p}"\n', UNSERVED) == []  # N4
    assert guard.ratchet_hits("x.py", 'import logging\nlogging.info(f"read the {x} rows")\n', UNSERVED) == []
    chrome = 'import argparse\np = argparse.ArgumentParser(description="Load the emulated exports")\n'
    assert guard.ratchet_hits("x.py", chrome, UNSERVED) == []
    rules = {f.split(":")[0] for f, _ in guard.ratchet_hits("x.py", (
        'A = "the plain words"\n'
        'B = {"x": "Recorded", "y": "Measured"}\n'
        'def g(e):\n    try:\n        pass\n    except Exception as e:\n        return str(e)\n'), UNSERVED)}
    assert rules == {"g", "i", "j"}


def test_prose():
    assert guard.prose("the gap") and guard.prose("Not available")
    assert not guard.prose("SELECT id FROM site") and not guard.prose("NOT_MATCHED") and not guard.prose("AB CD")


def test_mechanism_rules():
    import types

    schema = types.SimpleNamespace(UNSERVED=UNSERVED, TOKENS=frozenset({"money", "type"}), SYMBOLS=("", " ", "$"))
    src = ('A = "money"\nB = "$"\nC = "12.5"\nD = "less than"\nE = "MATCHED"\nF = "OTHER_CODE"\n'
           'G = f"{x:,.2f}$"\nH = f"{x} left"\n__all__ = ["Anything"]\n'
           'def f(spec):\n    if spec["type"] == "money":\n        return 1\n')
    hits = guard.mechanism_hits("m.py", src, schema, {"MATCHED"}, branch=True)
    codes = sorted((h.split()[0], h.split()[1]) for h in hits)
    assert codes == [("MECH_BRANCH", "m.py:11"), ("MECH_INSTANCE", "m.py:5"), ("MECH_LITERAL", "m.py:4"),
                     ("MECH_LITERAL", "m.py:8")]
    assert all(not h.startswith("MECH_BRANCH") for h in guard.mechanism_hits("m.py", src, schema, set(), branch=False))


def test_imports():
    rel = "backend/assetops_backend/x.py"
    assert guard.import_hits(rel, "import assetops_backend.i18n.formats\n")[0].startswith("I18N_BYPASS")
    assert guard.import_hits(rel, "from assetops_backend.i18n.catalogue import _use\n")
    assert {h.split()[0] for h in guard.import_hits(
        rel, "from assetops_backend.i18n import catalogue\ncatalogue._use(1)\n")} == {"I18N_BYPASS", "I18N_PRIVATE"}
    assert guard.import_hits(rel, "from assetops_backend.i18n import message, render\n") == []
    assert guard.import_hits(rel, "from assetops_backend.i18n.messages import CATALOGUE\n") == []
    assert guard.import_hits(rel, "from .i18n.formats import money\n")[0].startswith("I18N_BYPASS")


#: Fix round 1 (D-SC1.33, D-SC1.37): the narrowed ratchet still catches these (P57a-d) and passes the replay's code
#: strings (N5-N12), each alone in a ratchet-scope module.
NARROWED_CATCHES = {
    "P57a": ('LABELS = ("PV array",)\n', "g"),
    "P57b": ('def f(k):\n    return f"Unknown change_kind {k!r}."\n', "a"),
    "P57c": ('def f(ok):\n    return "Yes" if ok else "No"\n', "f"),
    "P57d": ('def f(day_texts):\n    return ", ".join(day_texts)\n', "e"),
    "deferred": ('def f(d):\n    return " (deferred)" if d else ""\n', "f"),
}
NARROWED_PASSES = {
    "N5": '_COLUMNS = "id, tenant_id"\nQ = text("SELECT " + _COLUMNS + " FROM structure_snapshot WHERE tenant_id = :t '
          'AND site_id IS NULL ")\n',
    "N6": 'Q = "u.id, u.tenant_id, u.file_name, u.reader, " + " FROM commercial_upload u JOIN operator_account sa ON '
          'sa.tenant_id = u.tenant_id "\n',
    "N7": 'import hashlib\ndef f(lines):\n    return hashlib.sha256("\\n".join(lines).encode("utf-8"))\n',
    "N8": 'def f(r, j, k):\n    return ("LIVE" if r else "SIMULATED", "application/json" if j else "text/csv", '
          '"keep" if k else "grant")\n',
    "N9": 'class C:\n    def f(self, n):\n        self.logger.info(f"loaded {n} rows from the file")\n',
    "N9b": 'import logging\nlogging.getLogger(__name__).warning(f"loaded {n} rows from the file")\n',
    "N10": 'ORDER = "episode_start desc nulls last, site_code_key asc"\n',
    "N11": 'def f():\n    raise ValueError("expression is not text")\n',
    "N12": 'def f(known):\n    return " AND e.recorded_at <= :k" if known else ""\n',
}


@pytest.mark.parametrize("name", sorted(NARROWED_CATCHES))
def test_narrowed_ratchet_still_catches(name):
    source, rule = NARROWED_CATCHES[name]
    assert [f.split(":")[0] for f, _ in guard.ratchet_hits("x.py", source, UNSERVED)] == [rule]


@pytest.mark.parametrize("name", sorted(NARROWED_PASSES))
def test_narrowed_ratchet_passes_code_strings(name):
    assert guard.ratchet_hits("x.py", NARROWED_PASSES[name], UNSERVED) == []


def test_prose_by_class():
    assert guard.prose("Duplicate site_id in") and guard.prose("the readings(s) are late")
    assert not guard.prose("site_id is") and not guard.prose("NOT_MATCHED x")  # identifier beside a short word: hole
    assert not guard.prose("(SELECT 1)") and not guard.prose(" AND x = 1") and not guard.prose("a, b")


def test_word_map_is_one_fingerprint_per_entry():
    one = guard.ratchet_hits("x.py", 'M = {"A": "Recorded", "B": "Measured"}\n', UNSERVED)
    two = guard.ratchet_hits("x.py", 'M = {"A": "Recorded", "B": "Measured", "C": "Shut"}\n', UNSERVED)
    assert len(one) == 2 and len(two) == 3 and set(f for f, _ in one) < set(f for f, _ in two)


def test_catalogue_templates_are_left_to_the_legacy_ratchet():
    path = f"{guard.I18N}/messages.py"
    src = 'CATALOGUE = {"en": {"a.b": "A new sentence here.", "c.d": "Recorded", "e.f": "Measured"}}\n'
    assert guard.ratchet_hits(path, src, UNSERVED) == []
    assert guard.ratchet_hits(path, src + 'def f(x):\n    return f"the message {x} is late"\n', UNSERVED)
    assert len(guard.ratchet_hits("backend/assetops_backend/other.py", src, UNSERVED)) == 3


def test_unserved_served():
    src = ('def f(g):\n    try:\n        g()\n    except PlantRefused as e:\n        return {"detail": e.args[0]}\n')
    assert guard.unserved_served("x.py", src, ("PlantRefused",)) == ["UNSERVED_SERVED x.py:5 PlantRefused"]
    quiet = ('def f(g):\n    try:\n        g()\n    except PlantRefused as e:\n        logger.info("x %s", e)\n'
             '        if isinstance(e, KeyError):\n            pass\n        raise RuntimeError("X") from e\n')
    assert guard.unserved_served("x.py", quiet, ("PlantRefused",)) == []


def test_i18n_files_are_all_classified():
    kinds = {rel.split("/i18n/")[1]: kind for rel, _, kind in guard.i18n_files(ROOT)}
    assert kinds["render.py"] == "mechanism" and kinds["messages.py"] == "legacy"
    assert kinds["statements/__init__.py"] == "marker" and kinds["statements/en/__init__.py"] == "marker"
    assert kinds["statements/en/common.py"] == "data" and "unscoped" not in kinds.values()


def test_public_surfaces_and_bypass_through_them():
    surfaces, lines = guard.public_surfaces(ROOT)
    assert lines == [] and "formats" not in surfaces["render"] and "render" in surfaces["render"]
    rel = "backend/assetops_backend/x.py"
    for src in ("from assetops_backend.i18n.render import formats\n",
                "import assetops_backend.i18n.render as r\nr.formats.money(1)\n",
                "from assetops_backend.i18n import render\nrender.formats\n",
                "import assetops_backend.i18n.render\nassetops_backend.i18n.render.schema\n",
                "from .i18n.facts import schema\n"):
        assert [h.split()[0] for h in guard.import_hits(rel, src, surfaces)] == ["I18N_BYPASS"], src
    assert guard.import_hits(rel, "from assetops_backend.i18n.render import served\n", surfaces) == []  # N13
    assert guard.import_hits(rel, "from assetops_backend.i18n import locale\nlocale.current_locale()\n", surfaces) == []


#: Review round 2, M4: the package object, however it is bound, chains into the public modules' surfaces.
PACKAGE_BYPASSES = (
    "import assetops_backend.i18n as i\ni.render.formats.money(1)\n",
    "import assetops_backend.i18n as i\ni.formats.money(1)\n",
    "from assetops_backend import i18n\ni18n.formats.money(1)\n",
    "from assetops_backend import i18n as j\nj.schema\n",
    "from . import i18n\ni18n.formats\n",
    "import assetops_backend.i18n\nassetops_backend.i18n.formats\n",
    "import assetops_backend\nassetops_backend.i18n.render.schema\n",
    "import importlib\nf = importlib.import_module(\"assetops_backend.i18n.formats\")\n",
    "__import__(\"assetops_backend.i18n.catalogue\")\n",
    "import importlib\ni = importlib.import_module(\"assetops_backend.i18n\")\ni.render.schema\n",
)
PACKAGE_PUBLIC = (
    "from assetops_backend import i18n\ni18n.message(\"a\")\ni18n.render.served(1)\ni18n.Money\n",
    "import assetops_backend.i18n as i\ni.messages.message\ni.locale.current_locale()\n",
    "from . import i18n\ni18n.served(1)\n",
    "import importlib\ni = importlib.import_module(\"assetops_backend.i18n\")\ni.served(1)\n",
)


@pytest.mark.parametrize("src", PACKAGE_BYPASSES)
def test_package_object_bypass(src):
    hits = guard.import_hits("backend/assetops_backend/x.py", src, guard.public_surfaces(ROOT)[0])
    assert [h.split()[0] for h in hits] == ["I18N_BYPASS"], hits


@pytest.mark.parametrize("src", PACKAGE_PUBLIC)
def test_package_object_public_names_pass(src):
    assert guard.import_hits("backend/assetops_backend/x.py", src, guard.public_surfaces(ROOT)[0]) == []
    assert guard.import_hits("backend/assetops_backend/x.py", "from assetops_backend import i18n\ni18n._x\n",
                             guard.public_surfaces(ROOT)[0])[0].startswith("I18N_PRIVATE")


def test_allowed_entries_print_their_source_line(tmp_path):
    """Review round 2, L7: each live allow entry is reported with its file, line and text; it still counts as
    baselined, and a stale one still fails."""
    rel = "backend/assetops_backend/x.py"
    (tmp_path / rel).parent.mkdir(parents=True)
    (tmp_path / rel).write_text("A = 1\nQ = \"select a from b\"\n", encoding="utf-8")
    hits = {rel: [("g:<module>:abc", 2)]}
    notes: list = []
    allowed, lines = guard._allow({rel: [{"fingerprint": "g:<module>:abc", "class": "SQL", "why": "a query"},
                                         {"fingerprint": "g:<module>:old", "class": "SQL", "why": "gone"}]},
                                  hits, (), tmp_path, notes)
    assert notes == [f"ALLOWED {rel}:2 SQL g:<module>:abc | Q = \"select a from b\""]
    assert allowed == {rel: guard.Counter({"g:<module>:abc": 1})} and lines == [f"ALLOW_STALE {rel} g:<module>:old"]


def test_site_tokens_hold_the_real_site_codes():
    tokens = guard.site_tokens(ROOT)
    assert {"kisiwa", "kobo"} <= tokens
    assert "site" not in tokens  # the noun key `site` must never read as a Site code


def _run(*args):
    proc = subprocess.run([sys.executable, str(HERE / "statement_catalogue.py"), *args], capture_output=True,
                          text=True, timeout=600)
    return proc.returncode, proc.stdout + proc.stderr


def test_guard_clean_on_the_real_tree():
    code, out = _run()
    assert code == 0, out


def test_guard_self_test():
    code, out = _run("--self-test")
    assert code == 0, out
    assert "FAIL" not in out
