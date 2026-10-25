/**
 * W6-01c C2/C3: the work request page parts shared by Overview (C2), Maintenance record (C3) and History (C4), from the
 * v6.9 `wr-overview` mock (`index.html:966-968`: `wrHeader`, `WR_TABS`, `breadcrumbs`, shell heading action) and
 * `.agent/W6-01-build-spec.md` "C1-C3 pre-flight rulings" P-C2-1..14 and P-X-1..3, which supersede section 2,
 * CL3-5 and A2Q7 for these pages.
 *
 * The page reads `GET /api/work/requests/{case_id}?site_id={site_code}[&known_at=]` once per route/query. Headings
 * stay visible while loading and on refusal with ruled literals; an invalid page query never fetches. The tab row
 * owns the remaining `UnavailableTab` literals once, so `navigation-truthfulness.ps1` `$expectedTabs` counts each
 * once. C3 promoted Maintenance record (`${WORK_REQUEST_PATH_PREFIX}/{id}/record`) and W6-01d C4 promoted History
 * (`${WORK_REQUEST_PATH_PREFIX}/{id}/history`); Verification stays unavailable until its page mounts.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { MetricHeader, PageHeader, Panel } from "../ui";
import { UnavailableTab } from "../ui/UnavailableEntry";
import { useCurrentTabInView } from "../ui/useCurrentTabInView";
import {
  GLOBAL_WORK_DETAIL_REFUSAL_COPY,
  createGlobalWorkClient,
  findingLinkSelectsRevision,
  globalWorkDetailPageQuery,
  globalWorkRequestHref,
  globalWorkUtc,
  globalWorkUtcSeconds,
  type GlobalWorkClient,
  type GlobalWorkDetailBody,
  type GlobalWorkDetailPageQuery,
  type GlobalWorkDetailRefusalCode,
  type GlobalWorkDetailResult,
  type GlobalWorkLink,
  type WorkCaseDetailRecord,
} from "./globalWorkClient";
import { Clamp, MockDeviation, joined } from "./globalWorkParts";
import "./globalWork.css";

/** The request route path prefix; `WORK_REQUEST_ROUTE_PATH` in `shell/operatorSiteRoutes.ts` is `${this}/:caseId`. */
export const WORK_REQUEST_PATH_PREFIX = "/maintenance/requests";
export const WORK_REQUEST_HEADING_ID = "work-request-heading";

/** P-C2-1: the heading literals before data, on refusal and with no `site_id`. */
export const WORK_REQUEST_TITLE = "Work request";
export const WORK_REQUEST_LOADING = "Loading the work request.";
export const WORK_REQUEST_REFUSED_SUBTITLE = "Request details could not be shown.";
/** Post-W6 W6 Q11 (R367): a no-site address states the refusal subtitle and this body sentence. */
export const WORK_REQUEST_NO_SITE_SENTENCE = "Choose a request at a site.";
/** P-C2-4: the date-bar line on refusal. */
export const WORK_REQUEST_UNAVAILABLE = "Work request unavailable.";
export const NOT_ASSIGNED = "Not assigned";
export const NOT_RECORDED = "Not recorded";
export const LINK_UNAVAILABLE_AT_CUTOFF = "Link unavailable at this cutoff";

const STATE_LABEL: Readonly<Record<string, string>> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
  // Post-W6 W6 Q12 (R370): no writer enters this state yet; the summary appends `· outcome not established`.
  VERIFICATION_WINDOW: "Verification open",
};

export function stateLabel(state: string): string {
  return STATE_LABEL[state] ?? state;
}

/** Why the page shows no request: an invalid page query (no fetch) or a refused/malformed read. */
export type WorkRequestFailure =
  | { kind: "no-site" }
  | { kind: "code"; code: GlobalWorkDetailRefusalCode };

export interface WorkRequestRead {
  parsed: GlobalWorkDetailPageQuery;
  /** The validated case ID and Site code, when both are valid (the tab row's anchor inputs). */
  target: { caseId: string; siteId: string; knownAt: string | null } | null;
  read: GlobalWorkDetailResult | null;
  body: GlobalWorkDetailBody | null;
  failure: WorkRequestFailure | null;
  /** True only while a fetchable query waits for its answer. */
  loading: boolean;
  reload: () => void;
}

