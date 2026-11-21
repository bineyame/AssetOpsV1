"""SC-1 spec section 3.8: the statement catalogue guard's rules on source strings, its run on the real tree and its
self-test (every guard plant fails with its code, N1 to N4 pass).

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
