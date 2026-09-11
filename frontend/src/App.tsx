import { Route, Routes } from "react-router-dom";

import { OperatorShellFrame } from "./shell/OperatorShellFrame";
import { SimulatorLabUnavailableFrame } from "./shell/SimulatorLabUnavailableFrame";

/**
 * T001 route table.
 *
 * Only the minimal operator shell frame and the Simulator Lab unavailable frame
 * exist. Sites, Site Details, and Site Configuration route frames are owned by
 * a later slice, and serving behavior for `simulator_lab.enabled` is owned by
 * the Simulator Lab feature gate slice.
 */
export function App() {
  return (
    <Routes>
      <Route path="/" element={<OperatorShellFrame />} />
      <Route path="/simulator-lab" element={<SimulatorLabUnavailableFrame />} />
      <Route
        path="*"
        element={<p>This route is not available in this build.</p>}
      />
    </Routes>
  );
}
