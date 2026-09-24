import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  Badge,
  DataTable,
  Fact,
  FactList,
  PageHeader,
  Panel,
  ReviewProposal,
} from "../ui";
import type {
  ScenarioCatalogClient,
  ScenarioDetailResult,
  ScenarioObservationReconciliation,
  ScenarioObservationSourceResolution,
  ScenarioParameter,
  ScenarioTargetResolution,
  ScenarioTimelineEntry,
} from "./scenarioCatalogClient";

/**
 * Read-only inspection of one saved ScenarioDefinition, and its executable
 * contract.
 *
 * ## What this screen says, and what it refuses to say
 *
 * It says what a simulated interval is intended to do, and what an executor
 * would be allowed to do with each authored value. It does not say that
 * AssetOps has observed anything: no run exists in this build, so there is no
 * outcome, no accepted evidence, no source quality result, no incident, no
 * action and no product judgement anywhere on it, and no control that would
 * produce one.
 *
 * Two controls are rendered, and the rule for which
 * (`D-2026-09-20-scenario-detail-affordances`) is that a disabled control
 * appears only when the action is native to the object being viewed and the
 * missing prerequisite is the next named causal capability. `Create Draft Run`
 * is native to a scenario, and since T019 it is a real destination whenever
 * the declared target site resolves: run setup exists, and a control that
 * stayed disabled would be claiming otherwise. When the target does not
 * resolve it is still disabled, carrying the backend's own reason, because a
 * run is bound to a concrete site and there is nothing to freeze without one.
 * `Open target Site` is the one product bridge, enabled only when the declared
 * target resolves. Everything downstream belongs to another object or another
 * lifecycle, so it is absent rather than disabled: a disabled control from a
 * later step teaches the wrong object model.
 *
 * ## What T017 settled, and what this screen now asks
 *
 * The T017 checkpoint was accepted on 2026-09-21
 * (`D-2026-09-21-scenario-authoring-semantics`). Its three provisional regions
 * are gone and the versioning fields, the entry kinds and the categories are
 * rendered as settled values. Nothing about them changed; only the marking
 * did.
 *
 * What this screen asks about instead is the execution contract: the four
 * roles, who owns each initial world value and each reporting cadence, how a
 * point and a window are dispatched and bounded, and what to do about two
 * readings the declared causes do not reach.
 *
 * ## Digits
 *
 * Every number on this screen comes from the scenario record, the contract the
 * backend computes from it, or the Site record: a version, an offset, a
 * parameter value, a canonical value, a declared level, a difference. The
 * prose, including every proposal region, contains no digit at all, which is
 * what makes "no invented digit" checkable rather than argued.
 */

/**
 * The event taxonomy, with what each value means.
 *
 * Declared here because a legend is presentation and the frontend has no
 * access to the backend's vocabulary module. What keeps the two from drifting
 * is a pair of assertions rather than a shared import: a backend test asserts
 * the shipped Fuel Loss Event exercises the whole of `EVENT_CATEGORIES` and
 * `TIMELINE_ENTRY_KINDS`, and a frontend test asserts this legend covers every
 * value the rendered record uses. A category added on either side without the
 * other fails one of them.
 */
export const TIMELINE_ENTRY_KIND_LEGEND: ReadonlyArray<
  readonly [string, string]
> = [
  ["EVENT", "Something the simulated world does."],
  ["INTERVENTION", "Something a person does to it, authored in advance."],
  [
    "EVIDENCE_CONDITION",
    "A condition the evidence path is expected to be in, so a later analysis has something to be right or wrong about.",
  ],
];

export const EVENT_CATEGORY_LEGEND: ReadonlyArray<readonly [string, string]> = [
  ["LOAD", "What the site is asked to supply."],
  ["WEATHER", "Conditions the site operates under."],
  [
    "EQUIPMENT",
    "An authored equipment cause, such as a generator being unavailable or dispatched.",
  ],
  ["DATA_QUALITY", "Gaps, delays, or defects in what gets reported."],
  ["LOSS_OR_FRAUD", "Quantities leaving the site unaccounted for."],
  ["INTERVENTION", "An operator or technician acting on the site."],
  ["MAINTENANCE", "Planned work, including scheduled deliveries."],
];

