"""CH-0 U1 (build sheet §2; design §13): the chain coherence check.

    python tools/checks/chain_coherence.py collect --work <work-dir> --database-url <url> --out <bundle-dir> [--known-at <iso>]
    python tools/checks/chain_coherence.py collect --work <work-dir> --base-url http://127.0.0.1:8990 --out <bundle-dir>
    python tools/checks/chain_coherence.py check   --bundle <bundle-dir> [--expect <expected.json>] [--report <out.json>]

`collect` issues GETs only (in process through `tools/demo_combined_finish.py` `app_client`, or over HTTP) and writes
a bundle: `manifest.json` plus one JSON file per response, paginated bodies as `<name>.p<N>.json`. Every window comes
from the work dir's `story.json` and `days.json`. `check` is pure: it reads only the bundle and `screen_routes.json`,
and runs `RULES`; each rule is pure over the bundle and never parses copy, except the info rules COH-9(b) and COH-12.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
ROUTES_FILE = HERE / "fixtures" / "chain_coherence" / "screen_routes.json"
#: CH-2 COH-10: the expected Finding threads per Site (full ids from the CH-2 L4 dry run).
THREADS_FILE = HERE / "fixtures" / "chain_coherence" / "expected-threads.json"
BUNDLE_SCHEMA = "chain-coherence-bundle/1"
REPORT_SCHEMA = "chain-coherence-report/1"
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001", "kisiwa": "KISIWA-001"}
#: CH-5a1 (R6, CH5a1-R Q8; closes MD0-R R10): the Sites whose board day is their Site-local day. EV keeps its
#: `[start, end)` (`Etc/UTC`, `[d 08:00Z, d 16:00Z)`). DIESEL-1-R3q: Kisiwa's boards are its Site-local day too.
LOCAL_DAY_TZ = {"kobo": "Africa/Addis_Ababa", "cold": "Africa/Addis_Ababa", "kisiwa": "Africa/Dar_es_Salaam"}
SUMMARY_SITE_TZ = {"KISIWA-001": "Africa/Dar_es_Salaam"}  # DIESEL-1-R3p: config/operational-actions/kisiwa-001-operational-actions-v1.yaml timezone; Kisiwa boards stay K9's (SITE_CODE)
#: DIESEL-1-R3q: the Kisiwa boards `demo_combined.story_links` opens (offset from S in days, id kind).
KISIWA_BOARD_DAYS = ((-5, "fuel-morning"), (0, "S"))
DOMAIN_SITES = ("COLD-LAB-001", "EV-LAB-001")
ESTATE_WINDOWS = ("week", "S", "month")
HTTP_TIMEOUT_SECONDS = 30
MAX_PAGES = 50


# ---- windows ---------------------------------------------------------------------------------------------------

def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _midnight(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def estate_windows(story: dict) -> dict[str, tuple[str, str]]:
    """`week` is the runbook's Portfolio week (`demo_combined.story_week_query`); `month` is `story_links`' month."""
    sys.path.insert(0, str(TOOLS))
    from demo_combined import story_week_query

    week = urllib.parse.parse_qs(story_week_query(story))
    S = at(story["S"])
    return {"week": (week["from"][0], week["to"][0]),
            "S": (iso(S), iso(S + timedelta(days=1))),
            "month": (iso(S - timedelta(days=28)), iso(S + timedelta(days=3)))}


def day_windows(days: list[dict]) -> list[dict[str, Any]]:
    """Board windows (CH-5a1 R6, DD1b1-R2): a Kobo built day is its Site-local day (`LOCAL_DAY_TZ`; the board reads
    `?date=`); a Cold or EV built day is its whole UTC day, the form `demo_combined.story_links` opens. `estate` is the enclosing UTC-midnight window the estate routes accept (they refuse a non-midnight
    bound)."""
    out = []
    for d in days:
        if d.get("assess") != "build" or not d.get("start") or d.get("site") not in SITE_CODE:
            continue
        if d["site"] == "kisiwa":  # DIESEL-1-R3q: Kisiwa's board days come only from `kisiwa_day_windows`
            continue
        start, end = at(d["start"]), at(d["end"])
        zone = LOCAL_DAY_TZ.get(d["site"])
        if d["site"] in ("cold", "ev"):   # DD1b1-R2: a Cold or EV story day is its whole UTC day
            lo = _midnight(start)
            hi = lo + timedelta(days=1)
        elif zone:
            local = _midnight(start.astimezone(ZoneInfo(zone)))
            lo, hi = local.astimezone(timezone.utc), (local + timedelta(days=1)).astimezone(timezone.utc)
        else:
            lo, hi = start, end
        e_lo, e_hi = _midnight(lo), _midnight(hi - timedelta(microseconds=1)) + timedelta(days=1)
        out.append({"id": f"day:{d['site']}:{d['kind']}:{d['day']}", "site_code": SITE_CODE[d["site"]],
                    "from": iso(lo), "to": iso(hi), "date": local.date().isoformat() if d["site"] == "kobo" else None,
                    "estate": (iso(e_lo), iso(e_hi))})
    return out


def kisiwa_day_windows(story: dict) -> list[dict[str, Any]]:
    """DIESEL-1-R3q: Kisiwa's board days, from `story["kisiwa"]` (not `days.json`), only when Kisiwa is in
    `story["sites"]`. Each is its Site-local day read by `?date=` (mini board), in `day_windows`' row shape."""
    if "kisiwa" not in (story.get("sites") or []) or not story.get("kisiwa"):
        return []
    from datetime import time

    out = []
    for n, kind in KISIWA_BOARD_DAYS:
        day = (at(story["S"]) + timedelta(days=n)).date()
        local = datetime.combine(day, time(0), tzinfo=ZoneInfo(LOCAL_DAY_TZ["kisiwa"]))
        lo, hi = local.astimezone(timezone.utc), (local + timedelta(days=1)).astimezone(timezone.utc)
        e_lo, e_hi = _midnight(lo), _midnight(hi - timedelta(microseconds=1)) + timedelta(days=1)
        out.append({"id": f"day:kisiwa:{kind}:{day.isoformat()}", "site_code": SITE_CODE["kisiwa"],
                    "from": iso(lo), "to": iso(hi), "date": day.isoformat(), "estate": (iso(e_lo), iso(e_hi))})
    return out


# ---- collect ---------------------------------------------------------------------------------------------------

class Getter:
    def get(self, path: str, params: dict[str, str]) -> tuple[int, Any]:
        raise NotImplementedError


class InProcess(Getter):
    def __init__(self, client: Any) -> None:
        self.client = client

    def get(self, path: str, params: dict[str, str]) -> tuple[int, Any]:
        r = self.client.get(path, params=params)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"text": r.text[:4000]}


class Http(Getter):
    def __init__(self, base_url: str) -> None:
        self.base = base_url.rstrip("/")

    def get(self, path: str, params: dict[str, str]) -> tuple[int, Any]:
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}" if params else f"{self.base}{path}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="GET"),
                                        timeout=HTTP_TIMEOUT_SECONDS) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            text = error.read().decode("utf-8", errors="replace")
            try:
                return error.code, json.loads(text)
            except ValueError:
                return error.code, {"text": text[:4000]}


@dataclass
class Collector:
    getter: Getter
    out: Path
    known_at: str | None = None
    requests: list[dict[str, Any]] = field(default_factory=list)
    #: MD-0 (MD0-S2): the domain Sites the story has; a Kobo-only work folder requests no Cold/EV action index.
    domain_sites: tuple[str, ...] = DOMAIN_SITES
    day_names: set[str] = field(default_factory=set)

    def _file(self, name: str, page: int | None) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        return f"{safe}.p{page}.json" if page else f"{safe}.json"

    def fetch(self, name: str, path: str, params: dict[str, str], window: str, *, paged: bool = False) -> Any:
        params = {**params, **({"known_at": self.known_at} if self.known_at else {})}
        page, cursor, first = 1, None, None
        while True:
            p = {**params, **({"cursor": cursor} if cursor else {})}
            status, body = self.getter.get(path, p)
            file = self._file(name, page if paged else None)
            (self.out / file).write_text(json.dumps(body, indent=1, sort_keys=True), encoding="utf-8")
            self.requests.append({"name": name, "path": path, "params": p, "status": status, "file": file,
                                  "window": window, "page": page if paged else None})
            first = body if first is None else first
            cursor = body.get("next_cursor") if (paged and status == 200 and isinstance(body, dict)) else None
            if cursor and page >= MAX_PAGES:
                self.requests[-1]["truncated"] = True  # cut off with a cursor still set: COH-0 fails the bundle
            if not cursor or page >= MAX_PAGES:
                return first if status == 200 else None
            page += 1

    def board(self, name: str, code: str, window: str, lo: str, hi: str, date: str | None) -> Any:
        params = {"date": date} if date else {"from": lo, "to": hi}
        return self.fetch(name, f"/api/sites/{code}/outcome-board", params, window)

    def estate(self, window: str, lo: str, hi: str, prefix: str = "") -> None:
        w = {"from": lo, "to": hi}
        self.fetch(f"{prefix}findings_all.{window}", "/api/estate/findings", {**w, "lens": "all", "state": "all"},
                   window, paged=True)
        # CH-5a2b COH-17 (§B13 R3): the estate chain body of every estate window read.
        self.fetch(f"{prefix}chain_estate.{window}", "/api/estate/chain", w, window)
        if prefix:
            return
        self.fetch(f"portfolio.{window}", "/api/estate/portfolio", {**w, "lens": "all"}, window, paged=True)
        self.fetch(f"findings_opp.{window}", "/api/estate/findings",
                   {**w, "lens": "opportunities", "state": "all"}, window, paged=True)
        self.fetch(f"actions.{window}", "/api/estate/actions", w, window, paged=True)
        for code in self.domain_sites:
            self.fetch(f"action_index.{code}.{window}", f"/api/sites/{code}/domain-work/action-index", w, window,
                       paged=True)
        summary = self.fetch(f"summary.{window}", "/api/estate/outcome-summary", w, window)
        for site in (summary or {}).get("sites", []):
            sw = site.get("window") or {}
            if site.get("site_code") and sw.get("from") and sw.get("to"):
                self.board(f"board_summary.{window}.{site['site_code']}", site["site_code"], window,
                           sw["from"], sw["to"], None)
            self.day_bodies(site, window, lo, hi)
        # CH6b3-R Q2: the "Why?" trace of each estate card.
        for category in _categories():
            self.fetch(f"why_estate.{window}.{category}", "/api/estate/chain/why", {**w, "category": category}, window)

    def day_bodies(self, site: dict, window: str, lo: str, hi: str) -> None:
        """CH6b3-R Q3: COH-18's Site chain bodies. `date` is read only for a mini Site (`board_window`), so a mini Site
        has one body per `window_days` date, deduplicated across windows; Cold and EV one range body per window."""
        code = site.get("site_code")
        if not code:
            return
        path = f"/api/sites/{code}/chain"
        if site.get("domain") != MINI_DOMAIN:
            self.fetch(f"chain_span.{window}.{code}", path, {"from": lo, "to": hi}, window)
            return
        for d in _window_dates({"from": lo, "to": hi}):
            name = f"chain_day.{code}.{d}"
            if name not in self.day_names:
                self.day_names.add(name)
                self.fetch(name, path, {"date": d}, window)


