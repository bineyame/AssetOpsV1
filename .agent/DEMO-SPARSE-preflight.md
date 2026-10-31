# DEMO-SPARSE pre-flight (build sheet `AssetOpsV1-plan2/.agent/build-sheet-DEMO-SPARSE.md` §9)

Worktree `-demo3`, branch `task/DEMO-A-combined-dataset`, head `50cbc02be`, 2026-10-31.

- [x] Clean tree; `git ls-files --eol` shows no `w/crlf` on `eol=lf` files.
- [x] PYTHONPATH / interpreter / DB names / no `-ExecutionPolicy` / no BOM / keys / keep-awake / no `datetime.now()`
  for story instants: as the sheet states.
- [x] `pgb.imported(store, code, when=)` (`backend/tests/test_s1_bindings_postgres.py:88`), `pgb.Clock` (`:58`),
  `pgb.FIXTURE` (`:52`), `convert` and `BindingService` via `pgb.convert` / `pgb.BindingService` (module imports
  `:38-43`, from `assetops_backend.sites.binding_conversion` / `.binding_service`). No test-module edit needed.
- [x] Register: `| R61[5-9] ` count 0.

## Question (one, sent to the coordinator)

Q1. Code reality the sheet's §1 does not list: `pub.configure` (`host/tests/test_s6_verification_publication.py:82-87`)
publishes the two demo configurations at a fixed knowledge clock `CONVERTED_AT + 10 min` = 2026-10-07 11:40
(`backend/tests/test_s1_bindings.py:33`, `test_s1_cutover.py:47`), and the fixtures carry fixed effective dates:
generator properties 2026-10-01, roles-2 bindings 2026-10-02, roles-3 (capability + critical-load channels)
2026-10-12 (`backend/conversions/kobo-001-s3-dispatch-demo-config.json:7,18`,
`kobo-001-s6-verification-demo-config.json:7,18`). With install at S−29 (2026-09-30 for S = 10-29), Kobo days
before 2026-10-13 (S−28, S−21) run on a Foundation without the generator values or roles-3 channels, and for any
later S (2027-03-01) the fixed dates fall before install. Proposed default: call
`apply_demo_configuration` directly (no test-module edit) with in-memory copies of both fixtures whose
`effective_from` values are re-timed to install_at + 10 min (properties, roles-2) and + 20 min (roles-3), knowledge
clock install_at + 30 min; values unchanged. U1 P4 records what the unmodified path does.


## Ruling Q1 (Architect: Claude, `.ai/ROLE_CONFIG.md:9`, 2026-10-31): ACCEPT the proposed default, with conditions

- **Why accept.** The fixed dates (properties 10-01, roles-2 10-02, roles-3 10-12) record when the S3 and S6 features
  were built. They are not events in the Site's story. In the story, the Site is commissioned with its full channel
  set before its first assessed day. If roles-3 were staged relative to the trial (for example S-1), then S-28..S-3
  would run without the capability and critical-load channels. Those days would not be assessed on the same basis as
  S and S+1: the S-28 On track, the S-21 "weather explains the generator" control and the S-14/S-7 overuse beats
  could not honestly show what the calendar claims, and the month would mix two channel sets. Putting roles-3 at
  install +20 min gives every story day the same Foundation. That is the more honest comparison.
- **Conditions.**
  1. Values are byte-identical to the fixtures; only `effective_from` moves. Both fixture files stay unchanged on
     disk, with no test-module edit, and their "SIMULATED DEMO CONFIGURATION" label is carried on the copies.
  2. Keep the order properties = roles-2 (install +10 min) < roles-3 (+20 min) < knowledge clock (+30 min). All of
     them must be at least 1 h before the earliest day run's start; otherwise `INSTALL_CLOCK_CONFLICT`.
  3. Every run's `foundation_known_at` is at or after install +30 min (already true: D-1d 12:00).
  4. `kobo.json` records the re-timed effective dates and the knowledge clock. U1 P4 also records what the
     unmodified `pub.configure` path does, for the packet.
- No register row: nothing changes on screen. The Foundation history page shows the commissioning dates at install,
  which is consistent with the story.
