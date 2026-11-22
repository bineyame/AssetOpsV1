#!/usr/bin/env python3
"""Independent model of the Layer 4 structure specification (design-pack checker input).

Written from `structure-specification.md` (rev 13) and `demo-site-scenario-manifest.yaml` alone.
It does not read or import any other program of the design pack.

Interface: compute(manifest_path) -> dict  (see the specification and the checker for the paths).
Python 3 standard library plus PyYAML.

SPEC AMBIGUITIES (each decided from the specification's wording and the manifest; listed for review)
 A1  Vertical key. Tenant `vertical: EV_DEPOT` has no `structures` entry; the structures, bounds, protect
     nodes, forward baseline and option detail are declared under `EV_DEPOT_CAPTIVE`. A vertical that is not a
     key is mapped to the unique key that starts with it.
 A2  Context `tenant` (§2.3) is the tenant's record (mapping), because `factor_map.COLD_CHAIN.capacity_crate_days`
     reads `tenant.capacity_crates_per_room`. Context `site` is the site's name, so `prices.x[site]` indexes by it.
     A bracket index that is a name (`[site]`) is evaluated as an expression.
 A3  Leaves (§3) are evaluated with context paths only (no node, factor or parameter lookup); node, change,
     cost-line, bound and parameter expressions use the full order parameter -> node -> factor -> context.
 A4  `period_end` for a side is the record's own `period_end` when present, else `evaluation.period_end`.
     Options use the actual side, so their `period_end` is `evaluation.period_end`.
 A5  Not-decomposed status string is exactly "not decomposed: stated total"; the stated total is the record's
     `contribution`, else its `total`.
 A6  Portfolio sums (§3) are taken over structure nodes only (leaves are not summed). The not-decomposed form is
     {"sums": {"outcome_total_with_stated_totals": Σ stated totals of ALL the tenant's sites}, "not_decomposed": [...]},
     reading "the tenant's total is the sum of the stated totals" literally (for metro-bus plan this is the
     sum of the three `total` records).
 A7  november_to_date portfolio side: composed over the sites that have that side; omitted for a tenant
     where no site has it. Sites without the side are not listed as not decomposed.
 A8  Operations measure without a denominator: the per-site figure is the numerator (rounded to `decimals`),
     the portfolio figure is Σ numerators; no `numerator`/`denominator` sub-dicts are emitted for it.
 A9  Sensitivity `factors` overrides (§5.3, §5.8) are applied to the reference as well (for both a
     `reference_option` and the baseline reference): "with the same overrides". Sensitivity `params` overrides
     apply to the option only (a reference option keeps its own parameters).
 A10 `reference_factors` are applied before the option's parameters are resolved; parameters are resolved over
     the baseline factors after `reference_factors`.
 A11 Parameter phases: all non-restore parameters that do not read `restore_date`, in declared order; then the
     restore date (its `plus` items may name parameters declared after it); then `days_to_restore` and
     `value_days_to_restore`; then the parameters that read `restore_date`, in declared order.
 A12 `performed_under` is tested against the right's state under the option (after set/void/lapse rules).
 A13 `value_days_to_restore` with a restore date = (min(restore, value_horizon_end + 1 day) - as_of) days.
 A14 Right identity is its `asset` string, global across sites (deciders are keyed by it). A right missing
     `cover_value` has cover 0. A LAPSED right gets eligibility "LAPSED" (so it is no longer covered).
 A15 An option whose crew visits are unknown makes any combination that contains it infeasible (never defaulted).
 A16 Valued-decision candidates: every option of the decision has an evaluable value, so candidates are the
     options with hard violation 0 (or all, under fallback); only valued-in-money options add to the plan value.
 A17 A switch-sensitivity replaces the value only of options that declare that sensitivity; valued-in-money
     status is unchanged.
 A18 RESOLVED by the spec (§6.4 amended): case keys join the values with "/", booleans written True/False,
     numbers as written (5000). (Still decided here: `requires_switch` and `by_if_switch` need the switch to be
     literally true in the case.)
 A19 RESOLVED by the spec (§6.4 amended): switch-sensitivity values (the case with that switch value and every
     other switch at its first value) are reported under the sensitivity's name in `sensitivity_values`, and the
     downside is the minimum of the downside drops, sensitivity values and switch-sensitivity values. `downside` is
     a number (null only if there is nothing to take the minimum of); drop values are under `downside_drops`.
 A20 RESOLVED by the spec (§6.3 amended): `not_valued_in_money` = spend - valued option costs, a money figure;
     spend = Σ operator one-off of the items.
 A21 `value_if_admissible` follows the brief: the option's value when valued in money, else null (regardless of
     its admissibility, which is reported separately under `admissible`).
 A22 Infeasible case: value, spend, crew_visits_used, valued_option_costs and not_valued_in_money null; items []
     (and not_valued_in_money_items []); protective_choices {}.
 A23 A combination's total violation counts only decisions on their fallback; a decision is on its fallback when
     none of its (non-excluded) options has hard violation 0 and it declares `fallback: least_violation`.
 A24 Owner-question variant changes are null when either the variant's or the applied variant's figure is null.
 A26 (§4.2 amended) When the `if_not_covered` replacement applies and declares `crew_visits` (value or
     {value, basis}), it replaces the option's crew visits (option field and row alike). It is evaluated as an
     expression in the option's final environment. Under the normal (covered) state nothing changes. The EV bill-line
     nodes (peak_cost, offpeak_cost, night_cost, demand_cost) are read generically from `structures`; they are
     reported with every evaluated side's nodes and summed in the portfolio like any other node.
 A25 (§3 amended) Not-decomposed `cost_per_departure_required` = the stated total / Σ departures_required, emitted
     only when every site record of that side states `departures_required` (summed over those records).
"""

import ast
import copy
import datetime as dt
import itertools
import re
import sys
from collections import OrderedDict
from decimal import Decimal, getcontext, ROUND_HALF_EVEN, ROUND_CEILING, ROUND_FLOOR, InvalidOperation

import yaml

getcontext().prec = 50

ZERO = Decimal(0)
ONE = Decimal(1)
CENT = Decimal("0.01")


# --------------------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------------------
class Unresolved(Exception):
    pass


class NotAvailable:
    """N1 (0K4m spec §2.2, R4): a value that is not available, carrying its record words. It is its own value, never a
    missing record: `|` falls through only on Unresolved, never on this. Arithmetic on it gives it back (so sums and
    differences stay not available); comparisons and truth tests are not defined and fail loudly."""
    __slots__ = ("words",)

    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return "NotAvailable(%r)" % (self.words,)

    def _same(self, *_):
        return self

    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = _same
    __neg__ = __pos__ = _same

    def __bool__(self):
        raise TypeError("a not-available value has no truth value")


def is_na(v):
    return isinstance(v, NotAvailable)


def first_na(*vals):
    for v in vals:
        if isinstance(v, NotAvailable):
            return v
    return None


def D(x):
    if isinstance(x, Decimal):
        return x
    if isinstance(x, NotAvailable):
        raise TypeError("a not-available value reached a number conversion: %r" % (x,))
    if isinstance(x, bool) or x is None:
        raise Unresolved("not a number: %r" % (x,))
    if isinstance(x, int):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(repr(x))
    raise Unresolved("not a number: %r" % (x,))


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v[:10])
        except ValueError:
            raise Unresolved("not a date: %r" % v)
    raise Unresolved("not a date: %r" % (v,))


def add_business_days(d, n):
    n = int(n)
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def r2(x):
    if x is None or is_na(x):
        return None
    return float(D(x).quantize(CENT, rounding=ROUND_HALF_EVEN))


def rdec(x, decimals):
    if is_na(x):
        return None
    q = Decimal(1).scaleb(-int(decimals))
    return float(D(x).quantize(q, rounding=ROUND_HALF_EVEN))


def iso(d):
    return d.isoformat() if d is not None else None


def fmt_switch(v):
    return str(v)   # §6.4: booleans True/False, numbers as written


def is_true(v):
    return v is True


# --------------------------------------------------------------------------------------------------------------
# expression language (§2.4)
# --------------------------------------------------------------------------------------------------------------
_PARSE_CACHE = {}


