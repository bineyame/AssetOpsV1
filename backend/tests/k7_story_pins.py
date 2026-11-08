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

#: (db_now ISO, sha256 of the resolved story text, its length in characters, S)
THREE_SITE_STORY_PINS = (
    ("2026-11-08T10:00:00Z", "06a08d50ff94f5efb5a2c2ade11874fca9169cc6bef55b006a6caafa63f81a87", 44906,
     "2026-11-06T00:00:00Z"),
    ("2026-12-03T23:30:00Z", "9631fc7fcce4f7049c1b702e49502f624b54d4cea5e50122afc5b966cb25c3bd", 44904,
     "2026-12-01T00:00:00Z"),
)
