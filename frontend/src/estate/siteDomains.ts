/**
 * IA-P3 fix round 1 (D-IAP.48): the domain of each Site, from the Site directory, for a `group:` scope on the Findings
 * and Actions lists (their rows carry a `site_code` but no domain). The join is by Site code, case-blind (Site identity
 * is case-blind, `site_id_key`). A row whose code is not in the directory has no domain: it is in no group.
 *
 * The directory is read only while the scope is a group (`on`). `loading` and `unavailable` are states of their own, so
 * a list never reads "none" before the directory says which rows are in the group.
 */
import { useEffect, useMemo, useState } from "react";

import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";

export type SiteDomains =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "unavailable"; retry(): void }
  | { state: "ready"; domainOf(siteCode: string): string | null };

export function useSiteDomains(directory: SiteDirectoryClient | null, on: boolean): SiteDomains {
  const [read, setRead] = useState<{ directory: SiteDirectoryClient; byCode: Map<string, string> | null } | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!on || directory === null) return undefined;
    let live = true;
    void directory.listSites().then((r) => {
      if (!live) return;
      setRead({ directory, byCode: r.status === "loaded" ? new Map(r.sites.map((s) => [s.site_id.toLowerCase(), s.site_type])) : null });
    });
    return () => {
      live = false;
    };
  }, [on, directory, attempt]);
  return useMemo<SiteDomains>(() => {
    if (!on || directory === null) return { state: "idle" };
    if (read === null || read.directory !== directory) return { state: "loading" };
    const { byCode } = read;
    if (byCode === null) {
      return {
        state: "unavailable",
        retry: () => {
          setRead(null);
          setAttempt((n) => n + 1);
        },
      };
    }
    return { state: "ready", domainOf: (code) => byCode.get(code.toLowerCase()) ?? null };
  }, [on, directory, read]);
}
