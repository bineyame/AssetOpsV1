# 3C1a and 3C1b reviewer guide (rev 2: handshake round 1 folded in; review each unit separately)

You are the fresh Reviewer.
- **At the handshake:** read `spec.md`, `rulings.md` and this guide, and write your questions in `handshake.md`.
- **At the review:** the depth is discovery (W5).

## First checks

1. **Scope.** Compare the diff with spec §7.6's list.
2. **Today's path unchanged.** The existing files listed in spec §6 pass without edits. Diff every service and adapter
   line by line: with no person, the bytes written must be identical.
3. **The migration** widens only what §4 names. It refuses the upgrade on a planted USER row.
4. **Module path.** The packet shows the worktree.

## Probes

- **P1 Browser actor.** Signed in as Peter (SITE_MANAGER at Kobo), POST a work case whose body names a SERVICE
  actor: 422.
- **P2 Site binding.** Peter posting to Kisiwa: 403 `PERSON_ROLE_REQUIRED`.
- **P3 Tenant.** A Harvest Cold person posting to Kobo: the route's 404, with no row written.
- **P4 Database.** Raw SQL inserting `actor_kind='USER'` without `person_id` fails. Inserting `person_id` with
  `SERVICE` fails.
- **P5 Switch.** With `ASSETOPS_REQUIRE_PERSON=on` and no cookie, every command of the unit answers 401
  `PERSON_REQUIRED`.
- **P5b Nothing opened** (D-3C1.12).
  - With no work principal composed, a signed-in person gets 403 `WORK_WRITE_FORBIDDEN`.
  - With the entry switch off, the entry route refuses a person too.
  - 3C1b: a Finding outside the grant file is refused as today.
- **P5c Hash.** The same person in a new session replays with 200. A second person with the same key gets 409.
  3C1b: a second person's identical accept gets 409, never a replay.
- **P6 Attestation.**
  - The stored attestation and basis equal spec §2's forms, per table.
  - Domain tables have no basis, and `action_event` has no attestation.
  - The admitting role is the first match in the order of `COMMAND_ROLES`.
  - `actor_id` equals `person:` followed by `person_id` (the database checks this).
- **P7 Reads.** Event and work reads are byte-equal for SYSTEM and SERVICE rows, and `person_id` is not in
  `EVENT_COLUMNS`. A USER label reads "Recorded by a signed-in person", with no name.

## Class sweeps (W6)

- If one command misses the person step, check all 13.
- If one table lacks the FK or CHECK, check all ten.

## Risks

- `3C0b` will turn the switch on. Check that nothing else depends on it being off.
- The verification and decision paths stay system or service paths (D-3C1.3). A person cannot reach them through a
  side door.
