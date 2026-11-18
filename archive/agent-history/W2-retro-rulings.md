# W2 retro rulings (2026-10-18)

Architect decision `D-2026-10-18-w2-retro-rulings`. This closes the implementation choices recorded in the W2-02 and W2-03 review packets. `ACCEPT` makes the stated behavior a build contract. `CORRECT` states the required replacement; it does not assert that code has changed. Existing decisions `D-2026-10-17-w2-02-buildspec` and `D-2026-10-18-w2-03-answers` prevail where cited. The v6.9 named screen and its honest gaps remain the user-facing authority.

| Slice | Item | Ruling | Required change if CORRECT |
| --- | --- | --- | --- |
| W2-02 | Deviation 1, cold acquisition snapshot gate | ACCEPT; already ruled by q6 | — |
| W2-02 | Deviation 2, session conflict through test-only S2 basis | ACCEPT; already ruled by q6, proves ledger accounting only | — |
| W2-02 | Deviation 3, V4 publication header dispatch | ACCEPT; already ruled by q6 | — |
| W2-02 | Deviation 4, manifest field readings and opt-in writer | ACCEPT | — |
| W2-02 | Deviation 5, replay refusal ladder and production owner check | ACCEPT; preserve 403 without an owner principal and 404 for out-of-scope runs | — |
| W2-02 | Deviation 6, deterministic test allocation | ACCEPT; test-only, never product IDs | — |
| W2-02 | Deviation 7a, `YamlExecutionArtifacts` schema 6 instead of named JSON store | ACCEPT; the schema and strict read contract matter, and existing store is the artifact owner | — |
| W2-02 | Deviation 7b, Draft `inputs_identity` and empty digest | ACCEPT; already specified by the final W2-02 build spec | — |
| W2-02 | Deviation 7c, host-only `PUBLICATION_REFUSED` excluded from simulator reachability guard | ACCEPT; host must prove the failure, with no kernel reachability claim | — |
| W2-02 | Deviation 7d, cold Lab setup literal readings (last `/`, basis at document start, clear result on Site change, home link, loading recognizer) | ACCEPT; keep selected choice and result consistent with the selected Site and document | — |
| W2-02 | Deviation 8, composition leaf supplies pack | ACCEPT; no dependency-guard relaxation | — |
| W2-02 | Deviation 9, six cold pack interpretations and frozen signal mappings | ACCEPT; already specified in the final W2-02 build spec | — |
| W2-02 | Fix M1, legacy scenario rejects either cold profile before Draft | ACCEPT | — |
| W2-02 | Fix M2, setup state said once and Foundation version fact | ACCEPT; version or “Not available” is a fact, with the actual refusal in its own state message | — |
| W2-02 | Fix L3, choice display name and separate read-only ID | ACCEPT | — |
| W2-02 | Fix L4, guarded STARTING to STOPPED restore transition | ACCEPT | — |
| W2-02 | Fix L5, two-method replay reader facade | ACCEPT | — |
| W2-02 | Fix L6, physical transition refusal uses `FROZEN_RUN_NOT_RECONSTRUCTIBLE` | ACCEPT; the same kind covers a frozen run that cannot execute, before Stage | — |
| W2-02 | Fix F1, Foundation version fact says “Not available” | ACCEPT; “Not available yet” is reserved for unbuilt capability gaps | — |
| W2-03 | Deviation 1, 5-minute bracket and 10-minute work bridge | ACCEPT; already ruled, six-case window `[19:00,20:05)` | — |
| W2-03 | Deviation 2, labelled simulated SYSTEM clock attestation in replay test | ACCEPT; no accepted-row insert | — |
| W2-03 | Deviation 3, MIXED ad hoc split and test-only positive classifier | ACCEPT; scope the positive link proof to the double | — |
| W2-03 | Deviation 4, supported episode loses Finding warrant | ACCEPT; already ruled `UNCONFIRMED` with `SUPPORT_CHANGED` or `BASIS_REFRESHED` | — |
| W2-03 | Deviation 5, W2-00 no-dispatch assertion excludes cold work | ACCEPT; cold roles now enqueue their domain work | — |
| W2-03 | Deviation 6, incidental start Finding in excursion replay | ACCEPT; do not describe the excursion fixture as having a clean start | — |
| W2-03 | Deviation 7, SQL read class at end of assessment store | ACCEPT; pure rules remain in `cold_reads.py`, SQL driver guard unchanged | — |
| W2-03 | Deviation 8, default latest selected window or paired bounds | ACCEPT; one bound alone is 422 | — |
| W2-03 | Deviation 9, selected run and window-end probe freshness | ACCEPT; already ruled by W2-03 amendment | — |
| W2-03 | Deviation 10, pending overlapping bridged cold job | ACCEPT; include PENDING, LEASED and FAILED | — |
| W2-03 | Deviation 11, injectable disclosure seam and MIXED provenance | ACCEPT; default allow is only the absence of a separate disclosure policy, never a source-gate pass or a Finding entitlement | — |
| W2-03 | Deviation 12, 409 cursor-basis conflict | ACCEPT; a selected row must join a settled revision; corrupt/unavailable storage is 503 | — |
| W2-03 | Deviation 13, list/detail basis hashes and `as_of` | ACCEPT; document each object's stated time meaning | — |
| W2-03 | Deviation 14, cold Evidence Analysis links unverified | CORRECT | Render a link only after an integration test proves its exact `record` or `assessment` target displays the selected cold ID in the existing Evidence Analysis route, preserving Site, window and cutoff. Until then, show the exact reference as labelled text with an honest “Analysis view not available for this cold record” gap; never offer a dead or misleading link. Keep working Finding/evidence destinations independently. |
| W2-03 | Deviation 15, missing-probe episode without exposure Finding | ACCEPT; UNKNOWN claim and no exposure Finding | — |
| W2-03 | Deviation 16, Cooling and Recommendation unbuilt rows | ACCEPT; already ruled visible, accessible, noninteractive in mock order | — |
| W2-03 | Deviation 17, “Stock loading / batch” in place of mock “Loading / batch” | CORRECT | Restore the mock's exact “Loading / batch” row label. Change the capture/settling detector to match its actual loading-state element or exact loading sentences; ordinary content containing “Loading” must not hold captures open. Retain “Not established” when no loading record exists. |
| W2-03 | Deviation 18, plain title, columns and generated-test source label | ACCEPT; already ruled as narrow mock exceptions, with exact provenance in detail | — |
| W2-03 | Deviation 19, unknown-kind refused Finding keeps mock slots | ACCEPT; refusal plus in-slot gaps may not imply a known Finding kind or claim | — |
| W2-03 | Deviation 20, manual recovery and Incident without a record | ACCEPT; “Not recorded” is an honest gap and no Incident link is drawn | — |
| W2-03 | Deviation 21, chart axis from selected policy/data | ACCEPT; illustration values are not evidence, and an axis covering real selected values preserves the chart slot | — |
| W2-03 | Fix M1, probe “after recovery” only when cooling runs | ACCEPT | — |
| W2-03 | Fix M2, intake-driven unattested probe exclusion | ACCEPT | — |
| W2-03 | Fix M2 unbound, accepted outside-period record cannot enter S2 | ACCEPT; retain pure rule defence-in-depth proof and explicit test limitation | — |
| W2-03 | Fix L3, “Above policy · At least 45 min” | ACCEPT | — |
| W2-03 | Fix L4, failed/contradictory result chip tones | ACCEPT | — |
| W2-03 | Fix L5, late 19:25 HIGH and absent 19:20 proof | ACCEPT | — |
| W2-03 | Fix L6, LOW excursion minimum proof | ACCEPT | — |
| W2-03 | Fix L7, SQL read-class docstring | ACCEPT | — |

The two `CORRECT` rows are implementation and review gates before W2-03 merge. This decision does not record an independent review verdict or owner acceptance.
