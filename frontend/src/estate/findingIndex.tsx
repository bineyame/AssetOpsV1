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
import { TechnicalDetails } from "../ui/TechnicalDetails";
import { SOURCE_WORDS, sourceState, type SourceProvenance } from "../sites/sourceProvenance";
import { CategoryTags } from "../sites/outcomeCategories";
import { EarlyWarningList } from "../sites/EarlyWarnings";
import type { OutcomeWarning } from "../sites/outcomeBoardClient";
import { useOutcomeSummary } from "./useOutcomeSummary";
import {
  createEstateClient,
  findingOpportunities,
  findingOpportunitiesUnread,
  type EstateClient,
  type EstateConsequence,
  type EstateFindingRow,
  type EstateFindingsBody,
  type EstateLens,
  type EstateLifecycle,
  type EstateOpportunity,
  type EstateResult,
  type EstateScopeBody,
  type EstateStateFilter,
} from "./estateClient";
import { linkFor } from "../shell/operatorSiteRoutes";
import {
  EARLIER_CUTOFF,
  EstateDateBar,
  EstateRefusal,
  LimitationNotice,
  PARTIAL_COVERAGE,
  PARTIAL_TOTALS,
  PENDING_EVIDENCE,
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

/** OUT-C U5: which summary warnings each lens lists (All lists every one; none is an Opportunity yet). */
const LENS_WARNING_FILTER: Readonly<Record<EstateLens, (w: OutcomeWarning) => boolean>> = {
  all: () => true,
  cost: (w) => w.lens === "COST",
  risks: (w) => w.lens === "RISK",
  opportunities: (w) => w.lens === "OPPORTUNITY",
};

/** The lens-specific second empty line (dry-read table); All has none. */
const LENS_EMPTY: Readonly<Record<EstateLens, string | null>> = {
  all: null,
  cost: "No supported priced consequence in this selection.",
  risks: "No supported risk classification in this selection.",
  opportunities: "No supported opportunity Finding in this selection.",
};

const SUBTITLE: Readonly<Record<EstateLens, string>> = {
  all: "Evidence-backed operating conclusions",
  cost: "Evidence-backed operating conclusions",
  risks: "Evidence-backed operating conclusions",
  opportunities: "Evidence-backed operating conclusions",
};

const LIFECYCLE_WORDS: Readonly<Record<EstateLifecycle, { text: string; tone: string; filter: EstateStateFilter }>> = {
  SUPPORTED: { text: "Confirmed", tone: "blue", filter: "supported" },
  UNCONFIRMED: { text: "Not yet confirmed", tone: "amber", filter: "unconfirmed" },
  NO_LONGER_SUPPORTED: { text: "No longer applies", tone: "neutral", filter: "no_longer_supported" },
  MERGED: { text: "Combined with another", tone: "neutral", filter: "merged" },
};

const LENS_FLAG_WORDS: Readonly<Record<string, string>> = { COST: "Cost", RISK: "Risk", OPPORTUNITY: "Opportunity" };

export const AWAITING_ZERO = "No Actions from selected Finding revisions are awaiting verification in this window.";
export const AWAITING_RULE =
  "Counts Actions from the exact selected Finding revision with an open frozen verification window and no resolved outcome.";
export const FINDINGS_NOTICE = "Priority, confidence and workflow state stay separate.";
export const FINDINGS_LINKED_NOTICE =
  "A finding title that is a link opens that finding with its site in the breadcrumb; other titles are shown without a link.";
export const FINDINGS_UNLINKED_NOTICE =
  "Finding titles on this page are shown without a link; the Site link opens the site.";

/**
 * The Main consequence cell (Run 6 Blocker 2, Run 8 rulings 3-4): a PRICED row shows its stored interval, never a
 * sum or point estimate; a withheld amount on a historical basis says `Historical as of {known_at}`; another
 * withheld amount says `Source not checked`; a stored unpriced row says `Unpriced`; no row says `No consequence
 * recorded`.
 */
export function consequenceWords(consequence: EstateConsequence, rowStatus: string, knownAt: string): string {
  if (consequence.state === "PRICED" && consequence.amount_low !== null && consequence.amount_high !== null) {
    return `${consequence.amount_low}–${consequence.amount_high} ${consequence.currency ?? ""}`.trim();
  }
  // COV-PARTIAL MOCK DEVIATION R622: a partly checked Site's row never shows an amount (the backend sends none).
  if (rowStatus === "PARTIAL") {
    return `Partly checked · ${consequence.source_revision_id === null ? "No consequence recorded" : consequence.state === "UNPRICED" ? "Unpriced" : "value shown once every day is checked"}`;
  }
  if (consequence.source_revision_id === null) return "No consequence recorded";
  if (consequence.state === "UNPRICED") return "Unpriced";
  if (rowStatus === "HISTORICAL") return `Historical as of ${utcInstant(knownAt)}`;
  return "Source not checked";
}

function count(value: number | null): string {
  return value === null ? "Some data missing" : String(value);
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

const STATE_CHIPS: readonly { filter: EstateStateFilter; text: string; tone: string }[] = [
  { filter: "all", text: "All states", tone: "neutral" },
  ...(["SUPPORTED", "UNCONFIRMED", "NO_LONGER_SUPPORTED", "MERGED"] as const).map((value) => ({
    filter: LIFECYCLE_WORDS[value].filter,
    text: LIFECYCLE_WORDS[value].text,
    tone: LIFECYCLE_WORDS[value].tone,
  })),
];

/**
 * The five stable state filter controls (Run 13 ruling 2): `All states` and the four supported filter values, in
 * that order on every lens and read. They carry no counts and never claim a lifecycle occurs in the basis or page.
 */
function StateChips({ active, href }: { active: EstateStateFilter; href: (state: EstateStateFilter) => string }) {
  return (
    <ul className="v69-chips estate-state-chips" aria-label="Workflow state" data-estate-state-chips>
      {STATE_CHIPS.map((chip) => (
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

/**
 * Post-W6 W3-estate Q7 (R294): the cause-aware limitation copy of the four Finding lenses. Site names come from a
 * second `scope()` read at the identical `from`/`to`/`known_at`, joined on `site_id`. A Site that is
 * PENDING_RECOMPUTE with a selection is being reassessed; a Site with no selection (or UNKNOWN) has no selected
 * result. A failed or unfinished scope read, or a Site the scope does not name, falls back to the generic copy.
 * The Actions root keeps `limitationSentences` unchanged.
 */
export interface FindingCauseCopy {
  panel: string[];
  notice: string[];
}

export function findingCauseCopy(body: EstateFindingsBody, scope: EstateScopeBody | null): FindingCauseCopy {
  const generic: FindingCauseCopy = {
    panel: body.total_count === null ? [PARTIAL_TOTALS] : [],
    notice: limitationSentences(body, PARTIAL_COVERAGE),
  };
  if (scope === null) return generic;
  const names = new Map(scope.sites.map((site) => [site.site_id, site.site_name]));
  const pending = body.coverage.sites.filter((site) => site.state === "PENDING_RECOMPUTE" && site.selection_id !== null);
  const missing = body.coverage.sites.filter(
    (site) => !(site.state === "PENDING_RECOMPUTE" && site.selection_id !== null) && (site.state === "UNKNOWN" || site.selection_id === null),
  );
  // COV-PARTIAL MOCK DEVIATION R622: partly checked Sites name their checked days from the backend's `days.text`.
  const partial = body.coverage.sites.filter((site) => site.state === "PARTIAL" && site.days?.text);
  if ([...pending, ...missing, ...partial].some((site) => !names.has(site.site_id))) return generic;
  const partialNames = partial.map((site) => names.get(site.site_id));
  const onlyPartial =
    partial.length > 0 && body.coverage.sites.every((site) => ["CURRENT", "HISTORICAL", "NOT_APPLICABLE", "PARTIAL"].includes(site.state));
  const pendingNames = pending.map((site) => names.get(site.site_id)).join(", ");
  const missingNames = missing.map((site) => names.get(site.site_id)).join(", ");
  const panel: string[] = [];
  if (body.total_count === null) {
    if (pending.length > 0) {
      panel.push(`Totals are unknown while new evidence for ${pendingNames} is assessed; ${pending.length === 1 ? "its" : "their"} rows are held until then.`);
    }
    if (missing.length > 0) panel.push(`${missingNames} has no selected result; totals are unknown.`);
    if (partial.length > 0) {
      panel.push(`${partialNames.join(", ")} ${partial.length === 1 ? "is" : "are"} partly checked; totals are unknown.`);
    }
    if (panel.length === 0) panel.push(PARTIAL_TOTALS);
  }
  const states = new Set(body.coverage.sites.map((site) => site.state));
  const notice: string[] = [];
  if (body.status === "HISTORICAL") notice.push(EARLIER_CUTOFF);
  if (pending.length > 0) notice.push(`New evidence for ${pendingNames} is being assessed.`);
  else if (states.has("PENDING_RECOMPUTE")) notice.push(PENDING_EVIDENCE);
  if (states.has("STALE_SOURCE")) notice.push("Some sites' results may miss newer readings.");
  partial.forEach((site, i) => notice.push(`${partialNames[i]}: ${site.days?.text}.`));
  if (body.coverage.state !== "COMPLETE") {
    if (missing.length > 0) notice.push(`${missingNames} is not yet assessed; estate totals are unknown.`);
    else if (pending.length === 0 && !onlyPartial) notice.push(PARTIAL_COVERAGE);
  }
  return { panel, notice };
}

/**
 * Sites whose rows link `links.finding` (Run 13 ruling 3): the mini-grid rows, whose exact `revision_id` the
 * reviewed W1 Finding detail consumes. The wire has no row domain; the existing coverage reports a mini-grid
 * Site with a matcher state, while cold and EV Sites report `match_state NOT_APPLICABLE`. A Site missing from
 * coverage is never linked.
 */
function miniGridSiteIds(body: EstateFindingsBody): ReadonlySet<string> {
  return new Set(body.coverage.sites.filter((site) => site.match_state !== "NOT_APPLICABLE").map((site) => site.site_id));
}

/**
 * Post-W6 W3-estate Q4 (R297): whether a row's Finding title is live. A mini-grid row links its exact revision
 * link. A cold or EV row is live only when the server sends a provable row-local windowed link (one carrying its
 * own `from`, `to` and `known_at`; the server otherwise sends `null`); a null, absent or unwindowed link leaves the title inert with a labelled unavailable detail.
 */
export function findingLinkLive(row: EstateFindingRow, miniGridIds: ReadonlySet<string>): boolean {
  // CH5a2-R4(c): the gate reads the Ref sibling, never the legacy href text.
  const ref = row.link_refs?.finding;
  // DIESEL-1-R3p: an unexplained-fuel Finding opens its own page (one address, no window or revision to prove).
  if (ref?.kind === "FUEL_FINDING") return Boolean(linkFor(ref));
  if (!ref || ref.kind !== "FINDING" || !linkFor(ref)) return false;
  if (miniGridIds.has(row.site_id)) return true;
  const w = ref.window;
  return Boolean(w?.from && w.to && w.known_at);
}

export const FINDING_DETAIL_UNAVAILABLE = "Finding detail unavailable";

function Row({ row, knownAt, linked }: { row: EstateFindingRow; knownAt: string; linked: boolean }) {
  const lifecycle = LIFECYCLE_WORDS[row.lifecycle];
  const finding = linkFor(row.link_refs?.finding);
  const site = linkFor(row.link_refs?.site);
  const source = SOURCE_WORDS[sourceState(row.source_provenance as unknown as SourceProvenance)];
  return (
    <tr data-estate-finding={row.finding_id}>
      <td>
        {linked && finding ? (
          <Link className="estate-cell__primary" to={finding} data-estate-finding-link>
            {row.title}
          </Link>
        ) : (
          <>
            <span className="estate-cell__primary" data-estate-finding-inert>
              {row.title}
            </span>
            <span className="estate-cell__secondary" data-estate-finding-unavailable>
              {FINDING_DETAIL_UNAVAILABLE}
            </span>
          </>
        )}
        <CategoryTags categories={row.categories} />
        <TechnicalDetails name={`estate-finding-${row.finding_id}`}>
          <span className="estate-cell__detail">
            Finding {row.finding_id} · revision {row.finding_revision_id} · {source.label}
          </span>
        </TechnicalDetails>
      </td>
      <td>
        {site ? (
          <Link to={site} data-estate-site-link>
            {row.site_code}
          </Link>
        ) : (
          <span>{row.site_code}</span>
        )}
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
        {row.lens_flags.length === 0 ? "Not in any category" : row.lens_flags.map((flag) => LENS_FLAG_WORDS[flag]).join(", ")}
      </td>
    </tr>
  );
}

/** CH-4: the size-unknown words of an opportunity table row. */
export const OPPORTUNITY_SIZE_UNKNOWN = "Size not worked out yet";
export const OPPORTUNITY_LIST_TITLE = "Opportunities to grow";
export const OPPORTUNITIES_UNREAD = "Opportunities could not be read, so none are listed here.";
export const OPPORTUNITY_LIST_NOTE = "Each opportunity is one row · open it for the detail";
export const OPPORTUNITY_INSPECT = "Inspect the solar room →";

/** CH-4 (mock `screens.js:812` oppListPanel): one plain row per opportunity thread; limited evidence in words. */
export function OpportunityList({ items }: { items: readonly EstateOpportunity[] }) {
  return (
    <Panel heading={OPPORTUNITY_LIST_TITLE} headingId="estate-opportunity-list-heading" description={OPPORTUNITY_LIST_NOTE}>
      <ul className="opp-list" data-estate-opportunity-list>
        {items.map((item) => (
          <li key={item.thread_id} data-estate-opportunity-item={item.thread_id}>
            <div>
              <Link to={item.links.opportunity}>
                <strong>{item.title}</strong>
              </Link>
              <small>
                {item.seen_line}
                {item.value_line ? ` · ${item.value_line}` : ""}
              </small>
              {item.limit_line ? <small className="opp-limit">{item.limit_line}</small> : null}
            </div>
            <Link to={item.links.evidence} data-estate-opportunity-evidence>
              {OPPORTUNITY_INSPECT}
            </Link>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

function OpportunityRow({ item }: { item: EstateOpportunity }) {
  return (
    <tr data-estate-opportunity={item.thread_id}>
      <td>
        <Link className="estate-cell__primary" to={item.links.opportunity} data-estate-opportunity-link>
          {`${item.study.code} · ${item.title}`}
        </Link>
        <CategoryTags categories={item.categories} />
      </td>
      <td>
        <Link to={item.links.site} data-estate-site-link>
          {item.site_code}
        </Link>
        <span className="estate-cell__secondary">{item.site_name}</span>
      </td>
      <td>Not assessed</td>
      <td>{item.evidence_label}</td>
      <td>
        <span className="estate-chip" data-estate-opportunity-state={item.state}>
          {item.state_label}
        </span>
      </td>
      <td>{item.value_line ?? OPPORTUNITY_SIZE_UNKNOWN}</td>
      <td>Opportunity</td>
    </tr>
  );
}

function FindingRowsTable({
  body,
  linkedIds,
  opportunities,
}: {
  body: EstateFindingsBody;
  linkedIds: ReadonlySet<string>;
  opportunities: readonly EstateOpportunity[];
}) {
  return (
    <DataTable labelledBy="estate-findings-heading">
      <colgroup>
        {[23, 13, 10, 11, 11, 22, 10].map((width, index) => (
          <col key={index} className="estate-findings-col" style={{ width: `${width}%` }} />
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
          <Row key={row.finding_id} row={row} knownAt={body.window.known_at} linked={findingLinkLive(row, linkedIds)} />
        ))}
        {opportunities.map((item) => (
          <OpportunityRow key={item.thread_id} item={item} />
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

  // Q7: Site names for the cause-aware copy, read at the identical window and cutoff.
  const scopeKey = `${query.from}|${query.to}|${query.known_at ?? ""}`;
  const [scopeResult, setScopeResult] = useState<{ key: string; read: EstateResult<EstateScopeBody> } | null>(null);
  useEffect(() => {
    let live = true;
    void reads
      .scope({ from: query.from, to: query.to, known_at: query.known_at })
      .then((read) => {
        if (live) setScopeResult({ key: scopeKey, read });
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, scopeKey]);
  const scopeBody =
    scopeResult?.key === scopeKey && scopeResult.read.status === "loaded" ? scopeResult.read.value : null;

  const path = ESTATE_FINDING_LENS_PATHS[lens];
  const lensHref = (next: EstateLens) => estateHref(ESTATE_FINDING_LENS_PATHS[next], query, { state: query.state });
  const stateHref = (state: EstateStateFilter) => estateHref(path, query, { state });
  const firstPage = estateHref(path, query, { state: query.state });
  const read = result?.key === `${lens}|${key}` ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;
  // OUT-C U5: the early warnings of the page's own window, from the estate outcome summary.
  const summary = useOutcomeSummary(reads, { from: query.from, to: query.to, known_at: query.known_at });
  const warnings = summary?.status === "loaded" ? summary.value.warnings.filter(LENS_WARNING_FILTER[lens]) : [];

  return (
    <div className="estate-page" data-estate-root={lens}>
      <PageHeader title="Findings" subtitle={SUBTITLE[lens]} />
      <LensTabs lens={lens} href={lensHref} />
      <EstateDateBar
        key={`${query.from}|${query.to}|${query.known_at ?? ""}`}
        query={query}
        body={body}
        windowRefused={read?.status === "refused" && read.code === "INVALID_WINDOW"}
        onApply={(next) => navigate(estateHref(path, next, { state: query.state }))}
      />
      {read === null ? (
        <p className="estate-loading">Loading the findings across the estate.</p>
      ) : read.status === "refused" ? (
        <EstateRefusal code={read.code} copy={read.copy} window={query} firstPage={firstPage} />
      ) : (
        <Loaded
          body={read.value}
          scope={scopeBody}
          lens={lens}
          active={query.state}
          stateHref={stateHref}
          path={path}
          query={query}
          warnings={warnings}
        />
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
  scope,
  warnings,
}: {
  body: EstateFindingsBody;
  scope: EstateScopeBody | null;
  lens: EstateLens;
  active: EstateStateFilter;
  stateHref: (state: EstateStateFilter) => string;
  path: string;
  query: ReturnType<typeof queryFromParams>;
  warnings: readonly OutcomeWarning[];
}) {
  const linkedIds = miniGridSiteIds(body);
  const anyLinked = body.rows.some((row) => findingLinkLive(row, linkedIds));
  const cause = findingCauseCopy(body, scope);
  const complete = body.total_count !== null;
  const empty = complete && body.total_count === 0;
  const next = body.next_cursor === null ? null : estateHref(path, query, { state: active, cursor: body.next_cursor });
  // CH-4: opportunity items join the table on lens All and Opportunities, on page one only, after the Finding rows.
  const opportunities = (lens === "all" || lens === "opportunities") && query.cursor === null ? findingOpportunities(body) : [];
  // CH-4 M1: a failed opportunity read is said so on the lenses that list opportunities, never an empty lens.
  const unread = (lens === "all" || lens === "opportunities") && findingOpportunitiesUnread(body);
  return (
    <>
      <Cards body={body} />
      <StateChips active={active} href={stateHref} />
      {lens === "opportunities" && opportunities.length > 0 ? <OpportunityList items={opportunities} /> : null}
      <Panel
        heading={PANEL_TITLE[lens]}
        headingId="estate-findings-heading"
        description="Lens is how a finding is read, not a second object · state is a filter"
      >
        {body.rows.length > 0 || opportunities.length > 0 ? (
          <FindingRowsTable body={body} linkedIds={linkedIds} opportunities={opportunities} />
        ) : null}
        {empty && opportunities.length === 0 ? (
          <div className="estate-empty" data-estate-empty>
            <p>No findings match.</p>
            {LENS_EMPTY[lens] === null || (unread && lens === "opportunities") ? null : <p>{LENS_EMPTY[lens]}</p>}
          </div>
        ) : null}
        {unread ? (
          <p className="estate-partial" data-estate-opportunities-unread>
            {OPPORTUNITIES_UNREAD}
          </p>
        ) : null}
        {cause.panel.map((line) => (
          <p key={line} className="estate-partial" data-estate-partial>
            {line}
          </p>
        ))}
        <Pager next={next} first={stateHref(active)} paged={query.cursor !== null} />
        <EarlyWarningList warnings={warnings} showSite />
      </Panel>
      <LimitationNotice sentences={cause.notice} />
      <Notice tone="blue" data={{ "data-estate-notice": "" }}>
        {FINDINGS_NOTICE}
        {body.rows.length === 0 ? null : ` ${anyLinked ? FINDINGS_LINKED_NOTICE : FINDINGS_UNLINKED_NOTICE}`}
      </Notice>
    </>
  );
}
