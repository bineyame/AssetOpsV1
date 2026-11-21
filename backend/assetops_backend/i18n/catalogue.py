"""SC-1 (spec section 3.7; D-SC1.3, D-SC1.20, D-SC1.21, D-SC1.22): load, merge and prove the catalogue.

Loading merges `messages.CATALOGUE` (legacy strings, untouched) with every `statements/<locale>/*.py` module into the
catalogue `render` reads, then validates it. Any failure raises `CatalogueError(code, key, detail)` at import, so a
bad catalogue never serves. Tests build catalogues only through `_build(statements, vocabulary)`, this same
validator, and install one with `_use(cat)`; `render` and `served` take no catalogue (D-SC1.22).
"""
from __future__ import annotations

import ast
import itertools
import pkgutil
import string
import unicodedata
from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator

from assetops_backend.i18n import conditions, schema
from assetops_backend.i18n.facts import BY_TYPE, FIGURES, is_lower_snake, is_upper_snake
from assetops_backend.i18n.messages import CATALOGUE as LEGACY

_FIGURE_TYPES = tuple(t for t, cls in BY_TYPE.items() if cls in FIGURES)
_FACT_TYPES = tuple(BY_TYPE)
_STATEMENT_FIELDS = ("slots", "variants", "exhaustive", "evidence", "rephrase", "part_only")
_VARIANT_FIELDS = ("id", "when", "requires", "options", "text")
_SLOT_FIELDS = ("type", "absent", "optional")
_FORMS = ("label", "in_sentence", "article", "one", "other", "symbol")
_EVIDENCE_TABLES = ("by_evidence_first", "by_origin", "no_origin", "observed_by_evidence", "money_suffix")
_OPTIONAL_STRUCTURAL = ("evidence", "domain")
_INLINE, _WITH, _DERIVED = schema.OPTIONS["money"]["evidence"]
#: D-SC1.21: the percent signs refused besides category `Sc` (U+0025, U+2030, U+2031, U+066A, U+FE6A, U+FF05).
_PERCENTS = frozenset("%" + chr(0x2030) + chr(0x2031) + chr(0x066A) + chr(0xFE6A) + chr(0xFF05))
#: The only digits a vocabulary word may hold: superscript two and three, in the `unit` vocabulary's `symbol`.
_SUPERSCRIPTS = frozenset(chr(0xB2) + chr(0xB3))
_MAX_DEPTH = 4


class CatalogueError(ValueError):
    """A catalogue that cannot load: `code` (section 3.7), the statement `key`, a `detail` (a slot, variant, path or
    value; never prose)."""

    def __init__(self, code: str, key=None, detail=None):
        super().__init__(code, key, detail)
        self.code, self.key, self.detail = code, key, detail


class StatementError(ValueError):
    """A message that cannot be rendered truthfully (section 3.6): codes only. There is no fallback text."""

    def __init__(self, code: str, key=None, variant=None, slot=None):
        super().__init__(code, key, variant, slot)
        self.code, self.key, self.variant, self.slot = code, key, variant, slot


class Catalogue:
    """A proved catalogue: legacy templates, structured statements and vocabulary per locale, and each statement's
    tree of slots (its own and those of every part it reaches)."""

    def __init__(self, legacy: dict, statements: dict, vocabulary: dict, trees: dict):
        self.legacy, self.statements, self.vocabulary, self.trees = legacy, statements, vocabulary, trees


# --- reading modules (NOT_DATA, KEY_DUPLICATE) ---------------------------------------------------------------------


def _dict_duplicates(node: ast.AST, path: tuple = ()) -> None:
    if isinstance(node, ast.Dict):
        seen = set()
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant):
                if k.value in seen:
                    raise CatalogueError("KEY_DUPLICATE", path[0] if path else k.value,
                                         ".".join(str(p) for p in (*path, k.value)))
                seen.add(k.value)
            _dict_duplicates(v, (*path, k.value) if isinstance(k, ast.Constant) else path)
    elif isinstance(node, (ast.List, ast.Tuple)):
        for i, v in enumerate(node.elts):
            _dict_duplicates(v, (*path, i))


