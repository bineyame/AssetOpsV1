# W5-04 V2a review: EV Site Work Actions tab (pure fixtures)

Independent Reviewer (Claude), 2026-10-24. Branch `task/W5-04b-ev-work-ui` at `9558a035`, diff `a0883773..9558a035`
(17 files, +1345/−189). Read against the build spec V2a card, readiness rulings 1–52 (mainly 14, 17–20, 25, 39, 44–52),
pre-flight 24–34, register rows R03/R04/R74–R80/R104/R108/R111–R113, the v69 `ev-work` mock (`index.html:334–343`), the
handoff, the builder's questions file, and the V1 wire as built (`task/W5-04a-ev-work-backend` `0ef0b17a`,
`work/domain_action_index.py` `_select`/`index`).

## Verdict: ACCEPT

There are no High or Medium findings. There are 4 Low findings, and none of them blocks the slice. Per rulings 39 and
46, merge still waits for V1b's independent review, because no UI unit merges on an unreviewed wire. The Architect
should also answer the items below before merge.

Counts: High 0, Medium 0, Low 4. There are 10 Items for the Architect (the builder's 6 calls, 3 of the handoff's other
calls, and 1 of mine).

## Checks I ran (on 9558a035 unless noted)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` | Clean (no output). |
| Targeted vitest, `--maxWorkers=1 --minWorkers=1`: `evWorkActions`, `coldWorkActions`, `coldWorkCases`, `siteWorkActions`, `w1f4ChangesWorkStructure`, `operatorSiteTabs`, `operatorRouteFrames` | 7 files, **200/200 passed**, 32 s. |
| Targeted vitest: `domainActionVerification`, `siteDetailRoute`, `siteAction` | 3 files, **88/88 passed**. |
| `tools/check-all.ps1` | **All 11 guards passed**, including architecture seams, agent workflow, navigation truthfulness, missing-claim scan and screen ledger. |
| Cold DOM differential (my own scratch test, deleted after the run and never committed) | See "Cold-unchanged" below. Cold `main.outerHTML` was rendered for 13 states at base `a0883773` and at head, then compared after removing `data-domain-work*` attributes and `domain-work-*` class tokens. |
| Non-vacuity spot checks (reverted with `git checkout`, tree clean afterwards) | EV `domainActionLink: true` gave 4 failures across `evWorkActions`, `w1f4ChangesWorkStructure` and `operatorRouteFrames`. The EV branch of `fallbackOf` disabled gave 3 failures in `evWorkActions`. |

I did not run the full vitest suite, the vite build or Postgres, per the dispatch constraint and the other builder's
Postgres run. The implementer's full run (125 files, 2904 passed, 7m10s) is at `f7158a08`. Head `9558a035` adds only
the two `.agent` documents, so that run covers the same product code. Layout evidence is recorded as **not run**, with
its precondition named (V2b captures need the reviewed V1b manifest, rulings 25/39). That is the correct way to record
it. The 1440/390 heights, table scroll and the caps in rulings 25/50 are therefore unverified for `ev-work`.

## Focus 1: mock fidelity (from code and tests)

Against the v69 `SITE_WORK.ev` / `WORK_COLS` / `WORK_EMPTY` / `siteWorkScreen` source (`index.html:334–343`):

- **Breadcrumb, Site header and Work tab.** The h1 is the stored name (R111). The subtitle is always
  `EV charging operations at this site.` (R78, labelled at `SiteFoundationChange.tsx:105–106`).
- **Page-local Window** after the subtabs (R112, labelled in the `DomainWorkWindow` docblock). The labels are
  `From (UTC)` and `To (UTC, exclusive)` (R77; see Architect item 4).
- **Strip.** `Scoped to {shortName} · 1 action|{n} actions` (R79, R111). The EV-only detail and the plain global gap
  replace `Same records…` and `Manage in Actions →` (R04, labelled in `evWorkPresentation.ts`).
- **Notice.** The currentness notice sits between the strip and the panel, blue or amber, with none on CURRENT
  (R80/R104, labelled).
- **Panel.** One `Actions at this site` panel with the six mock columns in mock order. The panel description is
  `Due dates are not yet set` only when every due date is unset (R76). The successful zero uses the exact mock
  `WORK_EMPTY.Actions` copy, with no deviation (pre-flight 27).
