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
from pathlib import Path
from typing import Any, Callable, Iterator
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
ROUTES_FILE = HERE / "fixtures" / "chain_coherence" / "screen_routes.json"
#: CH-2 COH-10: the expected Finding threads per Site (full ids from the CH-2 L4 dry run).
THREADS_FILE = HERE / "fixtures" / "chain_coherence" / "expected-threads.json"
BUNDLE_SCHEMA = "chain-coherence-bundle/1"
REPORT_SCHEMA = "chain-coherence-report/1"
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001"}
#: CH-5a1 (R6, CH5a1-R Q8; closes MD0-R R10): the Sites whose board day is their Site-local day. EV keeps its
#: `[start, end)` (`Etc/UTC`, `[d 08:00Z, d 16:00Z)`).
LOCAL_DAY_TZ = {"kobo": "Africa/Addis_Ababa", "cold": "Africa/Addis_Ababa"}
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
    """Board windows (CH-5a1 R6): a Kobo or Cold built day is its Site-local day (`LOCAL_DAY_TZ`; Kobo's board reads
    `?date=`, Cold's the local-day `from`/`to`); an EV day is its `[start, end)`, as `demo_combined_finish.Ctx.window`
    reads it. `estate` is the enclosing UTC-midnight window the estate routes accept (they refuse a non-midnight
    bound)."""
    out = []
    for d in days:
        if d.get("assess") != "build" or not d.get("start") or d.get("site") not in SITE_CODE:
            continue
        start, end = at(d["start"]), at(d["end"])
        zone = LOCAL_DAY_TZ.get(d["site"])
        if zone:
            local = _midnight(start.astimezone(ZoneInfo(zone)))
            lo, hi = local.astimezone(timezone.utc), (local + timedelta(days=1)).astimezone(timezone.utc)
        else:
            lo, hi = start, end
        e_lo, e_hi = _midnight(lo), _midnight(hi - timedelta(microseconds=1)) + timedelta(days=1)
        out.append({"id": f"day:{d['site']}:{d['kind']}:{d['day']}", "site_code": SITE_CODE[d["site"]],
                    "from": iso(lo), "to": iso(hi), "date": local.date().isoformat() if d["site"] == "kobo" else None,
                    "estate": (iso(e_lo), iso(e_hi))})
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
        if prefix:
            return
        self.fetch(f"portfolio.{window}", "/api/estate/portfolio", {**w, "lens": "all"}, window, paged=True)
        self.fetch(f"findings_opp.{window}", "/api/estate/findings",
                   {**w, "lens": "opportunities", "state": "all"}, window, paged=True)
        self.fetch(f"actions.{window}", "/api/estate/actions", w, window, paged=True)
        for code in DOMAIN_SITES:
            self.fetch(f"action_index.{code}.{window}", f"/api/sites/{code}/domain-work/action-index", w, window,
                       paged=True)
        summary = self.fetch(f"summary.{window}", "/api/estate/outcome-summary", w, window)
        for site in (summary or {}).get("sites", []):
            sw = site.get("window") or {}
            if site.get("site_code") and sw.get("from") and sw.get("to"):
                self.board(f"board_summary.{window}.{site['site_code']}", site["site_code"], window,
                           sw["from"], sw["to"], None)


