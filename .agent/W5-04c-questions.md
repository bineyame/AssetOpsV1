# W5-04c questions (V4a/V4b/V5 build, 2026-10-24)

Builder: W5-04c on `task/W5-04c-ev-action`. One open item; everything else is built to the rulings.

## Q1 - does the live EV Work link itself carry `from,to,known_at`? (blocks nothing; one-line change either way)

- **Ruling text.** Readiness 46: "V4a then makes the selected `links.action` href live, preserving `from,to,known_at`".
  Ruling 14 and the V4a card: "`ev-action` keeps query selection", "Preserve selected from,to,known_at query on
  Action detail".
- **Merged code.** `SiteWorkActions.tsx:908` renders `<Link to={row.links.action}>`; the server href
  (`domain_action_index.py:477`) is the bare `/sites/{code}/actions/{id}/verification` with no query. The cold row
  uses the same bare href, so a cold historical list opens the current detail. `SiteWorkActions.tsx` is not in the V4a
  file list (V2a/V2b own it).
- **Built (pending ruling).** `EV_ACTION_LINK_LIVE = true` (the single switch, build spec Low-2) makes the EV code a
  live link to the server's bare `links.action`, exactly as cold. On the detail, every link the page owns keeps the
  selected `from,to,known_at`: the Verification tab, and the redirect from a bare/legacy address
  (`domainVerificationHref` in `SiteAnalyticsFrames.tsx`). Cold keeps K4's `known_at`-only address (byte-identical).
- **Options.**
  - (a) Keep as built: the list link is the server href; the detail preserves whatever query it is opened with.
  - (b) Append the Work page's selected `from,to,known_at` to the EV link only. Needs `SiteWorkActions.tsx` added to
    V4a's files (about 4 lines through `DomainWorkPresentation`), and makes EV differ from cold.
  - (c) As (b) for both domains. Changes cold output, which rulings 41/53 forbid without a new ruling.
- **Mock.** `ACT-061` in `SITE_WORK.ev` links to `ev-action` (`index.html:337`); the mock has no query state.
