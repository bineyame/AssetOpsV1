# WK rulings (D-WK.1 to D-WK.9)

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
Owner-level calls are logged in `specs/OWNER-AWAY/decisions-2026-11-21.md` rows 53 and 54. Row 36 (owner: option b)
is the authority for the copy.

## D-WK.1 WK is one coordinator-only tool over DS4's world

`tools/walk_world.py` copies, prepares, checks, serves, smoke-tests and drops one walkthrough database. It writes into
the copy only through product commands. It never builds, clones, freezes or drops a world rung; those stay with
`tools/world.py`, which refuses every walk or serve name (D-DS3.22, D-DS4.13). Splitting the tools this way keeps the
world ladder unable to touch a served database, and the walk tool unable to change a template.

## D-WK.2 The parent is the L2 at today's key whose check passed on today's check inputs

The copy reads the parent through `World.current_l2()` and `World.check_state()`. These are the same functions
`world clone` and `world list` use, so `check_passed: true` in `world list` and WK's gate cannot disagree. A name typed
by hand or read from `list` alone is not enough: `list` does not show whether the key is today's, and DS4's fix round
(D-DS4.33) replaces the kept ladder under new names. Stale, unchecked or failed parents are refused, each with its code.

## D-WK.3 What WK adds: two emulated statements and one rebuild; no agreed Action (owner-level, row 53)

- **Added.** The finance lead's draft and final management-accounts statements for October, the figures of DDR S5
  and S8 (revenue 9,700.00; fuel cost 5,100.00, then 5,000.00), with source text "Emulated management accounts,
  October 2026, draft" and "..., final". Then one snapshot rebuild per tenant and month.
- **Why.** The deep-dive's money reads "not yet reconciled" until a closed month matches the operator's accounts
  (3A7). With no statement, the walkthrough could show only the refusal. With the two statements it shows both states
  in the record: the draft misses on fuel (2.1%), and the final matches within 1% against the world's own records
  (revenue 9,688.00, fuel 4,995.00, `derived-values.json`). The source text says "Emulated", because the statement is
  as emulated as the exports it reconciles (D14: emulated is never Recorded). The rebuild is required: 5c reads the
  standing at the snapshot's as of, and the L2 snapshot predates the statements (the 3B4 merge note).
- **Not added.** An agreed Action. The change is agreed by people at the walkthrough and recorded then (RC9; §5 step
  10). A pre-recorded Action would show a decision nobody took. No observer rerun (statements change no observation)
  and no profile admission (DDR proves that path).
- **Reverse by:** removing the `statements` entries from `walk-layer4-v1.json`. The rebuild then has nothing new to
  read and the screen shows "not yet reconciled"; W4's `expect.reconciled` becomes false.

## D-WK.4 "Clean and good" for the copy is W1 to W7

The owner accepted DS4's meaning for the world: an L2 whose `world check` passed (strategy §10 Q4; OD-4, a verified
clone counts). WK keeps that meaning and proves the copy still holds it after its own writes. W1 proves lineage and
currency. W2 proves the new snapshot rebuilds. W3 proves the copy differs from its parent only by the declared rows.
W4 proves the screen's month is served, current and reconciled, with the step-5 figures. W5 runs the independent model
again. W6 proves nothing else was touched. W7 proves every step ran. A FAIL stops the run (W9) and goes to the Architect.

## D-WK.5 The serve is the 13 Nov shape on ports 8991 and 5491 (owner-level, row 54)

- **Shape.** The same mechanism as `tools/demo_combined.py serve`: `uvicorn lab_app:app` from the tree's `host/`
  on 127.0.0.1, Vite dev with `ASSETOPS_API_PORT`, children in their own sessions, logs under `var/polish_walk*`,
  owner access through Tailscale and an SSH tunnel. It does not run the demo tick loop, warming or the upload
  gateway: those serve the demo tenant's telemetry stories, which the world does not have.
- **Ports.** 8991 and 5491, fixed in the walk definition. 8990 and 5490 belong to the 13 Nov walkthrough serve, which
  WK must not touch. 5490 is listening on the server today. A busy port is refused, never taken over.
- **Environment.** Built, never inherited. The served tenant is `lakeside-power` (ON1). No pseudonym key folder,
  because nothing on the walkthrough uploads, so the commercial upload router stays off (`main.py:690`). Also no
  real-data, operational-entry, upload, gateway or live-field switch.
- **Reverse by:** changing the two ports in the walk definition once the owner retires the 13 Nov serve, and removing
  them from `PROTECTED_PORTS`.

## D-WK.6 A walk serves exactly the commit it was copied at

The parent's key covers the code trees at that commit, so the snapshots are current for that code. A newer `main` may
change the rules digest and make the month read REBUILD_NEEDED. So a newer walkthrough is a new WK with the next label,
and a running serve is never re-pointed at a newer tree. `serve` refuses a tree whose HEAD differs from the manifest's.

## D-WK.7 Teardown on the owner's word

Stop by recorded PID (checked against its command line), drop without `FORCE`, remove the detached worktree. The L2,
the world manifests, the key folder and the 13 Nov database stay. A walk database is torn down after the walkthrough
it served, on the owner's word, or when a newer WK replaces it.

## D-WK.8 Size and review

1.25 units, one commit, against the plan's 1. The difference is the check (W1 to W7) and the smoke, which make "clean,
good" a command for the copy as DS4 did for the world. Standard review: the tool reuses DS4's reviewed check and adds no
product mechanism. The coordinator's run follows the merge (§5).

## D-WK.9 WK needs 5c's route, not 5c's screen

WK builds after 5c units 1 and 2 (the read and `GET /api/portfolio/month`), because W4 and S2 read through them. 5c's
screen is a UI merge, held for the owner's walkthrough, and the owner walks it first on DDR's rehearsed tenant (5c
§9). So WK does not wait for it. When the screen is on `main`, the copy serves it, and `/portfolio/month` is in the
smoke's page list either way.
