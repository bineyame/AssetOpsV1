"""DIESEL-K5 (`.agent/build-sheet-DIESEL-1.md` §9l.2, ruling DIESEL-1-R3l): the read behind the Fuel page's night mode,
the fuel Finding page and the Site Findings "Fuel checks" panel.

Read-only. Windows and fuel Findings come through K3/K4a's `PostgresFuelBalanceStore` (`has_windows`, `windows`,
`fuel_findings`, `fuel_finding`) and its two K5 snapshot reads (`night_context`; `night_records_and_provenance`, which
runs K2's caller-connection `select_fuel_records` and the mini-depth provenance builder `mini_blocks`, the block the
mini-depth fuel read returns, with the window revision as the basis selection). No storage technology here: the
store is the adapter. Every visible string is composed by `night_text` (or K4a's `finding_text`).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import quote
from uuid import UUID

from assetops_backend.chain import refs
from assetops_backend.chain.read import window_days
from assetops_backend.fuel_balance import finding_text, night_text

#: Nights list: the default span and the most a request may ask for.
DEFAULT_NIGHTS = 14
MAX_NIGHTS = 31
_EARLIEST, _LATEST = date(2000, 1, 1), date(2100, 1, 1)


class FuelNightRefused(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class FuelNightUnavailable(Exception):
    """The product database could not be read."""


def site_path(code: str) -> str:
    return f"/sites/{quote(code, safe='')}"


def fuel_page_href(code: str, night_date: date) -> str:
    return f"{site_path(code)}/performance/fuel?night={night_date.isoformat()}"


class FuelNightRead:
    def __init__(self, *, store: Any, link_rows: Any,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        """`store` is the fuel-balance store (`fuel_balance/composition.py`) and `link_rows` the evidence link-row
        reader (`evidence/composition.py`), both injected by `main.py`."""
        self._store = store
        self._link_rows = link_rows
        # Test-only virtual read instant; the production composition never passes it.
        self.test_read_clock_override = test_read_clock_override

    def dispose(self) -> None:
        self._store.dispose()

    @staticmethod
    def _guard(work: Callable[[], Any]) -> Any:
        """A store failure is a typed unavailable read (the API's 503); a refusal or a programming error is not."""
        try:
            return work()
        except (FuelNightRefused, ValueError, TypeError, KeyError, AttributeError):
            raise
        except Exception as error:  # the adapter's driver errors; the domain layer names no storage technology
            raise FuelNightUnavailable(f"The fuel night read failed: {error.__class__.__name__}") from error

    def _context(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> tuple[str, str | None, datetime]:
        """The Site's time zone, its one active fuel tank (None when not exactly one) and the as-known instant."""
        tz, tank, now = self._guard(lambda: self._store.night_context(tenant_id, site_id))
        if self.test_read_clock_override is not None:
            now = self.test_read_clock_override()
        now = now.astimezone(timezone.utc)
        if known_at is not None and known_at > now:
            raise FuelNightRefused("INVALID_KNOWN_AT")
        return tz, tank, (now if known_at is None else known_at)

    def _records_and_provenance(self, tenant_id: UUID, site_id: UUID, windows: list[Any],
                                known: datetime, records_of: Any = None) -> tuple[list[Any], dict[str, Any]]:
        return self._guard(lambda: self._store.night_records_and_provenance(
            tenant_id, site_id, windows, known, records_of, self._link_rows))

    # --- route 1: the nights list ------------------------------------------------------------------------------

    def nights(self, *, tenant_id: UUID, site_id: UUID, code: str, lo: date | None, hi: date | None,
               known_at: datetime | None, window: tuple[datetime, datetime] | None = None) -> dict[str, Any]:
        """`lo`/`hi` are the night dates `[lo, hi)`. SR-10k: `window` is the date range's UTC instants `[from, to)`;
        the nights listed are those whose `night_date` is one of `window_days(from, to, tz)` (D-SR.45), at most
        `MAX_NIGHTS`, else `FuelNightRefused("INVALID_WINDOW")`."""
        tz, tank, known = self._context(tenant_id, site_id, known_at)
        if window is not None:
            days = window_days(window[0], window[1], tz)
            if not days or len(days) > MAX_NIGHTS:
                raise FuelNightRefused("INVALID_WINDOW")
            lo, hi = days[0], days[-1] + timedelta(days=1)
        listed: list[Any] = []
        has = tank is not None and self._guard(lambda: self._store.has_windows(tenant_id, site_id, known))
        if has:
            if lo is None or hi is None:
                every = self._guard(lambda: self._store.windows(tenant_id, site_id, UUID(tank), _EARLIEST, _LATEST,
                                                                known))
                end = every[-1].night_date + timedelta(days=1)
                lo, hi = end - timedelta(days=DEFAULT_NIGHTS), end
                listed = [w for w in every if lo <= w.night_date < hi]
            else:
                listed = list(self._guard(lambda: self._store.windows(tenant_id, site_id, UUID(tank), lo, hi, known)))
        _, blocks = self._records_and_provenance(tenant_id, site_id, listed, known)
        return {"site_code": code, "mode": "NIGHTS" if has else "NONE", "time_zone": tz, "known_at": known.isoformat(),
                "nights": [night_text.night_summary(w) for w in listed], "provenance": blocks}

    # --- route 2: one night ------------------------------------------------------------------------------------

    def _night_body(self, tenant_id: UUID, site_id: UUID, code: str, tz: str, window: Any,
                    known: datetime) -> dict[str, Any]:
        records, blocks = self._records_and_provenance(tenant_id, site_id, [window], known, records_of=window)
        view = night_text.night_view(window, records, tz)
        return {"site_code": code, "night_date": view.pop("night_date"), "label": view.pop("label"), "time_zone": tz,
                "known_at": known.isoformat(), **view, "provenance": blocks,
                "links": {"evidence": refs.href_for(refs.evidence_ref(code)),
                          "fuel_page": fuel_page_href(code, window.night_date)}}

    def night(self, *, tenant_id: UUID, site_id: UUID, code: str, night_date: date,
              known_at: datetime | None) -> dict[str, Any] | None:
        tz, tank, known = self._context(tenant_id, site_id, known_at)
        if tank is None:
            return None
        found = self._guard(lambda: self._store.windows(tenant_id, site_id, UUID(tank), night_date,
                                                        night_date + timedelta(days=1), known))
        if not found:
            return None
        window = found[0]
        body = self._night_body(tenant_id, site_id, code, tz, window, known)
        cited = [f for f in self._guard(lambda: self._store.fuel_findings(
            tenant_id, site_id, window.window_start, window.window_end, known))
            if f.night_date == window.night_date and str(f.window.tank_asset_id) == str(window.tank_asset_id)]
        if cited:
            ff = cited[0]
            lines = finding_text.finding_lines(ff, tz)
            body["finding"] = {"finding_id": str(ff.finding_id), "title": finding_text.TITLE,
                               "text": lines["claim"] or lines["no_longer"],
                               "href": refs.href_for(refs.fuel_finding_ref(code, str(ff.finding_id)))}
            body["finding_note"] = None
        else:
            body["finding"] = None
            body["finding_note"] = night_text.finding_note(window.state)
        return body

    # --- route 3: the Site's fuel Findings ---------------------------------------------------------------------

    def fuel_findings(self, *, tenant_id: UUID, site_id: UUID, code: str, lo: datetime, hi: datetime,
                      known_at: datetime | None) -> dict[str, Any]:
        _, _, known = self._context(tenant_id, site_id, known_at)
        found = self._guard(lambda: self._store.fuel_findings(tenant_id, site_id, lo, hi, known))
        return {"site_code": code, "rows": [{
            "finding_id": str(f.finding_id), "night_date": f.night_date.isoformat(), "lifecycle": f.lifecycle,
            "text": night_text.fuel_checks_row(f),
            "href": refs.href_for(refs.fuel_finding_ref(code, str(f.finding_id)))} for f in found]}

    # --- route 4: one fuel Finding -----------------------------------------------------------------------------

    def fuel_finding(self, *, tenant_id: UUID, site_id: UUID, code: str, finding_id: UUID,
                     revision_id: UUID | None, known_at: datetime | None) -> dict[str, Any] | None:
        tz, _, known = self._context(tenant_id, site_id, known_at)
        revisions: list[Any] = []
        at: datetime | None = known
        while True:  # each earlier revision is the latest as known just before the next one was written
            head = self._guard(lambda: self._store.fuel_finding(tenant_id, site_id, finding_id, at))
            if head is None or (revisions and head.revision_no >= revisions[-1].revision_no):
                break
            revisions.append(head)
            at = head.created_at - timedelta(microseconds=1)
        if not revisions:
            return None
        chosen = revisions[0] if revision_id is None else next(
            (r for r in revisions if str(r.revision_id) == str(revision_id)), None)
        if chosen is None:
            return None
        night = self._night_body(tenant_id, site_id, code, tz, chosen.window, known)
        canonical = refs.href_for(refs.fuel_finding_ref(code, str(finding_id)))
        return {"site_code": code, "finding_id": str(finding_id), "revision_id": str(chosen.revision_id),
                "revision_no": chosen.revision_no, "lifecycle": chosen.lifecycle,
                "lifecycle_text": night_text.LIFECYCLE.get(chosen.lifecycle, chosen.lifecycle),
                "night_date": chosen.night_date.isoformat(), "label": night_text.night_label(chosen.night_date),
                "lines": finding_text.finding_lines(chosen, tz), "night": night,
                "revisions": [{"revision_id": str(r.revision_id), "revision_no": r.revision_no,
                               "text": night_text.version_row(r.revision_no, r.lifecycle, r.created_at, tz)}
                              for r in sorted(revisions, key=lambda r: r.revision_no)],
                "provenance": night["provenance"],
                "links": {"canonical": canonical, "fuel_night": fuel_page_href(code, chosen.night_date),
                          "fuel_night_label": night_text.FUEL_NIGHT_LINK}}


__all__ = ["DEFAULT_NIGHTS", "MAX_NIGHTS", "FuelNightRead", "FuelNightRefused", "FuelNightUnavailable",
           "fuel_page_href"]
