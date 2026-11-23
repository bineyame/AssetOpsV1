/**
 * IA-P P7 (spec §6 P7 "Scope"; IA-1 §2.3 item 1; IA-2b §3.3; D-IAP.40 Q23 to Q24): the top bar's scope switch.
 *
 * - The button reads "All sites ▾", "{domain word} ▾" or "{Site name} ▾", from the address's `scope`.
 * - The menu lists "All sites", one entry per domain present (the directory's `site_type` through `DOMAIN_WORD`, in its
 *   order), then the Sites in directory order. The directory is read when the menu opens, or when a Site is the scope
 *   (its name is the button's word); no other page pays a read.
 * - On a list (`HomeList`'s own address) an entry writes `scope=` and keeps every other parameter (facets, sort, `q`,
 *   the range); `show` goes, as `homeListHref` drops it on a scope change. On a Site page or a hub, a Site entry opens
 *   `/sites/{code}` with the range, and a group or all writes `scope=` (all removes it) on the same address.
 * - `EverySiteChip` (MD-IAP-5; D-IAP.40, D-IAP.50): every operator page that is neither a `HomeList` list nor a Site page
 *   says "This page shows every Site" while the scope is not all: the Overview, Demand & capacity, Outcomes (above L1;
 *   L2 follows the scope), Results, Evidence & records, Incidents, Maintenance and Financials. Site pages keep the
 *   parameter and show nothing more.
 */
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { DOMAIN_WORD } from "../estate/portfolioWords";
import { useProvidedSiteDirectory } from "../estate/estateReadCache";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";
import type { SiteSummary } from "../sites/siteReadModel";
import { withRange } from "../ui/sharedRange";
import "./scopeSearch.css";

export const ALL_SITES = "All sites";
export const EVERY_SITE_CHIP = "This page shows every Site";
export const SCOPE_MENU_LABEL = "Scope";

/** The addresses of the lists drawn by `HomeList`, where a Site entry scopes the list. */
const LIST_PATHS = /^\/(?:decisions|findings|actions|sites)\/?$/;
/** A Site page: it keeps the scope parameter and says nothing more (D-IAP.40). */
const SITE_PAGES = /^\/sites\/[^/]/;

export interface ScopeEntry {
  word: string;
  /** `all`, `group:{DOMAIN}` or `site:{code}`. */
  scope: string;
}

/** "All sites", each domain present in `DOMAIN_WORD` order, then the Sites in directory order. */
export function scopeEntries(sites: readonly SiteSummary[]): ScopeEntry[] {
  const present = new Set(sites.map((s) => s.site_type));
  const domains = (Object.keys(DOMAIN_WORD) as (keyof typeof DOMAIN_WORD)[]).filter((d) => present.has(d));
  return [
    { word: ALL_SITES, scope: "all" },
    ...domains.map((d) => ({ word: DOMAIN_WORD[d], scope: `group:${d}` })),
    ...sites.map((s) => ({ word: s.display_name, scope: `site:${s.site_id}` })),
  ];
}

/** The button's word for a scope; a Site not (yet) in the directory reads its code. */
export function scopeWord(scope: string, sites: readonly SiteSummary[]): string {
  if (scope.startsWith("group:")) return (DOMAIN_WORD as Record<string, string>)[scope.slice(6)] ?? scope.slice(6);
  if (scope.startsWith("site:")) {
    const code = scope.slice(5);
    return sites.find((s) => s.site_id.toLowerCase() === code.toLowerCase())?.display_name ?? code;
  }
  return ALL_SITES;
}

/** Where an entry goes from `pathname` (spec §6 P7). */
export function scopeTarget(entry: ScopeEntry, pathname: string, params: URLSearchParams): string {
  if (entry.scope.startsWith("site:") && !LIST_PATHS.test(pathname)) {
    return withRange(`/sites/${encodeURIComponent(entry.scope.slice(5))}`, params);
  }
  const next = new URLSearchParams(params);
  next.delete("show");
  if (entry.scope === "all") next.delete("scope");
  else next.set("scope", entry.scope);
  const query = next.toString();
  return query === "" ? pathname : `${pathname}?${query}`;
}

