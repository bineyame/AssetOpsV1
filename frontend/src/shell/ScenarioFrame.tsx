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
  ScenarioParameter,
  ScenarioTargetResolution,
  ScenarioTimelineEntry,
} from "./scenarioCatalogClient";

/**
 * Read-only inspection of one saved ScenarioDefinition, and the M1B
 * user-review checkpoint.
 *
 * ## What this screen says, and what it refuses to say
 *
 * It says what a simulated interval is intended to do. It does not say that
 * AssetOps has observed anything: no run exists in this build, so there is no
 * outcome, no accepted evidence, no source health, no confidence, no severity,
 * no incident, no action, no verification outcome and no product conclusion
 * anywhere on it, and no control that would produce one.
 *
 * Two controls are rendered, and the rule for which
 * (`D-2026-09-20-scenario-detail-affordances`) is that a disabled control
 * appears only when the action is native to the object being viewed and the
 * missing prerequisite is the next named causal capability. `Create Draft Run`
 * is native to a scenario and is rendered disabled with the prerequisite named.
 * `Open target Site` is the one product bridge, enabled only when the declared
 * target resolves. Everything downstream - commit, release, ingestion, replay,
 * runtime controls, gateway output, product analytics - belongs to another
 * object or another lifecycle, so it is absent rather than disabled: a
 * disabled control from a later step teaches the wrong object model.
 *
 * ## The three provisional proposals
 *
 * This is a checkpoint screen, and a checkpoint screen has to make accepting it
 * a decision. Each `ReviewProposal` region states one question, this project's
 * proposal, what is already settled, and what accepting or redirecting would
 * mean. None of them offers a menu: the last checkpoint that did settled
 * nothing.
 *
 * ## Digits
 *
 * Every number on this screen comes from the scenario record or the Site
 * record: a version, a supersedes, an offset, a parameter value. The prose,
 * including all three proposal regions, contains no digit at all, which is what
 * makes "no invented digit" checkable rather than argued.
 */

/**
 * The proposed event taxonomy, with what each value means.
 *
 * Declared here because a legend is presentation and the frontend has no
 * access to the backend's vocabulary module. What keeps the two from drifting
 * is a pair of assertions rather than a shared import: a backend test asserts
 * the shipped Fuel Loss Event exercises the whole of `EVENT_CATEGORIES` and
 * `TIMELINE_ENTRY_KINDS`, and a frontend test asserts this legend covers every
 * value the rendered record uses. A category added on either side without the
 * other fails one of them.
 */
export const PROPOSED_TIMELINE_ENTRY_KINDS: ReadonlyArray<
  readonly [string, string]
> = [
  ["EVENT", "Something the simulated world does."],
  ["INTERVENTION", "Something a person does to it, authored in advance."],
  [
    "EVIDENCE_CONDITION",
    "A condition the evidence path is expected to be in, so a later analysis has something to be right or wrong about.",
  ],
];

export const PROPOSED_EVENT_CATEGORIES: ReadonlyArray<
  readonly [string, string]
