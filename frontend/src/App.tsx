import { Route, Routes } from "react-router-dom";

import { OperatorShellFrame } from "./shell/OperatorShellFrame";
import { OperatorShellLayout } from "./shell/OperatorShellLayout";
import { SimulatorLabUnavailableFrame } from "./shell/SimulatorLabUnavailableFrame";
import { SiteConfigurationFrame } from "./shell/SiteConfigurationFrame";
import { SiteDetailsFrame } from "./shell/SiteDetailsFrame";
import { SitesFrame } from "./shell/SitesFrame";

/**
 * T002 route table.
 *
 * Operator route frames (shell home, Sites, Site Details, Site Configuration)
 * render inside `OperatorShellLayout`, which owns operator navigation. The
 * Simulator Lab route stays outside that layout so the operator shell exposes
 * no Simulator Lab entry point; serving behavior for `simulator_lab.enabled`
 * is owned by the Simulator Lab feature gate slice.
 *
 * Site Details and Site Configuration are parameterless, because no Site schema
 * or Site identity exists yet.
 */
export function App() {
  return (
    <Routes>
      <Route element={<OperatorShellLayout />}>
        <Route path="/" element={<OperatorShellFrame />} />
        <Route path="/sites" element={<SitesFrame />} />
        <Route path="/site-details" element={<SiteDetailsFrame />} />
        <Route
          path="/site-configuration"
          element={<SiteConfigurationFrame />}
        />
      </Route>
      <Route path="/simulator-lab" element={<SimulatorLabUnavailableFrame />} />
      <Route
        path="*"
        element={<p>This route is not available in this build.</p>}
      />
    </Routes>
  );
}
