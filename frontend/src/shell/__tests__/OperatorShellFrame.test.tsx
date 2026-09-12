import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";

/**
 * The operator shell frame is served in both gate states. Flags are passed
 * explicitly so the shipped value in `config/app-config.json` cannot change
 * what these assertions mean.
 */
const simulatorLabDisabled = featureFlagsWith(false);

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={simulatorLabDisabled} />
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