def collect(getter: Getter, story: dict, days: list[dict], out: Path, source: str,
            known_at: str | None = None) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    c = Collector(getter, out, known_at)
    if story.get("sites"):
        c.domain_sites = tuple(SITE_CODE[s] for s in story["sites"] if SITE_CODE.get(s) in DOMAIN_SITES)
    windows = estate_windows(story)
    for wid, (lo, hi) in windows.items():
        c.estate(wid, lo, hi)
    days_out = day_windows(days) + kisiwa_day_windows(story)  # DIESEL-1-R3q: Kisiwa's two boards (`date=`)
    for d in days_out:
        c.board(f"board.{d['id']}", d["site_code"], d["id"], d["from"], d["to"], d["date"])
        c.fetch(f"chain_site.{d['id']}", f"/api/sites/{d['site_code']}/chain",
                {"date": d["date"]} if d["date"] else {"from": d["from"], "to": d["to"]}, d["id"])  # CH-5a2b R3
        c.estate(d["id"], *d["estate"], prefix="day_")
    manifest = {"schema": BUNDLE_SCHEMA, "S": story["S"], "code": story.get("code"),
                "collected_at": iso(datetime.now(timezone.utc)), "source": source,
                "freshness": "not ticked" if source == "in-process" else "as served",
                "known_at": known_at, "threads": True,  # CH-2: this tool revision expects the `thread` fields
                "lifecycle": True,  # CH-3: and the thread `state_day` and the Portfolio `action_segment_no`
                "opportunities": True,  # CH-4: and the Findings `opportunities` and the Portfolio `opportunity.items`
                "claims": True,  # CH-5a2b: and `/estate/chain` per estate window and the summaries' `claims`
                "full_claims": True,  # CH6b3-R Q1, Q2: and the summary, board and `why_estate` bodies COH-17 compares
                "day_bodies": True,  # CH6b3-R Q3: and the `chain_day` / `chain_span` bodies COH-18 sums
                "windows": {**{k: {"from": lo, "to": hi} for k, (lo, hi) in windows.items()},
                            **{d["id"]: {"from": d["from"], "to": d["to"], "site_code": d["site_code"],
                                         "estate": {"from": d["estate"][0], "to": d["estate"][1]}}
                               for d in days_out}},
                "requests": c.requests}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


# ---- bundle ----------------------------------------------------------------------------------------------------

@dataclass
class Body:
    name: str
    path: str
    window: str
    status: int
    body: Any
    files: list[str]
    params: dict[str, str] = field(default_factory=dict)  # the first request's query, for the self-link check
    truncated: bool = False


class Bundle:
    """The bundle's bodies by request name; the pages of one name are merged (`rows` concatenated, other keys from
    page 1). A non-200 body is kept with its status and never treated as data by a rule."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        self.windows: dict[str, dict[str, Any]] = self.manifest.get("windows", {})
        self.bodies: dict[str, Body] = {}
        for req in self.manifest["requests"]:
            body = json.loads((self.root / req["file"]).read_text(encoding="utf-8"))
            have = self.bodies.get(req["name"])
            if have is None:
                self.bodies[req["name"]] = Body(req["name"], req["path"], req["window"], req["status"], body,
                                                [req["file"]], dict(req.get("params") or {}),
                                                bool(req.get("truncated")))
                continue
            have.files.append(req["file"])
            have.truncated = have.truncated or bool(req.get("truncated"))
            if req["status"] != 200:
                have.status = req["status"]
            elif isinstance(have.body, dict) and isinstance(body, dict):
                have.body = {**have.body, "rows": [*(have.body.get("rows") or []), *(body.get("rows") or [])]}

    def get(self, name: str) -> Any:
        b = self.bodies.get(name)
        return b.body if b is not None and b.status == 200 else None

    def files(self, name: str) -> list[str]:
        b = self.bodies.get(name)
        return list(b.files) if b else []

    def ok(self) -> Iterator[Body]:
        return (b for b in self.bodies.values() if b.status == 200)

    def estate_windows(self) -> list[str]:
        return [w for w in ESTATE_WINDOWS if w in self.windows]

    def day_windows(self) -> list[str]:
        return [w for w in self.windows if w.startswith("day:")]

    def contains(self, outer: str, inner: str) -> bool:
        o, i = self.windows[outer], self.windows[inner]
        return at(o["from"]) <= at(i["from"]) and at(i["to"]) <= at(o["to"])


def finding(rule: str, site_code: str | None, window: str | None, subject: str | None, detail: str,
            bodies: list[str]) -> dict[str, Any]:
    return {"rule": rule, "site_code": site_code, "window": window, "subject": subject, "detail": detail,
            "bodies": sorted(set(bodies))}


def _rows(body: Any) -> list[dict]:
    return list(body.get("rows") or []) if isinstance(body, dict) else []


def _walk(node: Any, path: str = "$") -> Iterator[tuple[str, Any, Any, list[dict]]]:
    """(path, key, value, ancestors) for every dict entry; `ancestors` are the enclosing dicts, innermost last."""
    stack: list[tuple[Any, str, list[dict]]] = [(node, path, [])]
    while stack:
        cur, p, anc = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                yield f"{p}.{k}", k, v, [*anc, cur]
                stack.append((v, f"{p}.{k}", [*anc, cur]))
        elif isinstance(cur, list):
            for n, v in enumerate(cur):
                stack.append((v, f"{p}[{n}]", anc))


def _site_of(ancestors: list[dict], default: str | None) -> str | None:
    for d in reversed(ancestors):
        if isinstance(d.get("site_code"), str):
            return d["site_code"]
    return default


def _actions(bundle: Bundle, window: str) -> list[dict[str, Any]]:
    """Every Action in a window: the estate (mini) index with `source_finding_id`, and each domain index with
    `origin.finding_id`. `created` is the estate `created_at`, or the domain row's `raised_at` (pre-flight P2: the
    domain index carries no `created_at`)."""
    out: dict[str, dict[str, Any]] = {}
    for r in _rows(bundle.get(f"actions.{window}")):
        out[str(r["action_id"])] = {"action_id": str(r["action_id"]), "origin": r.get("source_finding_id"),
                                    "created": r.get("created_at"), "site_code": r.get("site_code"),
                                    "verification_outcome": r.get("verification_outcome"),
                                    "file": f"actions.{window}"}
    for code in DOMAIN_SITES:
        for r in _rows(bundle.get(f"action_index.{code}.{window}")):
            out.setdefault(str(r["action_id"]), {
                "action_id": str(r["action_id"]), "origin": (r.get("origin") or {}).get("finding_id"),
                "created": r.get("raised_at") or r.get("recorded_at"), "site_code": code,
                "verification_outcome": None, "file": f"action_index.{code}.{window}"})
    return list(out.values())


def _board_findings(board: dict, primary_only: bool = False) -> Iterator[tuple[str, str]]:
    """The board's FINDING issues as (row category, finding id). CH-5a2 B5: `primary_only` keeps only the
    issue on the Finding's lens row (`primary` true); a checked-row or secondary appearance is not a lens."""
    for row in board.get("rows") or []:
        for issue in row.get("issues") or []:
            ref = issue.get("ref")
            if primary_only and issue.get("primary") is not True:
                continue
            if issue.get("kind") == "FINDING" and isinstance(ref, dict) and ref.get("finding_id"):
                yield row.get("category"), str(ref["finding_id"])


def _board_hrefs(board: dict) -> list[str]:
    out = []
    for row in board.get("rows") or []:
        for key in ("in_hand", "earlier", "issues"):
            out += [i["href"] for i in row.get(key) or [] if isinstance(i, dict) and isinstance(i.get("href"), str)]
        mnh = row.get("must_not_harm")
        if isinstance(mnh, dict) and isinstance(mnh.get("href"), str):
            out.append(mnh["href"])
    return out


# ---- rules -----------------------------------------------------------------------------------------------------

def load_routes(path: Path = ROUTES_FILE) -> list[str]:
    return list(json.loads(path.read_text(encoding="utf-8"))["routes"])


def _segments_match(pattern: list[str], path: list[str]) -> bool:
    return all(a == b or (a.startswith(":") and b != "") for a, b in zip(pattern, path))


def route_matches(pattern: str, pathname: str) -> bool:
    """`:name` matches exactly one non-empty segment; a trailing `/*` matches the rest (one or more segments)."""
    if pattern == "/" or pathname in ("", "/"):
        return pattern == pathname
    p, s = pattern.strip("/").split("/"), pathname.strip("/").split("/")
    if pattern.endswith("/*"):
        return len(s) > len(p) - 1 and _segments_match(p[:-1], s)
    return len(p) == len(s) and _segments_match(p, s)


def link_problem(href: str, routes: list[str]) -> str | None:
    if href.startswith("/api"):
        return "an API URL, not a screen"
    if "://" in href:
        return "an absolute URL, not a screen"
    pathname = href.split("#", 1)[0].split("?", 1)[0]
    if not any(route_matches(r, pathname) for r in routes):
        return f"no screen route matches {pathname}"
    return None


LINK_KEYS = ("href", "destination", "overview_href")
#: A `links` entry whose key ends with this is the link's display text (`links.current_view_label`), not a link.
LABEL_SUFFIX = "_label"


def coh0_missing_data(bundle: Bundle) -> list[dict]:
    """A request that did not return 200, or a paged read cut off at MAX_PAGES, leaves every rule over it vacuous;
    the bundle then fails rather than passing on missing data (CH-0 review M1)."""
    out = []
    for b in bundle.bodies.values():
        if b.status != 200:
            out.append(finding("COH-0", None, b.window, b.name, f"request {b.path} returned status {b.status}",
                               b.files))
        if b.truncated:
            out.append(finding("COH-0", None, b.window, b.name,
                               f"request {b.path} was cut off at {MAX_PAGES} pages with a cursor still set",
                               b.files))
    return out


def _board_query(path: str, query: dict[str, list[str]], window: Any = None) -> dict[str, list[str]]:
    """CH0-R addendum, CH-5a1 R6: on the outcome-board route only, `date=D` is the same read as the body's own
    `window.from`/`window.to` (D's Site-local day; the screen calls Kobo's board with `date`, the body names the
    range). Without a body window there is no equivalence (never UTC midnights)."""
    if path.endswith("/outcome-board") and set(query) == {"date"} and len(query["date"]) == 1:
        try:
            datetime.strptime(query["date"][0], "%Y-%m-%d")
        except ValueError:
            return query
        if isinstance(window, dict) and window.get("from") and window.get("to"):
            return {"from": [str(window["from"])], "to": [str(window["to"])]}
    return query


def is_own_self_link(b: Body, where: str, href: str) -> bool:
    """CH0-R: the one exempt `/api` link is a body's root `links.self`, equal to that body's own request path and
    query (with the outcome-board `date` equivalence above). A nested or non-equal self stays a COH-1 contradiction."""
    if where != "$.links.self":
        return False
    url = urllib.parse.urlsplit(href)
    own = urllib.parse.parse_qs(urllib.parse.urlencode(b.params), keep_blank_values=True)
    theirs = urllib.parse.parse_qs(url.query, keep_blank_values=True)
    window = b.body.get("window") if isinstance(b.body, dict) else None
    return url.path == b.path and _board_query(b.path, own, window) == _board_query(url.path, theirs, window)


def coh1_links(bundle: Bundle, routes: list[str] | None = None) -> list[dict]:
    routes = routes if routes is not None else load_routes()
    out, seen = [], set()
    for b in bundle.ok():
        default_site = b.body.get("site_code") if isinstance(b.body, dict) else None
        for path, key, value, anc in _walk(b.body):
            hrefs: list[tuple[str, str]] = []
            if key == "links" and isinstance(value, dict):
                hrefs = [(f"{path}.{k}", v) for k, v in value.items()
                         if isinstance(v, str) and not k.endswith(LABEL_SUFFIX)]
            elif isinstance(value, str) and (key in LINK_KEYS or key.endswith("_href")):
                hrefs = [(path, value)]
            for where, href in hrefs:
                if is_own_self_link(b, where, href):
                    continue
                problem = link_problem(href, routes)
                site = _site_of(anc, default_site)
                if problem and (b.window, site, href) not in seen:
                    seen.add((b.window, site, href))
                    out.append(finding("COH-1", site, b.window, href, f"{b.name} {where}: {problem}", b.files))
    return out


def coh2_action_on_portfolio(bundle: Bundle) -> list[dict]:
    out = []
    for w in bundle.estate_windows():
        portfolio = {str(r["finding_id"]): r for r in _rows(bundle.get(f"portfolio.{w}")) if r.get("finding_id")}
        for a in _actions(bundle, w):
            row = portfolio.get(str(a["origin"])) if a["origin"] else None
            if row is not None and row.get("action_id") is None:
                out.append(finding("COH-2", row.get("site_code"), w, a["action_id"],
                                   f"Action {a['action_id']} answers Finding {a['origin']}, but its Portfolio row "
                                   "has no action_id", [*bundle.files(f"portfolio.{w}"), *bundle.files(a["file"])]))
    return out