> = [
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

export interface ScenarioFrameProps {
  catalog: ScenarioCatalogClient;
  scenariosPath: string;
  simulatorLabPath: string;
  /** The operator address of one site. Passed in, because this module may not
   *  decide where an operator surface lives. */
  siteHref: (siteId: string) => string;
}

export function ScenarioFrame({
  catalog,
  scenariosPath,
  simulatorLabPath,
  siteHref,
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

  const { scenario, targetResolution, privateExpectations } = result;

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

        <ReviewProposal
          id="scenario-versioning"
          question="Which fields should a scenario version carry?"
          proposal={
            <>
              <p>
                Proposed: the four above. A scenario identity that never
                changes; a scenario version, which is the thing a future run
                freezes; the instant that version became the authored one; and
                the version it superseded, so drift between versions stays
                inspectable without a separate history store.
              </p>
              <p>
                Deliberately not proposed: a lifecycle state such as draft or
                released, an author, or a change note. None of them has a
                capability behind it in this milestone, and a field with nothing
                to fill it invites a screen to state something nobody recorded.
              </p>
            </>
          }
          settled={
            <>
              Scenario identity and scenario version are distinct; a version a
              run has referenced is immutable; timeline identities are stable
              within a version; and a future run freezes the concrete version it
              used rather than following the latest.
            </>
          }
          onAccepting={
            <>
              This field list, as the version identity run setup will be built
              on.
            </>
          }
          onRedirecting={
            <>
              Naming which field to add or drop, before run setup is built
              against it.
            </>
          }
        />
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
        heading="Public authoring parameters"
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
                <th scope="col">Parameter ID</th>
              </tr>
            </thead>
            <tbody>
              {scenario.public_parameters.map((parameter) => (
                <tr key={parameter.parameter_id}>
                  <td>{parameter.display_name}</td>
                  <td>{parameterValue(parameter)}</td>
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
              <th scope="col">Kind</th>
              <th scope="col">Category</th>
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
            {PROPOSED_TIMELINE_ENTRY_KINDS.map(([value, gloss]) => (
              <Fact key={value} term={value}>
                {gloss}
              </Fact>
            ))}
            {PROPOSED_EVENT_CATEGORIES.map(([value, gloss]) => (
              <Fact key={value} term={value}>
                {gloss}
              </Fact>
            ))}
          </FactList>
        </div>

        <ReviewProposal
          id="scenario-event-taxonomy"
          question="What should the scenario event taxonomy be?"
          proposal={
            <>
              <p>
                Proposed: two axes, both closed. Every timeline row has a kind
                and a category, and the legend above is the whole of both. The
                parser refuses any other value, so an unsupported category
                cannot reach a screen, a run, or a simulator.
              </p>
              <p>
                Deliberately absent: breaker position and control mode. An
                equipment or intervention row names an authored cause or action
                in words and in its parameters; a position or a mode is a
                time-scoped operational fact, which in this project means
                evidence. A check fails the build if one becomes a kind, a
                category, a parameter key, or a unit, in the model, in the
                shipped definition, or in a test fixture.
              </p>
            </>
          }
          settled={
            <>
              Timeline rows are authored sub-artifacts inside a scenario
              version, addressed by scenario identity, version and event
              identity. A future runtime injection is a run-scoped record under
              a simulation run and is never written back into a scenario
              version. Breaker position and control mode are evidence, not
              configuration and not scenario schema.
            </>
          }
          onAccepting={<>These kinds and these categories, as the closed taxonomy.</>}
          onRedirecting={
            <>Naming a category or kind to add, drop, merge, or rename.</>
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

        <ReviewProposal
          id="scenario-public-private-boundary"
          question="Which scenario data is public authoring data, and which is a private test-oracle expectation?"
          proposal={
            <>
              <p>
                Proposed: everything that describes what the simulated world
                does is public authoring data. That is the identity, the
                version, the target-site requirement, the parameters above the
                timeline, and every timeline row with its kind, category,
                offset, description and parameters.
              </p>
              <p>
                Everything that describes what a later test should be able to
                conclude is a private expectation: the region directly above,
                and nothing else.
              </p>
              <p>
                The split is in the parser, not in this screen. The two halves
                are separate parsed fields with separate payload builders, and
                the builders that produce the public sections never read the
                private field, so no operator surface can receive one by
                omission or by a screen forgetting to filter.
              </p>
            </>
          }
          settled={
            <>
              A private expectation is test-oracle metadata only. It is never
              pipeline input, product evidence, operator content, an export, an
              analytic, or product provenance.
            </>
          }
          onAccepting={
            <>
              This boundary, as the contract run setup and the evidence path
              will be built against.
            </>
          }
          onRedirecting={
            <>
              Naming a value on this screen that belongs on the other side of
              the line.
            </>
          }
        />
      </Panel>

      <Panel
        heading="What can be done with this scenario"
        headingId="scenario-actions-heading"
      >
        <ul className="action-list">
          <li className="action-list__item">
            <button
              type="button"
              className="action"
              disabled
              aria-describedby="scenario-run-reason"
            >
              Create Draft Run
            </button>
            <p className="action-list__reason" id="scenario-run-reason">
              Run setup does not exist yet. Creating a draft simulation run
              needs a run setup surface and a draft simulation run record, and
              this build has neither, so there is nothing for this control to
              do.
            </p>
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
      <td>{entry.entry_kind}</td>
      <td>{entry.category}</td>
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
              </li>
            ))}
          </ul>
        )}
      </td>
    </tr>
  );
}

/**
 * How a parameter reads.
 *
 * A number always carries its unit, because a quantity without one cannot be
 * read; a text parameter has no unit and gets none appended, because a unit on
 * a phrase would make the phrase look like a quantity.
 */
function parameterValue(parameter: ScenarioParameter): string {
  return parameter.unit === null
    ? String(parameter.value)
    : `${parameter.value} ${parameter.unit}`;
}
