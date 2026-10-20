/**
 * W3-01 commit 3: the four estate Finding lens roots (v6.9 `findings`, `findings-cost`, `findings-risks`,
 * `findings-opportunities`) read from `GET /api/estate/findings` (`estate-finding-index-2`). Copy and states follow
 * `.agent/W3-01-build-spec.md` "Per-screen panel/copy/layout dry-read", Review closure B3/B7/S19, Run 6 Blocker 2,
 * Run 8 rulings 3-5 and Run 12 ruling 3. Priority and confidence stay `Not assessed`; Risks and Opportunities stay
 * honestly empty until a stored eligible kind exists. No mock ID, count, price or savings is rendered.
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { DataTable, Disclosure, MetricCard, MetricCards, Notice, PageHeader, Panel } from "../ui";
import { SOURCE_WORDS, sourceState, type SourceProvenance } from "../sites/sourceProvenance";
import {
  createEstateClient,
  type EstateClient,
  type EstateConsequence,
  type EstateFindingRow,
  type EstateFindingsBody,
  type EstateLens,
  type EstateLifecycle,
  type EstateResult,
  type EstateStateFilter,
} from "./estateClient";
import {
  EstateDateBar,
  EstateRefusal,
  LimitationNotice,
  PARTIAL_COVERAGE,
  PARTIAL_TOTALS,
  Pager,
  SiteStateChip,
  estateHref,
  limitationSentences,
  queryFromParams,
  utcInstant,
} from "./estateShared";

/** The four estate Finding lens routes (Lane A mounts them; this page links between them). */
export const ESTATE_FINDING_LENS_PATHS: Readonly<Record<EstateLens, string>> = {
  all: "/findings",
  cost: "/findings/cost",
  risks: "/findings/risks",
  opportunities: "/findings/opportunities",
};

const LENS_TABS: readonly { lens: EstateLens; label: string }[] = [
  { lens: "all", label: "All findings" },
  { lens: "cost", label: "Cost" },
  { lens: "risks", label: "Risks" },
  { lens: "opportunities", label: "Opportunities" },
];

/** v6.9 panel title per lens (rendered-panels JSON). */
const PANEL_TITLE: Readonly<Record<EstateLens, string>> = {
  all: "Findings across the estate",
  cost: "Cost lens",
  risks: "Risks lens",
  opportunities: "Opportunities lens",
};

/** The lens-specific second empty line (dry-read table); All has none. */
const LENS_EMPTY: Readonly<Record<EstateLens, string | null>> = {
  all: null,
  cost: "No supported priced consequence in this selection.",
  risks: "No supported risk classification in this selection.",
  opportunities: "No supported opportunity Finding in this selection.",
};

const SUBTITLE: Readonly<Record<EstateLens, string>> = {
  all: "Evidence-backed operating conclusions · one global object model",
  cost: "Evidence-backed operating conclusions · one object model",
  risks: "Evidence-backed operating conclusions · one object model",
  opportunities: "Evidence-backed operating conclusions · one object model",
};

const LIFECYCLE_WORDS: Readonly<Record<EstateLifecycle, { text: string; tone: string; filter: EstateStateFilter }>> = {
  SUPPORTED: { text: "Supported", tone: "blue", filter: "supported" },
  UNCONFIRMED: { text: "Unconfirmed", tone: "amber", filter: "unconfirmed" },
  NO_LONGER_SUPPORTED: { text: "No longer supported", tone: "neutral", filter: "no_longer_supported" },
  MERGED: { text: "Merged", tone: "neutral", filter: "merged" },
};
const LIFECYCLE_ORDER: readonly EstateLifecycle[] = ["SUPPORTED", "UNCONFIRMED", "NO_LONGER_SUPPORTED", "MERGED"];
const FILTER_LIFECYCLE: Readonly<Record<EstateStateFilter, EstateLifecycle | null>> = {
  all: null,
  supported: "SUPPORTED",
  unconfirmed: "UNCONFIRMED",
  no_longer_supported: "NO_LONGER_SUPPORTED",
  merged: "MERGED",
};

const LENS_FLAG_WORDS: Readonly<Record<string, string>> = { COST: "Cost", RISK: "Risk", OPPORTUNITY: "Opportunity" };

export const AWAITING_ZERO = "No Actions from selected Finding revisions are awaiting verification in this window.";
export const AWAITING_RULE =
  "Counts Actions from the exact selected Finding revision with an open frozen verification window and no resolved outcome.";
export const FINDINGS_NOTICE =
  "Priority, confidence and workflow state stay separate. Opening a finding moves you to Findings with its site in the breadcrumb.";

/**
 * The Main consequence cell (Run 6 Blocker 2, Run 8 rulings 3-4): a PRICED row shows its stored interval, never a
 * sum or point estimate; a withheld amount on a historical basis says `Historical as of {known_at}`; another
 * withheld amount says `Source unverified`; a stored unpriced row says `Unpriced`; no row says `No consequence
 * recorded`.
 */
