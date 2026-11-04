/**
 * CH5a2-R4(c): the client renders a link only from its Ref sibling. A body that still carries the legacy `href`
 * (or `links`) text but no `link_ref` (or `link_refs`) renders no link at all.
 */
import { render, screen } from "@testing-library/react";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { describe, expect, it } from "vitest";

import { boardBody, fakeOutcomeBoard, outcomeWarning } from "../../test/outcomeBoardFixture";
import { settledScreen } from "../../test/settled";
import { findingRow } from "../../estate/__tests__/estateFixtures";
import { findingLinkLive } from "../../estate/findingIndex";
import { EarlyWarningList } from "../EarlyWarnings";
import { OutcomeBoard } from "../OutcomeBoard";

/** A deep copy without any `link_ref` / `link_refs` key; every legacy href text stays. */
function withoutRefs<T>(value: T): T {
  if (Array.isArray(value)) return value.map(withoutRefs) as T;
  if (value === null || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value).filter(([k]) => k !== "link_ref" && k !== "link_refs").map(([k, v]) => [k, withoutRefs(v)]),
  ) as T;
}

async function renderBoard(body = boardBody()) {
  const fake = fakeOutcomeBoard({ status: "loaded", value: body });
  render(
    <MemoryRouter>
      <OutcomeBoard client={fake.client} siteCode="KOBO-001" query={{ date: "2026-10-06" }} />
    </MemoryRouter>,
  );
  await settledScreen();
  return screen.getByRole("region", { name: "Outcomes at this site" });
}

describe("CH-5a2a links render only from link_ref", () => {
  it("boardWithRefsRendersLinks", async () => {
    const board = await renderBoard();
    expect(board.querySelectorAll("a[href]").length).toBeGreaterThan(0); // the set is not empty
  });

  it("boardWithoutLinkRefRendersNoLink", async () => {
    const body = withoutRefs(boardBody());
    expect(JSON.stringify(body)).toContain('"href":"/sites/KOBO-001/'); // the legacy text is still on the body
    const board = await renderBoard(body);
    expect(board.querySelectorAll("a[href^='/sites/'], a[href^='/maintenance/']")).toHaveLength(0);
    expect(board.textContent).toContain("Generator use"); // the item still renders, as text
  });

  it("warningWithoutLinkRefRendersNoLink", () => {
    const warning = outcomeWarning();
    const { unmount } = render(
      <MemoryRouter>
        <EarlyWarningList warnings={[warning]} showSite />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: warning.title })).toHaveAttribute("href", warning.href as string);
    unmount();
    render(
      <MemoryRouter>
        <EarlyWarningList warnings={[withoutRefs(warning)]} showSite />
      </MemoryRouter>,
    );
    expect(screen.queryByRole("link", { name: warning.title })).toBeNull();
    expect(screen.getByText(warning.title)).toBeInTheDocument();
  });

  it("estateFindingGateReadsTheRefNotTheHref", () => {
    const mini = new Set([findingRow(1).site_id]);
    expect(findingLinkLive(findingRow(1), mini)).toBe(true);
    expect(findingLinkLive(withoutRefs(findingRow(1)), mini)).toBe(false);
    // a cold/EV ref is live only with a window, whatever the href text says
    const windowed = `/sites/COLD-1/findings/f?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A05%3A00Z`;
    const cold = findingRow(2, { site_id: "cold-site", links: { finding: windowed, site: "/sites/COLD-1" } });
    expect(findingLinkLive(cold, mini)).toBe(true);
    const bare = findingRow(2, {
      site_id: "cold-site",
      links: { finding: windowed, site: "/sites/COLD-1" },
      link_refs: { finding: { kind: "FINDING", site: "COLD-1", id: "f", revision: "r" }, site: null },
    });
    expect(findingLinkLive(bare, mini)).toBe(false);
  });
});
