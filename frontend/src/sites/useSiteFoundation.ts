import { useEffect, useState } from "react";

import type {
  FoundationRead,
  FoundationReadModel,
  FoundationVersionsReadModel,
  SiteFoundationClient,
} from "./siteFoundationClient";

export const SITE_FOUNDATION_LOADING = "Loading the site's Foundation revision.";

export interface SiteFoundationState {
  foundation: FoundationRead<FoundationReadModel> | null;
  versions: FoundationRead<FoundationVersionsReadModel> | null;
}

/**
 * The persisted Foundation at `at` (null = in effect now) and its version
 * list. `refresh` re-reads both after a publish. `null` means in flight.
 */
export function useSiteFoundation(
  siteId: string | undefined,
  at: string | null,
  client: SiteFoundationClient,
  refresh: number,
): SiteFoundationState {
  const [state, setState] = useState<SiteFoundationState>({ foundation: null, versions: null });

  useEffect(() => {
    let live = true;
    setState({ foundation: null, versions: null });
    if (siteId === undefined) {
      setState({
        foundation: { status: "not_found", message: "No site is named." },
        versions: null,
      });
      return;
    }
    void Promise.all([client.getFoundation(siteId, at), client.listVersions(siteId)]).then(
      ([foundation, versions]) => {
        if (live) setState({ foundation, versions });
      },
    );
    return () => {
      live = false;
    };
  }, [siteId, at, client, refresh]);

  return state;
}
