/**
 * PF-T: the Portfolio section tab row, shared by the Portfolio tabs and "The month" (5c, spec §5.1).
 */
import { RangeLink as Link } from "../ui/RangeLink";
import { useCurrentTabInView } from "../ui/useCurrentTabInView";
import type { EstateLens, EstateQuery } from "./estateClient";
import { estateHref } from "./estateShared";
import { DECISIONS_PATH, PORTFOLIO_TABS, PORTFOLIO_TABS_LABEL, portfolioTabPath, type PortfolioTab } from "./portfolioWords";

type Window = Pick<EstateQuery, "from" | "to" | "known_at">;

/**
 * A Portfolio URL: the tab's address with the accepted window and explicit cutoff, never a cursor. PF-T: a
 * non-default lens travels on Act first only. 5c: moved here from `EstatePortfolio.tsx` with the tab row.
 */
export function portfolioHref(window: Window, _lens: EstateLens, tab: PortfolioTab = "overview"): string {
  // 5c (spec §5.1): "The month" is the plain path; it carries no window and no lens (its state is `?month=`).
  if (tab === "month") return portfolioTabPath("month");
  return estateHref(portfolioTabPath(tab), window);
}

/** IA-P P2: the Decisions list at the page's window and cutoff (Act first's new home). */
export function decisionsHref(window: Window): string {
  return estateHref(DECISIONS_PATH, window);
}

/**
 * PF-T: the section tab row. The Site tab family (`site-tabs` links with `aria-current`, not an ARIA tablist): each
 * tab is an address carrying the window and cutoff; `lens` only on Act first. A count that is unknown shows no badge.
 * 5c (spec §5.1): moved verbatim from `EstatePortfolio.tsx`; `counts` is optional (the month page passes none).
 */
export function PortfolioTabs({
  current,
  window,
  lens,
  counts,
}: {
  current: PortfolioTab;
  window: Window;
  lens: EstateLens;
  counts?: Partial<Record<PortfolioTab, number | null | undefined>>;
}) {
  const rowRef = useCurrentTabInView<HTMLElement>();
  return (
    <nav className="site-tabs pf-tabs" aria-label={PORTFOLIO_TABS_LABEL} ref={rowRef} data-portfolio-tabs>
      <ol className="site-tabs__list">
        {PORTFOLIO_TABS.map(({ tab, label }) => {
          const n = counts?.[tab];
          return (
            <li key={tab} className={tab === "scope" ? "site-tabs__item pf-tabs__deep" : "site-tabs__item"}>
              <Link className="site-tabs__link" to={portfolioHref(window, lens, tab)} aria-current={tab === current ? "page" : undefined}>
                <span data-pf-tab-label>{label}</span>
                {typeof n === "number" ? (
                  <span className="pf-tabs__count" data-pf-tab-count>
                    {n}
                  </span>
                ) : null}
              </Link>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
