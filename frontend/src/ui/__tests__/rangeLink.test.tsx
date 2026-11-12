/** SR-4a (D-SR.2, architect rev 8 §8.3): `carryRange` and `RangeLink` carry the shared range onto Site links only. */
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { RangeLink } from "../RangeLink";
import { carryRange } from "../sharedRange";

const RANGE = "from=2026-11-03T00%3A00%3A00Z&to=2026-11-10T00%3A00%3A00Z";
const ranged = (extra = "") => new URLSearchParams(`from=2026-11-03T00:00:00Z&to=2026-11-10T00:00:00Z${extra}`);

describe("SR-4a carryRange", () => {
  it("adds the range to a Site path and a /performance path", () => {
    expect(carryRange("/sites/KOBO-001/findings", ranged())).toBe(`/sites/KOBO-001/findings?${RANGE}`);
    expect(carryRange("/sites", ranged())).toBe(`/sites?${RANGE}`);
    expect(carryRange("/performance/KOBO-001", ranged())).toBe(`/performance/KOBO-001?${RANGE}`);
  });

  it("keeps a target that names its own range", () => {
    const own = "/sites/COLD-LAB-001?from=2026-11-03T06:00:00Z&to=2026-11-03T09:30:00Z";
    expect(carryRange(own, ranged())).toBe(own);
    expect(carryRange({ pathname: "/sites/EV-LAB-001/ev", search: "?from=a&to=b" }, ranged())).toEqual({ pathname: "/sites/EV-LAB-001/ev", search: "?from=a&to=b" });
  });

  it("keeps a #hash after the query and keeps the target's own parameters", () => {
    expect(carryRange("/sites/KOBO-001/evidence?tab=x#claims", ranged())).toBe(`/sites/KOBO-001/evidence?tab=x&${RANGE}#claims`);
  });

  it("carries onto an object target", () => {
    expect(carryRange({ pathname: "/sites/KOBO-001/work", search: "?view=open", hash: "#top" }, ranged())).toEqual({
      pathname: "/sites/KOBO-001/work",
      search: `?view=open&${RANGE}`,
      hash: "#top",
    });
    expect(carryRange({ pathname: "/sites/KOBO-001" }, ranged())).toEqual({ pathname: "/sites/KOBO-001", search: `?${RANGE}` });
  });

  it("leaves relative and non-Site targets untouched", () => {
    expect(carryRange("evidence", ranged())).toBe("evidence");
    expect(carryRange("../findings", ranged())).toBe("../findings");
    expect(carryRange("/portfolio", ranged())).toBe("/portfolio");
    expect(carryRange("/sitesx", ranged())).toBe("/sitesx");
    expect(carryRange({ search: "?day=2026-11-04" }, ranged())).toEqual({ search: "?day=2026-11-04" });
  });

  it("adds nothing when the address range is absent or invalid", () => {
    expect(carryRange("/sites/KOBO-001", new URLSearchParams())).toBe("/sites/KOBO-001");
    expect(carryRange("/sites/KOBO-001", new URLSearchParams("from=2026-11-10T00:00:00Z&to=2026-11-03T00:00:00Z"))).toBe("/sites/KOBO-001");
    expect(carryRange("/sites/KOBO-001", new URLSearchParams("from=2026-11-03T00:00:00Z"))).toBe("/sites/KOBO-001");
  });

  it("never carries day, hour, event or cursor; carries known_at", () => {
    const params = ranged("&day=2026-11-05&hour=12&event=E1&cursor=c2&known_at=2026-11-09T12:00:00Z");
    expect(carryRange("/sites/KOBO-001", params)).toBe(`/sites/KOBO-001?${RANGE}&known_at=2026-11-09T12%3A00%3A00Z`);
  });
});

describe("SR-4a RangeLink", () => {
  it("renders the carried href", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio?from=2026-11-03T00:00:00Z&to=2026-11-10T00:00:00Z&day=2026-11-05"]}>
        <RangeLink to="/sites/KOBO-001/performance">Performance</RangeLink>
        <RangeLink to="/findings">Findings</RangeLink>
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: "Performance" })).toHaveAttribute("href", `/sites/KOBO-001/performance?${RANGE}`);
    expect(screen.getByRole("link", { name: "Findings" })).toHaveAttribute("href", "/findings");
  });
});