def read_module(source: str, name: str) -> dict:
    """The literal of a statements (`STATEMENTS`) or vocabulary (`VOCABULARY`) module: its body is an optional
    docstring and one assignment whose value `ast.literal_eval` accepts."""
    try:
        body = ast.parse(source).body
    except SyntaxError:
        raise CatalogueError("NOT_DATA", None, name) from None
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    if len(body) != 1 or not isinstance(body[0], ast.Assign) or len(body[0].targets) != 1 \
            or not isinstance(body[0].targets[0], ast.Name) or body[0].targets[0].id != name:
        raise CatalogueError("NOT_DATA", None, name)
    try:
        value = ast.literal_eval(body[0].value)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        raise CatalogueError("NOT_DATA", None, name) from None
    if not isinstance(value, dict):
        raise CatalogueError("NOT_DATA", None, name)
    _dict_duplicates(body[0].value)
    return value


def _modules(value, name: str) -> list[dict]:
    if isinstance(value, (str, dict)):
        value = [value]
    return [read_module(m, name) if isinstance(m, str) else m for m in value]


# --- literals (LITERAL_DIGIT, LITERAL_SYMBOL, LITERAL_NUMBER_WORD) -------------------------------------------------


def _words(text: str) -> Iterator[str]:
    for is_word, run in itertools.groupby(text, key=str.isalpha):
        if is_word:
            yield "".join(run)


def check_literal(text, locale: str, key=None, detail=None, *, superscripts: bool = False) -> None:
    if not isinstance(text, str):
        raise CatalogueError("NOT_DATA", key, detail)
    for c in text:
        if unicodedata.category(c)[0] == "N" and not (superscripts and c in _SUPERSCRIPTS):
            raise CatalogueError("LITERAL_DIGIT", key, detail)
    for c in text:
        if unicodedata.category(c).upper() == "SC" or c in _PERCENTS:
            raise CatalogueError("LITERAL_SYMBOL", key, detail)
    banned = schema.NUMBER_WORDS[locale]
    for w in _words(text):
        if w.casefold() in banned:
            raise CatalogueError("LITERAL_NUMBER_WORD", key, detail)


# --- vocabulary (VOCABULARY_FORM, VOCABULARY_SCHEMA) ---------------------------------------------------------------


def _check_evidence_table(table, locale: str) -> None:
    def fail(detail):
        raise CatalogueError("VOCABULARY_SCHEMA", "evidence", detail)

    if not isinstance(table, dict) or set(table) != set(_EVIDENCE_TABLES):
        fail(None)
    first, by_origin, observed = (table["by_evidence_first"], table["by_origin"], table["observed_by_evidence"])
    if not all(isinstance(t, dict) for t in (first, by_origin, observed)):
        fail(None)
    if set(first) & set(observed) or set(first) | set(observed) != set(schema.EVIDENCES):
        fail("by_evidence_first")
    observed_origins = set(schema.ORIGIN_ORDER[:3])
    if set(by_origin) & observed_origins or set(by_origin) | observed_origins != set(schema.ORIGINS):
        fail("by_origin")
    words = [*first.values(), *by_origin.values(), *observed.values(), table["no_origin"], table["money_suffix"]]
    for w in words:
        check_literal(w, locale, "evidence", None)
        if any(part.upper() == "VERIFIED" for part in _words(w)):
            fail(w)


#: Forms each vocabulary the formats read must declare.
_REQUIRED_FORMS = {"format": ("in_sentence",), "unit": ("symbol",), "noun": ("one", "other"), "month": ("label",)}


def _check_vocabulary(vocab, locale: str) -> None:
    if not isinstance(vocab, dict) or not set(schema.FORMAT_VOCABULARIES) <= set(vocab):
        raise CatalogueError("VOCABULARY_SCHEMA", None, locale)
    for name, v in vocab.items():
        if name == "evidence":
            _check_evidence_table(v, locale)
            continue
        if not isinstance(v, dict) or set(v) != {"forms", "order", "entries"}:
            raise CatalogueError("VOCABULARY_SCHEMA", name, None)
        forms, order, entries = v["forms"], v["order"], v["entries"]
        if not isinstance(forms, list) or not forms or len(set(forms)) != len(forms) or not set(forms) <= set(_FORMS):
            raise CatalogueError("VOCABULARY_SCHEMA", name, "forms")
        if not set(_REQUIRED_FORMS.get(name, ())) <= set(forms):
            raise CatalogueError("VOCABULARY_SCHEMA", name, "forms")
        if not isinstance(entries, dict) or not entries or not isinstance(order, list) \
                or len(set(order)) != len(order) or set(order) != set(entries):
            raise CatalogueError("VOCABULARY_SCHEMA", name, "order")
        for key, entry in entries.items():
            if not isinstance(entry, dict) or set(entry) != set(forms):
                raise CatalogueError("VOCABULARY_FORM", name, key)
            for form, w in entry.items():
                check_literal(w, locale, name, key, superscripts=(name, form) == ("unit", "symbol"))
    if set(vocab["format"]["entries"]) != set(schema.FORMAT_WORDS):
        raise CatalogueError("VOCABULARY_SCHEMA", "format", None)
    if len(vocab["month"]["entries"]) != 12:
        raise CatalogueError("VOCABULARY_SCHEMA", "month", None)


