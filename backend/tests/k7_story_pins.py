"""DIESEL-1 K7 (ruling DIESEL-1-R3l §9l.3, L0 test 1): byte-equal pins of the three-Site story.

Taken on the unedited tree (main `78a224393`, the R3l ruling commit) and committed as the branch's first commit,
before any edit to `tools/demo_combined.py`, so git history shows they predate K7 (the K0 precedent).

Recipe: `tools/demo_combined.py` `resolve_story(db_now)` with its default story file and default day list, for each
`db_now` below; the pin is the sha256 (and length) of `json.dumps(story, indent=2)` encoded as UTF-8, the same
serialisation `prepare` writes to `<work>/story.json` (before it pops `days` and adds `code` and `sites`).
`backend/tests/test_k7_kisiwa_story.py` asserts that a K7 tree with Kisiwa off (`kisiwa=False`) still produces these
bytes (stop S-9).
"""

from __future__ import annotations

#: (db_now ISO, sha256 of the resolved story text, its length in characters, S) on the v3 day list
#: (`demo-story-days-v3.json`, the default until FX-KOBO-GAPS). Unchanged: they are now asserted with the v3 list.
THREE_SITE_STORY_PINS_V3 = (
    ("2026-11-08T10:00:00Z", "06a08d50ff94f5efb5a2c2ade11874fca9169cc6bef55b006a6caafa63f81a87", 44906,
     "2026-11-06T00:00:00Z"),
    ("2026-12-03T23:30:00Z", "9631fc7fcce4f7049c1b702e49502f624b54d4cea5e50122afc5b966cb25c3bd", 44904,
     "2026-12-01T00:00:00Z"),
)
#: FX-KOBO-GAPS (D-E5.12, D-E5.17): the same recipe on the default v4 day list as amended (S-27..S-22 filled),
#: taken on the FX-KOBO-GAPS tree whose v3 result still equals the pins above byte for byte (so only the day list
#: moved them). Superseded v4 (D-E5.12 only) pins: 91ea68a9... / 50821 and 9fe1af48... / 50819.
THREE_SITE_STORY_PINS = (
    ("2026-11-08T10:00:00Z", "1d50fb8fe637ba2a6d739a916bba8622524811440e2f47acd511257a1fbf97ba", 65083,
     "2026-11-06T00:00:00Z"),
    ("2026-12-03T23:30:00Z", "1bfc759279bc94a37fb7d9832c4be4014fdbcb285cca34733de2223c6986640f", 65081,
     "2026-12-01T00:00:00Z"),
)