def _coh3_evaluate(bundle: Bundle) -> Iterator[tuple[dict, str, dict, bool]]:
    """COH-3's one loop: each (board, day, Action, linked) whose origin Finding is on the board and which existed by
    the board window's end."""
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board:
            continue
        to = at(bundle.windows[d]["to"])
        actions: dict[str, dict] = {}
        for w in bundle.estate_windows():
            if bundle.contains(w, d):
                for a in _actions(bundle, w):
                    actions.setdefault(a["action_id"], a)
        hrefs = _board_hrefs(board)
        on_board = {f for _, f in _board_findings(board)}
        for a in actions.values():
            if a["origin"] and str(a["origin"]) in on_board and a["created"] and at(a["created"]) <= to:
                yield board, d, a, any(a["action_id"] in h for h in hrefs)


def coh3_pairs(bundle: Bundle) -> Iterator[tuple[Any, str, str, str, bool]]:
    """DD1b1-R Q6: the pairs COH-3 evaluates, `(site_code, day, action_id, finding_id, linked)`. A rule that reports
    only findings cannot show it looked at anything, so F-COH3 and the probe count these."""
    for board, d, a, linked in _coh3_evaluate(bundle):
        yield board.get("site_code"), d, a["action_id"], str(a["origin"]), linked


def coh3_action_on_board(bundle: Bundle) -> list[dict]:
    return [finding("COH-3", board.get("site_code"), d, a["action_id"],
                    f"Finding {a['origin']} is on the board and Action {a['action_id']} answering it "
                    "existed by the window end, but no board link names the Action",
                    [*bundle.files(f"board.{d}"), *bundle.files(a["file"])])
            for board, d, a, linked in _coh3_evaluate(bundle) if not linked]


def _finding_rows(bundle: Bundle, name: str, site_code: str | None = None) -> dict[str, dict]:
    return {str(r["finding_id"]): r for r in _rows(bundle.get(name))
            if r.get("finding_id") and (site_code is None or r.get("site_code") == site_code)}


def coh4_findings_contain(bundle: Bundle) -> list[dict]:
    out = []
    for w in bundle.estate_windows():
        if bundle.get(f"findings_all.{w}") is None:
            continue
        index = _finding_rows(bundle, f"findings_all.{w}")
        for r in _rows(bundle.get(f"portfolio.{w}")):
            if r.get("finding_id") and str(r["finding_id"]) not in index:
                out.append(finding("COH-4", r.get("site_code"), w, str(r["finding_id"]),
                                   "a Portfolio Finding is missing from the Findings list of the same window",
                                   [*bundle.files(f"portfolio.{w}"), *bundle.files(f"findings_all.{w}")]))
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board or bundle.get(f"day_findings_all.{d}") is None:
            continue
        index = _finding_rows(bundle, f"day_findings_all.{d}", board.get("site_code"))
        for f in sorted({f for _, f in _board_findings(board)}):
            if f not in index:
                out.append(finding("COH-4", board.get("site_code"), d, f,
                                   "a board Finding is missing from the Findings list for the board's window and Site",
                                   [*bundle.files(f"board.{d}"), *bundle.files(f"day_findings_all.{d}")]))
    return out


#: The outcome-map/1 reading of a board category as a Findings lens (build sheet §2.3 COH-5): an Optimize-cost
#: Finding belongs on the Cost lens, a Protect-asset one on Risks and a Grow-revenue one on Opportunities;
#: ASSURE_PERFORMANCE has no lens and is skipped. Pre-flight P3: no backend constant states this map.
CATEGORY_LENS = {"OPTIMIZE_COST": "COST", "PROTECT_ASSET": "RISK", "GROW_REVENUE": "OPPORTUNITY"}


def coh5_lens(bundle: Bundle) -> list[dict]:
    out, seen = [], set()
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board:
            continue
        index = _finding_rows(bundle, f"day_findings_all.{d}", board.get("site_code"))
        for category, f in _board_findings(board, primary_only=True):
            lens = CATEGORY_LENS.get(category)
            row = index.get(f)
            if lens and row is not None and lens not in (row.get("lens_flags") or []) and (d, f, lens) not in seen:
                seen.add((d, f, lens))
                out.append(finding("COH-5", board.get("site_code"), d, f"{f}:{lens}",
                                   f"on the board under {category}, but its Findings row lens_flags "
                                   f"{row.get('lens_flags')} lack {lens}",
                                   [*bundle.files(f"board.{d}"), *bundle.files(f"day_findings_all.{d}")]))
    return out


def _shows_opportunity(board: dict) -> bool:
    if any(i.get("kind") == "OPPORTUNITY" for row in board.get("rows") or [] for i in row.get("issues") or []):
        return True
    return any(isinstance(w, dict) and w.get("badge") == "OPPORTUNITY"
               for holder in [board, *(board.get("rows") or [])] for w in holder.get("warnings") or [])


def _opportunity_items(body: Any, key: str) -> list[dict]:
    """CH-4: the opportunity items of a Findings body (`opportunities`) or of the Portfolio `opportunity` block
    (`items`); one shape, built by `chain.opportunities.opportunity_items` for both screens."""
    if not isinstance(body, dict):
        return []
    holder = body if key == "opportunities" else body.get("opportunity")
    if not isinstance(holder, dict):
        return []
    return [i for i in holder.get(key) or [] if isinstance(i, dict)]


def coh6_opportunity(bundle: Bundle) -> list[dict]:
    """A board that shows an opportunity has an item for its Site on the Findings Opportunities lens and in a FOUND
    Portfolio opportunity block, in every estate window containing the board day (CH-4: read from the opportunity
    items, not from Finding rows or the retired UNSUPPORTED literal)."""
    out, seen = [], set()
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board or not _shows_opportunity(board):
            continue
        site = board.get("site_code")
        for w in bundle.estate_windows():
            if not bundle.contains(w, d):
                continue
            opp = bundle.get(f"findings_opp.{w}")
            if (opp is not None and not any(i.get("site_code") == site for i in _opportunity_items(opp, "opportunities"))
                    and (w, site, "findings:opportunities") not in seen):
                seen.add((w, site, "findings:opportunities"))
                out.append(finding("COH-6", site, w, "findings:opportunities",
                                   f"board {d} shows an opportunity, but the Opportunities lens lists no item for "
                                   "the Site", [*bundle.files(f"board.{d}"), *bundle.files(f"findings_opp.{w}")]))
            portfolio = bundle.get(f"portfolio.{w}")
            state = ((portfolio or {}).get("opportunity") or {}).get("state")
            listed = any(i.get("site_code") == site for i in _opportunity_items(portfolio, "items"))
            if (portfolio is not None and (state != "FOUND" or not listed)
                    and (w, site, "portfolio:opportunity") not in seen):
                seen.add((w, site, "portfolio:opportunity"))
                out.append(finding("COH-6", site, w, "portfolio:opportunity",
                                   f"board {d} shows an opportunity, but the Portfolio opportunity is {state} and "
                                   f"{'lists' if listed else 'does not list'} the Site",
                                   [*bundle.files(f"board.{d}"), *bundle.files(f"portfolio.{w}")]))
    return out