# --- slots (SLOT_TYPE, SLOT_OPTION) --------------------------------------------------------------------------------


def _display_options(kind: str) -> dict:
    return {n: a for n, a in schema.OPTIONS[kind].items() if a and n != "evidence"}


def _allowed(value, allowed: tuple) -> bool:
    for a in allowed:
        if a is int:
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return True
        elif type(value) is type(a) and value == a:
            return True
    return False


def _check_codes(codes) -> bool:
    return isinstance(codes, list) and bool(codes) and len(set(codes)) == len(codes) and all(
        is_upper_snake(c) for c in codes)


def _check_slot(key: str, name: str, spec, mode: str, vocab: dict, *, nested: bool = False) -> None:
    def fail(code="SLOT_OPTION", detail=name):
        raise CatalogueError(code, key, detail)

    if not isinstance(spec, dict) or spec.get("type") not in schema.TYPES:
        fail("SLOT_TYPE")
    kind = spec["type"]
    opts = schema.OPTIONS[kind]
    takes_fact = kind in _FACT_TYPES
    for field in spec:
        if field not in _SLOT_FIELDS and field not in opts:
            fail()
    for opt, allowed in _display_options(kind).items():
        if opt in spec and not _allowed(spec[opt], allowed):
            fail()
    for opt, allowed in opts.items():
        if not allowed and opt not in _OPTIONAL_STRUCTURAL and opt not in spec:
            fail()
    if "absent" in spec and (not takes_fact or nested or not _check_codes(spec["absent"])):
        fail()
    if "optional" in spec and (not takes_fact or nested or not isinstance(spec["optional"], bool)):
        fail()
    if kind in _FIGURE_TYPES:
        if nested:
            fail()
        if mode == "served":
            if "evidence" in spec:
                fail()
        elif "evidence" not in spec:
            fail("EVIDENCE_UNSHOWN")
        else:
            ev = spec["evidence"]
            if not (ev == _INLINE or (isinstance(ev, dict) and len(ev) == 1 and (
                    isinstance(ev.get(_WITH), str)
                    or (isinstance(ev.get(_DERIVED), list) and ev[_DERIVED]
                        and all(isinstance(s, str) for s in ev[_DERIVED]))))):
                fail()
    _STRUCTURE[kind](key, name, spec, mode, vocab, fail)


def _word_structure(key, name, spec, mode, vocab, fail):
    v = vocab.get(spec["vocabulary"]) if isinstance(spec["vocabulary"], str) else None
    if not isinstance(v, dict) or "forms" not in v:
        fail()
    if spec.get("form", "label") not in v["forms"] or (spec.get("article") and "article" not in v["forms"]):
        fail()


def _items_structure(key, name, spec, mode, vocab, fail):
    of = spec["of"]
    if not isinstance(of, dict) or of.get("type") not in _FACT_TYPES or of.get("type") in ("items", "state", "flag"):
        fail()
    _check_slot(key, name, of, mode, vocab, nested=True)
    if spec.get("order") == "vocabulary" and of["type"] != "word":
        fail()


def _evidence_structure(key, name, spec, mode, vocab, fail):
    of = spec["of"]
    if mode == "served" or not isinstance(of, list) or not of or len(set(of)) != len(of) \
            or not all(isinstance(s, str) for s in of):
        fail()


