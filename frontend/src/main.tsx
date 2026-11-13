import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { applyReviewLabels } from "./ui/reviewLabels";

// The one visual vocabulary, loaded once for the whole app. Tokens first: the
// primitives read them. UQ-FI-1 (D-UQFI.2): the Inter face loads before the tokens.
import "./ui/fonts.css";
import "./ui/tokens.css";
import "./ui/primitives.css";
// POLISH §2 (P-04): the label hide rule, app-wide (the MockDeviation component does not load it itself).
import "./ui/mock-deviation.css";

// POLISH §2 (P-04): review mode is applied first, before the app renders.
applyReviewLabels();

const container = document.getElementById("root");

if (!container) {
  throw new Error("Root container #root was not found in index.html");
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
