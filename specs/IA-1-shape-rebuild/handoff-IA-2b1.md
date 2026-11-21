# IA-2b1 handoff (units 1 to 3 done; unit 4 next), 2026-11-21

Status: units 1 to 3 are built and committed (unit 3 at `8b0543c7e`). Nothing is live. With IA-2b1 not landed, every touched gate is green or dormant.
Branch `task/IA-2b1-lists`, worktree `/opt/assetecon/AssetOpsV1-ia2b1`. Main 757aba13d is merged in at unit 3 (doc conflicts kept both sides: the IA rulings index moved to `index-rulings-23.md`, the owner-away IA-2b row renumbered 57).
Mid-build questions: `mid-build-questions.md` § IA-2b1, Q1 to Q4, each built on its default (Q1 waits for the Architect at review).

## Done
- **Unit 1 (the checks, all dormant until IA-2b1 is landed or forced with `IA_FORCE_LANDED=IA-2b1`).**
  - `tools/list_shape_check.cjs`: blocks A, B, C and D. B is written (spec §8 row 2, D-IA.69/70/73). Forced now, it runs 136 views over
    10 scenario boots. Its own store reads give the live sizes of spec §1 (Decisions 8/3/4, Findings 9/4/7, Actions 6/3/2, Sites 3/3/3),
    every store item has a live target, and its word tables match the product, except `IA_DEC_STATE_WORD`, which does not exist yet
    (unit 3/4). `LIST_VERBOSE=1` prints every failure.
  - The B plants are in `plantSource`: `tile` (SRC rule), and `rowctl`, `restore`, `own`, `stakesort` and `notarget` (window plants).
  - `shape_check`:
    - item 7 reads alias values with its own split (plant `aliasq`);
    - item 12 expects the "Decisions" crumb to be a link to `#/decisions` once IA-2b1 is landed (plant `deccrumb`, decision-hosted);
    - item 15 checks that no list view links its own address;
    - item 10's row selector also reads `table.ia-list tbody tr[data-row]` (the Outcomes fold).
  - `click_depth_check`: each list is at 1 via the rail (`nav.rail a[href="#/<list>"]`, landed, labelled with the list's name). Plant
    `listrail`.
  - `copy_check`: a new IA-2b1 block (spec §7, `LIST_COPY`). It reads the list section outside the row cells. Plant `COPY_PLANT=list`.
- **Unit 2 (`qty_check`):** the count mode (`data-qty-kind="count"`), the format mode (one number of decimals per screen and key; keys
  with a QTY-table member are printed as deferred to IA-2e), `EQUAL` `[['sites:gap:', 'overview-gap']]`, and the five DOM plants. Each plant
  exits 2 if it finds nothing.

- **Unit 3 (the component, `8b0543c7e`; not live).** Evidence: `/opt/assetecon/evidence/IA-2b1/unit3/`.
  - `ia-shapes.js`: `IA_LIST_CAP` (10), `IA_LIST_DEFS` (empty: unit 4 fills it), `iaInScope`, `iaListTier`, `iaListText`,
    `iaListModel`, `iaListHref`, `iaListQk`, `iaQty`, `iaListCents`, `iaListTiles`, `iaListChips`, `iaListTools`, `iaListBody`,
    `shapeList`, all top-level `function`s; every `SRC` rule string of `list_shape_check` is present verbatim (plants found them).
    `iaScopeEntries` has the list branch (`route && route.shape === 'list'`).
  - `ia-routes.js`: `let IA_LIST_KEEP`; `iaAliasTarget` (the one splitter), `iaLiveAlias` returns the path, `iaCanon` writes the value's
    query then the href's own (through `iaListHref` for a list target; an alias without a query keeps the href's query byte for byte);
    the tools listener (`iaListWrite`, change on a select, submit prevented) and `iaListRestore`, registered last (after `iaTabSwitch`).
    The four list aliases are added now (dormant: their targets are unlanded), so `aliasq` could be proved.
  - `loop-core.js` `resolveScreen`: a live alias's replaced hash goes through `iaCanon` (so `findings-cost` lands on `findings?heading=optimize`).
  - `ia.css`: the list block (levels `display: contents`, tools and chips wrap, stretched row link, row focus ring, group heads).
  - Checks fixed: `list_shape_check` A's keep items were inside the sort's top 10, so `keep` passed A; now i21/i24, and `keep` also
    bites D. `shape_check` item 7 failed unplanted under force on legitimate aliases (`evidence/records`, other operators' Site
    tabs, `cold`/`ev` with no Site); its reserved-path rule now binds values with a query, and a null function value must give null.

