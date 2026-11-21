# 0K3 mid-build questions

Implementer (Claude), 2026-11-21. Each has a proposed default; nothing else was stopped.

## Q1 Kobo's zone is `Africa/Addis_Ababa`, not `Africa/Nairobi` (pre-flight (c))

- **Found.** `find_site_by_id(...).timezone` of DS3's converted Kobo is `Africa/Addis_Ababa` (spec §0 (c) and D-0K3.12
  expected `Africa/Nairobi`). MG-W402-001 is `Africa/Nairobi` as expected.
- **Effect.** None on any outcome: both zones are UTC+3 with no clock change, so the window of local 2026-10-06 is
  2026-10-05T21:00Z to 2026-10-06T21:00Z either way, and G4b's subject
  `feeder_demand:load-clinic@2026-10-06T00:00:00.000000Z` is unchanged.
- **Default applied.** G4b reads the Site's own zone and asserts it is `Africa/Addis_Ababa`; the reader always takes the
  zone from the Site. Architect to confirm the spec's expectation was a slip.
