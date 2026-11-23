/**
 * IA-P P7 (spec §6 P7 "Search"; D-IAP.40 Q25): the search palette, a dialog with one input, opened by its button or by
 * Ctrl K / ⌘ K (the same keys close it; focus returns to where it was).
 *
 * - Entries: Sites (`name`, "Site", `/sites/{code}`), Decisions (`title`, "Decision · {Site}", the Decisions list's
 *   target), Findings (`title`, "Finding · {Site}", the Findings list's target), Actions (`action_title`,
 *   "Action · {owner or Site}", `link_refs.action`), then every live rail item (label, "Go to"). An entry with no live
 *   target is not indexed, as an unavailable rail item is not (plant `deadlink`).
 * - Words are ANDed, case-blind, over the label and its kind; the first `SEARCH_CAP` matches show, in that kind order.
 * - The reads are the lists' cached reads (`useEstateRead`, the same keys as the Decisions, Findings and Actions lists)
 *   and the Site directory, made only while the palette is open: a page that never opens it pays no read.
 */
import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import type { EstateActionRow, EstateClient } from "../estate/estateClient";
import { createEstateClient } from "../estate/estateClient";
import { useEstateRead, useProvidedEstateClient, useProvidedSiteDirectory } from "../estate/estateReadCache";
import { decisionItems, decisionsDef, findingItems, findingsDef, type DecisionItem, type FindingItem } from "../estate/homeLists";
import { queryFromParams } from "../estate/estateShared";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";
import type { SiteSummary } from "../sites/siteReadModel";
import type { NavRailItem } from "../ui/NavRail";
import { withRange } from "../ui/sharedRange";
import { linkFor } from "./operatorSiteRoutes";
import { useDirectoryWhen } from "./ScopeSwitch";
import "../ui/drawer.css";
import "./scopeSearch.css";

export const SEARCH_LABEL = "Search Sites, decisions and Findings";
export const SEARCH_CAP = 20;
export const SEARCH_COPY = {
  short: "Search",
  keys: "Ctrl K",
  none: "Nothing matches",
  loading: "Loading…",
} as const;

export interface SearchEntry {
  label: string;
  /** "Site", "Decision · {Site}", "Finding · {Site}", "Action · {owner or Site}" or "Go to". */
  kind: string;
  to: string;
}

export interface SearchSources {
  sites: readonly SiteSummary[];
  decisions: readonly DecisionItem[];
  findings: readonly FindingItem[];
  actions: readonly EstateActionRow[];
  rail: readonly NavRailItem[];
}

/** Every indexed entry, in kind order; only live targets. */
export function searchEntries(src: SearchSources): SearchEntry[] {
  const out: SearchEntry[] = [];
  for (const s of src.sites) out.push({ label: s.display_name, kind: "Site", to: `/sites/${encodeURIComponent(s.site_id)}` });
  const decisionTarget = decisionsDef().target;
  for (const d of src.decisions) {
    const to = decisionTarget(d);
    if (to) out.push({ label: d.row.title, kind: `Decision · ${d.row.site_name}`, to });
  }
  const findingTarget = findingsDef().target;
  for (const f of src.findings) {
    const to = findingTarget(f);
    if (to) out.push({ label: f.row.title, kind: `Finding · ${f.row.site_name}`, to });
  }
  for (const a of src.actions) {
    const to = linkFor(a.link_refs?.action);
    if (to) out.push({ label: a.action_title, kind: `Action · ${a.owner ?? a.site_name}`, to });
  }
  for (const item of src.rail) {
    if (item.kind === "live") out.push({ label: item.label, kind: "Go to", to: item.to });
  }
  return out;
}

/** Words ANDed, case-blind, over the label and its kind; the first `SEARCH_CAP`. */
export function searchMatches(entries: readonly SearchEntry[], text: string): SearchEntry[] {
  const words = text.toLowerCase().split(/\s+/).filter((w) => w !== "");
  const out: SearchEntry[] = [];
  for (const e of entries) {
    const hay = `${e.label} ${e.kind}`.toLowerCase();
    if (words.every((w) => hay.includes(w))) out.push(e);
    if (out.length === SEARCH_CAP) break;
  }
  return out;
}