def _pick_structure(key, name, spec, mode, vocab, fail):
    on, words = spec["on"], spec["words"]
    if not (isinstance(on, str) or (isinstance(on, dict) and len(on) == 1 and isinstance(on.get("sign"), str))):
        fail()
    if not isinstance(words, dict) or not words or not all(isinstance(w, str) for w in words.values()):
        fail()
    if "domain" in spec and not (isinstance(spec["domain"], list) and spec["domain"]
                                 and len(set(spec["domain"])) == len(spec["domain"])):
        fail()


def _state_structure(key, name, spec, mode, vocab, fail):
    if not _check_codes(spec["values"]):
        fail()


def _string_option(option):
    def check(key, name, spec, mode, vocab, fail):
        if not isinstance(spec[option], str) or not spec[option]:
            fail()
    return check


def _no_structure(key, name, spec, mode, vocab, fail):
    return None


_STRUCTURE = {kind: _no_structure for kind in schema.TYPES}
_STRUCTURE.update({"word": _word_structure, "items": _items_structure, "evidence": _evidence_structure,
                   "pick": _pick_structure, "state": _state_structure, "part": _string_option("key"),
                   "example": _string_option("text")})


# --- one statement -------------------------------------------------------------------------------------------------


def fields(text: str) -> list[tuple[str, str | None]]:
    """(literal, field) pairs of a template already proved by `_check_template`."""
    return [(lit, f) for lit, f, _, _ in string.Formatter().parse(text)]


def _check_template(key: str, vid: str, text, slots: dict, locale: str) -> None:
    if not isinstance(text, str):
        raise CatalogueError("NOT_DATA", key, vid)
    try:
        parsed = list(string.Formatter().parse(text))
    except ValueError:
        raise CatalogueError("FIELD_FORM", key, vid) from None
    for literal, field, spec, conversion in parsed:
        check_literal(literal, locale, key, vid)
        if "{" in literal or "}" in literal:
            raise CatalogueError("FIELD_FORM", key, vid)
        if field is None:
            continue
        if spec or conversion is not None or not field.isidentifier():
            raise CatalogueError("FIELD_FORM", key, vid)
        if field not in slots:
            raise CatalogueError("FIELD_UNDECLARED", key, field)
        if slots[field]["type"] in ("state", "flag"):
            raise CatalogueError("STATE_PRINTED", key, field)


def _check_statement(key: str, st, locale: str, vocab: dict) -> None:
    if not isinstance(st, dict) or not set(st) <= set(_STATEMENT_FIELDS) or "variants" not in st:
        raise CatalogueError("NOT_DATA", key, None)
    parts = key.split(".")
    if len(parts) != 2 or not all(is_lower_snake(p) for p in parts):
        raise CatalogueError("KEY_FORM", key, None)
    if st.get("rephrase", "never") not in schema.REPHRASE or not isinstance(st.get("part_only", False), bool):
        raise CatalogueError("REPHRASE", key, None)
    mode = st.get("evidence", "inline")
    if mode not in schema.MODES:
        raise CatalogueError("EVIDENCE_MODE", key, None)
    slots = st.get("slots", {})
    if not isinstance(slots, dict):
        raise CatalogueError("NOT_DATA", key, None)
    for name, spec in slots.items():
        if not isinstance(name, str) or not is_lower_snake(name):
            raise CatalogueError("SLOT_TYPE", key, name)
        _check_slot(key, name, spec, mode, vocab)
        if spec["type"] == "pick":
            for w in spec["words"].values():
                check_literal(w, locale, key, name)
    variants = st["variants"]
    if not isinstance(variants, list) or not variants:
        raise CatalogueError("NOT_DATA", key, None)
    seen = set()
    for i, v in enumerate(variants):
        if not isinstance(v, dict) or not set(v) <= set(_VARIANT_FIELDS) or "text" not in v:
            raise CatalogueError("NOT_DATA", key, i)
        vid = v.get("id")
        if not is_lower_snake(vid) or vid in seen or ("when" not in v and i != len(variants) - 1):
            raise CatalogueError("VARIANT_ID", key, vid)
        seen.add(vid)
        _check_template(key, vid, v["text"], slots, locale)


def _check_choice(key: str, st: dict) -> None:
    """A fallback (a last variant without `when`) or a proved exhaustive set; run once the conditions are proved."""
    if "exhaustive" in st:
        _check_exhaustive(key, st, st.get("slots", {}))
    elif "when" in st["variants"][-1]:
        raise CatalogueError("NO_FALLBACK", key, st["variants"][-1]["id"])


