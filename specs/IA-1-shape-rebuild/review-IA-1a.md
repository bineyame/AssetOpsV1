# IA-1a review, round 1 (fresh discovery review, W5)

Branch `task/IA-1a-frame`, head `23c7a416d`, worktree `/opt/assetecon/AssetOpsV1-ia1a` (read only). Merge base with main
`f4b8923a7`; main has not touched `vNEXT/` since. Judged against spec rev 2 §2 and §6 to §8, rulings D-IA.1 to D-IA.20 and the
handshake answers, reviewer guide rev 2, and the two owner files of 20 Nov.

## Summary (round 1)

- **Verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH** (M1, M2, M3; the Lows may be fixed or logged).
- The render path matches spec §2.4. The 13 gate runs bite as claimed. `planParts` is byte-identical (8 of 8, rerun). No link
  to an unlanded or legacy screen survives in the frame. The reviewed Decision, Site and plan pages pass `ux_interaction_check`
  324/0.
- **M1:** Harvest's not-found top bar is broken at 1280 and 1440, in light and dark. The builder's own screenshot shows it,
  but the shot script records it as "ok".
- **M2:** below 1280, the unavailable rail items either overflow the 64 px icon rail (1024 to 1279) or lose their "Not
  available yet" status (761 to 1100). At 761 to 1100 they look the same as live links.
- **M3:** `after_render_check` does not see the frame root being replaced after render (my plant passes).
- **Lows:** the no-tab-stop rule is unchecked; the Lab shows in `?book` mode with the switch off; the deviation-3 summary
  string was added without a ruling; `walkthroughs.md` still names the old plan route; two hardening gaps in `shape_check`.
- **Residual for the Architect:** `IA_ALIASES.financials` collides with IA-2e's `financials` route.
- Deviations: 1, 2, 4, 5 and 6 are sound. 3 is a workaround and should be called one. 7 is acceptable for IA-1a and must flip
  in IA-1b.

## Checks I ran (head 23c7a416d)

Every browser or jsdom run went through `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh`, with the pw `env.sh` sourced and
`LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH` set.

