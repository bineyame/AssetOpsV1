/**
 * W3-01 commit 3: the four estate Finding lens roots (v6.9 `findings`, `findings-cost`, `findings-risks`,
 * `findings-opportunities`) read from `GET /api/estate/findings` (`estate-finding-index-2`). Copy and states follow
 * `.agent/W3-01-build-spec.md` "Per-screen panel/copy/layout dry-read", Review closure B3/B7/S19, Run 6 Blocker 2,
 * Run 8 rulings 3-5 and Run 12 ruling 3. Priority and confidence stay `Not assessed` in the row columns (the summary cards no longer show them, FC-1); Risks and Opportunities stay
 * honestly empty until a stored eligible kind exists. No mock ID, count, price or savings is rendered.
 */
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { RangeLink as Link } from "../ui/RangeLink";
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
  EstateCutoffLine,
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
  // COV-PARTIAL MOCK DEVIATION R622: a row of a Site with incomplete days never shows an amount (the backend sends
  // none). PF-W (D-E5.46): "incomplete days", never "checked".
  if (rowStatus === "PARTIAL") {
    return consequence.source_revision_id === null ? "No consequence recorded" : consequence.state === "UNPRICED" ? "Unpriced" : "Value not shown while this site has incomplete days";
  }
  if (consequence.source_revision_id === null) return "No consequence recorded";
  if (consequence.state === "UNPRICED") return "Unpriced";
  if (rowStatus === "HISTORICAL") return `Historical as of ${utcInstant(knownAt)}`;
  return "Source not checked";
}

export const NOT_COUNTED_YET = "Not counted yet";
export const COUNTED_WHEN_ANALYSED = "Counted once every site is fully analysed";
export const NOT_YET_CONFIRMED_NOTE = "Seen, but the readings do not yet confirm it · read with care";
export const AWAITING_MINI_GRID_ONLY = "mini-grid sites only; cold room and EV charging are not counted here yet";
export const SO_FAR_EXPLAINED =
  "\"So far\" because findings on incomplete days are not shown, so more may appear once those days have a usable result.";

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

/**
 * FC-1 (D-E5.26): the Site breakdown behind the "So far" note, in the analysis words of the proposal's term table,
 * from `coverage.sites` (NOT_APPLICABLE sites leave the denominator). Returns null when every applicable Site is fully
 * analysed.
 */
function siteBreakdown(body: EstateFindingsBody): { full: number; applicable: number; parts: string[] } | null {
  const sites = body.coverage.sites.filter((x) => x.state !== "NOT_APPLICABLE");
  const full = sites.filter((x) => x.state === "CURRENT" || x.state === "HISTORICAL").length;
  if (full === sites.length) return null;
  const of = (...states: string[]) => sites.filter((x) => states.includes(x.state)).length;
  const known = ["CURRENT", "HISTORICAL", "PARTIAL", "PENDING_RECOMPUTE", "STALE_SOURCE"];
  const parts: string[] = [];
  const add = (n: number, one: string, many: string) => n > 0 && parts.push(plural(n, one, many));
  // D-E5.46 (amends D-E5.26): a PARTIAL Site has incomplete days (no readings, or not analysed yet).
  add(of("PARTIAL"), "site with incomplete days", "sites with incomplete days");
  add(of("PENDING_RECOMPUTE"), "site still processing", "sites still processing");
  add(of("STALE_SOURCE"), "site with no new readings received", "sites with no new readings received");
  add(sites.filter((x) => !known.includes(x.state)).length, "site not analysed yet", "sites not analysed yet");
  return { full, applicable: sites.length, parts };
}

const withParts = (lead: string, parts: string[]) => [lead, ...parts].join(" · ");

/**
 * FC-1 (D-E5.25 to D-E5.28; MOCK DEVIATION MD-FC-1..3, register R715-R717, v71 findings-cards draft): three cards.
 * The counts are over the rows read; when the coverage is not complete each carries "So far" and the Site breakdown,
 * and a null count (an older backend) reads "Not counted yet".
 */
function Cards({ body }: { body: EstateFindingsBody }) {
  const s = body.summary;
  const breakdown = siteBreakdown(body);
  const complete = body.coverage.state === "COMPLETE";
  const parts = breakdown?.parts ?? [];
  const soFar = withParts(
    breakdown === null ? "So far" : `So far: ${breakdown.full} of ${plural(breakdown.applicable, "site", "sites")} fully analysed`,
    parts,
  );
  const unconfirmed = s.unconfirmed_findings ?? null;
  const anyCounted = [s.supported_findings, unconfirmed, s.awaiting_verification].some((v) => v !== null);
  const awaitingBase = s.awaiting_verification === 0 ? AWAITING_ZERO : "Action taken; outcome open";
  const card = (key: string, label: string, value: number | null, note: string, extra?: React.ReactNode) => (
    <MetricCard
      label={label}
      value={value === null ? NOT_COUNTED_YET : String(value)}
      word={value === null}
      tone={value === null ? "amber" : undefined}
      note={
        <>
          {note}
          {extra}
        </>
      }
      data={{ "data-estate-card": key }}
    />
  );
  return (
    <>
      <MetricCards columns={3} label="Findings summary" data={{ "data-estate-cards": "" }}>
        {card(
          "supported_findings",
          "Confirmed findings",
          s.supported_findings,
          s.supported_findings === null
            ? withParts(COUNTED_WHEN_ANALYSED, parts)
            : complete
              ? `Across ${body.scope.authorized_site_count} sites`
              : soFar,
        )}
        {card(
          "unconfirmed_findings",
          "Not yet confirmed",
          unconfirmed,
          unconfirmed === null ? COUNTED_WHEN_ANALYSED : complete ? NOT_YET_CONFIRMED_NOTE : soFar,
        )}
        {card(
          "awaiting_verification",
          "Awaiting verification",
          s.awaiting_verification,
          s.awaiting_verification === null
            ? COUNTED_WHEN_ANALYSED
            : complete
              ? `${awaitingBase} · ${AWAITING_MINI_GRID_ONLY}`
              : `So far · ${AWAITING_MINI_GRID_ONLY}`,
          s.awaiting_verification === null ? undefined : (
            <>
              {" "}
              <Disclosure summary="How this is counted" name="estate-awaiting-rule" variant="inline">
                {AWAITING_RULE}
              </Disclosure>
            </>
          ),
        )}
      </MetricCards>
      {!complete && anyCounted ? <p className="estate-cards-note" data-estate-so-far>{SO_FAR_EXPLAINED}</p> : null}
    </>
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
  // COV-PARTIAL MOCK DEVIATION R622: Sites with incomplete days name their days from the backend's `days.text`.
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
      panel.push(`${partialNames.join(", ")} ${partial.length === 1 ? "has" : "have"} incomplete days; totals are unknown.`);
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
      <EstateCutoffLine query={query} body={body} windowRefused={read?.status === "refused" && read.code === "INVALID_WINDOW"} />
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
