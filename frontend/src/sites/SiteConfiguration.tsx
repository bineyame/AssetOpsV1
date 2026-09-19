import type { ReactNode } from "react";

import {
  Badge,
  Breadcrumbs,
  DataTable,
  Fact,
  FactList,
  PageHeader,
  Panel,
  type Crumb,
} from "../ui";
import {
  FOUNDATION_CONTROLS_ID,
  FOUNDATION_DEFINITION_ID,
  FOUNDATION_TOPOLOGY_ID,
  FoundationSubtabs,
} from "./FoundationSubtabs";
import type { SiteKeyParameterView } from "./siteViewModel";
import type { SiteDetailClient } from "./siteDirectoryClient";
import type { SiteDetailReadModel } from "./siteReadModel";
import { useSiteRecord } from "./useSiteRecord";
import {
  deriveSiteConfigurationView,
  type SiteComponentView,
  type SiteUnavailableFact,
} from "./siteViewModel";

/**
 * One site's Foundation, presented from the shared substrate.
 *
 * Foundation is the product name of this surface, from v6.9's operator Site
 * tab row. Configuration is the domain word underneath it: the document a site
 * was created from, its configuration origin, and the rule that configuration
 * is fixed at creation. So the heading says Foundation and the content still
 * says configuration where configuration is what it means.
 *
 * The module, the component and the heading id deliberately still say
 * `SiteConfiguration`. T011A renamed what a reader sees and what an address
 * says; renaming these would touch every test in this directory and both
 * single-definition guard patterns without changing one rendered character.
 *
 * This is the same shared-region rule the site page follows. A shell composes
 * it, supplies the landmark around it, and hands it chrome to place; there is
 * no `variant`, `mode`, `shell`, or `isLab` prop and no import of shell code,
 * simulator code, or the feature flag. The one extension slot, `tabs`, is
 * named, optional, and opaque: this component decides where it renders and
 * never what is in it.
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
 * - No tab row of its own. The operator shell hands one in through `tabs`,
 *   and this component decides only where such a row goes: under the page
 *   header, above the facts, and only for a site it actually loaded.
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
  /**
   * Chrome the composing shell places under the page header. Nothing renders
   * when it is absent, and nothing here reads what is in it.
   */
  tabs?: ReactNode;
  /**
   * The trail above this page, built by the shell from the canonical
   * `site_id`. Foundation sits two levels down, so its parent is the Site
   * itself, and the Site's crumb has to be spelled the way the record spells
   * it rather than the way the address did.
   */
  parentTrail?: (siteId: string) => Crumb[];
}

export function SiteConfiguration({
  siteId,
  detail,
  tabs,
  parentTrail,
}: SiteConfigurationProps) {
  const result = useSiteRecord(siteId, detail);

  if (result === null) {
    return (
      <>
        <PageHeader
          title="Foundation"
          headingId={SITE_CONFIGURATION_HEADING_ID}
        />
        <p>Loading the configured site.</p>
      </>
    );
  }

  if (result.status === "not_found") {
    return (
      <>
        <PageHeader
          title="Site not found"
          headingId={SITE_CONFIGURATION_HEADING_ID}
        />
        <Panel
          heading="No such site"
          headingId="site-configuration-not-found-heading"
        >
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
        </Panel>
      </>
    );
  }

  if (result.status === "unavailable") {
    return (
      <>
        <PageHeader
          title="Foundation"
          headingId={SITE_CONFIGURATION_HEADING_ID}
        />
        <Panel
          heading="Site unavailable"
          headingId="site-configuration-unavailable-heading"
        >
          <p>
            The site store could not be read, so this site&apos;s configuration
            cannot be shown. This is a statement about the store: nothing is
            known about whether the site is configured.
          </p>
        </Panel>
      </>
    );
  }

  return (
    <SiteConfigurationFacts
      site={result.site}
      tabs={tabs}
      parentTrail={parentTrail}
    />
  );
}

/**
 * The configuration itself, rendered from one record.
 *
 * Split out so the rendering can be exercised directly over records, with no
 * client, no router, and no shell in the way.
 */
export interface SiteConfigurationFactsProps {
  site: SiteDetailReadModel;
  /** See `SiteConfigurationProps.tabs`. */
  tabs?: ReactNode;
  /** See `SiteConfigurationProps.parentTrail`. */
  parentTrail?: (siteId: string) => Crumb[];
}

