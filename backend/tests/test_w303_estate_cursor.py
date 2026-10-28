"""W3-03 run 0a: the Portfolio parser kind and its five-part cursor (pure; no storage).

Spec: `.agent/W3-03-build-spec.md` Review closure 4, "B1/B2 — shared selection and sole editor". The Portfolio cursor
is the Finding key set plus `kind`, with `state_filter` null and the marker
[episode_start_or_null, site_code_key, site_id, finding_id, finding_revision_id]; existing roots keep their key sets
and bytes (see `test_w302_estate_cursor.py`). Run-1b ruling Q-1b-1 (`.agent/W3-03-build-spec.md` "Run-1b rulings"):
the Portfolio cursor carries an HMAC-SHA-256 `mac` keyed by `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX`, verified before
any payload field is trusted; the key is a fixed test-only value set with `monkeypatch`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from assetops_backend.estate.index import EstateIndexService
from assetops_backend.estate.scope import (
    PORTFOLIO_CURSOR_KEY_ENV, EstateRefusal, cursor_after, decode_cursor, decode_portfolio_cursor, encode_cursor,
    encode_portfolio_cursor, parse_request, portfolio_cursor_key, resume_after, selection_token)

KEY_HEX = "a5" * 32  # test-only; never a committed default for any server
KEY = bytes.fromhex(KEY_HEX)


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, KEY_HEX)

T = UUID("10000000-0000-4000-8000-000000000001")
S = UUID("10000000-0000-4000-8000-000000000011")
S2 = UUID("10000000-0000-4000-8000-000000000012")
F = "30000000-0000-4000-8000-000000000001"
FR = "30000000-0000-4000-8000-000000000002"
READ_AT = datetime(2026, 10, 8, tzinfo=timezone.utc)
D0, D1 = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 8, tzinfo=timezone.utc)
WIN = [("from", "2026-10-01T00:00:00Z"), ("to", "2026-10-08T00:00:00Z")]
# CC-R2 (R5.4): the six-part Portfolio marker `(group_rank, at|None, site_code_key, site_id, finding_id, revision)`;
# these fixtures were five-part before CC-R2 and are rewritten by design.
MARK = (2, datetime(2026, 10, 6, 4, tzinfo=timezone.utc), "kobo-001", str(S), F, FR)
NULL_MARK = (2, None, *MARK[2:])
FIVE_PART = ["2026-10-06T04:00:00.000000Z", "kobo-001", str(S), F, FR]  # the pre-CC-R2 wire form


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


def test_six_part_marker_round_trips_with_null_instant() -> None:
    for marker in (MARK, NULL_MARK):
        token, cursor = _page_two(marker, lens="risks")
        payload = _payload(cursor)
        assert set(payload) == {"v", "kind", "tenant_id", "authorized_site_ids", "access_basis", "from", "to",
                                "known_at", "lens", "state_filter", "selection_token", "after", "page_one_mode", "mac"}
        mac = payload.pop("mac")
        assert len(mac) == 64 and mac == mac.lower()
        assert (payload["kind"], payload["lens"], payload["state_filter"]) == ("portfolio", "risks", None)
        assert payload["page_one_mode"] == "live" and payload["v"] == 1
        assert decode_portfolio_cursor(cursor, KEY) == payload
        _refused("INVALID_CURSOR", decode_cursor, "portfolio", cursor)  # no unsigned Portfolio path
        assert cursor_after(payload) == marker
        req, scope = _scope(cursor=cursor, lens="risks")
        assert EstateIndexService._fence(T, req, scope, token) == marker
    assert _payload(_page_two(NULL_MARK)[1])["after"][:2] == [2, None]
    assert _payload(_page_two(MARK)[1])["after"][:2] == [2, "2026-10-06T04:00:00.000000Z"]
    rows = [MARK, NULL_MARK]
    assert resume_after(rows, MARK) == 1
    _refused("INVALID_CURSOR", resume_after, rows, (2, None, "kobo-001", str(S2), F, FR))  # valid nonmember: 422
    _refused("INVALID_CURSOR", resume_after, rows, (3, *MARK[1:]))  # same row facts, another group: 422


def _mutated(marker, changes):
    """A shape mutation re-signed with the valid key, so the existing shape checks (not the MAC) refuse it."""
    payload = _payload(_page_two(marker)[1])
    payload.pop("mac")
    for key, value in changes.items():
        if value is ...:
            payload.pop(key)
        else:
            payload[key] = value
    return encode_portfolio_cursor(payload, KEY)


@pytest.mark.parametrize("changes", [
    {"kind": ...}, {"kind": "findings"}, {"kind": "financials"}, {"page_one_mode": ...},
    {"page_one_mode": "current"}, {"state_filter": "SUPPORTED"}, {"state_filter": ...}, {"lens": ...},
    {"lens": "money"}, {"limit": 50}, {"v": 2},
    {"after": [2, "2026-10-06T04:00:00.000000Z", "kobo-001"]},  # arity
    {"after": FIVE_PART},  # CC-R2: the pre-CC-R2 five-part cursor is refused
    {"after": [None, "kobo-001", str(S), F, FR]},  # five-part, null instant
    {"after": [2, None, "kobo-001", str(S), F]},
    {"after": [2, None, "kobo-001", str(S), F, FR, "x"]},
    {"after": [True, None, "kobo-001", str(S), F, FR]},  # bool is not a group_rank
    {"after": [0, None, "kobo-001", str(S), F, FR]},  # rank out of range
    {"after": [6, None, "kobo-001", str(S), F, FR]},
    {"after": ["2", None, "kobo-001", str(S), F, FR]},  # rank as a string
    {"after": [2.0, None, "kobo-001", str(S), F, FR]},  # rank as a float
    {"after": [2, "2026-10-06T04:00:00Z", "kobo-001", str(S), F, FR]},  # non-canonical instant
    {"after": [2, None, "", str(S), F, FR]},  # empty site_code_key
    {"after": [2, None, "kobo-001", "not-a-uuid", F, FR]},
    {"after": [2, None, "kobo-001", str(S), "finding-1", FR]},
    {"after": [2, None, "kobo-001", str(S), F, 7]},
    {"known_at": "2026-10-08T00:00:00Z"},  # non-canonical cutoff
    {"authorized_site_ids": [7]},
])
def test_malformed_portfolio_cursor_is_422_invalid_cursor(changes) -> None:
    cursor = _mutated(MARK, changes)
    _refused("INVALID_CURSOR", decode_portfolio_cursor, cursor, KEY)
    _refused("INVALID_CURSOR", _scope, cursor)  # parser envelope, then MAC and shape in the snapshot: never a 500


def test_portfolio_and_other_kinds_do_not_cross() -> None:
    cursor = _page_two(MARK)[1]
    for other in ("findings", "actions", "evidence", "financials", "scope"):
        _refused("INVALID_CURSOR", decode_cursor, other, cursor)
    at = datetime(2026, 10, 6, 10, tzinfo=timezone.utc)
    for kind, extra in (("findings", [("lens", "all"), ("state", "all")]), ("actions", [])):
        req = parse_request(kind, WIN + extra)
        scope = EstateIndexService._scope(Snap(SITES), T, req, lambda code: True)
        other_cursor = EstateIndexService._cursor(T, req, scope, "t", at, "r")
        _refused("INVALID_CURSOR", decode_portfolio_cursor, other_cursor, KEY)
        _refused("INVALID_CURSOR", parse_request, "portfolio", WIN + [("cursor", other_cursor)])


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


def test_portfolio_signed_round_trip_and_tamper() -> None:
    """r1b Q-1b-1: round trip; a missing, malformed or wrong MAC, or any unsigned field change (including the
    `page_one_mode` flip), is 422 INVALID_CURSOR before any payload field is used."""
    token, cursor = _page_two(MARK)
    payload = _payload(cursor)
    mac = payload.pop("mac")
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    assert mac == hmac.new(KEY, body, hashlib.sha256).hexdigest()
    assert decode_portfolio_cursor(cursor, KEY) == payload
    req, scope = _scope(cursor=cursor)
    assert EstateIndexService._fence(T, req, scope, token) == MARK
    assert KEY_HEX not in json.dumps(_payload(cursor)) and KEY_HEX not in cursor
    tampered = [
        encode_cursor(payload),  # mac missing
        encode_cursor({**payload, "mac": mac.upper()}),  # malformed (uppercase)
        encode_cursor({**payload, "mac": mac[:-1]}),  # malformed (length)
        encode_cursor({**payload, "mac": 7}),
        encode_cursor({**payload, "mac": "0" * 64}),  # wrong
        encode_cursor({**payload, "page_one_mode": "historical", "mac": mac}),  # the flip, unsigned
        encode_cursor({**payload, "known_at": "2026-10-05T00:00:00.000000Z", "mac": mac}),
        encode_cursor({**payload, "after": [None, *payload["after"][1:]], "mac": mac}),
        encode_cursor({**payload, "extra": 1, "mac": mac}),
        encode_portfolio_cursor(payload, b"\x00" * 32),  # signed with another key
        cursor + "A", "%%%",
    ]
    for value in tampered:
        _refused("INVALID_CURSOR", decode_portfolio_cursor, value, KEY)
        _refused("INVALID_CURSOR", _scope, value)
    historical = encode_portfolio_cursor({**payload, "page_one_mode": "historical"}, KEY)  # validly signed flip
    assert _scope(cursor=historical)[1]["page_one_mode"] == "historical"


@pytest.mark.parametrize("value", [None, "", "a5" * 31, "a5" * 32 + "0", "g" + "a" * 63, " " + "a5" * 31 + "a",
                                   "٠" * 64])
def test_portfolio_signing_key_missing_or_malformed(monkeypatch, value) -> None:
    """r1b Q-1b-1: missing or malformed configuration is 503 ESTATE_STORE_UNAVAILABLE on every Portfolio request,
    page one and an empty scope included, before any selection read; the key never appears in the refusal."""
    _, cursor = _page_two(MARK)
    if value is None:
        monkeypatch.delenv(PORTFOLIO_CURSOR_KEY_ENV)
    else:
        monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, value)
    error = _refused("ESTATE_STORE_UNAVAILABLE", portfolio_cursor_key)
    assert error.status == 503 and error.detail == {"code": "ESTATE_STORE_UNAVAILABLE",
                                                    "message": "Estate records could not be read.",
                                                    "rows": None, "total_count": None}

    class Unread(Snap):
        def imported_sites(self, tenant_id, to):  # the selection read must not happen
            raise AssertionError("selection read before the key check")

    for items in (WIN, WIN + [("cursor", cursor)]):
        req = parse_request("portfolio", items)
        _refused("ESTATE_STORE_UNAVAILABLE", EstateIndexService._scope, Unread([]), T, req, lambda code: True)
        _refused("ESTATE_STORE_UNAVAILABLE", EstateIndexService._scope, Unread([]), None, req, lambda code: True)
    # other roots never read the Portfolio key
    for kind, extra in (("findings", [("lens", "all"), ("state", "all")]), ("actions", []), ("evidence", []),
                        ("financials", [])):
        req = parse_request(kind, WIN + extra)
        assert EstateIndexService._scope(Snap(SITES), T, req, lambda code: True)["cursor"] is None


#: sha256 of the W3-01/02 cursor bytes captured before the r1b seam (same inputs); Findings, Actions, Evidence and
#: Financials keep the unsigned `encode_cursor` path with unchanged bytes.
UNCHANGED = {"findings": "9e6d514c6004aebc82508888509cf9ef35c8151c716455a5180d9ef63460c96c",
             "actions": "b57c10640be6aa1e46dd7e27584ea84a891110af90d6982f8b40d6261235acc1",
             "evidence": "8d53b6019c8937bcf49d0996c2b708167d6ec92561ba4f85ccec62ebdec4d287",
             "financials": "0fc2403ee32391f3134255dc2e72bc77f380c709ece408a69d98d6b46d4ec94a"}


@pytest.mark.parametrize("keyed", [True, False])
def test_w301_w302_cursor_bytes_unchanged(monkeypatch, keyed) -> None:
    if not keyed:
        monkeypatch.delenv(PORTFOLIO_CURSOR_KEY_ENV)
    at = datetime(2026, 10, 6, 4, tzinfo=timezone.utc)
    one = [{"site_id": S, "site_code": "SITE-A"}]
    for kind, extra, marker in (("findings", [("lens", "cost"), ("state", "all")], (at, "r1")),
                                ("actions", [], (at, "r1")), ("evidence", [], ("kobo-001", str(S), "cap")),
                                ("financials", [], (at, "kobo-001", str(S), "CAT", "line-1"))):
        req = parse_request(kind, WIN + extra)
        scope = EstateIndexService._scope(Snap(one), T, req, lambda code: True)
        cursor = EstateIndexService._cursor(T, req, scope, "sha256:" + "1" * 64, *marker)
        assert hashlib.sha256(cursor.encode("ascii")).hexdigest() == UNCHANGED[kind], kind
        assert "mac" not in _payload(cursor)
        assert decode_cursor(kind, cursor) == _payload(cursor)
