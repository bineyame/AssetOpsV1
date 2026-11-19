# T1 mid-build questions (RULES §4 item 7)

Raised by the Implementer during the build, 2026-11-19. Each stopped only the affected part; the rest is built.
Count: **2**.

## Q1. Spec §6 edits `.claude/agents/*.md`; the T1 dispatch forbids any `.claude/` change

- **Conflict.** Spec §6 rows 1 and 2 rewrite `.claude/agents/assetops-reviewer.md:35-38` and
  `.claude/agents/assetops-implementer.md:54` in pooled form, and inventory check 7 (§7.2) covers the §6
  documents. The reviewer guide R5 plants "an unpooled command in `.claude/agents/assetops-reviewer.md`". The
  coordinator's dispatch says: "No `.claude/` changes. Do not create or change anything under `.claude/`".
- **What is stopped.** The two `.claude/agents` edits. Nothing else.
- **What is built.** Check 7 runs on the other five §6 documents and is blocking. The two briefs are listed in
  `DOCS_PENDING` in `tools/checks/test_heavy_slot_inventory.mjs` and checked by test `7b` as a node:test
  `todo`: it reports their 4 unpooled lines on every run but does not fail. Today it reports
  `assetops-reviewer.md:37` (`-m pytest`), `:38` (`npx tsc`, `npx vitest`) and `assetops-implementer.md:54`
  (`-evidence.mjs`).
- **Asked.** Either (a) the coordinator (or an owner-approved change) makes the two §6 edits after the merge,
  then `7b` is folded into check 7 (move the two paths from `DOCS_PENDING` to `DOCS`, drop the todo); or
  (b) the Architect drops them from §6 and check 7. Until then an agent copying the reviewer brief's command
  block gets a refusal with the pooled form (the tripwires still hold), so nothing runs unpooled.

## Q2. A refused vitest run leaves `frontend/vite.config.ts.timestamp-*.mjs` behind

- **Observed.** P-T6 unpooled (`cd frontend && npx vitest run <file>`) exits 69 as specified, and leaves an
  untracked `frontend/vite.config.ts.timestamp-<ms>-<hash>.mjs`. Vite 5.4.21 bundles the config to that file,
  imports it and deletes it in a `finally`; `process.exit(69)` during the import skips the `finally`. The
  pooled run cleans up normally. `.gitignore` has no pattern for it, so `git status` shows one stray file per
  refused run until someone deletes it (check-all's tracked-evidence guard does not fail on untracked files).
- **What is stopped.** Nothing; the primary tripwire form stays (it works: refused unpooled, passes pooled).
  I deleted my one stray file.
- **Asked.** Which, if any: (a) a `.gitignore` line `frontend/vite.config.ts.timestamp-*` (`.gitignore` is not
  in the spec's file list); (b) switch to the spec's `globalSetup` fallback, which runs after Vite has removed
  the temp file (the spec allows it only if `import.meta.url` fails, which it does not); (c) accept and
  document. Default if unanswered: (c), stated in the packet.
