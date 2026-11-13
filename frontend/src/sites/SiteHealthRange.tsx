/**
 * SR-6b (rev 10 §10.2; D-SR.20, D-SR.49, D-SR.56): mini-grid Health over the date range, from one
 * `site-health-range-1` read. A status line (readings counted per day), the days (analysis state and "Readings used
 * for analysis"), then one row per gateway and per source with one cell per UTC day. Every word below is the ruled
 * wording; nothing is computed here beyond counting the body's own rows.
 *
 * MOCK DEVIATION R724 (v69 `health:1/2` shows current contact only): the range tables are added above the v69 panels,
 * which stay as "Battery (current settings)" and "Contact now".
 */
import { useEffect, useState, type ReactNode } from "react";

import { DataTable, Panel, StatusBar } from "../ui";
import { RangeLink as Link } from "../ui/RangeLink";
import { formatDay } from "../ui/time";
import { dayGapWords } from "../ui/productWords";
import { HealthGap } from "./SiteHealth";
import type { HealthRead } from "./healthClient";
import type { HealthRangeBody, HealthRangeClient, HealthRangeQuery } from "./healthRangeClient";
import { RETRYING_COPY, STILL_UNAVAILABLE_COPY } from "./temporarilyUnavailable";
import { SITE_HEALTH_RANGE_UNAVAILABLE, isRetryable } from "./healthRangeClient";

/** Gateway-day words (rev 10 §10.2; READINGS_ONLY D-SR.20; AFTER_CUTOFF D-SR.49 Q4). */
export const CONTACT_WORDS: Readonly<Record<string, string>> = {
  IN_CONTACT: "In contact",
  PARTIAL_CONTACT: "Partial contact",
  READINGS_ONLY: "Readings received; no status reports",
  NO_CONTACT: "No contact",
  NOT_EXPECTED: "Before it was registered",
  AFTER_CUTOFF: "Not reached yet",
};

/** Source-day words; a READINGS cell shows its count. */
export const SOURCE_WORDS: Readonly<Record<string, string>> = {
  NO_READINGS: "No readings",
  NOT_EXPECTED: "Before readings began",
  AFTER_CUTOFF: "Not reached yet",
};

/** The SR-5a day state, with ANALYSED collapsed (D-SR.22); gap states use the one D-E5.46 table. */
export function dayStateWord(state: string): string {
  if (state === "ANALYSED") return "Analysed";
  if (state === "STILL_PROCESSING") return "Still processing";
  if (state === "NOT_EXPECTED") return "Before readings began";
  const gap = dayGapWords(state);
  if (gap !== null) return gap.short.charAt(0).toUpperCase() + gap.short.slice(1);
  return "Not analysed yet";
}

const TONE: Readonly<Record<string, string>> = {
  IN_CONTACT: "good",
  READINGS: "good",
  PARTIAL_CONTACT: "partial",
  READINGS_ONLY: "partial",
  NO_CONTACT: "none",
  NO_READINGS: "none",
};
const toneOf = (state: string): string => TONE[state] ?? "muted";

export const dayLabel = (day: string): string => formatDay(`${day}T00:00:00Z`, { year: false });
const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

/** D-SR.49 Q1: "Readings on 1 of 4 days · 3 days with no readings", the other classes named when non-zero. */
export function statusLine(summary: HealthRangeBody["summary"]): string {
  const parts = [`Readings on ${summary.days_with_readings} of ${plural(summary.days_requested, "day", "days")}`];
  if (summary.days_without_readings > 0) parts.push(`${plural(summary.days_without_readings, "day", "days")} with no readings`);
  if (summary.days_not_expected > 0) parts.push(`${plural(summary.days_not_expected, "day", "days")} before readings began`);
  if (summary.days_after_cutoff > 0) parts.push(`${plural(summary.days_after_cutoff, "day", "days")} not reached yet`);
  return parts.join(" · ");
}

const HEALTH_RANGE_TEXTS: Record<string, string> = {
  [SITE_HEALTH_RANGE_UNAVAILABLE]: STILL_UNAVAILABLE_COPY,
  INVALID_WINDOW: "The date range could not be used for this site's health. Choose a range of at most 31 days.",
  HEALTH_RANGE_NOT_APPLICABLE: "This site reads its date range on its own Health page.",
};

function Cell({ state, label, children }: { state: string; label: string; children: ReactNode }) {
  return (
    <td className={`health-day health-day--${toneOf(state)}`} data-day-state={state} aria-label={label}>
      {children}
    </td>
  );
}

function DayHeads({ body, drill }: { body: HealthRangeBody; drill: boolean }) {
  return (
    <>
      {body.days.map((d) => (
        <th key={d.day} scope="col" className="health-nowrap">
          {drill ? dayLabel(d.day) : <Link to={body.links.day.replace("{day}", d.day)}>{dayLabel(d.day)}</Link>}
        </th>
      ))}
    </>
  );
}

