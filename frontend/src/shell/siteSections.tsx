import { SiteSections, type SiteSectionLink } from "../ui/SiteSections";

import { siteAssetsHref, siteEvidenceHref, siteFoundationHref, siteHealthHref, sitePerformanceHref, siteUploadsHref } from "./operatorSiteRoutes";

/**
 * IA-P P5 (spec §2.3): the three section lines, by tab. Performance's line is the page's own sub-tabs and then Health;
 * a page with no sub-tabs of its own (Health) shows Performance itself first.
 */
export type SetupSection = "Foundation" | "Changes" | "Assets";
export type EvidenceSection = "Records" | "Uploads";

export function SetupSections({ siteId, current }: { siteId: string; current: SetupSection }) {
  const links: SiteSectionLink[] = [
    { label: "Foundation", href: siteFoundationHref(siteId), current: current === "Foundation" },
    { label: "Changes", href: `${siteFoundationHref(siteId)}/changes`, current: current === "Changes" },
    { label: "Assets", href: siteAssetsHref(siteId), current: current === "Assets" },
  ];
  return <SiteSections tab="Setup" links={links} />;
}

/** `recordsHref`: the Site type's own Evidence page (EV `/ev/evidence`); the canonical one otherwise. */
export function EvidenceSections({ siteId, current, recordsHref }: { siteId: string; current: EvidenceSection; recordsHref?: string }) {
  const links: SiteSectionLink[] = [
    { label: "Records", href: recordsHref ?? siteEvidenceHref(siteId), current: current === "Records" },
    { label: "Uploads", href: siteUploadsHref(siteId), current: current === "Uploads" },
  ];
  return <SiteSections tab="Evidence" links={links} />;
}

/** The Health link that ends every Performance line. */
export function healthSectionLink(siteId: string, current: boolean, search = ""): SiteSectionLink {
  return { label: "Health", href: `${siteHealthHref(siteId)}${search}`, current };
}

/** The Health page's line: Performance, then Health (current). */
export function HealthSections({ siteId, search }: { siteId: string; search?: string }) {
  const q = search === undefined || search === "" || search === "?" ? "" : search.startsWith("?") ? search : `?${search}`;
  return (
    <SiteSections
      tab="Performance"
      links={[{ label: "Performance", href: `${sitePerformanceHref(siteId)}${q}`, current: false }, healthSectionLink(siteId, true, q)]}
    />
  );
}
