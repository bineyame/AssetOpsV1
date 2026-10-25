/**
 * W6-01b B2 (`.agent/W6-01-build-spec.md` "B1-B3 pre-flight rulings" P-B2-1): the global work list parts shared by
 * the Incidents (A2), Maintenance (B2), Preventive (B3) and Operational records (E2) roots, extracted from the A2
 * page without changing its DOM, `data-*` hooks, copy, URLs or behaviour: the trail, the three-line clamp, the
 * link-or-text cell, the A2Q6 refusal block, the control bar, the status line, the A2Q10 pager, the A2Q4 work
 * provenance line and the page read hook. Root-specific accessible names are parameters.
 *
 * W6-01e E2 (P-E2-1/2): the page query may carry `kind` on Operational records only. The hook takes an
 * operational-only kind validator; with it, an invalid or repeated `kind` is a no-fetch `INVALID_KIND` refusal, and a
 * valid kind rides through Show, Reload, the first-page link and the pager. Without it the other roots ignore `kind`.
 */
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import {
  GLOBAL_WORK_FIRST_PAGE_CODES,
  GLOBAL_WORK_PAGE_LIMIT,
  GLOBAL_WORK_REFUSAL_COPY,
  createGlobalWorkClient,
  findingLinkSelectsRevision,
  globalWorkHref,
  globalWorkPageQuery,
  globalWorkUtc,
  globalWorkUtcSeconds,
  type GlobalOperationalKind,
  type GlobalSiteDomain,
  type GlobalWorkClient,
  type GlobalWorkLink,
  type GlobalWorkPageQuery,
  type GlobalWorkProvenance,
  type GlobalWorkQuery,
  type GlobalWorkRefusalCode,
  type GlobalWorkResult,
  type GlobalWorkStatus,
} from "./globalWorkClient";

export const NO_ACCESSIBLE_SITES = "No accessible Sites.";
export const CHANGE_WINDOW = "Change the UTC window or open a Site record.";
export const SCROLL_TABLE = "Scroll table horizontally";
/** CL3-6 / P-E2-2: the Operational records page refusal for an invalid or repeated `kind` (no fetch). */
export const CHOOSE_RECORD_TYPE = "Choose a supported record type.";

/** A page-query refusal: the window/cutoff codes, or the Operational records `INVALID_KIND` (never an API code). */
export type GlobalWorkPageRefusalCode = GlobalWorkRefusalCode | "INVALID_KIND";

/** Section 2: the four work provenance pairs, chosen by `source_provenance.classification` (A2Q4). */
export const WORK_PROVENANCE_WORDS: Readonly<Record<string, [string, string]>> = {
  AUTHORED_DEMONSTRATION: [
    "Prepared example data",
    "These authored work records were prepared for an example. They are not physical equipment readings.",
  ],
  REGISTERED_SIMULATION: [
    "Generated test data",
    "These authored work records came from a registered simulation. They are not physical equipment readings.",
  ],
  MIXED: ["Sources do not agree", "The selected links do not establish one work source. No work outcome is verified."],
  UNKNOWN: [
    "Source unverified",
    "The origin of this authored work record is not established. No work outcome is verified.",
  ],
};

/** Earlier pages' cursors (null is page one), newest last; history state `globalWorkTrail` (A2Q10). */
export type Trail = (string | null)[];

export function readTrail(state: unknown): Trail {
  const trail = (state as { globalWorkTrail?: unknown } | null)?.globalWorkTrail;
  return Array.isArray(trail) && trail.every((c) => c === null || typeof c === "string") ? (trail as Trail) : [];
}

export function Clamp({ children, data }: { children: ReactNode; data?: Record<string, string> }) {
  return (
    <div className="global-work-clamp" {...data}>
      {children}
    </div>
  );
}

export function LinkOrText({ link, data }: { link: GlobalWorkLink; data?: Record<string, string> }) {
  return link.href ? (
    <Link to={link.href} {...data}>
      {link.label}
    </Link>
  ) : (
    <span {...data}>{link.label}</span>
  );
}

export function WorkSourceLine({ provenance }: { provenance: GlobalWorkProvenance }) {
  const [label, explanation] = WORK_PROVENANCE_WORDS[provenance.classification] ?? WORK_PROVENANCE_WORDS.UNKNOWN;
  return (
    <details className="global-work-details" data-global-work-source={provenance.classification}>
      <summary>{label}</summary>
      {explanation}
    </details>
  );
}

/**
 * Post-W6 W6 Q4/Q9/Q17: the visible 12 px label of a registered mock departure, adjacent to the element it explains,
 * with the matching `data-mock-deviation` register ID. It states a departure; it never claims the mock fact.
 */