export function HealthRangeView({ body, drill }: { body: HealthRangeBody; drill: boolean }) {
  const gatewayCount = body.gateways.length;
  return (
    <>
      <StatusBar label="Readings over the date range" data={{ "data-health-range-status": "loaded" }}>
        <p>
          <strong>{statusLine(body.summary)}</strong>
        </p>
        <p>
          Gateways in contact on every expected day: {body.summary.gateways_in_contact_all_days} of {gatewayCount}
        </p>
      </StatusBar>
      <Panel
        heading="Days"
        headingId="site-health-range-days-heading"
        description="Each day's analysis state, and the readings the analysis used. Open a day to see it on its own."
      >
        <DataTable labelledBy="site-health-range-days-heading" stickyFirstColumn>
          <thead>
            <tr>
              <th scope="col">Day</th>
              <DayHeads body={body} drill={drill} />
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Analysis</th>
              {body.days.map((d) => (
                <Cell key={d.day} state={d.state} label={`${dayLabel(d.day)}: ${dayStateWord(d.state).toLowerCase()}`}>
                  {dayStateWord(d.state)}
                </Cell>
              ))}
            </tr>
            <tr>
              <th scope="row">Readings used for analysis</th>
              {body.days.map((d) => (
                <Cell
                  key={d.day}
                  state={d.accepted_readings === null ? "NONE" : "COUNT"}
                  label={`${dayLabel(d.day)}: ${d.accepted_readings === null ? "none used" : `${d.accepted_readings} readings used for analysis`}`}
                >
                  {d.accepted_readings === null ? "—" : d.accepted_readings}
                </Cell>
              ))}
            </tr>
          </tbody>
        </DataTable>
      </Panel>
      <Panel
        heading="Gateway contact by day"
        headingId="site-health-range-gateways-heading"
        description="Contact means the server received a gateway's status reports; it says nothing about the equipment."
      >
        <DataTable labelledBy="site-health-range-gateways-heading" stickyFirstColumn>
          <thead>
            <tr>
              <th scope="col">Gateway</th>
              <DayHeads body={body} drill={drill} />
            </tr>
          </thead>
          <tbody>
            {body.gateways.length === 0 ? (
              <tr>
                <td colSpan={body.days.length + 1}>No gateway is registered for this site.</td>
              </tr>
            ) : (
              body.gateways.map((g) => (
                <tr key={g.gateway_external_id} data-gateway={g.gateway_external_id}>
                  <th scope="row" className="health-nowrap">
                    {g.gateway_external_id}
                    {g.disabled ? " · Disabled" : ""}
                  </th>
                  {g.days.map((d) => {
                    const word = CONTACT_WORDS[d.contact] ?? d.contact;
                    return (
                      <Cell
                        key={d.day}
                        state={d.contact}
                        label={`Gateway ${g.gateway_external_id}, ${dayLabel(d.day)}: ${word.toLowerCase()}`}
                      >
                        {word}
                      </Cell>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </DataTable>
      </Panel>
      <Panel
        heading="Readings received by day"
        headingId="site-health-range-sources-heading"
        description="Readings received from each source, counted on the day each reading's interval starts."
      >
        <DataTable labelledBy="site-health-range-sources-heading" stickyFirstColumn>
          <thead>
            <tr>
              <th scope="col">Source</th>
              <DayHeads body={body} drill={drill} />
            </tr>
          </thead>
          <tbody>
            {body.sources.length === 0 ? (
              <tr>
                <td colSpan={body.days.length + 1}>No source is registered for this site.</td>
              </tr>
            ) : (
              body.sources.map((s) => (
                <tr key={s.source_external_id} data-source={s.source_external_id}>
                  <th scope="row" className="health-nowrap">
                    {s.source_external_id}
                    {s.disabled ? " · Disabled" : ""}
                  </th>
                  {s.days.map((d) => {
                    const word = d.state === "READINGS" ? `${d.accepted_readings} readings received` : (SOURCE_WORDS[d.state] ?? d.state);
                    return (
                      <Cell key={d.day} state={d.state} label={`Source ${s.source_external_id}, ${dayLabel(d.day)}: ${word.toLowerCase()}`}>
                        {d.state === "READINGS" ? d.accepted_readings : word}
                      </Cell>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </DataTable>
      </Panel>
    </>
  );
}

/** The range page: one read; "Temporarily unavailable. Retrying…" while a 503 is retried. */
export function SiteHealthRange({
  siteCode,
  query,
  drill,
  client,
}: {
  siteCode: string;
  query: HealthRangeQuery;
  /** The one-day drill-in (`day=` in the address): the day heads do not link. */
  drill: boolean;
  client: HealthRangeClient;
}) {
  const key = `${siteCode}|${query.from}|${query.to}|${query.known_at ?? ""}`;
  const [read, setRead] = useState<{ key: string; read: HealthRead<HealthRangeBody> } | null>(null);
  const [retrying, setRetrying] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    void client
      .getHealthRange(siteCode, query, () => {
        if (live) setRetrying(key);
        return live;
      })
      .then((r) => {
        if (!live) return;
        setRetrying(null);
        setRead({ key, read: r });
      });
    return () => {
      live = false;
    };
    // `key` names the read.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, key]);
  const current = read?.key === key ? read.read : null;
  if (current === null) {
    return (
      <p role="status" data-temporarily-unavailable={retrying === key ? "retrying" : undefined}>
        {retrying === key ? RETRYING_COPY : "Loading the site's health over the date range."}
      </p>
    );
  }
  if (current.status === "refused") {
    if (current.http !== null && isRetryable(current.http, current.code)) {
      return (
        <p role="alert" className="v69-notice" data-temporarily-unavailable="still">
          {STILL_UNAVAILABLE_COPY}
        </p>
      );
    }
    return (
      <Panel heading="Health over the date range" headingId="site-health-range-refused-heading">
        <HealthGap refusal={current} subject="Health over the date range" name="site-health-range-refused-code" texts={HEALTH_RANGE_TEXTS} />
      </Panel>
    );
  }
  return <HealthRangeView body={current.value} drill={drill} />;
}
