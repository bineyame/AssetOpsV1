"""6h (`specs/6h-named-option-levers/spec.md` §10.2 test 8; D-P6.67): what is meant to stay unchanged, recorded.

`collect()` runs every test function of `test_6c_difference.py` and `test_6c_evaluate.py` in process (static checks
`test_8_*`/`test_9_*` aside) with the module names `difference` and `evaluate_options` wrapped, and records each call's
result field by field; it adds `prepare` of `generator_stop_reserve` on the Site 6a's prepare tests use (KOBO-001,
memory store). `python tests/capture_6h_parity.py` (from `backend/`) writes `tests/golden/6h_parity.json`; it was run
once, on the slice's base commit, before any 6h change. The golden is never refreshed inside the slice.
"""
from __future__ import annotations

import dataclasses
import functools
import importlib
import inspect
import json
import sys
import tempfile
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID

HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "golden" / "6h_parity.json"
MODULES = ("test_6c_difference", "test_6c_evaluate")
WRAPPED = ("difference", "evaluate_options")


def ser(obj):
    """A value as JSON, field by field: Decimals and fractions as `str`, tuples as lists, mappings as ordered pairs."""
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, (Decimal, Fraction, UUID)):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {"__type": type(obj).__name__,
                **{f.name: ser(getattr(obj, f.name)) for f in dataclasses.fields(obj)}}
    if isinstance(obj, Mapping):
        return {"__pairs": [[ser(k), ser(v)] for k, v in obj.items()]}
    if isinstance(obj, (tuple, list)):
        return [ser(v) for v in obj]
    if isinstance(obj, float):
        raise TypeError("a float in a recorded result")
    return {"__type": type(obj).__name__, "str": str(obj)}


def _param_sets(fn):
    """(id, kwargs) for each parametrize case of a test function; one empty case when it has none."""
    sets = [("", {})]
    for mark in getattr(fn, "pytestmark", ()):
        if mark.name != "parametrize":
            continue
        names = [n.strip() for n in mark.args[0].split(",")] if isinstance(mark.args[0], str) else list(mark.args[0])
        values = list(mark.args[1])
        nxt = []
        for sid, kw in sets:
            for i, v in enumerate(values):
                v = getattr(v, "values", v)  # pytest.param
                vals = v if len(names) > 1 else (v,)
                nxt.append((f"{sid}{'-' if sid else ''}{i}", {**kw, **dict(zip(names, vals))}))
        sets = nxt
    return sets


def _run_module(name: str, out: dict) -> None:
    import pytest
    module = importlib.import_module(name)
    for fname, fn in list(vars(module).items()):
        if not (fname.startswith("test_") and callable(fn)) or fname.startswith(("test_8_", "test_9_")):
            continue
        for pid, kwargs in _param_sets(fn):
            key = f"{name}::{fname}" + (f"[{pid}]" if pid else "")
            calls: list = []
            mp = pytest.MonkeyPatch()
            try:
                for wrapped in WRAPPED:
                    if hasattr(module, wrapped):
                        real = getattr(module, wrapped)

                        @functools.wraps(real)
                        def rec(*a, __real=real, __name=wrapped, **k):
                            result = __real(*a, **k)
                            calls.append({"call": __name, "result": ser(result)})
                            return result
                        mp.setattr(module, wrapped, rec)
                params = inspect.signature(fn).parameters
                with tempfile.TemporaryDirectory() as tmp:
                    for p in params:
                        if p in kwargs:
                            continue
                        if p == "tmp_path":
                            kwargs["tmp_path"] = Path(tmp)
                        elif p == "monkeypatch":
                            kwargs["monkeypatch"] = mp
                        else:
                            raise RuntimeError(f"{key}: no stand-in for the fixture {p!r}")
                    fn(**kwargs)
            finally:
                mp.undo()
            if calls:
                out[key] = calls


def _prepare(out: dict) -> None:
    """6a's prepare of `generator_stop_reserve` on KOBO-001 (test_6a_decisions.World), memory store."""
    import pytest
    from assetops_backend.accounts import passwords
    from test_3c0a_accounts_service import PW
    mp = pytest.MonkeyPatch()
    try:
        stored = passwords.hash_password(PW)
        mp.setattr(passwords, "hash_password", lambda _pw: stored)
        t6a = importlib.import_module("test_6a_decisions")
        got = t6a.World().prepare()
        out["test_6a_decisions::prepare[KOBO-001]"] = [{"call": "prepare", "result": {
            "options": [[o.option_key, o.position, ser(o.settings), o.generator] for o in got.options],
            "decision": ser(dataclasses.replace(got.decision, site_id=UUID(int=0), tenant_id=UUID(int=0),
                                                    prepared_by_person_id=UUID(int=0)))}}]
    finally:
        mp.undo()


def collect() -> dict:
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    out: dict = {}
    for name in MODULES:
        _run_module(name, out)
    _prepare(out)
    return out


def dump(data: dict) -> str:
    return "{\n" + ",\n".join(f"{json.dumps(k)}: {json.dumps(data[k], sort_keys=True)}" for k in sorted(data)) + "\n}\n"


if __name__ == "__main__":
    GOLDEN.parent.mkdir(exist_ok=True)
    GOLDEN.write_text(dump(collect()))
    print(f"wrote {GOLDEN} ({len(json.loads(GOLDEN.read_text()))} cases)")
