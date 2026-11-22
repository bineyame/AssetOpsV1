# Decision index: Demo-sprint and later rulings (index only) (D-DD.108 to D-DD.116, D-T1.19 to D-T1.26)

- `D-DD.108` DD3c Q1, Q6-Q8 accepted: roles-4 and roles-5 counted together (both = no work), TEL_FOUNDATION mapped to existing refusals, units in detail fields, event ties by Foundation order · live · specs/DD-demo-data/rulings.md
- `D-DD.109` DD3c Q2: migration 0074 with exact-count replacements, MINI_DEPTH_ROLE_SETS constant, gate reaches S1-S2/P1-P5 (incl. ROLES_BY_SET from served sets), parity tests T1-T7 · live · specs/DD-demo-data/rulings.md
- `D-DD.110` DD3c Q3, Q10 accepted; Kisiwa's v8 replay refusal is honest output; v9 replay to backlog · live · specs/DD-demo-data/rulings.md
- `D-DD.111` DD3c Q4 amended: Site state RUNNING if any known unit runs, else absent if any unit silent, else D-DD.41's cascade · live · specs/DD-demo-data/rulings.md
- `D-DD.112` DD3c Q5 and open point: installed and available rating are two functions; all units FAILED = 0 kW available, not absent · live · specs/DD-demo-data/rulings.md
- `D-DD.113` DD3c Q9: Kisiwa's NOT_ONE_EACH litres is a gap; litres split per unit in DD3c; fuel_basis checked against DD5's path, else backlog · live · specs/DD-demo-data/rulings.md
- `D-DD.114` DD3c Q11: Kobo-only move to roles-5; parity in two fresh states, normalised (UUIDs, role-set name), four outputs · live · specs/DD-demo-data/rulings.md
- `D-DD.115` DD3a W6 sweep: generator, site.code, mini-grid months, EV day_classes/families stay in the scope digest; no re-draw before the demo · live · specs/DD-demo-data/rulings.md
- `D-DD.116` DD3c 2.5 -> 3.25 u in five parts (survey +0.25, litres per unit +0.5); DD 44.0 u · live · specs/DD-demo-data/rulings.md
- `D-T1.19` T1b Two DB lanes: db-job.lock with assetops_test, db-job-b.lock with assetops_b_test · live · specs/T1-heavy-tool-slot-pool/rulings.md
- `D-T1.20` T1b --db takes both lanes (one heavy DB job at a time); --db-lane takes one (amends D-T1.4) · live · specs/T1-heavy-tool-slot-pool/rulings.md
- `D-T1.21` T1b Lane markers, acquire order, nested refusals (amends D-T1.13) · live · specs/T1-heavy-tool-slot-pool/rulings.md
- `D-T1.22` T1b Host Postgres pytest needs a lane and the lane's _test database, refused at configure time (revises D-T1.16) · live · specs/T1-heavy-tool-slot-pool/rulings.md
- `D-T1.23` T1b run-host-tests picks the lane's database URL · live · specs/T1-heavy-tool-slot-pool/rulings.md
- `D-T1.24` T1b What stays shared; _case_db names stem-derived; CREATE DATABASE inventory · live · specs/T1-heavy-tool-slot-pool/rulings.md
- `D-T1.25` T1b No new capacity: a lane holds a T1 slot; lane runs at most -n 2 · live · specs/T1-heavy-tool-slot-pool/rulings.md
- `D-T1.26` T1b Second database created by idempotent createdb, not migrated; 1.0 u · live · specs/T1-heavy-tool-slot-pool/rulings.md
