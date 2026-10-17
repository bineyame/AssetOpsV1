import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import {
  DataTable,
  Disclosure,
  ExactReferences,
  KeyValues,
  MetricCard,
  MetricCards,
  MissingClaim,
  moneyWords,
  Notice,
  Panel,
  ProductStatus,
  readResultWords,
  type ExactReference,
  type ProductWords,
  type ReadResultKind,
} from "../ui";
import { ConsequenceHistoryPanel, ConsequenceHistoryRefused } from "./ConsequenceHistory";
import type {
  AssumptionRevisionBody,
  ConsequenceHistoryBody,
  ConsequenceHistoryResult,
  AssumptionSeriesBody,
  FinancialReadResult,
  FinancialsClient,
  FindingConsequencesBody,
  FindingFinancialsBody,
  PriceAssignment,
  PriceRevision,
} from "./financialsClient";
import { FinancialsNotice, FinancialsStatusBar, FindingBridge, NotEstablishedCards, TradeoffsPanel } from "./FindingConsequence";
import { formatInstant } from "./FoundationRevisionPanel";
import "./w1ux02-money.css";

/**
 * S4-02a/S4-02b, W1-F3: Site > Financials in the v69 form. Overview (`financials`): statusbar, four money measures
 * (Operating-cost exposure is the current gated fuel range only when the read proves it; revenue or service, asset
 * exposure and realised savings are catalogued "Not established" gaps), "What happened → what it means in money"
 * (the exact Finding version's bridge, `FindingConsequence.tsx`), then "Assumptions in use" and "Trade-offs and
 * exclusions", and the closing notice. Assumptions (`assumptions`): notice, "Financial assumptions" (exact price,
 * fields, disabled edit with its reason, strip and schedule), "Impact preview" (a catalogued gap; no example result)
 * and "Interpretation history" (S4-08 fuel cost versions and the price versions, recorded at one moment).
 * Identifiers, digests and enum names sit in the closed exact-reference disclosures.
 *
 * Not built: the maintenance accrual consequence line, the Scenarios subtab, cash flow, FX and monthly
 * extrapolation (`.agent/S4-02b-review-packet.md`).
 */

export interface FinancialsLinks {
  /** The exact Finding version. */
  finding: (findingId: string, revisionId: string) => string;
  /** The Finding version's accepted evidence (S4-03). */
  evidence: (findingId: string, revisionId: string) => string;
  /** Assumptions, optionally pinned to an exact version or a recorded cutoff. */
  assumptions: (pin?: {
    revisionId?: string | null;
    recordedAt?: string | null;
    historyAfter?: string | null;
    historyLimit?: number | null;
  }) => string;
  /** The Overview pinned to one exact fuel cost version of the same Finding version (null: the latest). */
  consequence: (findingId: string, revisionId: string, consequenceRevisionId: string | null) => string;
  findings: string;
}

const BASIS_WORDS: Record<string, string> = {
  AUTHORED_ESTIMATE: "An estimate written for this site",
  CONTRACT_RATE: "A contract rate",
  RECORDED_PURCHASE: "A recorded fuel purchase",
};

const CHANGE_WORDS: Record<string, string> = {
  INITIAL: "First price",
  SUCCESSION: "Scheduled change",
  CORRECTION: "Correction",
};