/**
 * The execution roles, with what an executor may do with each.
 *
 * Held to the same rule as the taxonomy legend above: a backend test asserts
 * the shipped definition uses every role, and a frontend test asserts this
 * legend covers every role the rendered record uses.
 */
export const EXECUTION_ROLE_LEGEND: ReadonlyArray<readonly [string, string]> = [
  [
    "CAUSAL_INPUT",
    "Initializes or changes private world state. The only role that may.",
  ],
  [
    "FORCING_INPUT",
    "An exogenous condition the run is put under, on the world or on the reporting path. It names the state it forces and who owns that profile, and it declares no starting value of its own: the profile already says what the state is when the interval begins.",
  ],
  [
    "REPORTED_OBSERVATION",
    "A value arriving through a named source. It never initializes or changes private world state, and it carries no owner that could claim it does.",
  ],
  [
    "NON_EXECUTABLE_CONDITION",
    "Authored description an executor does not consume: what the interval is expected to look like, rather than what it is told to do.",
  ],
];

export interface ScenarioFrameProps {
  catalog: ScenarioCatalogClient;
  scenariosPath: string;
  simulatorLabPath: string;
  /** The operator address of one site. Passed in, because this module may not
   *  decide where an operator surface lives. */
  siteHref: (siteId: string) => string;
  /** Where a run is set up for this scenario. Passed in for the same reason:
   *  this module may not spell a simulator URL. */
  runSetupHref: (scenarioId: string) => string;
}

