# Owner: approve the RC4-F1 guard line (2026-11-20)

The coordinator asked: may one allow-list line be added to `tools/checks/configuration-persistence.ps1` (`$pgReaders`), admitting `backend/assetops_backend/database_target.py` to import only `make_url` from the database library (it parses a connection address exactly as the driver does and never connects; D-RC4F1.3)? The builder's own attempt was refused by the session's permissions, so the coordinator asked the owner instead of making it. A new test pins the admission narrow.

The owner replied, verbatim:

> yes, add the line
