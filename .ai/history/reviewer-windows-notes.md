> Moved out of `.claude/agents/assetops-reviewer.md` on 2026-11-18 (declutter step 1). Windows-laptop sandbox notes; the project now runs on a Linux VPS. History only.

In `frontend`, **use `npm.cmd` and `npx.cmd`, not `npm` and `npx`**:

```
npm.cmd test
npm.cmd run build
npx.cmd tsc --noEmit
```

This is not a preference. PowerShell's execution policy on this machine refuses
to load `npm.ps1`, so a bare `npm` fails with `UnauthorizedAccess` before it
runs anything, and it looks like a broken suite rather than a shell setting.
`npm.cmd` and `cmd /c npm` both work.

## A frontend check you are currently expected to fail

`npm.cmd test` and `npm.cmd run build` **cannot run under the sandbox on this
machine**, and that is known rather than something to debug:

```
X [ERROR] Cannot read directory "../../..": Access is denied.
X [ERROR] Could not resolve ".../frontend/vite.config.ts"
```

esbuild validates the case of every path segment when it bundles
`vite.config.ts`, which means enumerating each ancestor directory up to the
drive. The sandbox denies reading above the workspace, so config loading fails
before a single test runs. It is not a missing dependency, not a broken config,
and not something a root `package.json` fixes - that was tried and reverted.
`--add-dir` on the parent does not help either, because the denial is on
reading rather than writing.

So: run it, report the failure, and say plainly that the frontend suite, the
production build and their numbers are unverified. Do not infer a pass from the
Implementer's numbers, and do not spend the review debugging it.

`tsc --noEmit` does run, because it does not go through esbuild, so type
correctness is still independently checkable.