/** P-C2-14 query rules and one detail read per route/query; Reload repeats the same query. */
export function useWorkRequest(client: GlobalWorkClient | undefined): WorkRequestRead {
  const reads = useMemo(() => client ?? createGlobalWorkClient(), [client]);
  const { caseId } = useParams();
  const [params] = useSearchParams();
  const parsed = globalWorkDetailPageQuery(caseId, params);
  const query = parsed.status === "valid" ? parsed.query : null;
  const key = query === null ? "" : JSON.stringify(query);
  const [nonce, setNonce] = useState(0);
  const [result, setResult] = useState<{ key: string; nonce: number; read: GlobalWorkDetailResult } | null>(null);

  useEffect(() => {
    if (query === null) return undefined;
    let live = true;
    const pending: Promise<GlobalWorkDetailResult> = reads.detail
      ? reads.detail(query)
      : Promise.resolve({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
    void pending.then((read) => {
      if (live) setResult({ key, nonce, read });
    });
    return () => {
      live = false;
    };
    // `key` carries the whole page query; `nonce` is a Reload of the same query.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key, nonce]);

  const read = query !== null && result?.key === key && result.nonce === nonce ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;
  let failure: WorkRequestFailure | null = null;
  if (parsed.status === "invalid") {
    failure =
      parsed.reason === "no-site"
        ? { kind: "no-site" }
        : { kind: "code", code: parsed.reason === "known-at" ? "INVALID_KNOWN_AT" : "WORK_CASE_NOT_FOUND" };
  } else if (read?.status === "refused") {
    failure = { kind: "code", code: read.code };
  }
  const target =
    query !== null
      ? { caseId: query.case_id, siteId: query.site_id, knownAt: query.known_at }
      : parsed.status === "invalid" && parsed.reason === "known-at" && caseId !== undefined && parsed.siteId !== null
        ? { caseId, siteId: parsed.siteId, knownAt: null }
        : null;
  return {
    parsed,
    target,
    read,
    body,
    failure,
    loading: query !== null && read === null,
    reload: () => setNonce((n) => n + 1),
  };
}

/**
 * P-C2-2: the mock breadcrumb `Maintenance › {WR code} › Overview · site: {Site}`. `Maintenance` links to the root
 * with no invented window; the WR code and `Overview` are text; the Site links to `links.site.href` after load.
 * Before data it reads `Maintenance › Work request › Overview` with no Site.
 */
export function WorkRequestBreadcrumbs({ body, tab }: { body: GlobalWorkDetailBody | null; tab: WorkRequestTab }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb" data-work-request-breadcrumb>
      <ol className="breadcrumbs__list">
        <li className="breadcrumbs__item">
          <Link to="/maintenance">Maintenance</Link>
        </li>
        <li className="breadcrumbs__item">
          <span>{body?.selected.case_code ?? WORK_REQUEST_TITLE}</span>
        </li>
        <li className="breadcrumbs__item">
          <span className="breadcrumbs__current" aria-current="page">
            {TAB_LABEL[tab]}
          </span>
        </li>
      </ol>
      {body !== null ? (
        <span className="work-request-crumb-site" data-work-request-breadcrumb-site>
          {"· site: "}
          {body.links.site.href ? <Link to={body.links.site.href}>{body.links.site.label}</Link> : body.links.site.label}
        </span>
      ) : null}
    </nav>
  );
}

/**
 * P-C2-3: the mock `Open site` heading action. Post-W6 W6 Q11 (R367): rendered only with a Site href; before load
 * or on refusal there is no control.
 */
export function OpenSite({ body }: { body: GlobalWorkDetailBody | null }) {
  const href = body?.links.site.href ?? null;
  return href ? (
    <Link className="button" to={href} data-work-request-open-site>
      Open site
    </Link>
  ) : null;
}

export function subtitleOf(page: WorkRequestRead): string {
  if (page.body !== null) return `${page.body.selected.case_code} · ${page.body.links.site.label} · corrective`;
  if (page.failure !== null) return WORK_REQUEST_REFUSED_SUBTITLE;
  return WORK_REQUEST_LOADING;
}

export type WorkRequestTab = "overview" | "record" | "history";

/** The mock `WR_TABS` labels of the mounted tabs; the breadcrumb's last item names the current one (`s.section`). */
export const TAB_LABEL: Readonly<Record<WorkRequestTab, string>> = {
  overview: "Overview",
  record: "Maintenance record",
  history: "History",
};
/** The route suffix of each mounted tab under `${WORK_REQUEST_PATH_PREFIX}/{case_id}`. */
export const TAB_SUFFIX: Readonly<Record<WorkRequestTab, string>> = { overview: "", record: "/record", history: "/history" };

/** One mounted tab: the API link after load, else the validated inputs; text when neither exists. */
export function LiveTab({ page, tab, current }: { page: WorkRequestRead; tab: WorkRequestTab; current: WorkRequestTab }) {
  const { target, body } = page;
  const apiHref = body === null ? null : body.links[tab].href;
  const href =
    apiHref ??
    (target === null
      ? null
      : globalWorkRequestHref(`${WORK_REQUEST_PATH_PREFIX}/${encodeURIComponent(target.caseId)}${TAB_SUFFIX[tab]}`, {
          site_id: target.siteId,
          known_at: target.knownAt,
        }));
  const currentProps = tab === current ? ({ "aria-current": "page" } as const) : {};
  return (
    <li className="site-tabs__item">
      {href ? (
        <Link className="site-tabs__link" to={href} {...currentProps} data-work-request-tab={tab}>
          {TAB_LABEL[tab]}
        </Link>
      ) : (
        <span className="site-tabs__link" {...currentProps} data-work-request-tab={tab}>
          {TAB_LABEL[tab]}
        </span>
      )}
    </li>
  );
}

/**
 * P-C2-5 / F4: `Context tabs` in mock `WR_TABS` order. Overview (C2), Maintenance record (C3) and History (C4) are
 * live (validated inputs before the response, API `links.overview` / `links.record` / `links.history` after; an
 * explicit cutoff stays on each); Verification is unavailable until its page mounts. With no valid case/Site
 * the live labels are text. The `UnavailableTab` element renders an `li`, so the list element is the `ol` every
 * other tab row uses.
 */
export function WorkRequestTabs({ page, tab }: { page: WorkRequestRead; tab: WorkRequestTab }) {
  // Post-W6 W6 Q9 (R364, superseding W6-01d M1): at 760 px and below the row wraps with complete labels (CSS), so
  // nothing is clipped; the in-view hook stays harmless when the row does not scroll.
  const rowRef = useCurrentTabInView<HTMLElement>();
  return (
    <>
      <nav ref={rowRef} aria-label="Context tabs" className="site-tabs work-request-tabs" data-work-request-tabs>
        <ol className="site-tabs__list">
          <LiveTab page={page} tab="overview" current={tab} />
          <LiveTab page={page} tab="record" current={tab} />
          <UnavailableTab label="Verification" />
          <LiveTab page={page} tab="history" current={tab} />
        </ol>
        {/* MOCK DEVIATION D1 (R396): the mock's Verification tab is available; here it is visibly unavailable
            because no verification view is mounted for a work request. Owner decision open. The line sits under
            the row inside the same landmark (the T011C precedent). */}
        <MockDeviation category="D1" id="R396" />
      </nav>
    </>
  );
}

/** P-C2-4 (R6): the date-bar slot; no window picker, list status or invented chip. */
export function WorkRequestBar({ page }: { page: WorkRequestRead }) {
  const { body, failure, loading, target } = page;
  let line: ReactNode = null;
  if (loading) {
    line = (
      <p role="status" className="global-work-loading" data-global-work-loading>
        {WORK_REQUEST_LOADING}
      </p>
    );
  } else if (body !== null) {
    // Post-W6 W6 Q14 (R372): a historical cutoff is stated to the second; the current line keeps minutes.
    line = (
      <p className="work-request-asof" data-work-request-asof={target?.knownAt ? "historical" : "current"}>
        {target?.knownAt
          ? `Historical as of ${globalWorkUtcSeconds(body.selected.known_at)}`
          : `As known at ${globalWorkUtc(body.selected.known_at)}`}
      </p>
    );
  } else if (failure !== null) {
    line = <p data-work-request-unavailable>{WORK_REQUEST_UNAVAILABLE}</p>;
  }
  // Post-W6 W6 Q11 (R367): Reload repeats a loaded read or a 503 store refusal; never 401/403/404/422 or no-site.
  const retryable = failure?.kind === "code" && failure.code === "WORK_STORE_UNAVAILABLE";
  const fetched = page.parsed.status === "valid" && !loading && (body !== null || retryable);
  return (
    <div className="site-date-bar global-work-bar work-request-bar" data-global-work-bar>
      {line}
      {fetched ? (
        <button className="button" type="button" onClick={page.reload} data-work-request-reload>
          Reload
        </button>
      ) : null}
      {/* MOCK DEVIATION D2 (R363): the added date-bar row states the read cutoff. */}
      {body !== null ? <MockDeviation category="D2" id="R363" /> : null}
    </div>
  );
}

/** The one refusal sentence (Post-W6 W6 Q8/Q11: announced as an alert; no-site states its own sentence). */
export function WorkRequestRefusal({ failure }: { failure: WorkRequestFailure }) {
  const hook = failure.kind === "no-site" ? "NO_SITE" : failure.code;
  const sentence = failure.kind === "no-site" ? WORK_REQUEST_NO_SITE_SENTENCE : GLOBAL_WORK_DETAIL_REFUSAL_COPY[failure.code];
  return (
    <div role="alert" className="notice v69-notice global-work-state" data-global-work-refusal={hook} data-page-refusal={hook}>
      <p>{sentence}</p>
    </div>
  );
}

/** The selected maintenance-record heads (no other item supersedes them), in `(recorded_at, id)` order. */
export function recordHeads(records: WorkCaseDetailRecord[]): WorkCaseDetailRecord[] {
  const superseded = new Set(records.map((r) => r.supersedes_record_id).filter((id): id is string => id !== null));
  return records
    .filter((r) => !superseded.has(r.id))
    .sort((a, b) => (a.recorded_at === b.recorded_at ? (a.id < b.id ? -1 : 1) : a.recorded_at < b.recorded_at ? -1 : 1));
}

/** CL3-5 Owner: the last ASSIGN event's `payload.assignee` by `(recorded_at, id)`, else `Not assigned`. */
export function ownerOf(body: GlobalWorkDetailBody): string {
  const assigns = body.work_detail.events
    .filter((e) => e.kind === "ASSIGN")
    .sort((a, b) => (a.recorded_at === b.recorded_at ? (a.id < b.id ? -1 : 1) : a.recorded_at < b.recorded_at ? -1 : 1));
  const last = assigns[assigns.length - 1];
  const assignee = (last?.payload as Record<string, unknown> | undefined)?.assignee;
  return typeof assignee === "string" && assignee !== "" ? assignee : NOT_ASSIGNED;
}

function SourceLink({ link, plain = false }: { link: GlobalWorkLink; plain?: boolean }) {
  if (plain) return <span data-work-request-source-link="plain">{link.label}</span>;
  return link.href ? (
    <Link to={link.href} data-work-request-source-link="">
      {link.label}
    </Link>
  ) : (
    <span data-work-request-source-link="unavailable">{`${link.label} · ${LINK_UNAVAILABLE_AT_CUTOFF}`}</span>
  );
}

/**
 * P-C2-10: Source shows the incident link (when present), then every outer Finding link joined ` · `; a pinned
 * Finding without lineage is plain text with `Link unavailable at this cutoff`; neither is `Not recorded`. Post-W6
 * W6 Q2 (R352): a cold or EV Finding is plain `Finding {id8}` with no anchor and no unavailable suffix, because its
 * domain Finding frame does not select the revision.
 */
function sourceOf(body: GlobalWorkDetailBody): { node: ReactNode; text: string } {
  const plainFindings = !findingLinkSelectsRevision(body.selected.site_domain);
  const links = [
    ...(body.links.source_incident ? [{ link: body.links.source_incident, plain: false }] : []),
    ...body.links.findings.map((link) => ({ link, plain: plainFindings })),
  ];
  if (links.length === 0) return { node: NOT_RECORDED, text: NOT_RECORDED };
  return {
    node: joined(
      links.map(({ link, plain }, index) => <SourceLink key={`${link.label}-${index}`} link={link} plain={plain} />),
      " · ",
    ),
    text: links
      .map(({ link, plain }) => (plain || link.href ? link.label : `${link.label} · ${LINK_UNAVAILABLE_AT_CUTOFF}`))
      .join(" · "),
  };
}

/** Section 2: Owner and Source show a two-line preview and the complete escaped value in a disclosure. */
function Preview({ value, full, summary, hook }: { value: ReactNode; full: string; summary: string; hook: string }) {
  return (
    <>
      <div className="work-request-preview" data-work-request-preview={hook}>
        {value}
      </div>
      <details className="global-work-details" data-work-request-full={hook}>
        <summary>{summary}</summary>
        {full}
      </details>
    </>
  );
}

/** The mock `wrHeader` mheader (`.v69-mheader`): Owner, Due / SLA, State, Source, Success criterion (CL3-5). */
export function WorkRequestMHeader({ body }: { body: GlobalWorkDetailBody }) {
  const owner = ownerOf(body);
  const source = sourceOf(body);
  return (
    <MetricHeader
      label="Work request summary"
      data={{ "data-work-request-mheader": "" }}
      cells={[
        ["Owner", <Preview value={owner} full={owner} summary="Full owner text" hook="owner" />, "owner"],
        ["Due / SLA", "Not set", "due"],
        ["State", `${stateLabel(body.work_detail.case.state)} · outcome not established`, "state"],
        ["Source", <Preview value={source.node} full={source.text} summary="Full source text" hook="source" />, "source"],
        ["Success criterion", NOT_RECORDED, "success"],
      ]}
    />
  );
}

/**
 * The request page frame: breadcrumb, heading with `Open site`, tab row, date bar, then the refusal block or the
 * mheader, then the page's panels (`children` receives the loaded body or null; panels keep their slots). A page's
 * `accept` check (C4: a CREATED event) turns a loaded body it rejects into the 503 store refusal, failing closed.
 */
export function WorkRequestFrame({
  client,
  rootClass,
  tab = "overview",
  accept,
  children,
}: {
  client?: GlobalWorkClient;
  rootClass: string;
  /** The current mounted tab; Overview when omitted (C2's page passes none). */
  tab?: WorkRequestTab;
  /** A page-local consistency check on the loaded body; a rejected body reads as `WORK_STORE_UNAVAILABLE`. */
  accept?: (body: GlobalWorkDetailBody) => boolean;
  children: (body: GlobalWorkDetailBody | null) => ReactNode;
}) {
  const raw = useWorkRequest(client);
  const page: WorkRequestRead =
    accept !== undefined && raw.body !== null && !accept(raw.body)
      ? {
          ...raw,
          read: { status: "refused", code: "WORK_STORE_UNAVAILABLE" },
          body: null,
          failure: { kind: "code", code: "WORK_STORE_UNAVAILABLE" },
        }
      : raw;
  const { body, failure } = page;
  return (
    <main aria-labelledby={WORK_REQUEST_HEADING_ID}>
      <div className={`global-work work-request ${rootClass}`} data-work-request-root>
        <WorkRequestBreadcrumbs body={body} tab={tab} />
        <PageHeader
          title={body?.work_detail.selected_revision.title ?? WORK_REQUEST_TITLE}
          headingId={WORK_REQUEST_HEADING_ID}
          subtitle={subtitleOf(page)}
          actions={<OpenSite body={body} />}
        />
        <WorkRequestTabs page={page} tab={tab} />
        <WorkRequestBar page={page} />
        {failure !== null ? <WorkRequestRefusal failure={failure} /> : null}
        {body !== null ? <WorkRequestMHeader body={body} /> : null}
        {/* Post-W6 W6 Q11 (R367): a refused request shows the header and one refusal, never page panels. */}
        {failure === null ? children(body) : null}
      </div>
    </main>
  );
}

export const UNKNOWN_SECTION_HEADING_ID = "work-request-unknown-section-heading";
export const UNKNOWN_SECTION_TEXT = "No work request section is served at this address.";
export const OPEN_REQUEST_OVERVIEW = "Open this request's overview";

/**
 * Post-W6 W6 Q13 (R371): an unknown section under a work request (`/maintenance/requests/{id}/{anything}`) is stated
 * inside the operator shell, never redirected and never read from the API. With a valid request ID and Site it
 * offers that request's Overview, keeping the validated `site_id` and (when valid) `known_at`.
 */
export function WorkRequestUnknownSectionFrame() {
  const { caseId } = useParams();
  const [params] = useSearchParams();
  const parsed = globalWorkDetailPageQuery(caseId, params);
  const target =
    parsed.status === "valid"
      ? { caseId: parsed.query.case_id, site_id: parsed.query.site_id, known_at: parsed.query.known_at }
      : parsed.status === "invalid" && parsed.reason === "known-at" && caseId !== undefined && parsed.siteId !== null
        ? { caseId, site_id: parsed.siteId, known_at: null }
        : null;
  return (
    <main aria-labelledby={UNKNOWN_SECTION_HEADING_ID}>
      <div className="global-work work-request work-request--unknown-section" data-work-request-unknown-section>
        <PageHeader title="Page not available" headingId={UNKNOWN_SECTION_HEADING_ID} />
        <Panel heading="This address is not served" headingId="work-request-unknown-section-detail">
          <p>{UNKNOWN_SECTION_TEXT}</p>
          {target !== null ? (
            <p>
              <Link
                to={globalWorkRequestHref(`${WORK_REQUEST_PATH_PREFIX}/${encodeURIComponent(target.caseId)}`, target)}
                data-work-request-open-overview
              >
                {OPEN_REQUEST_OVERVIEW}
              </Link>
            </p>
          ) : null}
        </Panel>
      </div>
    </main>
  );
}

/** Re-exported for the page modules: the shared clamp keeps cell text bounded. */
export { Clamp };
