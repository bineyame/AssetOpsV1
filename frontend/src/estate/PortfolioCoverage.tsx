/**
 * PF-C (architect proposal 2026-11-10 §4 PF-C1, v71 `portfolio-tabs.html` `.pf-coverage`; owner walkthrough
 * 2026-11-10 items 2-3): the Portfolio's evidence coverage, shown ONCE for the whole screen, above the section tabs,
 * so it qualifies every number on every tab. The line is server text (`summary.coverage_line`, built from the same
 * day grades the cards count); the browser only adds each Site's incomplete days from the estate coverage, in the
 * D-E5.46 short words. It replaces the header row's per-Site notes (R620) and the days line under every card.
 *
 * MOCK DEVIATION MD-PFC-1: v71 names the partial day inside each Site clause ("Kobo: 6 Oct partial readings"); the
 * server's day grades are counts, so a clause reads "Kobo: complete readings on 6 of 7 days · 1 with partial
 * readings", and the named days come from the estate gaps ("4 Nov: no readings").
 * MOCK DEVIATION MD-PFC-2: v71's `aria-label="Days checked"` becomes "Readings coverage" (owner item 3: no
 * "checked" for data).
 */
import { RangeLink as Link } from "../ui/RangeLink";
import { Disclosure } from "../ui";
import type { EstateCoverageDays, EstateCoverageLine } from "./estateClient";
import { gapReasonClause, incompleteSites, READINGS_GLOSSARY_NOTE, READINGS_TERMS } from "./portfolioWords";

export const COVERAGE_LINK = "Which days, and why →";
export const COVERAGE_GLOSSARY = "What these words mean";
export const COVERAGE_LOADING = "Day readings are not known yet";

export interface PartialSite {
  site_code: string;
  site_name: string;
  days: EstateCoverageDays | null | undefined;
}

/** One clause per Site: the server's readings words, then that Site's incomplete days (estate gaps), if any. */
export function coverageClauses(line: EstateCoverageLine | null, partial: PartialSite[]): string[] {
  const gaps = new Map(partial.map((p) => [p.site_code, gapReasonClause(p.days)]));
  const clauses = (line?.sites ?? []).map((s) => {
    const gap = gaps.get(s.site_code);
    gaps.delete(s.site_code);
    return gap ? `${s.text} · ${gap}` : s.text;
  });
  // A Site the server line does not name still states its incomplete days.
  for (const p of partial) if (gaps.get(p.site_code)) clauses.push(`${p.site_name}: ${gaps.get(p.site_code)}`);
  return clauses;
}

export function PortfolioCoverage({
  line,
  partial,
  scopeHref,
}: {
  line: EstateCoverageLine | null;
  partial: PartialSite[];
  scopeHref: string;
}) {
  const complete = line?.state === "COMPLETE" && partial.length === 0;
  const lead: string[] = [];
  if (line === null) lead.push(COVERAGE_LOADING);
  else if (line.state !== "COMPLETE" || partial.length === 0) lead.push(line.lead);
  if (partial.length > 0) lead.push(incompleteSites(partial.length));
  const clauses = complete ? [] : coverageClauses(line, partial);
  return (
    <div
      className={`pf-coverage${complete ? " pf-coverage--complete" : ""}`}
      role="note"
      aria-label="Readings coverage"
      data-portfolio-coverage={line === null ? "LOADING" : complete ? "COMPLETE" : line.state === "NOT_KNOWN" ? "NOT_KNOWN" : "INCOMPLETE"}
    >
      <span className="dot" aria-hidden="true"></span>
      <b data-portfolio-coverage-lead>{lead.join(" · ")}</b>
      {clauses.length > 0 ? (
        <span className="sites">
          {clauses.map((c) => (
            <span key={c} data-portfolio-coverage-site>
              {c}
            </span>
          ))}
        </span>
      ) : null}
      {line?.rule ? (
        <span className="rule" data-portfolio-coverage-rule>
          {line.rule}
        </span>
      ) : null}
      <Disclosure summary={COVERAGE_GLOSSARY} name="portfolio-readings-words" variant="inline">
        <dl className="pf-glossary" data-portfolio-glossary>
          {READINGS_TERMS.map(([term, definition]) => (
            <div key={term}>
              <dt>{term}</dt>
              <dd>{definition}</dd>
            </div>
          ))}
        </dl>
        <p>{READINGS_GLOSSARY_NOTE}</p>
      </Disclosure>
      <Link to={scopeHref} data-portfolio-coverage-link>
        {COVERAGE_LINK}
      </Link>
    </div>
  );
}
