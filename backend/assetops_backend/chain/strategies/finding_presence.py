"""`finding_presence@1`: the status signals of a Finding source, as the `Signal` inputs `board.py:570-578` builds.
It computes no state: `outcome_state` stays in `outcomes/status.py`."""
from __future__ import annotations

from assetops_backend.chain.strategies.base import RECORDED, ContributionContext, Effect


class FindingPresence:
    key, version = "finding_presence", 1

    def effect(self, ctx: ContributionContext) -> Effect:
        sigs = tuple(ctx.signals)
        return Effect(ctx.record.direction, basis=RECORDED, title=ctx.title,
                      inputs={"open": any(s.open for s in sigs), "primary": any(s.primary for s in sigs),
                              "applied": any(s.applied for s in sigs), "signals": sigs})
