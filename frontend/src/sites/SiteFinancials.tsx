import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { DataTable, Disclosure, Fact, FactList, MissingClaim, Panel } from "../ui";
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
import { FindingBridge } from "./FindingConsequence";
import { formatInstant } from "./FoundationRevisionPanel";

/**
 * S4-02a/S4-02b: Site > Financials. The Overview holds the Finding bridge (an exact Finding version, its typed
 * `fuel-cost-1` money state, and an amount only for a current priced fuel cost; `FindingConsequence.tsx`), the
 * fuel cost versions of that Finding version, and the Site diesel price in use; Assumptions holds the current
 * price, its schedule, its recorded versions and the disabled human edit. Plain words by default; identifiers,
 * digests and enum names sit in the record-details and "How this is worked out" disclosures.
 *
 * Omitted for G-05 by manifest element (not rendered, not an empty tab; `.agent/S4-02b-review-packet.md`):
 * `financials:3#a`/`financials:3#b` (the Trade-offs panel), `assumptions:2#a` (the Impact preview), the
 * `financials` metric cards other than the one exposure range, the second (maintenance accrual) consequence line,
 * the Scenarios subtab, cash flow, FX and monthly extrapolation.
 */

export interface FinancialsLinks {
  /** The exact Finding version. */
  finding: (findingId: string, revisionId: string) => string;
  /** The Finding version's accepted evidence (S4-03). */
  evidence: (findingId: string, revisionId: string) => string;
  /** Assumptions, optionally pinned to an exact version or a recorded cutoff. */
  assumptions: (pin?: { revisionId?: string | null; recordedAt?: string | null; historyAfter?: string | null }) => string;
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

function ReadRefused({ read, what }: { read: Exclude<FinancialReadResult<unknown>, { status: "loaded" }>; what: string }) {
  const words: Record<typeof read.status, { heading: string; text: string }> = {
    not_found: { heading: `No such ${what}`, text: `This site has no ${what} with that reference. Nothing else is shown in its place.` },
    unauthenticated: { heading: "Sign in required", text: "Sign in to read this site's prices." },
    forbidden: { heading: "No access", text: "Your account has no access to this site." },
    closed: { heading: "Not released", text: "This finding's source is not released, so only an exact finding version can be opened." },
    unavailable: { heading: "Prices unavailable", text: "The price store could not be read, so nothing is known about this site's prices right now." },
  };
  return (
    <Panel heading={words[read.status].heading} headingId="site-financials-state-heading">
      <p data-financials-read={read.status}>{words[read.status].text}</p>
      {read.message ? <p className="muted">Reason given: {read.message}</p> : null}
    </Panel>
  );
}

function useRead<T, R = FinancialReadResult<T>>(load: () => Promise<R>, deps: unknown[]): R | null {
  const [read, setRead] = useState<R | null>(null);
  useEffect(() => {
    let active = true;
    setRead(null);
    void load().then((next) => {
      if (active) setRead(next);
    });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return read;
}

function RecordDetails({ price, assignment }: { price: PriceRevision; assignment?: PriceAssignment }) {
  return (
    <Disclosure summary="Record details" name={`price-record-${price.revision_no}`}>
      <FactList>
        <Fact term="Price version ID">
          <code data-vocabulary-exempt="source-reference" data-price-revision-id={price.revision_id}>{price.revision_id}</code>
        </Fact>
        <Fact term="Previous version ID">
          <code data-vocabulary-exempt="source-reference">{price.prior_revision_id ?? "none (first version)"}</code>
        </Fact>
        {assignment ? (
          <Fact term="Schedule entry ID">
            <code data-vocabulary-exempt="source-reference">{assignment.assignment_id}</code>
          </Fact>
        ) : null}
        <Fact term="Key and unit">
          <code data-vocabulary-exempt="source-reference">
            {price.assumption_key} · {price.unit}
          </code>
        </Fact>
        <Fact term="Basis and change">
          <code data-vocabulary-exempt="source-reference">
            {price.basis} · {price.change_kind}
          </code>
        </Fact>
        <Fact term="Published by">
          <code data-vocabulary-exempt="source-reference">
            {price.actor.kind} · {price.actor.id} · {price.channel}
          </code>
        </Fact>
        <Fact term="Authority">
          <code data-vocabulary-exempt="source-reference">{price.authorization_basis}</code>
        </Fact>
        <Fact term="Recorded at">
          <code data-vocabulary-exempt="source-reference">{price.recorded_at}</code>
        </Fact>
        <Fact term="Publication key">
          <code data-vocabulary-exempt="source-reference">{price.idempotency_key}</code>
        </Fact>
        <Fact term="Request digest">
          <code data-vocabulary-exempt="source-reference">{price.request_sha256}</code>
        </Fact>
      </FactList>
    </Disclosure>
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

function PriceFacts({ price, valid }: { price: PriceRevision; valid: { from: string; to: string | null } }) {
  return (
    <FactList>
      <Fact term="Price">{priceText(price)}</Fact>
      <Fact term="Applies">{applies(valid)}</Fact>
      <Fact term="Basis">{BASIS_WORDS[price.basis] ?? "Another basis"}</Fact>
      <Fact term="Source">{price.source_reference}</Fact>
      <Fact term="Set by">
        {setBy(price) === "the system" ? "The system" : "An operator"}, recorded on {day(price.recorded_at)}
      </Fact>
      {price.correction_reason ? <Fact term="Why it changed">{price.correction_reason}</Fact> : null}
    </FactList>
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
  const [after, setAfter] = useState(0);
  // Review L5 (S4-02a): "Show later versions" appends to the versions already shown rather than replacing them.
  const [earlier, setEarlier] = useState<PriceRevision[]>([]);
  const [validAt] = useState(now);
  // S4-08: the fuel cost history is read first. On the default address its server-fixed cutoff string, passed on
  // unchanged (review L-R1), is the moment the price list is read at, so both lists describe one instant; the
  // address itself is not rewritten. An explicit `recorded_at` address reads both at that moment.
  const historyRead = useRead<ConsequenceHistoryBody, ConsequenceHistoryResult>(
    () => client.getConsequenceHistory(siteId, { recordedAt, after: historyAfter }),
    [client, siteId, recordedAt, historyAfter],
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
    if (basisChanged) navigate(links.assumptions({ revisionId, recordedAt }), { replace: true });
  }, [basisChanged, navigate, links, revisionId, recordedAt]);

  if (recordedAtRaw !== null && recordedAt === null) {
    return <ReadRefused read={{ status: "not_found", message: null }} what="recorded date" />;
  }
  if (historyRead === null || exact === null) {
    return <p>Loading the site's prices.</p>;
  }
  const historyPanel =
    historyRead.status === "loaded" ? (
      <ConsequenceHistoryPanel body={historyRead.value} siteName={`Site ${siteId}`} links={links} />
    ) : (
      <ConsequenceHistoryRefused read={historyRead} />
    );
  if (cutoff === null) {
    // Review L-R2: without the history's moment there is no shared moment for the prices either. A plain
    // refusal, never a silent fall back to the current price list.
    return (
      <section className="site-financials" aria-label="Site prices" data-price-cutoff="NONE">
        <Panel heading="Prices unavailable" headingId="site-financials-state-heading">
          <p data-financials-read="no-cutoff">
            The moment to show this site's prices at could not be fixed, so no prices are shown right now. Nothing is
            assumed about them.
          </p>
        </Panel>
        {historyPanel}
      </section>
    );
  }
  if (series === null || (series.status === "loaded" && series.value === null)) {
    return <p>Loading the site's prices.</p>;
  }
  if (series.status !== "loaded") return <ReadRefused read={series} what="price list" />;
  const body = series.value as AssumptionSeriesBody;
  return (
    <section
      className="site-financials"
      aria-label="Site prices"
      data-price-cutoff={body.cutoff.selected_by}
      data-price-recorded-cutoff={body.cutoff.recorded_at ?? undefined}
    >
      {recordedAt !== null ? (
        <p className="notice" data-price-recorded-at={recordedAt}>
          Showing the prices as they were recorded on {formatInstant(recordedAt)}. Later changes are not shown.{" "}
          <Link to={links.assumptions()}>Show the current prices</Link>
        </p>
      ) : null}
      {exact.status !== "loaded" ? (
        <ReadRefused read={exact} what="price version" />
      ) : exact.value !== null ? (
        <ExactVersion body={exact.value} links={links} />
      ) : null}
      <CurrentPrice body={body} />
      <Schedule body={body} links={links} selectedRevision={revisionId} />
      <History
        body={body}
        shown={[...earlier, ...body.revisions]}
        links={links}
        onMore={(next) => {
          setEarlier((prior) => [...prior, ...body.revisions]);
          setAfter(next);
        }}
      />
      {historyPanel}
    </section>
  );
}

function CurrentPrice({ body }: { body: AssumptionSeriesBody }) {
  const selection = body.selection;
  return (
    <Panel
      heading="Site diesel price"
      headingId="site-price-heading"
      description="The price this site uses to turn litres of diesel into money. Technical findings do not change when it changes."
    >
      {selection?.state === "PRICED" ? (
        <div data-price-selection="PRICED" data-price-selected-revision={selection.revision_id}>
          <p className="financials-lead">
            Diesel price, set by {setBy(selection.price)} on {day(selection.price.recorded_at)}:{" "}
            <strong>{priceText(selection.price)}</strong>, {applies(selection.valid)}.
          </p>
          <PriceFacts price={selection.price} valid={selection.valid} />
          <RecordDetails price={selection.price} assignment={selection} />
        </div>
      ) : selection?.state === "CONFLICT" ? (
        <p data-price-selection="CONFLICT">
          Two stored prices claim today, so neither is shown. This needs to be checked before any price is used.
        </p>
      ) : (
        <p data-price-selection="NO_PRICE">
          No diesel price is recorded for today at this site. No default or company-wide price is used in its place.
        </p>
      )}
      <DisabledEdit />
    </Panel>
  );
}

function Schedule({
  body,
  links,
  selectedRevision,
}: {
  body: AssumptionSeriesBody;
  links: FinancialsLinks;
  selectedRevision: string | null;
}) {
  if (body.timeline.length === 0) return null;
  const today = body.selection?.state === "PRICED" ? body.selection.assignment_id : null;
  return (
    <Panel
      heading="Price schedule"
      headingId="site-price-schedule-heading"
      description="Which price applies to which dates. A later change or correction never rewrites an earlier version."
      flush
    >
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
                {a.assignment_id === today ? " (applies today)" : ""}
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
    </Panel>
  );
}

function History({
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
    <Panel
      heading="Price history"
      headingId="site-price-history-heading"
      description="Every recorded version, oldest first. Open a version to see exactly where it applied, or view the prices as they were recorded at that moment."
    >
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
                <Link to={links.assumptions({ recordedAt: r.recorded_at })}>
                  Prices as recorded then
                </Link>
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
    </Panel>
  );
}

function ExactVersion({ body, links }: { body: AssumptionRevisionBody; links: FinancialsLinks }) {
  const price = body.revision;
  return (
    <Panel
      heading={`Price version ${price.revision_no}`}
      headingId="site-price-version-heading"
      description="This exact version, as recorded. It stays the same after later changes."
    >
      <div data-price-exact-revision={price.revision_id}>
        <PriceFacts price={price} valid={price.authored_valid} />
        <h3 className="panel__subheading">Where this version applied</h3>
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
        <RecordDetails price={price} />
      </div>
    </Panel>
  );
}

/** The Overview: the Finding bridge when a Finding is selected, and the Site price in use. */
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

  return (
    <section className="site-financials" aria-label="Site financials overview">
      {bridge === null ? (
        <p>Loading the finding's money view.</p>
      ) : bridge.status !== "loaded" ? (
        <ReadRefused read={bridge} what="finding version" />
      ) : bridge.value !== null ? (
        <FindingBridge
          bridge={bridge.value}
          consequences={consequenceRead}
          links={links}
          pinnedConsequence={consequenceRevisionId}
        />
      ) : (
        <Panel heading="What this finding means in money" headingId="site-financials-bridge-heading">
          <p data-financials-bridge="none">
            Open a finding and choose “What this finding means in money” to see its money view here.{" "}
            <Link to={links.findings}>Go to this site's findings</Link>
          </p>
        </Panel>
      )}
      <PriceInUse siteId={siteId} client={client} links={links} />
    </section>
  );
}

function PriceInUse({ siteId, client, links }: { siteId: string; client: FinancialsClient; links: FinancialsLinks }) {
  const [validAt] = useState(() => new Date().toISOString());
  const read = useRead(() => client.getAssumptions(siteId, { validAt, limit: 1 }), [client, siteId, validAt]);
  return (
    <Panel heading="Price in use" headingId="site-financials-price-heading">
      {read === null ? (
        <p>Loading the site's prices.</p>
      ) : read.status !== "loaded" ? (
        <p data-financials-read={read.status}>The site's prices could not be read.</p>
      ) : read.value.selection?.state === "PRICED" ? (
        <p data-price-selection="PRICED" data-price-selected-revision={read.value.selection.revision_id}>
          Diesel price, set by {setBy(read.value.selection.price)} on {day(read.value.selection.price.recorded_at)}:{" "}
          <strong>{priceText(read.value.selection.price)}</strong>, {applies(read.value.selection.valid)}.
        </p>
      ) : (
        <p data-price-selection={read.value.selection?.state ?? "NO_PRICE"}>
          No diesel price is recorded for today at this site.
        </p>
      )}
      <p>
        <Link to={links.assumptions()}>See the price schedule and history</Link>
      </p>
    </Panel>
  );
}
