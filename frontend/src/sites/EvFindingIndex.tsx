import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { DataTable, Panel, StatusBar } from "../ui";
import { UnavailableInline } from "../ui/UnavailableEntry";
import { claimWord, lifecycleWord } from "./coldAssessmentWords";
import { windowText } from "./coldFormat";
import type { EvAssessmentClient, EvFindingsRead, EvRead, EvWindowQuery } from "./evAssessmentClient";
import { renderEvTabs, selectedWindowSearch, type EvTabs } from "./evSelectedWindow";
import { RefusedGap, RefusedHead } from "./EvAssessmentViews";
import { LensChips } from "./SiteFindingIndex";

export const EV_FINDING_INDEX_HEADING_ID = "ev-finding-index-heading";
export const EV_FINDING_INDEX_EMPTY = "No Findings at this site in the selected window.";
export const EV_FINDING_INDEX_GLOBAL_NOTE = "EV charging Findings are not in the global Findings list";
const NOT_ASSESSED = "Not assessed";
const HEADERS = ["Finding", "Domain", "Priority", "Confidence", "State", "Main consequence", "Lens"];

/** post-W6 W2-EV B9-10/R253: the EV Site Findings list, from the selected `ev/findings` read. */
export function EvFindingIndex({
  siteId,
  siteName,
  window,
  client,
  findingHref,
  sessionsHref,
  tabs,
}: {
  siteId: string;
  siteName: string;
  window: EvWindowQuery;
  client: EvAssessmentClient;
  findingHref: (findingId: string) => string;
  sessionsHref: string;
  tabs: EvTabs;
}) {
  const key = `${siteId}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}`;
  const [state, setState] = useState<{ key: string; read: EvRead<EvFindingsRead> } | null>(null);
  useEffect(() => {
    let active = true;
    void client.listFindings(siteId, window).then((read) => {
      if (active) setState({ key, read });
    });
    return () => {
      active = false;
    };
    // The key names the read.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, key]);
  const read = state !== null && state.key === key ? state.read : null;
  const tabRow = renderEvTabs(tabs, read !== null && read.status === "loaded" ? selectedWindowSearch(read.value) : "");
  if (read === null) {
    return (
      <>
        {tabRow}
        <p>Loading the site&apos;s EV findings.</p>
      </>
    );
  }
  if (read.status !== "loaded") {
    return (
      <div className="finding-index" data-ev-findings-index="refused">
        {tabRow}
        <RefusedHead read={read} window={window} label="EV Findings" />
        <Panel heading="Findings at this site" headingId={EV_FINDING_INDEX_HEADING_ID}>
          <RefusedGap id="ev-findings" read={read} />
        </Panel>
      </div>
    );
  }
  const body = read.value;
  const open = body.items.filter((i) => i.lifecycle === "SUPPORTED").length;
  return (
    <div className="finding-index" data-ev-findings-index="loaded">
      {tabRow}
      <LensChips />
      <StatusBar label="EV Findings" action={<UnavailableInline label="Manage in Findings" />}>
        <strong>{`Scoped to ${siteName} · ${open} open`}</strong>
        <span>{` · ${windowText(body.window.from, body.window.to)}`}</span>
        <span data-ev-findings-global-note>{` · ${EV_FINDING_INDEX_GLOBAL_NOTE}`}</span>
      </StatusBar>
      <Panel heading="Findings at this site" headingId={EV_FINDING_INDEX_HEADING_ID}>
        {body.items.length === 0 ? (
          <p className="prose" data-ev-findings-empty>
            {EV_FINDING_INDEX_EMPTY}
          </p>
        ) : (
          <DataTable labelledBy={EV_FINDING_INDEX_HEADING_ID}>
            <thead>
              <tr>
                {HEADERS.map((h) => (
                  <th key={h} scope="col">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.items.map((i) => (
                // The mini index row class (w1ux02-findings-index.css): a 15rem title column at phone width, other cells on one
                // line, so a long title wraps in a readable column instead of a one-word strip (Q26 cap fallback).
                <tr key={`${i.finding_id}|${i.revision_id}`} className="finding-index-row" data-ev-finding-row={i.finding_id}>
                  <td>
                    <Link to={findingHref(i.finding_id)}>{i.title}</Link>
                  </td>
                  <td>
                    <Link to={sessionsHref}>Sessions</Link>
                  </td>
                  <td>{NOT_ASSESSED}</td>
                  <td>{claimWord(i.claim_level)}</td>
                  <td>{lifecycleWord(i.lifecycle)}</td>
                  <td>Not in this list</td>
                  <td>{NOT_ASSESSED}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
        {body.next_cursor !== null ? (
          <p className="prose" data-ev-findings-cursor>
            {`Showing the first ${body.items.length} Findings; paging is not available on this page.`}
          </p>
        ) : null}
      </Panel>
    </div>
  );
}
