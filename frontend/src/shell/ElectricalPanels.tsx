import { DataTable, Fact, FactList, Panel } from "../ui";
import type { RunElectrical } from "./runSetupClient";

/**
 * An exact quantity as a reader meets it.
 *
 * The backend sends every exact quantity as text: a terminating decimal where
 * the rational has one, and the ratio itself where it does not - a state of
 * charge after a 95 % efficient discharge is `965/19`. That ratio is shown to
 * two decimal places, marked approximate, with the exact text in the title so
 * the number the kernel holds is one hover away. A terminating decimal is shown
 * exactly as sent. Nothing here does arithmetic the world depends on; this is
 * presentation of a number that is already exact on the wire.
 */
export function ExactQuantity({
  value,
  unit,
}: {
  value: string | null;
  unit?: string;
}) {
  if (value === null) {
    return <>not available</>;
  }
  const suffix = unit === undefined || unit === "" ? "" : ` ${unit}`;
  const ratio = /^(-?\d+)\/(\d+)$/.exec(value);
  if (ratio === null) {
    return (
      <span data-exact={value}>
        {value}
        {suffix}
      </span>
    );
  }
  const approximate = (Number(ratio[1]) / Number(ratio[2])).toFixed(2);
  return (
    <span data-exact={value} title={`exactly ${value}${suffix}`}>
      {`≈ ${approximate}${suffix}`}
    </span>
  );
}

function offsetSpan(from: number, to: number): string {
  return `[${from}, ${to}) min`;
}

/**
 * The electrical world of one execution (T024), for the gated Lab.
 *
 * Six panels, and the separation between them is the slice. What the
 * controller SAW, what it ASKED for and what the world ACCEPTED are three
 * records in the execution contract and three tables here: a request of 30 kW
 * against a 22 kW PCS shows both numbers on one row with the limit that bound
 * named beside them, and only the accepted number reaches a stock or a later
 * reading. Each load has its own row, because two loads of one type are two
 * addresses and nothing sums them before service is decided.
 *
 * Everything here is private truth on a gated surface. No operator screen
 * reads it.
 */