def _is_values(cond, slot: str) -> list | None:
    """The values an exhaustive variant's `when` selects (`is` on the slot, or `any` of such), else None."""
    if isinstance(cond, dict) and len(cond) == 1:
        (op, args), = cond.items()
        if op == "is" and isinstance(args, list) and len(args) == 2 and args[0] == slot:
            return [args[1]]
        if op == "any" and isinstance(args, list) and args:
            out = [_is_values(c, slot) for c in args]
            return None if None in out else [x for o in out for x in o]
    return None


def _check_exhaustive(key: str, st: dict, slots: dict) -> None:
    slot = st["exhaustive"]
    spec = slots.get(slot) if isinstance(slot, str) else None
    if spec is None or spec["type"] != "state" or "absent" in spec or spec.get("optional"):
        raise CatalogueError("NOT_EXHAUSTIVE", key, slot)
    covered: set = set()
    for v in st["variants"]:
        values = _is_values(v.get("when"), slot)
        if values is None:
            raise CatalogueError("NOT_EXHAUSTIVE", key, v["id"])
        covered.update(values)
    missing = set(spec["values"]) - covered
    if missing:
        raise CatalogueError("NOT_EXHAUSTIVE", key, sorted(missing)[0])


# --- trees (PART_UNKNOWN, PART_CYCLE, SLOT_CONFLICT, EVIDENCE_MODE) ------------------------------------------------


def _part_keys(st: dict) -> list[str]:
    return [s["key"] for s in st.get("slots", {}).values() if s["type"] == "part"]


def _tree(key: str, stmts: dict, path: tuple = ()) -> dict:
    if key in path or len(path) > _MAX_DEPTH:
        raise CatalogueError("PART_CYCLE", path[0] if path else key, key)
    st = stmts[key]
    mode = st.get("evidence", "inline")
    tree = dict(st.get("slots", {}))
    for part in _part_keys(st):
        if part not in stmts:
            raise CatalogueError("PART_UNKNOWN", key, part)
        if stmts[part].get("evidence", "inline") != mode:
            raise CatalogueError("EVIDENCE_MODE", key, part)
        for name, spec in _tree(part, stmts, (*path, key)).items():
            if name in tree and tree[name] != spec:
                raise CatalogueError("SLOT_CONFLICT", key, name)
            tree[name] = spec
    return tree


# --- conditions (CONDITION_OPERATOR, CONDITION_SLOT, CONDITION_VALUE) ---------------------------------------------


def _check_operand(key, operand, tree) -> None:
    if isinstance(operand, str):
        base, suffix = conditions.split_path(operand)
        spec = tree.get(base)
        if spec is None or spec["type"] not in _FACT_TYPES:
            raise CatalogueError("CONDITION_SLOT", key, operand)
        if suffix is None:
            if spec["type"] not in (*_FIGURE_TYPES, "count"):
                raise CatalogueError("CONDITION_SLOT", key, operand)
        elif suffix not in BY_TYPE[spec["type"]]._paths:
            raise CatalogueError("CONDITION_SLOT", key, operand)
        return
    if not isinstance(operand, dict) or len(operand) != 1:
        raise CatalogueError("CONDITION_OPERATOR", key, None)
    if conditions.ABS in operand:
        _check_operand(key, operand[conditions.ABS], tree)
        return
    if conditions.CONST not in operand:
        raise CatalogueError("CONDITION_OPERATOR", key, None)
    raw = operand[conditions.CONST]
    if isinstance(raw, bool) or not isinstance(raw, (int, str)):
        raise CatalogueError("CONDITION_VALUE", key, raw)
    if isinstance(raw, str):
        try:
            if not Decimal(raw).is_finite():
                raise InvalidOperation
        except InvalidOperation:
            raise CatalogueError("CONDITION_VALUE", key, raw) from None


def _slot_of(key, args, tree, types=None):
    if not isinstance(args, list) or len(args) != 2 or not isinstance(args[0], str):
        raise CatalogueError("CONDITION_OPERATOR", key, None)
    spec = tree.get(args[0])
    if spec is None or spec["type"] not in (types or _FACT_TYPES):
        raise CatalogueError("CONDITION_SLOT", key, args[0])
    return spec


