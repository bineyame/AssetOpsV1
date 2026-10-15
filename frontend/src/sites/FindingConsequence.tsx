import { Link } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, Panel } from "../ui";
import type {
  ConsequenceRevision,
  DemonstrationLabel,
  FinancialReadResult,
  FindingConsequencesBody,
  FindingFinancialsBody,
} from "./financialsClient";
import { formatInstant } from "./FoundationRevisionPanel";

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

const STATE_HEADLINE: Record<string, string> = {
  WITHHELD_GENERATOR_SERIES: "Withheld: the generator records are not in a proven time order",
  PENDING_REASSESSMENT: "Being reassessed: no current cost yet",
  UNPRICED: "No price for the whole window",
  QUANTITY_UNAVAILABLE: "Not calculated",
  STALE: "Out of date: no current cost",
  PENDING: "Not worked out yet",
  HISTORICAL: "Earlier finding version: kept for the record",
  AUDIT_ONLY: "For the record only: no current cost",
  UNAVAILABLE: "Could not be read",
  PRICED: "No rounded amount",
};

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

function Demonstration({ demo }: { demo: DemonstrationLabel }) {
  return (
    <p className="notice notice--info" data-financials-demonstration={demo.case_id}>
      <strong>{demo.label}.</strong> {demo.statement}
    </p>
  );
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

/** The lineage disclosure: model, multiplier, IDs, digests and every counted reading. */
function HowWorkedOut({
  rev,
  body,
  findingId,
  findingRevisionId,
}: {
  rev: ConsequenceRevision;
  body: FindingConsequencesBody;
  findingId: string;
  findingRevisionId: string;
}) {
  const evidence = body.links.evidence_records ?? {};
  return (
    <Disclosure summary="How this is worked out" name={`consequence-lineage-${rev.revision_no}`}>
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
      <FactList>
        <Fact term="Finding ID">
          <code data-vocabulary-exempt="source-reference">{findingId}</code>
        </Fact>
        <Fact term="Finding version ID">
          <code data-vocabulary-exempt="source-reference">{findingRevisionId}</code>
        </Fact>
        <Fact term="Fuel cost version ID">
          <code data-vocabulary-exempt="source-reference" data-consequence-lineage-id={rev.id}>{rev.id}</code>
        </Fact>
        <Fact term="Previous fuel cost version ID">
          <code data-vocabulary-exempt="source-reference">{rev.prior_consequence_revision_id ?? "none (first version)"}</code>
        </Fact>
        <Fact term="Kind and basis">
          <code data-vocabulary-exempt="source-reference">
            {rev.consequence_type} · {rev.basis_kind} · {rev.state}
          </code>
        </Fact>
        <Fact term="Model">
          <code data-vocabulary-exempt="source-reference">
            {rev.model.model_id} · {rev.model.formula_version} · {rev.model.parameter_version} · sfc_upper_multiplier ={" "}
            {rev.model.sfc_upper_multiplier ?? "none"}
          </code>
        </Fact>
        <Fact term="Model allowance reviewed">
          {rev.model.parameter_is_reviewed ? "Yes, the reviewed allowance" : "No: this allowance is not the reviewed one"}
        </Fact>
        <Fact term="Model allowance digest">
          <code data-vocabulary-exempt="source-reference">{rev.model.parameter_sha256}</code>
        </Fact>
        <Fact term="Quantity, unrounded">
          <code data-vocabulary-exempt="source-reference">
            {rev.quantity.low ?? "none"} to {rev.quantity.high ?? "none"} {rev.quantity.unit} · {rev.quantity.state}
            {rev.quantity.reason ? ` · ${rev.quantity.reason}` : ""}
          </code>
        </Fact>
        <Fact term="Price selection">
          <code data-vocabulary-exempt="source-reference">
            {rev.price.state}
            {rev.price.reason ? ` · ${rev.price.reason}` : ""}
            {rev.price.revision_id ? ` · ${rev.price.revision_id}` : ""}
          </code>
        </Fact>
        <Fact term="Amount, unrounded">
          <code data-vocabulary-exempt="source-reference">
            {rev.amount.low ?? "none"} to {rev.amount.high ?? "none"} {rev.amount.currency ?? ""}
          </code>
        </Fact>
        <Fact term="Technical input digest">
          <code data-vocabulary-exempt="source-reference">{rev.digests.technical_input_sha256}</code>
        </Fact>
        <Fact term="Fuel cost record digest">
          <code data-vocabulary-exempt="source-reference">{rev.digests.consequence_basis_sha256}</code>
        </Fact>
        <Fact term="Assessments">
          <code data-vocabulary-exempt="source-reference">
            {rev.lineage.assessments.map((a) => `${a.assessment_revision_id}${a.is_primary ? " (primary)" : ""}`).join(", ") ||
              "none"}
          </code>
        </Fact>
        <Fact term="Price and model versions linked">
          <code data-vocabulary-exempt="source-reference">
            {rev.lineage.assumptions.map((a) => `${a.role} ${a.assumption_revision_id}`).join(", ") || "none"}
          </code>
        </Fact>
      </FactList>
      {rev.lineage.power_intervals.length > 0 ? (
        <>
          <h3 className="panel__subheading" id={`consequence-readings-${rev.revision_no}`}>
            Generator power readings counted ({rev.lineage.power_intervals.length})
          </h3>
          <DataTable labelledBy={`consequence-readings-${rev.revision_no}`}>
            <thead>
              <tr>
                <th scope="col">From</th>
                <th scope="col">To</th>
                <th scope="col">Average kW</th>
                <th scope="col">Litres per kWh</th>
                <th scope="col">Record</th>
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
        </>
      ) : null}
      <h3 className="panel__subheading">Limits of this figure</h3>
      <ul>
        <li>It is a modelled range from zero up to an upper amount, not fuel saved, not money spent and not a physical maximum.</li>
        <li>Generator time that was needed, or that could not be judged, is never priced.</li>
        <li>No total is added up across findings, versions, currencies or time windows.</li>
      </ul>
      <p className="muted">Limits as recorded with this version:</p>
      <ul data-consequence-limitations={rev.limitations.length}>
        {[...rev.limitations, ...body.exclusions].map((l) => (
          <li key={l}>
            <code data-vocabulary-exempt="source-reference">{l}</code>
          </li>
        ))}
      </ul>
    </Disclosure>
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

/** The money headline: an amount only for a CURRENT PRICED bridge with a display range. */
function Headline({ bridge }: { bridge: FindingFinancialsBody }) {
  const c = bridge.consequence;
  const shown = c.state === "PRICED" && c.currentness === "CURRENT" && c.amount !== null && c.currency !== null;
  if (shown && c.amount && c.currency) {
    return (
      <div data-financials-headline="amount">
        <dl className="metric-row">
          <div className="metric">
            <dt>Modelled potential fuel-cost exposure</dt>
            <dd data-financials-range={`${c.amount.low}-${c.amount.high}`}>{range(c.amount.low, c.amount.high, c.currency)}</dd>
          </div>
        </dl>
        <p>
          Modelled potential fuel-cost exposure: {c.amount.low} to {c.amount.high} {c.currency}, under the reviewed fuel-cost-1
          assumptions. This is not measured fuel saved or a physical maximum.
        </p>
      </div>
    );
  }
  const why =
    c.state === "QUANTITY_UNAVAILABLE"
      ? quantityWords(c.quantity_reason)
      : c.state === "UNPRICED"
        ? priceWords(c.price_reason)
        : c.reason;
  return (
    <FactList>
      <Fact term="Cost">{STATE_HEADLINE[c.state] ?? "No cost shown"}</Fact>
      <Fact term="Why">
        <span data-financials-why={c.quantity_reason ?? c.price_reason ?? c.state}>{why}</span>
      </Fact>
    </FactList>
  );
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
}: {
  bridge: FindingFinancialsBody;
  consequences: FinancialReadResult<FindingConsequencesBody> | null;
  links: BridgeLinks;
  pinnedConsequence: string | null;
}) {
  const c = bridge.consequence;
  const findingId = bridge.finding.id;
  const rev = bridge.selection.revision_id;
  const shown = c.state === "PRICED" && c.currentness === "CURRENT" && c.amount !== null;
  const gated = c.state === "WITHHELD_GENERATOR_SERIES" || c.state === "PENDING_REASSESSMENT";
  const body = consequences?.status === "loaded" ? consequences.value : null;
  const head = body?.history.revisions.find((r) => r.id === body.consequence_selection.head_consequence_revision_id) ??
    (body?.consequence?.is_head ? body.consequence : null);
  // A pinned earlier version, or (LR-01) the recorded head that the money gate withholds.
  const pinned =
    pinnedConsequence !== null && body?.consequence && (!body.consequence.is_head || (gated && body.consequence.presented_as_current === false))
      ? body.consequence
      : null;
  return (
    <>
      <Panel
        heading="What this finding means in money"
        headingId="site-financials-bridge-heading"
        description="A modelled estimate, not a measured saving. Financials have no status of their own; the finding keeps its own status."
      >
        <div
          data-financials-bridge={c.state}
          data-financials-currentness={c.currentness ?? "NONE"}
          data-finding-id={findingId}
          data-finding-revision={rev}
          data-financials-amount={shown ? "shown" : "none"}
        >
          <p className="financials-lead">
            <strong>{bridge.revision.title}</strong>, version {bridge.revision.revision_no}
            {bridge.selection.is_latest ? " (latest)" : " (an earlier version)"}, {formatInstant(bridge.window.start)} to{" "}
            {formatInstant(bridge.window.end)}.
          </p>
          {bridge.demonstration ? <Demonstration demo={bridge.demonstration} /> : null}
          {bridge.audit_only ? <p className="notice">{bridge.audit_only.statement}</p> : null}
          <Headline bridge={bridge} />
          {gated ? <MoneyLimit c={c} links={links} findingId={findingId} rev={rev} /> : null}
          {head && body && shown ? (
            <>
              <h3 className="panel__subheading" id="site-financials-bridge-steps">
                From finding to money
              </h3>
              <BridgeTable rev={head} current links={links} headingId="site-financials-bridge-steps" />
              <HowWorkedOut rev={head} body={body} findingId={findingId} findingRevisionId={rev} />
            </>
          ) : head && body && !gated ? (
            <p data-financials-recorded-pointer="true">
              {bridge.audit_only
                ? "No amount is shown while the source is closed."
                : "No amount is shown here because this is not a current cost. Earlier fuel cost versions are listed under Fuel cost versions, kept for the record."}
            </p>
          ) : null}
          <p>
            <Link to={links.evidence(findingId, rev)}>See the evidence for this finding version</Link>
            {" · "}
            <Link to={links.finding(findingId, rev)}>Back to the finding</Link>
          </p>
        </div>
      </Panel>
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
            <BridgeTable
              rev={pinned}
              current={false}
              links={links}
              headingId="site-financials-consequence-version-heading"
            />
            <HowWorkedOut rev={pinned} body={body} findingId={findingId} findingRevisionId={rev} />
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
