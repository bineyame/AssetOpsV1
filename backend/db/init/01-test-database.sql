-- Disposable test database on the development service. Tests run every
-- migration from zero here and never touch the developer database.
CREATE DATABASE assetops_test OWNER assetops;
-- T1b (D-T1.19, D-T1.26): the second Postgres test lane's base database (tools/heavy-slot.sh --db-lane).
CREATE DATABASE assetops_b_test OWNER assetops;
