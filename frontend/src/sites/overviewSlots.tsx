/**
 * W1-F2 (D-2026-10-17-mockup-layout-spec): the v69 `mini` Site Overview panel grid.
 *
 * The mock lays the Overview out as: statusbar, objective line and five objective cards (none of them a panel),
 * then panel 1 full width, panels 2+3 as a two-column pair, panels 4+5 as a two-column pair. Every Overview body
 * (selected-day, legacy window, refused read) fills these same five slots, so a missing read is an honest gap
 * inside its panel, never a missing or extra panel.
 */
import type { ReactNode } from "react";

import { ChartNote, Panel } from "../ui";

export const OVERVIEW_PANEL_TITLES = [
  "What happened in the selected hour",
  "Operating context",
  "Needs attention",
  "Bounded money consequence",
  "Next step",
] as const;

export interface OverviewSlot {
  body: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}

export function OverviewGrid({
  lead,
  happened,
  context,
  attention,
  money,
  next,
}: {
  /** Statusbar, objective line and cards: above the panels, never a panel. */
  lead?: ReactNode;
  happened: OverviewSlot;
  context: OverviewSlot;
  attention: OverviewSlot;
  money: OverviewSlot;
  next: OverviewSlot;
}) {
  const [t1, t2, t3, t4, t5] = OVERVIEW_PANEL_TITLES;
  return (
    <>
      {lead}
      <Panel
        heading={t1}
        headingId="site-overview-happened-heading"
        description={happened.description}
        actions={happened.actions}
      >
        {happened.body}
      </Panel>
      <div className="panel-pair">
        <Panel
          heading={t2}
          headingId="site-window-context-heading"
          description={context.description}
          actions={context.actions}
        >
          {context.body}
        </Panel>
        <Panel
          heading={t3}
          headingId="site-window-findings-heading"
          description={attention.description}
          actions={attention.actions}
        >
          {attention.body}
        </Panel>
      </div>
      <div className="panel-pair">
        <Panel heading={t4} headingId="site-window-money-heading" description={money.description} actions={money.actions}>
          {money.body}
        </Panel>
        <Panel heading={t5} headingId="site-overview-next-heading" description={next.description} actions={next.actions}>
          {next.body}
        </Panel>
      </div>
    </>
  );
}

/** The in-panel gap for the hour the mock composes: the read covers a window, and no hour is selected. */
export function HourNotSelected({ scope }: { scope: string }) {
  return (
    <ChartNote data={{ "data-overview-gap": "selected-hour" }}>
      Hour not selected: this Overview reads {scope}, so it cannot say what happened in one hour. The periods below
      are the ones the read assessed.
    </ChartNote>
  );
}

/**
 * A page-level state (the Overview read failed or cannot be laid out) stated before the five panel slots,
 * each of which then says the same read gap inside it.
 */
export function OverviewRefused({
  title,
  reason,
  name,
  gapText = "Not shown: the Overview could not be read, so nothing is known here. This is not an empty result.",
}: {
  title: string;
  reason: ReactNode;
  name: string;
  gapText?: string;
}) {
  const gap = <p data-overview-gap="read">{gapText}</p>;
  return (
    <div className="site-window-overview" data-overview-state="refused">
      <div className="page-refusal" data-page-refusal={name}>
        <p className="page-refusal__title">
          <strong>{title}</strong>
        </p>
        <p>{reason}</p>
      </div>
      <OverviewGrid
        happened={{ body: gap }}
        context={{ body: gap }}
        attention={{ body: gap }}
        money={{ body: <p data-overview-gap="read">No current amount. {gapText}</p> }}
        next={{ body: <p data-overview-gap="next">No supported next action.</p> }}
      />
    </div>
  );
}