export function MockDeviation({ category, id }: { category: "D1" | "D2" | "D4"; id: string }) {
  return (
    <p className="global-work-deviation" data-mock-deviation={id}>
      {`MOCK DEVIATION ${category} (${id})`}
    </p>
  );
}

/** Post-W6 W6 Q18: the plain asset words for a stored asset type; an unlisted type keeps its stored label. */
const ASSET_WORDS: Readonly<Record<string, (code: string) => string>> = {
  EV_CONNECTOR: (code) => `EV connector ${code}`,
  GENERATOR: (code) => `Backup generator · ${code}`,
};

/** Post-W6 W6 Q18: `EV connector c1` / `Backup generator · generator-1` from the stored code and type. */
export function assetWords(code: string, type: string): string {
  const words = ASSET_WORDS[type];
  return words ? words(code) : `${code} · ${type}`;
}

/** The same words from a row's stored `code · TYPE` asset label (null when the row records no asset). */
export function assetLabelWords(label: string | null): string | null {
  if (label === null) return null;
  const at = label.lastIndexOf(" · ");
  return at < 0 ? label : assetWords(label.slice(0, at), label.slice(at + 3));
}

/** Post-W6 W6 Q18: `1 request`, `{n} requests`. */
export const requestCount = (n: number): string => `${n} ${n === 1 ? "request" : "requests"}`;

/**
 * Post-W6 W6 Q2 (R352): a cold or EV Finding is plain `Finding {id8}` (R66/R75): its domain Finding frame does not
 * select the revision, so it is never an anchor and carries no unavailable-link suffix. A mini-grid Finding keeps its
 * exact-revision link.
 */
export function findingLinks(links: GlobalWorkLink[], domain: GlobalSiteDomain): GlobalWorkLink[] {
  return findingLinkSelectsRevision(domain) ? links : links.map((link) => ({ label: link.label, href: null }));
}

export function joined(parts: ReactNode[], separator: string): ReactNode[] {
  return parts.flatMap((part, index) => (index === 0 ? [part] : [separator, part]));
}

/**
 * A2Q6: one refusal sentence, with `Reload the first page` for a changed list or a stale cursor. Post-W6 W6 Q8
 * (R361): the refusal is announced as an alert.
 */
export function RefusalBlock({ code, firstPage }: { code: GlobalWorkPageRefusalCode; firstPage: string }) {
  return (
    <div role="alert" className="notice v69-notice global-work-state" data-global-work-refusal={code} data-page-refusal={code}>
      <p>{code === "INVALID_KIND" ? CHOOSE_RECORD_TYPE : GLOBAL_WORK_REFUSAL_COPY[code]}</p>
      {code !== "INVALID_KIND" && GLOBAL_WORK_FIRST_PAGE_CODES.has(code) ? (
        <p>
          <Link to={firstPage} data-global-work-first-page>
            Reload the first page
          </Link>
        </p>
      ) : null}
    </div>
  );
}

export function dateOf(instant: string | null): string {
  return instant && /^\d{4}-\d{2}-\d{2}T/.test(instant) ? instant.slice(0, 10) : "";
}

/** The shared control bar (section 2): `From (UTC)`, `To (UTC, exclusive)`, `Show records`, `Reload`. */
export function ControlBar({
  label,
  from,
  to,
  onShow,
  onReload,
}: {
  /** The form's accessible name, e.g. `Incidents window` or `Maintenance window`. */
  label: string;
  from: string;
  to: string;
  onShow: (from: string, to: string) => void;
  onReload: () => void;
}) {
  const [first, setFirst] = useState(from);
  const [last, setLast] = useState(to);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first || !last) return;
    onShow(`${first}T00:00:00Z`, `${last}T00:00:00Z`);
  };
  return (
    <form className="global-work-controls" onSubmit={submit} data-global-work-controls aria-label={label}>
      <label className="global-work-controls__field">
        {"From (UTC) "}
        <input className="v69-chip-control" type="date" value={first} onChange={(e) => setFirst(e.target.value)} />
      </label>
      <label className="global-work-controls__field">
        {"To (UTC, exclusive) "}
        <input className="v69-chip-control" type="date" value={last} onChange={(e) => setLast(e.target.value)} />
      </label>
      <button className="button" type="submit" data-global-work-show>
        Show records
      </button>
      <button className="button" type="button" onClick={onReload} data-global-work-reload>
        Reload
      </button>
    </form>
  );
}

