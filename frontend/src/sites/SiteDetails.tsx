import type { ReactNode } from "react";

import { Badge, Fact, FactList, PageHeader, Panel } from "../ui";
import type { SiteDetailClient } from "./siteDirectoryClient";
import type { SiteDetailReadModel } from "./siteReadModel";
import { useSiteRecord } from "./useSiteRecord";
import { deriveSiteDetailView, type SiteUnavailableFact } from "./siteViewModel";

/**
 * One site, presented from the shared substrate.
 *
 * This component is the shared region. A shell composes it, supplies the
 * landmark around it, and adds beside it; it adds nothing to what is rendered
 * here beyond placing the chrome the shell hands it, and it knows nothing about
 * which shell is rendering it. There is no `variant`, `mode`, `shell`, or
 * `isLab` prop and no import of shell code, simulator code, or the feature
 * flag. The one extension slot, `tabs`, is named, optional, and opaque.
 *
 * A site is addressed by `site_id` and by nothing else. The identity that
 * arrives from the address is used to ask for the site; the identity that is
 * rendered is the one the store holds, so a case variant in an address
 * resolves to one canonical site rather than presenting the same site twice.
 *
 * What this surface shows is what the product actually knows about a site
 * somebody configured, and what it deliberately does not show is the rest:
 *
 * - No telemetry value, chart, series, gauge, or count. A configuration-only
 *   site has no evidence, and a zero, an empty chart, or a flat line is a
 *   measurement claim rather than an absence.
 * - No source health. Health becomes applicable once a source is expected to
 *   report; a configured source that has never been expected to report has no
 *   health state, so no source-health vocabulary appears at all.
 * - No evidence-derived timestamp. The one timestamp on this page is the start
 *   of the foundation's validity interval, which is configuration metadata
 *   from the record.
 * - No action control of any kind, in any state, absent from the DOM rather
 *   than rendered disabled. M1 has decided configuration is fixed at creation
 *   and that nothing removes a site, so a greyed-out control would make a
 *   promise the product has declined to make.
 * - No diagram, no empty frame reserved for a diagram, no signal selector, no
 *   site image or map panel, and no quick-actions container. Chrome with
 *   nothing behind it claims a step that has not landed.
 *
 * It renders no tab row of its own either. T011A adds one, and it is the
 * operator shell's: which aspects a workspace divides a site into is a shell's
 * opinion, and the Lab's site view will hold a different one. What this
 * component owns is where such a row goes - under the page header, above the
 * facts - so the shell hands it in through `tabs` and this decides the
 * position. The slot renders only for a site that was actually loaded, so a
 * site that is not found offers no tabs to the aspects of a site that does not
 * exist.
 */
export const SITE_DETAIL_HEADING_ID = "site-detail-heading";

export interface SiteDetailsProps {
  /** The identity taken from the address. `undefined` names no site. */
  siteId: string | undefined;
  detail: SiteDetailClient;
  /**
   * Chrome the composing shell places under the page header. Nothing renders
   * when it is absent, and nothing here reads what is in it.
   */
  tabs?: ReactNode;
}

export function SiteDetails({ siteId, detail, tabs }: SiteDetailsProps) {
  const result = useSiteRecord(siteId, detail);

  if (result === null) {
    return (
      <>
        <PageHeader title="Site" headingId={SITE_DETAIL_HEADING_ID} />
        <p>Loading the configured site.</p>
      </>
    );
  }

  if (result.status === "not_found") {
    return (
      <>
        <PageHeader title="Site not found" headingId={SITE_DETAIL_HEADING_ID} />
        <Panel heading="No such site" headingId="site-detail-not-found-heading">
          <p>
            No site with that site ID is configured. A site is addressed by its
            site ID and by nothing else, so it cannot be reached by its name or
            by the template it was created from.
          </p>
          <p>
            This is a statement that the site does not exist, not a site with
            nothing in it.
          </p>
        </Panel>
      </>
    );
  }

  if (result.status === "unavailable") {
    return (
      <>
        <PageHeader title="Site" headingId={SITE_DETAIL_HEADING_ID} />
        <Panel
          heading="Site unavailable"
          headingId="site-detail-unavailable-heading"
        >
          <p>
            The site store could not be read, so this site cannot be shown.
            This is a statement about the store: nothing is known about whether
            the site is configured.
          </p>
        </Panel>
      </>
    );
  }

  return <SiteDetailFacts site={result.site} tabs={tabs} />;
}

