import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { SITE_CONFIGURATION_HEADING_ID, SiteConfiguration } from "../sites/SiteConfiguration";
import { FOUNDATION_SUBTABS, FoundationSubtabs, foundationViewFor, type FoundationView } from "../sites/FoundationSubtabs";
import { FoundationPanelSkeletons, StoredFoundationViews } from "../sites/StoredFoundationViews";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import type { GatewayHealthClient } from "../sites/gatewayHealthClient";
import { bindingPublicationItem, type SiteFoundationClient } from "../sites/siteFoundationClient";
import type { SiteTemplateLineageClient } from "../sites/siteTemplateLineage";
import { SITE_FOUNDATION_LOADING, useSiteFoundation } from "../sites/useSiteFoundation";
import { PageHeader, Panel, plainTime, ProductStatus, readResultWords } from "../ui";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import { RouteNotAvailableFrame } from "./RouteNotAvailableFrame";
import {
  FOUNDATION_COMPONENT_PARAM,
  siteDetailHref,
  siteEvidenceHref,
  siteHealthHref,
  siteFoundationHref,
  siteFoundationViewHref,
  sitePerformanceHref,
} from "./operatorSiteRoutes";

const segmentFor = (target: FoundationView) =>
  FOUNDATION_SUBTABS.find((subtab) => subtab.view === target)?.segment ?? "";

export interface SiteFoundationFrameProps {
  detail: SiteDetailClient;
  /** S1-01: the persisted Foundation read and its one change. */
  foundation: SiteFoundationClient;
  sitesPath: string;
  templateLineage?: SiteTemplateLineageClient;
  /** V-01a round 3: the S2 central gateway-contact read shown on Readiness. */
  gatewayHealth?: GatewayHealthClient;
}

/**
 * Foundation for one Site (S1-01, organized into views by S1-03).
 *
 * A Site imported into the persisted store renders one of three views - Site
 * model (the Foundation address), Single line diagram (`/sld`) and Readiness
 * (`/readiness`) - of the stored version effective at the `at` instant carried
 * in the URL (absent = in effect now). Every view link carries `at`, so moving
 * between views, reloading and sharing keep the selection. A Site still read
 * from its original document renders its one legacy page, labelled as such,
 * with no view row; its view addresses state that the view needs an imported
 * Site. A period with no stored version is stated, never filled with the
 * current configuration.
 */
