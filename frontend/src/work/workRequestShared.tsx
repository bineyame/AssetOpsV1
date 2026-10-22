/**
 * W6-01c C2/C3: the work request page parts shared by Overview (C2), Maintenance record (C3) and History (C4), from the
 * v6.9 `wr-overview` mock (`index.html:966-968`: `wrHeader`, `WR_TABS`, `breadcrumbs`, shell heading action) and
 * `.agent/W6-01-build-spec.md` "C1-C3 pre-flight rulings" P-C2-1..14 and P-X-1..3, which supersede section 2,
 * CL3-5 and A2Q7 for these pages.
 *
 * The page reads `GET /api/work/requests/{case_id}?site_id={site_code}[&known_at=]` once per route/query. Headings
 * stay visible while loading and on refusal with ruled literals; an invalid page query never fetches. The tab row
 * owns the remaining `UnavailableTab` literals once, so `navigation-truthfulness.ps1` `$expectedTabs` counts each
 * once. C3 promoted Maintenance record (`${WORK_REQUEST_PATH_PREFIX}/{id}/record`); Verification and History stay
 * unavailable until their pages mount.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { MetricHeader, PageHeader } from "../ui";
import { UnavailableTab } from "../ui/UnavailableEntry";
import {
  GLOBAL_WORK_DETAIL_REFUSAL_COPY,
  createGlobalWorkClient,
  globalWorkDetailPageQuery,
  globalWorkRequestHref,
  globalWorkUtc,
  type GlobalWorkClient,
  type GlobalWorkDetailBody,
  type GlobalWorkDetailPageQuery,
  type GlobalWorkDetailRefusalCode,
  type GlobalWorkDetailResult,
  type GlobalWorkLink,
  type WorkCaseDetailRecord,
} from "./globalWorkClient";
import { Clamp, joined } from "./globalWorkParts";
import "./globalWork.css";

/** The request route path prefix; `WORK_REQUEST_ROUTE_PATH` in `shell/operatorSiteRoutes.ts` is `${this}/:caseId`. */
export const WORK_REQUEST_PATH_PREFIX = "/maintenance/requests";
export const WORK_REQUEST_HEADING_ID = "work-request-heading";

