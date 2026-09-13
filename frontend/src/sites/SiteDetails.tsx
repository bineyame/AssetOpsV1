import { useEffect, useState } from "react";

import type { SiteDetailClient } from "./siteDirectoryClient";
import type { SiteDetailReadModel, SiteDetailResult } from "./siteReadModel";
import { deriveSiteDetailView, type SiteUnavailableFact } from "./siteViewModel";

/**
 * One site, presented from the shared substrate.
 *
 * This component is the shared region. A shell composes it, supplies the
 * landmark around it, and adds beside it; it adds nothing to what is rendered
 * here, and this component knows nothing about which shell is rendering it.
 * There is no `variant`, `mode`, `shell`, or `isLab` prop, no import of shell
 * code, simulator code, or the feature flag, and no extension slot, because
 * nothing fills one in this slice.
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
 * - No tab bar, no diagram, no empty frame reserved for a diagram, no signal
 *   selector, no site image or map panel, and no quick-actions container.
 *   Chrome with nothing behind it claims a step that has not landed.
 */
export const SITE_DETAIL_HEADING_ID = "site-detail-heading";

export interface SiteDetailsProps {
  /** The identity taken from the address. `undefined` names no site. */
  siteId: string | undefined;
  detail: SiteDetailClient;
}

export function SiteDetails({ siteId, detail }: SiteDetailsProps) {
  const [result, setResult] = useState<SiteDetailResult | null>(null);

  useEffect(() => {
    let active = true;

    if (siteId === undefined || siteId === "") {
      setResult({ status: "not_found" });
      return undefined;
    }

    void detail.getSite(siteId).then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [detail, siteId]);

  if (result === null) {
    return (
      <>
        <h1 id={SITE_DETAIL_HEADING_ID}>Site</h1>
        <p>Loading the configured site.</p>
      </>
    );
  }

  if (result.status === "not_found") {
    return (
      <>
        <h1 id={SITE_DETAIL_HEADING_ID}>Site not found</h1>
        <section aria-labelledby="site-detail-not-found-heading">
          <h2 id="site-detail-not-found-heading">No such site</h2>
          <p>
            No site with that site ID is configured. A site is addressed by its
            site ID and by nothing else, so it cannot be reached by its name or
            by the template it was created from.
          </p>
          <p>
            This is a statement that the site does not exist, not a site with
            nothing in it.
          </p>
        </section>
      </>
    );
  }

  if (result.status === "unavailable") {
    return (
      <>
        <h1 id={SITE_DETAIL_HEADING_ID}>Site</h1>
        <section aria-labelledby="site-detail-unavailable-heading">
          <h2 id="site-detail-unavailable-heading">Site unavailable</h2>
          <p>
            The site store could not be read, so this site cannot be shown.
            This is a statement about the store: nothing is known about whether
            the site is configured.
          </p>
        </section>
      </>
    );
  }

  return <SiteDetailFacts site={result.site} />;
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
}

export function SiteDetailFacts({ site }: SiteDetailFactsProps) {
  const view = deriveSiteDetailView(site);

  return (
    <>
      <h1 id={SITE_DETAIL_HEADING_ID}>{view.displayName}</h1>

      <section aria-labelledby="site-detail-identity-heading">
        <h2 id="site-detail-identity-heading">Identity</h2>
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

      <section aria-labelledby="site-detail-provenance-heading">
        <h2 id="site-detail-provenance-heading">Provenance and status</h2>
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
          another. Lifecycle status is where the site is in its own life. Mode
          is where the site's evidence comes from, and it is provenance rather
          than status, health, or an assessment. Configuration origin is where
          the site's configuration document came from.
        </p>
      </section>

      <section aria-labelledby="site-detail-foundation-heading">
        <h2 id="site-detail-foundation-heading">Foundation</h2>
        <dl>
          <dt>Foundation version</dt>
          <dd>{view.foundationVersion}</dd>
          <dt>Valid from</dt>
          <dd>{view.foundationValidFrom}</dd>
        </dl>
        <p>
          The foundation is the site's configured content, copied from the
          template when the site was created. It is component truth declared by
          a document: nothing here states that a device exists, is
          commissioned, or has ever reported a measurement.
        </p>
      </section>

      <section aria-labelledby="site-detail-no-evidence-heading">
        <h2 id="site-detail-no-evidence-heading">Not available for this site</h2>
        <dl>
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
    <>
      <dt>{name}</dt>
      <dd>
        {fact.value}. {fact.reason}
      </dd>
    </>
  );
}
