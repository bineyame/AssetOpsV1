import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  DataTable,
  ExactReferences,
  MetricCard,
  MetricCards,
  MissingClaim,
  moneyWords,
  Notice,
  Panel,
  ProductStatus,
  StatusBar,
  type ExactReference,
  type ProductWords,
} from "../ui";
import "./w1ux02-money.css";
import type {
  ConsequenceRevision,
  FinancialReadResult,
  FindingConsequencesBody,
  FindingFinancialsBody,
} from "./financialsClient";
import { formatInstant } from "./FoundationRevisionPanel";
import { SourceProvenanceNotice } from "./sourceProvenance";

/**
 * S4-02b phase 2b: the Finding bridge on Site > Financials > Overview, over the stored `fuel-cost-1`
 * consequence of one exact Finding version.
 *
 * - An amount appears only when the bridge holds a CURRENT PRICED head with a display range. It is a modelled,
 *   assumption-conditioned potential fuel-cost exposure "from 0 up to X", never a point saving.
 * - Every other state (no price, quantity unavailable, not yet worked out, out of date, an earlier finding version,
 *   a source not open for current use, the store unreadable) is a typed state with no amount.
 * - Earlier fuel cost versions stay inspectable by ID and are labelled as kept for the record; the site list of
 *   every version is Assumptions > Interpretation history (W1-F3).
 * - Identifiers, digests, the model version and enum names sit only in the "How this is worked out" disclosure.
 */

export interface BridgeLinks {
  finding: (findingId: string, revisionId: string) => string;
  evidence: (findingId: string, revisionId: string) => string;
  assumptions: (pin?: { revisionId?: string | null; recordedAt?: string | null }) => string;
  /** The Overview pinned to one exact consequence version of the same Finding version (null: the latest). */
  consequence: (findingId: string, revisionId: string, consequenceRevisionId: string | null) => string;
  /** post-W6 W1-b Q21 / R198: the global Financials list (`Portfolio roll-up →` on the statusbar). */
  portfolio?: string;
  /** post-W6 W1-b Q22 / R199: the Site's Dispatch Analysis at one UTC day, optionally one proved interval revision. */
  dispatchAnalysis?: (day: string, intervalRevisionId: string | null) => string;
}

/**
 * post-W6 W1-b Q22 (pre-flight ruling 1): "Inspect technical basis →" targets Dispatch Analysis on the UTC day of the
 * Finding window start. A revision is added only when an explicit source proves it is a 15-minute interval revision
 * of the selected Finding on that same day; the bridge read supplies no such proof, and a Finding, consequence or
 * whole-window primary revision is never used. An absent or invalid window start gives no link.
 */
export function technicalBasisHref(
  windowStart: string | null | undefined,
  dispatchAnalysis: BridgeLinks["dispatchAnalysis"],
  proof?: { revisionId: string; intervalRevisionIds: string[]; intervalDay: string } | null,
): string | null {
  if (dispatchAnalysis === undefined || typeof windowStart !== "string") return null;
  if (!/^\d{4}-\d{2}-\d{2}T/.test(windowStart) || Number.isNaN(Date.parse(windowStart))) return null;
  const day = new Date(windowStart).toISOString().slice(0, 10);
  const proved =
    proof != null && proof.intervalRevisionIds.includes(proof.revisionId) && proof.intervalDay === day ? proof.revisionId : null;
  return dispatchAnalysis(day, proved);
}

/** Why the fuel quantity could not be bounded, in plain words, keyed by the stored reason. */
const QUANTITY_WORDS: Record<string, string> = {
  POWER_MISSING: "No accepted generator power readings cover this finding's time.",
  POWER_COVERAGE_GAP:
    "The generator power readings cover too little of this finding's time. Gaps between readings are never filled in, so no fuel amount is worked out.",
  INTERVAL_CROSSES_NECESSARY:
    "A generator power reading spans time when the generator was needed, so it cannot be split and counted.",
  INTERVAL_CROSSES_INDETERMINATE:
    "A generator power reading spans time that could not be judged, so it cannot be split and counted.",
  INTERVAL_CROSSES_UNOBSERVED: "A generator power reading spans time with no observations, so it cannot be counted.",
  INTERVAL_OUTSIDE_FINDING: "A generator power reading reaches outside this finding's time, so it cannot be counted.",
  INTERVAL_NOT_WHOLE_SECONDS: "A generator power reading has an unusable time span.",
  POWER_OVERLAP_CONFLICT: "Two generator power readings overlap or disagree, so neither is chosen.",
  POWER_NEGATIVE: "A generator power reading is below zero, so it is not used.",
  POWER_INVALID: "A generator power reading is not a usable value.",
  POWER_NOT_IN_ASSESSMENT_INPUTS: "A generator power reading was not among this finding's checked inputs.",
  SFC_MISSING: "The site model has no fuel use per kWh for the generator over this time.",
  SFC_NONPOSITIVE: "The generator's fuel use per kWh in the site model is not a positive value.",
  SFC_INVALID: "The generator's fuel use per kWh in the site model is not a usable value.",
  SFC_CONFLICT: "The site model gives two different fuel use values for the generator over this time.",
  SFC_CHANGES_WITHIN_INTERVAL: "The generator's fuel use per kWh changes part-way through a reading.",
  SFC_REVISION_UNVERIFIED: "The site model version for the generator's fuel use could not be confirmed.",
  BINDING_MISSING: "Which meter reports the generator's power is not recorded for part of this time.",
  BINDING_CHANGES_WITHIN_INTERVAL: "Which meter reports the generator's power changes part-way through a reading.",
  FINDING_NOT_SUPPORTED: "This finding is not a supported finding, so no fuel amount is worked out for it.",
  NO_CANDIDATE_TIME: "This finding has no observed avoidable generator time to count.",
  CANDIDATE_SPAN_UNVERIFIED: "The finding's avoidable generator time could not be confirmed from its checked inputs.",
  ASSESSMENT_LINEAGE_INVALID: "The finding's checked inputs could not be confirmed, so nothing is counted.",
};

