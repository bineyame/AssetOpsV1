# Architect request: W2-07 review findings (r1)

You are the AssetOps Architect. Read `.ai/ROLE_CONFIG.md` ("Mockup drives the design; implementers never decide", "Token Efficiency"), `.agent/W2-07-build-spec.md` (all rulings through q6), `.agent/W2-07-review.md`, and the v69 EV mock screens. Code is on branch `task/W2-07-ev-site-evidence-money` (`git show task/W2-07-ev-site-evidence-money:<path>`).

Give exact replacements (literal copy tables, predicates, test names and assertions) so a Sonnet fixer decides nothing:
1. M3: the full mapping from every capability/state code that the Analysis table can render (`ev_site_reads.py` ~650) to plain mock words. Enumerate every code that is reachable.
2. M4: the exact later-publication sentence, where it renders in Financials details, the fixture that makes it non-null, and the test assertion.
3. M2: confirm half-even in `money2` and give a discriminating test value.
4. M1: confirm the reseed with `golden_tariff`, the replay window, and that the tariff row renders plain copy instead of `AUTHORED_ESTIMATE` (give the string).
5. L1: the copy for a null consequence. L2: the chip aggregate versus the strip count of 4. L3: the next-evidence rank order including request/limit. L4: the ordering of abort versus fault at the same instant. L5: whether the downgrade test may delete rows.

Append as "Review r1 rulings" to `.agent/W2-07-build-spec.md`, amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