export function SiteConfigurationFacts({
  site,
  tabs,
  parentTrail,
}: SiteConfigurationFactsProps) {
  const view = deriveSiteConfigurationView(site);

  return (
    <>
      {parentTrail === undefined ? null : (
        <Breadcrumbs
          trail={[...parentTrail(view.siteId), { label: "Foundation" }]}
        />
      )}

      {/*
        * The page is Foundation and the subtitle says whose. T011A settled
        * that this heading reads `Foundation`, and it still does; what was
        * missing was any statement of which site's foundation this is, which
        * a reader arriving from a bookmark had no way to tell.
        */}
      <PageHeader
        title="Foundation"
        headingId={SITE_CONFIGURATION_HEADING_ID}
        subtitle={`${view.displayName} · ${view.siteId}`}
      />

      {tabs}

      <FoundationSubtabs />

      {/*
        * Definition, as v6.9 names it. T011A left a panel headed `Foundation`
        * directly under a page titled `Foundation` and said this slice owned
        * the correction; this is it, and the panel now carries what the
        * criterion assigns to Definition: identity, summary, validity and
        * provenance, in one place rather than scattered across three panels
        * the subtab row does not name.
        */}
      <Panel
        heading="Definition"
        headingId={FOUNDATION_DEFINITION_ID}
      >
        <FactList>
          <Fact term="Site ID">{view.siteId}</Fact>
          <Fact term="Name">{view.displayName}</Fact>
          <Fact term="Type">{view.siteType}</Fact>
          <Fact term="Location">{view.location}</Fact>
          <Fact term="Timezone">{view.timezone}</Fact>
          <Fact term="Foundation version">{view.foundationVersion}</Fact>
          <Fact term="Valid from">{view.foundationValidFrom}</Fact>
          <Fact term="Summary">{view.foundationSummary}</Fact>
          {/*
           * Three vocabularies, three tones, never one status pill. Template
           * provenance stays plain text: a site created from no template
           * renders an absence there, and an absence is not a badge value.
           */}
          <Fact term="Lifecycle status">
            <Badge tone="lifecycle">{view.lifecycleStatus}</Badge>
          </Fact>
          <Fact term="Mode">
            <Badge tone="provenance">{view.sourceMode}</Badge>
          </Fact>
          <Fact term="Configuration origin">
            <Badge tone="origin">{view.configurationOrigin}</Badge>
          </Fact>
          <Fact term="Created from template">{view.templateProvenance}</Fact>
        </FactList>
        <p>{view.foundationValiditySemantics}</p>
        <p>
          These are separate facts about a site and none is derived from
          another. Configuration origin is where this site&apos;s configuration
          document came from. Mode is where the site&apos;s evidence comes
          from, and it is provenance rather than status, health, or an
          assessment. Lifecycle status is where the site is in its own life.
        </p>
      </Panel>

      <Panel
        heading="Configuration is fixed at creation"
        headingId="site-configuration-fixed-heading"
      >
        <p>{view.configurationFixedAtCreation}</p>
      </Panel>

      <SiteKeyParameters parameters={view.keyParameters} />

      <Panel
        heading="Topology"
        headingId={FOUNDATION_TOPOLOGY_ID}
      >
        <FactList>
          <SiteConfigurationStatedAbsence name="Devices" fact={view.devices} />
          <SiteConfigurationStatedAbsence
            name="Signal mappings"
            fact={view.signalMappings}
          />
        </FactList>
      </Panel>

      <SiteConfigurationComponents components={view.components} />

      <Panel
        heading="Controls"
        headingId={FOUNDATION_CONTROLS_ID}
      >
        <FactList>
          <SiteConfigurationStatedAbsence
            name="Control assumptions"
            fact={view.controlAssumptions}
          />
        </FactList>
      </Panel>

      <Panel
        heading="Not available for this site"
        headingId="site-configuration-no-evidence-heading"
      >
        <FactList>
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
        </FactList>
        <p>
          Nothing below the configuration exists for this site yet. There is no
          accepted evidence, so there is nothing to chart, nothing to analyse,
          nothing to replay, and no finding to draw. Each of those arrives with
          the evidence that fills it rather than as an empty version of itself.
        </p>
      </Panel>
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
    <Panel
      heading="Components"
      headingId="site-configuration-components-heading"
      flush
    >
      <DataTable labelledBy="site-configuration-components-heading">
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
      </DataTable>
    </Panel>
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
    <Fact term={name}>
      {fact.value}. {fact.reason}
    </Fact>
  );
}

/**
 * The headline numbers the foundation declares.
 *
 * Only what is there. A component with no declared rating produces no row -
 * not a dash, not a zero, not a greyed entry - because this panel is a list of
 * what the document states, and a blank line in it would read as a property of
 * the site rather than a gap in the document. The components table says which
 * components declare no rating, in words, which is the honest place for that.
 *
 * The panel does not render at all when the foundation declares no rated
 * component. An empty card headed `Key parameters` would be chrome claiming
 * content, which is the one thing every panel in this tree refuses.
 *
 * The value is the record's, verbatim, with the unit the record carries. No
 * conversion, no rounding, no unit the document did not choose: a number this
 * screen reformatted would be a number this screen authored.
 */
export interface SiteKeyParametersProps {
  parameters: SiteKeyParameterView[];
}

export function SiteKeyParameters({ parameters }: SiteKeyParametersProps) {
  if (parameters.length === 0) {
    return null;
  }

  return (
    <Panel
      heading="Key parameters"
      headingId="site-configuration-key-parameters-heading"
    >
      <FactList>
        {parameters.map((parameter) => (
          <Fact key={`${parameter.label}-${parameter.value}`} term={parameter.label}>
            {parameter.value}
          </Fact>
        ))}
      </FactList>
    </Panel>
  );
}
