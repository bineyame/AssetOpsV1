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

describe("operator shell route frame", () => {
  it("renders the operator shell frame at the shell route", () => {
    renderAt("/");

    expect(
      screen.getByRole("heading", { level: 1, name: "AssetOps" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Operator shell")).toBeInTheDocument();
  });

  it("states an explicit empty/no-data state instead of placeholder values", () => {
    renderAt("/");

    expect(
      screen.getByRole("heading", { level: 2, name: "No site data" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /No sites are configured and no operational evidence has been recorded/i,
      ),
    ).toBeInTheDocument();
  });

  it("exposes no simulator entry point from the operator shell frame", () => {
    renderAt("/");

    expect(screen.queryByText(/simulator/i)).toBeNull();
  });
});
