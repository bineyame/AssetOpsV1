"""CH-5a1 L1 (CH5a1-R2 ledger): the outcome summary reads each (read, key) at most once (A0 "max 1 per key").

Before CH5a1-R2 the summary ledger read 3: `objectives` was keyed `()` on each of the 3 Sites, and Kobo's
`productive_readings` ran twice with the same arguments on the first day of a month (the board day and the
month-to-date window coincide). `objectives` is now keyed by Site and `productive_readings` is memoised (R1).
"""

from __future__ import annotations

from dataclasses import replace

import test_ch5a1_board_contract as BC
from assetops_backend import read_scope
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService

#: [31 Oct 21Z, 1 Nov 21Z): Kobo's summary day is local 1 Nov, the first day of its month.
LO, HI = BC.at(31, 21), BC.at(1, 21, month=11)


def _summary():
    port, never, executed = BC.Port(), [], []
    services = BC.services(port, never)
    base = type(services.mini_depth)

    class Depth(base):
        def productive_users(self, **kw):
            return [{"asset_id": "u1", "name": "Mill"}]

        def productive_readings(self, **kw):
            executed.append((kw["lo"], kw["hi"]))
            return []

    services = replace(services, mini_depth=Depth())
    with read_scope.scope("test:summary") as sc:
        body = SiteOutcomeBoardService(services).summary([BC.KOBO, BC.COLD, BC.EV], LO, HI, known_at=BC.KNOWN)
    return body, sc, executed


def test_summary_reads_each_key_at_most_once():
    body, sc, executed = _summary()
    assert [s["read_state"] for s in body["sites"]].count("UNAVAILABLE") == 0, body["sites"]
    assert sc.max_per_key() == 1, sc.repeated()
    objectives = sorted(k for (name, k) in sc.ledger if name == "objectives")
    assert objectives == sorted([(BC.KOBO.site_code,), (BC.COLD.site_code,), (BC.EV.site_code,)]), objectives
    # the month-to-date window equals the board day on 1 Nov: one executed read, the second a memo hit
    assert len(executed) == 1 and len(set(executed)) == 1, executed
    assert [k for (name, k) in sc.ledger if name == "productive_readings"] and sc.hits.get("productive_readings") == 1