- **Row cells.** Action is `ACT-… · title` as **plain text** (R113, labelled at the render site). Source is plain
  `Finding {id8}` with the `Finding version` disclosure (R74/R75, labelled). Then owner or `Not assigned`, due or
  `Not set`, amber `Open`, and the server criterion summary.
- **Fold.** Four rows with `Show all {n} Actions` (R108).
- **Closing notice.** The blue notice has its first sentence only (R03, labelled).

I found **no unlabelled departure**. Every visible difference from the mock maps to a register row that exists on main
with the ruled wording (R77/R78/R112/R113 were checked on base `a0883773`).

## Focus 2: cold-unchanged guarantee

**Result: cold is behaviourally unchanged.** My differential render covered these cold states:

- positive with 160+-character title/owner and HISTORICAL, plus a cursor page and `next_cursor`;
- the same page with `Show all` expanded;
- STALE_SOURCE;
- complete zero;
- 503 refusal;
- network refusal;
- each of the above after a 59-day Window Apply (the validation-error state);
- the cold Incidents and Maintenance tabs.

After the domain-only names were removed, all 13 outputs were **identical to base except one byte-level change**:
boolean cold attributes now render `=""` where they used to render `="true"` (Low-1). The classes, disclosure names
(`cold-work-*`), literals, attribute order, text, hrefs and element structure are unchanged. The cold read keeps its
two-argument `getIndex` call in both `DomainSiteWorkActions` and `useWorkCounts`, and `coldWorkActions` asserts this.

- **CSS.** The rename of `w1f4-changes-work.css` is 1:1 with unchanged specificity. Every renamed rule still reaches
  cold, because cold emits both class sets and the `data-domain-work-refusal-message` attribute. The cold-only notice
  selectors stay for `siteWorkCases.tsx` (V3a). `siteWorkCases.tsx`'s own `cold-work-longtext`/`cold-work-code`
  classes had no unscoped rule in this file. `w1f4-action.css:210` (`.work-cases[data-cold-cases] .cold-work-code`)
  is untouched.
- **Capture tool.** Every selector in `tools/w502-cold-work-evidence.mjs` still matches. These include
  `#cold-work-actions-heading`, `.cold-work-actions .data-table__scroll`, `.cold-work-code`, `[data-cold-work-window*]`
  and `[data-cold-work-refusal-message]`. Its `getAttribute(...)` reads use either valued attributes (state-panel,
  currentness, row, refusal) or `!== null` presence checks, so Low-1 does not affect them.
- **Mini-grid** stays on the W1 `SiteWorkActions` path, which this diff does not touch. Its `useWorkCounts` key is
  unchanged (no domain suffix), its subtab hrefs stay bare, and `siteWorkActions` asserts there is no
  `data-domain-work*` and no EV copy.
- **Existing cold suites.** `coldWorkActions` gained one test, `siteWorkActions` gained assertions only, and no
  existing cold assertion was edited.

## Focus 3: EV index parser against the V1 wire as built

`_select` emits each EV row with these fields, and `evRow()` matches them field for field:

- `action_id`, `action_code`;
- `domain: a["domain"]` (`EV_CHARGING`), string `title`, `owner_label`;
- `due_at` (ISO or null), `raised_at`, `recorded_at`;
- `origin {finding_id, finding_revision_id, label: "Finding {id8}", href: /sites/{code}/findings/{fid}?revision_id={rev} | null}`;
- `state: "OPEN"`, `criterion_summary`;
- `links {action: /sites/{code}/actions/{id}/verification, history: None}`.

`EV_SUMMARY` equals the backend `DomainSpec` summary `A complete witnessed session and no repeat fault`. The envelope
keys match `index()`: `schema_version`, `site_code`, `window{from,to,bounds}`, `known_at`, `status`,
`coverage{state,reason}`, `total_count`, `all_due_dates_unset`, `rows`, `next_cursor`, and a
`selection_token` of the form `sha256:…`. The W1 row on the EV Site matches the W1 branch (`domain: "MINIGRID"`, null
title, W1 state object, W1 links).

`isRow` accepts `EV_CHARGING` with the same constraints as cold: string title, `OPEN`, and `history === null`. Tests
prove that a malformed EV row (null title, W1 state, or a history link) gives the EV malformed-200 sentence rather than
a W1 parse.

**R113 / dead links.** The EV code renders inside `<span data-domain-work-action-plain>`. No anchor is emitted for an
EV row: the `linked = !domain || p.domainActionLink` branch (`SiteWorkActions.tsx:896`) is false for EV. The origin
`href` is never rendered on any row. Tests assert that no anchor contains `/actions/{EV id}` or `revision_id`, and that
the W1 row on the EV Site keeps its W1 link (pre-flight 28). I found no dead link.

