/**
 * IA-P P2 (spec §5.2, D-IAP.6): the pure model of a home list, IA-2b rev 2 §3.1 transcribed. The address is the view:
 * `homeListModel(def, items, q, scope)` turns the items and the address's parameters into rows, and `homeListHref` writes
 * the canonical address back. Nothing here reads a store, a date or a word of a list's own; the defs supply them.
 */

/** IA-2b D-IA.80: one cap per list. */
export const HOME_LIST_CAP = 10;

export interface ListOption {
  value: string;
  word: string;
}

export interface ListFacet<T> {
  key: string;
  label: string;
  options: readonly ListOption[];
  /** The way out: the word of "no value" ("All states"). */
  all: string;
  /** The item's value; a list when the item holds several (a Finding in more than one lens). */
  of(item: T): string | readonly string[] | null;
}

export interface ListSort<T> {
  key: string;
  label: string;
  /** Absent: the store's own order (the server's priority). */
  compare?: (a: T, b: T) => number;
}

export interface ListDefModel<T> {
  key: string;
  plural: string;
  facets: readonly ListFacet<T>[];
  /** The first sort is the default. */
  sorts: readonly ListSort<T>[];
  /** The row's rendered text, for search. */
  text(item: T): string;
  /** The row's Site code, for scope. A list without it ignores the scope. */
  site?(item: T): string;
  /** The row's domain, for a `group:` scope. */
  domain?(item: T): string | null;
  /** Kept inside the cap (shown before the rest). */
  keep?(item: T): boolean;
  group?(item: T): string;
}

export type ListQuery = Readonly<Record<string, string | null | undefined>>;

export interface HomeListModel<T> {
  rows: T[];
  shown: T[];
  hidden: T[];
  /** The rows after filters, before the cap. */
  n: number;
  /** The items in scope. */
  ns: number;
  tier: 0 | 1 | 2;
  groups: { g: string; n_g: number }[];
}

export function listTier(ns: number): 0 | 1 | 2 {
  return ns < 3 ? 0 : ns <= 10 ? 1 : 2;
}

function words(value: string | null | undefined): string[] {
  return (value ?? "").trim().toLowerCase().split(/\s+/).filter((w) => w !== "");
}

function plain(text: string): string {
  return text.replace(/<[^>]*>/g, "").toLowerCase();
}

function inScope<T>(def: ListDefModel<T>, item: T, scope: string): boolean {
  if (scope === "all" || def.site === undefined) return true;
  if (scope.startsWith("site:")) return def.site(item) === scope.slice(5);
  if (scope.startsWith("group:")) return def.domain !== undefined && def.domain(item) === scope.slice(6);
  return true;
}

/** The option's value when the address's value is one of the facet's options, else null (an invalid value is ignored). */
export function facetValue<T>(facet: ListFacet<T>, q: ListQuery): string | null {
  const value = q[facet.key];
  return value !== undefined && value !== null && facet.options.some((o) => o.value === value) ? value : null;
}

export function homeListModel<T>(
  def: ListDefModel<T>,
  items: readonly T[],
  q: ListQuery,
  scope: string = "all",
  cap: number = HOME_LIST_CAP,
): HomeListModel<T> {
  const scoped = items.filter((item) => inScope(def, item, scope));
  const ns = scoped.length;
  let rows = scoped;
  for (const facet of def.facets) {
    const value = facetValue(facet, q);
    if (value !== null) {
      rows = rows.filter((item) => {
        const of = facet.of(item);
        return Array.isArray(of) ? of.includes(value) : of === value;
      });
    }
  }
  const terms = words(q.q);
  if (terms.length > 0) {
    rows = rows.filter((item) => {
      const text = plain(def.text(item));
      return terms.every((term) => text.includes(term));
    });
  }
  const sort = def.sorts.find((s) => s.key === q.sort) ?? def.sorts[0];
  const compare = sort?.compare;
  // Array.prototype.sort is stable: ties stay in store order.
  const sorted = compare === undefined ? [...rows] : [...rows].sort(compare);
  const n = sorted.length;
  let shown: T[];
  let hidden: T[];
  if (q.show === "all" || n <= cap) {
    shown = sorted;
    hidden = [];
  } else {
    const kept = def.keep === undefined ? [] : sorted.filter((item) => def.keep!(item));
    const rest = def.keep === undefined ? sorted : sorted.filter((item) => !def.keep!(item));
    const take = new Set<T>([...kept, ...rest].slice(0, cap));
    shown = sorted.filter((item) => take.has(item));
    hidden = sorted.filter((item) => !take.has(item));
  }
  let groups: { g: string; n_g: number }[] = [];
  if (def.group !== undefined && n > HOME_LIST_CAP) {
    const counts = new Map<string, number>();
    for (const item of sorted) counts.set(def.group(item), (counts.get(def.group(item)) ?? 0) + 1);
    if (counts.size > 1) {
      groups = [...counts].map(([g, n_g]) => ({ g, n_g }));
      const order = new Map(groups.map((g, i) => [g.g, i]));
      shown = shown
        .map((item, i) => ({ item, i, o: order.get(def.group!(item)) ?? 0 }))
        .sort((a, b) => a.o - b.o || a.i - b.i)
        .map((x) => x.item);
    }
  }
  return { rows: sorted, shown, hidden, n, ns, tier: listTier(ns), groups };
}

const RANGE_KEYS = ["from", "to", "known_at"] as const;

/**
 * The canonical address of a list: the shared range untouched, then `scope`, the facets in def order, `sort`, `q` and
 * `show=all`, each only when it is not its default. `change` overrides; a facet, scope or search change drops `show`.
 */
export function homeListHref<T>(
  def: ListDefModel<T>,
  path: string,
  params: URLSearchParams,
  change: Readonly<Record<string, string | null | undefined>> = {},
): string {
  const value = (key: string): string | null => {
    if (key in change) return change[key] ?? null;
    return params.get(key);
  };
  const out = new URLSearchParams();
  for (const key of RANGE_KEYS) {
    const v = params.get(key);
    if (v !== null && v !== "") out.set(key, v);
  }
  const scope = value("scope");
  if (scope !== null && scope !== "" && scope !== "all") out.set("scope", scope);
  for (const facet of def.facets) {
    const v = facetValue(facet, { [facet.key]: value(facet.key) });
    if (v !== null) out.set(facet.key, v);
  }
  const sort = value("sort");
  if (sort !== null && def.sorts.some((s, i) => i > 0 && s.key === sort)) out.set("sort", sort);
  const text = (value("q") ?? "").trim();
  if (text !== "") out.set("q", text);
  const dropsShow = ["scope", "q", ...def.facets.map((f) => f.key)].some((k) => k in change);
  const show = "show" in change ? change.show : dropsShow ? null : params.get("show");
  if (show === "all") out.set("show", "all");
  const query = out.toString();
  return query === "" ? path : `${path}?${query}`;
}
