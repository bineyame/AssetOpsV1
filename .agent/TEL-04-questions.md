# TEL-04 builder questions (2026-10-27)

Items the spec does not cover. Each is left unhandled in code (no design chosen); the Architect decides.

**TEL-04-Q1. Gateway unavailable before START.** `GatewayUnavailable` from `identity` (check_identity) or from `release_previous` is not mapped to an exit code (exit 4 is defined only "at 10 consecutive publish instants"). Today it propagates: traceback, exit 1, no START. Should it be exit 4, exit 2, or a retry?

**TEL-04-Q2. Gateway unavailable at the final seal.** After `--stop-at` the poller calls a final `seal_and_release`. A `GatewayUnavailable` there propagates (exit 1, no EXIT line). Exit 4? Retry?

**TEL-04-Q3. Retained texts at `--stop-at`.** If the last publish instant(s) hit `GatewayUnavailable`, the retained texts are not admitted before the final `seal_and_release` (the spec names only the seal). They are counted in `status.retained_reports` and lost. Should the final step admit the retained texts first?

**TEL-04-Q4. EXIT line on exit 2.** Configuration refusals before START print only to stderr; no `FIELD-POLLER EXIT 2 ...` line (there is no status file yet). Exit 3/4 after START print EXIT with the status. Confirm.

**TEL-04-Q5 (confirm interpretation, implemented).** Gate 7 says the harness reads diagnostics "just before" the pause. The PV interval ending at the pause start (07:15Z) can only be admitted after 07:15Z (its publish instant), so a read strictly before the pause would see PV contact move. The harness reads after the last pre-pause publish (`status.last_publish_instant == 07:15Z`) and again >= 3.5 s wall later. Confirm.
