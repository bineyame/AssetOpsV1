# W5-04 V2a — interpretation notes for Architect confirmation

Builder, 2026-10-24, branch `task/W5-04b-ev-work-ui`. None of these block V2a: no ruling contradicted merged code. Each
is a reading of two rulings, or of a ruling against the card's file list, that I had to apply. Every one is reversible
in V2b/V3a. Please confirm or correct before V2a merges.

1. **EV case tabs in V2a: subrow dispatch only.** Ruling 45 says V2a covers "Window, `WorkSubrow`, `useWorkCounts` and
   `SiteWorkCasesFrame` dispatch". Ruling 14 says V2a owns the EV Window, V3a sets `windowForm=false`, and there must be
   no duplicate W4 case form. If V2a mounted the Window on EV Incidents/Maintenance while `windowForm` stayed true, those
   tabs would show two window forms until V3a merges. I did this:
   - `SiteWorkCasesFrame` gives an EV Site the domain subrow: the Actions count comes from the union index, with
     `known_at` and `from,to,known_at` subtab hrefs.
   - The EV case tabs keep the W4 form and get no Window. The Window and `windowForm=false` both land in V3a.

   If you want the Window, and therefore `windowForm=false`, on EV case tabs in V2a, it is a two-line change in
   `SiteAnalyticsFrames.tsx` (`legacyCold` already parameterises `DomainWorkWindow`).
2. **`SiteFoundationChange.tsx` is outside the V2a card's file list.** Ruling 20 (R78) requires
   `EV charging operations at this site.`. That subtitle comes from `ChangesWorkPageHeader`, which is where cold R90
   lives. I added the EV branch there. It applies to all three EV Work screens, not `changes`, mirroring cold.
3. **R75's "unavailable exact-revision control" in the list cell.** The cold K2 list cell has no such control. The only
   precedent is the K4 detail's muted `Open source Finding →` with
   `The selected Finding revision cannot be opened here yet.`. In the EV Source cell I put that existing sentence inside
   the `Finding version` disclosure, beside the revision ID. The closed state matches the mock: plain `Finding {id8}`
   plus the disclosure summary.
4. **R77 zone display.** The Window labels are ruling 14's exact `From (UTC)` and `To (UTC, exclusive)`. The window is
   UTC `[from,to)` by contract, and the fixture zone is `Etc/UTC`, so the zone shown equals UTC. I added no separate
   Site-zone indicator. R77 says "Selected Site-zone abbreviation inside the page-local Work Window control". If a
   non-UTC EV Site must show its own zone abbreviation, please name the literal and placement.
5. **Captures deferred to V2b.** The spec gives captures to V2b/V3b/V4b and producer manifests to reviewed V1b. I did
   not create `tools/w504-ev-work-evidence.mjs` and took no browser capture. Layout evidence for `ev-work` is not run in
   V2a.
6. **CSS naming.** `w1f4-changes-work.css` selectors moved from `.cold-work-*` to `.domain-work-*`. Cold elements now
   carry both class sets, so the cold layout and `tools/w502-cold-work-evidence.mjs` selectors are unchanged. The cold
   notice selectors are kept beside the domain ones because `siteWorkCases.tsx` (V3a) still emits
   `data-cold-work-currentness`/`-notice`.