| Check | Result |
|---|---|
| `node build.mjs` in a scratch copy, compared with the committed `index.html` | byte-identical (the bundle is current) |
| `node tools/ia_gates.cjs` | 13 runs, all as expected, 96.8 s. The plants' first lines match the packet's table (unlink, stub, rail, palette, primary, lab, engine, text, attr, late). |
| `ux_interaction_check.cjs` | 324 PASS, 0 FAIL, exit 0 (matches the packet) |
| `plan_parts_identity.cjs` (the builder's script), merge-base `index.html` against the branch | 8 of 8 byte-identical, same hashes as the packet |
| Rendered-text diff: legacy `#/portfolio/act-first/plan` (base) against `#/plan` (branch), 3 operators | Same segment count (101, 56, 52). The only change: "Decision →" becomes the unlinked "Decision". H1 and subtitle are the same; the title reads `The plan for November and December · <operator>`. |
| Drawer probe on `#/plan`: every `.ev-num` opened (16 drawers, 3 operators) | 0 links in any drawer; no non-good href |
| Frame anchors on `#/plan` | `#/plan`, `#/plan?scope=all`, `#/plan?scope=group:<v>` only; 13 `.ia-unlinked` spans |
| `pwsh tools/check-agent-workflow.ps1`, `tools/check-architecture.ps1` (guard python = main's `.venv`) | both passed |
| Screenshots (my own): plan at 1440 light, 1280 dark, 390 light and dark, 1200 light, 900 light; not-found at 1440 dark | see M1 and M2. 1440, 1280 and 390: frame correct, top bar on one line on the plan, no sideways scroll. |

### Reviewer plants (scratch copy `.../scratchpad/rev-ia1a-r1`, source edited, rebuilt, restored)

| Plant | Check | Expected | Got |
|---|---|---|---|
| r1 `iaUnlink` skips links inside `[data-level="L3"]` | shape_check | fail | **fail**: `#/plan links #/decision/mto-inverter (legacy or unknown)` |
| r2 `iaBind` replaces `#ia-root` with a clone whose H1 reads "Rewritten after render" (`setTimeout 0`) | after_render_check | fail | **PASS** (the plant bites: the H1 reads "Rewritten after render" at idle). See M3. |
| r3 `brandAndListenersOnly` appends text to the subtitle | after_render_check | fail | **fail**: `1 mutation(s) after insertion: children of p` |
| r4 the review select ignores the switch (`dev=true`) | shape_check | fail | **fail**: `review select lists a Lab screen with the switch off` |
| r5 `tabindex="0"` on every unavailable rail item | shape_check | fail (spec §2.2: "no tab stop") | **PASS**. See L1. |

The builder's runs I cite rather than rerun: `plan_switch_check` 781/0, `shell_check` 0 fails (with `SHELL_PLANT=1` failing),
`design_lint` exit 0 (with `LINT_PLANT=1` exit 1), `check_manifest.py` 7571/0, `vocab_check`, `copy_check`, `render_text` and
`hand_typed_scan` at 0. They ran on the branch head plus the last commit (the packet), and my reruns agree with every run I
repeated.

## Findings

### M1 (Medium, acceptance gap, spec §2.3 and §6 item 6): the not-found top bar breaks for an operator with a pending recalculation, and the evidence records it as a pass

- **Where:**
  - `loop-core.js` `uxScopeLine` returns before it moves the `.snap-pending` notice when `screen.noFigures` is set. The
    `not-found` route is `noFigures: true` (`ia-routes.js`).
  - `uxPeriodMenuHtml(op)` (`loop-ux.js`) puts `periodChip()`'s pending span inside the period `<summary>`.
  - `ia.css` sets `.ia-frame .topbar{flex-wrap:nowrap}`.
- **What I see:**
  - Harvest `#/x-unknown` at 1440 dark (my shot) and at 1280 light (the builder's own
    `/opt/assetecon/evidence/IA-1/IA-1a/screenshots/harvest-not-found-1280-light.png`).
  - The amber "Recalculation pending. At 09:40 on 6 Nov, Thika's October refrigeration ser…" pill runs off the right edge of
    the top bar.
  - The period chip is crushed into a column five lines tall ("October / 2026 · / Figures / as of / 06:00, 6 / Nov"), which
    hangs over the review bar and the bar's bottom border.
- **The evidence:** `shots.txt` says `ok harvest #/x-unknown 1280x720 light: … top bar on one line true (6 items)`. The script
  compares the items' vertical centres only, so a child that wraps inside its item, or runs off screen, passes.
  - This is the brief's case of "a skipped run recorded as a pass", for the one measurement the frame's C15 rule depends on.
- **Why it matters:** an unknown address is the frame's own route. The broken bar is on screen whenever Harvest has its
  pending snapshot, which is the demo default.
- **Fix:**
  - Decide where the pending notice goes on a route without figures, and put it there before insertion. Either the frame
    leaves the chip out for `noFigures` routes, or `uxScopeLine` moves the notice before its `noFigures` return. No new
    copy either way.
  - Tighten `shots.cjs`, or the uxi header check, run on IA routes. Every top-bar item must keep one line height (≤ about
    40 px), and no element in `.topbar` may end past `innerWidth`. Show that tightened check failing on the current head
    first.

### M2 (Medium, acceptance gap, spec §2.2 "unavailable root … with the status 'Not available yet'"; NavRail's "never colour alone"): the unavailable rail items break below 1280

- **Where:** `ia.css`. `@media (max-width:1100px){.ia-rail-status{display:none}}`, and no rule for the existing icon-rail band
  `@media (min-width:1024px) and (max-width:1279px)` in `ux.css` lines 26 to 32, which narrows only `.rail a` to 44 px.
- **1200 × 800** (my shot): the rail is 64 px. Each `.ia-rail-unavailable` span keeps its full label and status, so the words
  wrap into stacks ("Not / availa / yet", "Assets / & / cover") that spill past the rail's edge. The active Plan link is
  clipped to "P".
- **900 × 800** (my shot): the status is hidden. Portfolio, Sites, Findings and the rest look the same as live links, apart
  from the lit Plan item. Nothing on screen says they are unavailable; only the `aria-label` still does.
- **Why the evidence missed it:** spec §6 item 6 asks for screenshots at 1440, 1280 and 390 only, so 761 to 1279 is never
  captured. These are common laptop and tablet-landscape widths.
- **Fix:**
  - **1024 to 1279:** give `.ia-rail-unavailable` the icon rail's treatment (44 px wide, text hidden, the label and status
    kept in the accessible name and a `title`). Mark the icon itself, for example with a muted or dashed treatment, so that
    the state is not shown by colour alone.
  - **761 to 1100:** keep the status visible on one line (it fits in the 174 px rail at `--fs-xs`), or use the same icon
    marker.
  - Add 1200 × 800 to the shot set and assert that no rail child ends past the rail.

### M3 (Medium, gate gap, D-IA.13 and D-IA.17): `after_render_check` cannot see the frame root being replaced

- **Where:** `tools/after_render_check.cjs` line 24. The observer watches only `root`'s subtree, and `hooked` counts only
  calls to `__iaInserted`.
- **My plant r2:**
  - It replaces `#ia-root` after insertion with a rewritten clone (H1 "Rewritten after render").
  - The check passes on every route and operator. The mutation is a `childList` change on `#app`, outside the observed
    subtree, and the old root is simply detached.
- **Why it matters:** "re-render or swap the canvas after load" is exactly the class D-IA.13 bans: today's `uxShell` and
  `uxChrome` patch by injection. A check that passes on it cannot fail for that class.
- **Fix:**
  - At idle, assert `document.getElementById('ia-root') === root`, and assert that `hooked` rose by exactly one per `go()`.
  - Add `AR_PLANT=replace` (my r2) to the runner's IA-1a list, and show it failing.

### L1 (Low, gate gap): the "no tab stop" half of the unavailable-root rule is not asserted

- **Where:** `shape_check.cjs`, item 3.
- **What happens:** my plant r5 (`tabindex="0"` on every unavailable item) passes.
- **Fix:** item 3 also asserts that the item and its descendants have no `tabindex` ≥ 0, no `button` and no `a`.

### L2 (Low, D-IA.7 class sweep): the Lab is reachable with the switch off through `?book`, and a dead Lab link sits on the default landing

- **`?book`:** `http://…/index.html?book` renders all 42 book pages, including `#book-lab`, the full Lab shell, with
  `l4-dev` unset. It is mock tooling with no link to it in the UI. It is the same class as the review select, which the spec
  does gate.
- **The default landing:** an empty hash opens the legacy Portfolio (deviation 7). Its legacy rail footer shows
  "WORKSPACE › Simulator Lab" with the switch off; clicking it gives not-found, so the Lab is not reachable, but the link is
  dead.
- **Fix:**
  - Filter the book pages the way the review select is filtered (`p.root!=='Simulator Lab' || iaDev()`).
  - Either draw the legacy rail footer only under `iaDev()`, or leave both items to IA-1b, which retires the empty-hash
    landing.

### L3 (Low, spec §7 "a missing string is raised as a question, not invented"): deviation 3's summary label

- **Where:** the review-bar `<summary>`, "Still to be rebuilt (12)" (`loop-ux.js` `uxReviewExtrasHtml`).
- **What is wrong:** this is a new string. Spec §2.7 gives only the line "Still to be rebuilt: …", and the mid-build count
  is 0.
- **Is the change itself right?** The layout reason is real: the full line pushed the first queue row below the fold at
  1280, and uxi caught it.
- **Fix:** record it as a workaround with the Architect's acknowledgement (or a ruling) rather than as a silent deviation.
  The packet already names it; the label needs a ruling.

### L4 (Low, spec §0 "What you may touch": `walkthroughs.md` where a route changes)

- `walkthroughs.md` lines 18, 52, 76, 93 and 107 still name `#/portfolio/act-first/plan`. The route now resolves to `#/plan`
  through the live alias, so the owner's guide works, but it names the old address.
- **Fix:** update the guide to `#/plan`.

### L5 (Low, hardening)

- **Not-found's links are never classified.** `shape_check` crawls from `iaStart()` only. The typed `not-found` route is
  shape-checked but its hrefs are never classified (nothing links to it), so a fault in `iaUnlink` that affects only
  not-found would pass. Run the classifier on `#/x-unknown`'s `hrefsOf` too.
- **The primary rule passes when neither primary names its act.** If the L1 region has no primary and the sticky bar's
  primary has neither `data-act` nor `data-ux-act`, `undefined !== undefined` is false and the rule passes. Require that
  `l1act` is defined when a sticky primary exists.

## The packet's deviations

1. **`--ux-sticky-left/top` on `<html>`. Sound.**
   - Same layout. The phone rule (`top:auto;bottom:0` at 600 px or less) still wins.
   - It keeps a layout measurement out of the frame, in the same class as the existing `ux-has-sticky` class and scroll
     padding on `<html>`.
   - It is not a dodge: the value is positional, and the content and structure are unchanged.
   - uxi's sticky and focus-walk checks on the decision, Site and plan pages pass.
   - It should say plainly that the after-render check does not watch `<html>`.
2. **`data-ux-act` instead of `data-act`. Sound.** The check reads either. The spec text should say `data-ux-act`. See L5
   for the gap where neither attribute is set.
3. **The rebuild line in a popover. A workaround: call it one.** The layout reason is valid, but the summary string is new
   copy (L3).
4. **The trend wraps at 1280. Sound.** It carries the UI branch's r5 L-a item, which asked "prefer a shorter string"; a
   shorter string would be new copy under §7. uxi now asserts "none clipped" and passes, fold checks included.
5. **The plan's H1 and subtitle are the reviewed screen's own. Sound.** Spec §2.6 reuses the reviewed labels, and the
   rendered text is unchanged.
6. **Branch name.** Cosmetic; the dispatch governs.
7. **An empty hash opens the legacy Portfolio. Acceptable for IA-1a only.** Spec §2.2 defines `iaStart()` without saying
   what the empty hash opens. IA-1b must make the empty hash open `iaStart()`; see also L2.

## The dispatch's hunt list

- **Gates that can't fail:** the 13 packet runs bite, and so do my r1, r3 and r4. Two holes: frame-root replacement (M3) and
  the tab-stop rule (L1).
- **A link to an unbuilt or legacy screen that stays clickable:** none in the frame, the palette or the drawers.
  - The scope menu's Sites, the plan's decision and Site links, not-found's "Go to the Portfolio" and every unlanded rail
    item render as text.
  - Legacy screens stay reachable only through the review select and the empty-hash landing, as spec §2.1 allows.
- **The Lab without Developer access:** not reachable in the product frame (shape_check item 5, my r4). Reachable only
  through `?book` (L2).
- **Rewriting after render:** none found.
  - For IA routes, `afterRender` returns into `brandAndListenersOnly` (the brand attribute on `<html>`, `scrolls`).
  - `iaBind` schedules only `uxStickyTick`.
  - No `render` or `afterRender` wrapper exists elsewhere (searched `loop-*.js` and `screens.js`).
- **The plan split:** byte-identical, 8 of 8, rerun against the merge base.
- **Regressions in the reviewed pages:**
  - uxi 324/0. The rebuilt review bar keeps the reviewed order (D2 Grow, D5, decision marks, D2 Recalculate, Brand).
  - The legacy `uxChrome` uses the shared builders with the same markup. The legacy `uxScopeLine` call reads the
    pending notice from the shell's own top bar.
  - The decision sticky bar keeps its offsets through the CSS variables.

## Not verified

- P3 by hand in devtools (the jsdom observer and my plants cover the same ground). The P9 brand-pack sweep in Neutral: I
  looked only at East Africa.
- `audit.mjs` and `rendered_strings.cjs` after the retarget: not run (the packet says the same).
- I did not rerun the full `plan_switch_check`, `shell_check`, `design_lint` or `check_manifest.py`. I cite the builder's runs
  on the same head.

## Residual risk the packet does not name

- **`IA_ALIASES` key `financials`** (→ `site/kobo/financials`, per the spec's table) has the same path as the IA-2e rail
  route `financials`.
  - Alias-first resolution (`resolveScreen`, `iaCanon` in `iaUnlink`) will send the Financials rail item to Kobo's
    Financials once IA-2e lands.
  - This is a spec-level conflict. The Architect should rule before IA-2e (rename the alias key's target, or let a landed
    route win over an alias of the same path).
- **Interim text until IA-1b and IA-1c:**
  - each plan item shows an orphan "Decision" label;
  - not-found says "Go to the Portfolio" as plain text;
  - the scope menu lists Sites as plain spans inside `role="menu"`, and its "Type a Site name" filter acts only on
    `a[role=menuitem]`, so it no longer filters them.

  These are expected under D-IA.16, but the owner will see all of them at the G2 stop if IA-1b and IA-1c do not land the
  targets.
