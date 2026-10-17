import { Link } from "react-router-dom";

import {
  DataTable,
  Disclosure,
  ExactReferences,
  HeadlineVisualCard,
  moneyWords,
  Panel,
  ProductStatus,
  StepStrip,
  ValueBars,
  type ExactReference,
  type ProductWords,
  type Step,
} from "../ui";
import "./w1ux02-money.css";
import type {
  ConsequenceRevision,
  FinancialReadResult,
  FindingConsequencesBody,
  FindingFinancialsBody,
} from "./financialsClient";
import { formatInstant } from "./FoundationRevisionPanel";
import { SOURCE_WORDS, SourceProvenanceNotice, sourceState } from "./sourceProvenance";

/**
 * S4-02b phase 2b: the Finding bridge on Site > Financials > Overview, over the stored `fuel-cost-1`
 * consequence of one exact Finding version.
 *
 * - An amount appears only when the bridge holds a CURRENT PRICED head with a display range. It is a modelled,
 *   assumption-conditioned potential fuel-cost exposure "from 0 up to X", never a point saving.
 * - Every other state (no price, quantity unavailable, not yet worked out, out of date, an earlier finding version,
 *   a source not open for current use, the store unreadable) is a typed state with no amount.
 * - Earlier fuel cost versions stay inspectable by ID and are labelled as kept for the record.
 * - Identifiers, digests, the model version and enum names sit only in the "How this is worked out" disclosure.
 */