def _coh7a_window(site: dict, requested: dict) -> tuple[str, str]:
    """CH5a1-R2 (COH-7a, Architect 6; supersedes MD0-S4 R3): the expected window of one summary Site card.

    A mini Site's summary card is ONE Site-local day by design: `[local 00:00, next local 00:00)` of
    `chain.read.window_day(from, to, tz)` (CH5a2-R R7, owner-approved: the board route's day rule, so a UTC-midnight
    one-day pair is the picked calendar date). Both rules are imported from the backend, never re-derived here. Every other Site's window must equal the requested window.
    Merge note: MD-0's branch also edits this file; keep this helper and its one call when resolving."""
    if site.get("domain") != "mini_grid":
        return requested["from"], requested["to"]
    backend = str(TOOLS.parent / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from assetops_backend.chain.read import board_day, window_day

    tz = {**{SITE_CODE[k]: z for k, z in LOCAL_DAY_TZ.items()}, **SUMMARY_SITE_TZ}.get(site.get("site_code"))
    lo, hi = board_day(window_day(at(requested["from"]), at(requested["to"]), tz), tz)
    return iso(lo), iso(hi)


def coh7_summary_basis(bundle: Bundle) -> list[dict]:
    out = []
    for w in bundle.estate_windows():
        summary = bundle.get(f"summary.{w}")
        if not summary:
            continue
        files = bundle.files(f"summary.{w}")
        sites = summary.get("sites") or []
        requested = bundle.windows[w]
        for s in sites:
            # CH6b1-R Q2: the per-domain basis (mini DAY on `window_day`, every other Site PERIOD on the requested
            # window); two bases in one summary are correct by design. A failed Site (None basis) or a card with no
            # domain has no per-domain rule to judge.
            basis, domain = s.get("window_basis"), s.get("domain")
            expected = "DAY" if domain == "mini_grid" else "PERIOD"
            if basis is not None and domain is not None and basis != expected:
                out.append(finding("COH-7a", s.get("site_code"), w, "window_basis",
                                   f"summary Site window basis {basis} is not the {expected} basis of its domain",
                                   files))
            sw = s.get("window") or {}
            want = _coh7a_window(s, requested)  # CH5a1-R2: a mini Site's card is one Site-local day
            if (sw.get("from"), sw.get("to")) != want:
                out.append(finding("COH-7a", s.get("site_code"), w, "window",
                                   f"summary Site window [{sw.get('from')}, {sw.get('to')}) is not the expected "
                                   f"[{want[0]}, {want[1]})", files))
            name = f"board_summary.{w}.{s.get('site_code')}"
            board = bundle.get(name)
            if board is None:
                continue
            board_rows = {r.get("category"): r for r in board.get("rows") or []}
            for r in s.get("rows") or []:
                b = board_rows.get(r.get("category"))
                here = (r.get("state"), r.get("headline_money"))
                there = None if b is None else (b.get("state"), b.get("headline_money"))
                if here != there:
                    out.append(finding("COH-7b", s.get("site_code"), w, r.get("category"),
                                       f"summary {here} differs from the board at the same window {there}",
                                       [*files, *bundle.files(name)]))
    return out


def coh8_verified(bundle: Bundle) -> list[dict]:
    out = []
    for w in bundle.estate_windows():
        portfolio = bundle.get(f"portfolio.{w}")
        if portfolio is None:
            continue
        rows = {str(r["finding_id"]): r for r in _rows(portfolio) if r.get("finding_id")}
        progress = {str(p.get("action_id")): p for p in (portfolio.get("progress") or {}).get("rows") or []}
        for a in _actions(bundle, w):
            row = rows.get(str(a["origin"])) if a["origin"] else None
            if a["verification_outcome"] != "VERIFIED" or row is None:
                continue
            problems = []
            if row.get("verification_outcome") != "VERIFIED":
                problems.append(f"the Portfolio row reads verification_outcome {row.get('verification_outcome')}")
            p = progress.get(a["action_id"])
            if p is None:
                problems.append("its progress row is missing")
            elif p.get("origin_selected") is not True:  # CH-5a2 B6: the thread-based fact, not the exact revision
                problems.append(f"its progress row has origin_selected {p.get('origin_selected')}")
            if problems:
                out.append(finding("COH-8", row.get("site_code") or a["site_code"], w, a["action_id"],
                                   f"Action {a['action_id']} is VERIFIED, but " + "; ".join(problems),
                                   [*bundle.files(f"portfolio.{w}"), *bundle.files(a["file"])]))
    return out


def coh9_day_counts(bundle: Bundle) -> list[dict]:
    out = []
    for w in bundle.estate_windows():
        portfolio = bundle.get(f"portfolio.{w}")
        if portfolio is None:
            continue
        coverage = {str(s.get("site_id")): s for s in (portfolio.get("coverage") or {}).get("sites") or []}
        codes = {str(r.get("site_id")): r.get("site_code") for r in _rows(portfolio)}
        for c in (portfolio.get("summary") or {}).get("checked_days") or []:
            days = (coverage.get(str(c.get("site_id"))) or {}).get("days") or {}
            if (c.get("checked"), c.get("requested")) != (days.get("checked"), days.get("requested")):
                out.append(finding("COH-9a", codes.get(str(c.get("site_id"))) or c.get("site_name"), w,
                                   str(c.get("site_id")),
                                   f"checked_days {c.get('checked')}/{c.get('requested')} but coverage days "
                                   f"{days.get('checked')}/{days.get('requested')}", bundle.files(f"portfolio.{w}")))
    return out


DAY_PHRASE = re.compile(r"(\d+) of (\d+) (?:well-observed )?days|(\d+) of the last (\d+) days")


def info_coh9b(bundle: Bundle) -> list[dict]:
    """Info only, never failing (I-15): every day-count phrase in board texts, per Site and window."""
    out = []
    for b in bundle.ok():
        if not b.name.startswith("board") or not isinstance(b.body, dict):
            continue
        for row in b.body.get("rows") or []:
            texts = [("subline", row.get("subline")), ("not_measured_text", row.get("not_measured_text"))]
            texts += [(f"contributors[{n}].text", c.get("text"))
                      for n, c in enumerate(row.get("contributors") or []) if isinstance(c, dict)]
            for where, text in texts:
                for m in DAY_PHRASE.finditer(text if isinstance(text, str) else ""):
                    out.append({"site_code": b.body.get("site_code"), "window": b.window, "body": b.name,
                                "category": row.get("category"), "where": where, "phrase": m.group(0)})
    return out


def _source_mode(ancestors: list[dict]) -> str | None:
    for d in reversed(ancestors):
        sp = d.get("source_provenance")
        if isinstance(sp, dict):
            return sp.get("classification") or sp.get("state")
        if isinstance(d.get("source_mode"), str):
            return d["source_mode"]
    return None


def info_coh12(bundle: Bundle) -> list[dict]:
    """Info only, never failing (DS-R1 item 4): every body string containing "example data", with the Site, key path
    and the source mode where the body states one (`source_provenance` / `source_mode`). Owning fix: CH-5a."""
    out = []
    for b in bundle.ok():
        default_site = b.body.get("site_code") if isinstance(b.body, dict) else None
        for path, _key_name, value, anc in _walk(b.body):
            if isinstance(value, str) and "example data" in value.lower():
                out.append({"site_code": _site_of(anc, default_site), "window": b.window, "body": b.name,
                            "path": path, "source_mode": _source_mode(anc), "text": value[:200]})
    return out


def _threaded(bundle: Bundle) -> bool:
    """CH-2: a bundle stamped `threads` (every bundle this tool collects) is judged by COH-10/COH-11 and must carry the
    thread fields; an unstamped bundle collected before CH-2 is not judged by them. The stamp, not the presence of the
    key, decides, so a regression that drops the key fails instead of reading as a pre-CH-2 bundle (review L3)."""
    return bool(bundle.manifest.get("threads"))


def _missing_thread_keys(bundle: Bundle, rule: str, key: str) -> list[dict]:
    """COH-0 style: a stamped bundle whose Portfolio rows lack `key` fails rather than passing vacuously."""
    out = []
    for w in bundle.estate_windows():
        rows = _rows(bundle.get(f"portfolio.{w}"))
        gone = [r for r in rows if key not in r]
        if gone:
            out.append(finding(rule, None, w, key, f"{len(gone)} of {len(rows)} Portfolio rows carry no `{key}` key",
                               bundle.files(f"portfolio.{w}")))
    return out


def load_threads(path: Path = THREADS_FILE) -> list[dict]:
    return list(json.loads(Path(path).read_text(encoding="utf-8"))["threads"])


def _board_refs(board: dict) -> Iterator[dict]:
    for row in board.get("rows") or []:
        for issue in row.get("issues") or []:
            ref = issue.get("ref")
            if issue.get("kind") == "FINDING" and isinstance(ref, dict) and ref.get("finding_id"):
                yield ref


def _opportunities_stamped(bundle: Bundle) -> bool:
    """CH-4: a bundle stamped `opportunities` (every bundle this tool collects from CH-4 on) carries the Findings
    `opportunities` array and the Portfolio `opportunity.items`; an older bundle is not judged by COH-16 or by the
    COH-10 opportunity leg."""
    return bool(bundle.manifest.get("opportunities"))


def _coh10_opportunity_thread(bundle: Bundle, t: dict) -> list[dict]:
    """CH-4 COH-10 leg: an expected opportunity thread is read on one thread id across the Findings item, the
    Portfolio item and the board OPPORTUNITY issue `ref.thread`; and, read as known now, each item counts every
    expected study as an occurrence (`occurrences` is the thread's visible occurrences, not the window's)."""
    if not _opportunities_stamped(bundle):
        return []
    out: list[dict] = []
    ids: dict[Any, set] = {}  # thread id -> the bodies it was read on
    want = len(t.get("opportunities") or [])
    for w in bundle.estate_windows():
        for name, key in ((f"findings_opp.{w}", "opportunities"), (f"portfolio.{w}", "items")):
            for i in _opportunity_items(bundle.get(name), key):
                if i.get("site_code") != t["site_code"] or i.get("mechanism") != t.get("mechanism"):
                    continue
                ids.setdefault(i.get("thread_id"), set()).update(bundle.files(name))
                if bundle.manifest.get("known_at") is None and i.get("occurrences") != want:
                    out.append(finding("COH-10", t["site_code"], w, t["name"], f"opportunity thread {t['name']} "
                                       f"shows {i.get('occurrences')} occurrences on {name}; expected {want}",
                                       bundle.files(name)))
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board or board.get("site_code") != t["site_code"]:
            continue
        for row in board.get("rows") or []:
            for issue in row.get("issues") or []:
                ref = issue.get("ref")
                if issue.get("kind") == "OPPORTUNITY" and isinstance(ref, dict) and isinstance(ref.get("thread"), dict):
                    ids.setdefault(ref["thread"].get("id"), set()).update(bundle.files(f"board.{d}"))
    if not ids:
        out.append(finding("COH-10", t["site_code"], None, t["name"], f"no Findings or Portfolio item shows "
                           f"opportunity thread {t['name']}", []))
    elif len(ids) > 1:
        out.append(finding("COH-10", t["site_code"], None, t["name"], f"opportunity thread {t['name']} is split "
                           f"across {len(ids)} thread ids", sorted(f for v in ids.values() for f in v)))
    return out


def coh10_thread_identity(bundle: Bundle, threads: list[dict] | None = None) -> list[dict]:
    """CH-2 COH-10: each expected thread's Findings sit on one thread as occurrences 1..n of n, on every Portfolio
    row that shows them; each thread is observed at least once; a board ref's thread agrees with the Portfolio's
    for the same Finding in an estate window containing the board day."""
    if not _threaded(bundle):
        return []
    missing = _missing_thread_keys(bundle, "COH-10", "thread")
    if missing:
        return missing
    if threads is None:  # a fixture bundle names its own expectations; a collected bundle uses THREADS_FILE
        threads = bundle.manifest["expected_threads"] if "expected_threads" in bundle.manifest else load_threads()
    out: list[dict] = []
    seen: dict[str, dict[str, dict]] = {}  # window -> finding_id -> thread
    for w in bundle.estate_windows():
        seen[w] = {str(r["finding_id"]).lower(): r.get("thread") for r in _rows(bundle.get(f"portfolio.{w}"))
                   if r.get("finding_id")}
    for t in threads:
        fids = [f.lower() for f in t.get("findings") or []]
        if not fids:
            out.extend(_coh10_opportunity_thread(bundle, t))  # CH-4: an opportunity-only thread
            continue
        ids, observed = set(), False
        for w, rows in seen.items():
            files = bundle.files(f"portfolio.{w}")
            for n, f in enumerate(fids, start=1):
                if f not in rows:
                    continue
                observed = True
                th = rows[f]
                if th is None:
                    out.append(finding("COH-10", t["site_code"], w, f, f"Finding {f} of thread {t['name']} has no "
                                       "thread on its Portfolio row", files))
                    continue
                ids.add(th.get("id"))
                if (th.get("occurrence_no"), th.get("occurrences")) != (n, len(fids)):
                    out.append(finding("COH-10", t["site_code"], w, f, f"Finding {f} is occurrence "
                                       f"{th.get('occurrence_no')} of {th.get('occurrences')}; expected {n} of "
                                       f"{len(fids)} on thread {t['name']}", files))
        if not observed:
            out.append(finding("COH-10", t["site_code"], None, t["name"], f"no Portfolio row shows a Finding of "
                               f"thread {t['name']}", []))
        if len(ids) > 1:
            out.append(finding("COH-10", t["site_code"], None, t["name"], f"thread {t['name']} is split across "
                               f"{len(ids)} thread ids", []))
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board:
            continue
        for ref in _board_refs(board):
            f = str(ref["finding_id"]).lower()
            for w in bundle.estate_windows():
                if not bundle.contains(w, d) or f not in seen.get(w, {}):
                    continue
                want, got = seen[w][f], ref.get("thread")
                key = (lambda x: None if x is None else (x.get("id"), x.get("occurrence_no"), x.get("occurrences")))
                if key(want) != key(got):
                    out.append(finding("COH-10", board.get("site_code"), d, f, f"board thread {key(got)} != "
                                       f"Portfolio ({w}) thread {key(want)}",
                                       [*bundle.files(f"board.{d}"), *bundle.files(f"portfolio.{w}")]))
    return out


def coh11_actions_linked(bundle: Bundle) -> list[dict]:
    """CH-2 COH-11 (ruling R1, replaces the design's NOT NULL step e): every Action whose origin Finding has a
    Portfolio row (where COH-2 applies) finds that row on a thread, and the Action the row shows carries its own
    `chain_action_thread` link (`action_thread_id`) to that same thread (review L2). An Action no row selects is not
    observable here (a later Action wins the row) and is covered by the backfill's SQL proof."""
    if not _threaded(bundle):
        return []
    missing = _missing_thread_keys(bundle, "COH-11", "thread") + _missing_thread_keys(bundle, "COH-11",
                                                                                     "action_thread_id")
    if missing:
        return missing
    out = []
    for w in bundle.estate_windows():
        portfolio = {str(r["finding_id"]): r for r in _rows(bundle.get(f"portfolio.{w}")) if r.get("finding_id")}
        for a in _actions(bundle, w):
            row = portfolio.get(str(a["origin"])) if a["origin"] else None
            if row is None:
                continue
            files = [*bundle.files(f"portfolio.{w}"), *bundle.files(a["file"])]
            if row.get("thread") is None:
                out.append(finding("COH-11", row.get("site_code"), w, a["action_id"],
                                   f"Action {a['action_id']} answers Finding {a['origin']}, whose Portfolio row has "
                                   "no thread", files))
            elif str(row.get("action_id")) == a["action_id"] and (
                    row.get("action_thread_id") is None or row["action_thread_id"] != row["thread"].get("id")):
                out.append(finding("COH-11", row.get("site_code"), w, a["action_id"],
                                   f"Action {a['action_id']} has no thread link to its origin Finding's thread "
                                   f"(action_thread_id={row.get('action_thread_id')})", files))
    return out


# ---- CH-3 lifecycle rules ----------------------------------------------------------------------------------------

VERIFIED_THREAD_STATES = ("RESOLVED_MONITORING", "CLOSED")


def _lifecycle(bundle: Bundle) -> bool:
    """CH-3: a bundle stamped `lifecycle` must carry `state_day` on every board and Portfolio thread and
    `action_segment_no` on every Portfolio row; an unstamped bundle is not judged by COH-13 to COH-15."""
    return bool(bundle.manifest.get("lifecycle"))


def _missing_state_day(bundle: Bundle, rule: str) -> list[dict]:
    """COH-0 style: a stamped bundle whose board or Portfolio thread lacks `state_day` fails rather than passing
    vacuously."""
    out = []
    for w in bundle.estate_windows():
        rows = _rows(bundle.get(f"portfolio.{w}"))
        gone = [r for r in rows if isinstance(r.get("thread"), dict) and "state_day" not in r["thread"]]
        if gone:
            out.append(finding(rule, None, w, "state_day", f"{len(gone)} Portfolio threads carry no `state_day`",
                               bundle.files(f"portfolio.{w}")))
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        gone = [r for r in _board_refs(board or {}) if isinstance(r.get("thread"), dict)
                and "state_day" not in r["thread"]]
        if gone:
            out.append(finding(rule, (board or {}).get("site_code"), d, "state_day",
                               f"{len(gone)} board threads carry no `state_day`", bundle.files(f"board.{d}")))
    return out


def _state_reads(bundle: Bundle) -> Iterator[tuple[str, str, str, dict, dict]]:
    """Each (board day, estate window, Finding, board thread, Portfolio thread) pair of reads of one Finding's thread
    that both carry a `state_day`."""
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board:
            continue
        for ref in _board_refs(board):
            b = ref.get("thread")
            if not isinstance(b, dict) or not b.get("state_day"):
                continue
            f = str(ref["finding_id"]).lower()
            for w in bundle.estate_windows():
                for r in _rows(bundle.get(f"portfolio.{w}")):
                    p = r.get("thread")
                    if str(r.get("finding_id") or "").lower() == f and isinstance(p, dict) and p.get("state_day"):
                        yield d, w, f, b, p


def coh13_lifecycle_agreement(bundle: Bundle) -> list[dict]:
    """CH-3 COH-13 (time-zone free): a board read and a Portfolio read of one Finding's thread agree. The two reads
    are ordered by their `state_day` into lo and hi. With no state at hi, both are equal; when hi's state took effect
    on or before lo's day, both read the same (state, effective day); otherwise lo's state took effect earlier (or
    lo has none). `state_effective_day` and `state_day` are ISO dates, so they compare as text."""
    if not _lifecycle(bundle):
        return []
    missing = _missing_state_day(bundle, "COH-13")
    if missing:
        return missing
    out, seen = [], set()
    for d, w, f, b, p in _state_reads(bundle):
        lo, hi = sorted((b, p), key=lambda t: t["state_day"])
        pair = (lambda t: (t.get("state"), t.get("state_effective_day")))
        eff_hi, eff_lo = hi.get("state_effective_day"), lo.get("state_effective_day")
        if eff_hi is None:
            bad = pair(lo) != pair(hi)
        elif eff_hi <= lo["state_day"]:
            bad = pair(lo) != pair(hi)
        else:
            bad = eff_lo is not None and eff_lo >= eff_hi
        if bad and (d, w, f) not in seen:  # a Finding listed on several rows of one board is one finding
            seen.add((d, w, f))
            out.append(finding("COH-13", (bundle.get(f"board.{d}") or {}).get("site_code"), d, f,
                               f"board thread {pair(b)} on {b['state_day']} disagrees with Portfolio ({w}) thread "
                               f"{pair(p)} on {p['state_day']}", [*bundle.files(f"board.{d}"),
                                                                 *bundle.files(f"portfolio.{w}")]))
    return out


#: CH3-R M3 (fix round 2): the start of the thread-level line of a verified thread (the board's THREAD_MONITORING and
#: THREAD_CLOSED; `test_chain_coherence` pins the copy against `site_outcomes/board.py`).
VERIFIED_LINE_PREFIX = "Fix verified"


def coh14_rows(bundle: Bundle) -> Iterator[tuple[str, dict, dict]]:
    """The (window, board, row) COH-14 judges: a row whose MOVES Findings all sit on a RESOLVED_MONITORING or CLOSED
    thread, and (fix round 2, CH3-R M3) a row with no MOVES Finding that carries a verified thread's thread-level
    line (its Finding left the overview day, so the line, not an issue ref, says the thread is verified)."""
    if not _lifecycle(bundle):
        return
    for d in bundle.day_windows():
        board = bundle.get(f"board.{d}")
        if not board:
            continue
        for row in board.get("rows") or []:
            moves = [i for i in row.get("issues") or [] if i.get("kind") == "FINDING" and i.get("role") == "MOVES"
                     and isinstance(i.get("ref"), dict)]
            if moves:
                if all(isinstance(i["ref"].get("thread"), dict)
                       and i["ref"]["thread"].get("state") in VERIFIED_THREAD_STATES for i in moves):
                    yield d, board, row
            elif _verified_line(row):
                yield d, board, row


def _verified_line(row: dict) -> bool:
    """CH-5a2 B4: a verified thread's line, from the structured `thread_lines` where present (kind MONITORING or
    CLOSED), else from the copy (an older board body)."""
    if isinstance(row.get("thread_lines"), list):
        return any(isinstance(t, dict) and t.get("kind") in ("MONITORING", "CLOSED") for t in row["thread_lines"])
    return any(part.startswith(VERIFIED_LINE_PREFIX) for part in str(row.get("subline") or "").split(" · "))


def coh14_verified_not_attention(bundle: Bundle) -> list[dict]:
    """CH-3 COH-14 (I-02): a board row outcome is not NEEDS_ATTENTION for an open primary Finding when every MOVES
    Finding on the row sits on a RESOLVED_MONITORING or CLOSED thread, or (CH3-R M3) when the row carries a verified
    thread's thread-level line and no MOVES Finding (`coh14_rows`)."""
    out = []
    for d, board, row in coh14_rows(bundle):
        for o in row.get("outcomes") or []:
            if o.get("state") == "NEEDS_ATTENTION" and o.get("reason") == "PRIMARY_FINDING_OPEN":
                out.append(finding("COH-14", board.get("site_code"), d, f"{row.get('category')}:{o.get('key')}",
                                   f"outcome {o.get('key')} needs attention for an open primary Finding, but "
                                   "the row's thread is verified (every MOVES Finding, or its thread-level line)",
                                   bundle.files(f"board.{d}")))
    return out


def coh15_action_segment(bundle: Bundle) -> list[dict]:
    """CH-3 COH-15: no Portfolio row shows, as its Action, one from an earlier segment of the Finding's own thread.
    The board leg (an earlier-segment Action goes to Earlier, never in hand) carries no segment on the wire and is
    covered by the board unit tests."""
    if not _lifecycle(bundle):
        return []
    missing = _missing_thread_keys(bundle, "COH-15", "action_segment_no")
    if missing:
        return missing
    out = []
    for w in bundle.estate_windows():
        for r in _rows(bundle.get(f"portfolio.{w}")):
            th, seg = r.get("thread"), r.get("action_segment_no")
            if (r.get("action_id") and isinstance(th, dict) and r.get("action_thread_id") == th.get("id")
                    and seg is not None and th.get("segment_no") is not None and seg < th["segment_no"]):
                out.append(finding("COH-15", r.get("site_code"), w, str(r["action_id"]),
                                   f"Action {r['action_id']} is from segment {seg}, but Finding {r.get('finding_id')} "
                                   f"is in segment {th['segment_no']} of the thread", bundle.files(f"portfolio.{w}")))
    return out


def coh16_opportunity_agreement(bundle: Bundle) -> list[dict]:
    """CH-4 COH-16: in each estate window the Portfolio `opportunity.items` and the Findings Opportunities lens
    `opportunities` hold the same set of (thread_id, study code, state, evidence): one item builder feeds both."""
    if not _opportunities_stamped(bundle):
        return []
    out = []
    for w in bundle.estate_windows():
        listed, portfolio = bundle.get(f"findings_opp.{w}"), bundle.get(f"portfolio.{w}")
        files = [*bundle.files(f"findings_opp.{w}"), *bundle.files(f"portfolio.{w}")]
        if listed is None or portfolio is None:
            continue  # a missing or failed body is COH-0's
        if "opportunities" not in listed or "items" not in (portfolio.get("opportunity") or {}):
            out.append(finding("COH-16", None, w, "opportunities", "a stamped bundle lacks the Findings "
                               "`opportunities` or the Portfolio `opportunity.items`", files))
            continue

        def key(i: dict) -> tuple:
            return (i.get("thread_id"), (i.get("study") or {}).get("code"), i.get("state"), i.get("evidence"))

        a = {key(i): i.get("site_code") for i in _opportunity_items(listed, "opportunities")}
        b = {key(i): i.get("site_code") for i in _opportunity_items(portfolio, "items")}
        for tid in sorted({k[0] for k in set(a) ^ set(b)}, key=str):  # one finding per thread
            fa, fb = sorted(k[1:] for k in a if k[0] == tid), sorted(k[1:] for k in b if k[0] == tid)
            site = next((s for k, s in [*a.items(), *b.items()] if k[0] == tid), None)
            out.append(finding("COH-16", site, w, str(tid), f"thread {tid}: Findings lists {fa}, Portfolio lists {fb}",
                               files))
    return out


CLAIM_KEYS = ("count.open_threads", "count.verified_results", "count.opportunities", "count.sites_disrupted")
FINDINGS_CLAIM_KEYS = ("count.opportunities",)  # the estate Findings carry only this one (`estate/index.py`)
CLAIM_FIELDS = ("value", "basis", "text")
GROW, PROTECT, ASSURE = "GROW_REVENUE", "PROTECT_ASSET", "ASSURE_PERFORMANCE"
COST = "OPTIMIZE_COST"
MINI_DOMAIN = "mini_grid"
NODE_PARTS = ("kpi", "earnings", "potential")
SITE_DAY_KEYS = ("requested", "expected", "complete", "partial", "low", "no_data", "not_expected", "pending")


def new_tally() -> dict[str, int]:
    return {"compared": 0, "skipped": 0}


def _vocabulary() -> Any:
    """The backend's money and day rules, imported and never re-derived (as `_coh7a_window`)."""
    backend = str(TOOLS.parent / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from assetops_backend.chain import vocabulary

    return vocabulary


def _rows_by_category(rows: Any) -> dict[str, dict]:
    return {r.get("category"): r for r in rows or ()}


def _site_name(site: dict) -> str:
    return site.get("site_name") or site.get("site_code")


def _coh17_money(w: str, chain: dict, summary: dict, files: list[str], tally: dict[str, int]) -> list[dict]:
    """CH6b3-R Q1 rows M1-M6: `money_total` is one object, the sum of the shown rounded Site claims."""
    voc = _vocabulary()
    out = []

    def check(row: str, ok: bool, detail: str) -> None:
        tally["compared"] += 1
        if not ok:
            out.append(finding("COH-17", None, w, row, detail, files))

    total = chain.get("money_total") or {}
    grow = ((chain.get("cards") or {}).get(GROW) or {})
    check("M1", total == summary.get("money_total") == grow.get("claim"),
          f"money_total: chain {total!r}, summary {summary.get('money_total')!r}, Grow card {grow.get('claim')!r}")
    by_code = {s.get("site_code"): s for s in summary.get("sites") or ()}
    amounts, currencies = [], set()
    for s in chain.get("sites") or ():
        code = s.get("code")
        here, there = s.get("earnings"), (by_code.get(code) or {}).get("earnings")
        check("M6", here == there, f"{code} earnings: chain {here!r}, summary {there!r}")
        for label in voc.INCOME_LABELS:
            claim = (here or {}).get(label)
            if claim is None:
                continue
            prefix = f"{_site_name(by_code.get(code) or {'site_code': code})}: "
            check("M4", any(str(x).startswith(prefix) for x in total.get("lines") or ()),
                  f"{code} {label}: no money_total line starts with {prefix!r}")
            value = claim.get("value") or {}
            if value.get("amount") is not None:
                amounts.append(Decimal(voc.money2(value["amount"])))
                currencies.add(value.get("currency"))
    shown = total.get("value")
    if len(currencies) > 1:
        check("M3", shown is None, f"money_total {shown!r} over more than one currency {sorted(map(str, currencies))}")
    elif not amounts:
        check("M2", shown is None, f"money_total {shown!r} with no Site amount")
    else:
        got = None if shown is None else shown.get("amount")
        check("M2", got is not None and voc.money2(got) == voc.money2(sum(amounts, Decimal(0))),
              f"money_total {got!r} is not the sum {voc.money2(sum(amounts, Decimal(0)))} of the shown Site claims")
    lines = total.get("lines") or ()
    income = (grow.get("parts") or {}).get("income")
    if lines:
        check("M5", income == " · ".join(lines), f"Grow card income {income!r} is not the lines {list(lines)!r}")
    return out


def coh17_optimize(w: str, summary: dict, files: list[str], tally: dict[str, int]) -> list[dict]:
    """CH5d1-R 2.4 row O1: the summary's Optimize card is the priced Sites' cost claims (`sites[].rows[OPTIMIZE_COST]
    .nodes.earnings` with a value): none -> "Not known yet" and no claim; one -> that claim, its text the value; two
    or more -> each priced Site's name prefixes one detail line and no claim (never summed). C3 ties the chain's card
    to this one and V3/V4 tie the nodes to the board. An absent card is a finding."""
    voc = _vocabulary()
    tally["compared"] += 1
    card = (summary.get("cards") or {}).get(COST)
    priced = []
    for s in summary.get("sites") or ():
        claim = ((_rows_by_category(s.get("rows")).get(COST) or {}).get("nodes") or {}).get("earnings")
        if claim is not None and claim.get("value") is not None:
            priced.append((s, claim))
    if not card:
        problem = "the summary has no Optimize card"
    elif not priced:
        ok = (card.get("value") or {}).get("text") == voc.NOT_KNOWN_TEXT and card.get("claim") is None
        problem = None if ok else f"no priced Site, card value {card.get('value')!r}, claim {card.get('claim')!r}"
    elif len(priced) == 1:
        (_, claim), = priced
        ok = card.get("claim") == claim and (card.get("value") or {}).get("text") == claim.get("text")
        problem = None if ok else (f"one priced Site claim {claim!r}, card value {card.get('value')!r}, "
                                   f"claim {card.get('claim')!r}")
    else:
        lines = str(card.get("detail") or "").split(" · ")
        missing = [_site_name(s) for s, _ in priced if not any(x.startswith(f"{_site_name(s)}: ") for x in lines)]
        problem = (f"{len(priced)} priced Sites, the detail lacks {missing}" if missing
                   else f"{len(priced)} priced Sites, card claim {card.get('claim')!r}" if card.get("claim") is not None
                   else None)
    return [] if problem is None else [finding("COH-17", None, w, "O1", problem, files)]


def _strings(node: Any) -> Iterator[str]:
    """Every string in a JSON value (keys excluded)."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for x in node.values():
            yield from _strings(x)
    elif isinstance(node, (list, tuple)):
        for x in node:
            yield from _strings(x)


def coh17_values(w: str, summary: dict, files: list[str], tally: dict[str, int]) -> list[dict]:
    """PV-1-R §5 row PV1: (i) the Assure card's `value_lines` are the Sites' Assure `nodes.verified_values` texts in
    Site order, each in the `assure.value_line` form; (ii) no string on the Assure card holds the exact sum of two
    same-currency entry amounts (never added); (iii) `value_note` is `assure.values_separate` iff there are lines. A
    summary without the keys (an older bundle) is skipped and counted."""
    voc = _vocabulary()
    card = (summary.get("cards") or {}).get(ASSURE)
    if not card or "value_lines" not in card or "value_note" not in card:
        tally["skipped"] += 1
        return []
    out = []

    def check(ok: bool, detail: str) -> None:
        tally["compared"] += 1
        if not ok:
            out.append(finding("COH-17", None, w, "PV1", detail, files))

    entries, want = [], []
    for s in summary.get("sites") or ():
        for e in ((_rows_by_category(s.get("rows")).get(ASSURE) or {}).get("nodes") or {}).get("verified_values") or ():
            entries.append(e)
            want.append(voc.card_text("assure.value_line", site=_site_name(s), text=e.get("text")))
    lines = list(card.get("value_lines") or ())
    check(lines == want, f"Assure card value_lines {lines!r}, rebuilt from the Sites' nodes {want!r}")
    strings = list(_strings(card))
    amts = [x for e in entries for x in _amounts(e.get("currency"), e.get("amount"))]
    sums = nonzero_pair_sums((a, b) for i, a in enumerate(amts) for b in amts[i + 1:])
    held = sorted({x for x in sums if any(x in t for t in strings)})
    check(not held, f"the Assure card holds the sum of two same-currency amounts: {held!r}")
    separate = voc.card_text("assure.values_separate")
    note = card.get("value_note")
    check((note == separate) == bool(lines), f"Assure value_note {note!r} with {len(lines)} value lines")
    return out


def _amounts(currency: Any, *values: Any) -> list[tuple[Any, Decimal]]:
    return [(currency, Decimal(str(x))) for x in values if x is not None]


def nonzero_pair_sums(pairs: Iterable[tuple[tuple[Any, Decimal], tuple[Any, Decimal]]]) -> set[str]:
    """R3u: the two-place sums of same-currency pairs, neither addend zero (a sum with 0 shows no adding)."""
    return {f"{a[1] + b[1]:.2f}" for a, b in pairs if a[0] is not None and a[0] == b[0] and a[1] != 0 and b[1] != 0}


def coh17_fuel(w: str, summary: dict, files: list[str], tally: dict[str, int]) -> list[dict]:
    """DIESEL-1-R3j §9j.12 row UF1: (i) the Protect card's `fuel_lines` are the Sites' Protect `nodes.unexplained_fuel`
    texts in Site order, each in the `protect.fuel_line` form; (ii) for every same-currency pair drawn from the fuel
    amounts, the Optimize claim amounts and the Assure `verified_values` amounts, with at least one fuel amount, the
    two-place sum appears in no string of any Portfolio card (never added); (iii) `fuel_note` is
    `protect.fuel_separate` iff there are lines. A summary without the keys (an older bundle) is skipped and counted."""
    voc = _vocabulary()
    cards = summary.get("cards") or {}
    card = cards.get(PROTECT)
    if not card or "fuel_lines" not in card or "fuel_note" not in card:
        tally["skipped"] += 1
        return []
    out = []

    def check(ok: bool, detail: str) -> None:
        tally["compared"] += 1
        if not ok:
            out.append(finding("COH-17", None, w, "UF1", detail, files))

    want, fuel, other = [], [], []
    for s in summary.get("sites") or ():
        rows = _rows_by_category(s.get("rows"))
        for e in ((rows.get(PROTECT) or {}).get("nodes") or {}).get("unexplained_fuel") or ():
            want.append(voc.card_text("protect.fuel_line", site=_site_name(s), text=e.get("text")))
            fuel += _amounts(e.get("currency"), e.get("amount_low"), e.get("amount_high"))
        claim = ((rows.get(COST) or {}).get("nodes") or {}).get("earnings") or {}
        value = claim.get("value") or {}
        other += _amounts(value.get("currency"), value.get("low"), value.get("high"), value.get("amount"))
        for e in ((rows.get(ASSURE) or {}).get("nodes") or {}).get("verified_values") or ():
            other += _amounts(e.get("currency"), e.get("amount"))
    lines = list(card.get("fuel_lines") or ())
    check(lines == want, f"Protect card fuel_lines {lines!r}, rebuilt from the Sites' nodes {want!r}")
    pairs = [(a, b) for i, a in enumerate(fuel) for b in fuel[i + 1:]] + [(a, b) for a in fuel for b in other]
    sums = nonzero_pair_sums(pairs)
    strings = list(_strings(cards))
    held = sorted(x for x in sums if any(x in t for t in strings))
    check(not held, f"a Portfolio card holds the sum of an unexplained-fuel amount and another amount: {held!r}")
    separate = voc.card_text("protect.fuel_separate")
    note = card.get("fuel_note")
    check((note == separate) == bool(lines), f"Protect fuel_note {note!r} with {len(lines)} fuel lines")
    return out


def _coh17_a1(w: str, code: str | None, assure: dict, files: list[str], tally: dict[str, int]) -> list[dict]:
    """MB-1-R Q5 row A1 (a mini board, internal): the Assure headline's count equals the Assure "Verified results"
    entries that read as verified (" not yet verified" entries excluded)."""
    from assetops_backend.site_outcomes.mini import NO_VERIFIED

    tally["compared"] += 1
    headline = assure.get("headline")
    m = re.fullmatch(r"(\d+) verified results?", str(headline or ""))
    if headline != NO_VERIFIED and m is None:
        return [finding("COH-17", code, w, "A1", f"unreadable Assure headline {headline!r}", files)]
    shown = 0 if headline == NO_VERIFIED else int(m.group(1))
    listed = sum(1 for c in assure.get("contributors") or () if c.get("key") == "verified_results"
                 and re.fullmatch(r"\S+ verified\b.*", str(c.get("text") or ""))
                 and " not yet verified" not in str(c.get("text") or "")
                 and c.get("text") != NO_VERIFIED)  # the empty entry ("No verified result yet") matches the pattern
    if shown == listed:
        return []
    return [finding("COH-17", code, w, "A1", f"Assure headline {headline!r}, {listed} verified entries", files)]


def _coh17_full(bundle: Bundle, w: str, chain: dict, counts: dict, tally: dict[str, int]) -> list[dict]:
    """CH6b3-R Q1 rows C2, C3, M1-M6, V1-V4, L1, Q2 rows W1, W2, CH5d1-R row O1 and PV-1-R row PV1 for one estate
    window (Site sets equal)."""
    out = []
    chain_files = bundle.files(f"chain_estate.{w}")
    summary = bundle.get(f"summary.{w}")
    if summary is None:
        if f"summary.{w}" not in bundle.bodies:
            out.append(finding("COH-17", None, w, "summary", "a stamped bundle lacks the summary body", chain_files))
        tally["skipped"] += 1
        return out  # a failed body is COH-0's
    files = [*chain_files, *bundle.files(f"summary.{w}")]
    sites = {s.get("site_code"): s for s in summary.get("sites") or ()}
    if sorted(sites) != sorted(s.get("code") for s in chain.get("sites") or ()):
        tally["skipped"] += 1
        return out  # COH-17 compares equal Site sets only

    def check(row: str, ok: bool, detail: str, where: list[str] | None = None, site: str | None = None) -> None:
        tally["compared"] += 1
        if not ok:
            out.append(finding("COH-17", site, w, row, detail, where or files))

    cards = chain.get("cards") or {}
    for card, key in ((PROTECT, "count.sites_disrupted"), (ASSURE, "count.verified_results")):
        a, b = (cards.get(card) or {}).get("claim") or {}, counts.get(key) or {}
        diff = [f"{f}: card {a.get(f)!r}, counts {b.get(f)!r}" for f in CLAIM_FIELDS if a.get(f) != b.get(f)]
        # CH6b3-R3 (reviewer L3): an absent card claim or count key is a finding, never `{} == {}`.
        if not a or not b:
            diff.append(f"absent: card claim {'present' if a else 'missing'}, counts {'present' if b else 'missing'}")
        check("C2", not diff, f"{card} card against {key}: " + "; ".join(diff))
    check("C3", cards == summary.get("cards"), "chain `cards` differ from summary `cards`")
    out += coh17_optimize(w, summary, files, tally)
    out += coh17_values(w, summary, files, tally)   # PV-1-R §5 row PV1
    out += coh17_fuel(w, summary, files, tally)     # DIESEL-1-R3j §9j.12 row UF1
    # CH6b3-R3 L2: the summary's legacy verified count is the claim's value (both known).
    shown, claimed = summary.get("verified_result_count"), (counts.get("count.verified_results") or {}).get("value")
    if shown is not None and claimed is not None:
        check("L2", shown == claimed, f"summary verified_result_count {shown!r}, count.verified_results {claimed!r}")
    out += _coh17_money(w, chain, summary, files, tally)

    for s in chain.get("sites") or ():
        code = s.get("code")
        site = sites[code]
        rows = _rows_by_category(site.get("rows"))
        for cat, r in (s.get("rows") or {}).items():
            here = rows.get(cat) or {}
            a, b = (r.get("state"), r.get("state_label"), r.get("lead")), (
                here.get("state"), here.get("state_label"), here.get("lead_outcome"))
            check("V1", a == b, f"{cat}: chain {a!r}, summary {b!r}", site=code)
            check("V3", r.get("nodes") == here.get("nodes"), f"{cat}: chain nodes differ from summary nodes", site=code)
        board_name = f"board_summary.{w}.{code}"
        board = bundle.get(board_name)
        if board is None:
            tally["skipped"] += 1
            continue
        board_rows = _rows_by_category(board.get("rows"))
        for cat, here in rows.items():
            there = board_rows.get(cat) or {}
            fields = ("state", "state_label", "lead_outcome", "headline")
            a, b = tuple(here.get(f) for f in fields), tuple(there.get(f) for f in fields)
            where = [*bundle.files(f"summary.{w}"), *bundle.files(board_name)]
            check("V2", a == b, f"{cat}: summary {a!r}, board {b!r}", where, code)
            if w == "S" and site.get("domain") == MINI_DOMAIN:  # one day on both; other windows differ by design
                check("V4", here.get("nodes") == there.get("nodes"), f"{cat}: summary nodes differ from board nodes",
                      where, code)
        if site.get("domain") == MINI_DOMAIN:  # MB-1-R Q5 A1: board-internal, one board on one day
            if ASSURE in board_rows:
                out += _coh17_a1(w, code, board_rows[ASSURE], bundle.files(board_name), tally)
            else:
                tally["skipped"] += 1  # a stored board body with no Assure row (older fixtures): not judged

    portfolio = bundle.get(f"portfolio.{w}")
    if portfolio is None:
        tally["skipped"] += 1
    else:
        where = [*chain_files, *bundle.files(f"portfolio.{w}")]
        s, p = portfolio.get("summary") or {}, portfolio.get("progress") or {}
        want = (counts.get("count.verified_results") or {}).get("value")
        got = (s.get("verified_resolution_count"), p.get("verified_resolution_count"))
        check("L1", got == (want, want), f"verified_resolution_count (summary, progress) {got!r}, claim {want!r}", where)
        threads = [x.get("threads") for x in chain.get("sites") or ()]
        priority = None if any(t is None for t in threads) else sum(1 for t in threads if t["open"] + t["in_hand"] > 0)
        check("L1", s.get("priority_site_count") == priority,
              f"priority_site_count {s.get('priority_site_count')!r}, Sites with open threads {priority!r}", where)
        # CH6b3-R3 L3: the Findings table's "Verified" rows are the claim's threads (one row per Finding, one
        # thread counted once); only on a complete (unpaged) table and a known claim. MB-1-R Q5: plus each Site's
        # verified opportunity-origin domain Actions (`threads.verified_actions`; absent = 0, older bundles).
        if portfolio.get("next_cursor") is None and want is not None:
            verified = {str((r.get("thread") or {}).get("id")) for r in _rows(portfolio)
                        if r.get("workflow_label") == "Verified" and (r.get("thread") or {}).get("id")}
            mill = sum(int((x.get("threads") or {}).get("verified_actions") or 0) for x in chain.get("sites") or ())
            check("L3", len(verified) + mill == want,
                  f"{len(verified)} distinct Verified threads in the table + {mill} verified opportunity Actions, "
                  f"claim {want!r}", where)
        # CH6b3-R3 N1: "days checked" means graded COMPLETE; no card note speaks of the coverage count with it.
        for card, note in sorted((s.get("card_notes") or {}).items()):
            check("N1", "days checked" not in str(note or ""), f"{card} note {note!r} holds \"days checked\"", where)

    for cat in _categories():
        name = f"why_estate.{w}.{cat}"
        why = bundle.get(name)
        if why is None:
            if name not in bundle.bodies:
                out.append(finding("COH-17", None, w, name, "a stamped bundle lacks this Why? body", files))
            tally["skipped"] += 1
            continue
        where = [*bundle.files(f"summary.{w}"), *bundle.files(name)]
        for t in why.get("sites") or ():
            code = t.get("code")
            row = _rows_by_category((sites.get(code) or {}).get("rows")).get(cat) or {}
            say, want_say = (t.get("text") or {}).get("say"), row.get("headline") or row.get("state_label")
            check("W1", say == want_say, f"{cat}: Why? says {say!r}, the summary row {want_say!r}", where, code)
        # CH6b3-R3 W3: the Why? days are the card's own days line (Optimize has none: Protect's).
        want_days = (cards.get(cat) or {}).get("days_line") or (cards.get(PROTECT) or {}).get("days_line")
        used = (why.get("text") or {}).get("days_used")
        if want_days is not None:
            check("W3", used == want_days, f"{cat}: Why? days {used!r}, card days {want_days!r}", where)
        value = (counts.get("count.sites_disrupted") or {}).get("value")
        if cat == PROTECT and value is not None:
            lines = (why.get("text") or {}).get("comes_from") or ()
            named = [c for c, x in sites.items() if any(str(n).startswith(f"{_site_name(x)}: ") for n in lines)]
            check("W2", len(named) == value, f"Why? names {sorted(named)}, count.sites_disrupted is {value!r}", where)
    return out


def _categories() -> tuple[str, ...]:
    backend = str(TOOLS.parent / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from assetops_backend.outcomes.catalogue import CATEGORIES

    return tuple(CATEGORIES)


def info_coh17_period_nodes(bundle: Bundle) -> list[dict]:
    """CH6b3-R Q1: per non-mini Site, window, category and part, the board and summary node `text` and `days` wherever
    they differ. The two frames differ by design (the board reads the contained event's local days, the summary reads
    `window_days`), so this is a list, not a rule. `unexplained` marks equal `days` with a different value or text,
    which the frame does not explain (the builder stops and reports it). BL-33 owns a strict comparison."""
    if not bundle.manifest.get("full_claims"):
        return []
    out = []
    for w in bundle.estate_windows():
        for site in (bundle.get(f"summary.{w}") or {}).get("sites") or ():
            code = site.get("site_code")
            board = bundle.get(f"board_summary.{w}.{code}")
            if site.get("domain") == MINI_DOMAIN or board is None:
                continue
            there = _rows_by_category(board.get("rows"))
            for r in site.get("rows") or ():
                cat = r.get("category")
                a_nodes, b_nodes = (there.get(cat) or {}).get("nodes") or {}, r.get("nodes") or {}
                for part in NODE_PARTS:
                    a, b = a_nodes.get(part) or {}, b_nodes.get(part) or {}
                    text_or_days = a.get("text") != b.get("text") or a.get("days") != b.get("days")
                    same_days = a.get("days") == b.get("days")
                    if text_or_days or (same_days and a.get("value") != b.get("value")):
                        out.append({"site_code": code, "window": w, "category": cat, "part": part,
                                    "board_text": a.get("text"), "summary_text": b.get("text"),
                                    "board_days": a.get("days"), "summary_days": b.get("days"),
                                    "board_value": a.get("value"), "summary_value": b.get("value"),
                                    "unexplained": same_days})
    return out


def coh17_count_claims(bundle: Bundle, tally: dict[str, int] | None = None) -> list[dict]:
    """CH-5a2b COH-17 (§B13 R3, §B14 Q7): for each estate window, the `/estate/chain` `counts`, the Portfolio
    `summary.claims` (all keys) and the estate Findings (lens=all) `summary.claims` (`count.opportunities`)
    with equal key, Site set and window agree on value, basis and text. They come from one computation, so a
    difference means a route passed different scope, window or cutoff. A bundle not stamped `claims` is not judged.
    CH6b3-R Q1, Q2: a bundle also stamped `full_claims` is judged on the count, money, verdict, legacy and Why? rows
    (`_coh17_full`). `tally` receives `{compared, skipped}` (pipeline L5); a stamped bundle comparing nothing fails."""
    if not bundle.manifest.get("claims"):
        return []
    tally = new_tally() if tally is None else tally
    out = []
    full = bool(bundle.manifest.get("full_claims"))
    for w in [*bundle.estate_windows(), *bundle.day_windows()]:
        prefix = "" if w in ESTATE_WINDOWS else "day_"
        chain_name = f"{prefix}chain_estate.{w}"
        chain = bundle.get(chain_name)
        if chain is None:
            if chain_name not in bundle.bodies:
                out.append(finding("COH-17", None, w, "chain", "a stamped bundle lacks the `/estate/chain` body", []))
            continue  # a failed body is COH-0's
        bounds = bundle.windows[w].get("estate") or bundle.windows[w]
        cw = chain.get("window") or {}
        if not (cw.get("from") and cw.get("to")) or (at(cw["from"]), at(cw["to"])) != (at(bounds["from"]), at(bounds["to"])):
            out.append(finding("COH-17", None, w, "window", "the `/estate/chain` window is not the requested one",
                               bundle.files(chain_name)))
            continue
        sites = sorted(s.get("code") for s in chain.get("sites") or ())
        counts = chain.get("counts") or {}
        for name, keys in ((f"portfolio.{w}", CLAIM_KEYS), (f"{prefix}findings_all.{w}", FINDINGS_CLAIM_KEYS)):
            body = bundle.get(name)
            if body is None:
                tally["skipped"] += 1
                continue  # not read in this window (day windows have no Portfolio), or COH-0's
            files = [*bundle.files(chain_name), *bundle.files(name)]
            claims = (body.get("summary") or {}).get("claims")
            if not isinstance(claims, dict):
                out.append(finding("COH-17", None, w, name.split(".")[0], "a stamped bundle lacks `summary.claims`",
                                   files))
                continue
            disclosed = (body.get("scope_disclosure") or {}).get("sites")
            if disclosed is not None and sorted(s.get("site_code") for s in disclosed) != sites:
                tally["skipped"] += 1
                continue  # COH-17 compares equal Site sets only
            for key in keys:
                tally["compared"] += 1
                a, b = counts.get(key) or {}, claims.get(key) or {}
                diff = [f"{f}: chain {a.get(f)!r}, {name.split('.')[0]} {b.get(f)!r}" for f in CLAIM_FIELDS
                        if a.get(f) != b.get(f)]
                if diff:
                    out.append(finding("COH-17", None, w, key, "; ".join(diff), files))
        if full and w in ESTATE_WINDOWS:
            out += _coh17_full(bundle, w, chain, counts, tally)
    if tally["compared"] == 0:  # pipeline L5: a vacuous pass must not look like a clean one
        out.append(finding("COH-17", None, None, "vacuous", "a stamped bundle compared no claim at all", []))
    return out


def _site_day_grades(bundle: Bundle, w: str, code: str, dates: list[str]) -> tuple[dict[str, str], list[str]] | None:
    """`(day -> grade, the dates with no entry)` of one Site's collected chain bodies; None when a body failed (COH-0's)
    or was not read. A PERIOD Site has one `chain_span.{w}.{code}`; a mini Site one `chain_day.{code}.{d}` per date."""
    span = f"chain_span.{w}.{code}"
    names = [span] if span in bundle.bodies else [f"chain_day.{code}.{d}" for d in dates]
    grades: dict[str, str] = {}
    for name in names:
        body = bundle.get(name)
        if body is None:
            return None
        grades.update({e.get("day"): e.get("grade") for e in body.get("days") or ()})
    return {d: grades[d] for d in dates if d in grades}, [d for d in dates if d not in grades]


def _window_dates(bounds: dict) -> list[str]:
    backend = str(TOOLS.parent / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from assetops_backend.chain.read import window_days

    return [d.isoformat() for d in window_days(at(bounds["from"]), at(bounds["to"]), None)]


def _coh18_gaps(w: str, code: str, grades: dict[str, str], listed: set[tuple[str, str]],
                claims: list[tuple[str, Any]], files: list[str], tally: dict[str, int]) -> list[dict]:
    """CH6b3-R Q4a R3 and the Site-level half of R4; `claims` = (subject, basis) of the Site."""
    out = []
    for d, g in grades.items():
        tally["compared"] += 1
        if g not in ("COMPLETE", "NO_DATA", "NOT_EXPECTED") and (code, d) not in listed:
            out.append(finding("COH-18", code, w, f"built:{d}", f"built day {d} grades {g}, not a declared gap", files))
    excused = any((code, d) in listed or g == "NO_DATA" for d, g in grades.items())
    for subject, basis in claims:
        tally["compared"] += 1
        if basis == "CHECKED_DAYS" and not excused:
            out.append(finding("COH-18", code, w, subject, "CHECKED_DAYS with no declared gap or unbuilt day in the "
                               "window", files))
    return out


def coh18_day_grades(bundle: Bundle, gap_days: list[dict] | None = None,
                     tally: dict[str, int] | None = None) -> list[dict]:
    """CH-5a `:681`, CH6b3-R Q3, Q4a. For each estate window, the sum over `window_days` of each Site's per-day grades
    equals the chain's Site `days` (R1, an unbuilt day grades NO_DATA by the day rule), and the `counts[*].days` equal
    those summed (R2). With `gap_days` (`expected-mechanism.json`): every built day not listed is COMPLETE (R3), and a
    CHECKED_DAYS basis needs a listed gap or NO_DATA day (R4). A bundle not stamped `day_bodies` is not judged."""
    if not bundle.manifest.get("day_bodies"):
        return []
    voc = _vocabulary()
    tally = new_tally() if tally is None else tally
    listed = {(g["site_code"], g["day"]) for g in gap_days or ()}
    out = []
    for w in bundle.estate_windows():
        chain_name = f"chain_estate.{w}"
        chain = bundle.get(chain_name)
        if chain is None:
            tally["skipped"] += 1
            continue  # a failed or missing body is COH-0's and COH-17's
        dates = _window_dates(bundle.windows[w])
        chain_files = bundle.files(chain_name)
        tallies: list[dict[str, int]] = []
        any_excused = False
        for s in chain.get("sites") or ():
            code = s.get("code")
            read = _site_day_grades(bundle, w, code, dates)
            if read is None:
                tally["skipped"] += 1
                continue
            grades, missing = read
            for d in missing:
                out.append(finding("COH-18", code, w, f"missing:{d}", f"no day entry for {d} in the collected body",
                                   chain_files))
            count = {k: 0 for k in SITE_DAY_KEYS}
            for g in grades.values():
                count[g.lower()] += 1
            count["requested"] = len(dates)
            count["expected"] = len(dates) - count["not_expected"]
            tallies.append(count)
            days = s.get("days")
            tally["compared"] += 1
            if days is None:
                out.append(finding("COH-18", code, w, "days", "the chain's Site `days` is null", chain_files))
            else:
                diff = [f"{k}: chain {days.get(k)!r}, day grades {count[k]}" for k in SITE_DAY_KEYS
                        if days.get(k) != count[k]]
                if diff:
                    out.append(finding("COH-18", code, w, "days", "; ".join(diff), chain_files))
            if gap_days is not None:
                claims = [("count_basis", None if days is None else voc.count_basis(days))]
                claims += [(f"earnings.{k}", c.get("basis")) for k, c in (s.get("earnings") or {}).items()]
                out += _coh18_gaps(w, code, grades, listed, claims, chain_files, tally)
                any_excused = any_excused or any((code, d) in listed or g == "NO_DATA" for d, g in grades.items())
        summed = {k: sum(c[k] for c in tallies) for k in voc.CLAIM_DAY_KEYS}
        for key, claim in (chain.get("counts") or {}).items():
            tally["compared"] += 1
            have = claim.get("days")
            if len(tallies) == len(chain.get("sites") or ()) and have != summed:
                out.append(finding("COH-18", None, w, key, f"claim days {have!r}, the Sites' days summed {summed!r}",
                                   chain_files))
        if gap_days is not None:
            estate = [(k, c.get("basis")) for k, c in (chain.get("counts") or {}).items()]
            estate.append(("money_total", (chain.get("money_total") or {}).get("basis")))
            for subject, basis in estate:
                tally["compared"] += 1
                if basis == "CHECKED_DAYS" and not any_excused:
                    out.append(finding("COH-18", None, w, subject, "CHECKED_DAYS with no declared gap or unbuilt day "
                                       "at any Site in the window", chain_files))
    if tally["compared"] == 0:
        out.append(finding("COH-18", None, None, "vacuous", "a stamped bundle compared no day grade at all", []))
    return out


def rule_tallies(bundle: Bundle, gap_days: list[dict] | None = None) -> dict[str, dict[str, int]]:
    """Pipeline L5: `{compared, skipped}` of COH-17 and COH-18, so a vacuous pass does not read like a clean one."""
    t17, t18 = new_tally(), new_tally()
    coh17_count_claims(bundle, t17)
    coh18_day_grades(bundle, gap_days, t18)
    return {"COH-17": t17, "COH-18": t18}


def lifecycle_pairs(bundle: Bundle) -> int:
    """The number of board/Portfolio read pairs COH-13 compared (for the L3 report)."""
    return sum(1 for _ in _state_reads(bundle))


RULES: list[tuple[str, Callable[[Bundle], list[dict]]]] = [
    ("COH-0", coh0_missing_data), ("COH-1", coh1_links), ("COH-2", coh2_action_on_portfolio), ("COH-3", coh3_action_on_board),
    ("COH-4", coh4_findings_contain), ("COH-5", coh5_lens), ("COH-6", coh6_opportunity),
    ("COH-7", coh7_summary_basis), ("COH-8", coh8_verified), ("COH-9", coh9_day_counts),
    ("COH-10", coh10_thread_identity), ("COH-11", coh11_actions_linked),
    ("COH-13", coh13_lifecycle_agreement), ("COH-14", coh14_verified_not_attention),
    ("COH-15", coh15_action_segment), ("COH-16", coh16_opportunity_agreement), ("COH-17", coh17_count_claims),
    ("COH-18", coh18_day_grades)]
INFO: list[tuple[str, Callable[[Bundle], list[dict]]]] = [("COH-9b", info_coh9b), ("COH-12", info_coh12),
                                                          ("COH-17-period-nodes", info_coh17_period_nodes)]


# ---- check -----------------------------------------------------------------------------------------------------

def _key(f: dict) -> tuple:
    return (f["rule"], f.get("site_code"), f.get("window"), f.get("subject"))


def applicable(expect: list[dict] | None, variant: str | None) -> list[dict]:
    """MD0b-N1: an entry with `variants` applies only to a run of one of those variants; one without applies to all."""
    return [e for e in (expect or []) if "variants" not in e or variant in e["variants"]]


def check(bundle: Bundle, expect: list[dict] | None = None, threads: list[dict] | None = None,
          variant: str | None = None, gap_days: list[dict] | None = None) -> dict[str, Any]:
    """`variant` filters the expected entries by their optional `variants` list. `threads` (MD-0 R9, `check --threads`) replaces COH-10's expected threads; None keeps the bundle's own or
    THREADS_FILE. `gap_days` (CH6b3-R Q4a, `expected-mechanism.json`) turns on COH-18's R3 and R4."""
    expect = applicable(expect, variant)
    findings: list[dict] = []
    for _, rule in RULES:
        if rule is coh18_day_grades:
            findings += rule(bundle, gap_days)
            continue
        findings += rule(bundle, threads) if rule is coh10_thread_identity and threads is not None else rule(bundle)
    expected = {_key(e): e for e in (expect or []) if e.get("subject") != "*"}
    # MD0b-R: an entry with subject "*" covers up to `count` findings of its (rule, site, window) whose subject is a
    # server-generated id that changes on every template rebuild; a finding beyond the count is unexpected.
    wild = {_key(e)[:3]: e for e in (expect or []) if e.get("subject") == "*"}
    # M1: a wildcard also needs `detail_contains`, matched against the finding's detail, so a different kind of finding
    # (a missing progress row, a Portfolio row that lost VERIFIED) stays unexpected.
    used: dict[tuple, int] = {}
    unexpected = []
    found = set()
    for f in findings:
        found.add(_key(f))
        if _key(f) in expected:
            continue
        w = wild.get(_key(f)[:3])
        if (w is not None and w.get("detail_contains") and w["detail_contains"] in f["detail"]
                and used.get(_key(f)[:3], 0) < int(w.get("count", 1))):
            used[_key(f)[:3]] = used.get(_key(f)[:3], 0) + 1
            continue
        unexpected.append(f)
    found_wild = {k for k in used}
    resolved = [e for k, e in expected.items() if k not in found]
    resolved += [e for k, e in wild.items() if k not in found_wild]
    summary: dict[str, int] = {}
    for f in findings:
        summary[f["rule"]] = summary.get(f["rule"], 0) + 1
    manifest = {k: v for k, v in bundle.manifest.items() if k != "requests"}
    manifest["request_count"] = len(bundle.manifest["requests"])
    return {"schema": REPORT_SCHEMA, "bundle": manifest, "findings": findings, "expected_unmatched": unexpected,
            "resolved": resolved, "info": {name: fn(bundle) for name, fn in INFO}, "summary": summary,
            "tallies": rule_tallies(bundle, gap_days), "pass": not unexpected}


def load_expect(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(data["expectations"] if isinstance(data, dict) else data)


def load_gap_days(path: Path) -> list[dict] | None:
    """CH6b3-R Q4a: the expectation file's `gap_days`; None when it has none (polish), so only COH-18's R1, R2 run."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data.get("gap_days") if isinstance(data, dict) else None


def print_report(report: dict[str, Any], expect: list[dict] | None) -> None:
    unmatched = [id(f) for f in report["expected_unmatched"]]
    for rule, _ in RULES:  # COH-7 covers COH-7a/COH-7b, COH-9 covers COH-9a
        hits = [f for f in report["findings"] if f["rule"] == rule
                or (f["rule"].startswith(rule) and f["rule"][len(rule):].isalpha())]
        new = sum(1 for f in hits if id(f) in unmatched)  # L5: agrees with the check's own result
        print(f"{rule}: {len(hits)} finding(s), {len(hits) - new} expected, {new} new")
    for f in report["expected_unmatched"]:
        print(f"  NEW {f['rule']} {f['site_code']} {f['window']} {f['subject']}: {f['detail']}")
    for e in report["resolved"]:
        tag = "RESOLVED-WILDCARD (DELETE THIS ENTRY)" if e.get("subject") == "*" else "RESOLVED"
        print(f"  {tag} {e['rule']} {e.get('site_code')} {e.get('window')} {e.get('subject')}")
    for name, rows in report["info"].items():
        unexplained = sum(1 for r in rows if r.get("unexplained"))
        print(f"{name} (info): {len(rows)} item(s)" + (f", {unexplained} UNEXPLAINED" if unexplained else ""))
    for name, t in report["tallies"].items():
        print(f"{name}: compared {t['compared']}, skipped {t['skipped']}")
    unexpected = len(report["expected_unmatched"])
    print(f"self-check: {len(report['findings']) - unexpected} pass, {unexpected} fail "
          f"({len(report['resolved'])} resolved)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python tools/checks/chain_coherence.py")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--work", required=True, type=Path)
    src = c.add_mutually_exclusive_group(required=True)
    src.add_argument("--database-url")
    src.add_argument("--base-url")
    c.add_argument("--out", required=True, type=Path)
    c.add_argument("--known-at")
    k = sub.add_parser("check")
    k.add_argument("--bundle", required=True, type=Path)
    k.add_argument("--expect", type=Path)
    k.add_argument("--report", type=Path)
    k.add_argument("--variant", help="mechanism variant of this run (states, close); gates expected entries' `variants`")
    k.add_argument("--threads", type=Path, help=f"COH-10 expected threads (default {THREADS_FILE.name})")
    args = parser.parse_args(argv)
    if args.command == "collect":
        read = lambda name: json.loads((args.work / name).read_text(encoding="utf-8"))  # noqa: E731
        if args.database_url:
            # MD-0 R8: collect reads only story.json and days.json (as the HTTP branch), so a work folder with no
            # demo work documents (the mechanism DB's) collects in process too.
            sys.path.insert(0, str(TOOLS))
            from demo_combined_finish import app_client

            getter, source = InProcess(app_client(args.database_url, args.work)), "in-process"
        else:
            getter, source = Http(args.base_url), "http"
        m = collect(getter, read("story.json"), read("days.json")["days"], args.out, source, args.known_at)
        statuses: dict[int, int] = {}
        for r in m["requests"]:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        print(f"collected {len(m['requests'])} requests into {args.out}: statuses {statuses}")
        return 0
    expect = load_expect(args.expect) if args.expect else None
    report = check(Bundle(args.bundle), expect, load_threads(args.threads) if args.threads else None, args.variant,
                   load_gap_days(args.expect) if args.expect else None)
    expect = applicable(expect, args.variant)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print_report(report, expect)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