def _parse(expr):
    t = _PARSE_CACHE.get(expr)
    if t is None:
        t = ast.parse(expr.strip(), mode="eval")
        _PARSE_CACHE[expr] = t
    return t


def _fn_min(*a):
    return min(D(x) for x in a)


def _fn_max(*a):
    return max(D(x) for x in a)


def _fn_ceil(x):
    return D(x).to_integral_value(rounding=ROUND_CEILING)


def _fn_floor(x):
    return D(x).to_integral_value(rounding=ROUND_FLOOR)


def _fn_days_incl(a, b):
    return Decimal((to_date(b) - to_date(a)).days + 1)


def _fn_days_between(a, b):
    return Decimal((to_date(b) - to_date(a)).days)


def _fn_nights_listed(lst, frm, to=None):
    if not isinstance(lst, list):
        raise Unresolved("nights_listed: not a list")
    f = to_date(frm)
    t = to_date(to) if to is not None else None
    n = 0
    for x in lst:
        d = to_date(x)
        if d >= f and (t is None or d < t):
            n += 1
    return Decimal(n)


FUNCS = {"min": _fn_min, "max": _fn_max, "ceil": _fn_ceil, "floor": _fn_floor,
         "days_incl": _fn_days_incl, "days_between": _fn_days_between, "nights_listed": _fn_nights_listed}


def _ev_or(node, resolve):
    """(value, None) or (None, Unresolved): both operands of an operator are evaluated, so a not-available operand wins
    over a missing record whichever side it is on (N1: the node is not available when it reads a not-available value)."""
    try:
        return _ev(node, resolve), None
    except Unresolved as e:
        return None, e


def _operands(nodes, resolve):
    vals, err = [], None
    for n in nodes:
        v, e = _ev_or(n, resolve)
        vals.append(v)
        if e is not None and err is None:
            err = e
    na = first_na(*vals)
    if na is not None:
        return na, None
    if err is not None:
        raise err
    return None, vals


def _ev(node, resolve):
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            raise Unresolved("bool constant")
        if isinstance(v, (int, float)):
            return D(v)
        return v
    if isinstance(node, ast.Name):
        return resolve(node.id)
    if isinstance(node, ast.Attribute):
        base = _ev(node.value, resolve)
        if is_na(base):
            return base
        if isinstance(base, dict) and node.attr in base and base[node.attr] is not None:
            return base[node.attr]
        raise Unresolved("missing attribute %s" % node.attr)
    if isinstance(node, ast.Subscript):
        base = _ev(node.value, resolve)
        sl = node.slice
        if hasattr(ast, "Index") and isinstance(sl, getattr(ast, "Index")):  # pragma: no cover (py<3.9)
            sl = sl.value
        idx = _ev(sl, resolve)
        na = first_na(base, idx)
        if na is not None:
            return na
        if isinstance(base, list):
            try:
                i = int(D(idx))
            except (Unresolved, InvalidOperation):
                raise Unresolved("bad list index")
            if 0 <= i < len(base) and base[i] is not None:
                return base[i]
            raise Unresolved("index out of range")
        if isinstance(base, dict):
            key = idx
            if isinstance(key, Decimal):
                key = int(key)
            if key in base and base[key] is not None:
                return base[key]
            raise Unresolved("missing key %r" % (key,))
        raise Unresolved("not subscriptable")
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.BitOr):   # R4: the right side runs only on a missing record, never on not available
            try:
                return _ev(node.left, resolve)
            except Unresolved:
                return _ev(node.right, resolve)
        na, vals = _operands((node.left, node.right), resolve)
        if na is not None:
            return na
        a, b = D(vals[0]), D(vals[1])
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            if b == 0:
                raise Unresolved("division by zero")
            return a / b
        raise ValueError("operator not allowed")
    if isinstance(node, ast.UnaryOp):
        v = _ev(node.operand, resolve)
        if is_na(v):
            return v
        v = D(v)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return v
        raise ValueError("unary operator not allowed")
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "unavailable":   # I6: reserved, matched before FUNCS
            a = node.args
            if node.keywords or len(a) != 1 or not isinstance(a[0], ast.Constant) or not isinstance(a[0].value, str) \
                    or not a[0].value.strip():
                raise ValueError("unavailable() takes exactly one non-empty string of record words")
            return NotAvailable(a[0].value)
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCS or node.keywords:
            raise ValueError("function not allowed")
        if any(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in node.args):
            raise ValueError("a string argument is legal only in unavailable()")
        na, args = _operands(node.args, resolve)
        if na is not None:
            return na
        return FUNCS[node.func.id](*args)
    raise ValueError("expression element not allowed: %s" % type(node).__name__)


def evaluate(expr, resolve):
    """Raw value (number as Decimal, or a record value) of an expression or a literal."""
    if expr is None:
        raise Unresolved("null")
    if isinstance(expr, bool):
        raise Unresolved("bool")
    if isinstance(expr, (int, float, Decimal)):
        return D(expr)
    if isinstance(expr, str):
        return _ev(_parse(expr).body, resolve)
    raise Unresolved("not an expression: %r" % (expr,))


def evaluate_num(expr, resolve):
    v = evaluate(expr, resolve)
    return v if is_na(v) else D(v)


class Env:
    """Name resolution: option parameter -> structure node -> factor -> context path (§2.4)."""

    def __init__(self, ctx, structure=None, factors=None, params=None, extra_nodes=None):
        self.ctx = ctx
        self.structure = structure or {}
        self.factors = factors or {}
        self.params = params or {}
        self.extra_nodes = extra_nodes or {}
        self._memo = {}
        self._busy = set()

    def node(self, name):
        if name in self._memo:
            return self._memo[name]
        if name in self._busy:
            raise ValueError("cyclic node %s" % name)
        self._busy.add(name)
        try:
            v = evaluate_num(self.structure[name], self.resolve)
        finally:
            self._busy.discard(name)
        self._memo[name] = v
        return v

    def resolve(self, name):
        if name in self.params:
            return self.params[name]
        if name in self.structure:
            return self.node(name)
        if name in self.extra_nodes:
            return self.extra_nodes[name]
        if name in self.factors:
            return self.factors[name]
        if name in self.ctx:
            v = self.ctx[name]
            if v is None and name != "restore_date":
                raise Unresolved("context %s is null" % name)
            return v
        raise Unresolved("unknown name %s" % name)

    def all_nodes(self):
        return OrderedDict((n, self.node(n)) for n in self.structure)


def ctx_resolver(ctx):
    def r(name):
        if name in ctx and ctx[name] is not None:
            return ctx[name]
        raise Unresolved("unknown name %s" % name)
    return r


# --------------------------------------------------------------------------------------------------------------
# rights (§4.1)
# --------------------------------------------------------------------------------------------------------------
COVERED_ELIG = "POTENTIALLY_COVERED"
NOT_COVERED_CLAIMS = {"DENIED", "REJECTED"}
NOTIFIED_CLAIMS = {"NOTIFIED", "ACKNOWLEDGED", "ACCEPTED", "DENIED", "REJECTED"}


def right_covered(st):
    return st["eligibility"] == COVERED_ELIG and st["claim_state"] not in NOT_COVERED_CLAIMS


def right_notified(st):
    return st["claim_state"] in NOTIFIED_CLAIMS


def rights_nodes(state, lost):
    claimable = sum((st["cover"] for st in state.values() if right_covered(st)), ZERO)
    unclaimable = sum((st["cover"] for st in state.values() if st["eligibility"] == "INSUFFICIENT_EVIDENCE"), ZERO)
    return OrderedDict([("claimable_cover", claimable), ("unclaimable_cover", unclaimable),
                        ("cover_lost", lost), ("cover_not_claimable", unclaimable + lost)])


# --------------------------------------------------------------------------------------------------------------
# patches (§6.5)
# --------------------------------------------------------------------------------------------------------------
_SEG = re.compile(r"\[([^\]]+)\]|([^.\[\]]+)")


def _path_segments(path):
    segs = []
    for m in _SEG.finditer(path):
        if m.group(1) is not None:
            k, v = m.group(1).split("=", 1)
            segs.append(("filter", k.strip(), v.strip()))
        else:
            segs.append(("key", m.group(2)))
    return segs