def _check_condition(key: str, cond, tree: dict) -> None:
    if not isinstance(cond, dict) or len(cond) != 1:
        raise CatalogueError("CONDITION_OPERATOR", key, None)
    (op, args), = cond.items()
    if op not in schema.OPERATORS:
        raise CatalogueError("CONDITION_OPERATOR", key, op)
    _CONDITION_CHECKS[op](key, args, tree)


def _c_presence(key, args, tree):
    if not isinstance(args, str) or args not in tree or tree[args]["type"] not in _FACT_TYPES:
        raise CatalogueError("CONDITION_SLOT", key, args)


def _c_reason(key, args, tree):
    spec = _slot_of(key, args, tree)
    allowed = list(spec.get("absent", [])) + ["OMITTED"] * bool(spec.get("optional"))
    if args[1] not in allowed:
        raise CatalogueError("CONDITION_VALUE", key, args[1])


def _c_is(key, args, tree):
    spec = _slot_of(key, args, tree, ("state", "flag"))
    value = args[1]
    ok = isinstance(value, bool) if spec["type"] == "flag" else (isinstance(value, str) and value in spec["values"])
    if not ok:
        raise CatalogueError("CONDITION_VALUE", key, value)


def _c_sign(key, args, tree):
    _slot_of(key, args, tree, _FIGURE_TYPES)
    if args[1] not in schema.SIGNS:
        raise CatalogueError("CONDITION_VALUE", key, args[1])


def _c_cmp(key, args, tree):
    if not isinstance(args, list) or len(args) != 3:
        raise CatalogueError("CONDITION_OPERATOR", key, None)
    left, comparator, right = args
    if comparator not in schema.COMPARATORS:
        raise CatalogueError("CONDITION_OPERATOR", key, comparator)
    _check_operand(key, left, tree)
    _check_operand(key, right, tree)
    if conditions.operand_slot(left) is None and conditions.operand_slot(right) is None:
        raise CatalogueError("CONDITION_OPERATOR", key, None)


def _c_list(key, args, tree):
    if not isinstance(args, list) or not args:
        raise CatalogueError("CONDITION_OPERATOR", key, None)
    for c in args:
        _check_condition(key, c, tree)


_CONDITION_CHECKS = {"present": _c_presence, "absent": _c_presence, "reason": _c_reason, "is": _c_is,
                     "sign": _c_sign, "cmp": _c_cmp, "all": _c_list, "any": _c_list,
                     "not": lambda key, args, tree: _check_condition(key, args, tree)}


def condition_slots(cond) -> list[str]:
    """Every slot a (proved) condition reads."""
    if cond is None:
        return []
    (op, args), = cond.items()
    if op in ("all", "any"):
        return [s for c in args for s in condition_slots(c)]
    if op == "not":
        return condition_slots(args)
    if op in ("present", "absent"):
        return [args]
    if op == "cmp":
        return [s for s in (conditions.operand_slot(args[0]), conditions.operand_slot(args[2])) if s is not None]
    return [args[0]]


# --- the tree's references, renderings, PICK_REACH and EVIDENCE_UNSHOWN ---------------------------------------------


def _check_references(key: str, tree: dict) -> None:
    figures = {n for n, s in tree.items() if s["type"] in _FIGURE_TYPES}
    for name, spec in tree.items():
        kind = spec["type"]
        if kind == "evidence" and not set(spec["of"]) <= figures:
            raise CatalogueError("SLOT_OPTION", key, name)
        ev = spec.get("evidence") if kind in _FIGURE_TYPES else None
        if isinstance(ev, dict) and _WITH in ev:
            target = tree.get(ev[_WITH])
            if target is None or target["type"] != "evidence" or name not in target["of"]:
                raise CatalogueError("SLOT_OPTION", key, name)
        if isinstance(ev, dict) and _DERIVED in ev and not set(ev[_DERIVED]) <= figures - {name}:
            raise CatalogueError("SLOT_OPTION", key, name)
        if kind == "pick":
            _check_pick(key, name, spec, tree)


def pick_domain(spec: dict, tree: dict) -> tuple[str, list]:
    """(the slot a pick reads, its domain)."""
    on = spec["on"]
    if isinstance(on, str):
        return on, spec.get("domain", tree[on]["values"])
    return on["sign"], spec.get("domain", list(schema.SIGNS))


