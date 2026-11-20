# 4b rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. Index lines: `.ai/decisions/index-rulings-10.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-4B.1 A node that a record states is read from that record; its expression stays as the explanation

- **Ruling.** A registry node may declare `stated_by` (the record that states its total). `evaluate` takes an optional
  `stated` map: a stated value with a value is the node's value, and the node's expression is still evaluated and
  kept as `computed` and `detail_missing`. With no stated value the node is computed as before. MINI_GRID: `revenue`
  (CHARGE) and `fuel_cost` (EXPENSE FUEL) only. The seam is unit `4b1`, reviewed and merged on its own before `4b2`
  and before `5a`'s units 2 and 3 build on it (RULES §7: a unit that touches shared code is reviewed first).
- **Why.** A typical operator sends billing and fuel invoices, not kWh delivered or litres burned (`two-week-build-plan.md`
  §0.4). Bottom-up, `revenue` needs `delivered_kwh` (4a) and `fuel_cost` needs the litre split (4d), so without this
  the deep-dive screen could show neither heading. The charge total is revenue's own record, not a substitute (the
  structure specification's rule 1: a leaf "may fall back only to another record"; the pack's "stated totals", §3).
  The expression is kept so the screen can still say which factors below the heading are not available yet.
- **Consequence for D-BW1.10.** `5a` no longer waits for `4b`'s providers; it waits for `4b1` (1 unit, day 3), the
  seam both use. Its unit 1 does not wait at all.

## D-4B.2 Origin is carried beside the evidence class, and the weakest origin labels a total

- **Ruling.** `LeafValue` and `FactorValue` gain `origins` (the record provenances beneath the value, strongest first in
  `ORIGIN_ORDER`). Nodes and portfolio values take the union; `weakest_origin` gives the label's origin.
- **Why.** `economic-metric-and-effect-contracts.md` §4.4: a node "carries every provenance beneath it", and "no total
  is shown as a stronger class or provenance than its weakest part" (P3B rule: the weakest part sets the label).
  Emulated is a provenance, not a class (D-3B3.2), so it needs its own field; `3A5`'s rule on `5c` reads it.

## D-4B.3 Which records fill which leaf

- **Ruling.** As spec §3.4. Cost counts only `INVOICED` and `PAID` expenses, never `QUOTE`. Revenue is every CHARGE
  amount of the month. Credits (`ADJUSTMENT`) are not revenue; they are `liability`, outside 4b.
- **Why.** 3A4's queue Q3 (a quote is not a cost). A month's billing is the operator's billed revenue; netting credits
  would hide them, and the structure keeps them on their own leaf.

## D-4B.4 Money leaves from records need a closed month

- **Ruling.** While the month is open (3A4's `closed` false), every leaf and stated node 4b provides has no value,
  cause `NOT_RECEIVED`, note `MONTH_OPEN`.
- **Why.** The same class as D-3B3.12: a partial month's sum is a lower bound shown as the month.

## D-4B.5 Cause: connected, received, held

- **Ruling.** A record kind is *connected* for a Site when the store holds any record of that kind for the Site (as of
  `known_at`); it is *held for the month* when the month has a line of that kind. Absent value: `NOT_CONNECTED` when
  a needed kind is not connected, else `NOT_RECEIVED`. A ZERO_WHEN_HELD leaf reads a recorded 0 only when its kind is
  held for the month.
- **Why.** The structure specification §3.1 causes and rule 1 ("zero is a recorded fact only while the source that
  would record the event is held"). Kisiwa's missing O&M invoice is then "not received", not "not connected".

## D-4B.6 The diesel price comes from fuel invoices first; the declared price only when the month has none

- **Ruling.** New state `PROVIDED_ELSE_ASSUMED`. `diesel_price` = fuel cost / fuel litres over the month's INVOICED
  and PAID fuel invoices, evidence `DERIVED`. With no such invoice (no expense source, an open month, or no fuel line) it is read from the
  delegate (3B3's labelled assumption). With invoices that cannot give a price (mixed currencies), it has no value; the assumption never hides
  records.
- **Why.** The leaf's own record is `EXPENSE (FUEL)`; 3B3's declared price is the operator's value of the same
  quantity (D-3B3.11), so it is the honest fallback, still labelled.

## D-4B.7 Fuel cost is fuel bought in the month (owner question Q1)

- **Ruling.** The stated `fuel_cost` is the month's fuel invoices, named "Fuel invoices for the month". Litres burned
  come with `4d`; stock change is not modelled.
- **Why.** It is what the operator's accounts show as the month's fuel cost; anything else needs tank dips.

## D-4B.8 4b never fills a missing actual from a target (owner question Q2)

- **Ruling.** A missing actual reads not available, and the portfolio says "k of n sites". The structure
  specification's rule 3 (carry a missing line at its target, *Estimated*) needs `5a`'s targets, so `5b` applies it.
- **Why.** 4b does not depend on 5a (D-BW1.10); the owner accepted "k of n sites" (20 Nov).

## D-4B.9 Money in transit is read from the receipt's status

- **Ruling.** `in_transit` = the month's RECEIPT amounts with status `PAID_IN_TRANSIT`, as known at the read. Matching
  receipts to settlement statements is not built (queue Q3). A later revision of a receipt to `COLLECTED` moves it, as
  any late record does (3A4's stamps).
- **Why.** 2a carries the status on the receipt; matching by `receipts` references needs record bodies 3A4 does not
  line up, and is not on the path.

## D-4B.10 MINI_GRID becomes version 3, in place

- **Ruling.** `stated_by` is a row field, so the version moves to 3 (D-2A.2's class). It is replaced in place.
- **Why.** No stored value of version 2 exists (`3B7a` has not merged), as with D-3B3.9.

## D-4B.11 `detail_missing` names what is not available below a value

- **Ruling.** Every factor value carries `detail_missing`: the leaves beneath it with no value, even when the value
  itself rests on a stated record. The neutral identity (D-3B3.15) drops the other operand's list.
- **Why.** "Not available yet, with the record that would fill it" must survive under a stated heading: the screen says
  where the kWh and the litres are not known while revenue and fuel cost are.

## D-4B.12 One read of the store per Site-month read, never a cache across reads

- **Ruling.** `CommercialLeafSource` keeps one entry keyed by the identity of the `ReadContext` object, stored as one
  tuple. `StructureRead.site` builds a new context per call, so a later read always sees new records.
- **Why.** About ten leaves and stated nodes read the same month; a cache keyed by equality would serve a stale month
  after an intake.
