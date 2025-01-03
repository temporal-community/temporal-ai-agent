import React from "react";
import { createRoot } from "react-dom/client";
import App from "./pages/App";
import "./index.css"; // Tailwind imports

const container = document.getElementById("root");
const root = createRoot(container);

root.render(<App />);
