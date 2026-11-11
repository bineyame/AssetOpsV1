"""ANY-1 AR-0: the parity guard for stored read periods (architect answer 2026-11-10 §4, card AR-0; D-ANY.2).

    python tools/checks/period_read_parity.py --self-test
    python tools/checks/period_read_parity.py --database-url <clone url> --work <dir with keys.json>
        [--story <work>/story.json] [--seed 20261111] [--random 16] [--kinds mini_depth.renewable,...]
        [--record out.json]

For every story request (the pre-built script list, `chain.prebuild.paths()`, which honours
`ASSETOPS_PREBUILT_ROUTES`) plus seeded random cases - a board on any day, a Portfolio on any from/to of up to 31
days (aligned and unaligned), and historical `known_at` - the row-based compose must equal today's compose byte for
byte. Both run in one process over `lab_app` with the response store off (`ASSETOPS_RESPONSE_STORE=off`), so nothing
is pre-built or read from `chain_response`:

- oracle: `ASSETOPS_PERIOD_READ_KINDS` empty (today's compose for every page part);
- candidate: `ASSETOPS_PERIOD_READ_KINDS=<--kinds>` (those kinds' page parts from `site_period_read`).

Each request is fetched oracle, candidate, oracle. A status or byte difference between oracle and candidate is a
MISMATCH; two different oracle bodies are UNSTABLE (the request is not deterministic, so parity cannot be judged).
Either fails the run (exit 1). A kind that cannot be proven equal stays on the old path and is reported, never
approximated (architect answer §4 risks). With no `--kinds` (AR-1: no kind is served from rows) the run is the
baseline: it proves the oracle deterministic on every case.

`--self-test` runs on fakes (no database): the seeded cases are deterministic and in bounds, identical fetchers pass,
and one deliberate mismatch, a status difference and an unstable oracle each fail.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import quote

CHECKS = Path(__file__).resolve().parent
TOOLS = CHECKS.parent
KINDS_ENV = "ASSETOPS_PERIOD_READ_KINDS"
BOARD_SITES = ("KOBO-001", "KISIWA-001")
MAX_PORTFOLIO_DAYS = 31
UTC = timezone.utc


@dataclass(frozen=True)
class Case:
    id: str
    path: str
    family: str  # "story" | "board_any_day" | "portfolio_any_range"


@dataclass
class Outcome:
    case: Case
    verdict: str  # PASS | MISMATCH | UNSTABLE
    detail: str = ""
    oracle_ms: float = 0.0
    candidate_ms: float = 0.0


@dataclass
class Report:
    outcomes: list[Outcome] = field(default_factory=list)

    @property
    def failed(self) -> list[Outcome]:
        return [o for o in self.outcomes if o.verdict != "PASS"]

    def as_json(self) -> dict:
        return {"cases": len(self.outcomes), "pass": len(self.outcomes) - len(self.failed),
                "mismatch": sum(o.verdict == "MISMATCH" for o in self.outcomes),
                "unstable": sum(o.verdict == "UNSTABLE" for o in self.outcomes),
                "failed": [{"id": o.case.id, "path": o.case.path, "verdict": o.verdict, "detail": o.detail}
                           for o in self.failed]}


def _z(at: datetime) -> str:
    return at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _q(at: datetime) -> str:
    return quote(_z(at), safe="")


def seeded_cases(seed: int, count: int, first_day: date, last_day: date,
                 board_sites: Sequence[str] = BOARD_SITES) -> list[Case]:
    """Deterministic for a seed. The first five cases fix one of each class (board any day, aligned Portfolio,
    unaligned Portfolio, a 31-day Portfolio month, a historical `known_at`); the rest are drawn at random."""
    if last_day < first_day:
        raise ValueError("last_day is before first_day")
    rng = random.Random(seed)
    span = (last_day - first_day).days

    def day() -> date:
        return first_day + timedelta(days=rng.randint(0, span))

    def board(i: int, known: bool = False) -> Case:
        d = day()
        path = f"/api/sites/{rng.choice(list(board_sites))}/outcome-board?date={d.isoformat()}"
        if known:
            k = datetime.combine(d, datetime.min.time(), UTC) + timedelta(days=1, minutes=rng.randint(0, 72 * 60))
            path += f"&known_at={_q(k)}"
        return Case(f"any.board.{i}", path, "board_any_day")

    def portfolio(i: int, days: int | None = None, unaligned: bool | None = None, known: bool = False) -> Case:
        n = days if days is not None else rng.randint(1, MAX_PORTFOLIO_DAYS)
        start_day = first_day + timedelta(days=rng.randint(0, max(0, span + 1 - n)))
        lo = datetime.combine(start_day, datetime.min.time(), UTC)
        hi = lo + timedelta(days=n)
        if unaligned if unaligned is not None else rng.random() < 0.5:
            # a partial first and last day (a Site-local day against a UTC window, D-ANY.5 Low): both ends off a
            # UTC midnight, the span still more than 0 and at most `n` days
            h = rng.randint(1, 23)
            lo += timedelta(hours=h)
            end = rng.choice([x for x in range(1, 24) if (h + x) % 24])
            hi = lo + timedelta(days=n - 1, hours=end)
        path = f"/api/estate/portfolio?from={_q(lo)}&to={_q(hi)}&lens=all"
        if known:
            path += f"&known_at={_q(hi + timedelta(hours=rng.randint(0, 48)))}"
        return Case(f"any.portfolio.{i}", path, "portfolio_any_range")

    out = [board(0), portfolio(1, unaligned=False), portfolio(2, unaligned=True),
           portfolio(3, days=MAX_PORTFOLIO_DAYS, unaligned=False), portfolio(4, known=True)]
    for i in range(5, max(5, count)):
        out.append(board(i, known=rng.random() < 0.3) if rng.random() < 0.5
                   else portfolio(i, known=rng.random() < 0.3))
    return out


def portfolio_days(path: str) -> float:
    from urllib.parse import parse_qs, unquote, urlsplit

    q = parse_qs(urlsplit(path).query)
    lo = datetime.fromisoformat(unquote(q["from"][0]).replace("Z", "+00:00"))
    hi = datetime.fromisoformat(unquote(q["to"][0]).replace("Z", "+00:00"))
    return (hi - lo).total_seconds() / 86400


def _end_unaligned(path: str) -> bool:
    from urllib.parse import parse_qs, unquote, urlsplit

    hi = datetime.fromisoformat(unquote(parse_qs(urlsplit(path).query)["to"][0]).replace("Z", "+00:00"))
    return (hi.hour, hi.minute, hi.second) != (0, 0, 0)


#: D-ANY.5 step 5: one historical k taken from the database's own transaction-time clock, between a stored row's
#: revision 1 and revision 2 (the read-period rows when any kind has two revisions, else the day snapshots that
#: today's compose reads at k), so parity covers "revision 1 served at k", not only "nothing known yet".
#: `known_at` travels in whole seconds (`outcome_api._instant`), so k is the first whole second after revision 1,
#: and only a pair whose revision 2 came later than that qualifies.
_BETWEEN_REVISIONS = (
    "SELECT s.site_code, r1.local_day, date_trunc('second', r1.computed_at) + interval '1 second' AS k "
    "FROM {table} r1 JOIN {table} r2 ON r2.tenant_id = r1.tenant_id AND r2.site_id = r1.site_id "
    "AND {same} AND r2.revision = 2 AND r2.computed_at > date_trunc('second', r1.computed_at) + interval '1 second' "
    "JOIN site s ON s.tenant_id = r1.tenant_id AND s.id = r1.site_id "
    "WHERE r1.revision = 1 ORDER BY r1.local_day DESC, s.site_code LIMIT 1"
)
_REVISION_TABLES = (
    ("site_period_read", "r2.kind = r1.kind AND r2.period_start = r1.period_start"),
    ("site_day_snapshot", "r2.local_day = r1.local_day AND r2.measure = r1.measure "
                          "AND r2.subject_kind = r1.subject_kind AND r2.subject_ref = r1.subject_ref "
                          "AND r2.evidence_class = r1.evidence_class"),
)


def between_revisions_case(url: str) -> Case | None:
    """A board read on the day of the first row with two revisions, known at the instant between them."""
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    try:
        with engine.connect() as c:
            for table, same in _REVISION_TABLES:
                r = c.execute(text(_BETWEEN_REVISIONS.format(table=table, same=same))).first()
                if r is not None:
                    path = f"/api/sites/{r[0]}/outcome-board?date={r[1].isoformat()}&known_at={_q(r[2])}"
                    return Case(f"any.between_revisions.{table}", path, "historical_between_revisions")
    finally:
        engine.dispose()
    return None


def _first_difference(a: bytes, b: bytes) -> str:
    n = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return (f"first difference at byte {n} (lengths {len(a)} vs {len(b)}): "
            f"oracle {a[max(0, n - 40):n + 40]!r} candidate {b[max(0, n - 40):n + 40]!r}")


Fetch = Callable[[str], tuple[int, bytes]]


def compare(cases: Sequence[Case], oracle: Fetch, candidate: Fetch) -> Report:
    report = Report()
    for case in cases:
        t0 = time.perf_counter()
        s1, a = oracle(case.path)
        t1 = time.perf_counter()
        s2, b = candidate(case.path)
        t2 = time.perf_counter()
        s3, c = oracle(case.path)
        o = Outcome(case, "PASS", oracle_ms=round((t1 - t0) * 1000, 1), candidate_ms=round((t2 - t1) * 1000, 1))
        if (s1, a) != (s3, c):
            o.verdict, o.detail = "UNSTABLE", f"oracle not deterministic: {_first_difference(a, c)}" \
                if s1 == s3 else f"oracle status {s1} then {s3}"
        elif s1 != s2:
            o.verdict, o.detail = "MISMATCH", f"status oracle {s1} candidate {s2}"
        elif a != b:
            o.verdict, o.detail = "MISMATCH", _first_difference(a, b)
        report.outcomes.append(o)
    return report


def print_report(report: Report) -> None:
    for o in report.outcomes:
        print(f"{o.verdict:<9} {o.case.id:<22} {o.oracle_ms:>9.1f} ms {o.candidate_ms:>9.1f} ms  {o.case.path}")
        if o.detail:
            print(f"          {o.detail}")
    s = report.as_json()
    print(f"period_read_parity: {'FAIL' if report.failed else 'PASS'} ({s['cases']} cases, {s['mismatch']} mismatch, "
          f"{s['unstable']} unstable)")


# --- self-test (fakes, no database) ------------------------------------------------------------------------------


def self_test() -> list[str]:
    problems: list[str] = []
    first, last = date(2026, 10, 10), date(2026, 11, 7)
    a = seeded_cases(7, 24, first, last)
    if a != seeded_cases(7, 24, first, last):
        problems.append("seeded cases are not deterministic for one seed")
    if a == seeded_cases(8, 24, first, last):
        problems.append("two seeds gave the same cases")
    if len(a) != 24 or len({c.id for c in a}) != 24:
        problems.append("case count or ids wrong")
    fams = {c.family for c in a}
    if fams != {"board_any_day", "portfolio_any_range"}:
        problems.append(f"families {fams}")
    for c in a:
        if c.family == "portfolio_any_range":
            n = portfolio_days(c.path)
            if not 0 < n <= MAX_PORTFOLIO_DAYS:
                problems.append(f"{c.id}: {n} days")
        else:
            d = date.fromisoformat(c.path.split("date=")[1][:10])
            if not first <= d <= last:
                problems.append(f"{c.id}: day {d} outside the range")
    if not any("known_at=" in c.path for c in a):
        problems.append("no historical known_at case")
    if not any(portfolio_days(c.path) == MAX_PORTFOLIO_DAYS for c in a if c.family == "portfolio_any_range"):
        problems.append("no 31-day Portfolio case")
    if not any(portfolio_days(c.path) % 1 for c in a if c.family == "portfolio_any_range"):
        problems.append("no unaligned Portfolio case")
    if not any(_end_unaligned(c.path) for c in a if c.family == "portfolio_any_range"):
        problems.append("no Portfolio case whose end is off a UTC midnight")

    cases = [Case("story.0", "/api/estate/portfolio?from=a&to=b", "story")] + a[:4]
    bodies = {c.path: json.dumps({"path": c.path, "n": i}).encode() for i, c in enumerate(cases)}

    def same(path: str) -> tuple[int, bytes]:
        return 200, bodies[path]

    if compare(cases, same, same).failed:
        problems.append("identical fetchers failed")
    target = cases[2].path

    def one_byte(path: str) -> tuple[int, bytes]:
        body = bodies[path]
        return 200, (body[:-2] + b"9}" if path == target else body)

    bad = compare(cases, same, one_byte)
    if [o.case.path for o in bad.failed] != [target] or bad.failed[0].verdict != "MISMATCH":
        problems.append(f"one deliberate byte mismatch was not caught alone: {bad.as_json()}")

    def status(path: str) -> tuple[int, bytes]:
        return (500 if path == target else 200), bodies[path]

    if [o.verdict for o in compare(cases, same, status).failed] != ["MISMATCH"]:
        problems.append("a status difference was not caught")
    calls: dict[str, int] = {}

    def drifting(path: str) -> tuple[int, bytes]:
        calls[path] = calls.get(path, 0) + 1
        return 200, bodies[path] + (str(calls[path]).encode() if path == target else b"")

    if [o.verdict for o in compare(cases, drifting, same).failed] != ["UNSTABLE"]:
        problems.append("an unstable oracle was not caught")
    return problems


# --- database mode ------------------------------------------------------------------------------------------------


def story_cases() -> list[Case]:
    from assetops_backend.chain.prebuild import paths

    return [Case(f"story.{i}", p, "story") for i, p in enumerate(paths())]


def _range_from_story(story: Path | None) -> tuple[date, date]:
    if story is None:
        return date(2026, 10, 10), date(2026, 10, 31)
    s = json.loads(story.read_text(encoding="utf-8"))["S"]
    last = datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    return last - timedelta(days=28), last


def run(url: str, work: Path, story: Path | None, seed: int, count: int, kinds: str) -> Report:
    os.environ["ASSETOPS_RESPONSE_STORE"] = "off"
    sys.path.insert(0, str(TOOLS))
    import chain_perf_probe

    c = chain_perf_probe.client(url, work)
    first, last = _range_from_story(story)
    cases = story_cases() + seeded_cases(seed, count, first, last)
    between = between_revisions_case(url)
    if between is not None:
        cases.append(between)

    def fetch(value: str) -> Fetch:
        def go(path: str) -> tuple[int, bytes]:
            os.environ[KINDS_ENV] = value
            r = c.get(path)
            return r.status_code, r.content
        return go

    try:
        report = compare(cases, fetch(""), fetch(kinds))
    finally:
        os.environ.pop(KINDS_ENV, None)
    if between is None:  # never silent: a parity DB with no second revision cannot prove the historical case
        report.outcomes.append(Outcome(Case("any.between_revisions", "-", "historical_between_revisions"),
                                       "MISSING", "no stored row with a revision 2 on this database"))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python tools/checks/period_read_parity.py")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--database-url")
    p.add_argument("--work", type=Path)
    p.add_argument("--story", type=Path)
    p.add_argument("--seed", type=int, default=20261111)
    p.add_argument("--random", type=int, default=16)
    p.add_argument("--kinds", default="", help="comma-separated kinds served from rows in the candidate")
    p.add_argument("--record", type=Path)
    args = p.parse_args(argv)
    if args.self_test:
        problems = self_test()
        for line in problems:
            print(f"FAIL {line}")
        print(f"period_read_parity self-test: {'FAIL' if problems else 'PASS'}")
        return 1 if problems else 0
    if not args.database_url or not args.work:
        p.error("--self-test, or --database-url with --work")
    report = run(args.database_url, args.work, args.story, args.seed, args.random, args.kinds)
    print_report(report)
    if args.record:
        args.record.write_text(json.dumps({"params": {"seed": args.seed, "random": args.random,
                                                      "kinds": args.kinds},
                                           **report.as_json(),
                                           "timings": [{"id": o.case.id, "oracle_ms": o.oracle_ms,
                                                        "candidate_ms": o.candidate_ms}
                                                       for o in report.outcomes]},
                                          indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
