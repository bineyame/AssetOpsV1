import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Simulator Lab unavailable shell frame", () => {
  it("renders a Simulator Lab frame that declares simulator execution unavailable", () => {
    renderAt("/simulator-lab");

    expect(
      screen.getByRole("heading", { level: 1, name: "Simulator Lab" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        level: 2,
        name: "Simulator Lab unavailable",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Simulator execution is not available in this build/i),
    ).toBeInTheDocument();
  });

  it("offers no run execution, inspection, or truth comparison action", () => {
    renderAt("/simulator-lab");

    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.queryAllByRole("link")).toHaveLength(0);
  });
});