## Focus 4: implementer decisions

See "Items for the Architect". Calls 5, 7 and 9 are decided by rulings. Calls 1, 2, 3, 4 and 6 are partly decided,
and the implementer's reading needs confirmation.

## Focus 5: test strength

The 17 EV tests cover the following, asserted on literals rather than snapshots:

- parser acceptance and refusal;
- the ruling 44 sentences, both through the fake client and the real client;
- the strip, columns, plain code, source disclosure and note;
- one/many grammar;
- the successful zero;
- fallbacks;
- mixed W1 rows;
- all four currentness tones with DOM order;
- 403/503 with Retry;
- the fold;
- the R-9 default window with subtab query and count;
- Window Apply and the validation error;
- the EV case-tab subrow.

The new EV blocks in `w1f4ChangesWorkStructure`, `operatorSiteTabs` and `operatorRouteFrames` cover the panel
structure, query preservation and App-level dispatch. The non-vacuity proofs hold: the builder's four mutations and my
two extra ones each fail tests. The gaps are in Low-3.

## Findings

### Low-1: cold boolean `data-cold-work*` attributes changed value from `"true"` to `""`

`frontend/src/sites/SiteWorkActions.tsx:706` (`workAttrs(..., value = "")`) and its uses for `window`,
`window-from/-to/-apply/-error`, `strip`, `global-gap`, `revision`, `owner`, `due`, `criterion`, `pages`, `show-all`,
`first`, `next`, `retry`, `refusal-message` and `empty`.

- **What changed.** The K2 JSX wrote these as bare boolean props, so they rendered `="true"`. They now render `=""`.
- **Why it matters.** The handoff's claim that every K2 `data-cold-work*` attribute is kept is not byte-exact. No
  test, CSS rule or capture selector reads these values: I checked by grep and by the differential render. The
  practical risk is close to nil, but V4a must prove cold output "byte-identical" (ruling 41), and the change is
  better known now.
- **Fix (optional).** Either pass `"true"` as the default value for the cold-only key, or record in the packet that
  presence-only attributes now render empty. This is a preference, not an acceptance gap.

### Low-2: `EV_ACTION_LINK_LIVE` is exported but unused

`frontend/src/sites/evWorkPresentation.ts:42`, and `SiteWorkActions.tsx:692` hard-codes `domainActionLink: false`.

- **What is wrong.** The R113 switch exists in two places, and the labelled constant drives nothing.
- **Why it matters.** V4a could flip one place and miss the other.
- **Fix.** Use `domainActionLink: EV_ACTION_LINK_LIVE` in `EV_WORK_PRESENTATION`, or delete the constant and keep the
  R113 label at line 692.

### Low-3: test gaps on paths the EV surface inherits

The EV path is not exercised for:

- the cursor pager (`Next page` pins `known_at`, and `First page`);
- the 409 `WORK_BASIS_CHANGED` restart with a cursor.

The code is shared with cold and tested there, so this is not an acceptance gap. Two other things are also missing:

- No test pins the builder's Q1 interim, that an EV Incidents/Maintenance tab has exactly one window form (the W4 form)
  and no `data-domain-work-window`. `evWorkActions.test.tsx:421` asserts only the subrow and subtitle.
- The card lists `frontend/src/shell/__tests__/siteDetailRoute.test.tsx`, but it was not touched. Its 88-test group
  passed unchanged.

**Fix.** Add an EV pager case and a single-form assertion on the EV case tab. Alternatively, the Architect can confirm
that `siteDetailRoute` needs no EV vector.

### Low-4: R77 wording and implementation agree only for an `Etc/UTC` Site

`frontend/src/sites/SiteWorkActions.tsx:739–740`, register R77 at `.agent/mock-departure-register.md:132`.

- **What is wrong.** R77 says "Selected Site-zone abbreviation inside the page-local Work `Window` control". The code
  shows ruling 14's fixed `From (UTC)` and `To (UTC, exclusive)` and never reads `site.timezone`. For EV-LAB-001
  (`Etc/UTC`) the two coincide.
- **Why it matters.** For a future non-UTC EV Site, the label would be accurate about the window, which is UTC by
  contract, but would not satisfy R77's text.
- **Fix.** The Architect should pick one wording; see item 4. The departure is labelled, so this is not a High.

