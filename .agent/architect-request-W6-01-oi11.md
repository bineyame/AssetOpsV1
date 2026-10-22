# Architect request: W6-01 OI-11

You are the AssetOps Architect. `.agent/W6-01-closure-check-2.md` confirms OI-1 to OI-10 are closed. It found one new item, OI-11: the replacement Site Work strip links "Manage in Incidents" and "Manage in Maintenance" have no literal href or helper. A2 must also keep the shared `WORK_MANAGE_UNAVAILABLE_STATUS` and its exemption until B2 removes them.

In `.agent/W6-01-build-spec.md`, give:
- the literal hrefs, with query parameters such as site, window and known_at, or the helper name and signature;
- the A2 and B2 file lists and steps for the shared status and its exemption;
- the fixes for the example-versus-offset time mismatches the check notes.

Add rows to the closure table and an amendment line to `D-2026-10-22-w6-01-buildspec`. Write nothing else. Do not commit.
