import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { DataTable, PageHeader, Panel } from "../ui";
import type {
  ScenarioCatalogClient,
  ScenarioListResult,
} from "./scenarioCatalogClient";

/**
 * The scenario catalog, a Simulator Lab developer-workspace surface.
 *
 * Served only when `simulator_lab.enabled` is true. It is not an operator
 * screen and nothing it lists is a Site: a scenario has a `scenario_id`, a
 * scenario version and a declared target, and none of those is Site identity.
 *
 * Every value here comes from a scenario document. There is no create,
 * duplicate, import, upload, edit, delete, approve, publish, or run control,
 * enabled or disabled: nothing in this slice can produce or execute a
 * scenario, so a control implying otherwise would be a promise the product
 * cannot keep. The client this screen is built on has no method for any of
 * them either.
 *
 * The target column states what each scenario declares it needs, and does not
 * say whether that Site is configured. Resolving a declared target is a read
 * against the Site store, and the catalog does not make one: a listing that
 * claimed a Site resolved would be reporting on a different installation's
 * state than the one it looked at.
 *
 * The unavailable state is stated rather than rendered as an empty catalog,
 * because "no scenario is saved" and "the store could not be read" are
 * different facts.
 *
 * Paths arrive as props. This module must not spell a simulator URL: the
 * single chokepoint in `simulatorLabRoutes.tsx` is what keeps a Lab surface
 * from being addressable outside the gate.
 */
export interface ScenariosFrameProps {
  catalog: ScenarioCatalogClient;
  scenarioHref: (scenarioId: string) => string;
  simulatorLabPath: string;
}

export function ScenariosFrame({
  catalog,
  scenarioHref,
  simulatorLabPath,
}: ScenariosFrameProps) {
  const [result, setResult] = useState<ScenarioListResult | null>(null);

  useEffect(() => {
    let active = true;

    void catalog.listScenarios().then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [catalog]);

  const saved = result?.status === "loaded" ? result.scenarios : [];

  return (
    <main aria-labelledby="scenarios-heading">
      <PageHeader
        title="Scenarios"
        headingId="scenarios-heading"
        subtitle="Developer workspace"
      />

      <Panel
        heading="A scenario is not a site, and not a run"
        headingId="scenarios-not-a-site-heading"
      >
        <p>
          A scenario definition says what happens during a simulated interval.
          A site&apos;s Foundation says what the site is. The two do not
          duplicate one another: a scenario declares which site it needs, and
          that is the whole of the relationship.
        </p>
        <p>
          Nothing here has been run. No simulation run exists in this build, so
          nothing on this screen reports an outcome, and nothing on it creates,
          changes, or removes anything.
        </p>
      </Panel>

      <Panel
        heading="Saved scenarios"
        headingId="scenarios-catalog-heading"
        flush={saved.length > 0}
      >
        {result === null ? <p>Loading saved scenarios.</p> : null}

        {result?.status === "unavailable" ? (
          <p>
            The scenario store could not be read, so no scenario can be listed.
            This is a statement about the store, not a statement that none is
            saved.
          </p>
        ) : null}

        {result?.status === "loaded" && saved.length === 0 ? (
          <p>No scenario is saved.</p>
        ) : null}

        {saved.length > 0 ? (
          <DataTable labelledBy="scenarios-catalog-heading">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Scenario ID</th>
                <th scope="col">Version</th>
                <th scope="col">Origin</th>
                <th scope="col">Declared target site</th>
                <th scope="col">Purpose</th>
              </tr>
            </thead>
            <tbody>
              {saved.map((scenario) => (
                <tr key={scenario.scenario_id}>
                  <td>
                    <Link to={scenarioHref(scenario.scenario_id)}>
                      {scenario.display_name}
                    </Link>
                  </td>
                  <td>{scenario.scenario_id}</td>
                  <td>{scenario.version.scenario_version}</td>
                  <td>{scenario.origin}</td>
                  <td>
                    {scenario.target_site.site_id ??
                      scenario.target_site.template_id ??
                      "Not declared"}
                  </td>
                  <td>{scenario.purpose}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : null}
      </Panel>

      <p>
        <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
      </p>
    </main>
  );
}
