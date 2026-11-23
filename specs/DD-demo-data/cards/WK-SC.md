# Build card: WK-SC, the story clock

Part WK-SC = three units, **3.0 u** (D-DD.172; owner O1 approved the clock at 2.0 u, and the owner has been told of
the 3.0), branch `task/WK-SC-story-clock`, one discovery review. Spec: `specs/DD-demo-data/spec-WK-SC.md` (W).
Rulings: D-DD.135, D-DD.137, D-DD.168 (the check it reuses), D-DD.172, D-DD.173 (`rulings.md` R3379-3421 as at
`task/DD-cards-2`). Read W whole (it is the binding part), then the code. A question W does not answer stops only the
affected unit and goes to the lane Architect; count it in the packet.

## What you build

1. **WK-SC.1 The clock and its wiring (1.25; W §1, §2, §3.1, §4).** `prepare_clock.story_anchor`, `story_clock`,
   `world_clock`, `STORY_ACT_COLUMNS`. The world-time compositions (agreed actions, decisions act times, evaluation
   `run_at` split from `known_at`, verification `today`, the deep-dive agreed-list `today`). `main.create_app` fails
   fast. `GET /api/clock`. The W/S sweep table of every clock read in the packet.
2. **WK-SC.2 The workflow and the serve (1.25; W §3.2, §3.3).** Walk definition `/2` `story` and
   `WALK_STORY_MISMATCH`. `workflow_plan`: 6h §7's ten decisions, `M`'s nine Actions, D-DD.173's seven choices, one
   world instant per step (`story.now + k s`). The manifest's `workflow` list. `M` `proposed_by` and
   `check_manifest.py` `workflow()`. The serve anchor.
3. **WK-SC.3 The screen's calendar (0.5; W §3.4).** `ui/clock.ts`, `main.tsx` awaits it, `sharedRange.ts` defaults
   to `appNow()`, the frontend W/S sweep. No new element or word.

## Facts the code fixes (D-DD.162)

- Protected: every system-time site (W §1) is unchanged, and with `ASSETOPS_STORY_NOW` unset every behaviour is
  byte-identical to main (tests pin it). The owner's walk, ports 5490/8990/8992 and the development database are
  untouched. Production composition sets no story clock.
- Names: people, titles, due dates, option keys and values come from `M` and `structure/levers.py`; the item →
  (Site, lever, option) map is D-DD.173's table, and nothing else is typed.
- Decimals: one-off amounts and option records are passed as `M` prints them (at most 2 decimals for money);
  compared as `Decimal`.
- Ids: decision, Action and choice ids are the product's; a re-run finds them (`already_*`); the Finding id is
  read from the walk database, never formed.
- Tests: nothing under `backend/` imports `gateway`, `host`, `simulator` or `tools`; walk tests live in
  `backend/tests/test_wk_walk_world.py` as today (it already runs the tool as a subprocess).

## Tests and plants

W §5 and §6.

## Reach set

`test_3c2_agreed_actions{,_postgres}.py`, `test_6a_decisions{,_postgres}.py`, `test_6a_migration_postgres.py`,
`test_6c_*`, `test_6h_*`, `test_5c_deep_dive_*`, `test_k6b_fuel_verification_rules.py`, `test_s6_*`,
`test_wk_walk_world.py`, `test_ds4_world.py`, tests importing `prepare_clock` or `demo_story_clock`, the frontend
`ui/` and `estate/` vitest files reading `sharedRange`, `check_manifest.py`. Guards: statement catalogue,
`check-decision-index.py`, `check-agent-workflow.ps1`, the architecture guard (route list for `/api/clock`).
Postgres through `tools/heavy-slot.sh --db-lane`; vitest only through `tools/heavy-slot.sh`.

## Merge order and shared files

- Starts after DD6 (walk `/2`, `prepare`, `serve`) and DD3d-a (`prepare_clock.py` widened) are on main.
- Shared: `tools/walk_world.py` (DD6 → WK-SC), `prepare_clock.py` (DD3d-a → WK-SC), `M` and `check_manifest.py`
  (DD3d-b → WK-SC), `frontend/src/ui/sharedRange.ts` (IA-P → WK-SC; merge main first).
- After merge, DD6's C8 pending lines drop "WK-SC" (D-DD.174); the coordinator re-runs `walk_world.py prepare` on a
  fresh walk copy.
- Evidence under `/opt/assetecon/evidence/WK-SC/`.

## Done when

W §7's five gates hold. Packet: mid-build question count, the W/S sweep table (backend and frontend), each workflow
step's exit or refusal code, the serve anchor, every moved pin.
