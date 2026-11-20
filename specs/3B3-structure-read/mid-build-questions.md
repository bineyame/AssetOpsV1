# 3B3 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **4** (reset at rev 2, after handshake round 1; Q1-Q4 raised during the build, 2026-11-20; all four answered in `rulings.md`, round 1).

## Q1. `month_sum` signature: spec §3 and rulings P1 disagree with the handshake text "P1: adopted" (Medium)

- Section: spec §3 "`month_sum` (P1)" and rulings "P1: adopted" give `month_sum(rows, lo, hi, key)`; the handshake's
  proposed answer, which "adopted" makes the ruling, is `month_sum(rows, measure, lo, hi, key)`.
- Why it matters: the returned `GradeCounts` is `counts(rows, lo, hi, [measure])`. Without `measure`, a month with
  no stored row at all counts every day NOT_EXPECTED (expected 0) instead of NO_DATA, which changes
  `_month_reading`'s days (no longer "no behaviour change") and turns the leaf's NOT_RECEIVED into NOT_CONNECTED.
- Built: the handshake form, `month_sum(rows, measure, lo, hi, key)`, which keeps `_month_reading` unchanged.
  Nothing stopped. Ask: confirm the five-argument form (or rule how the four-argument form counts an empty month).
- **Answered** (rulings.md, "Mid-build answers (round 1)", Q1): the five-argument form is the ruling; P1 amended.

## Q2. A COMPLETE `critical_served` day whose row has no `unserved_kwh` (Medium)

- Section: spec §3, `unserved_critical_kwh` row; D-3B3.12.
- `month_sum` (unchanged extraction) skips a counted day whose value lacks the key, so a closed month with every day
  COMPLETE but one row with `value = None` (the SR-7 "analysed, no value" kind) sums the other days and reads as the
  month. That is an unknown day read as zero.
- Stopped: no extra guard was added (the extraction is behaviour-neutral by P1). Ask: should the leaf also require
  every COMPLETE day to state the key (else NOT_RECEIVED), and is that check the leaf's or `month_sum`'s?
- **Answered** (rulings.md, Q2; D-3B3.17): yes, unknown read as zero. `month_sum` returns `unstated`; the leaf's coverage excludes those days (NOT_RECEIVED, note `VALUE_NOT_STATED:<n>`).

## Q3. "The month has closed" when no `known_at` is given (Low)

- Section: spec §3 (D-3B3.12) says "closed in the Site's calendar"; `known_at` may be None.
- Built: closed means the month window's end (Site-local midnight of the next month, in UTC) is at or before
  `known_at`, or before the wall clock when `known_at` is None (`structure/composition.py` `_utc_now`, injected
  into `ProductLeafSource`). Ask: confirm, or name the read-instant seam `3B7a` will use.
- **Answered** (rulings.md, Q3): confirmed, the injected `now`; `3B7a` always passes `known_at`.

## Q4. `Composition.sites` and the "n" of "k of n Sites" (Low)

- Section: spec §2.3/§4 records; owner file `owner/owner-k-of-n-sites-2026-11-20.md`.
- Built: `Composition.sites` = the Sites composed (the MINI_GRID Sites); `Composition.sites_excluded` = Sites left
  out whole (`STRUCTURE_NOT_DECLARED`); `PortfolioStructure.sites` = every Site asked for, in order. Per factor,
  `included` + `excluded` cover `Composition.sites`. Ask: which set is `3B5`'s "n".
- **Answered** (rulings.md, Q4; D-3B3.13 amended): n = `PortfolioStructure.sites`; add `site_count` in `read.py`.
