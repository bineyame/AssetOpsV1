/**
 * IA-P P3b (spec §2.2, D-IAP.4): the Portfolio's three tabs, drawn by the one tab component (`ui/SectionTabs.tsx`).
 * Every tab link carries the address's shared range (`from`, `to`, `known_at`); this fixes 5c's default-window tabs.
 */
import type { EstateQuery } from "./estateClient";
import { estateHref } from "./estateShared";
import { SectionTabs } from "../ui/SectionTabs";
import { DECISIONS_PATH, PORTFOLIO_TABS, PORTFOLIO_TABS_LABEL, portfolioTabPath, type PortfolioTab } from "./portfolioWords";

type Window = Pick<EstateQuery, "from" | "to" | "known_at">;

/** A Portfolio tab's address with the given window and cutoff (the tab row itself carries the address's range). */
export function portfolioHref(window: Window, tab: PortfolioTab = "overview"): string {
  return estateHref(portfolioTabPath(tab), window);
}

/** IA-P P2: the Decisions list at the page's window and cutoff (Act first's new home). */
export function decisionsHref(window: Window): string {
  return estateHref(DECISIONS_PATH, window);
}

const TABS = PORTFOLIO_TABS.map(({ tab, label }) => ({ label, to: portfolioTabPath(tab) }));

export function PortfolioTabs({ current }: { current: PortfolioTab }) {
  return <SectionTabs label={PORTFOLIO_TABS_LABEL} tabs={TABS} current={portfolioTabPath(current)} />;
}
