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

## D-3A7.8 Only a statement compared on both headings against recorded money opens the gate (handshake R1; amends D-3A7.2)

- **Ruling.** A statement **opens** the gate when its state is `MATCHED` and both headings matched against used lines
  (each heading's `reason` is None). A heading matched as `NONE_RECORDED_ZERO_STATED` still makes its own statement
  `MATCHED` (the month's own standing is not held back by it), but that statement does not open the gate.
- **Why.** §7.2's gate is "one closed month reconciled ... on revenue and fuel or energy cost": it validates that the
  billing path and the fuel path deliver what the accounts say. A 0.00/0.00 statement for a Site with no records, or
  revenue plus 0.00 fuel for a Site with no generator, compares nothing on at least one path, so it cannot validate
  it for the whole tenant.
- **Residual (queue Q6).** An operator with no fuel at all (solar only) can never open the gate; the default keeps it
  "not yet reconciled". Owner to weigh in only if a pilot operator has no generator.

## D-3A7.9 The standing is read at the instant of the figure it labels (handshake R2; amends D-3A7.6)

- **Ruling.** `standing`, `check` and `statements` take `known_at: datetime | None = None`. At `k = known_at` (or the
  clock when None): only statements with `recorded_at <= k` exist, the tolerance is the latest row with `set_at <= k`
  (else the default), and every month is read with `site_month(..., known_at=known_at)`. `5c` passes the `as_of` of
  the 3B7a snapshot whose figures it shows, and None only beside live figures; 5c's spec must cite this ruling. The
  standing's JSON carries `known_at`.
- **Why.** A label must describe the number beside it. After a late record or a correction, the snapshot's figure and
  the live figure differ, and a live standing beside a snapshot figure could call a figure that does not match
  "Recorded" (or the reverse). One parameter makes one source: the instant of the figure shown. 3A4's reads already
  take `known_at`, so nothing is snapshotted.

## D-3A7.10 Figures are compared exactly and displayed so that a sentence never contradicts its state (handshake R4, R5, R12)

- **Ruling.** Comparison stays in the exact context (`prec=200`, traps on `Inexact`, `Rounded`, `InvalidOperation`).
  Display uses `DISPLAY = Context(prec=34, traps=[InvalidOperation, DivisionByZero, Overflow])` and `quantize(Decimal
  ("0.01"), rounding=...)` per figure: accounts and recorded `ROUND_HALF_EVEN`; in a `MATCHED` sentence the difference
  rounds `ROUND_DOWN` and the allowed amount `ROUND_UP`; in a `NOT_MATCHED` sentence the difference rounds `ROUND_UP`,
  the allowed amount `ROUND_DOWN`, and the share (`abs(difference) / accounts * 100`, computed in `DISPLAY`) rounds
  `ROUND_UP`. `{gap}` is "the same" only for an exact zero; a non-zero difference that displays `0.00` reads "less than
  0.01 more" or "less than 0.01 less". The JSON keeps exact, unquantised decimals.
- **Why.** The exact context cannot divide `7.50 / 505.00`. Rounding each displayed figure away from the verdict keeps
  every sentence true: a mismatch never shows a difference within the amount allowed, and a match never shows one
  beyond it. Statement K's fuel share is therefore `2.25%` (17.50 / 780.00 = 2.2436%), not 2.24%.

## D-3A7.11 The organisation's scope is its mini-grid Sites (handshake R8)

- **Ruling.** An organisation statement covers the tenant's Sites whose `site_type` maps to `MINI_GRID` through
  `structure.read.SITE_TYPE_TO_STRUCTURE`; a Site statement for another Site type is refused `RECON_SITE_TYPE {site}`.
  The store read `site_rows(tenant) -> tuple[SiteRow, ...]` (`site_id`, `site_code`, `site_type`) replaces
  `site_codes`.
- **Why.** RC5 scopes the deep dive to mini-grids, and 4b's `stated` shows money only for them; summing other Sites'
  money would compare a total no screen shows, which D-3A7.1 forbids.

## D-3A7.12 A tolerance cites an owner file that names the tenant and the figure (handshake R7; amends D-3A7.4)

- **Ruling.** `set-tolerance` requires the cited `owner/owner-*.md` file to exist under the owner root (the repository
  root resolved from the module's path; `main(..., owner_root=None)` for tests) and its text to contain the tenant's
  slug and the tolerance either as written (`0.02`) or as the words' percentage (`2%`); else `OWNER_REF_INVALID`. The
  row stores `owner_ref_sha256` (the file's bytes). No `set_by` is stored: the owner, not a tenant person, sets it, and
  the owner file is the record. A deployment without an `owner/` folder cannot change the tolerance (1% stands).
- **Why.** "Any owner file exists" proves nothing about this tenant or this figure; naming both, and pinning the text
  by hash, shows the owner chose this tolerance for this operator.

## D-3A7.13 The standing's sentence says what did not match (handshake R6; amends D-3A7.7)

- **Ruling.** For `THIS_MONTH_NOT_MATCHED` and `THIS_MONTH_NOT_COMPARABLE`, `standing.text` is the standing sentence
  followed by a space and the sentences of `this_month`'s headings whose state is not `MATCHED`, in heading order,
  space-separated. `words` stays the standing sentence's message.
- **Why.** The owner asked that the product say exactly what did not match; the label 5c shows is `standing.text`, so
  it must carry the figures, not only point at them.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `task/3A6-3A7-handshake` c01baa35a. Every answer is folded into `spec.md` rev 2. A
gate named here has a plant in `reviewer-guide.md` rev 2 that fails it.

### Reviewer

- **R1 (High).** Accepted: D-3A7.8. `StatementCheck.opens: bool`; the gate needs an opener. New case T10 (fresh world,
  A and B only, S3 alone): S3 `MATCHED`, `opens` false; standing KOBO-001 and MTO-001 `2026-10` both `NONE_MATCHED`.
  `none_matched`'s words change to name both headings (§2.7). Gate: V13 (open on any `MATCHED`) fails R2 (T10).
- **R2 (High).** Accepted: D-3A7.9, one source: the instant of the figure shown. Test R9: S1 recorded at
  2026-11-05T10:00Z, C loaded at 2026-11-10T09:00Z; standing KOBO-001 `2026-10` with `known_at`
  2026-11-06T00:00Z is `RECONCILED`, with None `THIS_MONTH_NOT_MATCHED`, with 2026-11-04T00:00Z `NO_STATEMENT`. Gate:
  V14 (ignore `known_at`) fails R9.
- **R3 (High).** Accepted. Every statement's `recorded_at` is in §6.2 (S1 2026-11-05T10:00Z, S2 2026-11-12T10:00Z, S3
  2026-11-13T10:00Z, S4 2026-11-14T10:00Z; T3's tolerance `set_at` 2026-11-15T10:00Z); the test clock rule is §6.2's
  (one settable clock shared by months and reconciliation; set to a statement's time to record it, to
  2026-11-20T08:00Z for every read; C loaded only after T1's reads). R5 keeps fixed UUID literals for its tie. Gate:
  V20 (tie by insertion order) fails R5, and T6 holds deterministically.
- **R4 (Medium).** Accepted: D-3A7.10 (`DISPLAY` context; comparison exact).
- **R5 (Medium).** Accepted: D-3A7.10. R3 gains accounts 501.50, recorded 506.52: `NOT_MATCHED`, "Revenue: the
  accounts say 501.50 USD and the records say 506.52 USD, 5.02 more (1.01%), beyond the 5.01 allowed (1%)." K's fuel
  share becomes 2.25%. Gates: V9 (quantise before comparing) and V15 (half-even display of the allowed amount) fail R3.
- **R6 (Medium).** Accepted: D-3A7.13; T2 and T6 standing texts are written in full in §6.2. Gate: V19.
- **R7 (Medium).** Accepted in part: D-3A7.12 (slug and figure in the file, its SHA-256 stored; no `set_by`, reason
  there). M5 gains: a real owner file without the slug is `OWNER_REF_INVALID`. Gate: V17 fails M5.
- **R8 (Medium).** Accepted: D-3A7.11. §6.2 gains Site `FRZ-001` (`COLDCHAIN`) with a 999.00 CHARGE; every
  organisation literal is unchanged because it is excluded. Gate: V16 (every Site) fails R2 (T1 revenue 1749.00).
- **R9 (Medium).** One `standing` call memoises `site_month` by `(site_id, period)` for that call only (no cross-call
  cache). The gate walks current statements in the cited order (period descending, organisation first, then Site
  code) and stops at the first opener. `standing` does not call `statements()` (the list read); it reads
  `accounts_statements` once and `tolerances` once. R8's literals are in §7. Gate: V18 (no memo) fails R8.
- **R10 (Low).** `recon_amount` takes `{heading_words}`: "revenue" or "fuel cost".
- **R11 (Low).** The shape keeps `recorded_by` (UUID); `5c` resolves the name through the accounts service. The guide's
  probe now reads "names the finance lead's person ID".
- **R12 (Low).** D-3A7.10: "less than 0.01 more/less".
- **R13 (Low).** `ReconMemoryStore(MonthsMemoryStore)` is defined in `test_3a7_reconciliation.py`;
  `test_3a4_commercial_months.py` is not edited.
- **R14 (Low).** The CHECK becomes `CASE WHEN tolerance ~ '^0\.[0-9]{1,4}$' THEN tolerance::numeric > 0 AND
  tolerance::numeric <= 0.05 ELSE false END`; Q1 inserts `'0.06'`, `'abc'` and `'0.0000'`, each a check violation.

### Implementer pre-flight

- **P1 (High).** D-3A6.12: `0068_commercial_reconciliation` revises `0067_source_profile`; 3A7 branches after 3A6
  merges (which itself follows 3B7a); no renumbering. Q1 asserts the chain link.
- **P2 (Medium).** Yes: `SPEC_ROLES` gains `"commercial.accounts_statement": (FINANCE,)`; `test_3c1a_person_work.py`
  joins done 9 (one line).
- **P3 (Medium).** D-3A6.17: `AccountService.tenant_by_slug`, built by 3A6; 3A7 uses it.
- **P4 (Low).** Residual for the packet: `build_commercial_reconciliation` adds `structure` to
  `commercial.composition`'s import closure, so 3B7a's code digest changes (as 3A6's P9).
- **P5.** Noted; K's fuel share changes to 2.25% under D-3A7.10, every other figure stands.

## Amendment (SC-1, 2026-11-21): words as statements (D-SC1.14)

If `SC-1a` (`specs/SC-1-statement-composer/spec.md`) has merged when this unit's code starts, §2.7 is written as
structured statements in `i18n/statements/en/reconciliation.py`, not flat `messages.py` entries: the heading sentence
exactly as SC-1 §5.1 (states as an `exhaustive` variant set, `{gap}` and `{share}` as parts, D-3A7.10's rounding as
variant options, "less than 0.01" as the money format's `tiny`); the statement, standing and refusal sentences by the
same rules (refusal examples as `example` slots); `money_word` applies the shared `evidence` format (D-SC1.16);
`commercial/reconciliation.py` joins the guard's `ADOPTED`; every variant gets a case. Money reads in SC-1's one form
(D-SC1.10): `$505.00`, not `505.00 USD`; this unit's expected strings change by that rule only. Otherwise §2.7 ships as
written, its keys join the legacy baseline, and SC-1b converts them. Either way nothing waits.

**Amended (SC-1 handshake, 2026-11-21; D-SC1.26 replaces the "otherwise" above).** This unit's code starts when both
3A6 and SC-1a have merged; the coordinator checks SC-1a's merge at dispatch and says so in the brief. There is no flat
fallback. The heading reads as SC-1 §5.1 rev 2 (its `records` slot declares `"form": "in_sentence"`, because `record_noun` has only that form; D-SC1.31; transcribe the slot exactly, never default it to `label`), with the evidence word of the figures it states (`Revenue
(Recorded): the accounts say ...`, D-SC1.18), the difference, allowed amount and share declared `derived_from`; the
scope is SC-1 §5.4's `reconciliation.scope` (a `State` and a `Name`). Every template holding a number word is
reworded to drop it (D-SC1.21): `standing.none_matched` reads "Not yet reconciled: no month's recorded revenue and
fuel cost match the management accounts within {tolerance} yet." The command's printed sentences render the same
statements; any message the command stores or prints as JSON params goes through `i18n.to_wire` (D-SC1.19). This
unit's expected strings change by these rules only; the packet lists each changed string for the walkthrough.