## The def contract (unit 4 writes the four defs into `IA_LIST_DEFS`)
`{ key, title, plural, cols, items(op), site(it), text(it)?, keep?, group?, groupWord?, facets, sorts, row(it, ctx, qk), tiles?(m, ctx, qk), more?(m, ctx, qk), moreInline?, none }`
- `cols`: column words, the first is the title column; `row` returns `{ key, href (no '#/'), title, small, cells }`, cells in `cols[1..]`
  order, text only. `text` defaults to the row's own text (`iaListRowText`, called with `ctx` null and `qk` ''), so a row must render without ctx.
- `facets[i]`: `{ key, label, all, options() -> [[value, word]], of(it) }`. `options()` takes **no argument** (the `invalid` rule
  string), so it reads `LS.op` itself. Values compare as strings.
- `sorts`: an array of `{ key, word, cmp }` (stakesort pushes onto it); the first is the default.
- `tiles` returns the tiles after tile 1 (component: tile 1 = `def.title`, `{key}:n:{qk}`, total, count, from `m.n`); use `iaQty`.
- `more`: decisions return `iaCapMore(m.hidden ids)` (a block before "Show all"); Sites set `moreInline: true` and return
  `Not shown: {h} Sites, gap to target <span data-qty="sites:gap:{qk}" data-qty-role="part">…</span>.` (the `remainder` plant sets `more` to `() => ''`).
- `iaListCents(shownValues, hiddenValues)` says whether the Sites gap key takes cents (§3.4).
- The model returns `{ rows, shown, hidden, n, ns, tier, groups, sort, inScope }`. Routes: `{ id: key, shape: 'list', … render: ctx => shapeList(ctx, key) }`;
  `iaCanon` finds the def by the route id.

## Next: unit 4
- (a) the four defs and routes (`unit: 'IA-2b1'`), `iaDecStateKey` with `IA_DEC_STATE_WORD`, `iaActionStateKey`, `iaFindingSite`,
  `iaOutcomeRows`' text fields, the Outcomes fold (`iaListBody('sites', ctx, { tools: false })`) with `outcomes_table_check` retargeted,
  the crumbs (decision "Decisions", Site hub "Sites"), the search index, the rail units renamed. The aliases are already in.
- (b) the flip, `walkthroughs.md`, register rows, shots S1 to S9, `packet-IA-2b1.md`, spec `Status: in_review`.
- Unit 3 seams unit 4 must keep: markup B reads (spec §3.2) is drawn by the component; B's sort literals and word tables are the defs'.
- Note: `loop-ux.js` links `portfolio/act-first` ("Act first ›", "View all n in Act first"); with `decisions` landed they become live
  links to `#/decisions` through the alias. Check the hubs' copy at the flip (2b2 replaces the queue's "View all").

## Proofs (unit 3) and what is still owed
- Proved under `IA_FORCE_LANDED=IA-2b1`, each by a failure line that only the plant produces (the unplanted forced run has no A failure
  and no item 7 failure): `LIST_PLANT` cap, keep, scope, search, sort, invalid, group, canon, tier (block A); `SHAPE_PLANT=aliasq`
  (item 7: `iaAliasTarget("findings-cost") is { path: "findings?heading=optimize", query: "" }`).
- `qty_check` count and format modes, each shown failing on a real violation of IA-2a's live plan markup, then reverted (the released
  clause marked as a count: "holds 0 numbers" and "mixes count and money"; one key written with 0 and 2 decimals).
- **Owed by unit 4 (need the list routes):** `tile`, `rowctl`, `restore`, `own`, `stakesort`, `notarget`, `scopemenu`, `remainder`
  (today `rowctl`, `own`, `stakesort` exit 2; the others exit 1 only on the unplanted forced failures: no list section), `deccrumb`
  (the crumb is still text), `listrail`, `COPY_PLANT=list`, the five qty list plants; item 15 and the copy and qty list blocks failing
  on a real violation. Compare each plant's failures against the unplanted forced run, never the exit code alone.

## Risks
- `copy_check` needs `tools/rendered-text.json`, which is ignored by git. Run `node tools/render_text.cjs` first.
- The forced `list_shape_check` takes about 30 s with no lists, longer once B renders them (24+ boots, 12 fresh-boot comparisons).
- `shape_check` prints at most 12 failures; to see a plant's own lines under force, widen the slice for the run and put it back.
- The worktree has no `.venv`: run `tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`.