export function ScenarioFrame({
  catalog,
  scenariosPath,
  simulatorLabPath,
  siteHref,
  runSetupHref,
}: ScenarioFrameProps) {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [result, setResult] = useState<ScenarioDetailResult | null>(null);

  useEffect(() => {
    let active = true;

    if (scenarioId === undefined) {
      setResult({ status: "not_found" });
      return undefined;
    }

    void catalog.getScenario(scenarioId).then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [catalog, scenarioId]);

  const backLinks = (
    <p>
      <Link to={scenariosPath}>Back to Scenarios</Link>{" "}
      <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
    </p>
  );

  if (result === null) {
    return (
      <main aria-labelledby="scenario-heading">
        <PageHeader title="Scenario" headingId="scenario-heading" />
        <p>Loading the saved scenario.</p>
        {backLinks}
      </main>
    );
  }

  if (result.status === "not_found") {
    return (
      <main aria-labelledby="scenario-heading">
        <PageHeader title="Scenario" headingId="scenario-heading" />
        <Panel
          heading="No such saved scenario"
          headingId="scenario-missing-heading"
        >
          <p>
            No scenario with that scenario identity is saved. Scenario
            identities are not site identities, and no site can be addressed
            here.
          </p>
        </Panel>
        {backLinks}
      </main>
    );
  }

  if (result.status === "unavailable") {
    return (
      <main aria-labelledby="scenario-heading">
        <PageHeader title="Scenario" headingId="scenario-heading" />
        <Panel
          heading="Scenario unavailable"
          headingId="scenario-unavailable-heading"
        >
          <p>
            The scenario store could not be read, so this scenario cannot be
            shown. Nothing is known about its content.
          </p>
        </Panel>
        {backLinks}
      </main>
    );
  }

  const {
    scenario,
    targetResolution,
    observationSourceResolutions,
    privateExpectations,
  } = result;
  const contract = scenario.execution_contract;

  return (
    <main aria-labelledby="scenario-heading">
      <PageHeader
        title={scenario.display_name}
        headingId="scenario-heading"
        subtitle="Developer workspace"
        badge={<Badge tone="origin">{scenario.origin}</Badge>}
      />

      <Panel
        heading="What this scenario answers"
        headingId="scenario-purpose-heading"
      >
        <p>{scenario.purpose}</p>
        <p>
          A scenario definition answers what happens during the simulated
          interval. A site&apos;s Foundation answers what the site is. The two
          do not duplicate one another: this scenario declares which site it
          needs, and the site&apos;s own configuration stays the authority on
          what that site is made of.
        </p>
        <p>
          Nothing here has been run. No simulation run exists in this build, so
          this screen reports no outcome and offers no way to produce one.
        </p>
      </Panel>

      <Panel
        heading="Scenario identity and version"
        headingId="scenario-version-heading"
      >
        <FactList>
          <Fact term="Scenario ID">{scenario.scenario_id}</Fact>
          <Fact term="Scenario version">
            {scenario.version.scenario_version}
          </Fact>
          <Fact term="Version valid from">
            {scenario.version.version_valid_from}
          </Fact>
          <Fact term="Supersedes">
            {scenario.version.supersedes === null
              ? "No earlier version"
              : scenario.version.supersedes}
          </Fact>
        </FactList>
      </Panel>

      <Panel heading="Target site" headingId="scenario-target-heading">
        <FactList>
          <Fact term="Target policy">{scenario.target_site.policy}</Fact>
          <Fact term="Declared site">
            {scenario.target_site.site_id ?? "None declared"}
          </Fact>
          <Fact term="Declared template">
            {scenario.target_site.template_id ?? "None declared"}
          </Fact>
          <Fact term="What the scenario needs of it">
            {scenario.target_site.requirement}
          </Fact>
          <Fact term="On this installation">
            {targetResolution.reason}
          </Fact>
        </FactList>

        <ul className="action-list">
          <TargetSiteAction
            resolution={targetResolution}
            siteHref={siteHref}
          />
        </ul>

        <p>
          Opening the target site opens the configured site itself. It does not
          create, rename, clone, or promote one: a scenario declares which site
          it needs and can allocate none.
        </p>
      </Panel>

      <Panel
        heading="How each authored value executes"
        headingId="scenario-roles-heading"
      >
        <p>
          Every value below carries one execution role. The role is what an
          executor is allowed to do with it, and it is a field rather than a
          reading of the wording, so a later run setup does not have to
          interpret a description to know whether a row is a cause or a
          reading.
        </p>

        <FactList>
          {EXECUTION_ROLE_LEGEND.map(([value, gloss]) => (
            <Fact key={value} term={value}>
              {gloss}
            </Fact>
          ))}
        </FactList>

        <p>
          An executable value also names the state it concerns and says whether
          later run setup may proceed without support for it. A required input
          the chosen model profile does not support blocks that run setup
          rather than being quietly left out, because a run that skipped part
          of a scenario would still claim to have executed it.
        </p>

        <ReviewProposal
          id="scenario-execution-roles"
          question="Should every authored value carry one of these four execution roles?"
          proposal={
            <>
              <p>
                Proposed: the four roles above, on every public parameter and
                every timeline row, with only a causal input able to reach
                private world state. That is enforced twice over and not only
                described: a reported reading carries no owner and no state
                effect at all, so there is no field it could arrive in as an
                initial value or a change; and a forcing input, which does have
                an owner, may not declare a starting value either, because the
                profile it names already says what its state is when the
                interval begins.
              </p>
              <p>
                Proposed with it: an evidence condition may be delivered as a
                reported reading or carried as description, and may never be a
                cause. That is the ambiguity this slice exists to remove - one
                row that prescribed both a cause and its own expected result
                would let a scenario author the state trajectory instead of the
                causes.
              </p>
            </>
          }
          settled={
            <>
              The three entry kinds and the seven categories, accepted at the
              previous checkpoint. The roles here are a second axis beside
              them, not a replacement: a row still says what sort of authored
              item it is, and now also says how it executes.
            </>
          }
          onAccepting={
            <>
              These four roles, as the classification later run setup and the
              first kernel are built on.
            </>
          }
          onRedirecting={
            <>
              Naming a role to add, drop, or merge, or a value on this screen
              whose role is wrong.
            </>
          }
        />
      </Panel>

      <Panel
        heading="Scenario-level authoring parameters"
        headingId="scenario-public-parameters-heading"
      >
        <p>
          These are the scenario-level values that say what the simulated world
          will be told to do. They are authoring data, not measurements: a value
          here is an intention, and nothing has reported anything.
        </p>

        {scenario.public_parameters.length > 0 ? (
          <DataTable labelledBy="scenario-public-parameters-heading">
            <thead>
              <tr>
                <th scope="col">Parameter</th>
                <th scope="col">Value</th>
                <th scope="col">In canonical terms</th>
                <th scope="col">Execution role</th>
                <th scope="col">State</th>
                <th scope="col">Owner</th>
                <th scope="col">Parameter ID</th>
              </tr>
            </thead>
            <tbody>
              {scenario.public_parameters.map((parameter) => (
                <tr key={parameter.parameter_id}>
                  <td>{parameter.display_name}</td>
                  <td>{parameterValue(parameter)}</td>
                  <td>{canonicalValue(parameter)}</td>
                  <td>{parameter.execution_role}</td>
                  <td>{parameter.state_key ?? "Not consumed"}</td>
                  <td>{ownershipText(parameter)}</td>
                  <td>{parameter.parameter_id}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : (
          <p>This scenario declares no scenario-level parameter.</p>
        )}
      </Panel>

      <Panel
        heading="Initial world values and who owns them"
        headingId="scenario-initialization-heading"
      >
        <p>
          Every value the simulated world would start from has one owner that
          answers for it. A site&apos;s Foundation owns what the site is; this
          scenario owns what the interval starts from; a run may override
          either; a versioned model rule owns what neither states. A start
          value with no owner is one a recording could invent, which is why
          there is no such option here.
        </p>

        {contract.initialization_inputs.length > 0 ? (
          <DataTable labelledBy="scenario-initialization-heading">
            <thead>
              <tr>
                <th scope="col">World state</th>
                <th scope="col">Starting value</th>
                <th scope="col">In canonical terms</th>
                <th scope="col">Owner</th>
                <th scope="col">Declared by</th>
              </tr>
            </thead>
            <tbody>
              {contract.initialization_inputs.map((input) => (
                <tr key={input.state_key}>
                  <td>{input.state_key}</td>
                  {/*
                    * A value the site's foundation answers for has no number
                    * here and the row says who answers instead of showing a
                    * blank. The unit is still rendered, because what kind of
                    * quantity the site has to answer with is the scenario's
                    * to declare and the row would be unreadable without it.
                    */}
                  <td>
                    {input.value === null
                      ? `${DECLARED_BY_THE_SITE} (${input.unit})`
                      : `${input.value} ${input.unit}`}
                  </td>
                  <td>
                    {input.canonical_value === null
                      ? "Resolved when a run freezes it"
                      : `${input.canonical_value} ${input.canonical_unit}`}
                  </td>
                  <td>{input.owner}</td>
                  <td>{input.display_name}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : (
          <p>This scenario declares no initial world value.</p>
        )}
      </Panel>

      <Panel
        heading="Where each reading comes from"
        headingId="scenario-sources-heading"
      >
        <p>
          Every reading in the timeline arrives through one of these. A device
          source names a device and a signal the target site configures; a
          hand-recorded value names neither, because it did not arrive through
          any configured signal and borrowing one would put an operator&apos;s
          note into the evidence path wearing a sensor&apos;s name.
        </p>

        {scenario.observation_sources.length > 0 ? (
          <DataTable labelledBy="scenario-sources-heading">
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">Kind</th>
                <th scope="col">Device</th>
                <th scope="col">Signal</th>
                <th scope="col">On this installation</th>
                <th scope="col">Who owns the reporting cadence</th>
              </tr>
            </thead>
            <tbody>
              {scenario.observation_sources.map((source) => {
                const resolution = observationSourceResolutions.find(
                  (item) => item.source_id === source.source_id,
                );
                return (
                  <tr key={source.source_id}>
                    <td>
                      {source.source_id}
                      <span className="cell-secondary">
                        {source.description}
                      </span>
                    </td>
                    <td>{source.source_kind}</td>
                    <td>{deviceText(source.device_id, resolution)}</td>
                    <td>{signalText(source.signal_id, resolution)}</td>
                    <td>
                      {resolution?.reason ??
                        "Nothing is known about this source on this installation."}
                    </td>
                    <td>
                      {source.cadence_ownership}
                      <span className="cell-secondary">
                        {resolution?.cadence_statement ??
                          "No statement about this source's cadence is available."}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
        ) : (
          <p>This scenario declares no observation source.</p>
        )}

        <ReviewProposal
          id="scenario-input-ownership"
          question="Who should own an initial world value, and who should own a reporting cadence?"
          proposal={
            <>
              <p>
                Proposed for initial values: exactly one owner each, from the
                site&apos;s Foundation, this scenario, a run override, or a
                versioned model rule, as the table above this one shows. Two
                owners for one value is refused when the definition is read,
                because a run would otherwise start from whichever the code
                happened to consult first.
              </p>
              <p>
                Proposed for cadence: the scenario owns none. A site&apos;s
                Foundation declares that a signal can report and declares its
                unit; it declares no rate, and there is nothing else to derive
                one from. Nothing infers a cadence from a device&apos;s name,
                from what a screen shows, or from the spacing between rows, and
                a duration written onto a reading is refused by name. A cadence
                arrives when a versioned observation profile declares one.
              </p>
              <p>
                A hand-recorded value is a real source with its own identity
                and no device identity, which is what the table above states
                rather than leaving blank.
              </p>
            </>
          }
          settled={
            <>
              Initial conditions must be explicit and attributable, and a trace
              may not hide or invent one. What is being asked here is which
              owners the product recognises and where a cadence comes from,
              not whether attribution is required.
            </>
          }
          onAccepting={
            <>
              These four owners, and a scenario that owns no reporting cadence
              at all.
            </>
          }
          onRedirecting={
            <>
              Naming an owner to add or drop, or saying that a scenario should
              be able to declare how often a source reports.
            </>
          }
        />
      </Panel>

      <Panel
        heading="Event and intervention timeline"
        headingId="scenario-timeline-heading"
      >
        <p>
          The authored items inside this scenario version, in the order the
          definition declares. An offset is measured from the start of the
          simulated interval; when that interval is, how fast it is stepped, and
          what seed it uses are run setup, which does not exist yet.
        </p>

        <DataTable labelledBy="scenario-timeline-heading">
          <thead>
            <tr>
              <th scope="col">Order</th>
              <th scope="col">Offset (minutes)</th>
              <th scope="col">Timing</th>
              <th scope="col">Kind</th>
              <th scope="col">Category</th>
              <th scope="col">Execution role</th>
              <th scope="col">What is authored</th>
              <th scope="col">Parameters</th>
            </tr>
          </thead>
          <tbody>
            {scenario.timeline.map((entry) => (
              <TimelineRow key={entry.event_id} entry={entry} />
            ))}
          </tbody>
        </DataTable>

        <div className="subsection">
          <h3
            className="subsection__heading"
            id="scenario-taxonomy-legend-heading"
          >
            Category and kind legend
          </h3>
          <FactList>
            {TIMELINE_ENTRY_KIND_LEGEND.map(([value, gloss]) => (
              <Fact key={value} term={value}>
                {gloss}
              </Fact>
            ))}
            {EVENT_CATEGORY_LEGEND.map(([value, gloss]) => (
              <Fact key={value} term={value}>
                {gloss}
              </Fact>
            ))}
          </FactList>
        </div>
      </Panel>

      <Panel
        heading="How an entry is dispatched, and what happens at a bound"
        headingId="scenario-dispatch-heading"
      >
        <p>
          These rules are the same for every scenario, so they are versioned
          simulator semantics rather than authoring. They are shown here
          because they are what the timing column above commits the product to.
        </p>

        <FactList>
          <Fact term="Execution contract version">
            {contract.contract_version}
          </Fact>
          {contract.dispatch_rules.map((rule) => (
            <Fact key={rule.rule_id} term={rule.display_name}>
              {rule.statement}
            </Fact>
          ))}
        </FactList>

        <div className="subsection">
          <h3 className="subsection__heading" id="scenario-bounds-heading">
            What a later run does at a bound
          </h3>
          <DataTable labelledBy="scenario-bounds-heading">
            <thead>
              <tr>
                <th scope="col">Case</th>
                <th scope="col">Policy</th>
                <th scope="col">What that means</th>
              </tr>
            </thead>
            <tbody>
              {contract.bound_cases.map((boundCase) => (
                <tr key={boundCase.case_id}>
                  <td>{boundCase.display_name}</td>
                  <td>{boundCase.policy}</td>
                  <td>{boundCase.statement}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </div>

        <ReviewProposal
          id="scenario-timing-and-bounds"
          question="How should an entry be placed in time, and what should happen when a bound is reached?"
          proposal={
            <>
              <p>
                Proposed for timing: an instant, a window with a declared
                length, or the whole interval, validated as three distinct
                shapes. A point with a length and a window without one are both
                refused, because either one looks like a complete definition
                and means something the author did not write. A rate may only
                be declared over a window, since a rate at an instant moves
                nothing.
              </p>
              <p>
                Proposed for dispatch: the run interval and every step are
                half-open, so an instant belongs to exactly one step and an
                entry on a boundary is applied by the step that begins there
                and by no other. Applying something once becomes a property of
                the time model rather than of whichever code reads it.
              </p>
              <p>
                Proposed for bounds: the table above. Every case either refuses
                the definition when it is read, fails the run, or produces a
                bounded change recorded with the quantity it refused. There is
                deliberately no option meaning clamp quietly or drop the
                remainder - a trajectory nothing in the evidence path can
                account for is worse than a run that stops and says why.
              </p>
            </>
          }
          settled={
            <>
              Simulation intervals are half-open, and a scheduled cause is
              applied exactly once. What is being asked is how the shapes above
              realise that, and which bound behaviour is acceptable.
            </>
          }
          onAccepting={
            <>
              These three timing shapes, this boundary rule, and these four
              bound policies.
            </>
          }
          onRedirecting={
            <>
              Naming a shape to add or drop, or a bound case whose policy
              should be different.
            </>
          }
        />
      </Panel>

      <Panel
        heading="The readings, against the causes declared before them"
        headingId="scenario-reconciliation-heading"
      >
        <p>
          Neither reading below prescribes what the simulated world holds. Each
          is a value from a named source, and neither appears among the inputs
          that start or change private world state. What this table adds is the
          other half: whether the causes this scenario declares actually reach
          the value the source reports.
        </p>
        <p>
          The declared column is arithmetic over the authored causes that are
          complete by that offset, in canonical units. It computes no
          trajectory, holds no state, and changes nothing. Where it differs
          from the reported value, the difference is stated with its sign
          rather than left for a reader to work out.
        </p>
        <p>
          Where it cannot answer it says so and says why, rather than
          reporting a number the contract refuses elsewhere. There are three
          such cases and each is a different fact: no declared starting value
          for the state, a declared cause still running when the reading is
          taken, and a declared cause that would take the state past a bound
          this definition declares. Working out what a run does at a bound is
          the runtime&apos;s, not this screen&apos;s.
        </p>

        {contract.observation_reconciliation.length > 0 ? (
          <DataTable labelledBy="scenario-reconciliation-heading">
            <thead>
              <tr>
                <th scope="col">Reading</th>
                <th scope="col">Source</th>
                <th scope="col">Offset (minutes)</th>
                <th scope="col">Reported</th>
                <th scope="col">Declared causes reach</th>
                <th scope="col">Difference</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {contract.observation_reconciliation.map((item) => (
                <tr key={item.event_id}>
                  <td>{item.event_id}</td>
                  <td>{item.source_id}</td>
                  <td>{item.offset_minutes}</td>
                  <td>{`${item.reported_value} ${item.unit}`}</td>
                  <td>
                    {amount(item.declared_value, item.unit)}
                    <span className="cell-secondary">
                      {accountedByText(item)}
                    </span>
                  </td>
                  <td>{amount(item.difference, item.unit)}</td>
                  <td>
                    {item.state}
                    <span className="cell-secondary">{item.reason}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : (
          <p>This scenario authors no reading to reconcile.</p>
        )}

        <ReviewProposal
          id="scenario-observation-reconciliation"
          question="What should happen when the declared causes do not reach a reported reading?"
          proposal={
            <>
              <p>
                Proposed: state it, with the quantity and the sign, and do not
                resolve it in code. The two readings this scenario authors are
                reported observations from a named source, so neither can
                prescribe tank state and the contract is coherent as it stands.
                What it also has to say out loud is that the causes it declares
                do not reach either of them.
              </p>
              <p>
                Deliberately not done: adjusting any authored number so that
                the two sides agree. The values on this screen are the ones the
                previous checkpoint accepted, and editing them into agreement
                would settle a product question by arithmetic rather than by
                review.
              </p>
              <p>
                There are three honest ways out and they are yours to choose
                between: model the missing cause as its own causal entry;
                declare a reporting behaviour that explains the difference; or
                accept the authored readings and change the causes. Until one
                is chosen, a later run setup should treat an unreached reading
                as a reason to block rather than as a rounding matter.
              </p>
            </>
          }
          settled={
            <>
              A scenario authors causes and conditions, not the state
              trajectory they produce, and a reported value is never private
              world truth. Both readings are already classified that way and
              neither reaches an initial value or a state change.
            </>
          }
          onAccepting={
            <>
              The contract stating the difference rather than hiding it, with
              the resolution left to a later slice you direct.
            </>
          }
          onRedirecting={
            <>
              Naming which of the three ways out to take, or saying that a
              difference of this size should be tolerated and why.
            </>
          }
        />
      </Panel>

      <Panel
        heading="Private test-oracle expectations"
        headingId="scenario-private-heading"
      >
        <div className="private-region" data-private-region="expectations">
          <p>
            This is developer metadata, not product content. It says what a
            later test should be able to conclude about a run of this scenario.
            It is parsed into a field of its own and served in a section of its
            own, and no operator route, evidence payload, export, site page or
            provenance record receives it.
          </p>

          {privateExpectations.length > 0 ? (
            <DataTable labelledBy="scenario-private-heading">
              <thead>
                <tr>
                  <th scope="col">Expectation</th>
                  <th scope="col">Oracle kind</th>
                  <th scope="col">What a later test must be able to show</th>
                </tr>
              </thead>
              <tbody>
                {privateExpectations.map((expectation) => (
                  <tr key={expectation.expectation_id}>
                    <td>{expectation.display_name}</td>
                    <td>{expectation.oracle_kind}</td>
                    <td>{expectation.statement}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          ) : (
            <p>This scenario declares no expectation.</p>
          )}
        </div>
      </Panel>

      <Panel
        heading="What can be done with this scenario"
        headingId="scenario-actions-heading"
      >
        <ul className="action-list">
          <li className="action-list__item">
            {targetResolution.state === "RESOLVED" &&
            targetResolution.site_id !== null ? (
              <>
                <Link
                  className="action"
                  to={runSetupHref(scenario.scenario_id)}
                >
                  Create Draft Run
                </Link>
                <p className="action-list__reason">
                  Setting a run up freezes the inputs a simulation would
                  consume and creates a draft. It does not execute anything.
                </p>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="action"
                  disabled
                  aria-describedby="scenario-run-reason"
                >
                  Create Draft Run
                </button>
                <p className="action-list__reason" id="scenario-run-reason">
                  {targetResolution.reason} A run is bound to a concrete site
                  and to the exact version of its foundation, so there is
                  nothing to freeze until that site is configured here.
                </p>
              </>
            )}
          </li>
        </ul>
      </Panel>

      {backLinks}
    </main>
  );
}

/**
 * The one product bridge on this screen.
 *
 * Enabled only when the declared target site resolves, and then it is a link
 * to the configured site rather than a button, because following it is
 * navigation. In every other state it is a disabled control carrying the
 * reason the backend produced, so the screen and the API cannot describe the
 * same state differently.
 *
 * `disabled` is the real attribute rather than `aria-disabled`, because the
 * claim is the true one: the control does nothing. The reason is rendered
 * beside it and tied to it with `aria-describedby`, since a disabled button
 * takes no focus and a tooltip on one is a reason a keyboard cannot reach.
 */
function TargetSiteAction({
  resolution,
  siteHref,
}: {
  resolution: ScenarioTargetResolution;
  siteHref: (siteId: string) => string;
}) {
  if (resolution.state === "RESOLVED" && resolution.site_id !== null) {
    return (
      <li className="action-list__item">
        <Link className="action" to={siteHref(resolution.site_id)}>
          Open target site
        </Link>
        <p className="action-list__reason">{resolution.reason}</p>
      </li>
    );
  }

  return (
    <li className="action-list__item">
      <button
        type="button"
        className="action"
        disabled
        aria-describedby="scenario-target-reason"
      >
        Open target site
      </button>
      <p className="action-list__reason" id="scenario-target-reason">
        {resolution.reason}
      </p>
    </li>
  );
}

function TimelineRow({ entry }: { entry: ScenarioTimelineEntry }) {
  return (
    <tr>
      <td>{entry.sequence}</td>
      <td>{entry.offset_minutes}</td>
      <td>
        {entry.timing.shape}
        {entry.timing.duration_minutes === null ? null : (
          <span className="cell-secondary">
            {`${entry.timing.duration_minutes} min`}
          </span>
        )}
      </td>
      <td>{entry.entry_kind}</td>
      <td>{entry.category}</td>
      <td>
        {entry.execution_role}
        <span className="cell-secondary">{executionDetail(entry)}</span>
      </td>
      <td>
        {entry.description}
        <span className="cell-secondary">{entry.event_id}</span>
      </td>
      <td>
        {entry.parameters.length === 0 ? (
          "None declared"
        ) : (
          <ul className="cell-list">
            {entry.parameters.map((parameter) => (
              <li key={parameter.parameter_id}>
                {parameter.display_name}: {parameterValue(parameter)}
                <span className="cell-secondary">
                  {parameter.execution_role}
                </span>
              </li>
            ))}
          </ul>
        )}
      </td>
    </tr>
  );
}

/**
 * What an entry's role actually does, in the entry's own terms.
 *
 * A cause says which state it moves and which way; a reading says which source
 * it came through; a forcing input says what it forces. Description says it is
 * not consumed, rather than leaving the cell blank: a blank cell reads as
 * missing data, and this is a fact.
 */
function executionDetail(entry: ScenarioTimelineEntry): string {
  if (entry.state_effect !== null && entry.state_key !== null) {
    const direction =
      entry.state_effect.direction === "INCREASE" ? "raises" : "lowers";
    return `${direction} ${entry.state_key}`;
  }
  if (entry.observation !== null) {
    return `reported through ${entry.observation.source_id}`;
  }
  if (entry.state_key !== null) {
    return `forces ${entry.state_key}`;
  }
  return "not consumed by an executor";
}

/**
 * What a parameter the site's foundation answers for shows instead of a number.
 *
 * Not a dash and not a blank cell. The scenario has not omitted this value: it
 * declares that it is not the scenario's to state, and the unit beside it says
 * what kind of quantity a site has to answer with.
 */
export const DECLARED_BY_THE_SITE = "Declared by the site's foundation";

/**
 * How a parameter reads.
 *
 * A number always carries its unit, because a quantity without one cannot be
 * read; a text parameter has no unit and gets none appended, because a unit on
 * a phrase would make the phrase look like a quantity. A parameter with no
 * number says who answers for it, with the unit it will be answered in.
 */
function parameterValue(parameter: ScenarioParameter): string {
  if (parameter.value === null) {
    return `${DECLARED_BY_THE_SITE} (${parameter.unit})`;
  }
  return parameter.unit === null
    ? String(parameter.value)
    : `${parameter.value} ${parameter.unit}`;
}

/** The same quantity in canonical terms, or why there is none. */
function canonicalValue(parameter: ScenarioParameter): string {
  if (parameter.canonical !== null) {
    return `${parameter.canonical.value} ${parameter.canonical.unit}`;
  }
  // Two different reasons there is no canonical form, and they are not the
  // same fact. A phrase is not a quantity at all; a foundation-owned value is
  // a quantity nobody has answered with yet, and saying it was not one would
  // be wrong about the only thing this row is for.
  return parameter.value === null
    ? "Resolved when a run freezes it"
    : "Not a quantity";
}

/**
 * Who owns a parameter, as one phrase.
 *
 * A reported value says so explicitly rather than rendering an empty cell.
 * That it owns nothing is the guarantee this screen is here to show, and an
 * empty cell would read as a field somebody forgot to fill.
 */
function ownershipText(parameter: ScenarioParameter): string {
  if (parameter.ownership === null) {
    return parameter.execution_role === "REPORTED_OBSERVATION"
      ? "Reported, so it owns nothing"
      : "Not consumed, so it owns nothing";
  }
  return parameter.ownership.initializes
    ? `${parameter.ownership.owner}, starting value`
    : `${parameter.ownership.owner}, used by a change`;
}

function deviceText(
  deviceId: string | null,
  resolution: ScenarioObservationSourceResolution | undefined,
): string {
  if (deviceId === null) {
    return "No device";
  }
  return resolution?.device_display_name === undefined ||
    resolution.device_display_name === null
    ? deviceId
    : `${deviceId}, ${resolution.device_display_name}`;
}

function signalText(
  signalId: string | null,
  resolution: ScenarioObservationSourceResolution | undefined,
): string {
  if (signalId === null) {
    return "No signal";
  }
  return resolution?.signal_display_name === undefined ||
    resolution.signal_display_name === null
    ? signalId
    : `${signalId}, ${resolution.signal_display_name}`;
}

/** A quantity the contract could compute, or a statement that it could not. */
function amount(value: number | null, unit: string): string {
  return value === null ? "Cannot be worked out" : `${value} ${unit}`;
}

function accountedByText(item: ScenarioObservationReconciliation): string {
  if (item.accounted_by.length === 0) {
    return "no declared cause is complete by this offset";
  }
  return `counting ${item.accounted_by.join(", ")}`;
}
