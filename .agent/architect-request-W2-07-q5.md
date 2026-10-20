# Architect request: W2-07 commit 3 readings and the commits 4–5 UI closure (q5)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`;
- `.agent/W2-07-build-spec.md`, everything through q4;
- the "Run 6" note in `.agent/W2-07-phase-handoff.md` on branch `task/W2-07-ev-site-evidence-money` at `df6b2045`;
- the commit 3 code: `ev_site_api.py` and `ev_site_reads.py`.

## Commit 3 readings

The builder made the readings below. Each one is a defect. Confirm or replace each with literal values, a formula or a table, and name the test.

1. The service window is returned as null.
2. Source contact is always UNKNOWN, because no source diagnostic is wired.
3. Claim coverage seconds are a heuristic built from session spans and Site-import intervals. A heuristic is not acceptable: give the exact definition, or the honest-missing value.
4. The closure's "no Site import" example contradicts the replay, which has a 60 kW peak and 223 accepted Analysis records. Correct the example, or the expectation.
5. Some returned fields are not named in the spec: consequence history and the tariff publication note. Ratify the exact key list per route, or remove the extra fields.

## Commits 4–5 dry-read

Then do a final implementer dry-read of commits 4–5 (the five UI routes) against the commit 3 wire as built. Cover:
- the exact UI paths `/sites/{code}/ev/...`, with `from`/`to`/`known_at`;
- the panel order checked by `expectV69Panels`;
- the measured heights;
- the ≤1.3x budget at 1440 and 390;
- every string and the source field it comes from;
- the tab-inventory multiset;
- the r10 N3 `SOURCE_UNVERIFIED` sentence placement.

If nothing else is open, say so in one line.

## Output

Append to `.agent/W2-07-build-spec.md` as "Run 6 rulings (q5)". Write nothing else. Do not commit.
