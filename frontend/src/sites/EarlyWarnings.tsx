import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable } from "../ui";
import { ExplainerDialog, ISSUE_KIND } from "./OutcomeBoard";
import type { OutcomeBoardClient, OutcomeBoardQuery, OutcomeBoardRead, OutcomeWarning } from "./outcomeBoardClient";
import "./outcomes.css";

/**
 * OUT-C U5: "Early warnings · not priced yet", the warning list of the v7.0 mock (`outcomes.js:137-140`
 * `warningList`). Every text on an item is backend data (sheet §3, §4); the frontend adds only the heading, the
 * badge labels of the board's issue kinds and the explainer prose. A warning never carries money.
 */
export const WARNINGS_TITLE = "Early warnings · not priced yet";
export const WARNINGS_EXPLAIN_TITLE = "Early warnings";
export const WARNINGS_EXPLAIN =
  "An early warning points at something that tends to cost money or shorten equipment life, before its cost can be worked out. It shows what was seen and how often. It never shows a money figure.";

/** Label of the first MOVES category item (the outcome category the warning moves), or null. */
export function warningCategoryLabel(warning: OutcomeWarning): string | null {
  const item = (warning.categories?.items ?? []).find((i) => i.role === "MOVES");
  return item?.label ?? null;
}

function To({ href, children }: { href: string | null; children: ReactNode }) {
  return href ? <Link to={href}>{children}</Link> : <>{children}</>;
}

function badgeOf(warning: OutcomeWarning): [string, string] {
  return ISSUE_KIND[warning.badge] ?? [warning.badge_label, ""];
}

export function EarlyWarningList({
  warnings,
  max,
  showSite,
}: {
  warnings: readonly OutcomeWarning[];
  max?: number;
  showSite: boolean;
}) {
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const rows = warnings.slice(0, max ?? warnings.length);
  if (rows.length === 0) return null;
  return (
    <div className="oc-warn" data-early-warnings>
      <div className="oc-warn-head">
        <h3>{WARNINGS_TITLE}</h3>
        <button type="button" ref={opener} className="oc-info" aria-label="About early warnings" onClick={() => setOpen(true)}>
          i
        </button>
      </div>
      <ul>
        {rows.map((w) => {
          const [label, cls] = badgeOf(w);
          const small = [showSite ? w.site_name.split(" ")[0] : null, warningCategoryLabel(w), w.seen]
            .filter(Boolean)
            .join(" · ");
          return (
            <li key={`${w.site_code}|${w.key}`} data-warning-key={w.key}>
              <span className={`oc-kind ${cls}`.trim()}>{label}</span>
              <div>
                <To href={w.href}>
                  <strong>{w.title}</strong>
                </To>
                <small>{small}</small>
              </div>
            </li>
          );
        })}
      </ul>
      {open ? (
        <ExplainerDialog
          title={WARNINGS_EXPLAIN_TITLE}
          titleId={titleId}
          opener={opener.current}
          onClose={() => setOpen(false)}
          marker="data-warnings-explainer"
        >
          <p className="prose">{WARNINGS_EXPLAIN}</p>
          <div className="ob-dialog-table">
            <DataTable>
              <thead>
                <tr>
                  <th scope="col">Warning</th>
                  <th scope="col">Outcome</th>
                  <th scope="col">What would put a value on it</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((w) => (
                  <tr key={`${w.site_code}|${w.key}`}>
                    <td>{w.title}</td>
                    <td>{warningCategoryLabel(w)}</td>
                    <td>{w.price_needs}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </div>
        </ExplainerDialog>
      ) : null}
    </div>
  );
}

/**
 * The mini board day for a Findings window (`read.py` `mini_summary_day`): the UTC day of `to`, the previous day when
 * `to` is midnight. Null when `to` is not an instant.
 */
export function miniBoardDay(to: string | null | undefined): string | null {
  if (!to) return null;
  const at = new Date(to);
  if (Number.isNaN(at.getTime())) return null;
  const midnight = at.getUTCHours() === 0 && at.getUTCMinutes() === 0 && at.getUTCSeconds() === 0 && at.getUTCMilliseconds() === 0;
  if (midnight) at.setUTCDate(at.getUTCDate() - 1);
  return at.toISOString().slice(0, 10);
}

/** OUT-C U5: a Site Findings list's warnings, read from the Site board; nothing while loading, refused or empty. */
export function SiteEarlyWarnings({
  client,
  siteCode,
  query,
}: {
  client: OutcomeBoardClient;
  siteCode: string;
  query: OutcomeBoardQuery;
}) {
  const key = `${siteCode}|${query.date ?? ""}|${query.from ?? ""}|${query.to ?? ""}|${query.known_at ?? ""}`;
  const [read, setRead] = useState<{ key: string; read: OutcomeBoardRead } | null>(null);
  useEffect(() => {
    let live = true;
    void client
      .getOutcomeBoard(siteCode, query)
      .then((r) => {
        if (live) setRead({ key, read: r });
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, key]);
  const current = read?.key === key ? read.read : null;
  if (current?.status !== "loaded") return null;
  return <EarlyWarningList warnings={current.value.warnings ?? []} showSite={false} />;
}