export function ElectricalPanels({ electrical }: { electrical: RunElectrical }) {
  const latest = electrical.steps[electrical.steps.length - 1];
  if (latest === undefined) {
    return null;
  }
  const reserve = electrical.latest_effective_controls;
  return (
    <>
      <Panel
        heading="The electrical world at this step"
        headingId="run-electrical-heading"
      >
        <p>
          {`The step ${offsetSpan(latest.from_offset, latest.to_offset)} from ${latest.simulation_time}, resolved. `}
          Mean powers over the step in kW; the battery is positive while
          discharging to the bus and negative while charging from it.
        </p>
        <FactList>
          <Fact term="Battery state of charge">
            <span data-electrical-soc-start>
              <ExactQuantity value={latest.soc_start} unit="%" />
            </span>
            {" at the step's start, "}
            <span data-electrical-soc-end>
              <ExactQuantity value={latest.soc_end} unit="%" />
            </span>
            {" carried to its end"}
          </Fact>
          <Fact term="Reserve in effect">
            <span data-electrical-reserve={latest.reserve_origin}>
              <ExactQuantity value={latest.reserve} unit="%" />
              {` (${latest.reserve_origin.toLowerCase()})`}
            </span>
          </Fact>
          <Fact term="PV potential">
            <span data-electrical-pv-potential>
              <ExactQuantity value={latest.pv_potential} unit="kW" />
            </span>
          </Fact>
          <Fact term="PV delivered">
            <span data-electrical-pv-output>
              <ExactQuantity value={latest.pv_output} unit="kW" />
            </span>
          </Fact>
          <Fact term="PV curtailed">
            <span data-electrical-curtailed>
              <ExactQuantity value={latest.curtailed} unit="kW" />
            </span>
            {", clipped by the inverter "}
            <ExactQuantity value={latest.clipped} unit="kW" />
          </Fact>
          <Fact term="Battery power accepted">
            <span data-electrical-battery-accepted>
              <ExactQuantity value={latest.battery_power} unit="kW" />
            </span>
          </Fact>
          <Fact term="Demand, served, unserved">
            <span data-electrical-demand>
              <ExactQuantity value={latest.demand} unit="kW" />
            </span>
            {", "}
            <span data-electrical-served>
              <ExactQuantity value={latest.served} unit="kW" />
            </span>
            {", "}
            <span data-electrical-unserved>
              <ExactQuantity value={latest.unserved} unit="kW" />
            </span>
          </Fact>
        </FactList>
        {electrical.notes.length === 0 ? null : (
          <ul className="note">
            {electrical.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel
        heading="Requested versus accepted control"
        headingId="run-control-heading"
        flush
      >
        <DataTable labelledBy="run-control-heading">
          <thead>
            <tr>
              <th scope="col">Control</th>
              <th scope="col">Requested</th>
              <th scope="col">Accepted</th>
              <th scope="col">Limited by</th>
              <th scope="col">Why the controller asked</th>
            </tr>
          </thead>
          <tbody>
            {electrical.latest_controls.map((control) => {
              const request = electrical.latest_requests.find(
                (item) =>
                  item.address === control.address &&
                  item.quantity === control.quantity,
              );
              return (
                <tr
                  key={`${control.address}-${control.quantity}`}
                  data-control={control.quantity}
                >
                  <th scope="row">{`${control.quantity} at ${control.address}`}</th>
                  <td data-control-requested>
                    <ExactQuantity
                      value={request?.requested ?? control.requested}
                      unit={control.unit}
                    />
                  </td>
                  <td data-control-accepted>
                    <ExactQuantity value={control.accepted} unit={control.unit} />
                  </td>
                  <td className="cell-secondary" data-control-limited-by>
                    {control.limited_by.length === 0
                      ? "nothing bound"
                      : control.limited_by.join("; ")}
                  </td>
                  <td className="cell-secondary">{request?.reason ?? ""}</td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
      </Panel>

      <Panel
        heading="Each load: demand and service"
        headingId="run-loads-heading"
        flush
      >
        <DataTable labelledBy="run-loads-heading">
          <thead>
            <tr>
              <th scope="col">Load</th>
              <th scope="col">Priority</th>
              <th scope="col">Demand</th>
              <th scope="col">Served</th>
              <th scope="col">Unserved</th>
              <th scope="col">Unserved energy this step</th>
            </tr>
          </thead>
          <tbody>
            {electrical.latest_loads.map((load) => (
              <tr key={load.address} data-load={load.address}>
                <th scope="row">{load.address}</th>
                <td>{String(load.priority_rank)}</td>
                <td data-load-demand>
                  <ExactQuantity value={load.demand_power} unit="kW" />
                </td>
                <td data-load-served>
                  <ExactQuantity value={load.served_power} unit="kW" />
                </td>
                <td data-load-unserved>
                  <ExactQuantity value={load.unserved_power} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={load.unserved_energy} unit="kWh" />
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>

      <Panel
        heading="Named flows this step"
        headingId="run-flows-heading"
        flush
      >
        <DataTable labelledBy="run-flows-heading">
          <thead>
            <tr>
              <th scope="col">Flow</th>
              <th scope="col">From</th>
              <th scope="col">To</th>
              <th scope="col">Energy</th>
              <th scope="col">Mean power</th>
            </tr>
          </thead>
          <tbody>
            {electrical.latest_flows.map((flow) => (
              <tr key={flow.flow_id} data-flow={flow.flow_id}>
                <th scope="row">{flow.flow_id}</th>
                <td>{flow.from_address}</td>
                <td>{flow.to_address}</td>
                <td>
                  <ExactQuantity value={flow.energy} unit="kWh" />
                </td>
                <td data-flow-power>
                  <ExactQuantity value={flow.mean_power} unit="kW" />
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <p className="note">
          {`Balances verified exactly this step: ${electrical.latest_balances.join(", ")}. `}
          {`Evaluated in ${electrical.latest_segments.length} segment(s): `}
          {electrical.latest_segments
            .map(([from, to]) => offsetSpan(from, to))
            .join(", ")}
          .
        </p>
      </Panel>

      <Panel
        heading="What the controller saw, and the reserve in effect"
        headingId="run-view-heading"
        flush
      >
        <DataTable labelledBy="run-view-heading">
          <thead>
            <tr>
              <th scope="col">Local input</th>
              <th scope="col">Address</th>
              <th scope="col">Value</th>
            </tr>
          </thead>
          <tbody>
            {electrical.latest_view.map((entry) => (
              <tr
                key={`${entry.name}-${entry.address}`}
                data-view={`${entry.name}:${entry.address}`}
              >
                <th scope="row">{entry.name}</th>
                <td>{entry.address}</td>
                <td>
                  <ExactQuantity value={entry.value} unit={entry.unit} />
                </td>
              </tr>
            ))}
            {reserve.map((item) => (
              <tr
                key={`reserve-${item.from_offset}`}
                data-effective-control={item.origin}
              >
                <th scope="row">{`reserve over ${offsetSpan(item.from_offset, item.to_offset)}`}</th>
                <td>{item.provenance}</td>
                <td>
                  <ExactQuantity value={item.value} unit={item.unit} />
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <p className="note">
          The controller reads these local inputs and never a published
          reading. The source and critical-load priorities are the baseline
          Site Controls this run froze; no scenario entry changes them in this
          build. The generator is not modelled until T025.
        </p>
      </Panel>

      <Panel
        heading="Against simulation time"
        headingId="run-electrical-series-heading"
        flush
      >
        <DataTable labelledBy="run-electrical-series-heading">
          <thead>
            <tr>
              <th scope="col">Step from</th>
              <th scope="col">SOC at start</th>
              <th scope="col">Reserve</th>
              <th scope="col">PV potential</th>
              <th scope="col">PV delivered</th>
              <th scope="col">Curtailed</th>
              <th scope="col">Battery requested</th>
              <th scope="col">Battery accepted</th>
              <th scope="col">Demand</th>
              <th scope="col">Unserved</th>
            </tr>
          </thead>
          <tbody>
            {electrical.steps.map((row) => (
              <tr key={row.from_offset} data-electrical-step={row.from_offset}>
                <th scope="row">{row.simulation_time}</th>
                <td>
                  <ExactQuantity value={row.soc_start} unit="%" />
                </td>
                <td>
                  <ExactQuantity value={row.reserve} unit="%" />
                </td>
                <td>
                  <ExactQuantity value={row.pv_potential} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.pv_output} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.curtailed} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.requested_battery_power} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.battery_power} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.demand} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.unserved} unit="kW" />
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>

      <Panel
        heading="What the controller and resolver commit to"
        headingId="run-coupling-heading"
      >
        <FactList>
          {electrical.coupling_rules.map((rule) => (
            <Fact key={rule.rule_id} term={rule.display_name}>
              {rule.statement}
            </Fact>
          ))}
        </FactList>
      </Panel>
    </>
  );
}