export function SearchPalette({ rail, client, directory }: { rail: readonly NavRailItem[]; client?: EstateClient; directory?: SiteDirectoryClient }) {
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLElement | null>(null);
  const button = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const onKey = (event: globalThis.KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((was) => {
          if (!was) opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : button.current;
          return !was;
        });
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const wasOpen = useRef(false);
  useEffect(() => {
    if (wasOpen.current && !open) (opener.current ?? button.current)?.focus();
    wasOpen.current = open;
  }, [open]);

  return (
    <>
      <button
        ref={button}
        type="button"
        className="ia-search"
        data-shell-control
        aria-haspopup="dialog"
        aria-label={SEARCH_LABEL}
        onClick={() => {
          opener.current = button.current;
          setOpen(true);
        }}
      >
        <span className="ia-search__label" aria-hidden="true">
          {SEARCH_LABEL}
        </span>
        <span className="ia-search__short" aria-hidden="true">
          {SEARCH_COPY.short}
        </span>
        <kbd className="ia-search__keys" aria-hidden="true">
          {SEARCH_COPY.keys}
        </kbd>
      </button>
      {open ? <Palette rail={rail} client={client} directory={directory} close={() => setOpen(false)} /> : null}
    </>
  );
}

function Palette({ rail, client, directory, close }: { rail: readonly NavRailItem[]; client?: EstateClient; directory?: SiteDirectoryClient; close(): void }) {
  const providedClient = useProvidedEstateClient();
  const providedDirectory = useProvidedSiteDirectory();
  const reads = useMemo(() => client ?? providedClient ?? createEstateClient(), [client, providedClient]);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = queryFromParams(params);
  const portfolio = useEstateRead(reads, "portfolio", query);
  const findings = useEstateRead(reads, "findings", query);
  const actions = useEstateRead(reads, "actions", query);
  const sites = useDirectoryWhen(true, directory ?? providedDirectory);
  const [text, setText] = useState("");
  const [at, setAt] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const listId = useId();

  const entries = useMemo(() => {
    const p = portfolio?.status === "loaded" ? portfolio.value : null;
    const f = findings?.status === "loaded" ? findings.value : null;
    const decided = p === null ? [] : decisionItems(p.first, p.rows);
    return searchEntries({
      sites,
      decisions: decided,
      findings: f === null ? [] : findingItems(f.rows, f.first.coverage.sites, decided),
      actions: actions?.status === "loaded" ? actions.value.rows : [],
      rail,
    });
  }, [portfolio, findings, actions, sites, rail]);
  const shown = useMemo(() => searchMatches(entries, text), [entries, text]);
  const active = Math.min(at, Math.max(shown.length - 1, 0));
  const loading = portfolio === null || findings === null || actions === null;

  useEffect(() => {
    input.current?.focus();
    document.body.classList.add("dd-locked");
    return () => document.body.classList.remove("dd-locked");
  }, []);

  function go(entry: SearchEntry) {
    close();
    navigate(withRange(entry.to, params));
  }

  function onKey(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (shown.length === 0) return;
      setAt((active + (event.key === "ArrowDown" ? 1 : -1) + shown.length) % shown.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (shown[active] !== undefined) go(shown[active]);
    } else if (event.key === "Tab") {
      // One input: focus stays in the dialog.
      event.preventDefault();
    }
  }

  const optionId = (i: number) => `${listId}-o${i}`;
  return (
    <div className="ia-palette" data-search-palette>
      <div className="ia-palette__scrim" onClick={close} aria-hidden="true" />
      <div className="ia-palette__panel" role="dialog" aria-modal="true" aria-label={SEARCH_LABEL}>
        <input
          ref={input}
          className="ia-palette__input"
          type="text"
          role="combobox"
          aria-expanded="true"
          aria-controls={listId}
          aria-autocomplete="list"
          aria-label={SEARCH_LABEL}
          aria-activedescendant={shown.length > 0 ? optionId(active) : undefined}
          placeholder={SEARCH_LABEL}
          autoComplete="off"
          value={text}
          onChange={(event) => {
            setText(event.target.value);
            setAt(0);
          }}
          onKeyDown={onKey}
        />
        <ul className="ia-palette__list" id={listId} role="listbox" aria-label={SEARCH_LABEL}>
          {shown.map((entry, i) => (
            <li
              key={`${entry.kind}|${entry.to}|${entry.label}`}
              id={optionId(i)}
              role="option"
              aria-selected={i === active}
              className="ia-palette__option"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => go(entry)}
            >
              <span className="ia-palette__label">{entry.label}</span> <small className="ia-palette__kind">{entry.kind}</small>
            </li>
          ))}
        </ul>
        {shown.length === 0 ? <p className="ia-palette__empty">{loading ? SEARCH_COPY.loading : SEARCH_COPY.none}</p> : null}
      </div>
    </div>
  );
}
