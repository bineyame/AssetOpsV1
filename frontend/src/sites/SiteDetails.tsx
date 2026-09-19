import type { ReactNode } from "react";

import {
  Badge,
  Breadcrumbs,
  Fact,
  FactList,
  PageHeader,
  Panel,
  type Crumb,
} from "../ui";
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
  /**
   * Where this Site sits in the composing shell's own route hierarchy.
   *
   * The shell knows its routes; this knows the Site. So the shell builds the
   * trail above this page and this appends the current crumb, spelled the way
   * the record spells it rather than the way the address did. It is a function
   * because a deeper surface needs the canonical `site_id` to build its own
   * parent, and only this side has it.
   */
  parentTrail?: (siteId: string) => Crumb[];
  /**
   * Site actions the composing shell owns, placed inside the Quick actions
   * panel. The gated ones cannot live here: they depend on the feature flag
   * and on the Lab entry point, and this module may import neither.
   */
  quickActions?: ReactNode;
}

export function SiteDetails({
  siteId,
  detail,
  tabs,
  parentTrail,
  quickActions,
}: SiteDetailsProps) {
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

  return (
    <SiteDetailFacts
      site={result.site}
      tabs={tabs}
      parentTrail={parentTrail}
      quickActions={quickActions}
    />
  );
}

/**
 * The site itself, rendered from one record.
 *
 * Split out so the rendering can be exercised directly over records, with no
 * client, no router, and no shell in the way.
 *
 * The six provenance-and-status concepts are laid out as six separate facts.
 * `Simulated` is the rendering of `source.mode`; it is provenance rather than
 * status or health, and putting it inside lifecycle status is the exact
 * collapse the canonical mockup makes and this product does not. Configuration
 * origin is a third fact, about the document rather than the evidence, and
 * none of the three is derived from or defaulted from another.
 *
 * T007 put lifecycle status next to mode so a reader could see the two were
 * different. T012 moves it up into the site's own facts, where the task's
 * information architecture puts it, and the separation survives the move
 * because adjacency was never what carried it: separate terms, separate values
 * and separate tones are, and each of those is asserted. The prose under
 * provenance still names lifecycle status and says where it went, so nothing
 * on the screen implies the two were merged.
 */
export interface SiteDetailFactsProps {
  site: SiteDetailReadModel;
  /** See `SiteDetailsProps.tabs`. */
  tabs?: ReactNode;
  /** See `SiteDetailsProps.parentTrail`. */
  parentTrail?: (siteId: string) => Crumb[];
  /** See `SiteDetailsProps.quickActions`. */
  quickActions?: ReactNode;
}

