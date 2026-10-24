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

## Q2 - `ev-action` ledger `data_owner` / `supported_claim` literals (V4b; blocks nothing)

- **Ruling text.** Build spec "EV producer, UI and registry": "Set `coverage:'partial'`, `task:'W5-04'`,
  `follow_on:null`, and the named data_owner/supported_claim below." No `data_owner`/`supported_claim` literal follows
  in the spec, the pre-flight (43) or readiness (21) rulings.
- **Built (pending ruling).** `data_owner: "W5 domain Action intent read"` (the merged cold-action row's literal for
  the same `domain-action-intent-read-1` read) and `supported_claim` = the spec's own EV panel-contract `claim_limit`
  (`Stored EV work and declared intent only; no completed-session, no-recurrence or availability pass is inferred.`).
  The panel-contract row uses the spec's literal row exactly. Ledger and registry checkers pass.
- **Ask.** Confirm these two strings or name the literals; V3b's three EV Work rows face the same gap.
