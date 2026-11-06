"""CH-5a2b (build sheet CH-5a §B13 R3 as amended by §B14 Q7/Q8): the estate count claims, ONE computation.

`/api/estate/chain` `counts` and `sites[].threads`, the Portfolio `summary.claims` and the estate Findings
`summary.claims` all call `estate_count_claims` (the two estate services through the injected `EstateClaims`), so
equal scope, window and cutoff give equal claims by construction; COH-17 checks the routes pass equal inputs.

- `days`: one `ChainRequest.day` per Site over `window_days(lo, hi, tz)`, `grade_counts_of` (review L2), summed by
  `sum_days`; any Site None (its read failed) -> None.
- Threads: `site_chain.threads_of` restricted to threads with a **Finding** occurrence whose episode meets `[lo, hi)`
  (no event-only, no opportunity-only thread), read on `window_day` at the per-Site cutoff (`site_cutoff`: mini ->
  the request's `k`; cold/EV -> the Site's evidence cutoff bounded by `k`), classified by `threads.classify`.
- `count.open_threads` = open + in hand, `count.verified_results` = verified, `count.opportunities` = the CH-4 item
  count (`opportunity_items`, the one read `/estate/chain` lists). A failed read is a null value (NOT_KNOWN).

Pure apart from the `ChainRequest` reads and the injected opportunity port.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence

from assetops_backend import read_scope
from assetops_backend.chain import site_chain
from assetops_backend.chain.measures import measures_for
from assetops_backend.chain.read import MINI_DOMAIN, SITE_TYPE_OF_DOMAIN, site_cutoff, window_day, window_days
from assetops_backend.chain.reader import grade_counts_of
from assetops_backend.chain.threads import classify
from assetops_backend.chain.vocabulary import Claim, count_claim, sum_days

OPEN_THREADS, VERIFIED_RESULTS, OPPORTUNITIES = "count.open_threads", "count.verified_results", "count.opportunities"
SITES_DISRUPTED = "count.sites_disrupted"   # CH6b2-R Q2: additive on `/estate/chain` `counts` and `summary.claims`
CLAIM_KEYS = (OPEN_THREADS, VERIFIED_RESULTS, OPPORTUNITIES, SITES_DISRUPTED)
PROTECT = "PROTECT_ASSET"
DISRUPTED_STATES = ("OPEN", "RECURRED", "ACTION_IN_HAND")


@dataclass(frozen=True)
class EstateCounts:
    """The one computation's result: the claims by key, and the per-Site parts `/estate/chain` lists."""

    claims: Mapping[str, Claim]
    days: Mapping[str, Any]          # site_code -> GradeCounts | None
    threads: Mapping[str, Any]       # site_code -> {"open", "in_hand", "verified"} | None
    #: CH6b2-R Q2: site_code -> the Site's disrupting threads (None: the read failed); the card's "Why?" names them.
    disrupted: Mapping[str, Any] = field(default_factory=dict)

    def claims_json(self, keys: Sequence[str] = CLAIM_KEYS) -> dict[str, dict[str, Any]]:
        return {k: self.claims[k].to_json() for k in keys}


def _measures(domain: str) -> tuple[str, ...]:
    return tuple(m.key for m in measures_for(SITE_TYPE_OF_DOMAIN[domain]))


def _finding_threads(rows: Mapping[str, Any], lo: datetime, hi: datetime) -> set[str]:
    """Threads with a Finding occurrence whose episode meets `[lo, hi)` (§B14 Q7)."""
    out = set()
    for o in rows.get("occurrences", ()):
        start, end = o["episode_start"], o["episode_end"]
        if o.get("finding_id") is not None and start is not None and start < hi and (end is None or end > lo):
            out.add(o["thread_id"])
    return out


def claim_days(req: Any, site: Any, lo: datetime, hi: datetime) -> Any:
    """§B14 Q8: one Site's `GradeCounts` over the estate window's days (`window_days`, the summary card's frame)."""
    facts = req.day(site.site_id, SITE_TYPE_OF_DOMAIN[site.domain], window_days(lo, hi, site.timezone))
    return grade_counts_of(facts, _measures(site.domain))


def counted_threads(req: Any, site: Any, lo: datetime, hi: datetime) -> list[dict[str, Any]]:
    """§B14 Q7: the counted threads of one Site (a Finding occurrence whose episode meets `[lo, hi)`), read on
    `window_day` at the per-Site cutoff. Early warnings are not threads, so they never enter (CH6b2-R Q2a)."""
    rows = req.threads(site.site_id)
    k = req.k
    ev = None if site.domain == MINI_DOMAIN else req.evidence_cutoff(site.site_id)
    cutoff = site_cutoff(site.domain, k, ev, k)
    wanted = _finding_threads(rows, lo, hi)
    threads = site_chain.threads_of(rows, site=site.site_code, domain=site.domain, tz=site.timezone, lo=lo, hi=hi,
                                    day=window_day(lo, hi, site.timezone), cutoff=cutoff)
    return [t for t in threads if t["id"] in wanted]


