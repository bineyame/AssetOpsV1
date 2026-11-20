# 2a reviewer guide

For the fresh Reviewer, first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`) and then at the review of the built unit. Review depth: discovery (W5), because this is a new shared
mechanism and a protected seam from now on (D-2A.2).

## What to check first

1. **Gate.** Did code start only after the handshake closed and the owner approved P2 (spec §0, §2)? The first
   commit may hold only tests and the fixture (spec §12).
2. **Scope.** `git diff --stat main...HEAD` lists only `contracts/assetops_contracts/canonical/*`,
   `contracts/tests/test_canonical_*.py`, `contracts/tests/fixtures/canonical_v1_examples.json` and the packet.
3. **Fixture.** `cmp specs/2a-canonical-format/examples-v1.json contracts/tests/fixtures/canonical_v1_examples.json`
   reports no difference.

## Done means

- Spec §10's six questions are each answered yes, with the command output in the packet.
- The catalogue in `factors.py` equals spec §5 row for row (ID, structure keys, unit text, display) and T1 passes.
- §6.4 is implemented as data (`KIND_SPECS`), not as per-kind branches that could drift from the table.
- Every refusal path of spec §6.7 has a T6 case asserting the full text.

## Probes (run them yourself; each is a small edit in a scratch copy)

- **P1 Floats.** Feed `{"value": 1.5, ...}` and `{"value": "1.5e0"}`: both `CANONICAL_NUMBER`.
- **P2 Closed schema.** Add `"note": "x"` to a body and to a top-level record: `CANONICAL_FORBIDDEN` with the path.
- **P3 Per-row independence.** In a batch of three, break record 2: records 1 and 3 still parse, record 2 holds
  its refusal, and `to_canonical_json(batch)` omits only record 2.
- **P4 Round trip.** For each example record, `parse_record(json.loads(to_canonical_json(r)))` equals `r`, and the
  bytes are identical a second time. Check that `"1.50"` stays `1.50` and `Z` becomes `+00:00`.
- **P5 Units.** `parse_unit` refuses lower-case names, spaces, `^`, out-of-order numerators and an empty string.
- **P6 No escape.** Run T7 with three other seeds (edit the seed locally): nothing but `CanonicalRefused` escapes.
- **P7 Neutrality.** `grep -rn "^import\|^from" contracts/assetops_contracts/canonical/` shows only standard-library
  modules and `assetops_contracts`.
- **P8 Independence of the checker (W2).** The parity test reads the manifest and the public API only; it shares no
  list with `factors.py` (it must not import a private constant or copy the table).

## Class sweeps (W6) the reviewer checks

- If one kind's table row was coded wrong, check all fourteen against spec §6.4, not only the one found.
- If one unit text was wrong, recompute all 73 with `str(LEAF_FACTORS[i].unit)` against spec §5.

## Risks to keep in view

- A future slice "fixing" version 1 in place (D-2A.2). Say so in the review if the packet suggests later edits.
- `3B1`'s unit check will meet the literal-unit cases D-2A.4 names; that is expected, not a 2a defect.
