import type { SiteDetailClient } from "./siteDirectoryClient";
import type { SiteDetailReadModel } from "./siteReadModel";
import { useSiteRecord } from "./useSiteRecord";
import {
  deriveSiteConfigurationView,
  type SiteComponentView,
  type SiteUnavailableFact,
} from "./siteViewModel";

/**
 * One site's configuration, presented from the shared substrate.
 *
 * This is the same shared-region rule the site page follows. A shell composes
 * it, supplies the landmark around it, and adds beside it; there is no
 * `variant`, `mode`, `shell`, or `isLab` prop, no import of shell code,
 * simulator code, or the feature flag, and no extension slot, because nothing
 * fills one in this slice.
 *
 * A site is addressed by `site_id` and by nothing else. Neither the foundation
 * version nor the template a site was created from addresses it, and nothing
 * on this screen changes it.
 *
 * What this surface shows is the configuration document, read back. It is
 * component truth declared by that document and never evidence: that a
 * foundation declares a 100 kW array is not a claim that any array exists, is
 * commissioned, or has ever reported a measurement.
 *
 * What it deliberately does not show:
 *
 * - No action control of any kind, in any state, absent from the DOM rather
 *   than rendered disabled. M1 has decided configuration is fixed at creation,
 *   so a greyed-out control would promise a capability the product has
 *   declined to have, and `Version History` would name a future capability
 *   wrongly: no configuration-change model exists, and the eventual shape of
 *   that territory is an auditable intervention record, which is a different
 *   thing.
 * - No single line diagram, no empty frame reserved for one, and no signal
 *   selector. The configured diagram is a later causal step, and a hole in the
 *   layout labelled for it would claim a step that has not landed.
 * - No telemetry, chart, series, gauge, count, source health, or analytics. A
 *   configuration-only site has no evidence, and a zero is a measurement claim
 *   rather than an absence.
 * - No device, signal mapping, or control assumption rendered as content. The
 *   M1 foundation declares none, and each is stated as undeclared with its
 *   reason rather than rendered as an empty list, which would say this site
 *   has none.
 */
export const SITE_CONFIGURATION_HEADING_ID = "site-configuration-heading";

export interface SiteConfigurationProps {
  /** The identity taken from the address. `undefined` names no site. */
  siteId: string | undefined;
  detail: SiteDetailClient;
}

export function SiteConfiguration({ siteId, detail }: SiteConfigurationProps) {
  const result = useSiteRecord(siteId, detail);

  if (result === null) {
    return (
      <>
        <h1 id={SITE_CONFIGURATION_HEADING_ID}>Site configuration</h1>
        <p>Loading the configured site.</p>
      </>
    );
  }

  if (result.status === "not_found") {
    return (
      <>
        <h1 id={SITE_CONFIGURATION_HEADING_ID}>Site not found</h1>
        <section aria-labelledby="site-configuration-not-found-heading">
          <h2 id="site-configuration-not-found-heading">No such site</h2>
          <p>
            No site with that site ID is configured, so there is no
            configuration to read. A site is addressed by its site ID and by
            nothing else, so it cannot be reached by its name or by the
            template it was created from.
          </p>
          <p>
            This is a statement that the site does not exist, not a site with
            nothing configured in it.
          </p>
        </section>
      </>
    );
  }

  if (result.status === "unavailable") {
    return (
      <>
        <h1 id={SITE_CONFIGURATION_HEADING_ID}>Site configuration</h1>
        <section aria-labelledby="site-configuration-unavailable-heading">
          <h2 id="site-configuration-unavailable-heading">Site unavailable</h2>
          <p>
            The site store could not be read, so this site&apos;s configuration
            cannot be shown. This is a statement about the store: nothing is
            known about whether the site is configured.
          </p>
        </section>
      </>
    );
  }

  return <SiteConfigurationFacts site={result.site} />;
}

/**
 * The configuration itself, rendered from one record.
 *
 * Split out so the rendering can be exercised directly over records, with no
 * client, no router, and no shell in the way.
 */
export interface SiteConfigurationFactsProps {
  site: SiteDetailReadModel;
}

