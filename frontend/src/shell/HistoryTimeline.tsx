import { useState } from "react";

import { DataTable, Panel } from "../ui";
import {
  intervalTimeline,
  LANE_HEADINGS,
  runTimeline,
  type TimelineEntry,
  type TimelineLane,
} from "./historyTimelineModel";
import type { RunHistory } from "./runHistory";

const LANES: TimelineLane[] = ["APPLIED", "PHYSICAL", "REPORTING"];

/**
 * The applied timeline in three lanes (T025d, Lab cockpit C3).
 *
 * By default it shows what bears on the selected boundary and the interval
 * that ended there; the whole run is one choice away, with contiguous repeats
 * of one cause grouped into one span that keeps its row count and shares.
 * Each lane is a table, so phase, origin, share, address and span are all
 * read as text; nothing is told apart by colour alone.
 */
export function HistoryTimeline({
  history,
  offset,
}: {
  history: RunHistory;
  offset: number;
}) {
  const [scope, setScope] = useState<"interval" | "run">("interval");
  const entries =
    scope === "interval" ? intervalTimeline(history, offset) : runTimeline(history);

  return (
    <Panel heading="Applied timeline" headingId="run-timeline-heading" flush>
      <fieldset className="timeline-scope" data-timeline-scope={scope}>
        <legend>Show</legend>
        <label>
          <input
            type="radio"
            name="run-timeline-scope"
            checked={scope === "interval"}
            onChange={() => setScope("interval")}
          />{" "}
          {`What bears on the selected boundary, ${offset} min`}
        </label>{" "}
        <label>
          <input
            type="radio"
            name="run-timeline-scope"
            checked={scope === "run"}
            onChange={() => setScope("run")}
          />{" "}
          The whole recorded run
        </label>
      </fieldset>
      <p>
        Every entry is read from the run&apos;s ledger: only what the run
        applied appears, never a planned event. A reporting condition is not a
        physical outage; the state it hides is in the other lanes.
      </p>
      {LANES.map((lane) => (
        <TimelineLaneTable
          key={lane}
          lane={lane}
          entries={entries.filter((e) => e.lane === lane)}
        />
      ))}
    </Panel>
  );
}

function TimelineLaneTable({
  lane,
  entries,
}: {
  lane: TimelineLane;
  entries: TimelineEntry[];
}) {
  const headingId = `run-timeline-${lane.toLowerCase()}-heading`;
  return (
    <div data-timeline-lane={lane}>
      <h3 className="subsection__subheading" id={headingId}>
        {LANE_HEADINGS[lane]}
      </h3>
      {entries.length === 0 ? (
        <p data-timeline-empty={lane}>Nothing recorded in this lane here.</p>
      ) : (
        <DataTable labelledBy={headingId}>
          <thead>
            <tr>
              <th scope="col">What</th>
              <th scope="col">Cause</th>
              <th scope="col">Address</th>
              <th scope="col">Phase</th>
              <th scope="col">Origin or outcome</th>
              <th scope="col">Share</th>
              <th scope="col">When</th>
              <th scope="col">Governs</th>
              <th scope="col">Detail</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr
                key={entry.key}
                data-timeline-entry={entry.kind}
                data-phase={entry.phase ?? ""}
                data-agrees={
                  entry.agrees === null ? undefined : entry.agrees ? "yes" : "no"
                }
              >
                <th scope="row">{entry.kind}</th>
                <td>{entry.source}</td>
                <td>{entry.address}</td>
                <td>{entry.phase ?? "none"}</td>
                <td>{entry.origin ?? "none"}</td>
                <td>{entry.share ?? "none"}</td>
                <td>
                  {entry.span[0] === entry.span[1]
                    ? `at ${entry.span[0]} min`
                    : `[${entry.span[0]}, ${entry.span[1]}) min`}
                </td>
                <td>{entry.applies}</td>
                <td>
                  {entry.detail}
                  {entry.agrees === null
                    ? ""
                    : entry.agrees
                      ? " - the recorded state agrees"
                      : " - the recorded state DISAGREES"}
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
    </div>
  );
}
