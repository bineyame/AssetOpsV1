# S4-02c phase 3: two-leg late-power walkthrough evidence

Tool: `tools/s402c_late_power_walkthrough.py run` (then `drop`), code from `94a62aad` (git HEAD, staged into a
private tree), database `assetops_s402c3walk`, TLS port 8918, http port 8919 (unused: no Lab/gateway case).
Fixture: `backend/conversions/s4-power-late-demo-cases-v1.json` (`P02-power-late`, day 2026-10-24), a
versioned authored demonstration variant of S4-02b P01-power with the 20 kW mean `[07:00, 07:05)` withheld.
`s4-power-demo-cases-v1.json`, the S4 Finding specs and their labels are unchanged. Full machine record:
`.agent/S4-02c-walkthrough-evidence.json` (every command, read, work row, attempt and consequence). All values
below are actual output of the accepted run (run 2); none are illustrative. The database was dropped afterwards.

Reads are fresh processes over Postgres (`ConsequenceReadService.read` + `finding_api.bridge_consequence`, the
API's own services) with `source_open=True`: the Performance source gate is a file-backed comparison this tool
does not run. Drains use the phase 2 runner CLI `recompute_consequences run --tenant demo --site KOBO-001
--limit 100` (Site claim, counts). S3/S4 use `assess_dispatch process-jobs` and `match-findings --tenant-id
--site-id`.

## Run 1 (rejected fixture authoring; kept as a finding)

The first run numbered the late mean after the last sequence of the epoch (sequence 25, after the 08:00 mean's
24). Leg A passed exactly as in run 2. In Leg B, S3 dispatch-3.1 reported `SEQUENCE_ORDER_INVERTED:
generator_power 07:05..08:00` and `GENERATOR_SERIES_AMBIGUOUS`; the revised FindingRevision (`e6f1ddfb...`,
`SUPPORT_CHANGED`) ended at 07:00, its Candidate time `[06:05, 07:00)` excluded the late mean, and its consequence
was PRICED over 11 means (6.05 L, 7.5625 USD). Check "r2 counts the late mean" FAILED (1 of 21). A store-and-forward
gateway numbers a reading when it takes it, so the variant now carries `power_rules.sequence_rule =
SOURCE_ORDER`: the first delivery leaves a gap at sequence 14 and the late delivery fills it (`94a62aad`). This
is a fixture authoring correction (the late mean's identity), not a change to force Leg A; N5 passed in both
runs. Run 1 IDs: Finding `14a518ba-2538-4d6d-929b-0ac0ca7c3468`, r1 `5cdb19ca-866d-422c-90c3-7524cde49229`, late
evidence `92260312-294f-435d-a6cd-808da0e0f0f8`, consequences `0f1217fd...` (r1 #1 POWER_COVERAGE_GAP),
`9892eac3...` (r1 #2 POWER_NOT_IN_ASSESSMENT_INPUTS), `e9e6a130...` (r2 #1 PRICED).

## Run 2 (accepted): 21 checks, 0 failed, tool exit 0

### 0. Price before both legs (N2)

SYSTEM fixture `publish_assumption fixture ... --step v1`: revision `508b264a-848b-4198-8413-298bd6aca8cd`
(1.25 USD/L, valid from 2026-01-01).

### 1. Initial Finding and pre-late S3 result

- First delivery: 6 batches, 174 accepted readings (24 generator-power means, 150 context), evidence digest
  `a81678785e008bcfe784342cfe4bb0c6bacffc3e5991552e64fee723120b8170`. `process-jobs` 1 job, 1 run;
  `match-findings` planned 1, new Finding 1, expected 1 OK.
- Finding `f650c53b-50c2-403f-b25e-66b0fccc5a04`; r1 `08ab98f3-b429-4152-8175-284cc722b82c` (rev 1, SUPPORTED,
  OPENED, episode `[06:05, 08:00)`), analytic run `23a015c9-382e-4dc3-98b0-35782c3d60d0` (174 inputs).
- Runner (bootstrap): selected 2, appended 1, replayed 1. Work `8e9dde22-488a-4d8f-b5c4-abf0724d1699`
  (ASSUMPTION_PUBLISHED, attempt `5e595057-...`) appended consequence 1 `cc57a011-8323-48ce-ad4c-e220b50a87c1`;
  r1's FRA work `efab5899-d5b5-4191-99fa-d0c5c02e7431` (attempt `a1f0894d-...`) replayed it.
- **Pre-late S3 result:** consequence 1 CURRENT, `QUANTITY_UNAVAILABLE/POWER_COVERAGE_GAP`; technical digest
  `97b8076e...85c3c`; examined 22 IDs (`82fe80bf...`).
- **N5 precondition (asserted):** r1's observed Candidate span is `[06:05, 08:00)`; `[07:00, 07:05)` lies inside
  it and the spans verify against the stored observed CANDIDATE segments. PASSED.

### 2. Leg A: late mean accepted, same FindingRevision drained

- Late delivery (same registered credential, TLS): batch `47751cc6...`, source sequence 14, accepted evidence
  **`a990d81c-c1d9-43b0-a8ae-1c9fda120f97`**.
- Exactly one EVIDENCE_ACCEPTED work row: **`c74fd0b9-2439-49a4-b29c-21cbf55e27f9`**, revision r1, affected
  `[07:00, 07:05)`, no attempts yet.
- **Before drain:** `STALE ['TECHNICAL_INPUT_CHANGED']`, head still consequence 1, `pending_work` = [`c74fd0b9...`],
  bridge `STALE_QUEUED`, `recalculation_queued` true, no amount. Derived now: `POWER_NOT_IN_ASSESSMENT_INPUTS`,
  examined 23 IDs (`917fd6a6...`), late ID examined, not in r1's run inputs.
- Runner: selected 1, appended 1, failed 0, backlog 0; attempt `b16f1339-d2c2-496f-9ddd-57ff643524a2` SUCCEEDED
  with [`87a04e1a-...`].
- **After drain:** same r1; consequence 2 **`87a04e1a-f077-4c65-be88-62d170c9a7e1`** CURRENT
  `QUANTITY_UNAVAILABLE/POWER_NOT_IN_ASSESSMENT_INPUTS`, technical digest `de861f3b...c5cec`; history
  [`cc57a011...` #1, `87a04e1a...` #2] (consequence 1 retained); bridge `QUANTITY_UNAVAILABLE`, no amount;
  **not S5-eligible**.

### 3. Leg B: S3/S4 re-evaluation, revised FindingRevision drained to PRICED

- `process-jobs`, then `match-findings`: r2 **`5b0a3942-1fad-4770-8097-416f188f9c87`** (rev 2, SUPPORTED,
  SUPPORT_CHANGED, episode `[06:05, 08:00)`), analytic run `7355a96e-199e-470b-b75a-a04f96450f2e` (175 inputs,
  includes the late ID); its CANDIDATE assessment carries only `OPEN_BOUND` (no sequence limitation).
- r2's one FRA work **`5f15e4bc-5607-4b08-95a3-bf32326956ec`**; before drain r2 `PENDING ['NOT_YET_COMPUTED']`
  with that work queued.
- Runner: selected 1, appended 1; attempt `163d2ab0-c635-4fb9-98a4-02697514437e` SUCCEEDED.
- **After drain:** consequence **`73bdcab5-952a-4f78-8605-39e91a05cb16`** (r2 #1) CURRENT **PRICED** by price
  `508b264a...`: 23 counted means, 12.65 L, amount high 15.8125 USD (display 0.00 to 15.82 USD); technical digest
  `d902ae7c...1ce04`; examined 23 IDs (`917fd6a6...`), late ID examined and in run inputs; bridge PRICED with
  amount; **S5 money-eligible** (CURRENT, PRICED, same FindingRevision and basis).
- r1 now `HISTORICAL ['FINDING_REVISION_SUPERSEDED']`, keeps both consequence revisions.
- The old evidence work had already drained before r2 existed, so the "drained after the revision -> superseded
  no-op" branch did not arise here; it is proved by `test_s4_evidence_drain_postgres.py` (superseded no-op).
- Replay run: selected 0, backlog 0. No duplicate `(finding_revision_id, consequence_basis_sha256)`.

### Not shown by this fixture (N7)

The "unrelated accepted input as typed no-op" (another generator's mean) cannot arise here: KOBO-001's variant
binds one generator-power source. The wrong-asset, wrong-role and outside-Candidate no-ops are proved by
`backend/tests/test_s4_evidence_drain_postgres.py` (phase 2), not by this fixture.

### Owner-facing copy

None added. The reads use existing reviewed `REASONS` keys (`STALE_QUEUED`, `QUANTITY_UNAVAILABLE`, `PENDING`,
`PRICED`, `HISTORICAL`) and the existing `POWER_NOT_IN_ASSESSMENT_INPUTS` reason; no questions file was needed.