export function SiteFoundationFrame({
  detail,
  foundation,
  sitesPath,
  templateLineage,
  gatewayHealth,
}: SiteFoundationFrameProps) {
  const { siteId, foundationView } = useParams<{ siteId: string; foundationView?: string }>();
  const view: FoundationView | null = foundationViewFor(foundationView);
  const [params, setParams] = useSearchParams();
  const at = params.get("at");
  const [refresh, setRefresh] = useState(0);
  const state = useSiteFoundation(siteId, at, foundation, refresh);

  const component = params.get(FOUNDATION_COMPONENT_PARAM);
  // A selected part that the newly selected period does not declare: its ID
  // and the period it was missing from, so the notice is about this period only.
  const [missingPart, setMissingPart] = useState<{ id: string; at: string | null } | null>(null);

  const selectAt = useCallback(
    (next: string | null) => {
      const updated = new URLSearchParams(params);
      if (next === null) updated.delete("at");
      else updated.set("at", next);
      setParams(updated);
    },
    [params, setParams],
  );

  const selectComponent = useCallback(
    (next: string | null) => {
      const updated = new URLSearchParams(params);
      if (next === null) updated.delete(FOUNDATION_COMPONENT_PARAM);
      else updated.set(FOUNDATION_COMPONENT_PARAM, next);
      setMissingPart(null);
      setParams(updated);
    },
    [params, setParams],
  );

  const loadedRead = state.foundation?.status === "loaded" ? state.foundation.value : null;
  const partDeclared =
    loadedRead === null || component === null
      ? null
      : loadedRead.detail.foundation.components.some((c) => c.component_id === component);

  // Retain the part across a period change only while that component ID is
  // declared in the selected Foundation; otherwise clear it, and say so,
  // rather than silently choosing another part.
  useEffect(() => {
    if (component === null || partDeclared !== false) return;
    setMissingPart({ id: component, at });
    const updated = new URLSearchParams(params);
    updated.delete(FOUNDATION_COMPONENT_PARAM);
    setParams(updated, { replace: true });
  }, [component, partDeclared, at, params, setParams]);

  // `/foundation/` with an empty segment never reaches here as a view route;
  // any other segment that is not a view is not a destination.
  if (view === null || (foundationView !== undefined && view === "model")) {
    return <RouteNotAvailableFrame />;
  }

  const loaded = state.foundation?.status === "loaded" ? state.foundation.value : null;

  const tabs = <OperatorSiteTabs siteId={siteId} current="Foundation" />;
  const parentTrail = (canonicalSiteId: string) => [
    { label: "Sites", to: sitesPath },
    { label: canonicalSiteId, to: siteDetailHref(canonicalSiteId) },
  ];

  if (state.foundation === null) {
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <PageHeader title="Foundation" headingId={SITE_CONFIGURATION_HEADING_ID} />
        <p>{SITE_FOUNDATION_LOADING}</p>
      </main>
    );
  }

  if (loaded !== null && siteId !== undefined) {
    const versions = state.versions?.status === "loaded" ? state.versions.value : null;
    const segmentOf = (target: FoundationView) =>
      FOUNDATION_SUBTABS.find((subtab) => subtab.view === target)?.segment ?? "";
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <StoredFoundationViews
          view={view}
          foundation={loaded}
          versions={versions}
          selectedAt={at}
          onSelectAt={selectAt}
          selectedComponent={partDeclared === true ? component : null}
          missingComponent={missingPart !== null && missingPart.at === at ? missingPart.id : null}
          onSelectComponent={selectComponent}
          viewHref={(target) =>
            siteFoundationViewHref(siteId, segmentOf(target), at, partDeclared === true ? component : null)
          }
          evidenceHref={siteEvidenceHref(siteId)}
          healthHref={siteHealthHref(siteId)}
          gatewayHealth={gatewayHealth}
          dispatchHref={sitePerformanceHref(siteId, "dispatch")}
          tabs={tabs}
          parentTrail={parentTrail}
          snapshotHref={foundation.snapshotUrl(siteId, loaded.resolved.at)}
          onPublishBindings={async (validFrom, bindings, note) => {
            const outcome = await foundation.publishBindings(siteId, {
              valid_from: validFrom,
              bindings: bindings.map(bindingPublicationItem),
              note,
            });
            if (outcome.status === "published") setRefresh((count) => count + 1);
            return outcome;
          }}
          onPublish={async (assetCode, value, validFrom) => {
            const outcome = await foundation.publishReserve(siteId, {
              asset_code: assetCode,
              value,
              valid_from: validFrom,
            });
            if (outcome.status === "published") setRefresh((count) => count + 1);
            return outcome;
          }}
        />
      </main>
    );
  }

  if (at !== null && (state.foundation.status === "not_found" || state.foundation.status === "invalid")) {
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <PageHeader title="Foundation" headingId={SITE_CONFIGURATION_HEADING_ID} subtitle={siteId} />
        {tabs}
        <FoundationSubtabs current={view} hrefFor={(target) => siteFoundationViewHref(siteId ?? "", segmentFor(target), at, null)} />
        {/* W1-F1: the page-level refusal, then the view's v69 panel slots with in-panel gaps. */}
        <div className="page-refusal" role="status" data-page-refusal="no-version">
          <p className="page-refusal__title">
            <strong>No stored version for this period</strong>
          </p>
          {/* W1-UX-05: the plain state line; the bound is the selected time the read was asked for. */}
          <ProductStatus
            words={{
              label: "No configuration for this period",
              sentence: "No Foundation version is stored for the selected time, so nothing is shown as configured.",
              tone: "limited",
              code: state.foundation.status,
              unrecognised: false,
            }}
            scope={`${siteId} · selected time ${plainTime(at) ?? at}`}
            asOf={at}
          />
          <p>{state.foundation.message}</p>
          <p>The configuration in effect now is not shown in its place.</p>
          <button type="button" onClick={() => selectAt(null)}>
            Show the version in effect now
          </button>
        </div>
        <FoundationPanelSkeletons
          view={view}
          siteName={siteId ?? ""}
          gap="No Foundation version is stored for the selected time, so nothing is shown as configured in this panel."
        />
      </main>
    );
  }

  if (
    view !== "model" &&
    siteId !== undefined &&
    state.foundation.status !== "migration_required" &&
    state.foundation.status !== "loaded"
  ) {
    // The store could not be read, or answered without a version: that is not
    // evidence that the Site has no stored records, so say only that.
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <PageHeader title="Foundation" headingId={SITE_CONFIGURATION_HEADING_ID} subtitle={siteId} />
        {tabs}
        <FoundationSubtabs current={view} hrefFor={(target) => siteFoundationViewHref(siteId, segmentFor(target), at, null)} />
        <div className="page-refusal" role="status" data-page-refusal="unavailable">
          <p className="page-refusal__title">
            <strong>Stored versions unavailable</strong>
          </p>
          <ProductStatus words={readResultWords("unavailable")} scope={`${siteId} · Foundation`} asOf={null} />
          <p>
            Stored Foundation versions could not be read
            {state.foundation.message === null ? "." : `: ${state.foundation.message}`} This view is
            not shown until they can be.
          </p>
          <p>
            <Link to={siteFoundationHref(siteId)}>Open this site&apos;s Foundation</Link>
          </p>
        </div>
        <FoundationPanelSkeletons
          view={view}
          siteName={siteId}
          gap="Stored Foundation versions could not be read, so this panel shows nothing configured."
        />
      </main>
    );
  }

  if (view !== "model" && siteId !== undefined) {
    // A Site that is not imported has no stored Foundation, binding set or
    // snapshot, so these views would imply records it does not have.
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <PageHeader title="Foundation" headingId={SITE_CONFIGURATION_HEADING_ID} subtitle={siteId} />
        {tabs}
        {/* No view row: a site that is not imported has no Readiness or SLD view to switch to. */}
        <div className="page-refusal" role="status" data-page-refusal="not-imported">
          <p className="page-refusal__title">
            <strong>This view needs an imported Site</strong>
          </p>
          <p>
            This site has no stored Foundation version, channel-link set or snapshot, so there is no
            {view === "sld" ? " bound single line diagram" : " configuration readiness"} to show here.
          </p>
          <p>
            <Link to={siteFoundationHref(siteId)}>Open this site&apos;s Foundation</Link>
          </p>
        </div>
        <FoundationPanelSkeletons
          view={view}
          siteName={siteId}
          gap="This site has no stored Foundation version, so this panel has nothing to show."
        />
      </main>
    );
  }

  const notice =
    state.foundation.status === "migration_required" ? (
      <Panel heading="Original configuration record" headingId="foundation-legacy-heading">
        <p>
          This site is read from its original configuration document. It has no stored
          Foundation versions until it is imported, so no period can be chosen and nothing can
          be changed here.
        </p>
      </Panel>
    ) : state.foundation.status === "unavailable" ? (
      <Panel heading="Stored versions unavailable" headingId="foundation-store-unavailable-heading">
        <p>
          Stored Foundation versions could not be read
          {state.foundation.message === null ? "." : `: ${state.foundation.message}`} The
          configuration below is the site&apos;s record as served now; no period can be chosen.
        </p>
      </Panel>
    ) : null;

  return (
    <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
      <SiteConfiguration
        siteId={siteId}
        detail={detail}
        templateLineage={templateLineage}
        tabs={tabs}
        revision={notice}
        parentTrail={parentTrail}
      />
    </main>
  );
}
