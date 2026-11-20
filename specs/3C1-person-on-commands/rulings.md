# 3C1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-7.md`. Handshake
answers go below, under "Handshake answers (round 1)".

## D-3C1.1 The person path is added beside today's path, behind one switch

- **Ruling.**
  - When a person is signed in, the command goes through the person path.
  - When no one is signed in, the command goes through today's path, unless `ASSETOPS_REQUIRE_PERSON=on`.
  - The switch ships off. `3C0b` turns it on.
- **Why.** D-BW1.3 holds the refusal until the sign-in page exists. A switch built and tested now makes `3C0b` a
  configuration change, not new code.

## D-3C1.2 Role per command is one literal table

- **Ruling.** `COMMAND_ROLES` maps each command to its roles, taken from `decision-loop-specification.md` §8. A
  Site manager's grant counts only for its own Site.
- **Why.** The design's permission table is the source. One table makes it configurable by role later, as the owner
  asked on 20 Nov (item 5), with no code spread across routes.
- **Owner's view welcome.** Whether a field technician may raise a work case. The default is yes: incidents are found
  in the field.

## D-3C1.3 Verification, financial and decision writes keep their paths

- **Ruling.** Verification steps, price entry and the mini, cold and EV decision writes are not in 3C1.
- **Why.**
  - Verification steps are the system's own work until the three verdicts (`8a`). The design says the system records,
    and a person does not.
  - Price entry is a setting, which needs step 7b's thresholds.
  - Decision writes are rebuilt in `6a`, on the new decision records.
  - Changing them now would be changed twice.

## D-3C1.4 The person is in the command's identity

- **Ruling.** The actor stays in the command hash.
- **Why.** Two people sending the same body are two commands, each recorded under its person. Merging them would hide
  one person's act.

## D-3C1.5 `USER` is the person's actor kind everywhere

- **Ruling.** The actor kind is `USER`, with `person_id` and `actor_id` `person:<uuid>`. The database enforces that
  `USER` holds exactly when `person_id` is set.
- **Why.** The W4 and decision tables already use `USER`. One word across tables keeps reads simple, and the
  constraint makes it impossible to record a "user" without a person.

## D-3C1.6 A cross-tenant person sees "not found"

- **Ruling.** A signed-in person of another tenant gets the route's not-found answer.
- **Why.** It is the same answer as for a Site that does not exist, so the answer reveals nothing about another
  operator's Sites (the 3C0a isolation rule).

## D-3C1.7 The split if the handshake grows it

- **Ruling.** If the pre-flight finds more than 4 units of work, the slice splits:
  - `3C1a`: work and domain commands;
  - `3C1b`: trial actions.
  The migration splits the same way.
- **Why.** W4 sets a limit of 6 units. The action tables carry the strictest CHECKs, so they are the part most likely
  to grow.
