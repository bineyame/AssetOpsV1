# IA-2b1 handoff (PARTIAL), 2026-11-21

Status: unit 1 is partly built. I stopped because of the context budget. Nothing is live, and every gate is green with IA-2b1 not landed.
Branch `task/IA-2b1-lists`, worktree `/opt/assetecon/AssetOpsV1-ia2b1`.

## Done
- **Base.** It holds IA-2a (f9430112e), the IA-2b spec (d789117f3), the handshake answers (590da9d75) and main at fa13f254f.
  - Merge 993177c9d resolved the index conflicts as unions. IA-2a's state line moved from 182 to 184 in `index-3.md`. The
    `index-rulings-14` row now reads `D-IA.49`–`D-IA.60`, `D-3C2.15`. In `specs/INDEX.md`, the duplicate
    `mockup-vnext-categories-snapshot` row is gone, which brings the file under the 8000-byte cap.
  - Earlier: owner-away row 47 became 52, and `index-rulings-20` became `index-rulings-22` (ea7716e4a).
  - `check-decision-index.py`: OK.
  - main has since moved to d615685d5 (the owner delegation, docs only). It is not merged.
- **`ia_gates.cjs`.**
  - The IA-2b1 PLANTS row is in.
  - The `OWN` map covers IA-2b1 and IA-2b2.
  - A check counts as dormant only when it prints "`<unit> not landed; dormant`" for a landed unit that owns it.
  - `list_shape_check` is added to the runs.
- **`tools/list_fixture.cjs`.** It provides `sites30` and `decisions25`, injected through `IA_LIST_DEFS[key].items`.
- **`tools/list_shape_check.cjs`.**
  - Blocks A, C and D are written. Block B is a stub that fails while IA-2b1 is landed, so the gate cannot pass without it.
  - Not landed, it prints "IA-2b1 not landed; dormant", and ia_gates shows "ok". Forced, it errors, because the component is
    not built yet.

## Next
1. **Finish unit 1.**
   - Write block B (spec §8 row 2, D-IA.73 independence) and its plants: `tile`, `rowctl`, `restore`, `own`, `stakesort` and
     `notarget`. Wire them in `plantSource`.
   - Add the check rows to `shape_check` (items 7, 12 and 15; plants `aliasq` and `deccrumb`), to `click_depth`
     (`listrail`) and to `copy_check` (an IA-2b1 block; `COPY_PLANT=list`).
   - Commit.
2. **Unit 2:** the `qty_check` count mode, format mode and `EQUAL` table, with five plants.
3. **Unit 3:** the component. It must contain the exact rule strings in `list_shape_check.cjs` `SRC`, because the source plants
   rewrite them. Those are `iaListModel`, `iaListHref`, `iaListTier`, the `IA_LIST_CAP` constant and the `iaScopeEntries`
   list branch.
4. **Unit 4:** units 4(a) and 4(b) per spec §9.

## Design choices already fixed by the written checks
- **Def interface.**
  - `{ key, site(it), text(it), keep?(it), group?(it), items(op), facets: [{ key, label, all, options() → [[value, word]] (the fixed vocabulary), of(it) }], sorts: [{ key, word, cmp }] }`.
  - B will also need `cells` / `title` / `target` / `rowKey` / `tiles` / `more` for rows, tiles and the remainder line.
- **Facet values.** A value is valid when it is in `options()`, otherwise it is ignored. A select is drawn when at least 2
  options are present in scope.
- **`iaListHref`.**
  - It returns the address without `#/`.
  - Values are `encodeURIComponent`-ed. Block A compares them decoded, and C compares `scope=site:k` decoded.
  - Invalid facet values and the default sort are dropped.
- **Block D.** At tier 2, "Clear filters" sits in the chips row even when no chip is drawn (two filters set, both drawn as
  controls).

## Open pre-flight questions (default used)
- **Q1.** `resolveScreen` (loop-core.js, a reviewed function) writes `'#/' + iaLiveAlias(id) + the typed query`. That drops an
  alias's own query (`findings-cost` → `findings?heading=optimize`).
  - Default: leave loop-core untouched. `iaLiveAlias` notes the alias it last resolved (reset on every call). `iaScreen` then
    merges that query and replaces the history entry with the canonical address.
  - The Architect should confirm.
- **Q2.** In the 4(a) re-scope, the group and Site scope of a fixture with fake Site keys (`fx..`) is undefined.
  - Default: block D uses scope `all` only.

## Risks
- The forced `ia_gates --force IA-2b1` run is slow (more than 2 minutes) while the component is absent, because every plant
  errors. Run it in the background.
