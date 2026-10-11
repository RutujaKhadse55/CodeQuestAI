import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./popup.css";

function PopupApp() {
  const [health, setHealth] = useState<"checking" | "ok" | "offline">("checking");

  useEffect(() => {
    chrome.runtime
      .sendMessage({ type: "HEALTH_CHECK" })
      .then((res) => setHealth(res?.error ? "offline" : "ok"))
      .catch(() => setHealth("offline"));
  }, []);

  return (
    <div className="popup-wrap">
      <header className="popup-header">
        <span className="logo">🔍</span>
        <div>
          <h2>CodeQuest AI</h2>
          <p className="subtitle">AI Coding Mentor</p>
        </div>
        <span className={`badge ${health}`}>
          {health === "checking" ? "…" : health === "ok" ? "Live" : "Offline"}
        </span>
      </header>

      <div className="popup-body">
        <p className="tip">
          Navigate to a <strong>LeetCode problem</strong>, select your code,
          and click <strong>🔍 Debug</strong> to get AI-powered feedback.
        </p>

        <a
          id="open-options"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            chrome.runtime.openOptionsPage();
          }}
          className="settings-link"
        >
          ⚙️ Settings
        </a>
      </div>
    </div>
  );
}

const root = createRoot(document.getElementById("popup-root")!);
root.render(<PopupApp />);
