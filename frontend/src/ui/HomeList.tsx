/**
 * IA-P P2 (spec §5.2, D-IAP.6): the one home list, IA-2b rev 2 §3 transcribed to React with the live tokens.
 * The address is the view: a control writes the address (`navigate`) and keeps its focus and place; a fresh mount at
 * that address draws the same list. One interactive element per row: the title link, stretched over the row.
 */
import { useLayoutEffect, useRef, type FormEvent, type ReactNode } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import "./homeList.css";
import { DataTable } from "./DataTable";
import { RangeLink as Link } from "./RangeLink";
import { facetValue, homeListHref, homeListModel, type HomeListModel, type ListDefModel } from "./homeListModel";

export interface HomeListColumn<T> {
  label: string;
  cell(item: T): ReactNode;
  /** A note under the column's heading, as `<small>` (IA-P P0/P4b: a column fed by a capped read says so). */
  note?: ReactNode;
}

export interface HomeListTile {
  label: string;
  value: ReactNode;
  /** A part of tile 1's whole (the parts sum to it), or the whole. */
  role: "total" | "part";
  note?: ReactNode;
}

export interface HomeListDef<T> extends ListDefModel<T> {
  /** The route of the list (its own address), where "View all" and every control write. */
  path: string;
  /** Tile 1's label ("Decisions"). */
  tileLabel: string;
  rowKey(item: T): string;
  title(item: T): string;
  small?(item: T): ReactNode;
  /** The row's one target; null draws the title as text with "Detail not available yet". */
  target(item: T): string | null;
  /** The first column's heading ("Decision"). */
  firstColumn: string;
  columns: readonly HomeListColumn<T>[];
  /** Tiles after the first. */
  /** `rows` are the filtered rows, so the parts sum to n; `whole` is true when nothing is filtered or scoped. */
  tiles?(model: HomeListModel<T>, rows: readonly T[], whole: boolean): HomeListTile[];
  /** A caption line under the tiles. */
  caption?(model: HomeListModel<T>, items: readonly T[]): ReactNode;
  /** The word of a scope chip. */
  scopeWord?(scope: string): string;
  groupWord?(group: string): string;
  /** IA-P P4b (MD-IAP-13): a text before "Show all", naming the rows the cap hides (never a figure the browser sums). */
  more?(hidden: readonly T[]): ReactNode;
  none: string;
}

export interface HomeListOptions {
  tools?: boolean;
  tiles?: boolean;
  /** Overrides the cap; "Show all" becomes "View all", linking to the list's own route. */
  cap?: number;
}

export const DETAIL_NOT_AVAILABLE = "Detail not available yet";

function holds(of: string | readonly string[] | null, value: string): boolean {
  return Array.isArray(of) ? of.includes(value) : of === value;
}

interface Keep {
  href: string;
  name: string;
  top: number;
}

