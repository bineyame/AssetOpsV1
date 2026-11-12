# PR-3 review: server fix round + form half (Reviewer, Claude, 2026-11-12)

Branch `task/PR-3-price-entry`, head `d4c0935c0`, worktree `AssetOpsV1-pr3`. Scope: (a) `d66bf933e..fc67edd70`
(L1 replay across the series, D-PRICE.2 site_name, Postgres cases) and (b) `e2959d4cf..d4c0935c0` (form half).
Main-merged content not reviewed. Spec: rev 5 §5.3-5.4, owner defaults 2026-11-12, D-PRICE.1-3 (no D-PRICE.4 on
file), v7.1 `price-it.html` (no form there; deviation labelled D-PRICE.3), rev-6 token rule.

**Verdict: ACCEPT with findings fixed on the branch** (two Medium; no High).

## Findings

**M1 (Medium, honesty) `frontend/src/sites/priceEntryClient.ts:458`** - every 5xx on save maps to `unavailable`,
which shows "Prices cannot be saved right now. Nothing was saved." (`SitePriceEntry.tsx:183-186`). Only the route's
503 `ASSUMPTION_STORE_UNAVAILABLE` means nothing was written; a 500/502/504 (dev proxy reset, gateway timeout, an
error after commit) may follow a landed save, so "Nothing was saved." can be false. Fix: on save, treat only 503 (or
the code `ASSUMPTION_STORE_UNAVAILABLE`) as `unavailable`; any other 5xx as `lost` ("We could not confirm the save.
Saving again is safe."). Add a vitest case for a 502 on save.

**M2 (Medium, accessibility) `frontend/src/sites/SitePriceEntry.tsx:92-105, 289-346`** - no focus management. Opening
replaces the focused "Set a new price" button with the form, Continue replaces the focused Continue button with Save,
and a save unmounts the form: each time keyboard focus drops to `<body>`. The brief asks for focus on open, confirm
and error. Fix: on open focus the Amount input (or the form title with `tabIndex=-1`); on confirm focus the confirm
heading/summary (or Reason when `reason_required`); after save focus the success note; on a refusal focus the first
`aria-invalid` field (the `role="alert"` line is announced already). Add vitest assertions on `document.activeElement`.

**L1 (Low) `frontend/src/sites/SitePriceEntry.tsx:331-341`** - "Change" after a `lost` save keeps the same key; if
that save landed, an edited resubmit gets 409 `IDEMPOTENCY_KEY_REUSED`, whose real store words
(`postgres_assumption_store.py:124-126`: "Idempotency key 'price-entry-…' already published revision <uuid> with a
different request; nothing was written.") are shown verbatim plus "Nothing was saved." - system text, a UUID, and
false for the earlier save. The vitest fixture (`sitePriceEntry.test.tsx:327`) uses a friendlier message than the
store sends, so this is untested as shipped. Fix: after `lost`, hide "Change" (or warn it starts a new save), and/or
map this code to plain words in the route.

**L2 (Low) `backend/assetops_backend/financials/price_entry.py:163-171` + `financial_api.py:145`** - L1 fix is
correct for series ≤1000 revisions and covered (no-DB + Postgres retry after a later SUCCESSION). Beyond 1000, the
page is the *oldest* 1000 (`ORDER BY revision_no LIMIT`), so a retry of a recent, no-longer-cited save falls through
to a fresh derivation; the store then either replays (same digest) or refuses 409 `IDEMPOTENCY_KEY_REUSED` - never a
duplicate write, but the retry can wrongly refuse. Unreachable for a demo series. Better: look the key up directly
(one indexed query) instead of paging the series.

**L3 (Low) `frontend/src/shell/SitePricesFrame.tsx:176-200`** - if the post-save re-read fails, `PricesRead` shows
the refusal and the rows (with the success note and Back link) disappear, so a landed save loses its note.

**L4 (Low, packet) `.agent/PR-3-packet.md`** - "→ 19/19 after the fixes" is inferred: only the two failing guards
were rerun. Say "17 pass on bb61216fb + 2 rerun pass on 528b7c8f6".

## Checked and fine

- Form only on `entry.enabled && entry.keys.includes(row.key) && row.stored` (`SitePricesFrame.tsx:183-185`); keys are
  `stored_keys(site_type)`; future keys never enterable (no-DB test asserts it).
- `entry.enabled` false under `known_at` and when the switch is off; live-view line + link dropping `known_at`; off
  keeps the administrator sentence, on uses default 7's sentence verbatim (`price_page.py:35`).
- One `useRef` key per opened form, reused on retry; "Saving again is safe." honest for an unchanged retry (store
  replays on same digest; L1 server fix covers a following save). Request has no actor/kind/instant fields.
- Refusals: server message + "Check: <fields>." + "Nothing was saved."; REASON_REQUIRED on save reopens Reason.
- Applies-from defaults to server Site-local today; preview is the one server sentence, no count (default 8).
- Re-read via `version` keeps the old body on screen; success note is the server's "Updating…" sentence + Back link.
- D-PRICE.2: `site_name` lookup inside the unavailable try (503 on failure, tested), code fallback on NULL.
- SR-2 exemption: one file, commented, pending Architect Q3 (`tools/checks/page-range-forms.ps1:77-80`).
- CSS: all new font sizes `var(--text-*)`. Mock deviation labelled in code and packet.
- Layout evidence: packet records 6/6 at 1440/390 with commands (not rerun by me; needs fixture API + vite).

## Checks run (by me, head d4c0935c0)

- pytest no-DB: `test_pr3_price_entry.py test_pr3_price_page_entry.py test_pr2a_price_page.py
  test_pr3_price_entry_postgres.py` → **107 passed, 4 skipped** (Postgres file skips without a URL; no DB used).
- `npx.cmd tsc --noEmit` → exit 0.
- `npx.cmd vitest run sitePriceEntry.test.tsx sitePrices.test.tsx` → **32 passed** (18 + 14).
- `tools/check-architecture.ps1` (no -ExecutionPolicy, `ASSETOPS_GUARD_PYTHON` set) → passed.
- Not run: Postgres files (lane rule), layout evidence, full frontend suite/build, check-all.
