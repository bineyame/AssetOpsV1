/**
 * IA-P P1 (spec §2.2, D-IAP.4): the one tab component of every IA tab group. The Site tab family (`site-tabs` links
 * with `aria-current="page"`, not an ARIA tablist), as `PortfolioTabs` draws it. Every tab link carries the address's
 * shared range (`from`, `to`, `known_at`), never a page-only parameter.
 */
import { useSearchParams } from "react-router-dom";

import { RangeLink as Link } from "./RangeLink";
import { withRange } from "./sharedRange";
import { useCurrentTabInView } from "./useCurrentTabInView";

export interface SectionTab {
  label: string;
  to: string;
}

/** Evidence & records (spec §2.2): Coverage and Records. */
export const EVIDENCE_RECORDS_TITLE = "Evidence & records";
export const EVIDENCE_RECORDS_TABS_LABEL = "Evidence & records sections";
export const EVIDENCE_RECORDS_TABS: readonly SectionTab[] = [
  { label: "Coverage", to: "/evidence" },
  { label: "Records", to: "/evidence/records" },
];

export function SectionTabs({ label, tabs, current }: { label: string; tabs: readonly SectionTab[]; current: string }) {
  const [params] = useSearchParams();
  const rowRef = useCurrentTabInView<HTMLElement>();
  return (
    <nav className="site-tabs" aria-label={label} ref={rowRef} data-section-tabs={label}>
      <ol className="site-tabs__list">
        {tabs.map((tab) => (
          <li key={tab.to} className="site-tabs__item">
            <Link className="site-tabs__link" to={withRange(tab.to, params)} aria-current={tab.to === current ? "page" : undefined}>
              {tab.label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}