/** P-C2-1: the heading literals before data, on refusal and with no `site_id`. */
export const WORK_REQUEST_TITLE = "Work request";
export const WORK_REQUEST_LOADING = "Loading the work request.";
export const WORK_REQUEST_REFUSED_SUBTITLE = "Request details could not be shown.";
export const WORK_REQUEST_NO_SITE_SUBTITLE = "Choose a request at a site.";
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
function WorkRequestBreadcrumbs({ body, tab }: { body: GlobalWorkDetailBody | null; tab: WorkRequestTab }) {
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

/** P-C2-3: the mock `Open site` heading action; text without an anchor before load or on refusal. */
function OpenSite({ body }: { body: GlobalWorkDetailBody | null }) {
  const href = body?.links.site.href ?? null;
  return href ? (
    <Link className="button" to={href} data-work-request-open-site>
      Open site
    </Link>
  ) : (
    <span className="button" data-work-request-open-site="text">
      Open site
    </span>
  );
}

function subtitleOf(page: WorkRequestRead): string {
  if (page.body !== null) return `${page.body.selected.case_code} · ${page.body.links.site.label} · corrective`;
  if (page.failure?.kind === "no-site") return WORK_REQUEST_NO_SITE_SUBTITLE;
  if (page.failure !== null) return WORK_REQUEST_REFUSED_SUBTITLE;
  return WORK_REQUEST_LOADING;
}

export type WorkRequestTab = "overview" | "record";

/** The mock `WR_TABS` labels of the mounted tabs; the breadcrumb's last item names the current one (`s.section`). */
const TAB_LABEL: Readonly<Record<WorkRequestTab, string>> = { overview: "Overview", record: "Maintenance record" };
/** The route suffix of each mounted tab under `${WORK_REQUEST_PATH_PREFIX}/{case_id}`. */
const TAB_SUFFIX: Readonly<Record<WorkRequestTab, string>> = { overview: "", record: "/record" };

/** One mounted tab: the API link after load, else the validated inputs; text when neither exists. */
function LiveTab({ page, tab, current }: { page: WorkRequestRead; tab: WorkRequestTab; current: WorkRequestTab }) {
  const { target, body } = page;
  const apiHref = body === null ? null : (tab === "overview" ? body.links.overview : body.links.record).href;
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
 * P-C2-5 / F4: `Context tabs` in mock `WR_TABS` order. Overview (C2) and Maintenance record (C3) are live (validated
 * inputs before the response, API `links.overview` / `links.record` after; an explicit cutoff stays on both);
 * Verification and History are unavailable until their pages mount (C4 promotes History). With no valid case/Site
 * the live labels are text. The `UnavailableTab` element renders an `li`, so the list element is the `ol` every
 * other tab row uses.
 */
function WorkRequestTabs({ page, tab }: { page: WorkRequestRead; tab: WorkRequestTab }) {
  return (
    <nav aria-label="Context tabs" className="site-tabs work-request-tabs" data-work-request-tabs>
      <ol className="site-tabs__list">
        <LiveTab page={page} tab="overview" current={tab} />
        <LiveTab page={page} tab="record" current={tab} />
        <UnavailableTab label="Verification" />
        <UnavailableTab label="History" />
      </ol>
    </nav>
  );
}

/** P-C2-4 (R6): the date-bar slot; no window picker, list status or invented chip. */
function WorkRequestBar({ page }: { page: WorkRequestRead }) {
  const { body, failure, loading, target } = page;
  let line: ReactNode = null;
  if (loading) {
    line = (
      <p className="global-work-loading" data-global-work-loading>
        {WORK_REQUEST_LOADING}
      </p>
    );
  } else if (body !== null) {
    const when = globalWorkUtc(body.selected.known_at);
    line = (
      <p className="work-request-asof" data-work-request-asof={target?.knownAt ? "historical" : "current"}>
        {target?.knownAt ? `Historical as of ${when}` : `As known at ${when}`}
      </p>
    );
  } else if (failure !== null) {
    line = <p data-work-request-unavailable>{WORK_REQUEST_UNAVAILABLE}</p>;
  }
  const fetched = page.parsed.status === "valid" && !loading;
  return (
    <div className="site-date-bar global-work-bar work-request-bar" data-global-work-bar>
      {line}
      {fetched ? (
        <button className="button" type="button" onClick={page.reload} data-work-request-reload>
          Reload
        </button>
      ) : null}
    </div>
  );
}

function RequestRefusal({ failure }: { failure: WorkRequestFailure }) {
  const code: GlobalWorkDetailRefusalCode = failure.kind === "no-site" ? "WORK_CASE_NOT_FOUND" : failure.code;
  const hook = failure.kind === "no-site" ? "NO_SITE" : failure.code;
  return (
    <div className="notice v69-notice global-work-state" data-global-work-refusal={hook} data-page-refusal={hook}>
      <p>{GLOBAL_WORK_DETAIL_REFUSAL_COPY[code]}</p>
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
  const assignee = last?.payload.assignee;
  return typeof assignee === "string" && assignee !== "" ? assignee : NOT_ASSIGNED;
}

function SourceLink({ link }: { link: GlobalWorkLink }) {
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
 * Finding without lineage is plain text with `Link unavailable at this cutoff`; neither is `Not recorded`.
 */
function sourceOf(body: GlobalWorkDetailBody): { node: ReactNode; text: string } {
  const links = [...(body.links.source_incident ? [body.links.source_incident] : []), ...body.links.findings];
  if (links.length === 0) return { node: NOT_RECORDED, text: NOT_RECORDED };
  return {
    node: joined(
      links.map((link, index) => <SourceLink key={`${link.label}-${index}`} link={link} />),
      " · ",
    ),
    text: links.map((link) => (link.href ? link.label : `${link.label} · ${LINK_UNAVAILABLE_AT_CUTOFF}`)).join(" · "),
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
function WorkRequestMHeader({ body }: { body: GlobalWorkDetailBody }) {
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
 * mheader, then the page's panels (`children` receives the loaded body or null; panels keep their slots).
 */
export function WorkRequestFrame({
  client,
  rootClass,
  tab = "overview",
  children,
}: {
  client?: GlobalWorkClient;
  rootClass: string;
  /** The current mounted tab; Overview when omitted (C2's page passes none). */
  tab?: WorkRequestTab;
  children: (body: GlobalWorkDetailBody | null) => ReactNode;
}) {
  const page = useWorkRequest(client);
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
        {failure !== null ? <RequestRefusal failure={failure} /> : null}
        {body !== null ? <WorkRequestMHeader body={body} /> : null}
        {children(body)}
      </div>
    </main>
  );
}

/** Re-exported for the page modules: the shared clamp keeps cell text bounded. */
export { Clamp };
