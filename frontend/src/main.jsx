// src/main.jsx
import * as React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles/globals.css";

/**
 * Application entry point. Vite's index.html loads this file via
 * <script type="module" src="/src/main.jsx"></script>, and this is
 * the only place ReactDOM.createRoot() is called in the whole app.
 *
 * React.StrictMode is enabled deliberately — it double-invokes
 * component bodies, effects, and reducers in development to surface
 * side-effect bugs early (e.g. an effect that fires an API call
 * without proper cleanup, or a mutation that isn't idempotent).
 * It has no effect in production builds.
 */
const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error(
    "Root element with id 'root' not found. Check that index.html contains <div id=\"root\"></div>."
  );
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);