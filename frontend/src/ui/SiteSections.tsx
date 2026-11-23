import type { ReactNode } from "react";

import { RangeLink as Link } from "./RangeLink";

/**
 * IA-P P5 (spec §2.3): the section links line. Under the Site tab row on every page that lights Performance, Evidence
 * or Setup, `<nav class="site-sections" aria-label="{Tab} sections">` holds "In {Tab}:" and the tab's pages; the current
 * one carries `aria-current="page"`. The shell names the links (this module knows no Site address).
 */
export interface SiteSectionLink {
  label: string;
  href: string;
  current: boolean;
  /** Extra attributes a page's own tests already pin (e.g. `data-performance-subtab`). */
  data?: Record<`data-${string}`, string | boolean | undefined>;
}

export function siteSectionsLabel(tab: string): string {
  return `${tab} sections`;
}

/** One link of the line, for a page that draws its own items (the Performance sub-tabs). */
export function SiteSectionItem({ link }: { link: SiteSectionLink }) {
  return (
    <li className="site-tabs__item">
      <Link className="site-tabs__link" to={link.href} aria-current={link.current ? "page" : undefined} {...(link.data ?? {})}>
        {link.label}
      </Link>
    </li>
  );
}

/**
 * The line. `links` are drawn in order; `children` (list items) come before them, for a page whose sub-tabs are its
 * own (the Performance pages put their sub-tabs first and Health last).
 */
export function SiteSections({ tab, links, children }: { tab: string; links: SiteSectionLink[]; children?: ReactNode }) {
  return (
    <nav className="site-tabs site-subtabs site-sections" aria-label={siteSectionsLabel(tab)}>
      <span className="site-sections__lead">{`In ${tab}:`}</span>
      <ol className="site-tabs__list">
        {children}
        {links.map((link) => (
          <SiteSectionItem key={link.label} link={link} />
        ))}
      </ol>
    </nav>
  );
}