const PRICE_WORDS: Record<string, string> = {
  NO_PRICE: "No diesel price is recorded for this finding's time. No default or company-wide price is used instead.",
  PRICE_SPANS_WINDOW:
    "The diesel price changes part-way through this finding's time, so no single price applies and none is chosen.",
  PRICE_UNIT_MISMATCH: "The recorded diesel price is not a price per litre, so it is not used.",
  PRICE_CONFLICT: "Two recorded diesel prices both cover this finding's time, so neither is used.",
  PRICE_INVALID: "The recorded diesel price is not a usable value.",
  PRICE_REVISION_MISSING: "The recorded diesel price version could not be found.",
};

/**
 * W1-UX-02: the plain words for the money state of one exact Finding version. Wrap-then-replace of the former
 * local `STATE_HEADLINE` map: the money codes the shared map owns (withheld, source not established, pending
 * reassessment, unpriced) come from `moneyWords`; the rest stay here as domain words. Nothing is derived: the
 * caller passes the state the bridge read returned. An unknown state falls back to the shared non-positive words.
 */
const NO_AMOUNT = "No current amount can be shown";

const LOCAL_MONEY_WORDS: Readonly<Record<string, Omit<ProductWords, "code" | "unrecognised">>> = {
  QUANTITY_UNAVAILABLE: {
    label: "Not calculated: no fuel amount, so no cost",
    sentence: "No fuel amount was worked out for this finding, so no price is applied and no cost is shown. This is not zero.",
    tone: "limited",
  },
  STALE: {
    label: NO_AMOUNT,
    sentence: "Readings arrived after this cost was worked out, so it is out of date and no current amount is shown. This is not zero.",
    next: "Look again after the finding has been checked again.",
    tone: "limited",
  },
  PENDING: {
    label: NO_AMOUNT,
    sentence: "The cost of this finding has not been worked out yet, so no amount is shown. This is not zero.",
    next: "Look again after the cost has been worked out.",
    tone: "waiting",
  },
  HISTORICAL: {
    label: NO_AMOUNT,
    sentence: "This is an earlier version of the finding, kept for the record, so no current amount is shown for it.",
    next: "Open the latest version of the finding to see its money view.",
    tone: "neutral",
  },
  AUDIT_ONLY: {
    label: NO_AMOUNT,
    sentence: "The source of these readings is closed, so this is kept for the record only and no amount is shown.",
    tone: "neutral",
  },
  UNAVAILABLE: {
    label: "The cost could not be read",
    sentence: "The cost of this finding could not be read, so nothing is known about it right now. This is not zero.",
    next: "Try again shortly.",
    tone: "problem",
  },
  PRICED_NOT_ROUNDED: {
    label: NO_AMOUNT,
    sentence: "No rounding rule is known for this price's currency, so no amount is shown. This is not zero.",
    tone: "limited",
  },
};

const SHARED_MONEY_STATES = new Set(["WITHHELD_GENERATOR_SERIES", "MIXED_OR_UNKNOWN_SOURCE", "PENDING_REASSESSMENT", "UNPRICED"]);

/** The money words for a bridge state; `shown` is true only for a current priced amount. */
export function consequenceWords(c: FindingFinancialsBody["consequence"], shown: boolean): ProductWords {
  if (shown) {
    return {
      label: "Modelled range, using the latest checked readings",
      sentence:
        "This is a modelled range of potential fuel cost, from zero up to an upper amount. It is not measured fuel saved, money spent or a physical maximum.",
      tone: "positive",
      code: c.state,
      unrecognised: false,
    };
  }
  if (SHARED_MONEY_STATES.has(c.state)) return moneyWords(c.state);
  // A priced cost whose currentness is not current reads by its currentness, never as a current amount.
  const key =
    c.state === "PRICED" ? (c.currentness !== null && c.currentness !== "CURRENT" ? c.currentness : "PRICED_NOT_ROUNDED") : c.state;
  const local = LOCAL_MONEY_WORDS[key];
  return local === undefined ? moneyWords(c.state) : { ...local, code: c.state, unrecognised: false };
}

export function quantityWords(reason: string | null): string {
  return (reason && QUANTITY_WORDS[reason]) || "The fuel amount could not be bounded from the accepted generator data.";
}

export function priceWords(reason: string | null): string {
  return (reason && PRICE_WORDS[reason]) || "No single recorded diesel price covers this finding's whole time.";
}

