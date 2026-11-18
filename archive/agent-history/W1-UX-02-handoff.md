# W1-UX-02 handoff - Site, Finding and money screens on the shared layer

Branch `task/W1-UX-02` (base main `a8cbb3d1`), final code revision `bc1cea1b`, status `in_review`. Packet `.agent/W1-UX-02-review-packet.md`. Built state `.ai/CODE_STATE.md` "W1-UX-02". Not merged.

## What landed
- Eight routes migrated and opted into the W1 set: `sites`, `mini` (rest of it), `sitefindings`, `finding` (Overview+Analysis), `finding-evidence`, `finding-history`, `financials`, `assumptions`. Each route has a `HeadlineVisualCard` lead, a `ProductStatus` state line, a visual, a destination and a closed `ExactReferences`. Anchors are in the packet table.
- Card names (`data-headline-card`): `sites-directory`, `overview-objective`, `site-findings`, `finding`, `finding-evidence`, `finding-history`, `financials-consequence`, `assumptions-price`.
- Duplicate word maps replaced: `FRESHNESS_WORDS` removed; `MONEY_STATE_WORDS` uses `moneyWords`; `findingCurrentnessWords` (`findingWords.ts:114`); `SiteFindingIndex` `STATUS_WORDS` wraps `currentnessWords`; `consequenceWords` replaces `STATE_HEADLINE`.
- Evidence tool `tools/w1-ux-02-evidence.mjs` (a sibling of w1-ux-01). It checks that the 390 layout width is within 370..390, accepts untimed state lines as recorded, counts a price strip as the visual, and records states with no disclosure.
- No shared-file edits (`ui/*`, `test/*`, vocabulary, primitives.css untouched). CSS is in `frontend/src/sites/w1ux02-*.css`.

## For later slices and the combined walkthrough
- Capture recipe and DB names: packet "Checks". The combined walkthrough also needs `var/sites/kobo-001.yaml` for `s4_finding_cases.py run`, and a fresh `assetops_s402bcases` template (`tools/s402b_power_cases.py run`) before s402b prepare.
- `LINK_DISPLAY_OVERRIDES` (`SiteFindingEvidence.tsx`) rewords backend "fingerprint" link words on screen only. A backend slice should reword `finding_read.BROKEN_WORDS` and retire it.
- Candidates for shared `readResultWords` kinds: the index refusals (closed, continuity, list changed, invalid, unauthenticated). A shared "time not recorded" variant of `expectStateLineVisible` would replace the local helpers in `siteFinancials.test.tsx` and the explicit checks elsewhere.
- `tools/s502-overview-finding-list-evidence.mjs:148` still reads the removed `[data-finding-index-token]`.

## Open risks
- Untimed reads show "As of: time not recorded": the directory, the lists, refusals, the Financials non-positive states, and the s402b priced case.
- The Financials readings table is in a closed `Disclosure`; there is no Financials Analysis tab.
- The Overview and Financials pages stay long below the new lead.
