# T022A - A run read that does not cost the whole store

Status: planned
USER_REVIEW_REQUIRED: true

Map: A hardening; unblocks the Lab as a demonstrable surface.
Depends on: T022.
Next: T023.
Branch: task/T022A-run-store-read-cost
Sizing: one read path; no new product behaviour.

## Outcome

Stepping a Draft in the Lab responds without a pause a person notices. Opening
a run, listing the inventory and reading an execution each cost what that one
thing costs, not what the whole store costs.

Found by the owner on 2026-09-28, stepping the first real run T022 delivered.
The run completed correctly and the values were right; every interaction took
about nine seconds, which reads as a hang. **This is the defect that would end
a demo in its first minute**, and T027 is the internal architecture demo.

## The measurement that opened it

Against a store of 216 runs, on the composed `host/lab_app.py`:

| Endpoint | Time |
| --- | --- |
| `/api/simulator-lab/status` | 0.003s |
| `/api/sites` | 0.41s |
| `/api/simulator-lab/runs` | 8.93s |
| `/api/simulator-lab/runs/{id}` | 9.06s |
| `/api/simulator-lab/runs/{id}/execution` | 9.21s |

The three run endpoints cost the same, so the cost is not in the execution
artifact or in rendering one run. `YamlRunStore.get_run` at
`backend/assetops_backend/runs/adapters/yaml_run_store.py:85` calls
`self.list_runs()`, which calls `read_run_records(self._root)` and parses every
stored run, then scans linearly for one id. A single-run read pays the whole
store.

This is the cost first measured in T020A at 70 Drafts and 6.8 seconds, carried
in `.ai/MILESTONE_REVIEW_BACKLOG.md` since, and named there as wanting a
bounded fix with an owner before T027. At 216 runs it has crossed from slow to
unusable.

## Deliver

Make a single-run read cost one run. Keep the strict validation the store
already performs on what it returns - this is about what is read, not about
reading it more loosely.

The inventory is a separate question from a single read and may still need
every record; if it does, say what makes it cheap enough and prove it at a
store size the project will actually reach.

## Acceptance criteria

1. `get_run` reads the record it was asked for. A store of any size does not
   change what one read costs beyond locating the file.
2. The inventory's cost is stated and measured, and its own strictness is
   unchanged. If it still reads every record, the task says why that is
   acceptable and at what size it stops being so.
3. Strict validation is preserved: an invalid stored document is still refused
   with its reason, and a single read that cannot be satisfied still raises
   `RunNotFound` rather than an empty or partial answer.
4. One invalid document does not make an unrelated single-run read fail. If the
   inventory still fails whole, that is stated rather than assumed - the
   scenario catalog has the same shape and it is already carried.
5. Identity and case handling are unchanged: `run_id_key` still decides what
   matches, and a case variant still resolves the same record.
6. Concurrency is unchanged. The write lock still serialises writes, and a read
   during a write returns a whole record rather than a partial one.
7. No stored record is rewritten, migrated, reindexed on disk or deleted.
   `var/runs` holds 216 records that are the owner's data and the evidence for
   this task.
8. Measured before and after at the real store size, through the composed app
   rather than against the adapter alone, with the numbers recorded.
9. The Lab's step interaction is measured end to end, because that is the
   symptom that opened this and the one a person judges.
10. No product behaviour changes. Same payloads, same statuses, same refusals.

## Proof

| Case | Required result |
| --- | --- |
| Single read at 216 records | Does not scale with store size |
| Single read at 10 records | Same path, same result |
| Unknown id | `RunNotFound`, not a silent empty |
| Case-variant id | Resolves the same record |
| Invalid document present | Its own read refuses with its reason |
| Step in the Lab | Responds without a noticeable pause |
| Read during a write | A whole record, never a partial one |

Measure through the composed app at the real store size. State what you
measured on, because a temp directory with ten records proves nothing here.

## Scope limits

Not a storage engine, not an index on disk, not a cache with an invalidation
policy nobody asked for, and not a migration. If the honest fix needs one of
those, stop and say so rather than building it.

The scenario catalog's all-or-nothing read is a separate carried item; do not
fix it here.

## Review

The owner steps a run and judges whether it responds. The Reviewer checks that
strictness, identity and concurrency are unchanged and that the measurement was
taken at the real store size.
Review outcome: pending.
