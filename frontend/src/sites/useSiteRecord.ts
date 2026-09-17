import { useEffect, useState } from "react";

import type { SiteDetailClient } from "./siteDirectoryClient";
import type { SiteDetailResult } from "./siteReadModel";

/**
 * Reading one site by the identity an address supplies.
 *
 * Every surface that presents one site asks the same question of the store and
 * has the same two ways to get it wrong, so the question is asked in one place.
 *
 * The first way is a late answer. A read that resolves after the surface has
 * moved on is discarded rather than rendered.
 *
 * The second is a stale answer, which is the defect T007's review found. The
 * answer is held together with the identity it was asked about, and it is
 * dropped in the render that first sees a new identity, before any effect
 * runs. Clearing inside the effect instead still commits one frame with the
 * previous site under the new address, and a site that outlives its own
 * address is the wrong site presented as the right one.
 *
 * `null` means the read has not settled. It is not a fourth outcome: the three
 * settled facts - here is the site, that site is not configured, the store
 * could not be read - are the result type's own, and none of them may be
 * degraded into another.
 */
interface SiteAnswer {
  siteId: string | undefined;
  result: SiteDetailResult | null;
}

export function useSiteRecord(
  siteId: string | undefined,
  detail: SiteDetailClient,
): SiteDetailResult | null {
  const [answer, setAnswer] = useState<SiteAnswer>({ siteId, result: null });

  if (answer.siteId !== siteId) {
    setAnswer({ siteId, result: null });
  }

  useEffect(() => {
    let active = true;

    if (siteId === undefined || siteId === "") {
      setAnswer({ siteId, result: { status: "not_found" } });
      return undefined;
    }

    void detail.getSite(siteId).then((loaded) => {
      if (active) {
        setAnswer({ siteId, result: loaded });
      }
    });

    return () => {
      active = false;
    };
  }, [detail, siteId]);

  return answer.siteId === siteId ? answer.result : null;
}
