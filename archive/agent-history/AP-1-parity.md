> Finished; historical. Archived from .agent/AP-1-parity.md on 2026-11-18 (declutter step 4).
# AP-1 parity (Kobo) and Kisiwa live read
- Clone assetops_ap1_audit_parity of assetops_polish_vps1_test; probe at 00d235abc; file roots = prepared tree var/ (no legacy Kobo evidence).
- Kobo: 10 role-keyed `available` mismatches (file false, stored true); id_differences only on policy/override rows (null ids, D-SR.78). File side level NONE, 0 intervals; stored FULL / CANDIDATE_AVOIDABLE, 27 intervals. All differences = record only in one store (file baseline empty), so this is not an independent parity: needs a ruling.
- Unwarmed stored read Kobo 0.231 s (< 2 s, no warm entry needed).
- Kisiwa: route returns 409 AWAITING_EVIDENCE_MIGRATION on the clone (comparison report for another tenant/env; Kobo same); the stored read direct gives 13 rows, 10 available, FULL, 0.117 s.