def _step(obj, seg):
    if seg[0] == "key":
        return obj[seg[1]]
    for item in obj:
        if isinstance(item, dict) and str(item.get(seg[1])) == seg[2]:
            return item
    raise KeyError("no item %s=%s" % (seg[1], seg[2]))


def apply_patch(doc, patch):
    for op in patch or []:
        segs = _path_segments(op["path"])
        parent = doc
        for s in segs[:-1]:
            parent = _step(parent, s)
        last = segs[-1]
        if "set" in op:
            if last[0] == "key":
                parent[last[1]] = op["set"]
            else:
                raise ValueError("cannot set a filtered item")
        if "remove" in op:
            target = _step(parent, last)
            if isinstance(target, list):
                if op["remove"] in target:
                    target.remove(op["remove"])
            elif isinstance(target, dict):
                target.pop(op["remove"], None)
    return doc


# --------------------------------------------------------------------------------------------------------------
# the model
# --------------------------------------------------------------------------------------------------------------
class Model:
    def __init__(self, m):
        self.m = m
        self.ev = m["evaluation"]
        self.as_of = to_date(m["as_of"])
        self.period_days = D(self.ev["period_days"])
        self.period_end = to_date(self.ev["period_end"])
        self.horizon_end = to_date(self.ev["horizon_end"])
        self.structures = m["structures"]
        self.factor_map = m["factor_map"]
        self.tenants = OrderedDict((t["tenant"], t) for t in m["tenants"])
        self.site_index = OrderedDict()   # site name -> (tenant id, tenant, site)
        for tid, t in self.tenants.items():
            for s in t["sites"]:
                self.site_index[s["site"]] = (tid, t, s)
        self.value_horizon_end = {tid: self._value_horizon(t) for tid, t in self.tenants.items()}
        self.plans_decl = m.get("plans", {}) or {}
        self._site_sides = {}
        self._baseline = {}
        self._runs = {}
        self._site_rights_cache = {}
        self.deciders = self._deciders()

    # ---- time -------------------------------------------------------------------------------------------------
    def _value_horizon(self, t):
        months = int(t["portfolio_constraints"]["horizon_months"])
        a = self.as_of
        if months % 12 == 0:
            end = a.replace(year=a.year + months // 12)
        else:
            y, mo = divmod(a.month - 1 + months, 12)
            end = a.replace(year=a.year + y, month=mo + 1)
        return end - dt.timedelta(days=1)

    # ---- vertical ---------------------------------------------------------------------------------------------
    def vkey(self, tenant):
        v = tenant["vertical"]
        if v in self.structures:
            return v
        cands = [k for k in self.structures if k.startswith(v)]
        if len(cands) != 1:
            raise ValueError("cannot map vertical %s" % v)
        return cands[0]

    # ---- contexts ---------------------------------------------------------------------------------------------
    def side_records(self, site):
        out = OrderedDict()
        period = site.get("period") or {}
        obs = site.get("observations") or {}
        if "plan" in period:
            out["plan"] = dict(period["plan"])
        if "actual" in period:
            rec = dict(period["actual"])
            rec.update(obs.get("october") or {})
            out["actual"] = rec
        if obs.get("november_to_date") is not None:
            out["november_to_date"] = dict(obs["november_to_date"])
        return out

    def base_ctx(self, tenant, site, record):
        pe = to_date(record["period_end"]) if record.get("period_end") is not None else self.period_end
        ctx = {
            "record": record,
            "prices": tenant.get("prices"),
            "energy_model": tenant.get("energy_model"),
            "physical": site.get("physical"),
            "tariff": site.get("tariff"),
            "incident": site.get("incident"),
            "entitlement": site.get("entitlement"),
            "observations": site.get("observations"),
            "tenant": tenant,
            "site": site["site"],
            "as_of": self.as_of,
            "period_days": self.period_days,
            "period_end": pe,
        }
        return {k: v for k, v in ctx.items() if v is not None}

    def leaf_exprs(self, V, site):
        exprs = OrderedDict(self.factor_map[V])
        for k, v in (site.get("factor_sources") or {}).items():
            exprs[k] = v
        return exprs

    def eval_leaves(self, V, site, ctx):
        res = ctx_resolver(ctx)
        leaves, missing = OrderedDict(), []
        for name, expr in self.leaf_exprs(V, site).items():
            try:
                leaves[name] = evaluate_num(expr, res)
            except Unresolved:
                missing.append(name)
        return leaves, missing

    # ---- §3 sites ---------------------------------------------------------------------------------------------
    def site_sides(self, sname):
        if sname in self._site_sides:
            return self._site_sides[sname]
        tid, t, s = self.site_index[sname]
        V = self.vkey(t)
        out = OrderedDict()
        for side, rec in self.side_records(s).items():
            ctx = self.base_ctx(t, s, rec)
            leaves, missing = self.eval_leaves(V, s, ctx)
            nodes = None
            if not missing:
                try:
                    nodes = Env(ctx, self.structures[V], leaves).all_nodes()
                except Unresolved:
                    nodes = None
            if nodes is None:
                stated = rec.get("contribution", rec.get("total"))
                out[side] = {"status": "not decomposed: stated total", "stated_total": D(stated) if stated is not None else None,
                             "missing": missing}
            else:
                allv = OrderedDict(nodes)
                for k, v in leaves.items():
                    allv[k] = v
                out[side] = {"status": "evaluated", "nodes": allv, "struct_nodes": nodes, "leaves": leaves}
        self._site_sides[sname] = out
        return out

    # ---- rights -----------------------------------------------------------------------------------------------
    def site_rights(self, site):
        rights = []
        if isinstance(site.get("entitlement"), dict):
            rights.append(site["entitlement"])
        for e in site.get("entitlements") or []:
            rights.append(e)
        inc = site.get("incident") or {}
        if isinstance(inc.get("entitlement"), dict):
            rights.append(inc["entitlement"])
        return rights

    def rights_at_as_of(self, site):
        key = site["site"]
        if key in self._site_rights_cache:
            return copy.deepcopy(self._site_rights_cache[key])
        state = OrderedDict()
        for r in self.site_rights(site):
            st = {"eligibility": r.get("eligibility"), "claim_state": r.get("claim_state"),
                  "cover": D(r["cover_value"]) if r.get("cover_value") is not None else ZERO,
                  "notice_deadline": to_date(r["notice_deadline"]) if r.get("notice_deadline") is not None else None}
            if right_covered(st) and not right_notified(st) and st["notice_deadline"] is not None and st["notice_deadline"] < self.as_of:
                st["eligibility"] = "LAPSED"
            state[r["asset"]] = st
        self._site_rights_cache[key] = state
        return copy.deepcopy(state)

    def _touched_rights(self, spec):
        out = set()
        for cl in (spec.get("cost_lines") or {}).values():
            if isinstance(cl, dict) and cl.get("covered_by"):
                out.add(cl["covered_by"])
        rest = (spec.get("params") or {}).get("restore")
        if isinstance(rest, dict) and rest.get("performed_under"):
            out.add(rest["performed_under"])
        for r in spec.get("voids_rights") or []:
            out.add(r)
        for r in (spec.get("set_rights") or {}):
            out.add(r)
        for r in (spec.get("files_notice") or {}):
            out.add(r)
        return out

    def _deciders(self):
        dec = {}
        touch = {}
        for oid, spec in (self.ev.get("options") or {}).items():
            for r in self._touched_rights(spec):
                touch.setdefault(r, set()).add(oid)
                dec.setdefault(r, set()).add(oid)
        for plan in self.plans_decl.values():
            for d in plan.get("decisions") or []:
                opts = d.get("options") or []
                for r, touching in touch.items():
                    if any(o in touching for o in opts):
                        dec[r].update(opts)
        return dec

    # ---- option rows ------------------------------------------------------------------------------------------
    def find_row(self, site, oid):
        lists = []
        if isinstance(site.get("decision"), dict):
            lists.append(site["decision"].get("options") or [])
        if isinstance(site.get("entitlement"), dict):
            lists.append(site["entitlement"].get("options") or [])
        for e in site.get("entitlements") or []:
            lists.append(e.get("options") or [])
        for lst in lists:
            for row in lst:
                if isinstance(row, dict) and row.get("id") == oid:
                    return row
        return None

    # ---- §5 options -------------------------------------------------------------------------------------------
    def option_setup(self, oid):
        spec = self.ev["options"][oid]
        tid, t, s = self.site_index[spec["site"]]
        V = self.vkey(t)
        return spec, tid, t, s, V

    def baseline(self, sname):
        """Actual leaves after the forward-baseline resets (§5.1)."""
        if sname in self._baseline:
            return self._baseline[sname]
        tid, t, s = self.site_index[sname]
        V = self.vkey(t)
        sides = self.site_sides(sname)
        act = sides.get("actual")
        if act is None or act["status"] != "evaluated":
            raise ValueError("site %s actual side not evaluated; options cannot start from it" % sname)
        rec = self.side_records(s)["actual"]
        ctx = self.base_ctx(t, s, rec)
        leaves = OrderedDict(act["leaves"])
        res = ctx_resolver(ctx)
        for leaf, expr in ((self.ev.get("forward_baseline") or {}).get(V) or {}).items():
            leaves[leaf] = evaluate_num(expr, res)
        self._baseline[sname] = (leaves, ctx)
        return self._baseline[sname]

    def date_spec(self, spec, env):
        if spec is None:
            return None
        d = spec.get("date")
        if d is None or d == "none":
            return None
        if d == "as_of":
            base = self.as_of
        else:
            base = to_date(evaluate(d, env.resolve))
        for p in spec.get("plus") or []:
            base = base + dt.timedelta(days=int(evaluate_num(p, env.resolve)))
        if spec.get("business_days") is not None:
            base = add_business_days(base, int(evaluate_num(spec["business_days"], env.resolve)))
        return base

    def _apply_overrides(self, factors, overrides, ctx, V, params, extra_nodes):
        for name, expr in (overrides or {}).items():
            env = Env(ctx, self.structures[V], factors, params, extra_nodes)
            factors[name] = evaluate_num(expr, env.resolve)

    def run_option(self, oid, param_over=None, factor_over=None):
        key = (oid, tuple(sorted((param_over or {}).items(), key=lambda kv: kv[0])) if param_over else (),
               tuple((factor_over or {}).items()))
        key = (oid, repr(param_over), repr(factor_over))
        if key in self._runs:
            return self._runs[key]
        spec, tid, t, s, V = self.option_setup(oid)
        base_leaves, base_ctx = self.baseline(s["site"])
        row = self.find_row(s, oid)
        ctx = dict(base_ctx)
        if row is not None:
            ctx["row"] = row
        ctx["restore_date"] = None
        factors = OrderedDict(base_leaves)
        structure = self.structures[V]

        # rights (§4.1), in order: set, void, lapse
        state = self.rights_at_as_of(s)
        lost = ZERO
        for r, elig in (spec.get("set_rights") or {}).items():
            if r in state:
                state[r]["eligibility"] = elig
        for r in spec.get("voids_rights") or []:
            if r in state:
                if right_covered(state[r]):
                    lost += state[r]["cover"]
                state[r]["eligibility"] = "VOIDED"
        notice_env = Env(ctx)
        for r, st in state.items():
            if (right_covered(st) and not right_notified(st) and st["notice_deadline"] is not None
                    and oid in self.deciders.get(r, set())):
                fn = (spec.get("files_notice") or {}).get(r)
                filed = self.date_spec(fn, notice_env) if fn else None
                if filed is None or filed > st["notice_deadline"]:
                    st["eligibility"] = "LAPSED"
                    lost += st["cover"]
        rnodes = rights_nodes(state, lost)

        # reference factors (§5.3)
        for name, expr in (spec.get("reference_factors") or {}).items():
            env = Env(ctx, structure, factors, {}, rnodes)
            factors[name] = evaluate_num(expr, env.resolve)

        # parameters (§4.2 order)
        pspecs = OrderedDict(spec.get("params") or {})
        for k, v in (param_over or {}).items():
            pspecs[k] = v
        params = OrderedDict()

        def pexpr(ps):
            return ps.get("value") if isinstance(ps, dict) else ps

        def reads_restore(ps):
            e = pexpr(ps)
            return isinstance(e, str) and re.search(r"\brestore_date\b", e) is not None

        deferred = []
        for name, ps in pspecs.items():
            if name == "restore":
                continue
            if reads_restore(ps):
                deferred.append(name)
                continue
            env = Env(ctx, structure, factors, params, rnodes)
            params[name] = evaluate_num(pexpr(ps), env.resolve)
        restore_date = None
        crew_override = None
        has_restore = "restore" in pspecs
        if has_restore:
            rs = pspecs["restore"]
            env = Env(ctx, structure, factors, params, rnodes)
            pu = rs.get("performed_under")
            use = rs
            if pu is not None:
                st = state.get(pu)
                if st is None or not right_covered(st):
                    use = rs.get("if_not_covered")
                    if isinstance(use, dict) and use.get("crew_visits") is not None:
                        crew_override = use["crew_visits"]   # §4.2 (amended), A26
            restore_date = self.date_spec(use, env) if use is not None else None
            ctx["restore_date"] = restore_date
            vend = self.value_horizon_end[tid]
            if restore_date is not None:
                dtr = (min(restore_date, self.horizon_end + dt.timedelta(days=1)) - self.as_of).days
                vdtr = (min(restore_date, vend + dt.timedelta(days=1)) - self.as_of).days
            else:
                dtr = (self.horizon_end - self.as_of).days + 1
                vdtr = (vend - self.as_of).days + 1
            params["days_to_restore"] = Decimal(dtr)
            params["value_days_to_restore"] = Decimal(vdtr)
        for name in deferred:
            env = Env(ctx, structure, factors, params, rnodes)
            params[name] = evaluate_num(pexpr(pspecs[name]), env.resolve)

        # changes, then sensitivity factor overrides (§5.3)
        for name, expr in (spec.get("changes") or {}).items():
            env = Env(ctx, structure, factors, params, rnodes)
            factors[name] = evaluate_num(expr, env.resolve)
        self._apply_overrides(factors, factor_over, ctx, V, params, rnodes)

        env = Env(ctx, structure, factors, params, rnodes)
        nodes = env.all_nodes()
        for k, v in rnodes.items():
            nodes[k] = v

        # cost lines (§5.4)
        cost_lines = OrderedDict()
        one_off = ZERO
        for name, cl in (spec.get("cost_lines") or {}).items():
            if isinstance(cl, dict):
                amt = evaluate_num(cl.get("amount"), env.resolve)
                cb = cl.get("covered_by")
            else:
                amt = evaluate_num(cl, env.resolve)
                cb = None
            share = 0 if (cb is not None and cb in state and right_covered(state[cb])) else 1
            cost_lines[name] = (amt, share)
            one_off += amt * share

        run = {"oid": oid, "tid": tid, "site": s, "V": V, "spec": spec, "row": row, "ctx": ctx,
               "factors": factors, "params": params, "nodes": nodes, "env": env,
               "restore_date": restore_date, "has_restore": has_restore, "crew_override": crew_override,
               "cost_lines": cost_lines, "one_off": one_off, "rights": state, "rights_nodes": rnodes}
        self._runs[key] = run
        return run

    def reference_run(self, oid, factor_over=None):
        spec, tid, t, s, V = self.option_setup(oid)
        if spec.get("reference_option"):
            r = self.run_option(spec["reference_option"], None, factor_over)
            return {"nodes": r["nodes"], "factors": r["factors"], "one_off": r["one_off"], "rights_nodes": r["rights_nodes"]}
        base_leaves, base_ctx = self.baseline(s["site"])
        ctx = dict(base_ctx)
        row = self.find_row(s, oid)
        if row is not None:
            ctx["row"] = row
        ctx["restore_date"] = None
        factors = OrderedDict(base_leaves)
        rnodes = rights_nodes(self.rights_at_as_of(s), ZERO)
        for name, expr in (spec.get("reference_factors") or {}).items():
            env = Env(ctx, self.structures[V], factors, {}, rnodes)
            factors[name] = evaluate_num(expr, env.resolve)
        self._apply_overrides(factors, factor_over, ctx, V, {}, rnodes)
        env = Env(ctx, self.structures[V], factors, {}, rnodes)
        nodes = env.all_nodes()
        for k, v in rnodes.items():
            nodes[k] = v
        return {"nodes": nodes, "factors": factors, "one_off": ZERO, "rights_nodes": rnodes}

    @staticmethod
    def _lookup(run, name):
        if name in run["nodes"]:
            return run["nodes"][name]
        if name in run["factors"]:
            return run["factors"][name]
        return None

    def option_value_parts(self, oid, param_over=None, factor_over=None):
        spec = self.ev["options"][oid]
        run = self.run_option(oid, param_over, factor_over)
        ref = self.reference_run(oid, factor_over)
        months = D(spec.get("months", 1))
        delta = run["nodes"]["contribution"] - ref["nodes"]["contribution"]
        value = delta * months - (run["one_off"] - ref["one_off"])
        return run, ref, delta, months, value

    def evaluate_option(self, oid):
        spec, tid, t, s, V = self.option_setup(oid)
        run, ref, delta, months, value = self.option_value_parts(oid)
        # N1: the option is not available when a param, its value, or a bound over its nodes is; the words are the first
        # not-available param's (in params order), else the value's, else the first such bound's
        na = first_na(*run["params"].values(), value)

        violations = OrderedDict()
        for b in (self.ev.get("bounds") or {}).get(V) or []:
            val = self._lookup(run, b["node"])
            if val is None:
                continue
            limit = evaluate_num(b["max"], run["env"].resolve)
            bna = first_na(val, limit)
            if bna is not None:   # neither passes nor fails: no violation is recorded (null), and the option is not available
                violations[b["id"]] = None
                na = na if na is not None else bna
                continue
            violations[b["id"]] = max(val - limit, ZERO)
        valued = (na is None) and (delta != 0) and not spec.get("comparator") and not spec.get("is_reference")

        cv = spec.get("crew_visits")
        if run["crew_override"] is not None:
            cv = run["crew_override"]
        crew = None
        if cv is not None:
            e = cv.get("value") if isinstance(cv, dict) else cv
            crew = int(evaluate_num(e, run["env"].resolve))
        elif run["row"] is not None and run["row"].get("crew_visits") is not None:
            crew = int(D(run["row"]["crew_visits"]))

        sens = OrderedDict()
        for name, sv in (spec.get("sensitivities") or {}).items():
            _, _, _, _, sval = self.option_value_parts(oid, sv.get("params"), sv.get("factors"))
            sens[name] = sval

        rr = None
        rq = spec.get("requires_restore")
        if rq:
            res = run["env"].resolve
            rr = {"decision": rq["decision"],
                  "plus_business_days": int(evaluate_num(rq.get("plus_business_days", 0), res)),
                  "by": to_date(evaluate(rq["by"], res)),
                  "by_if_switch": OrderedDict((k, to_date(evaluate(v, res))) for k, v in (rq.get("by_if_switch") or {}).items())}

        pn = (self.ev.get("protect_nodes") or {}).get(V) or []
        out = OrderedDict()
        out["site"] = s["site"]
        out["tenant"] = tid
        out["monthly_or_horizon_change"] = r2(delta)
        out["months"] = int(months)
        out["operator_one_off"] = r2(run["one_off"])
        out["reference_one_off"] = r2(ref["one_off"])
        out["net_one_off"] = r2(run["one_off"] - ref["one_off"])
        out["value"] = None if na is not None else r2(value)
        out["value_if_admissible"] = r2(value) if valued else None
        out["money_changes"] = False if na is not None else bool(delta != 0)
        out["valued_in_money"] = bool(valued)
        if na is not None:
            out["not_available"] = na.words
        out["crew_visits"] = crew
        out["restore_date"] = iso(run["restore_date"])
        out["protect"] = OrderedDict((n, r2(self._lookup(run, n))) for n in pn)
        out["reference_protect"] = OrderedDict((n, r2(self._lookup(ref, n))) for n in pn)
        out["rights"] = OrderedDict((k, r2(run["rights_nodes"][k])) for k in ("claimable_cover", "unclaimable_cover", "cover_lost"))
        out["right_states"] = OrderedDict((a, st["eligibility"]) for a, st in run["rights"].items())
        out["lapsed_rights"] = [a for a, st in run["rights"].items() if st["eligibility"] == "LAPSED"]
        out["violations"] = OrderedDict((k, r2(v)) for k, v in violations.items())
        out["params"] = OrderedDict((k, rdec(v, 6)) for k, v in run["params"].items())
        out["cost_lines"] = OrderedDict((k, {"amount": r2(a), "operator_share": sh}) for k, (a, sh) in run["cost_lines"].items())
        if sens:
            out["sensitivities"] = OrderedDict((k, None if out["value"] is None else r2(v)) for k, v in sens.items())
        od = (self.ev.get("option_detail") or {}).get(V)
        if od:
            if od.get("capacity"):
                out["bound"] = OrderedDict((n, r2(self._lookup(run, n))) for n in od["capacity"])
            for k, n in (od.get("option_nodes") or {}).items():
                out[k] = r2(self._lookup(run, n))
            for k, n in (od.get("reference_nodes") or {}).items():
                out[k] = r2(self._lookup(ref, n))
        # N3: information copied verbatim; N4: replay_sources, the sorted study ids its params and information read
        if "information" in spec:
            out["information"] = copy.deepcopy(spec["information"])
        studies = {ps["source"]["study"] for ps in (spec.get("params") or {}).values()
                   if isinstance(ps, dict) and isinstance(ps.get("source"), dict) and "study" in ps["source"]}
        info_src = (spec.get("information") or {}).get("source") if isinstance(spec.get("information"), dict) else None
        if isinstance(info_src, dict) and "study" in info_src:
            studies.add(info_src["study"])
        out["replay_sources"] = sorted(studies)
        internal = {"na": na, "value": value, "valued": valued, "one_off": run["one_off"], "crew": crew,
                    "violations": violations, "restore_date": run["restore_date"], "sens": sens,
                    "requires_restore": rr, "requires_switch": spec.get("requires_switch")}
        return out, internal

    # ---- §6 plans ---------------------------------------------------------------------------------------------
    def decision_of(self):
        out = {}
        for tid, plan in self.plans_decl.items():
            for d in plan.get("decisions") or []:
                for o in d.get("options") or []:
                    out[o] = d
        return out

    def solve(self, tid, sw, opt, exclude=frozenset(), value_over=None):
        plan = self.plans_decl[tid]
        t = self.tenants[tid]
        budget = D(sw["budget"]) if "budget" in sw else D(plan["budget"])
        crew_limit = int(D(t["portfolio_constraints"][plan["crew_limit"]]))

        def oval(o):
            if value_over and o in value_over:
                return value_over[o]
            return opt[o]["value"]

        decs, choices = [], []
        for d in plan.get("decisions") or []:
            kind = d.get("kind")
            if kind == "comparator":
                continue
            opts = [o for o in d.get("options") or [] if o not in exclude and opt[o]["na"] is None]   # N1: never chosen
            hard = d.get("hard") or []
            hv = {o: sum((opt[o]["violations"].get(b, ZERO) for b in hard), ZERO) for o in opts}
            zero = [o for o in opts if hv[o] == 0]
            on_fb = False
            if zero:
                cands = zero
            elif d.get("fallback") == "least_violation" and opts:
                cands, on_fb = list(opts), True
            else:
                cands = []
            how = None
            if kind == "protective":
                if cands:
                    ch = list(cands)
                else:   # D-0K4.46: no candidate takes none, never infeasible
                    ch = [None]
                    how = ("no candidate: every option is not available" if not opts else
                           "no candidate: no option meets %s and the decision declares no fallback" % ", ".join(hard))
            else:
                optional = d.get("optional", True)
                ch = ([None] if (optional or not cands) else []) + list(cands)
            decs.append({"d": d, "hv": hv, "on_fb": on_fb, "how": how})
            choices.append(ch)

        best, best_key = None, None
        for combo in itertools.product(*choices):
            chosen = [o for o in combo if o is not None]
            spend = sum((opt[o]["one_off"] for o in chosen), ZERO)
            if spend > budget:
                continue
            if any(opt[o]["crew"] is None for o in chosen):
                continue
            crew = sum(opt[o]["crew"] for o in chosen)
            if crew > crew_limit:
                continue
            ok = True
            for o in chosen:
                rs = opt[o]["requires_switch"]
                if rs is not None and not is_true(sw.get(rs)):
                    ok = False
                    break
                rr = opt[o]["requires_restore"]
                if rr is not None:
                    dep = None
                    for dd, c in zip(decs, combo):
                        if dd["d"].get("name") == rr["decision"]:
                            dep = c
                    if dep is None or opt[dep]["restore_date"] is None:
                        ok = False
                        break
                    deadline = rr["by"]
                    for s_name, alt in rr["by_if_switch"].items():
                        if is_true(sw.get(s_name)):
                            deadline = alt
                    if add_business_days(opt[dep]["restore_date"], rr["plus_business_days"]) > deadline:
                        ok = False
                        break
            if not ok:
                continue
            tv = sum((dd["hv"][c] for dd, c in zip(decs, combo) if dd["on_fb"] and c is not None), ZERO)
            value = sum((oval(o) for o in chosen if opt[o]["valued"]), ZERO)
            k = (-tv, value, -spend)
            if best_key is None or k > best_key:
                best_key = k
                best = {"combo": combo, "chosen": chosen, "spend": spend, "crew": crew, "value": value, "tv": tv}
        if best is None:
            return None
        prot, detail = OrderedDict(), OrderedDict()
        for dd, c in zip(decs, best["combo"]):
            d = dd["d"]
            if d.get("kind") != "protective":
                continue
            if c is None:   # D-0K4.46: {chosen: null, admissible: [], how}, no trade_off
                prot[d["name"]] = None
                detail[d["name"]] = OrderedDict([("chosen", None), ("admissible", []), ("how", dd["how"])])
                continue
            prot[d["name"]] = c
            v = dd["hv"][c]
            detail[d["name"]] = {"option": c,
                                 "status": "least violation within the plan" if v > 0 else "meets its hard bounds",
                                 "violation": r2(v),
                                 "trade_off": [o for o in dd["hv"] if dd["hv"][o] < v]}
        best["protective_choices"] = prot
        best["protective_detail"] = detail
        best["budget"] = budget
        best["crew_limit"] = crew_limit
        return best

    def case_out(self, best, opt, crew_limit):
        if best is None:
            return OrderedDict([("value", None), ("spend", None), ("items", []), ("valued_option_costs", None),
                                ("not_valued_in_money", None), ("crew_visits_used", None), ("crew_visits_limit", crew_limit),
                                ("protective_choices", OrderedDict())])
        chosen = best["chosen"]
        voc = sum((opt[o]["one_off"] for o in chosen if opt[o]["valued"]), ZERO)
        return OrderedDict([
            ("value", r2(best["value"])),
            ("spend", r2(best["spend"])),
            ("items", list(chosen)),
            ("valued_option_costs", r2(voc)),
            ("not_valued_in_money", r2(best["spend"] - voc)),
            ("not_valued_in_money_items", [o for o in chosen if not opt[o]["valued"]]),
            ("crew_visits_used", best["crew"]),
            ("crew_visits_limit", crew_limit),
            ("protective_choices", best["protective_choices"]),
            ("protective_detail", best["protective_detail"]),
            ("total_violation", r2(best["tv"])),
        ])

    def plan_tenant(self, tid, opt):
        plan = self.plans_decl[tid]
        t = self.tenants[tid]
        crew_limit = int(D(t["portfolio_constraints"][plan["crew_limit"]]))
        switches = OrderedDict(plan.get("switches") or {})
        names = list(switches)
        ss = plan.get("switch_sensitivity") or {}
        cases, raw = OrderedDict(), OrderedDict()
        for combo in itertools.product(*[switches[n] for n in names]) if names else [()]:
            sw = dict(zip(names, combo))
            key = "/".join(fmt_switch(v) for v in combo)
            value_over = {}
            for s_name, mapping in ss.items():
                if s_name in sw:
                    for mk, sens_name in (mapping or {}).items():
                        if mk == sw[s_name] and type(mk) is type(sw[s_name]):
                            for o, od in opt.items():
                                if sens_name in od["sens"]:
                                    value_over[o] = od["sens"][sens_name]
            best = self.solve(tid, sw, opt, value_over=value_over)
            cases[key] = self.case_out(best, opt, crew_limit)
            raw[key] = (sw, best)
        default_key = "/".join(fmt_switch(switches[n][0]) for n in names)
        default_sw, default_best = raw[default_key]
        out = OrderedDict()
        out["switch_cases"] = cases
        out["default_key"] = default_key
        out["default"] = cases[default_key]
        drops = OrderedDict()
        for dname, dlist in (plan.get("downside_drops") or {}).items():
            b = self.solve(tid, default_sw, opt, exclude=frozenset(dlist))
            drops[dname] = b["value"] if b is not None else None
        excluded_names = set(drops) | {sn for m in ss.values() for sn in (m or {}).values()}
        sv = OrderedDict()
        if default_best is not None:
            valued_items = [o for o in default_best["chosen"] if opt[o]["valued"]]
            for o in valued_items:
                for sn in opt[o]["sens"]:
                    if sn in excluded_names or sn in sv:
                        continue
                    sv[sn] = sum((opt[x]["sens"].get(sn, opt[x]["value"]) for x in valued_items), ZERO)
        # §6.4 switch-sensitivity values: the case with that switch value, every other switch at its first value
        for s_name, mapping in ss.items():
            if s_name not in switches:
                continue
            for mk, sens_name in (mapping or {}).items():
                vals = [v for v in switches[s_name] if v == mk and type(v) is type(mk)]
                if not vals:
                    continue
                key = "/".join(fmt_switch(vals[0] if n == s_name else switches[n][0]) for n in names)
                b = raw[key][1]
                sv[sens_name] = b["value"] if b is not None else None
        out["downside_drops"] = OrderedDict((k, r2(v)) for k, v in drops.items())
        out["sensitivity_values"] = OrderedDict((k, r2(v)) for k, v in sv.items())
        pool = [v for v in list(drops.values()) + list(sv.values()) if v is not None]
        out["downside"] = r2(min(pool)) if pool else None
        na = OrderedDict()
        for d in plan.get("decisions") or []:
            for o in d.get("options") or []:
                if o in opt and opt[o]["na"] is not None and o not in na:
                    na[o] = opt[o]["na"].words
        if na:
            out["not_available"] = na
        return out

    # ---- §3 portfolio and operations --------------------------------------------------------------------------
    def portfolio(self, tid):
        t = self.tenants[tid]
        out = OrderedDict()
        for side in ("plan", "actual", "november_to_date"):
            entries = []
            for s in t["sites"]:
                sd = self.site_sides(s["site"])
                if side in sd:
                    entries.append((s["site"], sd[side]))
            if not entries:
                continue
            if all(e["status"] == "evaluated" for _, e in entries):
                sums = OrderedDict()
                for n in entries[0][1]["struct_nodes"]:
                    sums[n] = sum((e["struct_nodes"][n] for _, e in entries), ZERO)
                if "departures_met" in sums and "cost_to_serve" in sums:
                    if sums["departures_met"] != 0:
                        sums["cost_per_departure_met"] = sums["cost_to_serve"] / sums["departures_met"]
                out[side] = {"sums": OrderedDict((k, r2(v)) for k, v in sums.items()), "not_decomposed": []}
            else:
                nd = [n for n, e in entries if e["status"] != "evaluated"]
                # A6: sum of the stated totals of all the tenant's sites (records)
                total = ZERO
                recs = []
                for s in t["sites"]:
                    rec = self.side_records(s).get(side)
                    if rec is None:
                        continue
                    recs.append(rec)
                    st = rec.get("contribution", rec.get("total"))
                    total += D(st)
                sums = OrderedDict([("outcome_total_with_stated_totals", r2(total))])
                # §3 (amended), A25: only when every record of the side states departures_required
                if recs and all(r.get("departures_required") is not None for r in recs):
                    dr = sum((D(r["departures_required"]) for r in recs), ZERO)
                    if dr != 0:
                        sums["cost_per_departure_required"] = r2(total / dr)
                out[side] = {"sums": sums, "not_decomposed": nd}
        return out

    def operations(self, tid):
        t = self.tenants[tid]
        out = OrderedDict()
        for meas in ((t.get("portfolio") or {}).get("operations") or {}).get("measures") or []:
            if not meas.get("numerator"):
                continue
            num_n, den_n = meas["numerator"], meas.get("denominator")
            scale = D(meas.get("scale", 1))
            dec = int(meas.get("decimals", 2))
            nums, dens, vals = OrderedDict(), OrderedDict(), OrderedDict()
            for s in t["sites"]:
                act = self.site_sides(s["site"]).get("actual")
                if act is None or act["status"] != "evaluated":
                    continue
                nv = act["nodes"][num_n]
                nums[s["site"]] = nv
                if den_n:
                    dv = act["nodes"][den_n]
                    dens[s["site"]] = dv
                    vals[s["site"]] = rdec(nv / dv * scale, dec) if dv != 0 else None
                else:
                    vals[s["site"]] = rdec(nv, dec)
            m = OrderedDict()
            m["sites"] = vals
            if den_n:
                sn, sd = sum(nums.values(), ZERO), sum(dens.values(), ZERO)
                m["portfolio"] = rdec(sn / sd * scale, dec) if sd != 0 else None
                m["numerator"] = OrderedDict((k, r2(v)) for k, v in nums.items())
                m["denominator"] = OrderedDict((k, r2(v)) for k, v in dens.items())
            else:
                m["portfolio"] = rdec(sum(nums.values(), ZERO), dec)
            out[meas["id"]] = m
        return out

    # ---- everything -------------------------------------------------------------------------------------------
    def options_and_plans(self):
        opts_out, internal = OrderedDict(), OrderedDict()
        for oid in (self.ev.get("options") or {}):
            o, i = self.evaluate_option(oid)
            opts_out[oid] = o
            internal[oid] = i
        dec_of = self.decision_of()
        for oid, o in opts_out.items():
            d = dec_of.get(oid)
            if d is None:
                o["admissible"] = True
            else:
                vs = [internal[oid]["violations"].get(b, ZERO) for b in d.get("hard") or []]
                # N1: a hard bound over a not-available node neither passes nor fails
                o["admissible"] = None if any(v is None for v in vs) else bool(sum(vs, ZERO) == 0)
        plans = OrderedDict((tid, self.plan_tenant(tid, internal)) for tid in self.plans_decl)
        return opts_out, plans

    def compute(self):
        out = OrderedDict()
        sites = OrderedDict()
        for sname, (tid, t, s) in self.site_index.items():
            entry = OrderedDict()
            for side, e in self.site_sides(sname).items():
                if e["status"] == "evaluated":
                    entry[side] = side_out(e["nodes"])
                else:
                    entry[side] = {"status": e["status"], "stated_total": r2(e["stated_total"])}
            sites["%s/%s" % (tid, sname)] = entry
        out["sites"] = sites
        out["portfolio"] = OrderedDict((tid, self.portfolio(tid)) for tid in self.tenants)
        out["operations"] = OrderedDict((tid, self.operations(tid)) for tid in self.tenants)
        opts, plans = self.options_and_plans()
        out["options"] = opts
        out["plans"] = plans
        out["horizons"] = {"protect_horizon_end": iso(self.horizon_end),
                           "value_horizon_end": OrderedDict((tid, iso(d)) for tid, d in self.value_horizon_end.items())}
        out["deciders"] = OrderedDict((r, sorted(v)) for r, v in sorted(self.deciders.items()))
        return out


def side_out(nodes, keep=None):
    """An evaluated side (or history month side): nodes rounded, a not-available node null, and (N1) the side map
    `not_available: {node: words}` when any node is not available."""
    keep = keep if keep is not None else (lambda k: True)
    out = {"status": "evaluated", "nodes": OrderedDict((k, r2(v)) for k, v in nodes.items() if keep(k))}
    na = OrderedDict((k, v.words) for k, v in nodes.items() if keep(k) and is_na(v))
    if na:
        out["not_available"] = na
    return out


def _variant_cases(plans):
    return OrderedDict((tid, OrderedDict((k, c) for k, c in p["switch_cases"].items())) for tid, p in plans.items())


def _diff(a, b):
    if a is None or b is None:
        return None
    return r2(D(a) - D(b))


def compute(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    result = Model(copy.deepcopy(manifest)).compute()

    oqv = OrderedDict()
    for q, qv in (manifest.get("owner_question_variants") or {}).items():
        applied = qv.get("applied")
        per_variant = OrderedDict()
        for vname, vdef in qv.items():
            if vname == "applied" or not isinstance(vdef, dict):
                continue
            doc = apply_patch(copy.deepcopy(manifest), vdef.get("patch") or [])
            _, plans = Model(doc).options_and_plans()
            per_variant[vname] = _variant_cases(plans)
        base = per_variant.get(applied)
        qout = OrderedDict()
        for vname, tenants in per_variant.items():
            vout = OrderedDict()
            for tid, cases in tenants.items():
                cout = OrderedDict()
                for key, c in cases.items():
                    a = base[tid][key] if base is not None else None
                    cout[key] = OrderedDict([
                        ("value", c["value"]), ("spend", c["spend"]), ("items", c["items"]),
                        ("crew_visits_used", c["crew_visits_used"]),
                        ("value_change_vs_applied", _diff(c["value"], a["value"]) if a else None),
                        ("spend_change_vs_applied", _diff(c["spend"], a["spend"]) if a else None),
                    ])
                vout[tid] = {"cases": cout}
            qout[vname] = vout
        qout_applied = OrderedDict([("applied", applied)])
        qout_applied.update(qout)
        oqv[q] = qout_applied
    result["owner_question_variants"] = oqv
    return result


# --------------------------------------------------------------------------------------------------------------
# July to September history (DS1 spec §8.2; R12, R16). Written from the spec and history.json alone: it shares no
# code or expression table with the evaluator. Each Site, side and month is evaluated through this model's own
# leaf and structure path, with the month's period_days and period_end, and no incident, entitlement or observations.
# --------------------------------------------------------------------------------------------------------------
_MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _left_alternative(tree):
    node = tree.body if isinstance(tree, ast.Expression) else tree
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        node = node.left
    return node


def _record_names(node):
    return {n.attr for n in ast.walk(node)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "record"}


def _names(expr):
    return {n.id for n in ast.walk(_parse(str(expr))) if isinstance(n, ast.Name)}


def _history_side(M, V, t, s, block, side, money_leaves):
    rec = OrderedDict()
    for k, v in block[side].items():
        rec[k] = (Decimal(v) / Decimal(100)) if k in money_leaves else v
    ctx = {"record": rec, "prices": t.get("prices"), "energy_model": t.get("energy_model"), "physical": s.get("physical"),
           "tariff": s.get("tariff"), "tenant": t, "site": s["site"], "as_of": M.as_of,
           "period_days": Decimal(block["period_days"]), "period_end": to_date(block["period_end"])}
    ctx = {k: v for k, v in ctx.items() if v is not None}
    leaves, missing = M.eval_leaves(V, s, ctx)
    own = set()   # leaves whose first alternative (their own record) resolves
    for name, expr in M.leaf_exprs(V, s).items():
        try:
            v = _ev(_left_alternative(_parse(str(expr))), ctx_resolver(ctx))
            if not is_na(v):   # N1: a not-available leaf is never the month's own record
                D(v)
                own.add(name)
        except (Unresolved, InvalidOperation):
            pass
    info = {"leaves": leaves, "unresolved": missing, "own": own}
    if not missing:
        try:
            nodes = Env(ctx, M.structures[V], leaves).all_nodes()
            allv = OrderedDict(nodes)
            allv.update(leaves)
            return {"status": "evaluated", "nodes": allv, **info}
        except Unresolved:
            pass
    stated = rec.get("contribution", rec.get("total"))
    return {"status": "not decomposed: stated total", "stated_total": D(stated) if stated is not None else None, **info}


def _reach(refs, leaves):
    """Structure nodes whose expression reaches any of `leaves`, directly or through another such node."""
    hit = set()
    while True:
        more = {n for n, r in refs.items() if n not in hit and r & (set(leaves) | hit)}
        if not more:
            return hit
        hit |= more


def _history_missing(manifest, M, V, s, refs, fed, sides, cause):
    """Each side's `missing` entries for one history month (review DS1p M1, L2; MB5), from the manifest's empty_states:
    plan: the target side's RESIDUAL or ASSUMPTION; actual: unreceived leaves, field assumptions, deferred stages;
    both: the observation-fed leaves (cause = history.missing_cause). October-only kinds (coverage ESTIMATED, rights
    conditions) cannot occur. Entries are {side, subject, record_kind, source_family, cause, carried_as, blocks, slice}."""
    ES = manifest["empty_states"]
    LS, TS = ES["leaf_sources"][V], ES["target_side"]
    order = list(M.leaf_exprs(V, s))

    def ent(side, subject, kind, family, cause_, carried, blocks, slice_):
        return {"side": side, "subject": subject, "record_kind": kind, "source_family": family, "cause": cause_,
                "carried_as": carried, "blocks": sorted(blocks), "slice": slice_}
    out = {"plan": [], "actual": []}
    plan, act = sides["plan"], sides["actual"]
    if plan["unresolved"]:
        gone = [f for f in order if f in plan["unresolved"]]
        out["plan"].append(ent("plan", {"leaves": gone}, TS["kind"], TS["family"], "NOT_RECEIVED", "RESIDUAL", _reach(refs, gone), TS["slice"]))
    else:
        result = manifest["chain_model"][V]["result"]
        split = [f for f in order if f not in plan["own"] and LS[f]["absent"] not in ("OPTION_ONLY", "NEVER_EMPTY")
                 and f in act["leaves"] and not is_na(act["leaves"][f]) and not is_na(plan["leaves"].get(f))
                 and act["leaves"][f] != plan["leaves"][f] and result in _reach(refs, [f])]
        if split:
            out["plan"].append(ent("plan", {"leaves": split}, TS["kind"], TS["family"], "NOT_RECEIVED", "ASSUMPTION", _reach(refs, split), TS["slice"]))
    for f in order:
        if f in act["unresolved"] and f not in fed:
            out["actual"].append(ent("actual", {"leaf": f}, LS[f]["kind"], LS[f]["family"], "NOT_RECEIVED", None, _reach(refs, [f]), LS[f]["slice"]))
    for path, ar in ES["assumptions"].items():
        head, field = path.split(".")
        if str((s.get(head) or {}).get(field, "")).startswith("[assumption]"):
            out["actual"].append(ent("actual", {"field": path, "label": ar["label"]}, ar["kind"], ar["family"], "NOT_RECEIVED", "ASSUMPTION",
                                     ar["blocks"], ar["slice"]))
    for st, dr in ES["deferred_stages"].items():
        if dr["vertical"] == V:
            out["actual"].append(ent("actual", {"stage": st, "label": dr["label"]}, dr["kind"], dr["family"], dr["cause"], None, dr["blocks"], dr["slice"]))
    for side in ("plan", "actual"):
        for f in sorted(fed):
            out[side].append(ent(side, {"leaf": f}, LS[f]["kind"], LS[f]["family"], cause, None, _reach(refs, [f]), LS[f]["slice"]))
    return out


def compute_history(manifest_path):
    import json
    import os
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    with open(os.path.join(os.path.dirname(os.path.abspath(manifest_path)), "history.json"), "r", encoding="utf-8") as f:
        hist = json.load(f)
    money_leaves = set(hist["meta"]["money_leaves"])
    months = list(hist["meta"]["months"]) + [manifest["accounting_period"]]
    M = Model(copy.deepcopy(manifest))
    out = OrderedDict([("months", months), ("tenants", OrderedDict())])
    for tid, t in M.tenants.items():
        V = M.vkey(t)
        cost = manifest["chain_model"][V].get("revenue") == "NOT_APPLICABLE"
        outcome = "cost_to_serve" if cost else "contribution"
        struct = M.structures[V]
        refs = {n: _names(e) for n, e in struct.items()}
        tout = OrderedDict([("kind", "cost" if cost else "contribution"), ("sites", OrderedDict())])
        for s in t["sites"]:
            sname = s["site"]
            obs_keys = set(((s.get("observations") or {}).get("october") or {}).keys())
            fed = {leaf for leaf, e in M.leaf_exprs(V, s).items() if _record_names(_left_alternative(_parse(str(e)))) & obs_keys}
            blocked = set()
            while True:   # every node whose expression reaches a fed leaf or a blocked node
                more = {n for n, r in refs.items() if n not in blocked and r & (fed | blocked)}
                if not more:
                    break
                blocked |= more
            periods, side_outcome = OrderedDict(), {}
            for mo in months[:-1]:
                block = hist["tenants"][tid][sname][mo]
                periods[mo] = OrderedDict()
                sides = {side: _history_side(M, V, t, s, block, side, money_leaves) for side in ("plan", "actual")}
                miss = _history_missing(manifest, M, V, s, refs, fed, sides, hist["meta"]["missing_cause"])
                for side in ("plan", "actual"):
                    e = sides[side]
                    if e["status"] == "evaluated":
                        val = e["nodes"][outcome]
                        periods[mo][side] = side_out(e["nodes"], lambda k: k not in blocked and k not in fed)
                        periods[mo][side].update({"outcome": r2(val), "not_observed": sorted(blocked)})
                    else:
                        val = e["stated_total"]
                        periods[mo][side] = {"status": e["status"], "stated_total": r2(val), "outcome": r2(val),
                                             "not_observed": sorted(blocked)}
                    periods[mo][side]["missing"] = miss[side]
                    side_outcome[(mo, side)] = r2(val)
            for side, e in M.site_sides(sname).items():
                if side in ("plan", "actual"):
                    v = e["nodes"][outcome] if e["status"] == "evaluated" else e["stated_total"]
                    side_outcome[(months[-1], side)] = r2(v)
            series, gap = [], []
            for mo in months:
                a, p = D(side_outcome[(mo, "actual")]), D(side_outcome[(mo, "plan")])
                label = _MONTH_NAMES[int(mo[5:7]) - 1]
                series.append({"m": label, "p": mo, "v": r2(a)})
                gap.append({"m": label, "p": mo, "v": r2(p - a if cost else a - p)})
            tout["sites"][sname] = OrderedDict([("outcome", series), ("gap", gap), ("periods", periods),
                                                ("observation_leaves", sorted(fed))])
        port = OrderedDict([("outcome", []), ("gap", [])])
        for i, mo in enumerate(months):
            for key in ("outcome", "gap"):
                total = sum((D(x[key][i]["v"]) for x in tout["sites"].values()), Decimal(0))
                port[key].append({"m": _MONTH_NAMES[int(mo[5:7]) - 1], "p": mo, "v": r2(total)})
        tout["portfolio"] = port
        out["tenants"][tid] = tout
    return out


def _main(argv):
    import os
    path = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo-site-scenario-manifest.yaml")
    res = compute(path)
    print("independent_model: %d site entries, %d options" % (len(res["sites"]), len(res["options"])))
    for key, sides in res["sites"].items():
        print("  %-36s %s" % (key, ", ".join("%s=%s" % (s, "eval" if e["status"] == "evaluated" else "stated %s" % e["stated_total"])
                                               for s, e in sides.items())))
    for tid, p in res["plans"].items():
        d = p["default"]
        print("plan %s [default %s]: value %s, spend %s, crew %s/%s" % (tid, p["default_key"], d["value"], d["spend"],
                                                                         d["crew_visits_used"], d["crew_visits_limit"]))
        print("    items: %s" % ", ".join(d["items"]))
        print("    protective: %s" % dict(d["protective_choices"]))
        for k, c in p["switch_cases"].items():
            print("    case %-12s value %-10s spend %-9s items %s" % (k, c["value"], c["spend"], ", ".join(c["items"])))
        print("    downside %s; drops %s; sensitivities %s" % (p["downside"], dict(p["downside_drops"]), dict(p["sensitivity_values"])))
    for q, qv in res["owner_question_variants"].items():
        for v, tenants in qv.items():
            if v == "applied":
                continue
            for tid, tc in tenants.items():
                for k, c in tc["cases"].items():
                    if c["value_change_vs_applied"] or c["spend_change_vs_applied"]:
                        print("  %s/%s %s %s: value %s (%+s) spend %s (%+s) items %s" % (q, v, tid, k, c["value"], c["value_change_vs_applied"],
                                                                                        c["spend"], c["spend_change_vs_applied"], ", ".join(c["items"])))


if __name__ == "__main__":
    _main(sys.argv)
