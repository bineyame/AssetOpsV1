/**
 * IA-P P2 (spec §4.1, D-IAP.17): the shared read cache of the estate lists. One promise per
 * `(client, read, from, to, known_at)`, every page of it (`loadAllPages`), so the Decisions list, the Findings list's
 * "Its decision" column, the inbox and search do not read twice. The cache is a React context mounted in
 * `OperatorShellLayout` and dropped when the range changes. Without a provider (a page under a bare test router) a hook
 * keeps its own.
 */
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";

import {
  FIRST_PAGE_CODES,
  type EstateActionsBody,
  type EstateClient,
  type EstateFindingsBody,
  type EstatePortfolioBody,
  type EstateQuery,
  type EstateResult,
} from "./estateClient";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";

/** The page size and the page count `loadAllPages` follows (spec §4.1: 20 pages of 50 are 1,000 rows). */
export const ALL_PAGES_LIMIT = 50;
export const ALL_PAGES_MAX = 20;
export const TRUNCATED_LINE = "Showing the first 1,000. Narrow the date range to see the rest.";

export interface AllPages<B, R> {
  /** Page one's body: the body-level fields (summary, coverage, total_count) are its, only `rows` are concatenated. */
  first: B;
  rows: R[];
  /** More rows remain after the page cap. */
  truncated: boolean;
}

export type AllPagesResult<B, R> = EstateResult<AllPages<B, R>>;

interface Paged<R> {
  rows: R[];
  next_cursor: string | null;
}

/**
 * Follows `next_cursor` up to `ALL_PAGES_MAX` pages. A later page refused with a first-page code (`ESTATE_BASIS_CHANGED`,
 * `INVALID_CURSOR`) restarts once from page one (I9); a second refusal is the result.
 */
export async function loadAllPages<B extends Paged<R>, R>(
  page: (cursor: string | null) => Promise<EstateResult<B>>,
): Promise<AllPagesResult<B, R>> {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const first = await page(null);
    if (first.status !== "loaded") return first;
    const rows = [...first.value.rows];
    let cursor = first.value.next_cursor;
    let pages = 1;
    let restart = false;
    while (cursor !== null && pages < ALL_PAGES_MAX) {
      const next = await page(cursor);
      if (next.status !== "loaded") {
        if (FIRST_PAGE_CODES.has(next.code) && attempt === 0) {
          restart = true;
          break;
        }
        return next;
      }
      rows.push(...next.value.rows);
      cursor = next.value.next_cursor;
      pages += 1;
    }
    if (restart) continue;
    return { status: "loaded", value: { first: first.value, rows, truncated: cursor !== null } };
  }
  /* c8 ignore next */
  throw new Error("unreachable");
}

export type EstateReadKind = "portfolio" | "findings" | "actions";
type Range = Pick<EstateQuery, "from" | "to" | "known_at">;

type ReadBody = {
  portfolio: EstatePortfolioBody;
  findings: EstateFindingsBody;
  actions: EstateActionsBody;
};
type ReadRow<K extends EstateReadKind> = ReadBody[K] extends { rows: (infer R)[] } ? R : never;

/** The read of one kind for a range, every page of it. */
export function readAll<K extends EstateReadKind>(client: EstateClient, kind: K, range: Range): Promise<AllPagesResult<ReadBody[K], ReadRow<K>>> {
  const base = { from: range.from, to: range.to, known_at: range.known_at, limit: ALL_PAGES_LIMIT };
  const run = (cursor: string | null): Promise<EstateResult<unknown>> =>
    kind === "portfolio"
      ? client.portfolio({ ...base, lens: "all", cursor })
      : kind === "findings"
        ? client.findings({ ...base, lens: "all", state: "all", cursor })
        : client.actions({ ...base, cursor });
  return loadAllPages(run as never) as never;
}

export interface EstateReadCache {
  get<K extends EstateReadKind>(client: EstateClient, kind: K, range: Range): Promise<AllPagesResult<ReadBody[K], ReadRow<K>>>;
}

const clientIds = new WeakMap<object, number>();
let nextClientId = 0;
function clientId(client: object): number {
  let id = clientIds.get(client);
  if (id === undefined) {
    id = nextClientId;
    nextClientId += 1;
    clientIds.set(client, id);
  }
  return id;
}

export function createEstateReadCache(): EstateReadCache {
  let rangeKey = "";
  let map = new Map<string, Promise<unknown>>();
  return {
    get(client, kind, range) {
      const next = `${range.from}|${range.to}|${range.known_at ?? ""}`;
      // The range changed: every held read is dropped.
      if (next !== rangeKey) {
        rangeKey = next;
        map = new Map();
      }
      const key = `${clientId(client)}|${kind}`;
      let held = map.get(key);
      if (held === undefined) {
        const read = readAll(client, kind, range);
        held = read;
        map.set(key, read);
        // A refusal is not kept: the next ask (a retry, another page) reads again.
        void read.then((result) => {
          if (result.status !== "loaded" && map.get(key) === read) map.delete(key);
        });
      }
      return held as never;
    },
  };
}

const CacheContext = createContext<EstateReadCache | null>(null);

/**
 * IA-P P6 (D-IAP.37 Q12): the app's estate client, so the shell's "Waiting for you" reads on the Decisions read's
 * cache key (the same client object, so no second read). `App` provides the client its routes get.
 */
const ClientContext = createContext<EstateClient | null>(null);
/** IA-P P7: the app's Site directory, for the shell's scope menu and search (read only when either opens). */
const DirectoryContext = createContext<SiteDirectoryClient | null>(null);

export function EstateClientProvider({ client, directory, children }: { client: EstateClient; directory?: SiteDirectoryClient; children: ReactNode }) {
  return (
    <ClientContext.Provider value={client}>
      <DirectoryContext.Provider value={directory ?? null}>{children}</DirectoryContext.Provider>
    </ClientContext.Provider>
  );
}

export function useProvidedEstateClient(): EstateClient | null {
  return useContext(ClientContext);
}

export function useProvidedSiteDirectory(): SiteDirectoryClient | null {
  return useContext(DirectoryContext);
}

export function EstateReadCacheProvider({ children }: { children: ReactNode }) {
  const cache = useRef<EstateReadCache | null>(null);
  if (cache.current === null) cache.current = createEstateReadCache();
  return <CacheContext.Provider value={cache.current}>{children}</CacheContext.Provider>;
}

/**
 * One read of every page for a range: `null` while it is in flight, then the result. A retry (a refusal's second
 * attempt) is a change of `attempt`.
 */
export function useEstateRead<K extends EstateReadKind>(
  client: EstateClient,
  kind: K,
  range: Range,
): AllPagesResult<ReadBody[K], ReadRow<K>> | null {
  const provided = useContext(CacheContext);
  const own = useRef<EstateReadCache | null>(null);
  if (provided === null && own.current === null) own.current = createEstateReadCache();
  const cache = provided ?? own.current!;
  const key = `${clientId(client)}|${kind}|${range.from}|${range.to}|${range.known_at ?? ""}`;
  const [state, setState] = useState<{ key: string; result: AllPagesResult<ReadBody[K], ReadRow<K>> } | null>(null);
  useEffect(() => {
    let live = true;
    void cache.get(client, kind, range).then((result) => {
      if (live) setState({ key, result });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cache, key]);
  return state?.key === key ? state.result : null;
}
