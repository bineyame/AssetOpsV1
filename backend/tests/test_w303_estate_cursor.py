"""W3-03 run 0a: the Portfolio parser kind and its five-part cursor (pure; no storage).

Spec: `.agent/W3-03-build-spec.md` Review closure 4, "B1/B2 — shared selection and sole editor". The Portfolio cursor
is the Finding key set plus `kind`, with `state_filter` null and the marker
[episode_start_or_null, site_code_key, site_id, finding_id, finding_revision_id]; existing roots keep their key sets
and bytes (see `test_w302_estate_cursor.py`).
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from assetops_backend.estate.index import EstateIndexService
from assetops_backend.estate.scope import (
    EstateRefusal, cursor_after, decode_cursor, encode_cursor, parse_request, resume_after, selection_token)

T = UUID("10000000-0000-4000-8000-000000000001")
S = UUID("10000000-0000-4000-8000-000000000011")
S2 = UUID("10000000-0000-4000-8000-000000000012")
F = "30000000-0000-4000-8000-000000000001"
FR = "30000000-0000-4000-8000-000000000002"
READ_AT = datetime(2026, 10, 8, tzinfo=timezone.utc)
D0, D1 = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 8, tzinfo=timezone.utc)
WIN = [("from", "2026-10-01T00:00:00Z"), ("to", "2026-10-08T00:00:00Z")]
MARK = (datetime(2026, 10, 6, 4, tzinfo=timezone.utc), "kobo-001", str(S), F, FR)
NULL_MARK = (None, *MARK[1:])


class Snap:
    def __init__(self, sites) -> None:
        self.read_at, self.historical, self.continuation, self.basis_historical = READ_AT, False, False, False
        self._sites = sites

    def imported_sites(self, tenant_id, to):
        return self._sites


SITES = [{"site_id": S, "site_code": "SITE-A"}, {"site_id": S2, "site_code": "SITE-B"}]


def _refused(code, fn, *args):
    with pytest.raises(EstateRefusal) as error:
        fn(*args)
    assert error.value.code == code
    return error.value


def _scope(cursor=None, known_at=None, admit=lambda code: True, lens=None):
    items = list(WIN) + ([] if lens is None else [("lens", lens)]) + (
        [] if known_at is None else [("known_at", known_at)]) + ([] if cursor is None else [("cursor", cursor)])
    req = parse_request("portfolio", items)
    return req, EstateIndexService._scope(Snap(SITES), T, req, admit)


def _token(scope, known=READ_AT, lens="all"):
    return selection_token(T, scope["ids"], D0, D1, known, lens, None, [])


def _page_two(marker, known_at=None, lens=None):
    req, scope = _scope(known_at=known_at, lens=lens)
    token = _token(scope, scope["token_k"], req.lens)
    return token, EstateIndexService._cursor(T, req, scope, token, *marker)


def _payload(cursor):
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))


def test_portfolio_parser_validates_lens_and_forbids_state() -> None:
    req = parse_request("portfolio", WIN + [("lens", "cost"), ("limit", "100"), ("known_at", "2026-10-07T00:00:00Z")])
    assert (req.kind, req.lens, req.state_filter, req.limit) == ("portfolio", "cost", None, 100)
    assert parse_request("portfolio", WIN).lens == "all"
    for lens in ("all", "cost", "risks", "opportunities"):
        assert parse_request("portfolio", WIN + [("lens", lens)]).lens == lens
    _refused("INVALID_LENS", parse_request, "portfolio", WIN + [("lens", "money")])
    _refused("INVALID_CURSOR", parse_request, "portfolio", WIN + [("state", "all")])  # forbidden key
    _refused("INVALID_CURSOR", parse_request, "portfolio", WIN + [("lens", "all"), ("lens", "cost")])
    _refused("INVALID_WINDOW", parse_request, "portfolio", WIN[:1])
    _refused("INVALID_LIMIT", parse_request, "portfolio", WIN + [("limit", "0")])


def test_five_part_marker_round_trips_with_null_first_member() -> None:
    for marker in (MARK, NULL_MARK):
        token, cursor = _page_two(marker, lens="risks")
        payload = _payload(cursor)
        assert set(payload) == {"v", "kind", "tenant_id", "authorized_site_ids", "access_basis", "from", "to",
                                "known_at", "lens", "state_filter", "selection_token", "after", "page_one_mode"}
        assert (payload["kind"], payload["lens"], payload["state_filter"]) == ("portfolio", "risks", None)
        assert payload["page_one_mode"] == "live" and payload["v"] == 1
        assert decode_cursor("portfolio", cursor) == payload
        assert cursor_after(payload) == marker
        req, scope = _scope(cursor=cursor, lens="risks")
        assert EstateIndexService._fence(T, req, scope, token) == marker
    assert _payload(_page_two(NULL_MARK)[1])["after"][0] is None
    assert _payload(_page_two(MARK)[1])["after"][0] == "2026-10-06T04:00:00.000000Z"
    rows = [MARK, NULL_MARK]
    assert resume_after(rows, MARK) == 1
    _refused("INVALID_CURSOR", resume_after, rows, (None, "kobo-001", str(S2), F, FR))  # valid nonmember: 422


def _mutated(marker, changes):
    payload = _payload(_page_two(marker)[1])
    for key, value in changes.items():
        if value is ...:
            payload.pop(key)
        else:
            payload[key] = value
    return encode_cursor(payload)


@pytest.mark.parametrize("changes", [
    {"kind": ...}, {"kind": "findings"}, {"kind": "financials"}, {"page_one_mode": ...},
    {"page_one_mode": "current"}, {"state_filter": "SUPPORTED"}, {"state_filter": ...}, {"lens": ...},
    {"lens": "money"}, {"limit": 50}, {"v": 2},
    {"after": ["2026-10-06T04:00:00.000000Z", "kobo-001"]},  # arity
    {"after": [None, "kobo-001", str(S), F]},
    {"after": [None, "kobo-001", str(S), F, FR, "x"]},
    {"after": ["2026-10-06T04:00:00Z", "kobo-001", str(S), F, FR]},  # non-canonical instant
    {"after": [None, "", str(S), F, FR]},  # empty site_code_key
    {"after": [None, "kobo-001", "not-a-uuid", F, FR]},
    {"after": [None, "kobo-001", str(S), "finding-1", FR]},
    {"after": [None, "kobo-001", str(S), F, 7]},
    {"known_at": "2026-10-08T00:00:00Z"},  # non-canonical cutoff
    {"authorized_site_ids": [7]},
])
def test_malformed_portfolio_cursor_is_422_invalid_cursor(changes) -> None:
    cursor = _mutated(MARK, changes)
    _refused("INVALID_CURSOR", decode_cursor, "portfolio", cursor)
    _refused("INVALID_CURSOR", parse_request, "portfolio", WIN + [("cursor", cursor)])  # never a 500


def test_portfolio_and_other_kinds_do_not_cross() -> None:
    cursor = _page_two(MARK)[1]
    for other in ("findings", "actions", "evidence", "financials", "scope"):
        _refused("INVALID_CURSOR", decode_cursor, other, cursor)
    at = datetime(2026, 10, 6, 10, tzinfo=timezone.utc)
    for kind, extra in (("findings", [("lens", "all"), ("state", "all")]), ("actions", [])):
        req = parse_request(kind, WIN + extra)
        scope = EstateIndexService._scope(Snap(SITES), T, req, lambda code: True)
        _refused("INVALID_CURSOR", decode_cursor, "portfolio", EstateIndexService._cursor(T, req, scope, "t", at, "r"))


def test_changed_grant_lens_window_cutoff_or_token_is_409_before_marker_lookup() -> None:
    token, cursor = _page_two(MARK)
    req, scope = _scope(cursor=cursor, admit=lambda code: code == "SITE-A")  # changed grant
    assert _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope, _token(scope)).status == 409
    req, scope = _scope(cursor=cursor, lens="cost")  # changed lens
    _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope, token)
    req, scope = _scope(cursor=cursor)  # changed selection digest
    _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope, "sha256:" + "0" * 64)
    req = parse_request("portfolio", [("from", "2026-10-02T00:00:00Z"), ("to", "2026-10-08T00:00:00Z"),
                                      ("cursor", cursor)])  # changed window
    scope = EstateIndexService._scope(Snap(SITES), T, req, lambda code: True)
    _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope, token)
    _refused("ESTATE_BASIS_CHANGED", _scope, cursor, "2026-10-07T00:00:00Z")  # changed cutoff


def test_historical_page_two_keeps_page_one_mode_and_cutoff() -> None:
    token, cursor = _page_two(NULL_MARK, known_at="2026-10-05T00:00:00Z")
    payload = _payload(cursor)
    assert payload["page_one_mode"] == "historical" and payload["known_at"] == "2026-10-05T00:00:00.000000Z"
    req, scope = _scope(cursor=cursor)
    assert scope["page_one_mode"] == "historical" and scope["k"] == datetime(2026, 10, 5, tzinfo=timezone.utc)
    assert EstateIndexService._fence(T, req, scope, token) == NULL_MARK
    # a live page one: a captured cutoff is a paging fence, never a historical basis
    _, live = _page_two(MARK)
    _, scope = _scope(cursor=live)
    assert scope["page_one_mode"] == "live"