/**
 * The site itself, rendered from one record.
 *
 * Split out so the rendering can be exercised directly over records, with no
 * client, no router, and no shell in the way.
 *
 * The six provenance-and-status concepts are laid out as six separate facts.
 * Lifecycle status and mode are adjacent rows and never one row: `Simulated`
 * is the rendering of `source.mode`, it is provenance rather than status or
 * health, and putting it inside lifecycle status is the exact collapse the
 * canonical mockup makes and this product does not. Configuration origin is a
 * third fact, about the document rather than the evidence, and none of the
 * three is derived from or defaulted from another.
 */
export interface SiteDetailFactsProps {
  site: SiteDetailReadModel;
  /** See `SiteDetailsProps.tabs`. */
  tabs?: ReactNode;
}

export function SiteDetailFacts({ site, tabs }: SiteDetailFactsProps) {
  const view = deriveSiteDetailView(site);

  return (
    <>
      <PageHeader title={view.displayName} headingId={SITE_DETAIL_HEADING_ID} />

      {tabs}

      <Panel heading="Identity" headingId="site-detail-identity-heading">
        <FactList>
          <Fact term="Site ID">{view.siteId}</Fact>
          <Fact term="Name">{view.displayName}</Fact>
          <Fact term="Type">{view.siteType}</Fact>
          <Fact term="Location">{view.location}</Fact>
          <Fact term="Timezone">{view.timezone}</Fact>
        </FactList>
      </Panel>

      <Panel
        heading="Provenance and status"
        headingId="site-detail-provenance-heading"
      >
        <FactList>
          {/*
           * Three vocabularies, three tones, and never one status pill. The
           * badge is reinforcement: each value is still the word the record
           * supplies, and the term beside it still names which vocabulary it
           * belongs to.
           *
           * Template provenance stays plain text, because a site created from
           * no template renders an absence there rather than a value.
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
        <p>
          These are separate facts about a site and none is derived from
          another. Lifecycle status is where the site is in its own life. Mode
          is where the site's evidence comes from, and it is provenance rather
          than status, health, or an assessment. Configuration origin is where
          the site's configuration document came from.
        </p>
      </Panel>

      <Panel heading="Foundation" headingId="site-detail-foundation-heading">
        <FactList>
          <Fact term="Foundation version">{view.foundationVersion}</Fact>
          <Fact term="Valid from">{view.foundationValidFrom}</Fact>
        </FactList>
        <p>
          The foundation is the site's configured content, copied from the
          template when the site was created. It is component truth declared by
          a document: nothing here states that a device exists, is
          commissioned, or has ever reported a measurement.
        </p>
      </Panel>

      <Panel
        heading="Not available for this site"
        headingId="site-detail-no-evidence-heading"
      >
        <FactList>
          <SiteDetailUnavailableFact
            name="Integration readiness"
            fact={view.integrationReadiness}
          />
          <SiteDetailUnavailableFact
            name="Evidence availability"
            fact={view.evidenceAvailability}
          />
          <SiteDetailUnavailableFact
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
 * One fact the product cannot state, with the reason it cannot.
 *
 * The reason is rendered next to the value every time. "No evidence" on its
 * own reads as a measurement; with its reason it reads as what it is, a
 * statement about what has been recorded.
 */
export interface SiteDetailUnavailableFactProps {
  name: string;
  fact: SiteUnavailableFact;
}

export function SiteDetailUnavailableFact({
  name,
  fact,
}: SiteDetailUnavailableFactProps) {
  return (
    <Fact term={name}>
      {fact.value}. {fact.reason}
    </Fact>
  );
}