export function HomeList<T>({
  def,
  items,
  total = null,
  options = {},
}: {
  def: HomeListDef<T>;
  items: readonly T[];
  /** The server's whole count when the read holds fewer rows (tile 1 shows it while nothing is filtered). */
  total?: number | null;
  options?: HomeListOptions;
}) {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const formRef = useRef<HTMLFormElement | null>(null);
  const keep = useRef<Keep | null>(null);
  const q: Record<string, string | null> = {};
  for (const key of ["sort", "q", "show", ...def.facets.map((f) => f.key)]) q[key] = params.get(key);
  const scope = params.get("scope") ?? "all";
  const model = homeListModel(def, items, q, scope, options.cap);
  const href = (change: Record<string, string | null> = {}) => homeListHref(def, def.path, params, change);
  const showTools = options.tools !== false;
  const showTiles = options.tiles !== false;
  const here = `${location.pathname}${location.search}`;

  // Restore: after the navigation that a control wrote, put its focus and place back (IA-2b §3.3).
  useLayoutEffect(() => {
    const k = keep.current;
    keep.current = null;
    if (k === null || k.href !== here) return;
    const el = formRef.current?.querySelector<HTMLElement>(`[name="${k.name}"]`);
    if (el === null || el === undefined) return;
    window.scrollTo({ top: window.scrollY + el.getBoundingClientRect().top - k.top, behavior: "instant" as ScrollBehavior });
    el.focus({ preventScroll: true });
  }, [here]);

  function write(name: string, value: string, el: HTMLElement) {
    const next = href({ [name]: value === "" ? null : value });
    if (next === here) return;
    keep.current = { href: next, name, top: el.getBoundingClientRect().top };
    navigate(next);
  }

  const setFacets = def.facets.filter((f) => facetValue(f, q) !== null);
  const scopedItems = items.filter((item) => homeListModel(def, [item], {}, scope).ns === 1);
  const drawn = (f: (typeof def.facets)[number]) =>
    model.tier === 2 && f.options.filter((o) => scopedItems.some((item) => holds(f.of(item), o.value))).length >= 2;
  const searchDrawn = model.tier === 2;
  const chips: { word: string; out: string; to: string }[] = [];
  if (scope !== "all") chips.push({ word: def.scopeWord?.(scope) ?? scope, out: "All sites", to: href({ scope: null }) });
  for (const f of setFacets) {
    if (drawn(f)) continue;
    const value = facetValue(f, q)!;
    chips.push({ word: f.options.find((o) => o.value === value)!.word, out: f.all, to: href({ [f.key]: null }) });
  }
  const text = (q.q ?? "").trim();
  if (text !== "" && !searchDrawn) chips.push({ word: `Matching “${text}”`, out: "Clear search", to: href({ q: null }) });
  const setCount = setFacets.length + (text !== "" ? 1 : 0);
  const clearAll = href({ ...Object.fromEntries(def.facets.map((f) => [f.key, null])), q: null });

  const whole = model.n === model.ns && setCount === 0 && scope === "all";
  const tile1 = total !== null && model.n === model.ns && setCount === 0 && total > model.n ? total : model.n;
  const tiles: HomeListTile[] = [{ label: def.tileLabel, value: tile1, role: "total" as const }, ...(def.tiles?.(model, model.rows, whole) ?? [])].slice(0, 4);
  const caption = def.caption?.(model, items) ?? null;
  const cols = def.columns.length + 1;
  const grouped = model.groups.length > 0;
  const rowOf = (item: T) => {
    const to = def.target(item);
    return (
      <tr key={def.rowKey(item)} data-row={def.rowKey(item)}>
        <th scope="row">
          {to !== null ? (
            <Link className="hl-go" to={to}>
              {def.title(item)}
            </Link>
          ) : (
            <span>{def.title(item)}</span>
          )}
          {def.small?.(item) ?? null}
          {to === null ? <small>{DETAIL_NOT_AVAILABLE}</small> : null}
        </th>
        {def.columns.map((c) => (
          <td key={c.label} data-label={c.label}>
            {c.cell(item)}
          </td>
        ))}
      </tr>
    );
  };
  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("q") as HTMLInputElement | null;
    if (input !== null) write("q", input.value, input);
  };

  return (
    <section data-shape="list" data-home-list={def.key}>
      {showTiles ? (
        <div data-level="L1">
          <div className="hl-tiles">
            {tiles.map((t, i) => (
              <div key={t.label} className="hl-tile" data-tile={i === 0 ? "total" : t.role}>
                <span className="hl-tile__label">{t.label}</span>
                <strong className="hl-tile__value">{t.value}</strong>
                {t.note !== undefined ? <small>{t.note}</small> : null}
              </div>
            ))}
          </div>
          {caption !== null ? <p className="hl-caption">{caption}</p> : null}
        </div>
      ) : null}
      <div data-level="L2">
        {chips.length > 0 ? (
          <p className="hl-chips" aria-label="In this view">
            {chips.map((c) => (
              <span key={c.out + c.word} className="hl-chip">
                {c.word} · <Link to={c.to}>{c.out}</Link>
              </span>
            ))}
            {setCount >= 2 ? <Link to={clearAll}>Clear filters</Link> : null}
          </p>
        ) : null}
        {showTools && model.tier > 0 ? (
          <form
            ref={formRef}
            className="hl-tools"
            data-home-list-tools={def.key}
            role="search"
            aria-label={`${model.tier === 2 ? "Filter and sort" : "Sort"} ${def.plural}`}
            onSubmit={onSubmit}
          >
            {def.facets.filter(drawn).map((f) => (
              <label key={f.key}>
                {f.label}{" "}
                <select name={f.key} value={facetValue(f, q) ?? ""} onChange={(e) => write(f.key, e.target.value, e.target)}>
                  <option value="">All</option>
                  {f.options.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.word}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label>
              Sort{" "}
              <select
                name="sort"
                value={def.sorts.some((s) => s.key === q.sort) ? (q.sort as string) : def.sorts[0].key}
                onChange={(e) => write("sort", e.target.value, e.target)}
              >
                {def.sorts.map((s) => (
                  <option key={s.key} value={s.key}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
            {searchDrawn ? (
              <>
                <label>
                  Search <input key={text} type="search" name="q" defaultValue={text} />
                </label>
                <button type="submit" className="button">
                  Search
                </button>
              </>
            ) : null}
          </form>
        ) : null}
        {model.n === 0 ? (
          model.ns === 0 ? (
            <p className="hl-empty" role="status">
              {def.none}
            </p>
          ) : (
            <p className="hl-empty" role="status">
              Nothing matches these filters. <Link to={clearAll}>Clear filters</Link>
            </p>
          )
        ) : (
          <DataTable tableClassName="hl-table">
            <thead>
              <tr>
                <th scope="col">{def.firstColumn}</th>
                {def.columns.map((c) => (
                  <th key={c.label} scope="col">
                    {c.label}
                    {c.note ? <small>{c.note}</small> : null}
                  </th>
                ))}
              </tr>
            </thead>
            {grouped ? (
              model.groups.map((g) => (
                <tbody key={g.g} data-group={g.g}>
                  <tr className="hl-group">
                    <th colSpan={cols} scope="rowgroup">
                      {def.groupWord?.(g.g) ?? g.g} <span className="hl-count">{g.n_g}</span>
                    </th>
                  </tr>
                  {model.shown.filter((item) => def.group!(item) === g.g).map(rowOf)}
                </tbody>
              ))
            ) : (
              <tbody>{model.shown.map(rowOf)}</tbody>
            )}
          </DataTable>
        )}
        {model.hidden.length > 0 ? (
          <p className="hl-more">
            {def.more ? <>{def.more(model.hidden)} </> : null}
            {options.cap !== undefined ? (
              <Link to={href({ show: null })}>View all {model.n}</Link>
            ) : (
              <Link to={href({ show: "all" })}>Show all {model.n}</Link>
            )}
          </p>
        ) : null}
      </div>
    </section>
  );
}