def _check_pick(key: str, name: str, spec: dict, tree: dict) -> None:
    on = spec["on"]
    if isinstance(on, str):
        target = tree.get(on)
        if target is None or target["type"] != "state":
            raise CatalogueError("SLOT_OPTION", key, name)
        universe = target["values"]
    else:
        target = tree.get(on["sign"])
        if target is None or target["type"] not in _FIGURE_TYPES:
            raise CatalogueError("SLOT_OPTION", key, name)
        universe = list(schema.SIGNS)
    _, domain = pick_domain(spec, tree)
    if not set(domain) <= set(universe):
        raise CatalogueError("SLOT_OPTION", key, name)
    if set(spec["words"]) != set(domain):
        raise CatalogueError("PICK_INCOMPLETE", key, name)


def _variant_conditions(st: dict) -> Iterator[tuple[dict, list]]:
    """Each variant with its own path condition: its `when` and `requires`, and `not when` of every earlier one."""
    earlier: list = []
    for v in st["variants"]:
        conds = [c for c in (v.get("when"), v.get("requires")) if c is not None]
        yield v, [*({"not": w} for w in earlier), *conds]
        if "when" in v:
            earlier.append(v["when"])


class _Node:
    """One chosen variant in a rendering, with its chain's path condition."""

    def __init__(self, key: str, variant: dict, chain: list):
        self.key, self.variant, self.chain = key, variant, chain


def renderings(key: str, stmts: dict, chain: tuple = ()) -> Iterator[list[_Node]]:
    """Every combination of chosen variants from `key` down through the parts each chosen variant prints."""
    st = stmts[key]
    slots = st.get("slots", {})
    for v, conds in _variant_conditions(st):
        node = _Node(key, v, [*chain, *conds])
        part_lists = [list(renderings(slots[f]["key"], stmts, tuple(node.chain)))
                      for _, f in fields(v["text"]) if f is not None and slots[f]["type"] == "part"]
        for combo in itertools.product(*part_lists):
            yield [node, *(n for nodes in combo for n in nodes)]


def _check_reach(key: str, rendering: list[_Node], stmts: dict, tree: dict) -> None:
    for node in rendering:
        slots = stmts[node.key].get("slots", {})
        for _, f in fields(node.variant["text"]):
            if f is None or slots[f]["type"] != "pick":
                continue
            x, domain = pick_domain(slots[f], tree)
            target = tree[x]
            universe = list(target["values"]) if target["type"] == "state" else list(schema.SIGNS)
            if "absent" in target or target.get("optional"):
                universe.append(None)
            for value in universe:
                if value in domain:
                    continue
                result = conditions.kleene({"all": node.chain} if node.chain else None, x, value)
                if result is not False:
                    raise CatalogueError("PICK_REACH", key, (node.key, node.variant["id"], f,
                                                             "ABSENT" if value is None else value))


def _check_shown(key: str, rendering: list[_Node], stmts: dict, tree: dict) -> None:
    printed: set = set()
    stated: set = set()
    for node in rendering:
        slots = stmts[node.key].get("slots", {})
        for _, f in fields(node.variant["text"]):
            if f is None:
                continue
            printed.add(f)
            if slots[f]["type"] == "pick":
                stated.add(pick_domain(slots[f], tree)[0])
        for c in (node.variant.get("when"), node.variant.get("requires")):
            stated.update(condition_slots(c))
    stated |= printed
    figures = [n for n in stated if tree.get(n, {}).get("type") in _FIGURE_TYPES]

    def shown(name: str, seen: frozenset) -> bool:
        ev = tree[name].get("evidence")
        if ev == _INLINE:
            return name in printed
        if _WITH in ev:
            return ev[_WITH] in printed
        return all(i in stated and i not in seen and shown(i, seen | {name}) for i in ev[_DERIVED])

    for name in sorted(figures):
        if not shown(name, frozenset()):
            raise CatalogueError("EVIDENCE_UNSHOWN", key, (rendering[0].variant["id"], name))


# --- build ---------------------------------------------------------------------------------------------------------


