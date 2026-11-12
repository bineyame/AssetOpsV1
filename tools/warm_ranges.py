"""WARM-1 (rev 7 §7.1, D-17N.1): prepare every range the presenter can reach by clicking, over HTTP.

A LABELLED WORKAROUND for the 17 Nov build only (it reverses D-ANY.3 for that build). It is throw-away once ANY-3
makes every range fast when computed live. Custom ranges outside the set below still compute live.

Range set (generated from the wall clock, which is what the browser's date bar uses, and each Site's dates):
  1. the five presets exactly as `frontend/src/ui/sharedRange.ts` `presetRange` computes them (full UTC days ending
     yesterday): Yesterday, Last 7 days, Last 30 days, This month, Last month (not `7dwork`: Work pages only, and no
     Work page is a stored route);
  2. every window of 7, 14, 30 and 31 UTC days inside the data window (first day: the earliest Site's first day;
     last day: the latest Site's last day);
  3. the story requests of the pre-built route list (`--routes`), sent as they are.

Requests per range (each exactly as the page sends it; the store keys on the parsed request, so a defaulted `lens`
or `limit` shares its key either way):
  - Portfolio: `/api/estate/portfolio?from&to&limit=50` (every PF-T tab but Act first's lens views) and
    `?from&to&lens={cost,risks,opportunities}&limit=50` (Act first's lens chips);
  - `/api/estate/outcome-summary?from&to`; the Findings index page 1 `/api/estate/findings?from&to`;
  - Cold and EV boards (the Site page and its Site Findings warnings panel): `/api/sites/{code}/outcome-board?from&to`;
  - Kobo and Kisiwa boards (the Site Findings warnings panel, `miniBoardDay(to)`): `?date={last day}`; and, for the
    Site Overview's served day, one board per day of each mini-grid Site's own dates.

`warm` (default) sends each request with `--workers` threads, presets first, newest ranges next. Before each batch
it waits while `pg_stat_activity` is above `--max-connections` (150). A 503 or a `stale` copy (and a body served
but not stored: `race`, `unstored`, `composed`) is retried 2, 5 and 10 s later (D-E5.47); one that stays so fails
the run (exit 1). `--verify` replays every request once and passes only when every answer is a stored `hit` and
the slowest is at most 2.0 s. Both write `--report` (`warm-report.json`), with a reason per failing request
(D-WARM.6). `--dry-run` only counts.

Architect rulings D-WARM.1-6 (`build-sheet-OWN-GAPS-2026-11-08.md`): the Findings lens pages
(`lens=cost|risks|opportunities`) are warmed for the presets and the story ranges (D-WARM.5); `--verify` also times
the unstored reads of the presets and story ranges (estate scope, actions, evidence, financials; each Site's
Overview and Site Findings read) under `unstored`, outside `pass` (D-WARM.2). The claim is "<=2 s on every stored
request of every clickable range".

    python tools/warm_ranges.py --base-url http://127.0.0.1:8990 --work var/polish_client4 --db-url postgresql://...
    python tools/warm_ranges.py --base-url http://127.0.0.1:8990 --work var/polish_client4 --verify
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from datetime import time as time_
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlencode

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROUTES = REPO / "config" / "chain" / "prebuilt-routes-v1.json"

#: `RANGE_PRESETS` order, without `7dwork` (Work pages only) and `custom`.
PRESETS = ("yesterday", "7d", "30d", "month", "lastmonth")
LENGTHS = (7, 14, 30, 31)
RANGE_MAX_DAYS = 31
PORTFOLIO_PAGE_SIZE = 50  # frontend/src/estate/portfolioWords.ts
PORTFOLIO_LENSES = ("cost", "risks", "opportunities")
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001", "kisiwa": "KISIWA-001"}
#: Sites whose board reads one day (`date=`); the others read the range's own `from`/`to`.
MINI_GRID = ("KOBO-001", "KISIWA-001")
HEADER = "x-assetops-stored"  # chain/response_store.py HEADER, lower-cased
STORED = ("hit", "stored")
DEGRADED = ("stale",)
RETRY_WAITS = (2, 5, 10)
MAX_CONNECTIONS = 150
CONNECTION_WAIT_SECONDS = 5
VERIFY_MAX_MS = 2000
TIMEOUT_SECONDS = 900


# ---- the range set (pure) ---------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Range:
    name: str
    first: date  # first day, included
    last: date  # last day, included

    @property
    def days(self) -> int:
        return (self.last - self.first).days + 1

    def window(self) -> tuple[str, str]:
        """`rangeWindow`: `first` 00:00Z and the day after `last` 00:00Z (half-open)."""
        return f"{self.first.isoformat()}T00:00:00Z", f"{(self.last + timedelta(days=1)).isoformat()}T00:00:00Z"


def preset_range(preset: str, today: date) -> tuple[date, date]:
    """`presetRange(preset, now)` for `now` on UTC day `today`."""
    yesterday = today - timedelta(days=1)
    if preset == "yesterday":
        return yesterday, yesterday
    if preset == "7d":
        return today - timedelta(days=7), yesterday
    if preset == "30d":
        return today - timedelta(days=30), yesterday
    if preset == "month":
        first = today.replace(day=1)
        return first, (first if yesterday < first else yesterday)
    if preset == "lastmonth":
        first = today.replace(day=1)
        return (first - timedelta(days=1)).replace(day=1), first - timedelta(days=1)
    raise ValueError(f"unknown preset {preset!r}")


def windows(data_first: date, data_last: date, lengths: Iterable[int] = LENGTHS) -> list[Range]:
    """Every day-aligned window of each length lying inside [data_first, data_last], newest first, then shortest."""
    out = []
    for n in lengths:
        last = data_last
        while last - timedelta(days=n - 1) >= data_first:
            out.append(Range(f"{n}d", last - timedelta(days=n - 1), last))
            last -= timedelta(days=1)
    return sorted(out, key=lambda r: (-r.last.toordinal(), r.days))


def ranges(today: date, data_first: date, data_last: date) -> list[Range]:
    """Presets first (in the bar's order), then every window; a window equal to a preset is listed once."""
    out = [Range(p, *preset_range(p, today)) for p in PRESETS]
    seen = {(r.first, r.last) for r in out}
    for r in windows(data_first, data_last):
        if (r.first, r.last) not in seen:
            seen.add((r.first, r.last))
            out.append(r)
    return out


@dataclass(frozen=True)
class Req:
    id: str
    path: str
    query: str

    @property
    def target(self) -> str:
        return f"{self.path}?{self.query}" if self.query else self.path


def _q(*pairs: tuple[str, str]) -> str:
    """`URLSearchParams.toString()` for these pairs, in order (`:` as `%3A`, space as `+`)."""
    return urlencode(list(pairs))


# `findingIndex.tsx` STATE_CHIPS, less "all" (which `estateQueryString` omits).
STATE_CHIPS = ("supported", "unconfirmed", "no_longer_supported", "merged")


def range_requests(r: Range, sites: dict[str, tuple[date, date]]) -> list[Req]:
    """The stored-route requests the pages make for one range. `sites`: Site code -> (first day, last day)."""
    f, t = r.window()
    tag = f"{r.name}:{r.first}..{r.last}"
    out = [Req(f"portfolio.{tag}", "/api/estate/portfolio", _q(("from", f), ("to", t), ("limit", str(PORTFOLIO_PAGE_SIZE))))]
    out += [Req(f"portfolio.{lens}.{tag}", "/api/estate/portfolio",
                _q(("from", f), ("to", t), ("lens", lens), ("limit", str(PORTFOLIO_PAGE_SIZE))))
            for lens in PORTFOLIO_LENSES]
    out.append(Req(f"summary.{tag}", "/api/estate/outcome-summary", _q(("from", f), ("to", t))))
    out.append(Req(f"findings.{tag}", "/api/estate/findings", _q(("from", f), ("to", t))))
    # D-WARM.7: the Findings state chips (`state=` values; "all" sends none) and the Portfolio scope-ids page 1.
    out += [Req(f"findings.state.{state}.{tag}", "/api/estate/findings", _q(("from", f), ("to", t), ("state", state)))
            for state in STATE_CHIPS]
    out.append(Req(f"scope-ids.{tag}", "/api/estate/portfolio/scope-ids", _q(("from", f), ("to", t))))
    # D-WARM.8: scope-ids under each lens (the client appends `lens=` last); page 2+ stays outside the claim.
    out += [Req(f"scope-ids.{lens}.{tag}", "/api/estate/portfolio/scope-ids", _q(("from", f), ("to", t), ("lens", lens)))
            for lens in PORTFOLIO_LENSES]
    for code in sorted(sites):
        path = f"/api/sites/{code}/outcome-board"
        if code in MINI_GRID:  # `miniBoardDay(to)`: the range's last day
            out.append(Req(f"board.{code}.{r.last}", path, _q(("date", r.last.isoformat()))))
        else:
            out.append(Req(f"board.{code}.{tag}", path, _q(("from", f), ("to", t))))
    return out


def day_requests(sites: dict[str, tuple[date, date]]) -> list[Req]:
    """The Site Overview's board on each day of a mini-grid Site's own dates, newest first."""
    out = []
    for code in sorted(sites):
        if code not in MINI_GRID:
            continue
        first, last = sites[code]
        d = last
        while d >= first:
            out.append(Req(f"board.{code}.{d}", f"/api/sites/{code}/outcome-board", _q(("date", d.isoformat()))))
            d -= timedelta(days=1)
    return out


def findings_lens_requests(f: str, t: str, tag: str) -> list[Req]:
    """D-WARM.5: the Findings lens pages (`/findings/{cost,risks,opportunities}`), page 1 (`estateQueryString`)."""
    return [Req(f"findings.{lens}.{tag}", "/api/estate/findings", _q(("from", f), ("to", t), ("lens", lens)))
            for lens in PORTFOLIO_LENSES]


def mini_board_day(t: str) -> str:
    """`miniBoardDay(to)`: the UTC day of `to`, the day before when `to` is a UTC midnight (an exclusive end)."""
    end = datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(timezone.utc)
    if (end.hour, end.minute, end.second, end.microsecond) == (0, 0, 0, 0):
        end -= timedelta(days=1)
    return end.date().isoformat()


def unstored_requests(f: str, t: str, tag: str, sites: dict[str, tuple[date, date]]) -> list[Req]:
    """D-WARM.2: the unstored reads the script pages send for one window; timed by `--verify`, never gated.
    Estate: the Findings page's scope, Actions, Evidence, Financials. Per Site: its Overview read (mini-grid:
    `overview?date=`; Cold/EV: `cold|ev/overview?from&to`) and its Site Findings read (mini-grid:
    `findings?from&to`; Cold/EV: `cold|ev/findings?from&to`)."""
    window = _q(("from", f), ("to", t))
    out = [Req(f"unstored.{name}.{tag}", f"/api/estate/{name}", window)
           for name in ("scope", "actions", "evidence", "financials")]
    for code in sorted(sites):
        if code in MINI_GRID:
            out.append(Req(f"unstored.overview.{code}.{tag}", f"/api/sites/{code}/overview",
                           _q(("date", mini_board_day(t)))))
            out.append(Req(f"unstored.findings.{code}.{tag}", f"/api/sites/{code}/findings", window))
        else:
            kind = "ev" if code.startswith("EV") else "cold"
            out.append(Req(f"unstored.overview.{code}.{tag}", f"/api/sites/{code}/{kind}/overview", window))
            out.append(Req(f"unstored.findings.{code}.{tag}", f"/api/sites/{code}/{kind}/findings", window))
    return out


def story_windows(routes: dict | None) -> list[tuple[str, str]]:
    """The story ranges: each distinct `from`/`to` of the pre-built list's estate requests, in list order."""
    from urllib.parse import parse_qsl

    out: list[tuple[str, str]] = []
    for r in (routes or {}).get("requests", []):
        if not r["path"].startswith("/api/estate/"):
            continue
        params = dict(parse_qsl(r["query"]))
        pair = (params.get("from", ""), params.get("to", ""))
        if all(pair) and pair not in out:
            out.append(pair)
    return out


def midnight_range(f: str, t: str) -> Range | None:
    """The `Range` whose `window()` is exactly `f`..`t`, when both are UTC midnights (half-open), else None."""
    try:
        a = datetime.strptime(f, "%Y-%m-%dT%H:%M:%SZ")
        b = datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    if a.time() != time_.min or b.time() != time_.min or b <= a:
        return None
    return Range("story", a.date(), b.date() - timedelta(days=1))


def story_requests(routes: dict | None) -> list[Req]:
    """The pre-built route list's requests, as they are (`chain-prebuilt-routes-1`)."""
    return [Req(f"story.{r['id']}", r["path"], r["query"]) for r in (routes or {}).get("requests", [])]


def report_path(work: Path | None, verify: bool) -> Path:
    """L3: `--verify` has its own default file, so serve's background warm never overwrites the gate's report."""
    name = "warm-verify.json" if verify else "warm-report.json"
    return (work / name) if work else Path(name)


def data_window(sites: dict[str, tuple[date, date]]) -> tuple[date, date]:
    """The estate data window: the earliest Site's first day to the latest Site's last day."""
    return min(v[0] for v in sites.values()), max(v[1] for v in sites.values())


def _dedupe(reqs: Iterable[Req]) -> list[Req]:
    out: list[Req] = []
    seen: set[tuple[str, str]] = set()
    for req in reqs:
        if (req.path, req.query) not in seen:
            seen.add((req.path, req.query))
            out.append(req)
    return out


def plan(today: date, sites: dict[str, tuple[date, date]], routes: dict | None = None) -> tuple[list[Range], list[Req]]:
    """The ordered, de-duplicated stored-request list: presets (with the Findings lens pages, D-WARM.5), then windows
    newest first, then mini-grid days, then the story list and the story ranges' Findings lens pages."""
    first, last = data_window(sites)
    rs = ranges(today, first, last)
    reqs: list[Req] = []
    for i, r in enumerate(rs):
        reqs += range_requests(r, sites)
        if i < len(PRESETS):  # `ranges` lists the five presets first
            reqs += findings_lens_requests(*r.window(), f"{r.name}:{r.first}..{r.last}")
    reqs += day_requests(sites) + story_requests(routes)
    for f, t in story_windows(routes):
        reqs += findings_lens_requests(f, t, f"story:{f}..{t}")
        story = midnight_range(f, t)  # M1 / D-SR.9: the story ranges get every page x Site request too
        if story is not None:
            reqs += range_requests(story, sites)
    return rs, _dedupe(reqs)


def unstored_plan(today: date, sites: dict[str, tuple[date, date]], routes: dict | None = None) -> list[Req]:
    """D-WARM.2: the unstored reads for the 5 presets and the story ranges (timed by `--verify`, not gated)."""
    reqs: list[Req] = []
    for p in PRESETS:
        r = Range(p, *preset_range(p, today))
        reqs += unstored_requests(*r.window(), f"{p}:{r.first}..{r.last}", sites)
    for f, t in story_windows(routes):
        reqs += unstored_requests(f, t, f"story:{f}..{t}", sites)
    return _dedupe(reqs)


def sites_from_work(work: Path) -> dict[str, tuple[date, date]]:
    """Each Site's (first day, last day) from a `demo_combined` work folder: the core Sites' `days.json` days
    (added dates included), Kisiwa's first story night (`run1_start`) to its latest story or added night."""
    sys.path.insert(0, str(REPO / "tools"))
    import demo_combined as dc
    import demo_combined_kisiwa as kis

    story = json.loads((work / "story.json").read_text(encoding="utf-8"))
    days_file = work / "days.json"
    days = json.loads(days_file.read_text(encoding="utf-8"))["days"] if days_file.is_file() else []
    last = dc.sites_last_day(story, days, kis.read_days(work))
    out: dict[str, tuple[date, date]] = {}
    for site in story["sites"]:
        if site not in last:
            continue
        if site == "kisiwa":
            first = date.fromisoformat(str(story["kisiwa"]["run1_start"])[:10])
        else:
            first = min(date.fromisoformat(d["day"]) for d in days if d["site"] == site)
        hi = last[site]
        out[SITE_CODE[site]] = (first, hi if isinstance(hi, date) else date.fromisoformat(str(hi)))
    return out


# ---- execution ---------------------------------------------------------------------------------------------------

@dataclass
class Result:
    id: str
    url: str
    status: int
    state: str
    ms: int
    attempts: int = 1
    waits: list[int] = field(default_factory=list)


Fetch = Callable[[str], tuple[int, str]]


def http_fetch(base_url: str, timeout: float = TIMEOUT_SECONDS) -> Fetch:
    """GET base_url + target; returns (status, the `X-AssetOps-Stored` value or "none"); never raises on a status."""
    base = base_url.rstrip("/")

    def fetch(target: str) -> tuple[int, str]:
        try:
            with urllib.request.urlopen(base + target, timeout=timeout) as response:
                response.read()
                return response.status, response.headers.get(HEADER, "none")
        except urllib.error.HTTPError as error:
            return error.code, (error.headers.get(HEADER, "none") if error.headers else "none")
    return fetch


def degraded(status: int, state: str) -> bool:
    """D-E5.47: a 503 (`TEMPORARILY_UNAVAILABLE`) or a stale copy served for a degraded compose."""
    return status == 503 or state in DEGRADED


def needs_retry(status: int, state: str) -> bool:
    """Warm: retried while degraded, or when a 200 body was served but not stored (race, unstored, composed)."""
    return degraded(status, state) or (status == 200 and state not in STORED)


def send(req: Req, fetch: Fetch, *, retry: bool, sleep: Callable[[float], None] = time.sleep,
         clock: Callable[[], float] = time.perf_counter) -> Result:
    """One request; with `retry` the 2/5/10 s rule. `ms` is the client-side time of the last attempt."""
    started = clock()
    status, state = fetch(req.target)
    out = Result(req.id, req.target, status, state, int((clock() - started) * 1000))
    if not retry:
        return out
    for wait in RETRY_WAITS:
        if not needs_retry(out.status, out.state):
            break
        sleep(wait)
        started = clock()
        out.status, out.state = fetch(req.target)
        out.ms = int((clock() - started) * 1000)
        out.attempts += 1
        out.waits.append(wait)
    return out


def throttle(connections: Callable[[], int | None] | None, limit: int = MAX_CONNECTIONS,
             sleep: Callable[[float], None] = time.sleep, say: Callable[[str], None] = print) -> int:
    """Wait while `pg_stat_activity` is above `limit`; returns the number of waits. No counter: no wait."""
    waits = 0
    while connections is not None:
        n = connections()
        if n is None or n <= limit:
            break
        say(f"  waiting: pg_stat_activity {n} > {limit}")
        sleep(CONNECTION_WAIT_SECONDS)
        waits += 1
    return waits


def run(reqs: list[Req], fetch: Fetch, *, workers: int, verify: bool,
        connections: Callable[[], int | None] | None = None, sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.perf_counter, say: Callable[[str], None] = print) -> list[Result]:
    """Send every request in batches of `workers`, throttled before each batch; results in request order."""
    results: list[Result] = []
    lock = threading.Lock()
    done = [0]

    def one(req: Req) -> Result:
        res = send(req, fetch, retry=not verify, sleep=sleep, clock=clock)
        with lock:
            done[0] += 1
            if done[0] % 25 == 0 or done[0] == len(reqs):
                say(f"  {done[0]}/{len(reqs)}")
        return res

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for i in range(0, len(reqs), max(1, workers)):
            throttle(connections, sleep=sleep, say=say)
            results += list(pool.map(one, reqs[i:i + max(1, workers)]))
    return results


def summarise(results: list[Result], *, verify: bool, wall_s: float) -> dict[str, Any]:
    """The report body and its verdict. Warm passes with nothing degraded, failed or unstored; verify passes when
    every answer is a 200 `hit` and the slowest is at most 2.0 s."""
    states: dict[str, int] = {}
    for r in results:
        states[r.state] = states.get(r.state, 0) + 1
    still_degraded = [r.url for r in results if degraded(r.status, r.state)]
    failed = [r.url for r in results if r.status != 200 and not degraded(r.status, r.state)]
    max_ms = max((r.ms for r in results), default=0)
    if verify:
        misses = [r.url for r in results if r.status == 200 and r.state != "hit"]
        slow = [r.url for r in results if r.ms > VERIFY_MAX_MS]
        ok = not (still_degraded or failed or misses or slow)
    else:
        misses = [r.url for r in results if r.status == 200 and r.state not in STORED]
        slow = []
        ok = not (still_degraded or failed or misses)
    hits = states.get("hit", 0)
    reasons: dict[str, str] = {}  # D-WARM.6: the reason per failing request
    for r in results:
        if degraded(r.status, r.state):
            reasons[r.url] = f"degraded after {r.attempts} attempts: HTTP {r.status} {r.state}"
        elif r.status != 200:
            reasons[r.url] = f"failed: HTTP {r.status}"
        elif r.url in misses:
            reasons[r.url] = (f"miss: {r.state}" if verify else f"not stored after {r.attempts} attempts: {r.state}")
        elif r.url in slow:
            reasons[r.url] = f"over 2 s: {r.ms} ms"
    return {"mode": "verify" if verify else "warm", "pass": ok, "requests": len(results), "states": states,
            "hit_percent": round(100.0 * hits / len(results), 2) if results else 0.0,
            "max_ms": max_ms, "wall_seconds": round(wall_s, 1), "degraded": still_degraded, "failed": failed,
            "not_stored" if not verify else "misses": misses, "over_2s": slow, "reasons": reasons,
            "results": [asdict(r) for r in results]}


def unstored_section(results: list[Result]) -> dict[str, Any]:
    """D-WARM.2: the unstored reads' times. Reported, never part of `pass`; any over 2 s goes to the presenter notes."""
    return {"gated": False, "requests": len(results), "max_ms": max((r.ms for r in results), default=0),
            "over_2s": [{"url": r.url, "ms": r.ms} for r in results if r.ms > VERIFY_MAX_MS],
            "non_200": [{"url": r.url, "status": r.status} for r in results if r.status != 200],
            "results": [{"id": r.id, "url": r.url, "status": r.status, "ms": r.ms} for r in results]}


def pg_connections(db_url: str) -> Callable[[], int | None]:
    """The `pg_stat_activity` count on `db_url` (a `postgresql+psycopg://` URL is accepted); None when unreadable."""
    url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)

    def count() -> int | None:
        try:
            import psycopg

            with psycopg.connect(url, connect_timeout=5) as c:
                return int(c.execute("SELECT count(*) FROM pg_stat_activity").fetchone()[0])
        except Exception:  # noqa: BLE001 - a throttle reading; unreadable never blocks
            return None
    return count


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base-url", help="the running serve, e.g. http://127.0.0.1:8990 (not needed for --dry-run)")
    p.add_argument("--work", type=Path, help="a demo_combined work folder: Site dates and its prebuilt-routes.json")
    p.add_argument("--site", action="append", default=[], metavar="CODE:FIRST:LAST",
                   help="a Site's dates (overrides --work for that Site); repeatable")
    p.add_argument("--routes", type=Path, help="the pre-built route list (default: <work>/prebuilt-routes.json, "
                                               "else config/chain/prebuilt-routes-v1.json)")
    p.add_argument("--today", type=date.fromisoformat, help="the UTC day the presets are computed for "
                                                            "(default: today in UTC, as the browser computes it)")
    p.add_argument("--db-url", help="for the pg_stat_activity throttle (omitted: no throttle)")
    p.add_argument("--workers", type=int, help="default 4 (warm) / 1 (verify)")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="count ranges and requests; send nothing")
    p.add_argument("--list", action="store_true", help="with --dry-run, print every request")
    p.add_argument("--report", type=Path, help="default <work>/warm-report.json (--verify: warm-verify.json), else ./")
    a = p.parse_args(argv)

    sites: dict[str, tuple[date, date]] = sites_from_work(a.work) if a.work else {}
    for spec in a.site:
        code, first, last = spec.split(":")
        sites[code] = (date.fromisoformat(first), date.fromisoformat(last))
    if not sites:
        p.error("no Site dates: give --work or --site")
    routes_path = a.routes or (a.work / "prebuilt-routes.json" if a.work and (a.work / "prebuilt-routes.json").is_file()
                               else DEFAULT_ROUTES)
    routes = json.loads(routes_path.read_text(encoding="utf-8")) if routes_path.is_file() else None
    today = a.today or datetime.now(timezone.utc).date()
    rs, reqs = plan(today, sites, routes)
    first, last = data_window(sites)
    print(f"WARM-1 (workaround): today {today}, data window {first}..{last}, {len(rs)} ranges, {len(reqs)} requests "
          f"({sum(1 for r in reqs if r.path.startswith('/api/estate/'))} estate, "
          f"{sum(1 for r in reqs if '/outcome-board' in r.path)} boards); routes {routes_path}")
    print("  sites: " + ", ".join(f"{code} {v[0]}..{v[1]}" for code, v in sorted(sites.items())))
    if a.dry_run:
        for r in rs:
            print(f"  range {r.name:9s} {r.first}..{r.last} ({r.days} d)")
        if a.list:
            for q in reqs:
                print(f"  {q.target}")
        return 0
    if not a.base_url:
        p.error("--base-url is required unless --dry-run")
    workers = a.workers or (1 if a.verify else 4)
    started = time.perf_counter()
    results = run(reqs, http_fetch(a.base_url), workers=workers, verify=a.verify,
                  connections=pg_connections(a.db_url) if a.db_url else None)
    report = summarise(results, verify=a.verify, wall_s=time.perf_counter() - started)
    if a.verify:  # D-WARM.2: the unstored reads of the presets and story ranges, timed and reported, never gated
        report["unstored"] = unstored_section(run(unstored_plan(today, sites, routes), http_fetch(a.base_url),
                                                  workers=workers, verify=True))
    report.update({"workaround": "WARM-1 (D-17N.1; reverses D-ANY.3 for the 17 Nov build only)", "today": str(today),
                   "data_window": [str(first), str(last)], "ranges": len(rs), "workers": workers,
                   "base_url": a.base_url})
    out = a.report or report_path(a.work, a.verify)
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"{report['mode']}: {'PASS' if report['pass'] else 'FAIL'} - {report['requests']} requests, "
          f"{report['hit_percent']}% hits, max {report['max_ms']} ms, {len(report['degraded'])} degraded, "
          f"{len(report['failed'])} failed, wall {report['wall_seconds']} s; report {out}")
    if "unstored" in report:
        u = report["unstored"]
        print(f"unstored (not gated, D-WARM.2): {u['requests']} requests, max {u['max_ms']} ms, "
              f"{len(u['over_2s'])} over 2 s")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
