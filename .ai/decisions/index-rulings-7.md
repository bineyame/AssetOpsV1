# Decision index: Demo-sprint and later rulings (index only) (D-BW1.1 to D-3C0A.10)

One line per decision ID: ID, title, status, file. Status is `live` unless a later decision text supersedes it. Top index: `INDEX.md`.

- `D-BW1.1` First non-screen wave: lane A 3C0a, lane B 2a (P2 pending; DS2 fills the gap); step 1 is screen · live · specs/BW1-build-wave1/rulings.md
- `D-BW1.2` Screen vs non-screen (a changed figure counts); 15 screen slices held for the UI review · live · specs/BW1-build-wave1/rulings.md
- `D-BW1.3` 3C0 split into 3C0a (API) and 3C0b (screens); 3C1's refusal switches on with 3C0b; 3C0a inside the start · live · specs/BW1-build-wave1/rulings.md
- `D-BW1.4` 0K split into 0K1 (port and adapter) and 0K2 (Kobo replays); 0M, 0E, 6c need 0K1; 9d, 9e split at P9 · live · specs/BW1-build-wave1/rulings.md
- `D-BW1.5` Data slices as step D with D-DS1.14 units; 3B7a, 3B7b in 3B; 4c and DS7 queued with triggers · live · specs/BW1-build-wave1/rulings.md
- `D-BW1.6` Re-cut inputs: day 1 = 20 Nov, 2 lanes, 0.1 lane-day handshake, must-keep first on short lanes · live · specs/BW1-build-wave1/rulings.md
- `D-2A.1` Canonical format in assetops_contracts.canonical, standard library only · live · specs/2a-canonical-format/rulings.md
- `D-2A.2` The format is a protected seam; a change is a new version · live · specs/2a-canonical-format/rulings.md
- `D-2A.3` Leaf IDs are the manifest factor_map keys (73, 4 shared); filling rules stay in the registry · live · specs/2a-canonical-format/rulings.md
- `D-2A.4` Six dimensions; counts dimensionless; nights are days; literal units ruled in 3B1 · live · specs/2a-canonical-format/rulings.md
- `D-2A.5` A budget line may name a node; currency rule checked for catalogue leaves only · live · specs/2a-canonical-format/rulings.md
- `D-2A.6` SERVICE_TICKET is an operational record; BUDGET_LINE replaces PLAN_LINE (OD-6) · live · specs/2a-canonical-format/rulings.md
- `D-2A.7` Readings and fuel records keep their existing formats · live · specs/2a-canonical-format/rulings.md
- `D-2A.8` world/leaves.py switches in DS1b, not 2a · live · specs/2a-canonical-format/rulings.md
- `D-2A.9` Exact decimal text with the DS1 magnitude bound; no JSON numbers · live · specs/2a-canonical-format/rulings.md
- `D-3C0A.1` Accounts behind the API now; no existing route or command changes · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.2` Append-only records, revoke-only sessions; current state derived · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.3` Email unique across tenants; sign-in needs no tenant · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.4` Manifest role codes; only SITE_MANAGER carries a Site · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.5` The tenant keeps one executive, under an advisory lock · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.6` One refusal for every failed sign-in; dummy hash; lockout 5 in 15 min · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.7` Onboarding creates people; only the first executive gets a role from it · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.8` Demo people's accounts come with WK, after 3C0b · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.9` The 3C1 seam is accounts.principal.person_from_request · live · specs/3C0a-operator-accounts/rulings.md
- `D-3C0A.10` Standard-library scrypt; no new dependency · live · specs/3C0a-operator-accounts/rulings.md