def _check_locales(statements: dict, vocabulary: dict) -> None:
    english = statements["en"]
    for locale, stmts in statements.items():
        if locale not in schema.NUMBER_WORDS or locale not in vocabulary:
            raise CatalogueError("LOCALE_INCOMPLETE", None, locale)
        if locale == "en":
            continue
        if set(stmts) != set(english):
            raise CatalogueError("LOCALE_INCOMPLETE", sorted(set(english) ^ set(stmts))[0], locale)
        for key, st in stmts.items():
            if _shape(st) != _shape(english[key]):
                raise CatalogueError("LOCALE_INCOMPLETE", key, locale)


def _shape(st) -> tuple:
    if not isinstance(st, dict):
        return ()
    slots = st.get("slots", {})
    return ([v.get("id") for v in st.get("variants", []) if isinstance(v, dict)],
            {n: s.get("type") for n, s in slots.items() if isinstance(s, dict)} if isinstance(slots, dict) else {},
            st.get("evidence", "inline"))


def _build(statements: dict, vocabulary: dict, legacy: dict | None = None) -> Catalogue:
    """Prove and assemble a catalogue. `statements`: locale -> one module or a list of modules, each a dict or
    the module's source; `vocabulary`: locale -> a dict or a vocabulary module's source."""
    legacy = LEGACY if legacy is None else legacy
    merged: dict = {}
    for locale, modules in statements.items():
        merged[locale] = {}
        for module in _modules(modules, "STATEMENTS"):
            for key, st in module.items():
                if key in merged[locale] or key in legacy.get("en", {}) or key in legacy.get(locale, {}):
                    raise CatalogueError("KEY_DUPLICATE", key, locale)
                merged[locale][key] = st
    merged.setdefault("en", {})
    vocab = {locale: _modules(v, "VOCABULARY")[0] for locale, v in vocabulary.items()}
    _check_locales(merged, vocab)
    trees: dict = {}
    for locale, stmts in merged.items():
        _check_vocabulary(vocab[locale], locale)
        for key, st in stmts.items():
            _check_statement(key, st, locale, vocab[locale])
        trees[locale] = {}
        for key, st in stmts.items():
            tree = trees[locale][key] = _tree(key, stmts)
            for v in st["variants"]:
                for c in (v.get("when"), v.get("requires")):
                    if c is not None:
                        _check_condition(key, c, tree)
                for slot, opts in v.get("options", {}).items():
                    _check_variant_options(key, slot, opts, tree)
            _check_choice(key, st)
        for key, st in stmts.items():
            if st.get("part_only"):
                continue
            tree = trees[locale][key]
            _check_references(key, tree)
            for rendering in renderings(key, stmts):
                _check_reach(key, rendering, stmts, tree)
                if st.get("evidence", "inline") == "inline":
                    _check_shown(key, rendering, stmts, tree)
    return Catalogue(legacy, merged, vocab, trees)


def _check_variant_options(key: str, slot, opts, tree: dict) -> None:
    spec = tree.get(slot)
    if spec is None or not isinstance(opts, dict):
        raise CatalogueError("SLOT_OPTION", key, slot)
    display = _display_options(spec["type"])
    for opt, value in opts.items():
        if opt not in display or not _allowed(value, display[opt]):
            raise CatalogueError("SLOT_OPTION", key, slot)


def _sources(folder: Path) -> Iterator[tuple[str, str]]:
    for info in pkgutil.iter_modules([str(folder)]):
        if not info.ispkg:
            origin = info.module_finder.find_spec(info.name).origin
            yield info.name, Path(origin).read_text(encoding="utf-8")


def _load() -> Catalogue:
    root = Path(__file__).resolve().parent / "statements"
    statements: dict = {}
    vocabulary: dict = {}
    for info in pkgutil.iter_modules([str(root)]):
        if not info.ispkg:
            continue
        statements[info.name] = []
        for name, source in _sources(root / info.name):
            if name == "vocabulary":
                vocabulary[info.name] = source
            else:
                statements[info.name].append(source)
    return _build(statements, vocabulary)


_LOADED = _load()
_CURRENT: ContextVar[Catalogue] = ContextVar("statements", default=_LOADED)


def current() -> Catalogue:
    return _CURRENT.get()


@contextmanager
def _use(cat: Catalogue) -> Iterator[Catalogue]:
    """Tests only: render through `cat` (built by `_build`) inside the block."""
    token = _CURRENT.set(cat)
    try:
        yield cat
    finally:
        _CURRENT.reset(token)