export function consequenceWords(consequence: EstateConsequence, rowStatus: string, knownAt: string): string {
  if (consequence.state === "PRICED" && consequence.amount_low !== null && consequence.amount_high !== null) {
    return `${consequence.amount_low}–${consequence.amount_high} ${consequence.currency ?? ""}`.trim();
  }
  if (consequence.source_revision_id === null) return "No consequence recorded";
  if (consequence.state === "UNPRICED") return "Unpriced";
  if (rowStatus === "HISTORICAL") return `Historical as of ${utcInstant(knownAt)}`;
  return "Source unverified";
}

function count(value: number | null): string {
  return value === null ? "Coverage incomplete" : String(value);
}

function Cards({ body }: { body: EstateFindingsBody }) {
  const s = body.summary;
  const awaitingNote =
    s.awaiting_verification === null ? undefined : s.awaiting_verification === 0 ? AWAITING_ZERO : "Action taken; outcome open";
  return (
    <MetricCards label="Findings summary" data={{ "data-estate-cards": "" }}>
      <MetricCard
        label="Supported findings"
        value={count(s.supported_findings)}
        word={s.supported_findings === null}
        tone={s.supported_findings === null ? "amber" : undefined}
        note={s.supported_findings === null ? undefined : `Across ${body.scope.authorized_site_count} sites`}
        data={{ "data-estate-card": "supported_findings" }}
      />
      <MetricCard label="High priority" value="Not assessed" word data={{ "data-estate-card": "high_priority" }} />
      <MetricCard label="Low confidence" value="Not assessed" word data={{ "data-estate-card": "low_confidence" }} />
      <MetricCard
        label="Awaiting verification"
        value={count(s.awaiting_verification)}
        word={s.awaiting_verification === null}
        tone={s.awaiting_verification === null ? "amber" : undefined}
        note={
          awaitingNote === undefined ? undefined : (
            <>
              {awaitingNote}{" "}
              <Disclosure summary="How this is counted" name="estate-awaiting-rule" variant="inline">
                {AWAITING_RULE}
              </Disclosure>
            </>
          )
        }
        data={{ "data-estate-card": "awaiting_verification" }}
      />
    </MetricCards>
  );
}