function day(value: string | null): string {
  if (value === null) return "no end date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

function setBy(price: PriceRevision): string {
  return price.actor.kind === "SYSTEM" ? "the system" : "an operator";
}

function priceText(price: PriceRevision): string {
  return `${price.value} ${price.currency} per litre`;
}

function applies(valid: { from: string; to: string | null }): string {
  return valid.to === null ? `from ${day(valid.from)}, with no end date` : `from ${day(valid.from)} until ${day(valid.to)}`;
}

function refusalWords(
  status: Exclude<FinancialReadResult<unknown>, { status: "loaded" }>["status"],
  what: string,
): { heading: string; text: string } {
  const words: Record<typeof status, { heading: string; text: string }> = {
    not_found: { heading: `No such ${what}`, text: `This site has no ${what} with that reference. Nothing else is shown in its place.` },
    unauthenticated: { heading: "Sign in required", text: "Sign in to read this site's prices." },
    forbidden: { heading: "No access", text: "Your account has no access to this site." },
    closed: { heading: "Not released", text: "This finding's source is not released, so only an exact finding version can be opened." },
    unavailable: { heading: "Prices unavailable", text: "The price store could not be read, so nothing is known about this site's prices right now." },
  };
  return words[status];
}

/** W1-UX-02: how a refused read ended, in the shared words. Refused and unavailable are never empty. */
const READ_KIND: Record<Exclude<FinancialReadResult<unknown>, { status: "loaded" }>["status"], ReadResultKind> = {
  not_found: "not-found",
  unauthenticated: "refused",
  forbidden: "refused",
  closed: "refused",
  unavailable: "unavailable",
};

/**
 * One read, keyed on its request. The stored result carries the deps it answered, and a result whose deps differ
 * from this render's is treated as still loading (W1-UX-06, W1-UX-02 re-review N1): the effect that clears the old
 * result runs after render, so without the key one commit could pair a new request with the previous answer (for
 * example, an amount drawn with "time not recorded" before its consequences read starts).
 */
function useRead<T, R = FinancialReadResult<T>>(load: () => Promise<R>, deps: unknown[]): R | null {
  const [read, setRead] = useState<{ deps: unknown[]; value: R } | null>(null);
  useEffect(() => {
    let active = true;
    setRead(null);
    void load().then((next) => {
      if (active) setRead({ deps, value: next });
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  if (read === null || !sameDeps(read.deps, deps)) return null;
  return read.value;
}

function sameDeps(a: unknown[], b: unknown[]): boolean {
  return a.length === b.length && a.every((v, i) => Object.is(v, b[i]));
}

/** W1-UX-02: the labelled exact values of one price version, for the closed "How this was worked out" disclosure. */
function priceReferences(price: PriceRevision, assignment?: PriceAssignment): ExactReference[] {
  return [
    { label: "Price version reference", value: price.revision_id },
    { label: "Previous price version reference", value: price.prior_revision_id },
    ...(assignment ? [{ label: "Schedule entry reference", value: assignment.assignment_id }] : []),
    { label: "Key and unit", value: `${price.assumption_key} · ${price.unit}` },
    { label: "Basis and change", value: `${price.basis} · ${price.change_kind}` },
    { label: "Published by", value: `${price.actor.kind} · ${price.actor.id} · ${price.channel}` },
    { label: "Authority", value: price.authorization_basis },
    { label: "Recorded at", value: price.recorded_at },
    { label: "Publication key", value: price.idempotency_key },
    { label: "Request reference", value: price.request_sha256 },
  ];
}

type StripState = "in-use" | "recorded-then" | "ended" | "later" | "not-known";

const STRIP_WORDS: Record<StripState, string> = {
  "in-use": "In use today",
  "recorded-then": "Covered today, as recorded then",
  ended: "Ended",
  later: "Starts later",
  "not-known": "Not known",
};

/**
 * W1-UX-02: the price effective-time strip. Each schedule entry the read returned, in order, with its dates,
 * price and whether it applies at the time the read was asked about. The entry in use is the one the read
 * selected; the others are placed only by their own recorded dates. Nothing is inferred beyond that.
 */
function PriceTimeStrip({ body, historical }: { body: AssumptionSeriesBody; historical: boolean }) {
  if (body.timeline.length === 0) return null;
  const selected = body.selection?.state === "PRICED" ? body.selection.assignment_id : null;
  const at = body.selection ? new Date(body.selection.valid_at).getTime() : Number.NaN;
  const stateOf = (a: PriceAssignment): StripState => {
    if (a.assignment_id === selected) return historical ? "recorded-then" : "in-use";
    if (Number.isNaN(at)) return "not-known";
    if (a.valid.to !== null && new Date(a.valid.to).getTime() <= at) return "ended";
    if (new Date(a.valid.from).getTime() > at) return "later";
    return "not-known";
  };
  return (
    <figure className="w1-money-strip" data-price-strip={body.timeline.length}>
      <figcaption className="w1-money-strip__title">When each price applies</figcaption>
      <ol className="w1-money-strip__list">
        {body.timeline.map((a) => {
          const state = stateOf(a);
          return (
            <li key={a.assignment_id} className={`w1-money-strip__item w1-money-strip__item--${state}`} data-price-strip-entry={state}>
              <span className="w1-money-strip__when">{applies(a.valid)}</span>
              <span>{priceText(a.price)}</span>
              <span className="w1-money-strip__state">{STRIP_WORDS[state]}</span>
            </li>
          );
        })}
      </ol>
    </figure>
  );
}

/** The human edit is not built: visibly disabled, its reason a catalogued gap (G-assumptions-human-edit). */
function DisabledEdit() {
  return (
    <div className="financials-edit" data-price-edit="disabled">
      <button type="button" className="action" disabled aria-describedby="price-edit-reason">
        Edit price
      </button>
      <p id="price-edit-reason">
        <MissingClaim gapId="G-assumptions-human-edit" placement="assumptions.price.human-edit">
          Editing the price here is not available yet: a price change must be made by a signed-in operator, and
          operator sign-in is not built yet. Prices are published by the system.
        </MissingClaim>
      </p>
    </div>
  );
}

/** W1-F3: the mock's read-only `.field` inputs for one price version (exact values, as recorded). */
function PriceFields({ price, valid }: { price: PriceRevision; valid: { from: string; to: string | null } }) {
  return (
    <div data-price-fields={price.revision_id}>
      <div className="input-row">
        <label className="field">
          Diesel price · {price.currency} per litre
          <input value={price.value} readOnly />
          <small>Version {price.revision_no} · {CHANGE_WORDS[price.change_kind] ?? "Change"}</small>
        </label>
        <label className="field">
          Currency and unit
          <input value={`${price.currency} · per litre`} readOnly />
          <small>{BASIS_WORDS[price.basis] ?? "Another basis"}</small>
        </label>
      </div>
      <div className="input-row">
        <label className="field">
          Effective period
          <input value={applies(valid)} readOnly />
        </label>
        <label className="field">
          Recorded
          <input value={`${day(price.recorded_at)}, by ${setBy(price)}`} readOnly />
          <small>Source: {price.source_reference}</small>
        </label>
      </div>
      {price.correction_reason ? <p className="v69-gap-line">Why it changed: {price.correction_reason}</p> : null}
    </div>
  );
}

const ASSUMPTIONS_NOTICE =
  "Prices are versioned business context for this site. A change adds a version and keeps the earlier one; technical findings do not change when a price changes.";

/** W1-F3: a page-level refusal (never a panel): its title, the shared state line and the reason given. */
function PageRefusal({
  code,
  title,
  text,
  words,
  scope,
  message,
}: {
  code: string;
  title: string;
  text: string;
  words: ProductWords;
  scope: string;
  message?: string | null;
}) {
  return (
    <div className="page-refusal" role="status" data-page-refusal={code}>
      <p className="page-refusal__title">
        <strong>{title}</strong>
      </p>
      <div data-financials-state={code}>
        <ProductStatus words={words} scope={scope} asOf={null}>
          <p data-financials-read={code}>{text}</p>
        </ProductStatus>
      </div>
      {message ? <p className="muted">Reason given: {message}</p> : null}
    </div>
  );
}

function refusedRead(read: Exclude<FinancialReadResult<unknown>, { status: "loaded" }>, what: string) {
  const w = refusalWords(read.status, what);
  return (
    <PageRefusal
      code={read.status}
      title={w.heading}
      text={w.text}
      words={readResultWords(READ_KIND[read.status])}
      scope={`This site's ${what}`}
      message={read.message}
    />
  );
}

/** W1-F3: "Impact preview" (`assumptions:2`). No authorized preview read exists, so no example result is drawn. */
function ImpactPreview() {
  return (
    <Panel heading="Impact preview" headingId="site-price-preview-heading">
      <div data-price-preview="unavailable">
        <p className="v69-eyebrow">Fuel cost exposure after a price change</p>
        <p className="v69-panel-value">Preview not available</p>
        <p className="v69-gap-line">
          <MissingClaim gapId="G-assumptions-impact-preview" placement="assumptions.preview.unavailable">
            A preview of how a price change would alter a fuel cost is not available yet: no authorized preview read
            exists, so no example result is shown.
          </MissingClaim>
        </p>
        <p className="v69-gap-line">Technical findings and their classification do not change when a price changes.</p>
      </div>
    </Panel>
  );
}

function AssumptionsNotice({ recordedAt, links }: { recordedAt: string | null; links: FinancialsLinks }) {
  return (
    <Notice tone="blue" data={{ "data-assumptions-notice": "" }}>
      {recordedAt !== null ? (
        <p data-price-recorded-at={recordedAt}>
          Showing the prices as they were recorded on {formatInstant(recordedAt)}. Later changes are not shown.{" "}
          <Link to={links.assumptions()}>Show the current prices</Link>
        </p>
      ) : null}
      <p>{ASSUMPTIONS_NOTICE}</p>
    </Notice>
  );
}

/** W1-F3: the Assumptions skeleton for a page-level refusal: the refusal, then the three panels with in-panel gaps. */
function AssumptionsRefused({
  refusal,
  gap,
  history,
  cutoff,
}: {
  refusal: ReactNode;
  gap: string;
  history: ReactNode | null;
  cutoff: string;
}) {
  return (
    <div className="site-financials" data-price-cutoff={cutoff}>
      {refusal}
      <div className="panel-pair">
        <Panel heading="Financial assumptions" headingId="site-price-heading">
          <p className="v69-gap-line" data-price-panel-gap="assumptions">
            {gap}
          </p>
        </Panel>
        <ImpactPreview />
      </div>
      {history ?? (
        <Panel heading="Interpretation history" headingId="site-consequence-history-heading">
          <p className="v69-gap-line" data-price-panel-gap="history">
            {gap}
          </p>
        </Panel>
      )}
    </div>
  );
}

export function SiteAssumptions({
  siteId,
  client,
  links,
  now = () => new Date().toISOString(),
}: {
  siteId: string;
  client: FinancialsClient;
  links: FinancialsLinks;
  now?: () => string;
}) {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const revisionId = params.get("revision_id");
  const recordedAtRaw = params.get("recorded_at");
  const recordedAt = recordedAtRaw !== null && !Number.isNaN(new Date(recordedAtRaw).getTime()) ? recordedAtRaw : null;
  const historyAfter = recordedAt !== null ? params.get("history_after") : null;
  // A page size the address names (1-100) is kept through paging: each cursor is issued for one page size.
  const limitRaw = Number(params.get("history_limit"));
  const historyLimit = Number.isInteger(limitRaw) && limitRaw >= 1 && limitRaw <= 100 ? limitRaw : null;
  const [after, setAfter] = useState(0);
  // Review L5 (S4-02a): "Show later versions" appends to the versions already shown rather than replacing them.
  const [earlier, setEarlier] = useState<PriceRevision[]>([]);
  const [validAt] = useState(now);
  // S4-08: the fuel cost history is read first. On the default address its server-fixed cutoff string, passed on
  // unchanged (review L-R1), is the moment the price list is read at, so both lists describe one instant; the
  // address itself is not rewritten. An explicit `recorded_at` address reads both at that moment.
  const historyRead = useRead<ConsequenceHistoryBody, ConsequenceHistoryResult>(
    () => client.getConsequenceHistory(siteId, { recordedAt, after: historyAfter, limit: historyLimit ?? undefined }),
    [client, siteId, recordedAt, historyAfter, historyLimit],
  );
  const cutoff = recordedAt ?? (historyRead?.status === "loaded" ? historyRead.value.cutoff.recorded_at : null);
  const series = useRead<AssumptionSeriesBody | null>(
    () =>
      cutoff === null
        ? Promise.resolve({ status: "loaded", value: null } as const)
        : client.getAssumptions(siteId, { validAt, recordedAt: cutoff, afterRevisionNo: after }),
    [client, siteId, validAt, cutoff, after],
  );
  const exact = useRead<AssumptionRevisionBody | null>(
    () =>
      revisionId === null
        ? Promise.resolve({ status: "loaded", value: null } as const)
        : client.getAssumptionRevision(siteId, revisionId),
    [client, siteId, revisionId],
  );
  useEffect(() => {
    setAfter(0);
    setEarlier([]);
  }, [cutoff]);
  // S4-08: a changed basis (typed 409) reloads the history from its first page at the same moment.
  const basisChanged = historyRead?.status === "basis_changed";
  useEffect(() => {
    if (basisChanged) navigate(links.assumptions({ revisionId, recordedAt, historyLimit }), { replace: true });
  }, [basisChanged, navigate, links, revisionId, recordedAt, historyLimit]);

  if (recordedAtRaw !== null && recordedAt === null) {
    return (
      <AssumptionsRefused
        cutoff="NONE"
        refusal={refusedRead({ status: "not_found", message: null }, "recorded date")}
        gap="No such recorded date: no price is shown here, and this is not a missing price."
        history={null}
      />
    );
  }
  if (historyRead === null || exact === null) {
    return <p>Loading the site's prices.</p>;
  }
  const historyPanel = (prices: ReactNode) =>
    historyRead.status === "loaded" ? (
      <ConsequenceHistoryPanel body={historyRead.value} siteName={`Site ${siteId}`} links={links} historyLimit={historyLimit}>
        {prices}
      </ConsequenceHistoryPanel>
    ) : (
      <ConsequenceHistoryRefused read={historyRead}>{prices}</ConsequenceHistoryRefused>
    );
  if (cutoff === null) {
    // Review L-R2: without the history's moment there is no shared moment for the prices either. A plain
    // refusal, never a silent fall back to the current price list.
    const gap = "Prices unavailable: no price is shown here, and nothing is assumed about them.";
    return (
      <AssumptionsRefused
        cutoff="NONE"
        refusal={
          <PageRefusal
            code="no-cutoff"
            title="Prices unavailable"
            text="The moment to show this site's prices at could not be fixed, so no prices are shown right now. Nothing is assumed about them."
            words={readResultWords("unavailable")}
            scope={`Diesel price for site ${siteId}`}
          />
        }
        gap={gap}
        history={historyPanel(
          <p className="v69-gap-line" data-price-panel-gap="price-history">
            {gap}
          </p>,
        )}
      />
    );
  }
  if (series === null || (series.status === "loaded" && series.value === null)) {
    return <p>Loading the site's prices.</p>;
  }
  if (series.status !== "loaded") {
    const w = refusalWords(series.status, "price list");
    const gap = `${w.heading}: no price is shown here, and this is not a missing price.`;
    return (
      <AssumptionsRefused
        cutoff={cutoff}
        refusal={refusedRead(series, "price list")}
        gap={gap}
        history={historyPanel(
          <p className="v69-gap-line" data-price-panel-gap="price-history">
            {gap}
          </p>,
        )}
      />
    );
  }
  const body = series.value as AssumptionSeriesBody;
  return (
    <div
      className="site-financials"
      data-price-cutoff={body.cutoff.selected_by}
      data-price-recorded-cutoff={body.cutoff.recorded_at ?? undefined}
    >
      <div className="panel-pair">
        <FinancialAssumptions
          body={body}
          siteId={siteId}
          historical={recordedAt !== null}
          exact={exact}
          links={links}
          selectedRevision={revisionId}
        />
        <ImpactPreview />
      </div>
      {/* W1-F3: the mock's notice follows the Financial assumptions panel (siteAssumptionsScreen). */}
      <AssumptionsNotice recordedAt={recordedAt} links={links} />
      {historyPanel(
        <PriceHistory
          body={body}
          shown={[...earlier, ...body.revisions]}
          links={links}
          onMore={(next) => {
            setEarlier((prior) => [...prior, ...body.revisions]);
            setAfter(next);
          }}
        />,
      )}
    </div>
  );
}

const PRICED_WORDS: ProductWords = {
  label: "Price recorded for this site",
  sentence: "This recorded price turns litres of diesel into money for this site. It is an assumption, not a measured cost.",
  tone: "positive",
  code: "PRICED",
  unrecognised: false,
};

const EARLIER_WORDS: ProductWords = {
  label: "Prices as recorded at an earlier moment",
  sentence: "This is the price list as it was recorded then. Later changes are not shown, so it may not be the price in use now.",
  tone: "neutral",
  code: "RECORDED_CUTOFF",
  unrecognised: false,
};

const CONFLICT_WORDS: ProductWords = {
  label: "Two prices cover this time",
  sentence: "Two stored prices both cover today, so neither is shown and no amount uses either. This is not zero.",
  next: "The price list needs to be checked before any price is used.",
  tone: "problem",
  code: "CONFLICT",
  unrecognised: false,
};

/**
 * W1-F3: "Financial assumptions" (`assumptions:1`), in the mock's form. The state line, the price in use (or
 * "No price published."), the exact version's read-only fields (the selected version when the address names one),
 * the disabled edit with its reason, the effective-time strip and the schedule. The state line's "as of" is the
 * moment the price list was read at, exactly as the read returned it.
 */
function FinancialAssumptions({
  body,
  siteId,
  historical,
  exact,
  links,
  selectedRevision,
}: {
  body: AssumptionSeriesBody;
  siteId: string;
  historical: boolean;
  exact: FinancialReadResult<AssumptionRevisionBody | null>;
  links: FinancialsLinks;
  selectedRevision: string | null;
}) {
  const selection = body.selection;
  const priced = selection?.state === "PRICED" ? selection : null;
  const state = priced !== null ? "PRICED" : selection?.state === "CONFLICT" ? "CONFLICT" : "NO_PRICE";
  const words = historical
    ? EARLIER_WORDS
    : state === "PRICED"
      ? PRICED_WORDS
      : state === "CONFLICT"
        ? CONFLICT_WORDS
        : moneyWords("NO_PRICE");
  const pinned = exact.status === "loaded" ? exact.value : null;
  return (
    <Panel
      heading="Financial assumptions"
      headingId="site-price-heading"
      description="Site-scoped business context · a change keeps the earlier version"
    >
      <div data-price-state={historical ? "RECORDED_CUTOFF" : state}>
        <ProductStatus words={words} scope={`Diesel price for site ${siteId}`} asOf={body.cutoff.recorded_at} />
      </div>
      {priced !== null ? (
        <div data-price-selection="PRICED" data-price-selected-revision={priced.revision_id}>
          <p className="financials-lead">
            {historical ? "Covering today, as recorded then. " : "In use today. "}Diesel price, set by {setBy(priced.price)} on{" "}
            {day(priced.price.recorded_at)}: <strong>{priceText(priced.price)}</strong>, {applies(priced.valid)}.
          </p>
          {pinned === null ? <PriceFields price={priced.price} valid={priced.valid} /> : null}
        </div>
      ) : state === "CONFLICT" ? (
        <p data-price-selection="CONFLICT">
          <strong>No price published for today.</strong> Two stored prices both cover today, so neither is used. This needs
          to be checked before any price is used.
        </p>
      ) : (
        <p data-price-selection="NO_PRICE">
          <strong>No price published.</strong> No diesel price is recorded for today at this site. No default or
          company-wide price is used in its place.
        </p>
      )}
      {exact.status !== "loaded" ? (
        <p className="v69-gap-line" role="status" data-price-exact-refused={exact.status}>
          <strong>{refusalWords(exact.status, "price version").heading}.</strong> {refusalWords(exact.status, "price version").text}
        </p>
      ) : pinned !== null ? (
        <ExactVersion body={pinned} links={links} />
      ) : null}
      <div className="form-footer">
        <DisabledEdit />
      </div>
      {body.timeline.length > 0 ? <PriceTimeStrip body={body} historical={historical} /> : null}
      <Schedule body={body} links={links} selectedRevision={selectedRevision} historical={historical} />
      <ExactReferences
        name="assumptions-price"
        references={[
          ...(priced !== null ? priceReferences(priced.price, priced) : [{ label: "Price state", value: state }]),
          { label: "Prices read at", value: body.cutoff.recorded_at },
        ]}
      />
    </Panel>
  );
}

function Schedule({
  body,
  links,
  selectedRevision,
  historical,
}: {
  body: AssumptionSeriesBody;
  links: FinancialsLinks;
  selectedRevision: string | null;
  historical: boolean;
}) {
  if (body.timeline.length === 0) return null;
  const today = body.selection?.state === "PRICED" ? body.selection.assignment_id : null;
  return (
    <div data-price-schedule="">
      <p className="v69-eyebrow" id="site-price-schedule-heading">
        Price schedule
      </p>
      <DataTable labelledBy="site-price-schedule-heading">
        <thead>
          <tr>
            <th scope="col">Applies</th>
            <th scope="col">Price</th>
            <th scope="col">Version</th>
            <th scope="col">What it was</th>
          </tr>
        </thead>
        <tbody>
          {body.timeline.map((a) => (
            <tr
              key={a.assignment_id}
              data-price-assignment={a.assignment_id}
              data-price-revision={a.revision_id}
              aria-current={a.assignment_id === today ? "true" : undefined}
              className={a.revision_id === selectedRevision ? "is-selected" : undefined}
            >
              <td>
                {applies(a.valid)}
                {a.assignment_id === today ? (historical ? " (covered today, as recorded then)" : " (applies today)") : ""}
              </td>
              <td>{priceText(a.price)}</td>
              <td>
                <Link to={links.assumptions({ revisionId: a.revision_id })}>Version {a.price.revision_no}</Link>
              </td>
              <td>{CHANGE_WORDS[a.price.change_kind] ?? "Change"}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

/** W1-F3: the price versions part of "Interpretation history", labelled as recorded by the history's moment. */
function PriceHistory({
  body,
  shown,
  links,
  onMore,
}: {
  body: AssumptionSeriesBody;
  shown: PriceRevision[];
  links: FinancialsLinks;
  onMore: (after: number) => void;
}) {
  const page = body.revision_page;
  return (
    <div role="region" aria-label="Price history" data-price-history-part="">
      <p className="v69-eyebrow">
        Price versions recorded by {body.cutoff.recorded_at ? formatInstant(body.cutoff.recorded_at) : "this moment"}, oldest
        first
      </p>
      {shown.length === 0 ? (
        <p data-price-history="empty">No price version had been recorded at this moment.</p>
      ) : (
        <ol className="price-history" data-price-history="loaded">
          {shown.map((r) => (
            <li key={r.revision_id} data-price-history-revision={r.revision_id}>
              <p>
                <strong>Version {r.revision_no}</strong> · {CHANGE_WORDS[r.change_kind] ?? "Change"} ·{" "}
                {priceText(r)}, {applies(r.authored_valid)}. Set by {setBy(r)} on {day(r.recorded_at)}.
              </p>
              {r.correction_reason ? <p className="muted">Why: {r.correction_reason}</p> : null}
              <p>
                <Link to={links.assumptions({ revisionId: r.revision_id })}>Open version {r.revision_no}</Link>
                {" · "}
                <Link to={links.assumptions({ recordedAt: r.recorded_at })}>Prices as recorded then</Link>
              </p>
            </li>
          ))}
        </ol>
      )}
      <p className="muted">
        Showing {shown.length} of {page.total} version{page.total === 1 ? "" : "s"}.{" "}
        {page.next_after_revision_no !== null ? (
          <button type="button" className="link-button" onClick={() => onMore(page.next_after_revision_no ?? 0)}>
            Show later versions
          </button>
        ) : null}
      </p>
      <Disclosure summary="How these times are read" name="price-cutoff-basis">
        <p>
          Prices as recorded on a date show what this site's price list said at that moment. Nothing else from that
          moment is reconstructed.
        </p>
        <p>
          Each date range starts on its first day and ends just before its end date, so a price ending on 1 June and
          the next starting on 1 June never overlap.
        </p>
      </Disclosure>
    </div>
  );
}

/** The exact version the address names, inside "Financial assumptions": its fields, where it applied, references. */
function ExactVersion({ body, links }: { body: AssumptionRevisionBody; links: FinancialsLinks }) {
  const price = body.revision;
  return (
    <div role="region" aria-label={`Price version ${price.revision_no}`} data-price-exact-revision={price.revision_id}>
      <p className="v69-eyebrow">
        Selected: price version {price.revision_no}, exactly as recorded: {priceText(price)}
      </p>
      <PriceFields price={price} valid={price.authored_valid} />
      <p className="v69-gap-line">Where this version applied:</p>
      <ul data-price-exact-assignments={body.assignments.length}>
        {body.assignments.map((a) => (
          <li key={a.assignment_id}>
            {applies(a.valid)}; known from {formatInstant(a.recorded.from)}
            {a.recorded.to === null ? ", still current" : `, replaced on ${formatInstant(a.recorded.to)}`}.
          </li>
        ))}
      </ul>
      <p>
        <Link to={links.assumptions()}>Back to the current prices</Link>
      </p>
      <ExactReferences name={`price-record-${price.revision_no}`} references={priceReferences(price)} />
    </div>
  );
}

/** W1-F3: the v69 `financials` Overview: the Finding bridge in the mock's form, or the skeleton with its gaps. */
export function SiteFinancialsOverview({
  siteId,
  client,
  links,
}: {
  siteId: string;
  client: FinancialsClient;
  links: FinancialsLinks;
}) {
  const [params, setParams] = useSearchParams();
  const findingId = params.get("finding_id");
  const revisionId = params.get("revision_id");
  const consequenceRevisionId = params.get("consequence_revision_id");
  const bridge = useRead<FindingFinancialsBody | null>(
    () =>
      findingId === null
        ? Promise.resolve({ status: "loaded", value: null } as const)
        : client.getFindingFinancials(siteId, findingId, revisionId),
    [client, siteId, findingId, revisionId],
  );
  // The exact consequence read waits for the bridge's exact Finding version, so both name the same version.
  const pinnedRevision = bridge?.status === "loaded" && bridge.value !== null ? bridge.value.selection.revision_id : null;
  const consequences = useRead<FindingConsequencesBody | null>(
    () =>
      findingId === null || pinnedRevision === null
        ? Promise.resolve({ status: "loaded", value: null } as const)
        : client.getFindingConsequences(siteId, findingId, { revisionId: pinnedRevision, consequenceRevisionId }),
    [client, siteId, findingId, pinnedRevision, consequenceRevisionId],
  );
  // Hold the exact version in the address once it is known, so reload and back keep the same version.
  useEffect(() => {
    if (bridge?.status === "loaded" && bridge.value !== null && revisionId === null && findingId !== null) {
      setParams({ finding_id: findingId, revision_id: bridge.value.selection.revision_id }, { replace: true });
    }
  }, [bridge, revisionId, findingId, setParams]);
  const consequenceRead =
    consequences === null || (consequences.status === "loaded" && consequences.value === null)
      ? null
      : (consequences as FinancialReadResult<FindingConsequencesBody>);
  const assumptions = <AssumptionsInUse siteId={siteId} client={client} links={links} />;

  return (
    <div className="site-financials">
      {bridge === null ? (
        <p>Loading the finding's money view.</p>
      ) : bridge.status !== "loaded" ? (
        <>
          {refusedRead(bridge, "finding version")}
          <Panel heading="What happened → what it means in money" headingId="site-financials-bridge-heading">
            <p className="v69-gap-line" data-financials-panel-gap="bridge">
              {refusalWords(bridge.status, "finding version").heading}: no money consequence is shown here, and this is not
              a zero amount.
            </p>
          </Panel>
          <div className="panel-pair">
            {assumptions}
            <TradeoffsPanel
              rev={null}
              body={null}
              gap={`${refusalWords(bridge.status, "finding version").heading}: no method or limit of a figure is shown, because no finding version was read.`}
            />
          </div>
          <FinancialsNotice />
        </>
      ) : bridge.value !== null ? (
        <FindingBridge
          bridge={bridge.value}
          consequences={consequenceRead}
          links={links}
          pinnedConsequence={consequenceRevisionId}
          consequencesLoading={consequences === null}
          assumptions={assumptions}
        />
      ) : (
        <>
          <FinancialsStatusBar lines="No finding selected" currency={null} />
          <MetricCards columns={4} label="Money consequence measures">
            <MetricCard
              label="Operating-cost exposure"
              value="No finding selected"
              word
              tone="muted"
              note="Open a finding to see its bounded fuel cost. This is not zero."
              data={{ "data-financials-metric": "operating-cost" }}
            />
            <NotEstablishedCards />
          </MetricCards>
          <Panel heading="What happened → what it means in money" headingId="site-financials-bridge-heading">
            <p data-financials-bridge="none">
              Open a finding and choose “What this finding means in money” to see its money view here.{" "}
              <Link to={links.findings}>Go to this site's findings</Link>
            </p>
          </Panel>
          <div className="panel-pair">
            {assumptions}
            <TradeoffsPanel rev={null} body={null} />
          </div>
          <FinancialsNotice />
        </>
      )}
    </div>
  );
}

/**
 * W1-F3: "Assumptions in use" (`financials:2`): the site diesel price in use today, its version and basis, as the
 * mock's key values. A missing price stays unpriced; no default is used.
 */
function AssumptionsInUse({ siteId, client, links }: { siteId: string; client: FinancialsClient; links: FinancialsLinks }) {
  const [validAt] = useState(() => new Date().toISOString());
  const read = useRead(() => client.getAssumptions(siteId, { validAt, limit: 1 }), [client, siteId, validAt]);
  const selection = read !== null && read.status === "loaded" ? read.value.selection : null;
  return (
    <Panel heading="Assumptions in use" headingId="site-financials-price-heading">
      {read === null ? (
        <p>Loading the site's prices.</p>
      ) : read.status !== "loaded" ? (
        <p className="v69-gap-line" data-financials-read={read.status}>
          The site's prices could not be read, so no price is shown and none is assumed.
        </p>
      ) : selection?.state === "PRICED" ? (
        <div data-price-selection="PRICED" data-price-selected-revision={selection.revision_id}>
          <KeyValues
            label="Diesel price in use"
            rows={[
              ["Diesel price", <strong key="p">{priceText(selection.price)}</strong>, "price"],
              [
                "Price version",
                <Link key="v" to={links.assumptions({ revisionId: selection.revision_id })}>
                  Version {selection.price.revision_no}
                </Link>,
                "version",
              ],
              ["Currency", selection.price.currency, "currency"],
              ["Effective period", applies(selection.valid), "effective"],
              ["Basis", BASIS_WORDS[selection.price.basis] ?? "Another basis", "basis"],
              ["Set by", `${setBy(selection.price) === "the system" ? "The system" : "An operator"}, recorded on ${day(selection.price.recorded_at)}`, "set-by"],
            ]}
          />
        </div>
      ) : (
        <div data-price-selection={selection?.state ?? "NO_PRICE"}>
          <KeyValues
            label="Diesel price in use"
            rows={[
              [
                "Diesel price",
                selection?.state === "CONFLICT" ? "Unpriced: two stored prices cover today" : "Unpriced: no price is recorded for today",
                "price",
              ],
              ["Default price", "None is used in its place", "default"],
            ]}
          />
          <p className="v69-gap-line">No diesel price is recorded for today at this site.</p>
        </div>
      )}
      <p className="form-footer">
        <Link className="button" to={links.assumptions()}>
          Review assumptions
        </Link>
      </p>
    </Panel>
  );
}
