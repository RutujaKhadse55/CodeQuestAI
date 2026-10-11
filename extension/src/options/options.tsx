import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "../i18n/setup";
import { useTranslation } from "react-i18next";
import "./options.css";

interface Settings {
  backendUrl: string;
  token: string;
  langPref: "en" | "hi" | "mr";
}

function OptionsApp() {
  const { t, i18n } = useTranslation();
  const [settings, setSettings] = useState<Settings>({
    backendUrl: "http://localhost:8000",
    token: "",
    langPref: "en",
  });
  const [saved, setSaved] = useState(false);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);

  // Load persisted settings on mount
  useEffect(() => {
    chrome.storage.sync.get(
      { backendUrl: "http://localhost:8000", token: "", langPref: "en" },
      (items) => {
        const s = items as Settings;
        setSettings(s);
        i18n.changeLanguage(s.langPref);
      }
    );
  }, []);

  const handleSave = () => {
    chrome.storage.sync.set(settings, () => {
      setSaved(true);
      i18n.changeLanguage(settings.langPref);
      setTimeout(() => setSaved(false), 2500);
    });
  };

  const handleHealthCheck = async () => {
    setHealthStatus("Checking…");
    try {
      const res = await chrome.runtime.sendMessage({ type: "HEALTH_CHECK" });
      if (res?.error) {
        setHealthStatus(`❌ ${res.error}`);
      } else {
        setHealthStatus(`✅ Backend OK (v${res.version ?? "?"})`);
      }
    } catch (err) {
      setHealthStatus(`❌ ${String(err)}`);
    }
  };

  return (
    <div className="options-wrap">
      <header className="options-header">
        <span className="logo">🔍</span>
        <div>
          <h1>{t("options.title")}</h1>
          <p className="subtitle">Configure your AI coding mentor</p>
        </div>
      </header>

      <section className="card">
        <label className="field-label">{t("options.backend_url")}</label>
        <input
          id="backend-url"
          type="text"
          className="field-input"
          value={settings.backendUrl}
          onChange={(e) => setSettings({ ...settings, backendUrl: e.target.value })}
          placeholder="http://localhost:8000"
        />

        <label className="field-label">{t("options.token")}</label>
        <input
          id="api-token"
          type="password"
          className="field-input"
          value={settings.token}
          onChange={(e) => setSettings({ ...settings, token: e.target.value })}
          placeholder="your-api-token"
        />

        <label className="field-label">{t("options.language")}</label>
        <select
          id="lang-pref"
          className="field-input"
          value={settings.langPref}
          onChange={(e) =>
            setSettings({ ...settings, langPref: e.target.value as Settings["langPref"] })
          }
        >
          <option value="en">{t("lang.en")}</option>
          <option value="hi">{t("lang.hi")}</option>
          <option value="mr">{t("lang.mr")}</option>
        </select>

        <div className="actions">
          <button id="save-btn" className="btn-primary" onClick={handleSave}>
            {saved ? t("options.saved") : t("options.save")}
          </button>
          <button id="health-btn" className="btn-secondary" onClick={handleHealthCheck}>
            Test Connection
          </button>
        </div>

        {healthStatus && (
          <p className={`health-status ${healthStatus.startsWith("✅") ? "ok" : "err"}`}>
            {healthStatus}
          </p>
        )}
      </section>

      <footer className="options-footer">
        CodeQuest AI v0.1.0 · VORTEXA 3.0
      </footer>
    </div>
  );
}

const root = createRoot(document.getElementById("options-root")!);
root.render(<OptionsApp />);
