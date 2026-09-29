import { DataTable, Fact, FactList, Panel } from "../ui";
import { ExactQuantity } from "./ElectricalPanels";
import type { RunGenerator } from "./runSetupClient";

/** A reported status reading: the member it carried, and its quality. */
function ReportedStatus({
  state,
  quality,
}: {
  state: string | null;
  quality: string | null;
}) {
  if (quality === null) {
    return <>not published by this run</>;
  }
  return (
    <span data-reported-quality={quality}>
      {state === null ? "no reading" : state}
      {` (${quality})`}
    </span>
  );
}

/**
 * The generator of a `mini-grid` execution (T025a), for the gated Lab.
 *
 * Four things the execution contract keeps apart are four fields here and
 * never one: the physical state a sample at T saw, the state over the step
 * after the request emitted at T took effect, the controller's request, and
 * the output the world accepted. A generator that is STARTING was asked to
 * run and delivers nothing; the panel shows both.
 *
 * The physical state is private truth. Since T025b a run under publication
 * profile 4 also carries the generator controller's REPORTED status: the
 * newest status reading at or before T and its quality, shown in its own
 * field and column beside the physical state and never in place of it. A
 * STALE "RUNNING" beside a physical STOPPED is the reporting path, not the
 * world. A run that publishes no status says so in the backend's sentence,
 * never by leaving the field out.
 */
export function GeneratorPanels({ generator }: { generator: RunGenerator }) {
  const latest = generator.steps[generator.steps.length - 1];
  if (latest === undefined) {
    return null;
  }
  // Only a run that publishes a status gets the column; a profile-3 run keeps
  // its table and says why in the reported-status fact.
  const publishesStatus = generator.steps.some(
    (row) => row.reported_quality !== null,
  );
  return (
    <>
      <Panel heading="The generator at this step" headingId="run-generator-heading">
        <p>
          {`The step [${latest.from_offset}, ${latest.to_offset}) min from ${latest.simulation_time}. `}
          Output in kW, mean over the step; fuel in litres.
        </p>
        <FactList>
          <Fact term="Physical state at T">
            <span data-generator-state-at-t>{latest.state_at_t}</span>
          </Fact>
          <Fact term="Physical state over the step">
            <span data-generator-state-for-step>{latest.state_for_step}</span>
          </Fact>
          <Fact term="Reported status at T">
            <span data-generator-reported-state={latest.reported_state ?? ""}>
              <ReportedStatus
                state={latest.reported_state}
                quality={latest.reported_quality}
              />
            </span>
          </Fact>
          <Fact term="Controller request">
            <span data-generator-request>{latest.requested}</span>
            {` - ${latest.request_reason}`}
          </Fact>
          <Fact term="Output accepted">
            <span data-generator-output>
              <ExactQuantity value={latest.output} unit="kW" />
            </span>
            {": to load "}
            <ExactQuantity value={latest.to_load} unit="kW" />
            {", to the battery "}
            <ExactQuantity value={latest.to_battery} unit="kW" />
          </Fact>
          <Fact term="Fuel in the tank">
            <span data-generator-fuel-start>
              <ExactQuantity value={latest.fuel_start} unit="L" />
            </span>
            {" at the step's start, "}
            <span data-generator-fuel-end>
              <ExactQuantity value={latest.fuel_end} unit="L" />
            </span>
            {" carried to its end"}
          </Fact>
          <Fact term="What bound it">
            {latest.limited_by.length === 0
              ? "nothing"
              : latest.limited_by.join("; ")}
          </Fact>
          <Fact term="Where the reported status comes from">
            <span data-generator-reported-status>{generator.reported_status}</span>
          </Fact>
        </FactList>
      </Panel>

      <Panel
        heading="Generator lifecycle transitions"
        headingId="run-generator-transitions-heading"
        flush
      >
        {generator.transitions.length === 0 ? (
          <p data-generator-no-transitions>
            No lifecycle transition so far.
          </p>
        ) : (
          <DataTable labelledBy="run-generator-transitions-heading">
            <thead>
              <tr>
                <th scope="col">At</th>
                <th scope="col">From</th>
                <th scope="col">To</th>
                <th scope="col">Phase</th>
                <th scope="col">Caused by</th>
              </tr>
            </thead>
            <tbody>
              {generator.transitions.map((item) => (
                <tr
                  key={`${item.at_offset_minutes}-${item.next}`}
                  data-generator-transition={item.next}
                >
                  <th scope="row">{item.simulation_time}</th>
                  <td>{item.previous}</td>
                  <td>{item.next}</td>
                  <td>{item.phase}</td>
                  <td>
                    {item.controller_ref === null
                      ? item.cause
                      : `${item.controller_ref}: ${item.cause}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        )}
      </Panel>

      <Panel
        heading="Generator against simulation time"
        headingId="run-generator-series-heading"
        flush
      >
        <DataTable labelledBy="run-generator-series-heading">
          <thead>
            <tr>
              <th scope="col">Step from</th>
              <th scope="col">State at T</th>
              <th scope="col">State over step</th>
              {publishesStatus ? <th scope="col">Reported status</th> : null}
              <th scope="col">Requested</th>
              <th scope="col">Output</th>
              <th scope="col">To load</th>
              <th scope="col">To battery</th>
              <th scope="col">Fuel at end</th>
            </tr>
          </thead>
          <tbody>
            {generator.steps.map((row) => (
              <tr key={row.from_offset} data-generator-step={row.from_offset}>
                <th scope="row">{row.simulation_time}</th>
                <td>{row.state_at_t}</td>
                <td>{row.state_for_step}</td>
                {publishesStatus ? (
                  <td data-generator-step-reported={row.reported_quality ?? ""}>
                    <ReportedStatus
                      state={row.reported_state}
                      quality={row.reported_quality}
                    />
                  </td>
                ) : null}
                <td>{row.requested}</td>
                <td>
                  <ExactQuantity value={row.output} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.to_load} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.to_battery} unit="kW" />
                </td>
                <td>
                  <ExactQuantity value={row.fuel_end} unit="L" />
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>

      <Panel
        heading="What the generator lifecycle commits to"
        headingId="run-generator-rules-heading"
      >
        <FactList>
          {generator.discrete_state_rules.map((rule) => (
            <Fact key={rule.rule_id} term={rule.display_name}>
              {rule.statement}
            </Fact>
          ))}
        </FactList>
      </Panel>
    </>
  );
}