function day(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

function minutes(start: string, end: string | null): string | null {
  if (end === null) return null;
  const ms = new Date(end).getTime() - new Date(start).getTime();
  if (!Number.isFinite(ms) || ms < 0) return null;
  const total = Math.round(ms / 60000);
  const h = Math.floor(total / 60);
  const m = total % 60;
  return h > 0 ? `${h} h ${m} min` : `${m} min`;
}

/** "0.00 to 15.82 USD": the display strings exactly as served (low rounded down, high rounded up). */
function range(low: string, high: string, unit: string): string {
  return `${low} to ${high} ${unit}`;
}

/** Why a stored revision has no amount, or why its amount is not current. */
function revisionWhy(rev: ConsequenceRevision): string {
  if (rev.state === "QUANTITY_UNAVAILABLE") return quantityWords(rev.quantity.reason);
  if (rev.state === "UNPRICED") return priceWords(rev.price.reason);
  if (rev.display?.state !== "ROUNDED_OUTWARD") return "No rounding rule is known for this price's currency, so no cost is shown.";
  return "";
}


/**
 * W1-F3: the v69 bridge table (`financials:1`): what happened, how it becomes money, the consequence, its basis
 * and the source to return to. One row, the stored `fuel-cost-1` line of one fuel cost version; `current` decides
 * whether its amount reads as current. The maintenance line of the mock is not built and is not drawn.
 */
function BridgeTable({
  rev,
  current,
  links,
  findingId,
  findingRevisionId,
  findingRevisionNo,
  labelledBy,
}: {
  rev: ConsequenceRevision;
  current: boolean;
  links: BridgeLinks;
  findingId: string;
  findingRevisionId: string;
  findingRevisionNo: number;
  labelledBy: string;
}) {
  const priced = rev.state === "PRICED" && rev.display?.state === "ROUNDED_OUTWARD";
  const span = minutes(rev.window.start, rev.window.end);
  return (
    <DataTable labelledBy={labelledBy}>
      <BridgeHead />
      <tbody>
        <tr data-bridge-row={rev.id}>
          <td data-bridge-step="fuel">
            {rev.quantity.high_display !== null ? `${range("0", rev.quantity.high_display, "litres")} of diesel` : "Fuel amount not calculated"}{" "}
            during the observed avoidable generator time, {formatInstant(rev.window.start)} to {formatInstant(rev.window.end)}
            {span ? ` (${span})` : ""}
          </td>
          <td data-bridge-step="price">
            {rev.price.value !== null && rev.price.currency !== null ? (
              <>
                Diesel at {rev.price.value} {rev.price.currency} per litre
                {rev.price.revision_id !== null ? (
                  <>
                    {" · "}
                    <Link to={links.assumptions({ revisionId: rev.price.revision_id })} data-bridge-price-revision={rev.price.revision_id}>
                      The site price version used
                    </Link>
                  </>
                ) : null}
              </>
            ) : rev.state === "QUANTITY_UNAVAILABLE" ? (
              "Not applied: no price is applied without a fuel amount"
            ) : (
              `No single price: ${priceWords(rev.price.reason)}`
            )}
          </td>
          <td data-bridge-amount={priced ? (current ? "current" : "recorded") : "none"}>
            {priced && rev.display ? (
              <strong>{range(rev.display.amount_low ?? "", rev.display.amount_high ?? "", rev.display.currency)}</strong>
            ) : (
              "No cost shown"
            )}
          </td>
          <td>
            <span className="badge badge--neutral">Modelled</span>{" "}
            {/* W1-F3 review M4: the "not a measured saving" caveat is said by the state line above and in Trade-offs. */}
            {priced ? (current ? "Modelled range" : "Recorded for this version; not the current cost") : revisionWhy(rev)}
          </td>
          <td>
            <ConfidenceNotAssessed />
          </td>
          <td>
            <Link to={links.finding(findingId, findingRevisionId)}>Finding version {findingRevisionNo}</Link>
          </td>
        </tr>
      </tbody>
    </DataTable>
  );
}

function BridgeHead() {
  return (
    <thead>
      <tr>
        <th scope="col">What happened</th>
        <th scope="col">How it becomes money</th>
        <th scope="col">Consequence</th>
        <th scope="col">Basis</th>
        <th scope="col">Confidence</th>
        <th scope="col">Source</th>
      </tr>
    </thead>
  );
}

/** W1-F3 review H2: the mock's Confidence column; no read assesses the confidence of a money line yet. */
function ConfidenceNotAssessed() {
  return (
    <span className="badge badge--not-assessed" data-bridge-confidence data-not-assessed>
      Not assessed
    </span>
  );
}

/** Why the fuel step has no price, from the bridge read only (no stored version is drawn). */
function bridgePriceWords(c: FindingFinancialsBody["consequence"]): string {
  if (c.state === "QUANTITY_UNAVAILABLE") return "Not applied: no price is applied without a fuel amount";
  if (c.state === "UNPRICED") return "No single price covers this finding's whole time";
  return "Not applied to a current amount";
}

/**
 * The bridge row when no stored version is drawn as current: the finding time, why no price is applied and no
 * amount. It never carries a fuel quantity or an amount, so nothing here can read as a current cost.
 */
function BridgeOnlyTable({ bridge, links, labelledBy }: { bridge: FindingFinancialsBody; links: BridgeLinks; labelledBy: string }) {
  const c = bridge.consequence;
  const span = minutes(bridge.window.start, bridge.window.end);
  return (
    <DataTable labelledBy={labelledBy}>
      <BridgeHead />
      <tbody>
        <tr data-bridge-row="none">
          <td data-bridge-step="fuel">
            {c.state === "QUANTITY_UNAVAILABLE" ? "Fuel amount not calculated for" : "Fuel amount not current for"} the generator time
            of this finding version, {formatInstant(bridge.window.start)} to {formatInstant(bridge.window.end)}
            {span ? ` (${span})` : ""}
          </td>
          <td data-bridge-step="price">{bridgePriceWords(c)}</td>
          <td data-bridge-consequence="none">No current amount</td>
          <td>
            <span className="badge badge--neutral">Modelled</span> No amount shown
          </td>
          <td>
            <ConfidenceNotAssessed />
          </td>
          <td>
            <Link to={links.finding(bridge.finding.id, bridge.selection.revision_id)}>Finding version {bridge.revision.revision_no}</Link>
          </td>
        </tr>
      </tbody>
    </DataTable>
  );
}

/**
 * W1-UX-02: the labelled exact values behind one fuel cost version, for the closed "How this was worked out"
 * disclosure. Values only (IDs, references, the site model and the codes as stored); the method and limits are
 * plain prose in the visible "From finding to money" section.
 */
export function consequenceReferences(
  rev: ConsequenceRevision,
  body: FindingConsequencesBody,
  findingId: string,
  findingRevisionId: string,
): ExactReference[] {
  return [
    { label: "Finding reference", value: findingId },
    { label: "Finding version reference", value: findingRevisionId },
    { label: "Fuel cost version reference", value: rev.id },
    { label: "Previous fuel cost version reference", value: rev.prior_consequence_revision_id },
    { label: "Kind and basis", value: `${rev.consequence_type} · ${rev.basis_kind} · ${rev.state}` },
    { label: "Site fuel model", value: `${rev.model.model_id} · ${rev.model.formula_version} · ${rev.model.parameter_version}` },
    { label: "Fuel use allowance", value: `sfc_upper_multiplier = ${rev.model.sfc_upper_multiplier ?? "none"}` },
    { label: "Fuel use allowance reference", value: rev.model.parameter_sha256 },
    {
      label: "Fuel amount, unrounded",
      value: `${rev.quantity.low ?? "none"} to ${rev.quantity.high ?? "none"} ${rev.quantity.unit} · ${rev.quantity.state}${
        rev.quantity.reason ? ` · ${rev.quantity.reason}` : ""
      }`,
    },
    {
      label: "Price chosen",
      value: `${rev.price.state}${rev.price.reason ? ` · ${rev.price.reason}` : ""}${rev.price.revision_id ? ` · ${rev.price.revision_id}` : ""}`,
    },
    { label: "Amount, unrounded", value: `${rev.amount.low ?? "none"} to ${rev.amount.high ?? "none"} ${rev.amount.currency ?? ""}`.trim() },
    { label: "Readings reference", value: rev.digests.technical_input_sha256 },
    { label: "Fuel cost record reference", value: rev.digests.consequence_basis_sha256 },
    {
      label: "Assessments used",
      value:
        rev.lineage.assessments.map((x) => `${x.assessment_revision_id}${x.is_primary ? " (primary)" : ""}`).join(", ") || null,
    },
    {
      label: "Linked price and site model records",
      value: rev.lineage.assumptions.map((x) => `${x.role} ${x.assumption_revision_id}`).join(", ") || null,
    },
    ...[...rev.limitations, ...body.exclusions].map((l, i) => ({ label: `Limit recorded with this version ${i + 1}`, value: l })),
  ];
}

/**
 * The method and limits of one drawn fuel cost version, in the mock's prose form for "Trade-offs and exclusions",
 * and its counted readings in their own closed table. Exact values are in `consequenceReferences`.
 */
function HowWorkedOut({ rev }: { rev: ConsequenceRevision }) {
  return (
    <div className="v69-prose w1-money-method" data-consequence-method={rev.revision_no}>
      <p>
        <strong>Limits of this figure.</strong> A modelled range from zero up to an upper amount: not fuel saved, not money
        spent, not a physical maximum. Needed or unjudged generator time is never priced; nothing is totalled.
      </p>
      <p className="v69-chart-note" data-consequence-allowance-reviewed={rev.model.parameter_is_reviewed ? "true" : "false"}>
        {rev.model.parameter_is_reviewed
          ? "The fuel use allowance is the reviewed one."
          : "The fuel use allowance is not the reviewed one, so treat this range with care."}
      </p>
    </div>
  );
}

/**
 * W1-F3 review M5: how the range is worked out and the counted readings, folded into the bridge's single
 * "How this was worked out" disclosure (they were two more closed disclosures in Trade-offs).
 */
function MethodDetail({ rev, body }: { rev: ConsequenceRevision; body: FindingConsequencesBody }) {
  const evidence = body.links.evidence_records ?? {};
  return (
    <>
      <div data-consequence-method-detail={rev.revision_no}>
        <p>
          The fuel amount is a modelled upper limit: each accepted generator power reading inside the observed avoidable
          time is multiplied by its length, by the site model's fuel use per kWh, and by an allowance of{" "}
          {rev.model.sfc_upper_multiplier ?? "a stated"} times that fuel use. The lower limit is zero. A reading that
          reaches outside that time, or a gap between readings, means no amount is worked out at all.
        </p>
        <p>
          The price is the one site diesel price that covers this finding's whole time, as it was recorded. A later price
          correction adds a new fuel cost version; it never rewrites this one.
        </p>
      </div>
      {rev.lineage.power_intervals.length > 0 ? (
        <div data-consequence-readings={rev.lineage.power_intervals.length}>
          <p>
            <strong>Generator power readings counted ({rev.lineage.power_intervals.length})</strong>
          </p>
          <DataTable>
            <thead>
              <tr>
                <th scope="col">From</th>
                <th scope="col">To</th>
                <th scope="col">Average kW</th>
                <th scope="col">Litres per kWh</th>
                <th scope="col">Record reference</th>
              </tr>
            </thead>
            <tbody>
              {rev.lineage.power_intervals.map((i) => (
                <tr key={i.evidence_id} data-consequence-reading={i.evidence_id}>
                  <td>{formatInstant(i.interval_start)}</td>
                  <td>{formatInstant(i.interval_end)}</td>
                  <td>{i.mean_kw}</td>
                  <td>{i.sfc_l_per_kwh}</td>
                  <td>
                    {evidence[i.evidence_id] ? (
                      <code data-vocabulary-exempt="source-reference" data-consequence-evidence={evidence[i.evidence_id]}>
                        {i.evidence_id}
                      </code>
                    ) : (
                      <code data-vocabulary-exempt="source-reference">{i.evidence_id}</code>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </div>
      ) : null}
    </>
  );
}

/** W1-F3: the short gap word of the Operating-cost exposure card when no current amount is shown. */
function exposureGapWord(c: FindingFinancialsBody["consequence"]): string {
  const key = c.state === "PRICED" ? (c.currentness !== null && c.currentness !== "CURRENT" ? c.currentness : "NOT_SHOWN") : c.state;
  switch (key) {
    case "QUANTITY_UNAVAILABLE":
      return "Not calculated";
    case "UNPRICED":
      return "Unpriced";
    case "WITHHELD_GENERATOR_SERIES":
    case "MIXED_OR_UNKNOWN_SOURCE":
      return "Withheld";
    case "PENDING":
    case "PENDING_REASSESSMENT":
      return "Not worked out yet";
    case "STALE":
      return "Out of date";
    case "HISTORICAL":
      return "Earlier version";
    case "AUDIT_ONLY":
      return "Record only";
    case "UNAVAILABLE":
      return "Not readable";
    case "NOT_SHOWN":
      return "Not shown";
    default:
      return "Not known";
  }
}

/** W1-F3: the mock's statusbar for Financials. Financials carry no status of their own; this is a count and a scope. */
export function FinancialsStatusBar({ lines, currency, rollUp }: { lines: string; currency: string | null; rollUp?: string }) {
  return (
    <StatusBar items label="Financials scope" data={{ "data-financials-statusbar": "" }}>
      <span className="badge badge--neutral" data-chip="lines">
        {lines}
      </span>
      {/* W1-F3 review H2: the mock's "Data confidence" chip, as an honest unknown. */}
      <span className="badge badge--not-assessed" data-chip="data-confidence" data-not-assessed>
        Data confidence: not assessed
      </span>
      <span className="status-strip__spacer" />
      <span>
        {currency ? `${currency} · ` : ""}selected finding window · no financial status here; status stays on the source
        finding
      </span>
      {/* post-W6 W1-b Q21 / R198: the mock's `Portfolio roll-up` link, to the global Financials list. */}
      {rollUp === undefined ? null : (
        <Link to={rollUp} data-financials-rollup>
          Portfolio roll-up →
        </Link>
      )}
    </StatusBar>
  );
}

/**
 * W1-F3: the three money measures with no supported read (revenue or service, asset exposure, realised savings).
 * Each is "Not established", never zero, and its note is a catalogued gap.
 */
export function NotEstablishedCards() {
  return (
    <>
      <MetricCard
        label="Revenue / service"
        value="Not established"
        word
        tone="muted"
        data={{ "data-financials-metric": "revenue-service" }}
        note={
          <MissingClaim gapId="G-financials-revenue-service" placement="financials.metrics.revenue-service">
            No supported unserved-energy or revenue basis exists for this site, so no revenue or service consequence is stated.
          </MissingClaim>
        }
      />
      <MetricCard
        label="Asset exposure"
        value="Not established"
        word
        tone="muted"
        data={{ "data-financials-metric": "asset-exposure" }}
        note={
          <MissingClaim gapId="G-financials-asset-exposure" placement="financials.metrics.asset-exposure">
            No asset value, replacement cost or warranty terms are recorded for this site, so no asset exposure is stated.
          </MissingClaim>
        }
      />
      <MetricCard
        label="Realised savings"
        value="Not established"
        word
        tone="muted"
        data={{ "data-financials-metric": "realised-savings" }}
        note={
          <MissingClaim gapId="G-financials-realised-savings" placement="financials.metrics.realised-savings">
            Savings need a verified comparison of energy and service with and without a change, which does not exist, so
            none is claimed.
          </MissingClaim>
        }
      />
    </>
  );
}

/** W1-F3: "Trade-offs and exclusions" (`financials:3`): the source gate, what is not included, and the drawn method. */
export function TradeoffsPanel({
  rev,
  body,
  gap,
  technicalBasis = null,
}: {
  rev: ConsequenceRevision | null;
  body: FindingConsequencesBody | null;
  /** A refused read: the gap stated in place of the method. */
  gap?: string;
  /** post-W6 W1-b Q22 / R199: the exact Dispatch Analysis address, or null when none can be formed. */
  technicalBasis?: string | null;
}) {
  return (
    <Panel heading="Trade-offs and exclusions" headingId="site-financials-tradeoffs-heading">
      <div className="v69-prose" data-financials-tradeoffs={rev ? "method" : gap ? "gap" : "general"}>
        <p>
          <strong>When an amount is shown.</strong> Only for a current finding version whose readings come from an
          established source and whose whole time one recorded diesel price covers. Every other state shows no amount,
          and no amount is ever zero by default.
        </p>
        <p>
          <strong>Not included.</strong> The maintenance allowance, revenue or service effects, asset value and realised
          savings are not added. No monthly figure is extrapolated, and lines with different bases are never added
          together.
        </p>
        {gap ? <p className="v69-gap-line">{gap}</p> : null}
        {rev === null && !gap ? <p>Generator time that was needed, or that could not be judged, is never priced.</p> : null}
        {technicalBasis === null ? null : (
          <p>
            <Link to={technicalBasis} data-financials-technical-basis>
              Inspect technical basis →
            </Link>
          </p>
        )}
      </div>
      {rev !== null && body !== null ? <HowWorkedOut rev={rev} /> : null}
    </Panel>
  );
}

/** The mock's closing blue notice on Financials. */
export function FinancialsNotice() {
  return (
    <Notice tone="blue" data={{ "data-financials-notice": "" }}>
      Financials carry no status of their own. Exposure is not a statement of net or realised savings, and lines with
      different bases are not added together.
    </Notice>
  );
}

/** Why no current amount is shown, in plain words: the specific stored reason where the read gives one. */
function whyNoAmount(c: FindingFinancialsBody["consequence"]): string {
  if (c.state === "QUANTITY_UNAVAILABLE") return quantityWords(c.quantity_reason);
  if (c.state === "UNPRICED") return priceWords(c.price_reason);
  return c.reason;
}

const SERIES_KIND_WORDS: Record<string, string> = {
  SEQUENCE_ORDER_INVERTED: "they arrived before an earlier reading and their clock is not proven",
  REPORTS_OVERLAP: "some overlap in time, so no order can be chosen",
};

/** LR-01: how a refused span relates to this finding, in plain words (never claims more than the relation). */
function seriesRelationWords(x: { relation?: string; source?: string }): string {
  if (x.source === "SELECTED_WINDOW") {
    return "These records are within 6 hours of this finding, so no current cost is shown until they are resolved.";
  }
  switch (x.relation) {
    case "CUTS_TAIL":
      return "The finding ends before them and that time is not judged.";
    case "CUTS_HEAD":
      return "The finding starts after them and that time is not judged.";
    case "INSIDE_EPISODE":
      return "They fall inside this finding, so its span is not proven.";
    case "INSIDE_FORMER_EPISODE":
      return "They fall inside an earlier version of this finding.";
    default:
      return "";
  }
}

/** LR-01: why no current amount is shown although a recorded cost exists, with exact links to that record. */
function MoneyLimit({
  c,
  links,
  findingId,
  rev,
}: {
  c: FindingFinancialsBody["consequence"];
  links: BridgeLinks;
  findingId: string;
  rev: string;
}) {
  const gate = c.money_eligibility;
  const limits = gate?.series_limits ?? [];
  const seen = new Set<string>();
  // One line per span and kind: Finding-revision limits come first so their specific wording wins over the
  // generic selected-window one for the same span.
  const ordered = [...limits].sort(
    (a, b) => Number(a.source === "SELECTED_WINDOW") - Number(b.source === "SELECTED_WINDOW"),
  );
  const spans = ordered.filter((x) => {
    const key = `${x.start}|${x.end}|${x.kind}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  return (
    <div data-financials-money-limit={c.state}>
      {c.state === "WITHHELD_GENERATOR_SERIES" ? (
        spans.length > 0 ? (
          <ul className="v69-chart-note w1-money-limits">
            {spans.map((x) => (
              <li key={`${x.start}|${x.end}|${x.kind}`} data-financials-series-limit={x.kind}>
                The order of generator records from {formatInstant(x.start)} to {formatInstant(x.end)} is not proven:{" "}
                {SERIES_KIND_WORDS[x.kind] ?? "they could not be ordered"}. {seriesRelationWords(x)}
              </li>
            ))}
          </ul>
        ) : null
      ) : c.state === "MIXED_OR_UNKNOWN_SOURCE" ? (
        <p className="v69-chart-note" data-financials-source-withheld="true">
          The cost is calculated, but the source of the records behind it is not established, so it is not shown as a
          current cost. The source record above says which records are affected.
        </p>
      ) : (
        <p className="v69-chart-note" data-financials-pending-reassessment="true">
          New evidence or clock proof is being taken into account. The current cost appears once the reassessment and
          the fuel cost recalculation have finished.
        </p>
      )}
      {c.recorded_consequence_revision_id ? (
        <p className="v69-chart-note">
          <Link
            to={links.consequence(findingId, rev, c.recorded_consequence_revision_id)}
            data-financials-recorded-link={c.recorded_consequence_revision_id}
          >
            Open the recorded fuel cost of this finding version
          </Link>{" "}
          (kept for the record, not a current cost).
        </p>
      ) : null}
    </div>
  );
}

/**
 * W1-F3: the v69 `financials` form for one exact Finding version: statusbar, the four money measures, "What
 * happened → what it means in money" (state line, bridge table, limits, exact references), then the pair of
 * "Assumptions in use" (passed in) and "Trade-offs and exclusions", and the closing notice. Every fuel cost version
 * of the site is listed in Assumptions > Interpretation history; an exact one opens here by address.
 */
export function FindingBridge({
  bridge,
  consequences,
  links,
  pinnedConsequence,
  consequencesLoading = false,
  assumptions,
}: {
  bridge: FindingFinancialsBody;
  consequences: FinancialReadResult<FindingConsequencesBody> | null;
  links: BridgeLinks;
  pinnedConsequence: string | null;
  /** The consequences read has not settled: no amount is drawn until it has (its time bounds the amount). */
  consequencesLoading?: boolean;
  /** The "Assumptions in use" panel. */
  assumptions: ReactNode;
}) {
  const c = bridge.consequence;
  const findingId = bridge.finding.id;
  const rev = bridge.selection.revision_id;
  // The only amount this page may call current: a PRICED bridge, CURRENT, with a served range and currency.
  const shown = c.state === "PRICED" && c.currentness === "CURRENT" && c.amount !== null && c.currency !== null;
  const gated =
    c.state === "WITHHELD_GENERATOR_SERIES" || c.state === "PENDING_REASSESSMENT" || c.state === "MIXED_OR_UNKNOWN_SOURCE";
  const body = consequences?.status === "loaded" ? consequences.value : null;
  const head = body?.history.revisions.find((r) => r.id === body.consequence_selection.head_consequence_revision_id) ??
    (body?.consequence?.is_head ? body.consequence : null);
  // A pinned earlier version, or (LR-01) the recorded head that the money gate withholds.
  const pinned =
    pinnedConsequence !== null && body?.consequence && (!body.consequence.is_head || (gated && body.consequence.presented_as_current === false))
      ? body.consequence
      : null;
  if (shown && consequencesLoading) {
    return <p data-financials-bridge-loading="true">Loading the finding's money view.</p>;
  }
  const words = consequenceWords(c, shown);
  const stepHead = shown && body !== null && head ? head : null;
  const drawn = pinned !== null && !bridge.audit_only ? pinned : stepHead;
  const scope = `Finding version ${bridge.revision.revision_no}${bridge.selection.is_latest ? " (latest)" : " (an earlier version)"}, ${formatInstant(
    bridge.window.start,
  )} to ${formatInstant(bridge.window.end)}`;
  const tableProps = {
    links,
    findingId,
    findingRevisionId: rev,
    findingRevisionNo: bridge.revision.revision_no,
    labelledBy: "site-financials-bridge-heading",
  };
  return (
    <>
      <FinancialsStatusBar lines="1 consequence line" currency={c.currency} rollUp={links.portfolio} />
      <div
        data-financials-bridge={c.state}
        data-financials-currentness={c.currentness ?? "NONE"}
        data-finding-id={findingId}
        data-finding-revision={rev}
        data-financials-amount={shown ? "shown" : "none"}
      >
        <MetricCards columns={4} label="Money consequence measures">
          <MetricCard
            label="Operating-cost exposure"
            data={{ "data-financials-metric": "operating-cost" }}
            word={!shown}
            tone={shown ? undefined : "muted"}
            value={
              shown && c.amount !== null && c.currency !== null ? (
                <span data-financials-headline="amount">
                  <strong data-financials-range={`${c.amount.low}-${c.amount.high}`}>{range(c.amount.low, c.amount.high, c.currency)}</strong>
                </span>
              ) : (
                <span data-financials-exposure-gap={c.state}>{exposureGapWord(c)}</span>
              )
            }
            note={
              shown ? (
                "Modelled fuel cost from zero up to an upper amount; not a measured saving"
              ) : (
                <>
                  <span data-financials-headline="none">No current amount is shown for this finding version</span>. This is not zero.
                </>
              )
            }
          />
          <NotEstablishedCards />
        </MetricCards>
        <Panel
          heading="What happened → what it means in money"
          headingId="site-financials-bridge-heading"
          description="Translated once here for this finding version · select the source to return to its finding"
        >
          <div className="v69-state-line w1-money-state-line" data-financials-state-line="">
            <ProductStatus
              inline
              words={words}
              scope={scope}
              // The time the shown range was worked out; no other state has a read instant, so it says so.
              asOf={stepHead !== null ? stepHead.recorded_at : null}
            >
              <SourceProvenanceNotice
                provenance={bridge.source_provenance?.consequence_revision ?? bridge.source_provenance?.finding_revision}
                subject="cost"
                name="bridge"
              />
              {bridge.audit_only ? <span className="notice"> {bridge.audit_only.statement}</span> : null}
            </ProductStatus>
          </div>
          <p className="v69-chart-note">
            For the finding <strong>{bridge.revision.title}</strong>.
          </p>
          {/* W1-F3 review M4: the state line already says why for every other state; only a missing fuel amount
              or price adds its specific stored reason here. */}
          {!shown && (c.state === "QUANTITY_UNAVAILABLE" || c.state === "UNPRICED") ? (
            <p className="v69-chart-note w1-money-why">
              <strong>Why no current amount: </strong>
              <span data-financials-why={c.quantity_reason ?? c.price_reason ?? c.state}>{whyNoAmount(c)}</span>
            </p>
          ) : null}
          {gated ? <MoneyLimit c={c} links={links} findingId={findingId} rev={rev} /> : null}
          {!shown && head && body && !gated ? (
            <p className="v69-chart-note" data-financials-recorded-pointer="true">
              {bridge.audit_only
                ? "No amount is shown while the source is closed."
                : "No amount is shown here because this is not a current cost. Every recorded fuel cost version is listed in Interpretation history, kept for the record."}
            </p>
          ) : null}
          {pinned && body && bridge.audit_only ? (
            <>
              <p className="notice" data-consequence-pinned={pinned.id} data-consequence-pinned-current="false">
                Fuel cost version {pinned.revision_no}, kept for the record. The source is closed, so no amount is shown for
                any version. This is audit material only.
              </p>
              <BridgeOnlyTable bridge={bridge} links={links} labelledBy={tableProps.labelledBy} />
            </>
          ) : pinned && body ? (
            <div data-consequence-pinned={pinned.id} data-consequence-pinned-current="false">
              {pinned.is_head ? (
                <p className="notice" data-consequence-pinned-withheld={c.state}>
                  Fuel cost version {pinned.revision_no}: the recorded fuel cost of this finding version, kept for the
                  record. It is not a current cost. Recorded on {day(pinned.recorded_at)}. {c.reason}{" "}
                  <Link to={links.consequence(findingId, rev, null)}>Back to this finding version's money view</Link>
                </p>
              ) : (
                <p className="notice">
                  Fuel cost version {pinned.revision_no}: an earlier version kept for the record, not the current cost.
                  Recorded on {day(pinned.recorded_at)}, for the same finding version.{" "}
                  {head && head.digests.technical_input_sha256 === pinned.digests.technical_input_sha256
                    ? "Its fuel amount is the same as in the latest version; only the price applied differs."
                    : "Its fuel amount differs from the latest version because the accepted readings behind it changed."}{" "}
                  <Link to={links.consequence(findingId, rev, null)}>Show the current fuel cost</Link>
                </p>
              )}
              <SourceProvenanceNotice provenance={pinned.source_provenance} subject="cost version" name="pinned" />
              <BridgeTable rev={pinned} current={false} {...tableProps} />
            </div>
          ) : stepHead !== null ? (
            <BridgeTable rev={stepHead} current {...tableProps} />
          ) : (
            <BridgeOnlyTable bridge={bridge} links={links} labelledBy={tableProps.labelledBy} />
          )}
          {consequences !== null && consequences.status !== "loaded" ? (
            <p className="v69-gap-line" data-consequence-history={consequences.status}>
              The fuel cost versions of this finding version could not be read, so none is shown.
            </p>
          ) : null}
          <p className="v69-chart-note">
            <Link to={links.evidence(findingId, rev)}>See the evidence for this finding version</Link>
            {" · "}
            <Link to={links.finding(findingId, rev)}>Back to the finding</Link>
            {" · "}
            <Link to={links.assumptions()} data-financials-history-link>
              Every recorded fuel cost version
            </Link>
          </p>
          <ExactReferences
            name="financials-consequence"
            // W1-F3 review M5: the panel's one disclosure, for the drawn (current or pinned) version with its method.
            extra={drawn !== null && body !== null ? <MethodDetail rev={drawn} body={body} /> : undefined}
            references={
              drawn !== null && body !== null
                ? consequenceReferences(drawn, body, findingId, rev)
                : [
                    { label: "Finding reference", value: findingId },
                    { label: "Finding version reference", value: rev },
                    { label: "Money state", value: c.state },
                    { label: "How current", value: c.currentness },
                    {
                      label: "Recorded fuel cost reference",
                      value: c.recorded_consequence_revision_id ?? c.consequence_revision_id ?? null,
                    },
                    { label: "Price version reference", value: c.price_revision_id },
                    ...[...(c.currentness_reasons ?? []), ...(c.withheld_reasons ?? [])].map((r, i) => ({
                      label: `Recorded reason ${i + 1}`,
                      value: r,
                    })),
                  ]
            }
          />
        </Panel>
      </div>
      <div className="panel-pair">
        {assumptions}
        <TradeoffsPanel rev={drawn} body={body} technicalBasis={technicalBasisHref(bridge.window.start, links.dispatchAnalysis)} />
      </div>
      <FinancialsNotice />
    </>
  );
}
