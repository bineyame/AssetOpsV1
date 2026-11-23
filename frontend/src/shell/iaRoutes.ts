/**
 * IA-P (spec §5.1, D-IAP.4): the route registry of the IA shape in the live router's terms (IA-1 §2.2).
 *
 * - `IA_LANDED`: the IA-P units that have landed. Each unit adds its ID in its last commit.
 * - `IA_HOMES`: one entry per spec §2.4 address family: the rail item it lights (`railHomeOf`) and its tab group.
 * - `LEGACY_ROUTES`: the §2.4 aliases. An alias is live only when its unit has landed (`liveLegacyRoutes`).
 * - `LegacyRedirect` (in `LegacyRedirect.tsx`) renders the alias: `<Navigate replace>`, keeping the query.
 *
 * `iaRouteMap.test.ts` reads `App.tsx` and fails on any route path that is not a live route, a live alias, a Lab route
 * or `*` (the "no screen lost" control, D-IAP.27).
 */

import { monthDays } from "../ui/sharedRange";

export type RailLabel =
  | "Portfolio"
  | "Sites"
  | "Assets & cover"
  | "Findings"
  | "Decisions"
  | "Plan"
  | "Actions"
  | "Incidents"
  | "Maintenance"
  | "Results"
  | "Evidence & records"
  | "Financials"
  | "Settings";

export type IaTabGroup = "Portfolio" | "Evidence & records" | "Site" | null;

export const IA_LANDED = new Set<string>(["IA-P1", "IA-P2", "IA-P3"]);

export interface IaHome {
  pattern: RegExp;
  home: RailLabel | null;
  tabGroup: IaTabGroup;
}

/** The first match wins: object pages before their Site family, the Site family before the Sites index. */
export const IA_HOMES: IaHome[] = [
  { pattern: /^\/portfolio(?:\/[^/]+)?\/?$/, home: "Portfolio", tabGroup: "Portfolio" },
  // Object pages (D-IA.9): a Site Action detail lights Actions, a Site Finding detail lights Findings.
  { pattern: /^\/sites\/[^/]+\/actions\/[^/]+(?:\/.*)?$/, home: "Actions", tabGroup: null },
  { pattern: /^\/sites\/[^/]+\/findings\/[^/]+(?:\/.*)?$/, home: "Findings", tabGroup: null },
  { pattern: /^\/sites\/[^/]+(?:\/.*)?$/, home: "Sites", tabGroup: "Site" },
  { pattern: /^\/sites\/?$/, home: "Sites", tabGroup: null },
  { pattern: /^\/findings(?:\/.*)?$/, home: "Findings", tabGroup: null },
  { pattern: /^\/decisions\/?$/, home: "Decisions", tabGroup: null },
  { pattern: /^\/actions\/?$/, home: "Actions", tabGroup: null },
  { pattern: /^\/results\/?$/, home: "Results", tabGroup: null },
  { pattern: /^\/incidents\/?$/, home: "Incidents", tabGroup: null },
  { pattern: /^\/maintenance(?:\/.*)?$/, home: "Maintenance", tabGroup: null },
  { pattern: /^\/evidence(?:\/records)?\/?$/, home: "Evidence & records", tabGroup: "Evidence & records" },
  { pattern: /^\/financials\/?$/, home: "Financials", tabGroup: null },
];

/** The rail item an address lights (replaces `railActiveLabel`); `null` for an address outside every family. */
export function railHomeOf(pathname: string): RailLabel | null {
  return IA_HOMES.find((entry) => entry.pattern.test(pathname))?.home ?? null;
}

/** The tab group an address belongs to; `null` outside every group. */
export function tabGroupOf(pathname: string): IaTabGroup {
  return IA_HOMES.find((entry) => entry.pattern.test(pathname))?.tabGroup ?? null;
}

export interface LegacyRoute {
  from: string;
  to: string | ((params: Record<string, string | undefined>, search: URLSearchParams) => string);
  unit: string;
  /** The alias keeps the sub-path under `from` (`/*`). */
  prefix?: true;
}

export const LEGACY_ROUTES: LegacyRoute[] = [
  // D-IA.15: the start is the Portfolio.
  { from: "/", to: "/portfolio", unit: "IA-P1" },
  // D-IAP.5: Operational records is the Records tab of Evidence & records.
  { from: "/operational-records", to: "/evidence/records", unit: "IA-P1" },
  // D-IAP.3, D-IAP.4: Act first is the Decisions list; the Finding lens roots are the Findings list's `lens` facet.
  { from: "/portfolio/act-first", to: "/decisions", unit: "IA-P1" },
  { from: "/findings/cost", to: "/findings?lens=cost", unit: "IA-P1" },
  { from: "/findings/risks", to: "/findings?lens=risks", unit: "IA-P1" },
  { from: "/findings/opportunities", to: "/findings?lens=opportunities", unit: "IA-P1" },
  // D-IAP.18: a month is its days on the Overview; `month` is dropped and its days win over a range in the address.
  // An invalid or absent month goes to the Overview (the address's range kept).
  { from: "/portfolio/month", to: (_params, search) => monthAlias(search), unit: "IA-P2" },
  // D-IAP.4: the old Portfolio tabs' homes.
  { from: "/portfolio/opportunity", to: "/portfolio/demand-and-capacity", unit: "IA-P2" },
  { from: "/portfolio/changes", to: "/results", unit: "IA-P2" },
  { from: "/portfolio/scope", to: "/evidence", unit: "IA-P2" },
];

/**
 * The `/portfolio/month?month=YYYY-MM` alias target. `month` is removed from the search the redirect merges (so it is
 * dropped), and the month's own days (`monthDays`, the server's `month_days` twin) are the target's query, which wins.
 */
function monthAlias(search: URLSearchParams): string {
  const days = monthDays(search.get("month"));
  search.delete("month");
  return days === null ? "/portfolio" : `/portfolio?from=${days.from}&to=${days.to}`;
}

/** The aliases whose unit has landed. */
export function liveLegacyRoutes(landed: ReadonlySet<string> = IA_LANDED): LegacyRoute[] {
  return LEGACY_ROUTES.filter((route) => landed.has(route.unit));
}

/**
 * The alias target with the original search merged: the target's own query first, then the original's parameters
 * that the target does not already set (spec §5.1).
 */
export function mergeLegacySearch(target: string, original: URLSearchParams): string {
  const [pathname, query = ""] = target.split("?", 2);
  const merged = new URLSearchParams(query);
  const own = new Set(merged.keys());
  for (const [key, value] of original) {
    if (!own.has(key)) merged.append(key, value);
  }
  const search = merged.toString();
  return search === "" ? pathname : `${pathname}?${search}`;
}
