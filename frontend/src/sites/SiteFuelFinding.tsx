/**
 * DIESEL-K5 (DIESEL-1-R3l, build sheet DIESEL-1 §9l.2): the unexplained-fuel Finding page body and the Site Findings
 * "Fuel checks" panel. The shell frame (`SiteFuelFindingFrame`) supplies the Site heading, the Site tabs and the
 * route builders; every line here is the server's (K4a's `finding_text`, K5's `night_text`).
 *
 * MOCK DEVIATION MD-FUEL-K4-1 (DIESEL-1-R3j, cited by K5): the fuel Finding page itself. v69 has no unexplained-fuel
 * Finding and defers "theft detection" (index.html:630).
 */
import { useEffect, useState } from "react";
import { RangeLink as Link } from "../ui/RangeLink";

import { Badge, Panel, StatusBar } from "../ui";
import type { FuelBalanceClient, FuelFindingBody, FuelFindingRow } from "./fuelBalanceClient";
import { FuelNightBridge, FuelNightRecords, fuelProvenanceChips } from "./MiniFuelNights";
import type { MiniRead } from "./miniDepthClient";
import { MINI_LOADING, MINI_UNAVAILABLE } from "./MiniPerformance";
import "./w4-mini-performance.css";

export function useFuelFinding(client: FuelBalanceClient, siteCode: string, findingId: string, revisionId: string | null): MiniRead<FuelFindingBody> | null {
  const key = `${siteCode}|${findingId}|${revisionId ?? ""}`;
  const [state, setState] = useState<{ key: string; value: MiniRead<FuelFindingBody> } | null>(null);
  useEffect(() => {
    let active = true;
    void client.getFuelFinding(siteCode, findingId, revisionId).then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
  }, [client, siteCode, findingId, revisionId, key]);
  return state !== null && state.key === key ? state.value : null;
}

export function SiteFuelFindingBody({
  read,
  revisionHref,
  nightHref,
}: {
  read: MiniRead<FuelFindingBody> | null;
  /** The shell's `siteFuelFindingHref(site, id, revision)`. */
  revisionHref: (revisionId: string) => string;
  /** The shell's Fuel page address for one night (`sitePerformanceHref(site, "fuel")` + `?night=`). */
  nightHref: (nightDate: string) => string;
}) {
  if (read === null) return <p role="status">{MINI_LOADING}</p>;
  if (read.status !== "loaded") {
    return (
      <p role="alert" data-fuel-finding-unavailable>
        {read.message ?? MINI_UNAVAILABLE}
      </p>
    );
  }
  const body = read.value;
  const { lines } = body;
  const facts = [lines.gap, lines.money, lines.margin, lines.not_why].filter((line): line is string => line !== null);
  return (
    <div data-fuel-finding={body.finding_id} data-fuel-finding-lifecycle={body.lifecycle}>
      <StatusBar label="Fuel finding" items data={{ "data-fuel-finding-status": body.lifecycle }}>
        <span className="status-strip__item">
          <Badge tone="neutral" className={body.lifecycle === "SUPPORTED" ? "mini-tone--amber status-tone--amber" : "status-tone--neutral"}>
            {body.lifecycle_text}
          </Badge>
        </span>
        <span className="status-strip__item" data-fuel-finding-night>
          {body.label}
        </span>
        {fuelProvenanceChips(body.provenance).map((chip) => (
          <span className="status-strip__item" key={chip} data-mini-provenance>
            <Badge tone="neutral">{chip}</Badge>
          </span>
        ))}
      </StatusBar>
      {/* UQ-FI-2 P3 (D-UQFI.18): the first lifecycle sentence (claim / no-longer line) is the page subtitle, said once. */}
      {facts.length === 0 ? null : (
        <ul className="prose" data-fuel-finding-facts>
          {facts.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
      <Panel heading="How the night was checked" headingId="fuel-finding-check-heading">
        <FuelNightBridge rows={body.night.bridge} evidenceHref={body.night.links.evidence} headingId="fuel-finding-bridge-heading" />
        <p>
          <Link to={nightHref(body.night_date)} data-fuel-finding-night-link>
            {body.links.fuel_night_label}
          </Link>
        </p>
      </Panel>
      <FuelNightRecords rows={body.night.records} emptyText={body.night.records_empty} headingId="fuel-finding-records-heading" />
      <Panel heading="Versions" headingId="fuel-finding-versions-heading">
        <ul data-fuel-finding-versions>
          {body.revisions.map((revision) => (
            <li key={revision.revision_id}>
              {revision.revision_id === body.revision_id ? (
                <span aria-current="true">{revision.text}</span>
              ) : (
                <Link to={revisionHref(revision.revision_id)}>{revision.text}</Link>
              )}
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}

/**
 * The Site Findings index's "Fuel checks" panel: one link row per fuel Finding in the index window. Rendered only when
 * there is at least one row, so a Site without fuel Findings (Kobo) is unchanged.
 *
 * MOCK DEVIATION MD-FUEL-K5-3 (DIESEL-1-R3l): v69's Findings index lists dispatch Findings only.
 */
export function SiteFuelChecks({
  client,
  siteCode,
  window,
  findingHref,
}: {
  client: FuelBalanceClient;
  siteCode: string;
  window: { from: string; to: string };
  findingHref: (findingId: string) => string;
}) {
  const [rows, setRows] = useState<{ key: string; rows: FuelFindingRow[] } | null>(null);
  const key = `${siteCode}|${window.from}|${window.to}`;
  useEffect(() => {
    let active = true;
    void client.getFuelFindings(siteCode, window).then((read) => {
      if (active) setRows({ key, rows: read.status === "loaded" ? read.value.rows : [] });
    });
    return () => {
      active = false;
    };
    // `window` is named by `key`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, key]);
  const shown = rows !== null && rows.key === key ? rows.rows : [];
  if (shown.length === 0) return null;
  return (
    <Panel heading="Fuel checks" headingId="site-fuel-checks-heading">
      <ul data-site-fuel-checks>
        {shown.map((row) => (
          <li key={row.finding_id} data-fuel-check-row={row.lifecycle}>
            <Link to={findingHref(row.finding_id)}>{row.text}</Link>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
