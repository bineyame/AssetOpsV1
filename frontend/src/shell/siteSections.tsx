import { SiteSections, type SiteSectionLink } from "../ui/SiteSections";

import { FINDINGS_PATH, siteAssetsHref, siteEvHref, siteEvidenceHref, siteFindingsHref, siteFoundationHref, siteHealthHref, sitePerformanceHref, siteUploadsHref } from "./operatorSiteRoutes";

/**
 * IA-P P5 (spec §2.3): the three section lines, by tab. Performance's line is the page's own sub-tabs and then Health;
 * a page with no sub-tabs of its own (Health) shows Performance itself first.
 */
export type SetupSection = "Foundation" | "Changes" | "Assets";
export type EvidenceSection = "Records" | "Uploads" | "Findings";

/**
 * D-IAP.42: the Site types whose `/sites/:id/findings` aliases to `/findings?scope=site:{id}` (both parity layers pass).
 * Every other type keeps its Site Findings index (MD-IAP-15): lit under Evidence, "Findings" in the Evidence line.
 */
const FINDINGS_ALIASED: ReadonlySet<string> = new Set(["COLDCHAIN", "EV_CHARGING"]);

export function siteFindingsAliased(siteType: string): boolean {
  return FINDINGS_ALIASED.has(siteType);
}

/** The alias target: `/findings`, the shared range (`from`, `to`, `known_at`) untouched, then `scope=site:{id}`. */
export function siteFindingsAlias(siteId: string, params: URLSearchParams): string {
  const out = new URLSearchParams();
  for (const key of ["from", "to", "known_at"]) {
    const v = params.get(key);
    if (v !== null && v !== "") out.set(key, v);
  }
  out.set("scope", `site:${siteId}`);
  return `${FINDINGS_PATH}?${out.toString()}`;
}

export function SetupSections({ siteId, current }: { siteId: string; current: SetupSection }) {
  const links: SiteSectionLink[] = [
    { label: "Foundation", href: siteFoundationHref(siteId), current: current === "Foundation" },
    { label: "Changes", href: `${siteFoundationHref(siteId)}/changes`, current: current === "Changes" },
    { label: "Assets", href: siteAssetsHref(siteId), current: current === "Assets" },
  ];
  return <SiteSections tab="Setup" links={links} />;
}

/**
 * The Evidence line for the pages the shell draws (MINI and other Evidence pages, every Uploads page, a kept Findings
 * index). By `siteType`: COLD and EV read "Records · Analysis · Uploads" (as their own Evidence pages draw it; EV's
 * Records is `/ev/evidence`); a type whose index is kept (MD-IAP-15) reads "Records · Uploads · Findings".
 */
export function EvidenceSections({ siteId, current, siteType }: { siteId: string; current: EvidenceSection; siteType: string }) {
  const ev = siteType === "EV_CHARGING";
  const cold = siteType === "COLDCHAIN";
  const links: SiteSectionLink[] = [
    { label: "Records", href: ev ? siteEvHref(siteId, "evidence") : siteEvidenceHref(siteId), current: current === "Records" },
    ...(ev || cold
      ? [{ label: "Analysis", href: ev ? siteEvHref(siteId, "analysis") : `${siteEvidenceHref(siteId)}?view=analysis`, current: false }]
      : []),
    { label: "Uploads", href: siteUploadsHref(siteId), current: current === "Uploads" },
    ...(siteFindingsAliased(siteType) ? [] : [{ label: "Findings", href: siteFindingsHref(siteId), current: current === "Findings" }]),
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