def collect(getter: Getter, story: dict, days: list[dict], out: Path, source: str,
            known_at: str | None = None) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    c = Collector(getter, out, known_at)
    windows = estate_windows(story)
    for wid, (lo, hi) in windows.items():
        c.estate(wid, lo, hi)
    days_out = day_windows(days)
    for d in days_out:
        c.board(f"board.{d['id']}", d["site_code"], d["id"], d["from"], d["to"], d["date"])
        c.estate(d["id"], *d["estate"], prefix="day_")
    manifest = {"schema": BUNDLE_SCHEMA, "S": story["S"], "code": story.get("code"),
                "collected_at": iso(datetime.now(timezone.utc)), "source": source,
                "freshness": "not ticked" if source == "in-process" else "as served",
                "known_at": known_at, "threads": True,  # CH-2: this tool revision expects the `thread` fields
                "lifecycle": True,  # CH-3: and the thread `state_day` and the Portfolio `action_segment_no`
                "opportunities": True,  # CH-4: and the Findings `opportunities` and the Portfolio `opportunity.items`
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


def _board_findings(board: dict) -> Iterator[tuple[str, str]]:
    for row in board.get("rows") or []:
        for issue in row.get("issues") or []:
            ref = issue.get("ref")
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


def coh3_action_on_board(bundle: Bundle) -> list[dict]:
    out = []
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
            if (a["origin"] and str(a["origin"]) in on_board and a["created"] and at(a["created"]) <= to
                    and not any(a["action_id"] in h for h in hrefs)):
                out.append(finding("COH-3", board.get("site_code"), d, a["action_id"],
                                   f"Finding {a['origin']} is on the board and Action {a['action_id']} answering it "
                                   "existed by the window end, but no board link names the Action",
                                   [*bundle.files(f"board.{d}"), *bundle.files(a["file"])]))
    return out


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
        for category, f in _board_findings(board):
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


def coh7_summary_basis(bundle: Bundle) -> list[dict]:
    out = []
    for w in bundle.estate_windows():
        summary = bundle.get(f"summary.{w}")
        if not summary:
            continue
        files = bundle.files(f"summary.{w}")
        sites = summary.get("sites") or []
        bases = sorted({str(s.get("window_basis")) for s in sites})
        if len(bases) > 1:
            out.append(finding("COH-7a", None, w, "window_basis",
                               f"summary Sites use more than one window basis: {bases}", files))
        requested = bundle.windows[w]
        for s in sites:
            sw = s.get("window") or {}
            if (sw.get("from"), sw.get("to")) != (requested["from"], requested["to"]):
                out.append(finding("COH-7a", s.get("site_code"), w, "window",
                                   f"summary Site window [{sw.get('from')}, {sw.get('to')}) is not the requested "
                                   f"[{requested['from']}, {requested['to']})", files))
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
            elif p.get("origin_revision_selected") is not True:
                problems.append(f"its progress row has origin_revision_selected {p.get('origin_revision_selected')}")
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
            elif any(part.startswith(VERIFIED_LINE_PREFIX) for part in str(row.get("subline") or "").split(" · ")):
                yield d, board, row


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


def lifecycle_pairs(bundle: Bundle) -> int:
    """The number of board/Portfolio read pairs COH-13 compared (for the L3 report)."""
    return sum(1 for _ in _state_reads(bundle))


RULES: list[tuple[str, Callable[[Bundle], list[dict]]]] = [
    ("COH-0", coh0_missing_data), ("COH-1", coh1_links), ("COH-2", coh2_action_on_portfolio), ("COH-3", coh3_action_on_board),
    ("COH-4", coh4_findings_contain), ("COH-5", coh5_lens), ("COH-6", coh6_opportunity),
    ("COH-7", coh7_summary_basis), ("COH-8", coh8_verified), ("COH-9", coh9_day_counts),
    ("COH-10", coh10_thread_identity), ("COH-11", coh11_actions_linked),
    ("COH-13", coh13_lifecycle_agreement), ("COH-14", coh14_verified_not_attention),
    ("COH-15", coh15_action_segment), ("COH-16", coh16_opportunity_agreement)]
INFO: list[tuple[str, Callable[[Bundle], list[dict]]]] = [("COH-9b", info_coh9b), ("COH-12", info_coh12)]


# ---- check -----------------------------------------------------------------------------------------------------

def _key(f: dict) -> tuple:
    return (f["rule"], f.get("site_code"), f.get("window"), f.get("subject"))


def check(bundle: Bundle, expect: list[dict] | None = None) -> dict[str, Any]:
    findings: list[dict] = []
    for _, rule in RULES:
        findings += rule(bundle)
    expected = {_key(e): e for e in (expect or [])}
    found = {_key(f) for f in findings}
    unexpected = [f for f in findings if _key(f) not in expected]
    resolved = [e for k, e in expected.items() if k not in found]
    summary: dict[str, int] = {}
    for f in findings:
        summary[f["rule"]] = summary.get(f["rule"], 0) + 1
    manifest = {k: v for k, v in bundle.manifest.items() if k != "requests"}
    manifest["request_count"] = len(bundle.manifest["requests"])
    return {"schema": REPORT_SCHEMA, "bundle": manifest, "findings": findings, "expected_unmatched": unexpected,
            "resolved": resolved, "info": {name: fn(bundle) for name, fn in INFO}, "summary": summary,
            "pass": not unexpected}


def load_expect(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(data["expectations"] if isinstance(data, dict) else data)


def print_report(report: dict[str, Any], expect: list[dict] | None) -> None:
    expected = {_key(e) for e in (expect or [])}
    for rule, _ in RULES:  # COH-7 covers COH-7a/COH-7b, COH-9 covers COH-9a
        hits = [f for f in report["findings"] if f["rule"] == rule
                or (f["rule"].startswith(rule) and f["rule"][len(rule):].isalpha())]
        new = sum(1 for f in hits if _key(f) not in expected)
        print(f"{rule}: {len(hits)} finding(s), {len(hits) - new} expected, {new} new")
    for f in report["expected_unmatched"]:
        print(f"  NEW {f['rule']} {f['site_code']} {f['window']} {f['subject']}: {f['detail']}")
    for e in report["resolved"]:
        print(f"  RESOLVED {e['rule']} {e.get('site_code')} {e.get('window')} {e.get('subject')}")
    for name, rows in report["info"].items():
        print(f"{name} (info): {len(rows)} item(s)")
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
    args = parser.parse_args(argv)
    if args.command == "collect":
        if args.database_url:
            sys.path.insert(0, str(TOOLS))
            from demo_combined_finish import app_client, load

            ctx = load(args.work, app_client(args.database_url, args.work))
            m = collect(InProcess(ctx.client), ctx.story, ctx.days, args.out, "in-process", args.known_at)
        else:
            read = lambda name: json.loads((args.work / name).read_text(encoding="utf-8"))  # noqa: E731
            m = collect(Http(args.base_url), read("story.json"), read("days.json")["days"], args.out, "http",
                        args.known_at)
        statuses: dict[int, int] = {}
        for r in m["requests"]:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        print(f"collected {len(m['requests'])} requests into {args.out}: statuses {statuses}")
        return 0
    expect = load_expect(args.expect) if args.expect else None
    report = check(Bundle(args.bundle), expect)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print_report(report, expect)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
