# WK rulings (D-WK.1 to D-WK.14)

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
Owner-level calls are logged in `specs/OWNER-AWAY/decisions-2026-11-21.md` rows 53, 54, 66 and 67. Row 36 (owner: option b)
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

## D-WK.10 After 0K4a, 0K4b and 0K4e, a C4 FAIL on the new L2 is a stop, never absorbed by the oracle (R2)

- **Ruling.** WK's run builds and checks a new L2 (spec §5 step 1). C4 judges each factor's value and whether a blank
  names its record. It never judges the record's text. The only expected change is that the honesty list names
  `dispatch-3.3` where it named `dispatch-3.2`, which cannot fail C4. Any C4 FAIL line is a stop: a class-B factor with
  a value, an E factor unequal, `uncontracted`, `not_in_product`, or a Site-set line. The run does not copy. Nobody
  edits `C4_CONTRACT`, `C4_SITE_CLASSES` or `C4_KNOWN_FINDINGS` from the run (it stays empty, D-DS4.27). The lines go
  to the Architect as a DS4 finding, who rules with an independent derivation (W2) before any re-check.
- **Why.** By construction, the three merges cannot move a C4 cell in this world.
  - 0K4e changes only the need strings of `necessary_l`, `candidate_l` and `unexplained_l`
    (`structure/rows_mini_grid.py`). It adds no factor row.
  - 0K4b's assumed values are Foundation properties (minimum load, taper start, `sites/models.py`). They are read only
    by the dispatch model and simulator v8, over readings.
  - 0K4a's v8 is a simulator version no world uses (owner-away row 56). v1 to v7 are byte-identical.
  - The world has no telemetry, so every litre leaf stays blank (DS4 §2.1, Src T).
  So a FAIL would mean the product changed meaning without a contract change. Absorbing it from the run would make the
  checker share its expected figure with the code, which W2 forbids.
- **Reversible.** The Architect amends §2.1's contract (an independent derivation, and T9b updated) if a finding
  shows the contract was wrong.

## D-WK.11 WK reaches the walk database only through its own guarded `walk_url` (I2)

- **Ruling.** Spec §3.1. One function builds the walk URL, after the label rule, the protected-name refusal and
  `walk_name_ok`. `walk_name_ok` refuses `assetops_polish_walk1113_test`, any case of `assetops_op*`, any `assetops_world*`
  rung, and anything not `assetops_polish_walk<4 digits>[a-z]_test`. RC4-F1's `database_target` must agree on name, host
  and port. `World.census`, `World.exists` and `check_name` are never called on it. `check_name`'s refusal of `walk`
  and `serve` stays as it is, the right rule for the world tool.
- **Why.** `check_name` is the world tool's tripwire against touching a walkthrough database, so WK cannot use it, and
  must not weaken it. A second, narrower guard is used only by WK. It admits exactly the one shape WK creates, and it
  keeps the 13 Nov database and every operator database out by name before any connection.

## D-WK.12 Two figures for one quantity only where the operator acts or reconciles: the allowed pairs (R4; DDR R16; owner-level)

- **Ruling.** On the served pages (WK) and the rehearsed screen (DDR), a quantity is shown once, except in these pairs:
  plan against actual (the contribution bar and the budget lines against actuals); Kisiwa's budget notice (the
  stated −$60.00 against its lines' −$65.00, a reconcile); and the finance lead's statement against the records,
  only while they do not match (DDR's S7 read). Once reconciled, the screen says so in words and does not repeat the
  statement's figure. Kobo's stop-70 litres and value read "Not available yet" (no EMS export in either world). The
  reviewers read the smoke PNGs (WK) and the expectation file's `screen` (DDR). A breach is a product finding for the
  Architect; neither unit adds product code to fix it. Logged as owner-away row 66.
- **Why.** The owner's rule (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`): two numbers confuse
  unless they set up something to act on or reconcile; plan against actual is the owner's own example. The statement
  pair is a reconcile only while it is open.
- **Reversible.** Add or remove a pair here; the reviewers' reads change with it.

## D-WK.13 The copy is checked clean again after the serve (R3)

- **Ruling.** Smoke S4 re-runs W3's census judge, read-only, after the browser pages. Any table outside the declared
  deltas FAILs, naming it. This is T5's judge with no new mechanism.
- **Why.** The owner walks only a clean database. A read path that writes (a cache, a response store) would make the
  walked copy differ from the checked one without anyone seeing it.

## D-WK.14 Day 14: 3C2 unit 2, the world build and check, WK, then DDR; sizes restated (owner-level, row 67)

- **Ruling.** Order and sizes:
  1. **3C2 unit 2** (0.25 unit, lane C, build now, verification review; D-3C2.16).
  2. **WK's tool** (1.4 units) and **DDR** (1.5 units) build at once in their own lanes.
  3. **World build and check** (WK §5 step 1, about 26 minutes, the one heavy database job), as soon as 3C2 unit 2
     has merged.
  4. **WK's run**, steps 3 to 11, once WK has merged. No merge to `main` from step 3 to step 5. The owner's walk
     database is then ready, and the 5c screen is walked on the rehearsed tenant.
  5. **DDR merges** after WK's step 5. The coordinator's rehearsal (DDR §5.1) follows, then its serve on 8992/5492
     (D-DDR.13).
- **Why.** WK's walk database must show the connected "Actions in hand", so that an agreed change recorded live
  appears (WK §5 step 10). So 3C2 unit 2 must be on `main` before the L2 is built, because unit 2 changes
  `backend/assetops_backend`, the world key. DDR's merge changes the same tree, but nothing served, so it waits until
  WK's copy is checked. The other order would stale the L2 and cost a second 26-minute build. Building in parallel
  keeps DDR on time, and the owner sees the deep-dive rehearsed before the 5c walkthrough.
- **Reversible.** Reorder; only the coordinator's run timing depends on it.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on `task/DDR-WK-handshake-answers` (questions at 99b1d8279; `main` 83419e876 merged
in). Folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2.

### Reviewer

- **R1 (High).** Accepted. Spec §5 step 1 is written for a stale L2 (about 26 minutes), with step 0's start condition
  and merge freeze (D-WK.14). 0K4a (83419e876) also changed `simulator/assetops_simulator` since the question, which
  is the same class.
- **R2 (High).** D-WK.10: a C4 FAIL is a stop. The `dispatch-3.3` text cannot fail C4.
- **R3 (Medium).** Accepted: D-WK.13 (smoke S4; T5).
- **R4 (Medium).** D-WK.12 (owner-away row 66).
- **R5 (Medium).** Accepted as written. The reviewer greps `source_ref` in the diff and in every `*_api.py`.
- **R6 (Low).** Accepted: T12 asserts the two paths, and `serve --tree` refuses the 13 Nov tree (T8).

### Implementer

- **I1 (High).** Accepted: W4 unpacks and disposes the read, builds `TenantRef` from the walk database, and takes
  `names` as the route does.
- **I2 (High).** D-WK.11.
- **I3 (Medium).** Accepted: the smoke's `node` env is exactly six names (T8).
- **I4 (Medium).** Accepted: `WalkDeps` (§3.1).
- **I5 (Low).** Accepted: `main.py:693` and exit 69 are fixed in the spec. `ASSETOPS_LIVE_FIELD_*` stays on the deny
  list. The Vite child is WK's own. The packet notes each.
- **I6 (Low).** No change.
