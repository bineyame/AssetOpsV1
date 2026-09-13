/**
 * Client for the gated create-a-site API.
 *
 * The client is created with its base path rather than importing one, so this
 * module never spells a simulator URL: `tools/check-architecture.ps1` allows
 * that only in `simulatorLabRoutes.tsx`, which is where the path lives and
 * where this client is constructed.
 *
 * It creates, and only creates. There is no update, rename, duplicate, or
 * delete method, so no screen built on it can offer one.
 *
 * A refusal is a named state carrying the backend's own product copy, not an
 * exception and not a generic failure. The backend is the one place that knows
 * why a create was refused - an identity already in use, a case variant of
 * one, a malformed identity, a missing field - and restating those rules here
 * would be a second copy of them that could drift.
 */

import type { SiteSummary } from "../sites/siteReadModel";
import { isSiteSummary } from "../sites/siteDirectoryClient";

export interface CreateSiteInput {
  template_id: string;
  site_id: string;
  display_name: string;
  location: {
    country: string;
    locality: string;
  };
  timezone: string;
}

export type CreateSiteResult =
  | { status: "created"; site: SiteSummary }
  | { status: "refused"; message: string }
  | { status: "unavailable" };

export interface SiteCreationClient {
  createSite(input: CreateSiteInput): Promise<CreateSiteResult>;
}

/** The shape the API uses for a refusal a screen can render. */
function refusalMessage(body: unknown): string | null {
  const detail = (body as Record<string, unknown>)?.detail;
  if (detail === null || typeof detail !== "object") {
    return null;
  }
  const message = (detail as Record<string, unknown>).message;
  return typeof message === "string" && message.length > 0 ? message : null;
}

export function createSiteCreationClient(basePath: string): SiteCreationClient {
  return {
    async createSite(input: CreateSiteInput): Promise<CreateSiteResult> {
      let response: Response;
      try {
        response = await fetch(basePath, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(input),
        });
      } catch {
        return { status: "unavailable" };
      }

      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }

      if (response.status === 201) {
        return isSiteSummary(body)
          ? { status: "created", site: body }
          : { status: "unavailable" };
      }

      const message = refusalMessage(body);
      return message === null
        ? { status: "unavailable" }
        : { status: "refused", message };
    },
  };
}