def site_thread_states(req: Any, site: Any, lo: datetime, hi: datetime) -> list[str | None]:
    """§B14 Q7: one state per counted thread of one Site."""
    return [t["state"] for t in counted_threads(req, site, lo, hi)]


def primary_category(thread: Mapping[str, Any]) -> str | None:
    """The thread's primary category: its first MOVES item (`outcome_roles` moves[0], as `estate/portfolio.py`
    `category_counts`); None when NOT_MAPPED."""
    items = ((thread.get("categories") or {}).get("items")) or ()
    return next((i["category"] for i in items if i.get("role") == "MOVES"), None)


def disrupting(threads: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """CH6b2-R Q2: the counted threads that disrupt service: primary Protect and OPEN, RECURRED or ACTION_IN_HAND."""
    return [t for t in threads if t.get("state") in DISRUPTED_STATES and primary_category(t) == PROTECT]


def opportunity_items(port: Any, sites: Sequence[Any], lo: datetime, hi: datetime,
                      known_at: datetime | None) -> list[Any] | None:
    """The CH-4 items of the mini Sites in scope: one memoised `opportunity_threads` read (None: the read failed;
    [] without a port or a mini Site)."""
    minis = [s for s in sites if s.domain == MINI_DOMAIN]
    if port is None or not minis:
        return []
    try:
        return list(read_scope.memo("chain.opportunities", port.opportunity_threads, minis[0].tenant_id,
                                    tuple(str(s.site_id) for s in minis), lo, hi, known_at))
    except Exception:  # noqa: BLE001 - a failed read is a null count (NOT_KNOWN), never zero
        return None


def estate_count_claims(req: Any, sites: Sequence[Any], lo: datetime, hi: datetime,
                        opportunities: Sequence[Any] | None,
                        unavailable: tuple[type[BaseException], ...] = ()) -> EstateCounts:
    """The three count claims over `sites` (SiteRefs) in `[lo, hi)` at the request's cutoff (module doc)."""
    days: dict[str, Any] = {}
    threads: dict[str, Any] = {}
    disrupted: dict[str, Any] = {}
    for site in sites:
        try:
            days[site.site_code] = claim_days(req, site, lo, hi)
        except unavailable:
            days[site.site_code] = None
        try:
            counted = counted_threads(req, site, lo, hi)
            threads[site.site_code] = classify(t["state"] for t in counted)
            disrupted[site.site_code] = disrupting(counted)
        except unavailable:
            threads[site.site_code] = disrupted[site.site_code] = None
    summed = sum_days([days[s.site_code] for s in sites])
    per = list(threads.values())
    known = all(t is not None for t in per)
    open_n = sum(t["open"] + t["in_hand"] for t in per) if known else None
    verified_n = sum(t["verified"] for t in per) if known else None
    opp_n = None if opportunities is None else len(opportunities)
    disrupted_n = sum(1 for t in disrupted.values() if t) if known else None
    claims = {OPEN_THREADS: count_claim(OPEN_THREADS, open_n, summed),
              VERIFIED_RESULTS: count_claim(VERIFIED_RESULTS, verified_n, summed),
              OPPORTUNITIES: count_claim(OPPORTUNITIES, opp_n, summed),
              SITES_DISRUPTED: count_claim(SITES_DISRUPTED, disrupted_n, summed)}
    return EstateCounts(claims, days, threads, disrupted)


class EstateClaims:
    """The injected callable of the two estate services (§B14 Q8): `(tenant_id, site_codes, lo, hi, known_at)` ->
    `EstateCounts`, over the board service's `ChainReader` and thread port and the Site registry, with the same
    request (`known_at`) `/estate/chain` reads with. Built in `chain/composition.py`, wired in `main.py`."""

    def __init__(self, chain_reader: Callable[[], Any], opportunities: Callable[[], Any],
                 resolve: Callable[[str], Any], unavailable: tuple[type[BaseException], ...] = ()) -> None:
        self._reader, self._opportunities, self._resolve = chain_reader, opportunities, resolve
        self._unavailable = unavailable

    def __call__(self, tenant_id: Any, site_codes: Sequence[str], lo: datetime, hi: datetime,
                 known_at: datetime | None) -> EstateCounts | None:
        reader = self._reader()
        if reader is None:
            return None
        try:
            sites = [s for s in (self._resolve(c) for c in site_codes) if s is not None]
        except self._unavailable:
            return None  # the Site registry could not be read: every claim NOT_KNOWN
        req = reader.request(tenant_id, known_at)
        items = opportunity_items(self._opportunities(), sites, lo, hi, known_at)
        return estate_count_claims(req, sites, lo, hi, items, self._unavailable)
