import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { createEstateClient } from "../../estate/estateClient";
import { OutcomeMatrixBody } from "../../estate/PortfolioOutcomes";
import { OutcomeBoard } from "../OutcomeBoard";
import { createOutcomeBoardClient, type OutcomeBoardRead } from "../outcomeBoardClient";
import { boardBody } from "../../test/outcomeBoardFixture";
import { settledScreen } from "../../test/settled";
import {
  RETRYING_COPY,
  STILL_UNAVAILABLE_COPY,
  TEMPORARILY_UNAVAILABLE,
  fetchRetrying,
} from "../temporarilyUnavailable";

/** INFRA-1 T7 (D-E5.47 rule 4): a 503 TEMPORARILY_UNAVAILABLE is a retrying state, never a data state. */
const UNAVAILABLE_503 = () =>
  new Response(JSON.stringify({ code: TEMPORARILY_UNAVAILABLE, message: "This view is temporarily unavailable. Retrying." }), {
    status: 503,
    headers: { "Content-Type": "application/json" },
  });
const DATA_STATES = /No target set yet|Unknown|PARTIAL/;

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("INFRA-1 temporarily unavailable", () => {
  it("fetchRetrying retries a 503 TEMPORARILY_UNAVAILABLE and stops at the first other answer", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(UNAVAILABLE_503())
      .mockResolvedValueOnce(new Response(JSON.stringify({ ok: 1 }), { status: 200 }));
    vi.stubGlobal("fetch", fetch);
    const onRetrying = vi.fn();
    const { response, body } = await fetchRetrying("/x", onRetrying, [1, 1, 1]);
    expect(response.status).toBe(200);
    expect(body).toEqual({ ok: 1 });
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(onRetrying).toHaveBeenCalledTimes(1);
  });

  it("the board client retries after 2, 4 and 8 s and then reads TEMPORARILY_UNAVAILABLE", async () => {
    vi.useFakeTimers();
    const fetch = vi.fn().mockImplementation(async () => UNAVAILABLE_503());
    vi.stubGlobal("fetch", fetch);
    const onRetrying = vi.fn();
    const pending = createOutcomeBoardClient("/api/sites").getOutcomeBoard("KOBO-001", {}, onRetrying);
    await vi.advanceTimersByTimeAsync(2000 + 4000 + 8000);
    expect(await pending).toEqual({ status: "refused", httpStatus: 503, code: TEMPORARILY_UNAVAILABLE });
    expect(fetch).toHaveBeenCalledTimes(4);
    expect(onRetrying).toHaveBeenCalledTimes(3);
  });

  it("the summary client reads TEMPORARILY_UNAVAILABLE with the still-unavailable copy after its retries", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => UNAVAILABLE_503()));
    const pending = createEstateClient("/api/estate").getOutcomeSummary!({ from: "a", to: "b", known_at: null });
    await vi.advanceTimersByTimeAsync(14000);
    expect(await pending).toEqual({ status: "refused", httpStatus: 503, code: TEMPORARILY_UNAVAILABLE, copy: STILL_UNAVAILABLE_COPY });
  });

  it("a 503 shows the retrying state on the board, then still-unavailable; never No target set yet", async () => {
    let finish: (read: OutcomeBoardRead) => void = () => undefined;
    const client = {
      getOutcomeBoard: (_site: string, _query: unknown, onRetrying?: () => void) => {
        onRetrying?.();
        return new Promise<OutcomeBoardRead>((resolve) => {
          finish = resolve;
        });
      },
    };
    render(
      <MemoryRouter>
        <OutcomeBoard client={client} siteCode="KOBO-001" query={{ from: null, to: null }} />
      </MemoryRouter>,
    );
    expect(await screen.findByText(RETRYING_COPY)).toBeTruthy();
    expect(document.body.textContent).not.toMatch(DATA_STATES);
    await act(async () => finish({ status: "refused", httpStatus: 503, code: TEMPORARILY_UNAVAILABLE }));
    expect(await screen.findByText(STILL_UNAVAILABLE_COPY)).toBeTruthy();
    expect(document.body.textContent).not.toMatch(DATA_STATES);
  });

  it("a loaded board after a retry renders its data (the retrying copy is gone)", async () => {
    const client = {
      getOutcomeBoard: async (_site: string, _query: unknown, onRetrying?: () => void) => {
        onRetrying?.();
        return { status: "loaded", value: boardBody() } as OutcomeBoardRead;
      },
    };
    render(
      <MemoryRouter>
        <OutcomeBoard client={client} siteCode="KOBO-001" query={{ from: null, to: null }} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(document.querySelector("[data-outcome-board]")?.getAttribute("data-outcome-board")).toBe("loaded");
    expect(screen.queryByText(RETRYING_COPY)).toBeNull();
  });

  it("the Portfolio outcome matrix shows the retrying copy for a TEMPORARILY_UNAVAILABLE read", () => {
    render(<OutcomeMatrixBody read={{ status: "refused", httpStatus: 503, code: TEMPORARILY_UNAVAILABLE, copy: RETRYING_COPY }} />);
    expect(screen.getByText(RETRYING_COPY)).toBeTruthy();
    expect(document.body.textContent).not.toMatch(DATA_STATES);
  });
});
