# IA-2b1 handoff (units 1 and 2 done; units 3 and 4 next), 2026-11-21

Status: units 1 and 2 are built and committed. Nothing is live. With IA-2b1 not landed, every touched gate is green or dormant.
Branch `task/IA-2b1-lists`, worktree `/opt/assetecon/AssetOpsV1-ia2b1`. Main d615685d5 is merged in (owner docs only, no conflict).
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

## Next: unit 3 (the component), then unit 4
The component must match these seams exactly, because the checks rewrite or wrap them:
- **`SRC` rule strings** (`list_shape_check.cjs` top):
  - `iaListModel` holds `rank.slice(0, IA_LIST_CAP)`,
    `def.keep ? [...rows.filter(def.keep), ...rows.filter(it => !def.keep(it))] : rows`,
    `items.filter(it => iaInScope(def.site(it), scope))`, `words.every(x => t.includes(x))`, `sort.cmp(a, b) || i - j`,
    `f.options().some(([o]) => String(o) === String(v))` and `n > IA_LIST_CAP && gs.length > 1`;
  - `iaListHref` holds `v.sort !== def.sorts[0].key`;
  - `iaListTier` holds `ns <= IA_LIST_CAP ? 1 : 2`;
  - **new:** `iaListTiles(def, m, ctx)` holds `const n = m.n;` (plant `tile`);
  - `iaScopeEntries` holds `route && route.shape === 'list'`.
- **Window plants (Q4).**
  - `shapeList` and `iaListModel` are top-level `function` declarations (the plants assign `w.shapeList` and `w.iaListModel`).
  - `IA_LIST_KEEP` is a top-level `let`.
  - `IA_LIST_DEFS.decisions.sorts` is an array, and `IA_LIST_DEFS.findings.items` is a function.
  - The `remainder` plant sets `IA_LIST_DEFS.sites.more = () => ''`, so the Sites remainder line comes from `def.more`.
- **Markup B reads (spec §3.2):**
  - `section[data-shape="list"][data-ia-list]`, with tiles as `.ux-kpi` whose `.ux-kpi-l` is the list title;
  - rows `tbody tr[data-row]` with one `a.ia-row-go`, and chips `.ia-list-chips .ia-chip`;
  - the form `[data-ia-list-tools]` with `select[name]`, `input[name=q]` and `button[type=submit]`;
  - "Show all n" as a link, and `.ux-empty[role=status]`.
  - The sort `<option>` values and texts must equal B's literals in order.
  - Facet option texts must equal B's word tables.
- **Sort orders B computes (Q3):**
  - Decisions: `priority` = the ATTN order; `due` = the earliest `uxDueIso` over the decision's ATTN rows, no date last.
  - Findings: `priority` = the `HC.findings` order; `site` = by Site name, `localeCompare`.
  - Actions: `due` = by `a.due`, no date last; `item` = by the index in `planItemsV1(op)`, items not in it last.
  - Sites: `gap` = D-IA.27 (Sites with a target first, gap ascending); `name` = `localeCompare`.
  - All sorts are stable.
- **Restore (D-IA.73 a):** the L2 `innerHTML` after an in-page Sort change must be byte-identical to a fresh boot at that address. Do not put
  render counters (such as `UX_QN`-style ids) in list markup.
- **Actions facets:** `state` takes the keys `released`, `waiting` and `returned`. B derives them from `planCaseIds` and `releaseShown(op,
  item).at`, which is `actionState`'s rule. `version` keeps the Actions of `planApprovedIds` when the plan is Approved, else those of
  `planItemsV1`.
- **Facet options:** `heading` lists the `LENS` keys present in the operator's Findings. Every other facet has a fixed vocabulary. A select is
  drawn at tier 2 when at least 2 options are present in scope.
- **Unit 4:**
  - `outcomes_table_check` is still to be retargeted (spec §9 unit 4(a)); it is not touched yet.
  - Item 12 of `shape_check` also suits the Site hub's "Sites" crumb, which is not asserted yet (spec §5). Add it with unit 4(a) if wanted.

## Proofs still owed (cannot run before the component exists)
- Every IA-2b1 plant fails under `node tools/ia_gates.cjs --force IA-2b1`. Today they exit 2 (no component). That is slow, so run it in the
  background.
- Item 15 and the copy and qty list blocks were not seen failing on a real violation. After unit 4, introduce one, watch it fail, then
  revert.
- `qty_check`'s `EQUAL` is dormant until IA-2b1 lands. It expects Lakeside −$852, Harvest −$770 and Metro −$3,184.

## Risks
- `copy_check` needs `tools/rendered-text.json`, which is ignored by git. Run `node tools/render_text.cjs` first.
- The forced `list_shape_check` takes about 35 s now, and longer once B renders real lists. That covers 24+ boots plus 12 fresh-boot
  comparisons.