export interface BridgeLinks {
  finding: (findingId: string, revisionId: string) => string;
  evidence: (findingId: string, revisionId: string) => string;
  assumptions: (pin?: { revisionId?: string | null; recordedAt?: string | null }) => string;
  /** The Overview pinned to one exact consequence version of the same Finding version (null: the latest). */
  consequence: (findingId: string, revisionId: string, consequenceRevisionId: string | null) => string;
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

/** One version's quantity, price and amount as stored. `current` decides whether its amount reads as current. */
function BridgeTable({
  rev,
  current,
  links,
  headingId,
}: {
  rev: ConsequenceRevision;
  current: boolean;
  links: BridgeLinks;
  headingId: string;
}) {
  const priced = rev.state === "PRICED" && rev.display?.state === "ROUNDED_OUTWARD";
  const span = minutes(rev.window.start, rev.window.end);
  return (
    <DataTable labelledBy={headingId}>
      <thead>
        <tr>
          <th scope="col">Step</th>
          <th scope="col">Value</th>
          <th scope="col">What it rests on</th>
        </tr>
      </thead>
      <tbody>
        <tr data-bridge-step="time">
          <th scope="row">Finding time</th>
          <td>
            {formatInstant(rev.window.start)} to {formatInstant(rev.window.end)}
            {span ? ` (${span})` : ""}
          </td>
          <td>Only the observed avoidable generator time inside it is counted</td>
        </tr>
        <tr data-bridge-step="fuel">
          <th scope="row">Diesel</th>
          <td>
            {rev.quantity.high_display !== null ? range("0", rev.quantity.high_display, "litres") : "Not calculated"}
          </td>
          <td>
            {rev.quantity.high_display !== null
              ? `Accepted generator power readings and the site model's fuel use, with up to ${
                  rev.model.sfc_upper_multiplier ?? "a stated"
                } times that fuel use allowed`
              : quantityWords(rev.quantity.reason)}
          </td>
        </tr>
        <tr data-bridge-step="price">
          <th scope="row">Diesel price</th>
          <td>
            {rev.price.value !== null && rev.price.currency !== null
              ? `${rev.price.value} ${rev.price.currency} per litre`
              : rev.state === "QUANTITY_UNAVAILABLE"
                ? "Not applied"
                : "No single price"}
          </td>
          <td>
            {rev.price.revision_id !== null ? (
              <Link to={links.assumptions({ revisionId: rev.price.revision_id })} data-bridge-price-revision={rev.price.revision_id}>
                The site price version used
              </Link>
            ) : rev.state === "QUANTITY_UNAVAILABLE" ? (
              "No price is applied without a fuel amount"
            ) : (
              priceWords(rev.price.reason)
            )}
          </td>
        </tr>
        <tr data-bridge-step="amount">
          <th scope="row">Fuel-cost exposure</th>
          <td data-bridge-amount={priced ? (current ? "current" : "recorded") : "none"}>
            {priced && rev.display ? (
              <strong>{range(rev.display.amount_low ?? "", rev.display.amount_high ?? "", rev.display.currency)}</strong>
            ) : (
              "No cost shown"
            )}
          </td>
          <td>{priced ? (current ? "Modelled range; not a measured saving" : "Recorded for this version; not the current cost") : revisionWhy(rev)}</td>
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
 * The visible method and limits of one fuel cost version, and its counted readings in their own closed table.
 * Plain prose; exact values are in `consequenceReferences`.
 */
function HowWorkedOut({ rev, body }: { rev: ConsequenceRevision; body: FindingConsequencesBody }) {
  const evidence = body.links.evidence_records ?? {};
  return (
    <div className="w1-money-method" data-consequence-method={rev.revision_no}>
      <h3 className="panel__subheading">How the range is worked out</h3>
      <p>
        The fuel amount is a modelled upper limit: each accepted generator power reading inside the observed avoidable time
        is multiplied by its length, by the site model's fuel use per kWh, and by an allowance of{" "}
        {rev.model.sfc_upper_multiplier ?? "a stated"} times that fuel use. The lower limit is zero. A reading that reaches
        outside that time, or a gap between readings, means no amount is worked out at all.
      </p>
      <p>
        The price is the one site diesel price that covers this finding's whole time, as it was recorded. A later price
        correction adds a new fuel cost version; it never rewrites this one.
      </p>
      <p data-consequence-allowance-reviewed={rev.model.parameter_is_reviewed ? "true" : "false"}>
        {rev.model.parameter_is_reviewed
          ? "The fuel use allowance is the reviewed one."
          : "The fuel use allowance is not the reviewed one, so treat this range with care."}
      </p>
      <h3 className="panel__subheading">Limits of this figure</h3>
      <ul>
        <li>It is a modelled range from zero up to an upper amount, not fuel saved, not money spent and not a physical maximum.</li>
        <li>Generator time that was needed, or that could not be judged, is never priced.</li>
        <li>No total is added up across findings, versions, currencies or time windows.</li>
      </ul>
      {rev.lineage.power_intervals.length > 0 ? (
        <Disclosure
          summary={`Generator power readings counted (${rev.lineage.power_intervals.length})`}
          name={`consequence-readings-${rev.revision_no}`}
        >
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
        </Disclosure>
      ) : null}
    </div>
  );
}

function versionWords(rev: ConsequenceRevision, hideAmount: boolean): string {
  if (rev.state === "PRICED" && hideAmount) return "No cost shown: the source is closed, so this is audit material only";
  if (rev.state === "PRICED" && rev.display?.state === "ROUNDED_OUTWARD") {
    return `${range(rev.display.amount_low ?? "", rev.display.amount_high ?? "", rev.display.currency)}, at ${
      rev.price.value ?? ""
    } ${rev.price.currency ?? ""} per litre`;
  }
  if (rev.state === "UNPRICED") return "No cost: no single price for the whole window";
  if (rev.state === "QUANTITY_UNAVAILABLE") return "No cost: the fuel amount is not calculated";
  return "No cost shown";
}

/** A served display string as a bar length only; the text always stays the served string. */
function barValue(text: string): number | null {
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}

/**
 * W1-UX-02: the basis and limit visual. An amount is drawn only for a current priced bridge; every other state
 * draws the shared "not known" mark, never a zero bar. The step strip says what the amount rests on, from the
 * bridge read only.
 */
function MoneyVisual({ bridge, shown }: { bridge: FindingFinancialsBody; shown: boolean }) {
  const c = bridge.consequence;
  const steps: Step[] = [
    {
      label: "Finding time",
      state: bridge.window.end === null ? "not-known" : "done",
      detail: `${formatInstant(bridge.window.start)} to ${formatInstant(bridge.window.end)}`,
    },
    shown && c.quantity !== null
      ? { label: "Fuel amount", state: "done", detail: `Up to ${c.quantity.high} litres` }
      : c.state === "QUANTITY_UNAVAILABLE"
        ? { label: "Fuel amount", state: "problem", detail: "Not calculated" }
        : { label: "Fuel amount", state: "not-known", detail: "Not current" },
    shown
      ? { label: "Diesel price", state: "done", detail: "The site price version used" }
      : c.state === "UNPRICED"
        ? { label: "Diesel price", state: "problem", detail: "No single price for the whole time" }
        : c.state === "QUANTITY_UNAVAILABLE"
          ? { label: "Diesel price", state: "waiting", detail: "Not applied without a fuel amount" }
          : { label: "Diesel price", state: "not-known", detail: "Not current" },
    shown
      ? { label: "Current amount", state: "done", detail: "Modelled range" }
      : c.state === "WITHHELD_GENERATOR_SERIES" || c.state === "MIXED_OR_UNKNOWN_SOURCE"
        ? { label: "Current amount", state: "problem", detail: "Withheld" }
        : c.state === "PENDING_REASSESSMENT" || c.state === "PENDING"
          ? { label: "Current amount", state: "waiting", detail: "Not worked out yet" }
          : { label: "Current amount", state: "not-known", detail: "Not shown" },
  ];
  return (
    <div className="w1-money-visual">
      {shown && c.amount !== null && c.currency !== null ? (
        <ValueBars
          title="Modelled fuel-cost range"
          items={[
            { label: "Lower end", key: "low", value: barValue(c.amount.low), valueText: `${c.amount.low} ${c.currency}` },
            { label: "Upper end", key: "high", value: barValue(c.amount.high), valueText: `${c.amount.high} ${c.currency}` },
          ]}
        />
      ) : (
        <ValueBars title="Current fuel-cost amount" items={[{ label: "Current amount", key: "none", value: null, valueText: "" }]} />
      )}
      <StepStrip title="What the amount rests on" steps={steps} />
    </div>
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
          <ul>
            {spans.map((x) => (
              <li key={`${x.start}|${x.end}|${x.kind}`} data-financials-series-limit={x.kind}>
                The order of generator records from {formatInstant(x.start)} to {formatInstant(x.end)} is not proven:{" "}
                {SERIES_KIND_WORDS[x.kind] ?? "they could not be ordered"}. {seriesRelationWords(x)}
              </li>
            ))}
          </ul>
        ) : null
      ) : c.state === "MIXED_OR_UNKNOWN_SOURCE" ? (
        <p data-financials-source-withheld="true">
          The cost is calculated, but the source of the records behind it is not established, so it is not shown as a
          current cost. The source record above says which records are affected.
        </p>
      ) : (
        <p data-financials-pending-reassessment="true">
          New evidence or clock proof is being taken into account. The current cost appears once the reassessment and
          the fuel cost recalculation have finished.
        </p>
      )}
      {c.recorded_consequence_revision_id ? (
        <p>
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

export function FindingBridge({
  bridge,
  consequences,
  links,
  pinnedConsequence,
  consequencesLoading = false,
}: {
  bridge: FindingFinancialsBody;
  consequences: FinancialReadResult<FindingConsequencesBody> | null;
  links: BridgeLinks;
  pinnedConsequence: string | null;
  /** The consequences read has not settled: no amount is drawn until it has (its time bounds the amount). */
  consequencesLoading?: boolean;
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
  const scope = `Finding version ${bridge.revision.revision_no}${bridge.selection.is_latest ? " (latest)" : " (an earlier version)"}, ${formatInstant(
    bridge.window.start,
  )} to ${formatInstant(bridge.window.end)}`;
  return (
    <>
      <div
        data-financials-bridge={c.state}
        data-financials-currentness={c.currentness ?? "NONE"}
        data-finding-id={findingId}
        data-finding-revision={rev}
        data-financials-amount={shown ? "shown" : "none"}
      >
        <HeadlineVisualCard
          dataName="financials-consequence"
          headingId="site-financials-bridge-heading"
          title="What this finding means in money"
          description="A modelled estimate, not a measured saving. Financials have no status of their own; the finding keeps its own status."
          question="What is the bounded economic consequence?"
          headline={
            shown && c.amount !== null && c.currency !== null ? (
              <span data-financials-headline="amount">
                Modelled potential fuel-cost exposure:{" "}
                <strong data-financials-range={`${c.amount.low}-${c.amount.high}`}>{range(c.amount.low, c.amount.high, c.currency)}</strong>
              </span>
            ) : (
              <span data-financials-headline="none">No current amount is shown for this finding version</span>
            )
          }
          status={
            <ProductStatus
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
              {bridge.audit_only ? <p className="notice">{bridge.audit_only.statement}</p> : null}
            </ProductStatus>
          }
          visual={<MoneyVisual bridge={bridge} shown={shown} />}
          meaning={
            <>
              <p className="financials-lead">
                For the finding <strong>{bridge.revision.title}</strong>.
              </p>
              {shown && c.amount !== null && c.currency !== null ? (
                <p>
                  Modelled potential fuel-cost exposure: {c.amount.low} to {c.amount.high} {c.currency}, under the reviewed
                  fuel cost assumptions. This is not measured fuel saved or a physical maximum.
                </p>
              ) : (
                <p className="w1-money-why">
                  <strong>Why no current amount: </strong>
                  <span data-financials-why={c.quantity_reason ?? c.price_reason ?? c.state}>{whyNoAmount(c)}</span>
                </p>
              )}
              {gated ? <MoneyLimit c={c} links={links} findingId={findingId} rev={rev} /> : null}
              {!shown && head && body && !gated ? (
                <p data-financials-recorded-pointer="true">
                  {bridge.audit_only
                    ? "No amount is shown while the source is closed."
                    : "No amount is shown here because this is not a current cost. Earlier fuel cost versions are listed under Fuel cost versions, kept for the record."}
                </p>
              ) : null}
            </>
          }
          todo={words.next === undefined ? undefined : <p>{words.next}</p>}
          destination={
            <>
              <Link to={links.evidence(findingId, rev)}>See the evidence for this finding version</Link>
              {" · "}
              <Link to={links.finding(findingId, rev)}>Back to the finding</Link>
            </>
          }
          references={
            <ExactReferences
              name="financials-consequence"
              references={
                stepHead !== null && body !== null
                  ? consequenceReferences(stepHead, body, findingId, rev)
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
          }
        />
        {stepHead !== null && body !== null ? (
          <Panel heading="From finding to money" headingId="site-financials-bridge-steps">
            <BridgeTable rev={stepHead} current links={links} headingId="site-financials-bridge-steps" />
            <HowWorkedOut rev={stepHead} body={body} />
          </Panel>
        ) : null}
      </div>
      {pinned && body && bridge.audit_only ? (
        <Panel
          heading={`Fuel cost version ${pinned.revision_no}`}
          headingId="site-financials-consequence-version-heading"
          description="An earlier fuel cost version of the same finding version, kept for the record."
        >
          <p className="notice" data-consequence-pinned={pinned.id} data-consequence-pinned-current="false">
            The source is closed, so no amount is shown for any version. This is audit material only.
          </p>
        </Panel>
      ) : pinned && body ? (
        <Panel
          heading={`Fuel cost version ${pinned.revision_no}`}
          headingId="site-financials-consequence-version-heading"
          description={
            pinned.is_head
              ? "The recorded fuel cost of this finding version, kept for the record. It is not a current cost."
              : "An earlier fuel cost version of the same finding version, kept for the record. It is not the current cost."
          }
        >
          <div data-consequence-pinned={pinned.id} data-consequence-pinned-current="false">
            {pinned.is_head ? (
              <p className="notice" data-consequence-pinned-withheld={c.state}>
                Recorded on {day(pinned.recorded_at)}. {c.reason}{" "}
                <Link to={links.consequence(findingId, rev, null)}>Back to this finding version's money view</Link>
              </p>
            ) : (
              <p className="notice">
                Recorded on {day(pinned.recorded_at)}, for the same finding version.{" "}
                {head && head.digests.technical_input_sha256 === pinned.digests.technical_input_sha256
                  ? "Its fuel amount is the same as in the latest version; only the price applied differs."
                  : "Its fuel amount differs from the latest version because the accepted readings behind it changed."}{" "}
                <Link to={links.consequence(findingId, rev, null)}>Show the current fuel cost</Link>
              </p>
            )}
            <SourceProvenanceNotice provenance={pinned.source_provenance} subject="cost version" name="pinned" />
            <BridgeTable
              rev={pinned}
              current={false}
              links={links}
              headingId="site-financials-consequence-version-heading"
            />
            <HowWorkedOut rev={pinned} body={body} />
            <ExactReferences name={`consequence-pinned-${pinned.revision_no}`} references={consequenceReferences(pinned, body, findingId, rev)} />
          </div>
        </Panel>
      ) : null}
      <ConsequenceHistory
        read={consequences}
        findingId={findingId}
        findingRevisionId={rev}
        links={links}
        selected={body?.consequence?.id ?? null}
        bridgeCurrent={c.currentness === "CURRENT" && !gated}
        gated={gated}
        hideAmounts={bridge.audit_only !== null && bridge.audit_only !== undefined}
      />
    </>
  );
}

function ConsequenceHistory({
  read,
  findingId,
  findingRevisionId,
  links,
  selected,
  bridgeCurrent,
  hideAmounts,
  gated,
}: {
  bridgeCurrent: boolean;
  gated: boolean;
  hideAmounts: boolean;
  read: FinancialReadResult<FindingConsequencesBody> | null;
  findingId: string;
  findingRevisionId: string;
  links: BridgeLinks;
  selected: string | null;
}) {
  return (
    <Panel
      heading="Fuel cost versions"
      headingId="site-financials-consequence-history-heading"
      description="Every fuel cost version of this finding version, oldest first. A later price or correction adds a version; earlier ones stay as recorded."
    >
      {read === null ? (
        <p>Loading the fuel cost versions.</p>
      ) : read.status !== "loaded" ? (
        <p data-consequence-history={read.status}>The fuel cost versions could not be read, so none is shown.</p>
      ) : read.value.history.revisions.length === 0 ? (
        <p data-consequence-history="empty">No fuel cost version has been recorded for this finding version yet.</p>
      ) : (
        <>
          <ol className="price-history" data-consequence-history="loaded">
            {read.value.history.revisions.map((r) => {
              const head = r.id === read.value.consequence_selection.head_consequence_revision_id;
              const current =
                head && bridgeCurrent && read.value.currentness.state === "CURRENT" && read.value.currentness.current_amount_shown;
              return (
                <li
                  key={r.id}
                  data-consequence-revision={r.id}
                  data-consequence-current={current ? "true" : "false"}
                  aria-current={r.id === selected ? "true" : undefined}
                >
                  <p>
                    <strong>Version {r.revision_no}</strong> · recorded {day(r.recorded_at)} · {versionWords(r, hideAmounts)}
                    {current ? " · the current fuel cost" : " · kept for the record"}
                    {" · "}
                    <span data-consequence-source={sourceState(r.source_provenance)}>
                      {SOURCE_WORDS[sourceState(r.source_provenance)].label}
                    </span>
                  </p>
                  <p>
                    <Link to={links.consequence(findingId, findingRevisionId, head && !gated ? null : r.id)}>
                      Open fuel cost version {r.revision_no}
                    </Link>
                    {r.price.revision_id ? (
                      <>
                        {" · "}
                        <Link to={links.assumptions({ revisionId: r.price.revision_id })}>Price version used</Link>
                      </>
                    ) : null}
                  </p>
                </li>
              );
            })}
          </ol>
          <p className="muted">
            Showing {read.value.history.revisions.length} of {read.value.history.total} version
            {read.value.history.total === 1 ? "" : "s"}, all for finding version {read.value.selection.revision_no}.{" "}
            {new Set(read.value.history.revisions.map((r) => r.digests.technical_input_sha256)).size === 1
              ? "The fuel amount is the same in every version shown."
              : "The fuel amount differs between versions because the accepted readings behind it changed."}
          </p>
        </>
      )}
    </Panel>
  );
}
