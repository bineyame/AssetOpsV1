"""W3-02 commit 0a: shared estate parser kinds and the 3- and 5-part cursor markers (pure; no storage).

Spec: `.agent/W3-02-build-spec.md` Review closure 4, "Shared parser, 3- and 5-part cursor, refusals (B1, S7-S8)".
Finding/Action two-part cursors keep their emitted bytes; the new markers are unsigned (no tamper claim).
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from assetops_backend.estate.index import EstateIndexService
from assetops_backend.estate.scope import (
    EstateRefusal, access_basis, cursor_after, decode_cursor, encode_cursor, parse_request, resume_after,
    selection_token)

T = UUID("10000000-0000-4000-8000-000000000001")
S = UUID("10000000-0000-4000-8000-000000000011")
S2 = UUID("10000000-0000-4000-8000-000000000012")
READ_AT = datetime(2026, 10, 8, tzinfo=timezone.utc)
D0, D1 = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 8, tzinfo=timezone.utc)
WIN = [("from", "2026-10-01T00:00:00Z"), ("to", "2026-10-08T00:00:00Z")]
EV_MARK = ("site-a", str(S), "temperature@2026-10-01T00:00:00.000000Z/2026-10-02T00:00:00.000000Z")
FIN_MARK = (datetime(2026, 10, 1, 6, tzinfo=timezone.utc), "site-a", str(S), "PRODUCT_EXPOSURE",
            "cold_chain:20000000-0000-4000-8000-000000000001")


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


def _scope(kind, cursor=None, known_at=None, admit=lambda code: True, sites=SITES):
    items = list(WIN) + ([] if known_at is None else [("known_at", known_at)]) + (
        [] if cursor is None else [("cursor", cursor)])
    req = parse_request(kind, items)
    return req, EstateIndexService._scope(Snap(sites), T, req, admit)


def _token(scope, known=READ_AT):
    return selection_token(T, scope["ids"], D0, D1, known, None, None, [])


def _page_two(kind, marker, known_at=None):
    req, scope = _scope(kind, known_at=known_at)
    token = _token(scope, scope["token_k"])
    return token, EstateIndexService._cursor(T, req, scope, token, *marker)


def _payload(cursor):
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))


def test_parser_new_kinds_and_unsupported_kind_is_typed_422() -> None:
    for kind in ("evidence", "financials"):
        req = parse_request(kind, WIN + [("known_at", "2026-10-07T00:00:00Z"), ("limit", "100")])
        assert (req.kind, req.limit, req.lens, req.state_filter) == (kind, 100, None, None)
        assert parse_request(kind, WIN).limit == 50
        _refused("INVALID_CURSOR", parse_request, kind, WIN + [("lens", "all")])  # unknown key
        _refused("INVALID_CURSOR", parse_request, kind, WIN + [("state", "all")])
        _refused("INVALID_CURSOR", parse_request, kind, WIN + [("limit", "5"), ("limit", "6")])  # repeated
        _refused("INVALID_WINDOW", parse_request, kind, WIN + [("from", "2026-10-01T00:00:00Z")])
        _refused("INVALID_WINDOW", parse_request, kind, WIN[:1])
        _refused("INVALID_LIMIT", parse_request, kind, WIN + [("limit", "101")])
        _refused("INVALID_KNOWN_AT", parse_request, kind, WIN + [("known_at", "2026-10-07T00:00:00+03:00")])
        _refused("INVALID_CURSOR", parse_request, kind, WIN + [("cursor", "not-a-cursor")])
    for kind in ("money", "", "Evidence"):  # an unsupported kind: typed 422, never KeyError/500
        refusal = _refused("INVALID_CURSOR", parse_request, kind, WIN)
        assert refusal.status == 422 and refusal.detail["rows"] is None
        _refused("INVALID_CURSOR", decode_cursor, kind, "e30")


def test_both_marker_arities_round_trip_and_null_first_money() -> None:
    for kind, marker in (("evidence", EV_MARK), ("financials", FIN_MARK), ("financials", (None, *FIN_MARK[1:]))):
        token, cursor = _page_two(kind, marker)
        payload = _payload(cursor)
        assert set(payload) == {"v", "kind", "tenant_id", "authorized_site_ids", "access_basis", "from", "to",
                                "known_at", "selection_token", "after", "page_one_mode"}
        assert payload["kind"] == kind and payload["page_one_mode"] == "live" and payload["v"] == 1
        assert decode_cursor(kind, cursor) == payload
        assert cursor_after(payload) == marker
        req, scope = _scope(kind, cursor=cursor)
        assert EstateIndexService._fence(T, req, scope, token) == marker
    assert _payload(_page_two("financials", (None, *FIN_MARK[1:]))[1])["after"][0] is None
    assert _payload(_page_two("financials", FIN_MARK)[1])["after"][0] == "2026-10-01T06:00:00.000000Z"
    rows = [EV_MARK, ("site-b", str(S2), "sessions@x")]
    assert resume_after(rows, EV_MARK) == 1
    _refused("INVALID_CURSOR", resume_after, rows, ("site-c", str(S2), "sessions@x"))  # absent marker: 422


def _mutated(kind, marker, changes):
    payload = _payload(_page_two(kind, marker)[1])
    for key, value in changes.items():
        if value is ...:
            payload.pop(key)
        else:
            payload[key] = value
    return encode_cursor(payload)


@pytest.mark.parametrize("kind,marker,changes", [
    ("evidence", EV_MARK, {"page_one_mode": ...}),  # missing page_one_mode
    ("evidence", EV_MARK, {"page_one_mode": "current"}),
    ("evidence", EV_MARK, {"kind": "financials"}),  # wrong kind
    ("financials", FIN_MARK, {"kind": "evidence"}),
    ("evidence", EV_MARK, {"limit": 50}),  # unknown key
    ("evidence", EV_MARK, {"lens": "all"}),
    ("evidence", EV_MARK, {"v": 2}),
    ("evidence", EV_MARK, {"after": list(EV_MARK[:2])}),  # arity
    ("evidence", EV_MARK, {"after": [*EV_MARK, "x"]}),
    ("evidence", EV_MARK, {"after": ["site-a", "not-a-uuid", EV_MARK[2]]}),
    ("evidence", EV_MARK, {"after": ["", str(S), EV_MARK[2]]}),
    ("evidence", EV_MARK, {"after": ["site-a", str(S), 7]}),
    ("financials", FIN_MARK, {"after": ["2026-10-01T06:00:00Z", *FIN_MARK[1:]]}),  # non-canonical instant
    ("financials", FIN_MARK, {"after": ["2026-10-01T06:00:00.000000+03:00", *FIN_MARK[1:]]}),
    ("financials", FIN_MARK, {"after": [None, "site-a", "nope", "RECORDED_REPAIR", "cold_chain:x"]}),
    ("financials", FIN_MARK, {"after": [None, "site-a", str(S), "", "cold_chain:x"]}),
    ("financials", FIN_MARK, {"after": [None, "site-a", str(S), "RECORDED_REPAIR"]}),
    ("financials", FIN_MARK, {"after": [None, "2026-10-01T06:00:00.000000Z"]}),  # two-part on money
    ("financials", FIN_MARK, {"known_at": "2026-10-08T00:00:00Z"}),  # non-canonical cutoff
    ("financials", FIN_MARK, {"authorized_site_ids": [7]}),
])
def test_malformed_new_cursor_is_422_invalid_cursor(kind, marker, changes) -> None:
    cursor = _mutated(kind, marker, changes)
    _refused("INVALID_CURSOR", decode_cursor, kind, cursor)
    _refused("INVALID_CURSOR", parse_request, kind, WIN + [("cursor", cursor)])  # never a 500


def test_kinds_do_not_cross_and_old_cursors_stay_two_part() -> None:
    ev = _page_two("evidence", EV_MARK)[1]
    for other in ("financials", "actions", "findings", "scope"):
        _refused("INVALID_CURSOR", decode_cursor, other, ev)
    at = datetime(2026, 10, 6, 10, tzinfo=timezone.utc)
    act = _page_two("actions", (at, "action-1"))[1]
    for other in ("evidence", "financials"):
        _refused("INVALID_CURSOR", decode_cursor, other, act)
    assert cursor_after(decode_cursor("actions", act)) == (at, "action-1")


def test_finding_and_action_cursor_bytes_unchanged() -> None:
    at = datetime(2026, 10, 6, 10, tzinfo=timezone.utc)
    for kind, extra in (("findings", [("lens", "all"), ("state", "all")]), ("actions", [])):
        req = parse_request(kind, WIN + extra)
        scope = EstateIndexService._scope(Snap(SITES), T, req, lambda code: True)
        ids = sorted(str(x["site_id"]).lower() for x in SITES)
        expected = {"v": 1, "tenant_id": str(T), "authorized_site_ids": ids, "access_basis": access_basis(T, ids),
                    "from": "2026-10-01T00:00:00.000000Z", "to": "2026-10-08T00:00:00.000000Z",
                    "known_at": "2026-10-08T00:00:00.000000Z", "selection_token": "sha256:t",
                    "after": ["2026-10-06T10:00:00.000000Z", "row-1"], "page_one_mode": "live"}
        expected.update({"lens": "all", "state_filter": "all"} if kind == "findings" else {"kind": "actions"})
        raw = json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("utf-8")
        old = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        assert EstateIndexService._cursor(T, req, scope, "sha256:t", at, "row-1") == old


def test_changed_grant_selection_or_old_digest_is_409_before_marker_lookup() -> None:
    for kind, marker in (("evidence", EV_MARK), ("financials", FIN_MARK)):
        token, cursor = _page_two(kind, marker)
        # changed grant: SITE-B no longer admitted
        req, scope = _scope(kind, cursor=cursor, admit=lambda code: code == "SITE-A")
        assert _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope,
                        _token(scope)).status == 409
        # changed selection digest under the same grant
        req, scope = _scope(kind, cursor=cursor)
        _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope, "sha256:" + "0" * 64)
        # an old estate-selection/1 digest carried by a structurally valid cursor reaches 409, not 422
        old = encode_cursor({**_payload(cursor), "selection_token": "sha256:" + "1" * 64})
        req, scope = _scope(kind, cursor=old)
        _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope, token)
        # changed window
        items = [("from", "2026-10-02T00:00:00Z"), ("to", "2026-10-08T00:00:00Z"), ("cursor", cursor)]
        req = parse_request(kind, items)
        scope = EstateIndexService._scope(Snap(SITES), T, req, lambda code: True)
        _refused("ESTATE_BASIS_CHANGED", EstateIndexService._fence, T, req, scope, token)
        # changed cutoff: refused while the scope normalizes it, before any marker lookup
        _refused("ESTATE_BASIS_CHANGED", _scope, kind, cursor, "2026-10-07T00:00:00Z")


def test_historical_page_two_keeps_page_one_mode_and_cutoff() -> None:
    for kind, marker in (("evidence", EV_MARK), ("financials", (None, *FIN_MARK[1:]))):
        token, cursor = _page_two(kind, marker, known_at="2026-10-05T00:00:00Z")
        payload = _payload(cursor)
        assert payload["page_one_mode"] == "historical" and payload["known_at"] == "2026-10-05T00:00:00.000000Z"
        req, scope = _scope(kind, cursor=cursor)  # page two omits known_at: the cursor's cutoff governs
        assert scope["page_one_mode"] == "historical" and scope["k"] == datetime(2026, 10, 5, tzinfo=timezone.utc)
        assert EstateIndexService._fence(T, req, scope, token) == marker
        req, scope = _scope(kind, cursor=cursor, known_at="2026-10-05T00:00:00Z")  # wire-second copy is accepted
        assert EstateIndexService._fence(T, req, scope, token) == marker
