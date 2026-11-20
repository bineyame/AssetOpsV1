# IA-1 rulings, continued

Architect (Claude), 2026-11-20. `rulings.md` is at the 15k-token cap (RULES §9); later answers are here. Index lines are in
`.ai/decisions/index-rulings-10.md`.

## IA-1b mid-build answers

Answered against `task/IA-1b-hub` at `aa9eb82f7`. Question in `mid-build-questions.md`.

### D-IA.31 A drawer's focus trap holds over what Tab really reaches (answers Q1)

- **Class.** The trap's first and last are computed from a set that is not the set Tab reaches. `offsetParent !== null`
  keeps links inside a closed `<details>` (Chromium), and the set changes whenever a link becomes text (`iaUnlink`, every
  unbuilt address under D-IA.16, now and in IA-1c). Waiting for IA-2d would fix this one drawer by accident and leave the
  class: the next unlinked last link breaks the trap again. IA-1b fixes it now.
- **Ruling: the reviewed code that may change, and nothing else.**
  - `loop-ux.js`, the drawer `keydown` listener (the one opening `const d = document.querySelector('.ux-drawer[data-open="true"]')`):
    only its `Tab` branch. Its `Escape` branch, `uxOpen`, `uxClose` and the click listener stay byte-identical.
  - One new page-global function in `loop-ux.js`, declared as a function declaration (so a plant can reassign it, as
    the palette plant does `iaPaletteFilter`), placed just above the listener:
    `function uxTabbable(x)` returns true only when all hold:
    1. `x.getClientRects().length > 0` (rendered; replaces `offsetParent`, which also misreads fixed-position elements);
    2. `getComputedStyle(x).visibility !== 'hidden'`;
    3. `!x.closest('[inert], [hidden], [aria-hidden="true"]')`;
    4. `!x.matches('[tabindex="-1"]')`;
    5. `!x.closest('details:not([open]) > :not(summary)')` (nothing inside a closed `details` but its own `summary`;
       this also covers nested closed `details`).
  - The `Tab` branch: the selector stays as it is; the filter becomes `.filter(uxTabbable)`. Wrap rule:
    `Tab` when `document.activeElement` is `last` **or is not in `f`** goes to `first`; `Shift+Tab` when it is `first`
    **or is not in `f`** goes to `last`; both `preventDefault()`. Otherwise the browser moves focus. With an empty `f`,
    `preventDefault()` and focus the drawer's Close (`.ux-x`), so focus never leaves an open drawer.
  - `index.html` is rebuilt from the module as for every vNEXT change. No other reviewed function changes.
- **Checks (uxi, `ux_interaction_check.cjs`).**
  - **Retarget "overview drawer &lt;k&gt;"** (block 1): after opening, press `Tab` 30 times then `Shift+Tab` 30 times,
    `waitForTimeout(12)` each, and assert after **every** press that `document.activeElement.closest('#uxd-<op>-<k>')`
    is non-null (today it checks only the end state). Run for all three operators (`lakeside`, `harvest`, `metro`), the four
    headings each.
  - **New "drawer trap sweep"**: for each operator, on `#/portfolio`, `#/portfolio/outcomes`,
    `#/portfolio/demand-and-capacity` and the operator's first Site Overview, every visible `[data-ux-drawer]` opener (one per
    drawer id) gets the same 30 + 30 walk with the same per-press assertion, then `Escape` returns focus to the opener. One
    line per route and operator, naming the first drawer that leaks.
  - **New "drawer trap unlinked last"** (the class, independent of the live link set): on Lakeside `#/portfolio`, open the
    Assure drawer, then in the page replace every `a[href]` after the Close button with `iaUnlink`'s text form (run
    `iaUnlink` on the drawer body with those hrefs treated as unbuilt, or substitute the exact markup it renders:
    the element carrying `data-ia-to`), and append `<details><summary>More</summary><a href="#/plan">x</a></details>` at the
    end of the drawer body, closed. The walk must stay inside, and `Shift+Tab` from Close must land on that `summary`.
    It holds whether or not IA-2d relinks Scope & coverage.
- **Plant that must fail: `UXI_PLANT=trap`.** In the page, `uxTabbable = x => x.offsetParent !== null` (the pre-fix
  filter). Runs "drawer trap unlinked last" and the Lakeside "overview drawer assure" walk only (its host), and must FAIL on
  both; the uxi plant runner exits non-zero if either passes. Record its first failing line in the packet's plant table.
- **Sweep of the class.** `offsetParent` decides focus in one other place, `uxFocusAction` (`loop-ux.js`): it picks a target
  to focus after an act, not a trap's bounds; a hidden target falls back to the page's `h1`, so focus does not escape. Not
  this class; unchanged. Any later trap (palette, popover) uses `uxTabbable`.
- **Count.** Q1 stays counted (1); the template defect is that the spec named `iaUnlink` but not the reviewed code that
  depends on the live link set. Spec §7's reused-code list must, from IA-1c, name each reviewed function that reads the
  focusable or link set of a page it changes.
- **Why.** A trap is correct only if its bounds are computed over what Tab can reach; matching that set (and wrapping
  from any position outside it) holds whatever the last element is. The unlinked synthetic case keeps the proof once the
  real link returns.