/** The envelope fields every page's status line, cards gate and pager read. */
export interface GlobalWorkBodyBase {
  status: GlobalWorkStatus;
  known_at: string;
  total_count: number;
  rows: unknown[];
  next_cursor: string | null;
}

/** Post-W6 W6 Q14 (R372): a historical line names its cutoff to the second; a current line keeps minutes. */
export function StatusLine({ body }: { body: GlobalWorkBodyBase }) {
  const text =
    body.status === "HISTORICAL"
      ? `Historical as of ${globalWorkUtcSeconds(body.known_at)}`
      : `As known at ${globalWorkUtc(body.known_at)}`;
  return (
    <p className="global-work-status" data-global-work-status={body.status}>
      {text}
    </p>
  );
}

export function Pager({
  label,
  body,
  trail,
  cursor,
  onPage,
}: {
  /** The pager's accessible name, e.g. `Incident pages` or `Maintenance pages`. */
  label: string;
  body: GlobalWorkBodyBase;
  trail: Trail;
  cursor: string | null;
  onPage: (cursor: string | null, trail: Trail) => void;
}) {
  const a = trail.length * GLOBAL_WORK_PAGE_LIMIT + 1;
  const b = a + body.rows.length - 1;
  // Post-W6 W6 Q6 (R354): a later page opened from its URL has no local trail, so its offset is unknown; it states
  // the page's row count without a numeric range. Previous then returns to page one.
  const unknownOffset = cursor !== null && trail.length === 0;
  const caption = unknownOffset ? `Later page · ${body.rows.length} of ${body.total_count}` : `Showing ${a}–${b} of ${body.total_count}`;
  return (
    <nav className="global-work-pager" aria-label={label} data-global-work-pager>
      <span data-global-work-showing>{caption}</span>
      {cursor !== null ? (
        <button
          type="button"
          className="link-button"
          data-global-work-previous
          onClick={() => onPage(trail.length > 0 ? trail[trail.length - 1] : null, trail.slice(0, -1))}
        >
          Previous
        </button>
      ) : null}
      {body.next_cursor !== null ? (
        <button
          type="button"
          className="link-button"
          data-global-work-next
          onClick={() => onPage(body.next_cursor, [...trail, cursor])}
        >
          Next
        </button>
      ) : null}
    </nav>
  );
}

/** The page read for one root: the validated page query, the history trail and the typed read of that query. */
export interface GlobalWorkPageRead<B extends GlobalWorkBodyBase> {
  parsed: GlobalWorkPageQuery | { status: "invalid"; code: "INVALID_KIND" };
  query: GlobalWorkQuery | null;
  /** The valid window and cutoff even when `kind` is invalid (P-E2-2: the chips preserve them), else null. */
  windowQuery: GlobalWorkQuery | null;
  trail: Trail;
  read: GlobalWorkResult<B> | null;
  body: B | null;
  /** A 200 whose status is CURRENT or HISTORICAL (A2Q1: the cards and the table render only then). */
  shown: boolean;
  firstPage: string;
  rawFrom: string | null;
  rawTo: string | null;
  go: (next: Pick<GlobalWorkQuery, "from" | "to" | "known_at" | "kind">, cursor: string | null, nextTrail: Trail) => void;
  reload: () => void;
}

/**
 * Reads the page query from the URL (section 1, A2Q10) and the root through `readRoot`, which receives the client
 * (a test may supply one). `readRoot` answering null (an optional client method that is absent) reads as
 * `WORK_STORE_UNAVAILABLE` (P-B2-2), never a throw. `kindOf` (Operational records only, P-E2-1) maps every `kind`
 * value in the URL to a stored kind, null for `all`/absent, or undefined for an invalid or repeated value.
 */
