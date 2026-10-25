# Owner authorization: three producer test DBs (2026-10-25)

Owner, verbatim: "yes, allow creating those three test databases"

Scope: create and drop `w301cap_test`, `w302j_test`, `w402r_test` in `assetopsv1-postgres-1`, as hard-coded by the unmodified W3-01 `serve.py`, W3-02 `serve.py` and W4-02 `seed.py` producers, to recapture post-W6 shell batches 10-12 (24 pairs disclosed as gaps under `.agent/post-W6-shell-closeout-rulings.md` ruling 4). Context: the permission classifier refused `CREATE DATABASE w301cap_test` although it falls under the 2026-10-18 `*_test` authorization. Producers run unmodified; no wrappers or renaming. Drop each DB after use. No other DBs.
