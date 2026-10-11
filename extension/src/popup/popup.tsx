import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./popup.css";

// Logo as a relative import — Vite bundles and inlines it automatically
import logoUrl from "../assets/logo.png";

interface DashSummary {
  totalAttempts: number;
  solvedCount: number;
  topMistake: string | null;
  streak: number;
}

function PopupApp() {
  const [health, setHealth] = useState<"checking" | "ok" | "offline">("checking");
  const [dash, setDash] = useState<DashSummary | null>(null);
  const [tab, setTab] = useState<"home" | "stats">("home");

  useEffect(() => {
    chrome.runtime
      .sendMessage({ type: "HEALTH_CHECK" })
      .then((res) => setHealth(res?.error ? "offline" : "ok"))
      .catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    if (health !== "ok") return;
    // Try real /dashboard from backend
    chrome.runtime
      .sendMessage({ type: "GET_DASHBOARD" })
      .then((data: Record<string, unknown> | null) => {
        if (!data || "error" in data) return;
        const mistakes = (data.mistakes ?? {}) as Record<string, number>;
        const topEntry = Object.entries(mistakes).sort((a, b) => b[1] - a[1])[0];
        const summary: DashSummary = {
          totalAttempts: (data.attempts as number) ?? 0,
          solvedCount: (data.solved as number) ?? 0,
          topMistake: topEntry ? `${topEntry[0].replace(/_/g, " ")} (×${topEntry[1]})` : null,
          streak: 0, // Phase 3: compute from habit_events
        };
        setDash(summary);
        chrome.storage.local.set({ cq_dash: summary });
      })
      .catch(() => {
        // Fallback to cached
        chrome.storage.local.get(["cq_dash"], (items) => {
          if (items.cq_dash) setDash(items.cq_dash as DashSummary);
        });
      });
  }, [health]);

  return (
    <div className="popup-wrap">
      <header className="popup-header">
        <img src={logoUrl} alt="CodeQuest" className="popup-logo" />
        <div>
          <h2>CodeQuest AI</h2>
          <p className="subtitle">AI Coding Mentor</p>
        </div>
        <span className={`badge ${health}`}>
          {health === "checking" ? "…" : health === "ok" ? "● Live" : "✕ Offline"}
        </span>
      </header>

      {/* Tab bar */}
      <div className="popup-tabs">
        <button className={`popup-tab ${tab === "home" ? "active" : ""}`} onClick={() => setTab("home")}>Home</button>
        <button className={`popup-tab ${tab === "stats" ? "active" : ""}`} onClick={() => setTab("stats")}>Stats</button>
      </div>

      {tab === "home" && (
        <div className="popup-body">
          <p className="tip">
            Navigate to a <strong>LeetCode problem</strong>, select your code or press
            <strong> 🔍 Debug</strong> for AI feedback.
          </p>

          <div className="quick-links">
            <a id="open-options" href="#" onClick={(e) => { e.preventDefault(); chrome.runtime.openOptionsPage(); }} className="settings-link">
              ⚙️ Settings
            </a>
            <a href="https://leetcode.com/problems/two-sum/" target="_blank" rel="noreferrer" className="settings-link" style={{ background: "#14532d" }}>
              🚀 Try Two Sum
            </a>
          </div>

          <div className="how-to">
            <div className="step"><span className="step-num">1</span>Open a LeetCode problem</div>
            <div className="step"><span className="step-num">2</span>Write or paste your solution</div>
            <div className="step"><span className="step-num">3</span>Select code + click Debug</div>
            <div className="step"><span className="step-num">4</span>Review verdict, trace &amp; hints</div>
          </div>
        </div>
      )}

      {tab === "stats" && (
        <div className="popup-body">
          {dash ? (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-val">{dash.totalAttempts}</div>
                <div className="stat-label">Attempts</div>
              </div>
              <div className="stat-card">
                <div className="stat-val">{dash.solvedCount}</div>
                <div className="stat-label">Solved</div>
              </div>
              <div className="stat-card">
                <div className="stat-val">{dash.streak}🔥</div>
                <div className="stat-label">Streak</div>
              </div>
              {dash.topMistake && (
                <div className="stat-card" style={{ gridColumn: "1/-1" }}>
                  <div className="stat-label">Top Mistake</div>
                  <div className="stat-val" style={{ fontSize: "0.85rem" }}>{dash.topMistake}</div>
                </div>
              )}
            </div>
          ) : (
            <p className="tip" style={{ textAlign: "center" }}>
              {health === "offline"
                ? "⚠️ Backend offline — start it at localhost:8000"
                : "No stats yet — debug a problem first!"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

const root = createRoot(document.getElementById("popup-root")!);
root.render(<PopupApp />);
