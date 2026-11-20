# 3A7 rulings

Architect (Claude), 2026-11-20. Applied by default; open questions with defaults are in `spec.md` §11.

## D-3A7.1 Reconcile exactly what the screen shows

- **Ruling.** Revenue is every CHARGE amount line; fuel cost is every FUEL expense amount line whose status is in 4b's
  `COST_STATUSES` (imported, not copied), summed exactly over the scope's Site-months from 3A4. Test R7 checks the
  per-Site figures against 4b's `stated` values on the same records.
- **Why.** The gate exists so that the money on the deep-dive screen is not called Recorded while it disagrees with the
  operator's accounts (§7.2). Checking any other definition would validate a figure nobody sees. Importing the status
  set and cross-checking against 4b closes the drift between two definitions of one figure.

## D-3A7.2 One matched month opens the gate for the tenant; a month's own mismatch still shows

- **Ruling.** Money reads "*<origin>*, not yet reconciled" until at least one current statement of the tenant matches.
  After that, a Site-month reads reconciled unless a statement covering it (its Site's, or the organisation's for that
  month) does not match or cannot be compared; then it reads not yet reconciled and says what did not match.
- **Why.** §7.2 and the owner's build plan: "Recorded money reads *not yet reconciled* until one closed month matches
  their management accounts". The gate validates the path (the exports and profiles) once; but a month the finance lead
  has compared and found wrong must never read Recorded because another month passed. A covering organisation statement
  covers every Site, since its mismatch cannot be placed on one Site.

## D-3A7.3 The comparison is made on every read

- **Ruling.** The standing recomputes each current statement against the store now. The stored result and tolerance at
  recording are an audit record only.
- **Why.** A late invoice (3A4's late records) can push a matched month outside the tolerance, or a correction bring an
  unmatched one inside. A stored verdict would go stale silently; a live check costs one month read per Site and is
  exact.

## D-3A7.4 Tolerance: 1 in 100 of the accounts' figure, per heading; the owner may set it per operator

- **Ruling.** Default 0.01 (RC8) of the management accounts' figure for each of revenue and fuel cost; both must match.
  An operator's tolerance is set only by the command with a cited owner file, between 0 and 5%, and is read at check
  time.
- **Why.** RC8 as accepted. The accounts are the operator's reference, so they are the base. A tolerance above 5%
  would make "reconciled" mean little; the owner can still choose within it. Requiring an owner file keeps the setting
  the owner's, not an agent's (RULES §3).

## D-3A7.5 The finance lead's statement, recorded by command for now

- **Ruling.** A statement names one Site or the organisation, a closed month, the currency, the two totals with two
  decimals, and where the figures came from. It is recorded by `reconcile_month record --as <finance lead>`, stored as
  `recorded_by_script`. Open months, other roles and malformed figures are refused in plain words, writing nothing.
- **Why.** Non-screen this fortnight (the owner presents, RC7); the upload screen and sign-in come next fortnight. The
  person is named and the scripted entry is marked, as the loader's acceptance is (D-3A3.11). Queue Q1 asks the owner.

## D-3A7.6 The standing is read live, not snapshotted

- **Ruling.** `3B7a`'s snapshot does not hold the standing; `5c` reads `CommercialReconciliation.standing` beside the
  snapshot through its own route.
- **Why.** The standing depends on statements and tolerance as well as records; a snapshot of it would need its own
  freshness rule. A live read is cheap (one statement read, one month read per Site).

## D-3A7.7 Words: say what did not match, with the figures

- **Ruling.** Each heading's sentence gives the accounts' figure, the records' figure, the difference with its
  direction and share, and the amount allowed with the tolerance; or names what is missing (records, currency, an open
  month). Exact copy in spec §2.7.
- **Why.** The owner asked that the product "say exactly what didn't match"; build plan risk 2 expects most first
  months to fail, so the sentence is the conversation's starting point and must carry the numbers.