export function useGlobalWorkPage<B extends GlobalWorkBodyBase>(
  pagePath: string,
  client: GlobalWorkClient | undefined,
  readRoot: (reads: GlobalWorkClient, query: GlobalWorkQuery) => Promise<GlobalWorkResult<B>> | null,
  kindOf?: (values: string[]) => GlobalOperationalKind | null | undefined,
): GlobalWorkPageRead<B> {
  const reads = useMemo(() => client ?? createGlobalWorkClient(), [client]);
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const windowParsed = globalWorkPageQuery(params);
  const kind = kindOf === undefined ? null : kindOf(params.getAll("kind"));
  const parsed: GlobalWorkPageRead<B>["parsed"] =
    windowParsed.status === "valid" && kind === undefined ? { status: "invalid", code: "INVALID_KIND" } : windowParsed;
  const windowQuery = windowParsed.status === "valid" ? windowParsed.query : null;
  const query: GlobalWorkQuery | null =
    parsed.status === "valid" ? (kind ? { ...parsed.query, kind } : parsed.query) : null;
  const trail = readTrail(location.state);
  const key = query === null ? "" : JSON.stringify(query);
  const [nonce, setNonce] = useState(0);
  const [result, setResult] = useState<{ key: string; nonce: number; read: GlobalWorkResult<B> } | null>(null);

  useEffect(() => {
    if (query === null) return undefined;
    let live = true;
    const pending = readRoot(reads, query) ?? Promise.resolve<GlobalWorkResult<B>>({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
    void pending.then((read) => {
      if (live) setResult({ key, nonce, read });
    });
    return () => {
      live = false;
    };
    // `key` carries the whole page query; `nonce` is a Reload of the same query.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key, nonce]);

  const go = (next: Pick<GlobalWorkQuery, "from" | "to" | "known_at" | "kind">, cursor: string | null, nextTrail: Trail) =>
    navigate(globalWorkHref(pagePath, next, cursor), { state: { globalWorkTrail: nextTrail } });

  const read = query !== null && result?.key === key && result.nonce === nonce ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;
  const shown = body !== null && (body.status === "CURRENT" || body.status === "HISTORICAL");
  const firstPage = query === null ? pagePath : globalWorkHref(pagePath, query);
  return {
    parsed,
    query,
    windowQuery,
    trail,
    read,
    body,
    shown,
    firstPage,
    rawFrom: params.get("from"),
    rawTo: params.get("to"),
    go,
    reload: () => {
      if (query === null) return;
      if (query.cursor === null && trail.length === 0) setNonce((n) => n + 1);
      else go(query, null, []);
    },
  };
}

/**
 * The date-bar slot (R6): the control bar, the root's membership line (Post-W6 W6 Q7: which stored time places a row
 * in the window) and, once a body is read, the status line.
 */
export function GlobalWorkBar<B extends GlobalWorkBodyBase>({
  page,
  label,
  membership,
}: {
  page: GlobalWorkPageRead<B>;
  label: string;
  membership: string;
}) {
  const { query, rawFrom, rawTo, body } = page;
  return (
    <div className="site-date-bar global-work-bar" data-global-work-bar>
      <ControlBar
        key={`${rawFrom ?? query?.from ?? ""}|${rawTo ?? query?.to ?? ""}`}
        label={label}
        from={query ? dateOf(query.from) : dateOf(rawFrom)}
        to={query ? dateOf(query.to) : dateOf(rawTo)}
        onShow={(from, to) =>
          page.go({ from, to, known_at: query?.known_at ?? null, ...(query?.kind ? { kind: query.kind } : {}) }, null, [])
        }
        onReload={page.reload}
      />
      <p className="global-work-membership" data-global-work-membership>
        {membership}
      </p>
      {body !== null ? <StatusLine body={body} /> : null}
    </div>
  );
}

/**
 * The leading state slot above the table panel (A2Q1/A2Q6, CL3-1): the invalid-query or refusal block, the loading
 * sentence, the empty-scope statement, or the cards for a CURRENT/HISTORICAL 200. An unproduced status is stated as
 * a read failure, never shown as zero.
 */
export function GlobalWorkSlot<B extends GlobalWorkBodyBase>({
  page,
  loading,
  cards,
}: {
  page: GlobalWorkPageRead<B>;
  loading: string;
  cards: (body: B) => ReactNode;
}) {
  const { parsed, read, firstPage, shown } = page;
  if (parsed.status === "invalid") return <RefusalBlock code={parsed.code} firstPage={firstPage} />;
  if (read === null) {
    return (
      <p role="status" className="global-work-loading" data-global-work-loading>
        {loading}
      </p>
    );
  }
  if (read.status === "refused") return <RefusalBlock code={read.code} firstPage={firstPage} />;
  if (read.value.status === "EMPTY_SCOPE") {
    return (
      // `data-page-refusal` is the panel-structure test's leading-state hook; EMPTY_SCOPE is stated, never a zero.
      <div
        role="status"
        className="notice v69-notice global-work-state"
        data-global-work-empty-scope
        data-page-refusal="EMPTY_SCOPE"
      >
        <p>{NO_ACCESSIBLE_SITES}</p>
      </div>
    );
  }
  if (shown) return <>{cards(read.value)}</>;
  // A status this read never produces (PARTIAL is reserved): stated, never shown as zero.
  return <RefusalBlock code="WORK_STORE_UNAVAILABLE" firstPage={firstPage} />;
}
