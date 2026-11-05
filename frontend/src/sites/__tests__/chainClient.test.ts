import { describe, expect, it } from "vitest";
import { createChainClient, estateWhyUrl, siteWhyUrl, WHY_SCHEMA, type WhyBody } from "../chainClient";

/** CH-5b3 (CH5b3-R Q2): the per-URL `{etag, body}` memory, `If-None-Match` on repeat, 304 reuse. */

function why(say: string): WhyBody {
  return {
    schema_version: WHY_SCHEMA,
    category: "OPTIMIZE_COST",
    text: {
      title: "Kobo · Optimize cost and efficiency",
      say,
      comes_from: ["a line"],
      days_used: "6 Oct partly checked",
      would_change: "Checking 1 more day",
      evidence_ref: { kind: "EVIDENCE", site: "KOBO-001", capability: "dispatch" },
      evidence_label: "Kobo evidence →",
    },
  };
}

type Answer = { status: number; body?: unknown; etag?: string };

function scripted(answers: Answer[]) {
  const calls: { url: string; ifNoneMatch: string | null; cache?: RequestCache }[] = [];
  const fetchImpl = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const headers = (init?.headers ?? {}) as Record<string, string>;
    calls.push({ url: String(input), ifNoneMatch: headers["If-None-Match"] ?? null, cache: init?.cache });
    const a = answers.shift();
    if (!a) throw new Error("no scripted answer");
    const h = new Headers();
    if (a.etag) h.set("ETag", a.etag);
    return new Response(a.status === 304 ? null : JSON.stringify(a.body ?? null), { status: a.status, headers: h });
  }) as typeof fetch;
  return { calls, client: createChainClient({ fetch: fetchImpl }) };
}

const Q = { date: "2026-10-06", known_at: "2026-10-07T00:00:00Z" };

describe("CH-5b3 chain client", () => {
  it("keysEveryQueryParameterAndTheCategory", () => {
    expect(siteWhyUrl("KOBO-001", "OPTIMIZE_COST", { ...Q, finding_id: "f1", finding_revision_id: "r1" })).toBe(
      "/api/sites/KOBO-001/chain/why?date=2026-10-06&known_at=2026-10-07T00%3A00%3A00Z&finding_id=f1&finding_revision_id=r1&category=OPTIMIZE_COST",
    );
    expect(estateWhyUrl("PROTECT_ASSET", { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", known_at: null })).toBe(
      "/api/estate/chain/why?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&category=PROTECT_ASSET",
    );
  });

  it("sendsIfNoneMatchOnRepeatAndReusesTheBodyOn304", async () => {
    const { calls, client } = scripted([{ status: 200, body: why("first"), etag: '"t1"' }, { status: 304 }]);
    const one = await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", Q);
    const two = await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", Q);
    expect(calls.map((c) => c.ifNoneMatch)).toEqual([null, '"t1"']);
    expect(calls.every((c) => c.cache === "no-store")).toBe(true);
    expect(one).toEqual({ status: "loaded", value: why("first") });
    expect(two).toEqual({ status: "loaded", value: why("first") });
  });

  it("aDifferentParameterIsADifferentKey", async () => {
    const { calls, client } = scripted([
      { status: 200, body: why("a"), etag: '"t1"' },
      { status: 200, body: why("b"), etag: '"t2"' },
      { status: 200, body: why("c"), etag: '"t3"' },
    ]);
    await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", Q);
    await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", { ...Q, known_at: "2026-10-08T00:00:00Z" });
    await client.getSiteWhy("KOBO-001", "PROTECT_ASSET", Q);
    expect(calls.map((c) => c.ifNoneMatch)).toEqual([null, null, null]);
  });

  it("aNon200Non304NeverShowsTheStoredBody", async () => {
    const { calls, client } = scripted([
      { status: 200, body: why("stored"), etag: '"t1"' },
      { status: 500, body: { detail: { code: "STORE_UNAVAILABLE" } } },
      { status: 304 },
      { status: 422, body: { detail: { code: "CATEGORY_UNKNOWN" } } },
    ]);
    await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", Q);
    expect(await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", Q)).toEqual({
      status: "refused",
      httpStatus: 500,
      code: "STORE_UNAVAILABLE",
    });
    // The failure dropped the memory: no validator is sent, and a stray 304 has nothing to reuse.
    expect(await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", Q)).toEqual({ status: "unavailable" });
    expect(calls[2].ifNoneMatch).toBeNull();
    expect(await client.getSiteWhy("KOBO-001", "NOT_A_CATEGORY", Q)).toEqual({
      status: "refused",
      httpStatus: 422,
      code: "CATEGORY_UNKNOWN",
    });
  });

  it("aBodyOfTheWrongShapeIsUnavailableAndNotStored", async () => {
    const { calls, client } = scripted([
      { status: 200, body: { schema_version: "other" }, etag: '"t1"' },
      { status: 200, body: why("ok") },
    ]);
    expect(await client.getEstateWhy("GROW_REVENUE", { from: "a", to: "b", known_at: null })).toEqual({ status: "unavailable" });
    await client.getEstateWhy("GROW_REVENUE", { from: "a", to: "b", known_at: null });
    expect(calls[1].ifNoneMatch).toBeNull();
  });

  it("aNetworkFailureIsUnavailable", async () => {
    const client = createChainClient({ fetch: (async () => Promise.reject(new Error("offline"))) as typeof fetch });
    expect(await client.getSiteWhy("KOBO-001", "OPTIMIZE_COST", Q)).toEqual({ status: "unavailable" });
  });
});