export function SiteDetailFacts({
  site,
  tabs,
  parentTrail,
  quickActions,
}: SiteDetailFactsProps) {
  const view = deriveSiteDetailView(site);

  return (
    <>
      {parentTrail === undefined ? null : (
        <Breadcrumbs trail={[...parentTrail(view.siteId), { label: view.siteId }]} />
      )}

      {/*
        * The identity header. The title is the `site_id`, because that is what
        * addresses a site and what a reader needs to quote; the display name
        * is beneath it, because a name is a label on the thing rather than the
        * thing. The badge is `source.mode`, which belongs here for the same
        * reason: where this site's evidence comes from is a fact about the
        * subject, not decoration beside it.
        *
        * The `site_id` rendered is the record's, never the address's. An
        * address in the wrong case resolves to one canonical site and this
        * header spells it the one way.
        */}
      <PageHeader
        title={view.siteId}
        headingId={SITE_DETAIL_HEADING_ID}
        subtitle={view.displayName}
        badge={<Badge tone="provenance">{view.sourceMode}</Badge>}
      />

      {tabs}

      {/*
        * Every fact the record carries about the site itself, in one panel.
        *
        * Lifecycle status is here rather than beside Mode, which is where T007
        * put it. The two were adjacent then so a reader could see they were
        * different, and the mockup's single `Status` field is still the error
        * this screen exists to correct - but adjacency was never what carried
        * that. Separate terms, separate values and separate tones are, and
        * each of those is asserted. What lifecycle status is, is a fact about
        * the site, so it sits with the site's other facts.
        *
        * The foundation's version and validity start are here for the same
        * reason: they describe this site's configured content. What a
        * foundation is, as a model, is explained underneath, because that is a
        * statement about the product rather than a fact about this site.
        */}
      <Panel
        heading="Site information"
        headingId="site-detail-identity-heading"
      >
        <FactList>
          <Fact term="Site ID">{view.siteId}</Fact>
          <Fact term="Name">{view.displayName}</Fact>
          <Fact term="Type">{view.siteType}</Fact>
          <Fact term="Location">{view.location}</Fact>
          <Fact term="Timezone">{view.timezone}</Fact>
          <Fact term="Lifecycle status">
            <Badge tone="lifecycle">{view.lifecycleStatus}</Badge>
          </Fact>
          <Fact term="Foundation version">{view.foundationVersion}</Fact>
          <Fact term="Valid from">{view.foundationValidFrom}</Fact>
          <Fact term="Summary">{view.foundationSummary}</Fact>
        </FactList>
        <p>
          The foundation is the site's configured content, copied from the
          template when the site was created. It is component truth declared by
          a document: nothing here states that a device exists, is
          commissioned, or has ever reported a measurement.
        </p>
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
          another. Mode is where the site's evidence comes from, and it is
          provenance rather than status, health, or an assessment.
          Configuration origin is where the site's configuration document came
          from. Neither is lifecycle status, which is where the site is in its
          own life and is listed above with the site's other facts.
        </p>
      </Panel>

      <SiteQuickActions>{quickActions}</SiteQuickActions>

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

/**
 * The Quick actions panel.
 *
 * Every action on this screen is disabled, and each one says what would make
 * it work. That is the third affordance state, and this is the screen where it
 * earns its keep: a labelled-in-place tab names an aspect of a Site, while a
 * disabled control names an action the product can sequence but cannot yet
 * perform. Blurring those two is how a UI starts promising things.
 *
 * `View Live Data` is owned here because it is not a simulator surface: live
 * data is an operator capability, it is unavailable for the same reason
 * everywhere, and the reason is about evidence rather than about the Lab. The
 * gated actions cannot be owned here, because deciding them means reading the
 * feature flag and naming the Lab's address, and this module may do neither.
 * They arrive through the slot.
 *
 * With the slot empty - which is what a gate-off build produces, and what a
 * substrate test renders - the panel is still correct: one action, disabled,
 * with its reason. It does not become an empty frame, and it does not
 * disappear, because `View Live Data` is unavailable whether or not a
 * developer workspace exists.
 *
 * What is not here, in any state, is every control the mockup draws that this
 * product has decided against: `Edit`, `Edit Configuration`, `Version
 * History`, `Duplicate Site`, `Delete Site`, and the site image `Change`. They
 * are absent from the DOM rather than disabled, because disabled would say the
 * capability exists and is unavailable to you, and what is true is that M1
 * decided configuration is fixed at creation and that nothing removes a site.
 */
export interface SiteQuickActionsProps {
  /** See `SiteDetailsProps.quickActions`. */
  children?: ReactNode;
}

export function SiteQuickActions({ children }: SiteQuickActionsProps) {
  return (
    <Panel heading="Quick actions" headingId="site-detail-actions-heading">
      <ul className="action-list">
        {children}
        <SiteQuickAction
          label="View Live Data"
          unavailableBecause={
            "No evidence has been accepted for this site. Live data arrives " +
            "with the ingestion and evidence steps, which are later than " +
            "configuring a site."
          }
        />
      </ul>
    </Panel>
  );
}

/**
 * One action the product can name but cannot yet perform.
 *
 * The reason is rendered beside the control, visibly, and tied to it with
 * `aria-describedby`. A reason that lives only in a tooltip is a reason most
 * people never read, and a `disabled` button is not focusable, so a tooltip on
 * one is a reason a keyboard cannot reach at all.
 *
 * `disabled` is the real attribute rather than `aria-disabled`, because the
 * claim is the true one: this control does nothing. It cannot navigate, it
 * cannot submit, and it has no handler to call, so there is no path from a
 * click to a request.
 */
export interface SiteQuickActionProps {
  label: string;
  unavailableBecause: string;
}

export function SiteQuickAction({
  label,
  unavailableBecause,
}: SiteQuickActionProps) {
  const reasonId = `site-action-${label.replace(/\s+/g, "-").toLowerCase()}-reason`;

  return (
    <li className="action-list__item">
      <button
        type="button"
        className="action"
        disabled
        aria-describedby={reasonId}
      >
        {label}
      </button>
      <p className="action-list__reason" id={reasonId}>
        {unavailableBecause}
      </p>
    </li>
  );
}
