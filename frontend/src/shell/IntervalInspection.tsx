import { DataTable, Panel } from "../ui";
import { parseExact, readable } from "./exactArithmetic";
import { completedIntervalAt } from "./intervalDrawingModel";
import type { RunHistory, RunHistoryControl, RunHistoryRequest } from "./runHistory";

/**
 * Requested versus accepted control for one recorded interval (T025d, C4).
 *
 * The interval is the one that ENDED at the selected boundary - the same one
 * the charts' interval readings and the drawing's flows describe. Every row is
 * read from that interval's own record: the controller's request with the
 * reason it recorded, what the resolver accepted and what limited it, the
 * effective controls with their provenance, each load's service and the exact
 * balance identities. Nothing is taken from the latest step, and nothing is
 * explained by comparing numbers: a reason shown is a reason recorded.
 */
export function IntervalInspection({
  history,
  offset,
}: {
  history: RunHistory;
  offset: number;
}) {
  const interval = completedIntervalAt(history, offset);

  if (interval === null) {
    return (
      <Panel
        heading="Requested and accepted control"
        headingId="run-interval-control-heading"
      >
        <p data-interval-none={offset}>
          {`No resolved interval ended at ${offset} min, so there is no request, acceptance, service or balance to show here. ` +
            "An interval is recorded from the boundary that decides it to the boundary that ends it."}
        </p>
      </Panel>
    );
  }

  const span = `[${interval.from_offset}, ${interval.to_offset})`;
  const rows = controlRows(interval.requests, interval.controls);

  return (
    <>
      <Panel
        heading="Requested and accepted control"
        headingId="run-interval-control-heading"
        flush
      >
        <p

          data-interval-span={`${interval.from_offset}-${interval.to_offset}`}
        >
          {`The interval ${span} min that ended at the selected boundary: decided at ${interval.from_offset} min from the controller's view there, and completed at ${interval.to_offset} min. Power is the mean over the interval in kW; energy is over the interval in kWh.`}
        </p>
        <DataTable labelledBy="run-interval-control-heading">
          <thead>
            <tr>
              <th scope="col">Control</th>
              <th scope="col">Requested</th>
              <th scope="col">Recorded reason</th>
              <th scope="col">Accepted</th>
              <th scope="col">Limited by</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ key, request, control }) => {
              const differs =
                request !== null &&
                control !== null &&
                request.requested !== control.accepted;
              return (
                <tr
                  key={key}
                  data-interval-control={key}
                  data-accepted-differs={differs ? "yes" : "no"}
                >
                  <th scope="row">{key}</th>
                  <td>
                    {request === null
                      ? "no request recorded"
                      : quantity(request.requested, request.unit)}
                  </td>
                  <td>{request?.reason ?? "no request recorded"}</td>
                  <td>
                    {control === null
                      ? "no acceptance recorded"
                      : quantity(control.accepted, control.unit)}
                    {differs ? " - differs from the request" : ""}
                  </td>
                  <td>
                    {control === null
                      ? ""
                      : control.limited_by.length === 0
                        ? "not limited"
                        : control.limited_by.join("; ")}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
      </Panel>

      <Panel
        heading="Effective controls over the interval"
        headingId="run-interval-effective-heading"
        flush
      >
        {interval.effective_controls.length === 0 ? (
          <p data-interval-no-effective>
            No effective control is recorded for this interval.
          </p>
        ) : (
          <DataTable labelledBy="run-interval-effective-heading">
            <thead>
              <tr>
                <th scope="col">Address</th>
                <th scope="col">Value</th>
                <th scope="col">In effect over</th>
                <th scope="col">Origin</th>
                <th scope="col">Provenance</th>
              </tr>
            </thead>
            <tbody>
              {interval.effective_controls.map((e) => (
                <tr
                  key={`${e.address}-${e.from_offset}`}
                  data-interval-effective={e.address}
                  data-origin={e.origin}
                >
                  <th scope="row">{e.address}</th>
                  <td>{quantity(e.value, e.unit)}</td>
                  <td>{`[${e.from_offset}, ${e.to_offset}) min`}</td>
                  <td>{e.origin}</td>
                  <td>{e.provenance}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
      </Panel>

      <Panel
        heading="Each load's service over the interval"
        headingId="run-interval-loads-heading"
        flush
      >
        {interval.loads.length === 0 ? (
          <p data-interval-no-loads>This model records no addressed load.</p>
        ) : (
          <DataTable labelledBy="run-interval-loads-heading">
            <thead>
              <tr>
                <th scope="col">Load</th>
                <th scope="col">Priority</th>
                <th scope="col">Demand</th>
                <th scope="col">Served</th>
                <th scope="col">Unserved</th>
              </tr>
            </thead>
            <tbody>
              {interval.loads.map((load) => (
                <tr key={load.address} data-interval-load={load.address}>
                  <th scope="row">{load.address}</th>
                  <td>{load.priority_rank}</td>
                  <td>{`${quantity(load.demand_power, "kW")}, ${quantity(load.demand_energy, "kWh")}`}</td>
                  <td>{`${quantity(load.served_power, "kW")}, ${quantity(load.served_energy, "kWh")}`}</td>
                  <td>{`${quantity(load.unserved_power, "kW")}, ${quantity(load.unserved_energy, "kWh")}`}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
      </Panel>

      <Panel
        heading="Exact balance over the interval"
        headingId="run-interval-balance-heading"
        flush
      >
        <p>
          Each identity the model checked, with the exact sums of the recorded
          flow energies it names. The residual is sources minus sinks.
        </p>
        <DataTable labelledBy="run-interval-balance-heading">
          <thead>
            <tr>
              <th scope="col">Identity</th>
              <th scope="col">Sources</th>
              <th scope="col">Sinks</th>
              <th scope="col">Residual</th>
            </tr>
          </thead>
          <tbody>
            {interval.balance_identities.map((b) => (
              <tr
                key={b.identity_id}
                data-interval-balance={b.identity_id}
                data-balance-holds={
                  b.residual === null ? "unknown" : b.residual === "0" ? "yes" : "no"
                }
              >
                <th scope="row">{b.identity_id}</th>
                <td>{`${b.sources.join(" + ")} = ${quantity(b.source_energy, "kWh")}`}</td>
                <td>{`${b.sinks.join(" + ")} = ${quantity(b.sink_energy, "kWh")}`}</td>
                <td>
                  {b.residual === null
                    ? "not computable: a named flow is not recorded"
                    : b.residual === "0"
                      ? "0 kWh - holds exactly"
                      : `${quantity(b.residual, "kWh")} - does not hold`}
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
    </>
  );
}

/** Exact text for a recorded quantity; a discrete member as itself. */
function quantity(value: string | null, unit: string): string {
  if (value === null) return "not recorded";
  if (unit === "state") return value;
  const parsed = parseExact(value);
  return `${parsed === null ? value : readable(parsed)} ${unit}`;
}

/** Requests and acceptances joined on address and quantity, in record order. */
function controlRows(
  requests: RunHistoryRequest[],
  controls: RunHistoryControl[],
): {
  key: string;
  request: RunHistoryRequest | null;
  control: RunHistoryControl | null;
}[] {
  const rows = new Map<
    string,
    { key: string; request: RunHistoryRequest | null; control: RunHistoryControl | null }
  >();
  for (const request of requests) {
    const key = `${request.quantity} at ${request.address}`;
    rows.set(key, { key, request, control: null });
  }
  for (const control of controls) {
    const key = `${control.quantity} at ${control.address}`;
    const row = rows.get(key) ?? { key, request: null, control: null };
    row.control = control;
    rows.set(key, row);
  }
  return [...rows.values()];
}
