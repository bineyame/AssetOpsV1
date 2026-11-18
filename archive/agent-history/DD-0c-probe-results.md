# DD-0c lever re-probe: results (complete; Â§4 is an estimate, see there)

- Date: 2026-11-06. Implementer (Claude). Brief: `AssetOpsV1-plan2/.agent/brief-DD-0c-levers-probe.md`. Feeds DD-1 R2, R3, P1.
- **Head.** Worktree `AssetOpsV1-dd0c`, branch `task/DD-0c-probe` at plan2 main `7a89f58f0`. Arm-B trees came from a throwaway local commit `f314efab4` (scratch branch, deleted; never pushed or merged). Every A tree reports `code 7a89f58f0`, every B tree `code f314efab4`.
- **Free RAM before:** 3,425 MB (08:19:48). Lane 1's `mechanism_dataset.py derive` (PIDs 4428, 18944) was running at 08:15 and had ended before the first run; no `chain_clone.py`, `mechanism_dataset.py` or probe process was alive at any step start. Lowest free RAM seen: 2,508 MB (Kobo B ticks).
- **Story clock:** `S = 2026-11-04T00:00:00Z`, accepted.
- **Step start times (local):** Kobo A prepare 08:19:56, A drain+ticks 1-2 08:25:18, A ticks 3-5 08:29:09, Kobo B prepare 08:33:21, B drain+ticks 08:35:40, board reads ~08:43, backfill 08:44:09, Cold C1 prepare 08:44:33, Cold add-day attempts 08:45:35 and 08:45:49 (refused, Â§6), profiled Cold run 08:46:34, Cold C3 A 08:48:14, Cold C3 B 08:49:40. Cleanup done 08:53. The longest single step was 285 s; DB work was about 31 min wall in total. Keep-awake was not needed (no step passed 10 min).
- **Cleanup:** `drop` for dd0cka, dd0ckb, dd0cc1, dd0cc3a and dd0cc3b. `pg_database LIKE 'assetops_polish_dd0c%'` returns `[]`. Day lists and the payload were removed from `var/`; the scratch branch was deleted. I did not touch `assetops_demo3_full_test`, `assetops_polish_full_test`, any `assetops_mechanism*_test`, polC or other agents' processes.
- **Evidence copies** (facts and parity dumps, board reads, Cold profile and top-25 tables, memory CSV, scripts): `C:\Users\assef\AppData\Local\Temp\claude\C--Users-assef-Bineyame-AssetOpsV1\809ecc09-3853-48b6-b795-60539b50a963\scratchpad\dd0c\`.

## 1. L1: what seals a batch

1. **Config or hard-coded? Hard-coded, and in the host, not the gateway.**
   - The envelope bound is already the contract maximum: `GatewayService.seal(max_envelopes=MAX_BATCH_ENVELOPES)` (`gateway/assetops_gateway/service.py:996-1005`). The IPC `seal` op takes no parameters (`gateway/assetops_gateway/ipc.py:65`, `:330-331`), and nothing in gateway config or a CLI sets it.
   - What actually sets readings per batch is **when** `seal` is called. `RegisteredGatewayPublisher.publish_in_boundary_order` seals after every boundary group: "Every group is sealed before the next, so the batches do not depend on how the operator stepped" (`host/gateway_publication.py:139-149`, `D-2026-10-09-s2-ordered-publication-and-closing-boundary`). The groups are one per reached source-boundary instant (`host/lab_execution.py:2974-2990`).
   - `seal` then cuts each (source, epoch, snapshot, state) group (`service.py:1017-1019`), so a batch holds one source's envelopes for one instant.
   - The uploader's `batches_per_pass` / `interval_seconds` (`uploader.py`) and the harness's `deliver(50)` loop (`host/tests/test_s6_verification_replay.py:194-240`) only pace delivery.
   - **DD-1 consequence:** L1 is a reviewed **host** change (`gateway_publication.py:146-149`), not a gateway or config change. For arm B I changed only that loop in a scratch commit: admit every group at its own instant as before, then seal once after the last group.
2. **Today's value and the maximum.** Measured here: Kobo **2.06** readings per batch (1,164 batches for 2,394 readings, max 4); Cold **1.04** (94 batches for 98 readings per run, max 2). The contract maximum is 256 envelopes per batch (`contracts/assetops_contracts/ingestion_batch_v2.py:63`, `:202-203`), and the byte bound is enforced by `_fit` (`service.py:1026`). Arm B reached 149.6 per batch (max 256) for Kobo and 12.25 (max 16) for Cold.
3. **Product rules that read batch boundaries:**
   - **Job coalescing.** `_coalesce_job` runs once per batch with that batch's window (`backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py:514-520`) and widens a PENDING job only on overlap (`:645-687`; Cold adds a 10-min bridge, `:658-661`). Measured: `recompute_job` rows are equal (Kobo 407/407, Cold 3/3), but `job.changed` events fall (Kobo 1,607 â†’ 1,229; Cold 51 â†’ 12).
   - **Receipts.** One receipt and one `ingestion_batch` row per batch (`postgres_evidence_ledger.py:691`).
   - **Publications.** `register_run(run_attestation(run, stage))` registers every STAGED batch as a publication (`test_s6_verification_replay.py:235`; `evidence_publication` and `batch_publication_link` 1,164 â†’ 16). The verification outcome's basis lists them (Â§2 parity, difference 2).
   - **`received_at`.** Every batch in a replay is decided at the same overridden instant (`test_decision_clock_override=received`), so no window depends on delivery order.
   - **Watermarks.** Not inspected.

## 2. L1 A/B: Kobo (two-run prepare) and Cold (three-run prepare)

**Deviation from the brief.** "One Kobo normal day" cannot be prepared: `resolve_story` requires both `trial-before` and `trial-after` (`tools/demo_combined.py:106-131`; `next(...)` without a default). So both arms ran DD-0b's K2 day list (`trial-before` S+0d, `trial-after` S+1d). Before the ticks, both arms ran the mini-depth drain that `finish` runs (`drain_mini`, `demo_combined.py:446-461`; 402 jobs each). Without it the tick's mini stage takes only 10 jobs per Site, so the queue cannot reach empty in 4 ticks.

| | Kobo A (seal per boundary) | Kobo B (seal once) | Cold C3 A | Cold C3 B |
|---|---|---|---|---|
| Batches / readings / per batch | 1,164 / 2,394 / 2.06 (max 4) | 16 / 2,394 / 149.6 (max 256) | 282 / 294 / 1.04 (max 2) | 24 / 294 / 12.25 (max 16) |
| Site seconds (manifest) | 266.1 | **104.0** | 66.4 | **31.3** |
| Per-run seconds (folder times) | 123, 121 | **38, 44** | 16.6, 17.8, 16.8 | **5.2, 5.4, 4.9** |
| Ingest (gateway sqlite window) | 111, 115 s | 26, 35 s | 14.7, 16.0, 15.1 s | 3.1, 3.4, 2.9 s |
| Before first run (after migrate) | 32 s | 31 s | 22 s | 24 s |
| Outbox by type | reading.accepted 2,394; job.changed 1,607; assessment.revised 406; foundation.revised 17; action.event 3; price.revised 2; opportunity.revised 2; finding.revised 2; verification.outcome 1 | identical except **job.changed 1,229** | reading.accepted 294; job.changed 51; assessment.revised 6; foundation.revised 1 | identical except **job.changed 12** |
| Recompute jobs | 407 (dispatch 3, mini_backup 130, mini_fuel 129, mini_service 129, mini_renewable 14, mini_opportunity 2) | 407, the same split | 3 | 3 |
| Mini drain | ~63 s | 66.2 s | â€” | â€” |
| Ticks to `snapshot_dirty = 0` | 3 (84.0, 77.0, 56.9 s); ticks 4-5 changed nothing (54.2, 57.9 s) | 3 (87.8, 62.4, 61.0 s) | not ticked | not ticked |
| `snapshot_dirty` after each tick | 227 â†’ 27 â†’ 0 | 227 â†’ 27 â†’ 0 | | |
| Snapshot rows after the drain | 147 | 147 | | |

- **`snapshots` consumer.** It held at 8 unconsumed events after every tick in both arms, with no change over ticks 3-5. My loop's stop rule required 0, which is why A ran 5 ticks.
- **Tick stage ms** (top stages from `assetops.perf`):
  - A: t1 51,239 total (opportunity 13,211; chain_snapshots 9,798); t2 46,665 (chain_snapshots 21,481); t3 29,169 (chain_snapshots 6,092).
  - B: t1 54,598 (opportunity 12,830; chain_snapshots 9,965); t2 36,136 (chain_snapshots 12,238); t3 34,272 (chain_snapshots 7,025).
  - Stage peak RSS was 68-81 MB in both arms.
- **Memory peaks** (sampler; py WS is the sum of all python processes, PG is the whole container, which also hosts other agents' DBs):

  | Step | py WS peak MB (first sample) | PG MiB peak | Min free MB |
  |---|---|---|---|
  | Kobo A prepare | 576 (264) | 1,045 | 3,091 |
  | Kobo A drain+ticks | 400 (263) | 1,047 | 2,634 |
  | Kobo B prepare | 336 (29) | 996 | 2,868 |
  | Kobo B drain+ticks | 244 (66) | 991 | 2,508 |
  | Cold C1 + profile | 356 (181) | 968 | 3,346 |
  | Cold C3 A/B | 376 (201) | 986 | 3,324 |

**Parity.** Each value was normalised as follows: asset, source, site and gateway UUIDs mapped to their codes; other UUIDs to `<uuid>`; 64-hex digests to `<sha>`; probe-day wall timestamps to `<now>`. The rows were then compared as multisets.

- **Kobo, equal:**
  - every `site_day_snapshot` row (147: measure, subject, grade, value, money, coverage) and every snapshot `revision` number;
  - every `finding_revision` (2: lifecycle, transition, claim level, episode, minutes, claim, limitations);
  - `finding` (1);
  - `assessment_revision` heads (3), with their keys, windows and claim levels;
  - `mini_depth_revision` (402);
  - `verification_metric` (12);
  - `trial_cost_comparison_revision` (1);
  - `financial_consequence_revision` (2);
  - `action_event` (3);
  - **the Kobo board read**: the one-day Finding index through the real router, as `trial_day_index` reads it, for 3, 4 and 5 Nov (UNASSESSED, CURRENT, CURRENT). Zero differences.
- **Kobo, different (verbatim, not explained away):**
  1. `mini_opportunity_revision` (2 rows): only `selection_seq` values differ.
     - Row 1, 7 entries: `[102] A 7 / B 8`, `[103] 6/13`, `[104] 5/22`, `[105] 4/7`, `[106] 3/12`, `[107] 2/19`, `[108] 8/3`.
     - Row 2, 14 entries: the same seven at `[78..84]`, plus `[101] 383/368`, `[102] 379/369`, `[103] 372/398`, `[104] 375/370`, `[105] 387/371`, and 2 more.
     - `local_day`, the windows, `evidence_ids` and `mini_revision_id` are equal.
  2. `verification_outcome` (1 row): the outcome is equal (`VERIFIED`, `TARGET_AND_GUARDRAILS_PASS`, the same metrics).
     - The basis differs in `source_resolutions.baseline.publication_ids` and `.later.publication_ids` (**A 74 / B 6** each) and in `sources.baseline/later.publication_ids` (74 / 6).
     - The `runs[0].run_id` values also differ (`run-fecec1d4â€¦` / `run-0bc4f9e0â€¦`, `run-9c29159dâ€¦` / `run-df5ecbacâ€¦`). Run IDs are minted per run.
     - The outcome's `plan_sha256` differs too (`81a6c65câ€¦` / `aa0321edâ€¦`). It was normalised away as a digest above.
- **Cold C3, equal:** `assessment_revision` keys, windows and claim levels (6). `cold_episode*` row counts are equal (3 / 30 / 3).
- **Cold C3, different (verbatim):**
  - One head, `cold-start-response:2026-11-02T16:00â€¦17:05`: `links[8].reason A "POWER_RESTORED" / B "TRANSFER_RESULT"` and `links[9].reason A "TRANSFER_RESULT" / B "POWER_RESTORED"` (also under `chains[0]`).
  - Observation only: in all six heads these two links appear in ascending `evidence_id` order (A `5df45816` < `79c9c0d2`; B `98c0b472` < `c61b060c`). The other two B days match A.
- **Verdict for the Architect:** the measures, findings, assessments and board read are equal. Differences 1-2 (Kobo) and the Cold link order are listed for ruling.

**Backfill** `python -m assetops_backend.chain.backfill --steps a,b,c,d` on the Kobo B DB (after the drain):
- **5 s.**
- a: considered 12, written 0;
- b: ALREADY_PLACED 2, written 0;
- c and d: written 0, one thread RESOLVED_MONITORING.

## 3. One Cold normal run under cProfile (child command directly)

- **Run.** `demo_combined_cold.py add-day` on the C1 DB, day S+1d (2026-11-05), epoch `day-12`, with the tool's child environment.
  - Profiled wall: **25.2 s** (rc 0); `run_day` 24.2 s.
  - Unprofiled references at this head: the C3 A runs were 16.6-17.8 s (DD-0b: 22.6 s).
- **Readings and batches.** 98 readings in **94 batches**; `ledger_service.submit` was called 94 times (cumulative 9.0 s).

| Bucket | Functions | Profiled s | Share of `run_day` |
|---|---|---|---|
| Per-run fixed | imports via `demo_combined_cold._patch` 5.9 (test-module import 5.6); `open` (fresh gateway, install, draft) 0.5; `attest` 0.3; host `start` 0.4 | ~7.1 | 0.29 |
| Ingestion (per batch) | `release_and_upload` 15.8: 97 POSTs `fake_central.do_POST` â†’ `forward` 11.3 (the ledger `_run` 658 calls 10.9; asyncio runner `close` 6.4 over 97 calls); `submit` 9.0 (`decide_chunk` 3.3, `register_publication` 2.1, `open_batch` 1.95, `receipt` 0.98, `_persist` 0.87 for 98, `_coalesce_job` 0.69); TLS `do_handshake` 97 calls 1.1 | 15.8 | 0.65 |
| Assessment and match | `produce` minus upload, open and attest | ~0.3 | 0.01 |

- **Answer.** Cold's run cost is mostly **per-batch** ingestion (about 0.17 s per batch, about 1 reading per batch), not per-run fixed cost. L1 is the primary lever for Cold as well. C3 B confirms it: 5.2 s per run against 17.1 s (ratio **0.30**).
- **Top-25 tables** (cumulative and tottime): `scratchpad\dd0c\top-cold.txt`; the profile is `dd0c-cold-run.prof`.

## 4. L2: Cold steady day as one 24 h run (estimate; the prototype is not data-only)

- **What data alone can do.** The scenario parser has no length cap: it checks only `start < end` (`backend/assetops_backend/scenarios/cold_parsing.py:166-169`). It accepts an empty `forcings` list (`:176-198`).
- **Why that is not enough.** The Cold replay path fixes the evidence and assessment window in code, so a 24 h scenario file alone would still be assessed over 65 min:
  - `WINDOW_MINUTES = {"ordinary": 65, â€¦}` and `window_end = start + 65 min` (`tools/w502_cold_work_cases.py:56`, `:144`);
  - `BASE_RELEASE` = start + 70 min (`:49`);
  - `produce` branches on `window_end == start + 65 min` (`backend/tests/test_w502_cold_scenario_producer.py:149`).
- So, following the brief, this is an analytic estimate. **Snapshot-grade equivalence is not proven.**
- **The estimate** for one 24 h run with L1:

  `fixed_nongateway + readings Ã— per_reading + assessment` = 2.0 + 2,178 Ã— 0.032 + 6.7 = **78 s per day**

  This compares with 22.2 short runs under L1 at **115 s per day**, and 502 s per day without levers (DD-0b).
  - **Measured inputs:**
    - C3 B: 5.17 s per run, gateway window 3.13 s per 98 readings, so 0.032 s per reading;
    - 98 readings per 65-min run.
  - **Assumed inputs:**
    - readings scale linearly to 24 h (2,178);
    - the non-gateway per-run part, 2.0 s, is paid once;
    - assessment and match scale linearly from the profile's ~0.3 s per run;
    - the seal fits 256 per batch.
  - Upper bound: Ã— 22.6/17.07 (the DD-0b load factor) = **104 s per day**.

## 5. B-22 extrapolation (DD-0b Â§7 formulas, lever values in place)

**Inputs:**

- **Unchanged from DD-0b:** `tree` 17.9 s; `finish` 90 s; Kobo fixed 27 s; Cold fixed 16.6 s; EV fixed 21 s and `day_ev` 368 / 766 s (EV has no lever measured, so it is conservative).
- **Kobo `per_run`:** central **41.0 s** (B measured); upper 136.8 Ã— 41.0/122.0 = **46.0 s**. So `day_kobo` = 123.0 / 137.9 s.
- **Cold `per_run`:** central **5.17 s** (B measured); upper 22.6 Ã— 0.303 = **6.84 s**. So `day_cold` = 114.8 / 152.0 s with L1. With L1 and L2: 78.3 / 103.7 s (Â§4 estimate).
- **Drain-to-empty add-on (not in the DD-0b formula):**
  - mini drain, measured at 32 s per Kobo day;
  - snapshot ticks, an unmeasured allowance of 900 s at B-22 (pro rata for B-16).
  - Together: 1,611 s at B-22 and 1,171 s at B-16.
- **Backfill** a-d measured 5 s here; at B-22 scale it is not measured.

| Option | Kobo s (c / u) | Cold s (c / u) | EV s (c / u) | **Sequential** central / upper | **+ drain** central / upper |
|---|---|---|---|---|---|
| **B-22, L1** | 2,733 / 3,061 | 2,543 / 3,361 | 1,125 / 2,318 | **6,508 s (1.81 h) / 8,848 s (2.46 h)** | **2.26 h / 2.91 h** |
| B-22, L1 + L2 (estimate) | 2,733 / 3,061 | 1,740 / 2,299 | 1,125 / 2,318 | 5,706 s (1.58 h) / 7,786 s (2.16 h) | 2.03 h / 2.61 h |
| **B-16 fallback, L1** | 1,995 / 2,234 | 1,854 / 2,449 | 757 / 1,552 | **4,714 s (1.31 h) / 6,343 s (1.76 h)** | **1.63 h / 2.09 h** |
| B-16, L1 + L2 (estimate) | 1,995 / 2,234 | 1,270 / 1,676 | 757 / 1,552 | 4,130 s (1.15 h) / 5,570 s (1.55 h) | 1.47 h / 1.87 h |
| (DD-0b, no levers) B-22 | 9,058 | 11,065 | 1,125 / 2,319 | 21,356 s (5.9 h) / 22,550 s (6.3 h) | â€” |

- **Against the 3 h cap.** B-22 with L1 alone projects to **1.8 h central, 2.5 h upper** by the DD-0b formula, and **2.3 h / 2.9 h** with the drain add-on.
  - It fits 3 h on every row. The upper-with-drain row leaves about 5 min of margin, and that margin rests on the unmeasured 900 s tick allowance.
  - L2 adds about 18-20 min of margin.
- **B-16 fallback:** 1.3 h / 1.8 h, or 1.6 h / 2.1 h with drain.
- **Conditional on parity.** All lever figures depend on L1's parity differences (Â§2) being accepted.

## 6. Refusals and deviations (verbatim)

- **One Kobo day not preparable.** `_trial` needs both trial kinds (`tools/demo_combined.py:110`), so A/B used the K2 list (Â§2).
- **Mini drain before the ticks** in both arms (Â§2). It is not in the brief's sequence.
- **L1 is hard-coded in the host** (`host/gateway_publication.py:146-149`). Arm B used a scratch commit `f314efab4`, created on a throwaway branch, built into the B trees via `git archive HEAD`, and then deleted. DD-1 needs a reviewed host change, not a gateway or config change.
- **Cold add-day before the latest delivered Cold day is refused** (S-1d and S-2d after an S+0d prepare):
  `Provisioning failed: (psycopg.errors.CheckViolation) new row for relation "gateway_credential" violates check constraint "gateway_credential_revocation" ... (2026-11-04 12:00:00+00, 2026-11-02 12:00:00+00) ... [SQL: UPDATE gateway_credential SET revoked_at = %(at)s WHERE gateway_id = %(g)s AND revoked_at IS NULL RETURNING selector]`.
  - The profiled run therefore used S+1d.
  - This bears on DD-1 fill-any-day (FILL-1) for Cold.
- **Cold C3 A/B was added beyond the brief** (two short prepares, about 2 min) to measure Cold `per_run` under L1 rather than assume it.
- **The PG container peak** includes other agents' DBs (about 1 GB, against about 370 MiB in DD-0b).
- **Sampler CSV.** The thousands separators split its columns, so peaks were re-parsed from the raw lines.
- **Board normalisation.** The CH3-R A/B normalisation was not found as code. Normalisation here is Â§2's UUID, digest and now mapping.