## Items for the Architect

1. **Builder Q1: EV case tabs get only the subrow in V2a.** This is partly decided. Ruling 45 lists "Window, …
   `SiteWorkCasesFrame` dispatch" under V2a. Ruling 14 says V3a sets `windowForm=false` and that there must never be a
   duplicate W4 form. Mounting the Window in V2a without `windowForm=false` would break ruling 14.
   - **Recommendation:** confirm the builder's interim. V3a lands the Window and `windowForm=false` together. Ask V3a,
     or a small V2a fix, to add the single-form assertion from Low-3.
2. **Builder Q2: `SiteFoundationChange.tsx` is outside the card's file list.** Ruling 20 and R78 require the subtitle,
   and `ChangesWorkPageHeader` is the only place it can render, as cold R90 already does.
   - **Recommendation:** accept, and add the file to V2a's list retroactively. Applying it to all three EV Work screens
     follows ruling 20's "always".
3. **Builder Q3: the R75 "unavailable exact-revision control" in the list cell.** This is partly decided. Pre-flight 24
   and R75 name a "control", while the builder renders the K4 sentence, with no muted control, inside the disclosure.
   The closed state matches the mock.
   - **Recommendation:** accept the sentence-in-disclosure as the list-cell form of R75 and amend R75's wording to
     match. A muted `Open source Finding →` in a table cell would add a pseudo-link the mock does not have.
4. **Builder Q4: R77 zone display.** Ruling 14 fixes the labels as `(UTC)` and calls the Site zone "where relevant".
   Pre-flight 29 says "format in stored Site zone". The two conflict only for a non-UTC Site.
   - **Recommendation:** keep the UTC labels, because the `[from,to)` window is a UTC contract and a Site-zone
     abbreviation beside UTC dates would mislead. Amend R77 to read "UTC labels; the `Etc/UTC` fixture zone equals
     UTC; a non-UTC Site zone display is deferred". See Low-4.
5. **Builder Q5: captures deferred to V2b.** Decided by rulings 25 and 39, which give V2b the capture scripts and the
   producer manifest. They supersede the V2a card's listing of `tools/w504-ev-work-evidence.mjs`.
   - **Recommendation:** no action beyond removing that tool from the V2a card text.
6. **Builder Q6: CSS rename to `domain-work-*` with dual class sets on cold.** Partly decided. Ruling 45 governs
   attributes and component names but says nothing about class names. Pre-flight 31 puts the CSS in V2a. Cold layout
   and capture selectors are preserved, as verified above.
   - **Recommendation:** accept. Note that the V4a/K2 regression baseline now includes both class sets on cold.
7. **Handoff call 7: `coldWorkQuery` and `ColdWorkQueryScope` kept as aliases.** Decided by pre-flight 30 ("No second
   route grammar").
   - **Recommendation:** accept.
8. **Handoff call 8: optional third `siteType` argument on `getIndex`.** Ruling 44 decides the copy, and the mechanism
   is an implementation choice. It keeps the cold two-argument call byte-for-byte, and a test proves this.
   - **Recommendation:** accept. V4a should reuse the same selector for `getDetail`.
9. **Handoff call 9: no register edits.** Decided by ruling 48. R77, R78, R112 and R113 already carry the ruled
   wording on base `a0883773`.
   - **Recommendation:** none, apart from the R75 and R77 wording in items 3 and 4.
10. **Reviewer: the ruling 17 selector.** Ruling 17 says each leading entry points to
    `[data-domain-action-currentness]` or "the actual case notice selector". For the Actions list, the actual notice
    selector is `[data-domain-work-currentness]` (`frontend/src/test/panelStructure.ts:75`), parallel to cold's
    `[data-cold-work-currentness]`.
    - **Recommendation:** confirm `[data-domain-work-currentness]` as the correct `ev-work` entry. The
      `data-domain-action-*` literal applies to `ev-action` (V4a).

## Residual risk not named in the packet

- **Unverified layout.** No browser has rendered the EV surface, and the renamed CSS has only been proven for cold in
  jsdom. A cascade regression would surface only in V2b and K2 recaptures. The cold class sets are unchanged, so the
  risk is small. Still, the first cold recapture after merge should be treated as a check of this rename.
- **No producer-backed claim.** The fixtures equal the V1 wire as of `0ef0b17a`. If V1b's review changes the index
  row shape, `evWorkFixtures.ts` must change with it before merge (ruling 39).