/** The directory, read once `on` turns true; empty until it loads (a refusal leaves it empty). */
export function useDirectoryWhen(on: boolean, directory: SiteDirectoryClient | null): readonly SiteSummary[] {
  const [sites, setSites] = useState<readonly SiteSummary[] | null>(null);
  const asked = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    if (!on || asked.current || directory === null) return;
    asked.current = true;
    void directory.listSites().then((r) => {
      if (mounted.current) setSites(r.status === "loaded" ? r.sites : []);
    });
  }, [on, directory]);
  return sites ?? [];
}

export function ScopeSwitch({ directory }: { directory?: SiteDirectoryClient }) {
  const provided = useProvidedSiteDirectory();
  const [params] = useSearchParams();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const scope = params.get("scope") ?? "all";
  const [open, setOpen] = useState(false);
  const sites = useDirectoryWhen(open || scope.startsWith("site:"), directory ?? provided);
  const button = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLUListElement>(null);
  const entries = scopeEntries(sites);

  useEffect(() => {
    if (!open) return undefined;
    menu.current?.querySelector<HTMLElement>('[role="menuitem"]')?.focus();
    const outside = (event: MouseEvent) => {
      const root = button.current?.parentElement;
      if (root && !root.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", outside);
    return () => document.removeEventListener("mousedown", outside);
  }, [open, entries.length]);

  function close() {
    setOpen(false);
    button.current?.focus();
  }

  function onMenuKey(event: KeyboardEvent<HTMLUListElement>) {
    const items = [...(menu.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [])];
    const at = items.indexOf(document.activeElement as HTMLElement);
    if (event.key === "Escape") {
      event.preventDefault();
      close();
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      items[(at + step + items.length) % items.length]?.focus();
    } else if (event.key === "Tab") {
      setOpen(false);
    }
  }

  return (
    <div className="ia-scope" data-scope-switch>
      <button
        ref={button}
        type="button"
        className="ia-scope__button"
        data-shell-control
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`${SCOPE_MENU_LABEL}: ${scopeWord(scope, sites)}`}
        onClick={() => setOpen((o) => !o)}
      >
        {`${scopeWord(scope, sites)} ▾`}
      </button>
      {open ? (
        <ul ref={menu} className="ia-scope__menu" role="menu" aria-label={SCOPE_MENU_LABEL} onKeyDown={onMenuKey}>
          {entries.map((entry, i) => {
            const kind = entry.scope === "all" ? "all" : entry.scope.startsWith("group:") ? "group" : "site";
            const firstSite = kind === "site" && (i === 0 || !entries[i - 1].scope.startsWith("site:"));
            return (
              <li key={entry.scope} role="none" className={firstSite || (kind === "group" && i === 1) ? "ia-scope__split" : undefined}>
                <button
                  type="button"
                  role="menuitem"
                  tabIndex={-1}
                  aria-current={entry.scope === scope ? "true" : undefined}
                  onClick={() => {
                    setOpen(false);
                    navigate(scopeTarget(entry, pathname, params));
                  }}
                >
                  {entry.word}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

/** MD-IAP-5 (D-IAP.40): the one chip on the pages whose reads have no scope, while the scope is not all. */
export function EverySiteChip() {
  const [params] = useSearchParams();
  const { pathname } = useLocation();
  const scope = params.get("scope");
  if (scope === null || scope === "" || scope === "all" || LIST_PATHS.test(pathname) || SITE_PAGES.test(pathname)) return null;
  return (
    <p className="ia-every-site" role="note" data-every-site-chip>
      <span className="ia-every-site__chip">{EVERY_SITE_CHIP}</span>
    </p>
  );
}