function LensTabs({ lens, href }: { lens: EstateLens; href: (lens: EstateLens) => string }) {
  return (
    <nav className="site-tabs site-subtabs estate-lens-tabs" aria-label="Finding lenses" data-estate-lenses>
      <ol className="site-tabs__list">
        {LENS_TABS.map((tab) => (
          <li className="site-tabs__item" key={tab.lens}>
            <Link
              className="site-tabs__link"
              to={href(tab.lens)}
              aria-current={tab.lens === lens ? "page" : undefined}
              data-estate-lens={tab.lens}
            >
              {tab.label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

/**
 * `All states` plus the stored lifecycle values present in the read rows (and the active filter); never a
 * mock-only value. Reading R1 in `.agent/W3-01-pending-rulings.md`: the API carries no full-basis lifecycle set.
 */
function StateChips({
  body,
  active,
  href,
}: {
  body: EstateFindingsBody | null;
  active: EstateStateFilter;
  href: (state: EstateStateFilter) => string;
}) {
  const present = new Set<EstateLifecycle>((body?.rows ?? []).map((row) => row.lifecycle));
  const activeLifecycle = FILTER_LIFECYCLE[active];
  if (activeLifecycle !== null) present.add(activeLifecycle);
  const chips: { filter: EstateStateFilter; text: string; tone: string }[] = [
    { filter: "all", text: "All states", tone: "neutral" },
    ...LIFECYCLE_ORDER.filter((value) => present.has(value)).map((value) => LIFECYCLE_WORDS[value]).map((w) => ({
      filter: w.filter,
      text: w.text,
      tone: w.tone,
    })),
  ];
  return (
    <ul className="v69-chips estate-state-chips" aria-label="Workflow state" data-estate-state-chips>
      {chips.map((chip) => (
        <li key={chip.filter}>
          <Link
            className={`v69-chip estate-state-chip estate-state-chip--${chip.tone}`}
            to={href(chip.filter)}
            aria-current={chip.filter === active ? "true" : undefined}
            data-estate-state={chip.filter}
          >
            {chip.text}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function Row({ row, knownAt }: { row: EstateFindingRow; knownAt: string }) {
  const lifecycle = LIFECYCLE_WORDS[row.lifecycle];
  const source = SOURCE_WORDS[sourceState(row.source_provenance as unknown as SourceProvenance)];
  return (
    <tr data-estate-finding={row.finding_id}>
      <td>
        <Link className="estate-cell__primary" to={row.links.finding} data-estate-finding-link>
          {row.title}
        </Link>
        <Disclosure summary={row.finding_label} name={`estate-finding-${row.finding_id}`} variant="inline">
          <span className="estate-cell__detail">
            Finding {row.finding_id} · revision {row.finding_revision_id} · {source.label}
          </span>
        </Disclosure>
      </td>
      <td>
        <Link to={row.links.site} data-estate-site-link>
          {row.site_code}
        </Link>
        <span className="estate-cell__secondary">{row.site_name}</span>
      </td>
      <td>{row.priority ?? "Not assessed"}</td>
      <td>{row.confidence ?? "Not assessed"}</td>
      <td>
        <span className={`estate-chip estate-chip--${lifecycle.tone}`} data-estate-lifecycle={row.lifecycle}>
          {lifecycle.text}
        </span>
        <SiteStateChip state={row.status} />
      </td>
      <td data-estate-consequence={row.consequence.state}>{consequenceWords(row.consequence, row.status, knownAt)}</td>
      <td>
        {row.lens_flags.length === 0 ? "No supported lens" : row.lens_flags.map((flag) => LENS_FLAG_WORDS[flag]).join(", ")}
      </td>
    </tr>
  );
}

function FindingRowsTable({ body }: { body: EstateFindingsBody }) {
  return (
    <DataTable labelledBy="estate-findings-heading">
      <colgroup>
        {[23, 13, 10, 11, 11, 22, 10].map((width, index) => (
          <col key={index} style={{ width: `${width}%` }} />
        ))}
      </colgroup>
      <thead>
        <tr>
          {["Finding", "Site", "Priority", "Confidence", "State", "Main consequence", "Lens"].map((h) => (
            <th key={h} scope="col">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {body.rows.map((row) => (
          <Row key={row.finding_id} row={row} knownAt={body.window.known_at} />
        ))}
      </tbody>
    </DataTable>
  );
}

export interface EstateFindingsPageProps {
  lens: EstateLens;
  client?: EstateClient;
}

/** One estate Finding lens root. Reads its window, cutoff, state filter and cursor from the URL. */
export function EstateFindingsPage({ lens, client }: EstateFindingsPageProps) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = queryFromParams(params);
  const key = params.toString();
  const [result, setResult] = useState<{ key: string; read: EstateResult<EstateFindingsBody> } | null>(null);

  useEffect(() => {
    let live = true;
    void reads.findings({ ...query, lens }).then((read) => {
      if (live) setResult({ key: `${lens}|${key}`, read });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, lens, key]);

  const path = ESTATE_FINDING_LENS_PATHS[lens];
  const lensHref = (next: EstateLens) => estateHref(ESTATE_FINDING_LENS_PATHS[next], query, { state: query.state });
  const stateHref = (state: EstateStateFilter) => estateHref(path, query, { state });
  const firstPage = estateHref(path, query, { state: query.state });
  const read = result?.key === `${lens}|${key}` ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;

  return (
    <div className="estate-page" data-estate-root={lens}>
      <PageHeader title="Findings" subtitle={SUBTITLE[lens]} />
      <LensTabs lens={lens} href={lensHref} />
      <EstateDateBar
        key={`${query.from}|${query.to}|${query.known_at ?? ""}`}
        query={query}
        body={body}
        onApply={(next) => navigate(estateHref(path, next, { state: query.state }))}
      />
      {read === null ? (
        <p className="estate-loading">Loading the findings across the estate.</p>
      ) : read.status === "refused" ? (
        <EstateRefusal code={read.code} copy={read.copy} firstPage={firstPage} />
      ) : (
        <Loaded body={read.value} lens={lens} active={query.state} stateHref={stateHref} path={path} query={query} />
      )}
    </div>
  );
}

function Loaded({
  body,
  lens,
  active,
  stateHref,
  path,
  query,
}: {
  body: EstateFindingsBody;
  lens: EstateLens;
  active: EstateStateFilter;
  stateHref: (state: EstateStateFilter) => string;
  path: string;
  query: ReturnType<typeof queryFromParams>;
}) {
  const complete = body.total_count !== null;
  const empty = complete && body.total_count === 0;
  const next = body.next_cursor === null ? null : estateHref(path, query, { state: active, cursor: body.next_cursor });
  return (
    <>
      <Cards body={body} />
      <StateChips body={body} active={active} href={stateHref} />
      <Panel
        heading={PANEL_TITLE[lens]}
        headingId="estate-findings-heading"
        description="Lens is how a finding is read, not a second object · state is a filter"
      >
        {body.rows.length > 0 ? <FindingRowsTable body={body} /> : null}
        {empty ? (
          <div className="estate-empty" data-estate-empty>
            <p>No findings match.</p>
            {LENS_EMPTY[lens] === null ? null : <p>{LENS_EMPTY[lens]}</p>}
          </div>
        ) : null}
        {complete ? null : (
          <p className="estate-partial" data-estate-partial>
            {PARTIAL_TOTALS}
          </p>
        )}
        <Pager next={next} first={stateHref(active)} paged={query.cursor !== null} />
      </Panel>
      <LimitationNotice sentences={limitationSentences(body, PARTIAL_COVERAGE)} />
      <Notice tone="blue" data={{ "data-estate-notice": "" }}>
        {FINDINGS_NOTICE}
      </Notice>
    </>
  );
}