export function SiteConfigurationFacts({ site }: SiteConfigurationFactsProps) {
  const view = deriveSiteConfigurationView(site);

  return (
    <>
      <h1 id={SITE_CONFIGURATION_HEADING_ID}>Site configuration</h1>

      <section aria-labelledby="site-configuration-identity-heading">
        <h2 id="site-configuration-identity-heading">Site</h2>
        <dl>
          <dt>Site ID</dt>
          <dd>{view.siteId}</dd>
          <dt>Name</dt>
          <dd>{view.displayName}</dd>
          <dt>Type</dt>
          <dd>{view.siteType}</dd>
          <dt>Location</dt>
          <dd>{view.location}</dd>
          <dt>Timezone</dt>
          <dd>{view.timezone}</dd>
        </dl>
      </section>

      <section aria-labelledby="site-configuration-fixed-heading">
        <h2 id="site-configuration-fixed-heading">
          Configuration is fixed at creation
        </h2>
        <p>{view.configurationFixedAtCreation}</p>
      </section>

      <section aria-labelledby="site-configuration-provenance-heading">
        <h2 id="site-configuration-provenance-heading">
          Provenance and status
        </h2>
        <dl>
          <dt>Lifecycle status</dt>
          <dd>{view.lifecycleStatus}</dd>
          <dt>Mode</dt>
          <dd>{view.sourceMode}</dd>
          <dt>Configuration origin</dt>
          <dd>{view.configurationOrigin}</dd>
          <dt>Created from template</dt>
          <dd>{view.templateProvenance}</dd>
        </dl>
        <p>
          These are separate facts about a site and none is derived from
          another. Configuration origin is where this site&apos;s configuration
          document came from. Mode is where the site&apos;s evidence comes
          from, and it is provenance rather than status, health, or an
          assessment. Lifecycle status is where the site is in its own life.
        </p>
      </section>

      <section aria-labelledby="site-configuration-foundation-heading">
        <h2 id="site-configuration-foundation-heading">Foundation</h2>
        <dl>
          <dt>Foundation version</dt>
          <dd>{view.foundationVersion}</dd>
          <dt>Valid from</dt>
          <dd>{view.foundationValidFrom}</dd>
          <dt>Summary</dt>
          <dd>{view.foundationSummary}</dd>
        </dl>
        <p>{view.foundationValiditySemantics}</p>
      </section>

      <SiteConfigurationComponents components={view.components} />

      <section aria-labelledby="site-configuration-undeclared-heading">
        <h2 id="site-configuration-undeclared-heading">
          Not declared in this foundation
        </h2>
        <dl>
          <SiteConfigurationStatedAbsence name="Devices" fact={view.devices} />
          <SiteConfigurationStatedAbsence
            name="Signal mappings"
            fact={view.signalMappings}
          />
          <SiteConfigurationStatedAbsence
            name="Control assumptions"
            fact={view.controlAssumptions}
          />
        </dl>
      </section>

      <section aria-labelledby="site-configuration-no-evidence-heading">
        <h2 id="site-configuration-no-evidence-heading">
          Not available for this site
        </h2>
        <dl>
          <SiteConfigurationStatedAbsence
            name="Integration readiness"
            fact={view.integrationReadiness}
          />
          <SiteConfigurationStatedAbsence
            name="Evidence availability"
            fact={view.evidenceAvailability}
          />
          <SiteConfigurationStatedAbsence
            name="Source health"
            fact={view.sourceHealth}
          />
        </dl>
        <p>
          Nothing below the configuration exists for this site yet. There is no
          accepted evidence, so there is nothing to chart, nothing to analyse,
          nothing to replay, and no finding to draw. Each of those arrives with
          the evidence that fills it rather than as an empty version of itself.
        </p>
      </section>
    </>
  );
}

/**
 * The components the foundation declares.
 *
 * A rating here is the archetype's declared design rating, copied from
 * the template at creation. It is nameplate intent from a document, so the
 * column says declared and never shares a column with anything a device could
 * report.
 */
export interface SiteConfigurationComponentsProps {
  components: SiteComponentView[];
}

export function SiteConfigurationComponents({
  components,
}: SiteConfigurationComponentsProps) {
  return (
    <section aria-labelledby="site-configuration-components-heading">
      <h2 id="site-configuration-components-heading">Components</h2>
      <table>
        <caption>
          The components this site&apos;s foundation declares, with the design
          ratings declared for them. These are configuration, not measurements:
          nothing here states that a device exists, is commissioned, or has
          ever reported.
        </caption>
        <thead>
          <tr>
            <th scope="col">Component</th>
            <th scope="col">Type</th>
            <th scope="col">Declared rating</th>
            <th scope="col">Component ID</th>
          </tr>
        </thead>
        <tbody>
          {components.map((component) => (
            <tr key={component.componentId}>
              <td>{component.displayName}</td>
              <td>{component.componentType}</td>
              <td>{component.rating}</td>
              <td>{component.componentId}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

/**
 * One thing this screen does not state, with the reason it does not.
 *
 * The reason is rendered next to the value every time. "Not declared" on its
 * own reads as a fact about the site; with its reason it reads as what it is,
 * a statement about what the configuration document carries.
 */
export interface SiteConfigurationStatedAbsenceProps {
  name: string;
  fact: SiteUnavailableFact;
}

export function SiteConfigurationStatedAbsence({
  name,
  fact,
}: SiteConfigurationStatedAbsenceProps) {
  return (
    <>
      <dt>{name}</dt>
      <dd>
        {fact.value}. {fact.reason}
      </dd>
    </>
  );
}
