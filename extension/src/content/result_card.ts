// ─── Result Card — Shadow DOM panel ──────────────────────────────────────────
// Fully matches the CodeQuest reference screenshots.

import type { AnalyzeResponse, TestResult, Diagnosis, Verified, ChatSendResponse, ConsentInfo, ConsentStatus, ChatStreamEvent,
  ExplainProblemResponse, CrewEnvelope, CrewTestReport, CrewTestCase, CrewTraceReport, CrewDebugReport, CrewExplanation } from "../api/types";
import { renderMarkdown, stripMarkdown } from "./markdown";
import { LOGO_DATA_URL } from "../assets/logo";

// ── Styles ────────────────────────────────────────────────────────────────────

const CARD_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:host { all: initial; font-family: 'Inter', system-ui, sans-serif; }
* { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Panel shell ─────────────────────────────────────────────────────────── */
#cq-panel {
  position: fixed;
  top: 0; right: -410px;
  width: 390px; height: 100vh;
  background: #f5efe0;
  border-left: 1px solid #ddd4c0;
  display: flex; flex-direction: column;
  z-index: 2147483646;
  transition: right 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: -6px 0 28px rgba(0,0,0,0.13);
  color: #111827; overflow: hidden;
  font-family: 'Inter', system-ui, sans-serif;
}
#cq-panel.open { right: 0; }

/* ── Header ──────────────────────────────────────────────────────────────── */
.cq-header {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #ede8df;
  flex-shrink: 0;
}
.cq-logo-img {
  width: 36px; height: 36px; object-fit: contain; flex-shrink: 0;
  border-radius: 6px;
}
.cq-title { font-size: 1.05rem; font-weight: 800; color: #111827; flex: 1; }
.cq-badge-oracle {
  display: flex; align-items: center; gap: 5px;
  border: 1.5px solid #22c55e; border-radius: 999px;
  padding: 4px 10px; font-size: 0.62rem; font-weight: 700;
  color: #16a34a; text-transform: uppercase; letter-spacing: 0.06em;
  background: #fff; white-space: nowrap;
}
.cq-badge-oracle::before { content: "✓"; font-size: 0.72rem; }
.cq-badge-unverified {
  border: 1.5px solid #d1d5db; border-radius: 999px;
  padding: 4px 10px; font-size: 0.62rem; font-weight: 700;
  color: #9ca3af; text-transform: uppercase; letter-spacing: 0.06em;
  background: #fff;
}
.cq-close {
  background: none; border: none; cursor: pointer;
  color: #6b7280; font-size: 1.3rem; padding: 2px 4px;
  transition: color 0.15s; font-weight: 300; line-height: 1;
}
.cq-close:hover { color: #111827; }

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.cq-tabs {
  display: flex;
  background: #fff;
  border-bottom: 1.5px solid #ede8df;
  flex-shrink: 0; padding: 0 10px;
}
.cq-tab {
  flex: 1; padding: 13px 4px 11px;
  background: none; border: none;
  border-bottom: 2.5px solid transparent;
  margin-bottom: -1.5px;
  cursor: pointer; font-size: 0.8rem; font-weight: 500;
  color: #9ca3af; font-family: inherit; transition: all 0.15s;
}
.cq-tab.active { color: #b45309; border-bottom-color: #d97706; font-weight: 700; }
.cq-tab:hover:not(.active) { color: #374151; }

/* ── Scrollable body ─────────────────────────────────────────────────────── */
.cq-body { flex: 1; overflow-y: auto; }
.cq-tab-panel { display: none; }
.cq-tab-panel.active { display: block; }

/* ── Section sub-header ──────────────────────────────────────────────────── */
.sec-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px 12px;
}
.sec-title {
  font-size: 0.88rem; font-weight: 800; color: #111827;
  text-transform: uppercase; letter-spacing: 0.06em;
}
.sec-subtitle {
  font-size: 0.78rem; color: #6b7280; padding: 0 20px 14px;
}
.listen-btn {
  display: flex; align-items: center; gap: 6px;
  background: #f5efe0; border: 1.5px solid #d97706; border-radius: 10px;
  color: #b45309; font-size: 0.78rem; font-weight: 600;
  padding: 6px 14px; cursor: pointer; font-family: inherit;
  transition: background 0.15s;
}
.listen-btn:hover { background: #fde68a; }

/* ═══════════════════════════════════════════════════════════════
   DEBUG TAB
══════════════════════════════════════════════════════════════ */
.debug-body { padding: 0 16px 16px; display: flex; flex-direction: column; gap: 10px; }

/* Result card row */
.res-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 12px 14px; display: flex; gap: 12px; align-items: flex-start;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.res-ico {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; margin-top: 1px; font-weight: 700;
}
.res-ico.p { background: #dcfce7; color: #16a34a; }
.res-ico.f { background: #fee2e2; color: #dc2626; }
.res-ico.e { background: #ffedd5; color: #ea580c; }
.res-body { flex: 1; }
.res-kind { font-size: 0.67rem; color: #9ca3af; margin-bottom: 2px; font-weight: 500; }
.res-verdict { font-size: 0.9rem; font-weight: 700; margin-bottom: 4px; }
.vp { color: #16a34a; } .vf { color: #dc2626; } .ve { color: #ea580c; }
.res-detail { font-size: 0.73rem; color: #6b7280; line-height: 1.5; font-family: 'Courier New', monospace; }
.res-detail b { color: #374151; }

/* Diagnosis card */
.diag-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.diag-card-head {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border-bottom: 1px solid #f3f4f6;
}
.diag-ico-box {
  width: 24px; height: 24px; border-radius: 7px;
  background: #fef3c7; display: flex; align-items: center;
  justify-content: center; font-size: 0.78rem;
}
.diag-head-lbl { font-size: 0.65rem; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.07em; }
.diag-card-body { padding: 10px 14px 12px; }
.diag-name  { font-size: 0.9rem; font-weight: 700; color: #111827; margin-bottom: 3px; }
.diag-sub   { font-size: 0.71rem; color: #9ca3af; margin-bottom: 9px; }
.conf-bar   { height: 5px; background: #f3f4f6; border-radius: 3px; overflow: hidden; margin-bottom: 4px; }
.conf-fill  { height: 100%; background: linear-gradient(90deg,#22c55e,#16a34a); border-radius: 3px; transition: width 0.5s; }
.conf-lbl   { font-size: 0.68rem; color: #9ca3af; margin-bottom: 8px; }
.div-chip {
  background: #f9fafb; border-radius: 8px; padding: 8px 11px;
  font-size: 0.73rem; font-family: 'Courier New', monospace; line-height: 1.7; color: #6b7280;
}
.dline { color: #d97706; font-weight: 700; }
.dvar  { color: #059669; font-weight: 600; }
.dval  { color: #dc2626; }
.dexp  { color: #16a34a; }

/* Explanation card */
.expl-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.expl-head {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border-bottom: 1px solid #f3f4f6;
}
.expl-body { padding: 10px 14px 12px; font-size: 0.84rem; color: #374151; line-height: 1.6; }

/* ═══════════════════════════════════════════════════════════════
   TRACE TAB — dark card with timeline
══════════════════════════════════════════════════════════════ */
.trace-outer { padding: 0 16px 16px; display: flex; flex-direction: column; gap: 12px; }

.trace-dark-card {
  background: #1a1f2e; border-radius: 16px; padding: 6px 0 0;
  overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.25);
}
.trace-timeline { padding: 12px 16px 4px; }
.trace-tl-row {
  display: flex; align-items: center; gap: 12px; position: relative;
  padding-bottom: 4px;
}
/* Dashed vertical connector */
.trace-tl-row:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 12px; top: 28px;
  width: 1px; height: calc(100% + 4px);
  border-left: 2px dashed #374151;
}
.tl-icon {
  width: 24px; height: 24px; flex-shrink: 0; z-index: 1;
  display: flex; align-items: center; justify-content: center;
}
.tl-pin {
  font-size: 1.2rem; line-height: 1; margin-top: -4px;
}
.tl-circle {
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid #374151; background: #1a1f2e;
}
.tl-label {
  font-size: 0.8rem; color: #9ca3af; width: 72px; flex-shrink: 0;
}
.tl-value-box {
  flex: 1; background: #0f1623; border-radius: 8px;
  padding: 9px 12px; font-family: 'Courier New', monospace;
  font-size: 0.88rem; font-weight: 600;
  margin: 3px 0;
}
.tlv-green { color: #4ade80; }
.tlv-amber { color: #f59e0b; }

/* Trace nav row */
.trace-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px 14px;
  border-top: 1px solid #242938;
  margin-top: 8px;
}
.trace-nav-btn {
  display: flex; align-items: center; gap: 5px;
  background: #242938; border: none; border-radius: 10px;
  color: #9ca3af; font-size: 0.78rem; font-weight: 600;
  padding: 8px 14px; cursor: pointer; font-family: inherit;
  transition: background 0.15s;
}
.trace-nav-btn:hover:not(:disabled) { background: #2d3447; color: #e2e8f0; }
.trace-nav-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.trace-nav-btn.next { background: #d97706; color: #fff; }
.trace-nav-btn.next:hover { background: #b45309; }
.trace-nav-center { text-align: center; }
.trace-nav-label { font-size: 0.73rem; color: #9ca3af; margin-bottom: 5px; }
.trace-dots { display: flex; gap: 5px; justify-content: center; }
.trace-dot { width: 8px; height: 8px; border-radius: 50%; background: #374151; }
.trace-dot.active { background: #d97706; }

/* Trace Insight card */
.insight-card {
  background: #fff; border: 1px solid #ede8df; border-radius: 14px;
  padding: 14px 16px; display: flex; gap: 12px; align-items: flex-start;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.insight-ico {
  width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
  background: #fef3c7; display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
}
.insight-body { flex: 1; }
.insight-label { font-size: 0.67rem; font-weight: 800; color: #d97706; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 5px; }
.insight-text { font-size: 0.83rem; color: #374151; line-height: 1.6; }
.code-chip {
  display: inline-block; background: #fde68a; color: #92400e;
  border-radius: 5px; padding: 1px 6px; font-family: 'Courier New', monospace;
  font-size: 0.78rem; font-weight: 600;
}

/* ═══════════════════════════════════════════════════════════════
   HINTS TAB — timeline ladder
══════════════════════════════════════════════════════════════ */
.hints-outer { padding: 0 16px 16px; display: flex; flex-direction: column; gap: 0; }
.hint-ladder { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.hint-row {
  display: flex; gap: 14px; align-items: flex-start; position: relative;
}
.hint-row:not(:last-child) .hint-tl::after {
  content: '';
  position: absolute;
  left: 19px; top: 42px;
  width: 2px; height: calc(100% + 8px);
  border-left: 2px dashed #d1d5db;
  z-index: 0;
}
.hint-tl {
  width: 40px; flex-shrink: 0;
  display: flex; justify-content: center;
  padding-top: 2px; position: relative;
}
.hint-num-circle {
  width: 38px; height: 38px; border-radius: 50%;
  background: #d97706; color: #fff;
  font-size: 1rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(217,119,6,0.35);
  z-index: 1; position: relative;
}
.hint-lock-circle {
  width: 38px; height: 38px; border-radius: 50%;
  background: #f3f4f6; border: 2px solid #d1d5db; color: #9ca3af;
  font-size: 0.9rem;
  display: flex; align-items: center; justify-content: center;
  z-index: 1; position: relative;
}
.hint-card-unlocked {
  flex: 1;
  background: #fffbeb; border: 2px solid #fde68a; border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 2px 8px rgba(217,119,6,0.1);
}
.hint-card-locked {
  flex: 1;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 12px 14px;
}
.hint-card-head-lbl {
  font-size: 0.67rem; font-weight: 800; letter-spacing: 0.07em; text-transform: uppercase;
  margin-bottom: 6px;
}
.hint-card-head-lbl.unlocked { color: #b45309; }
.hint-card-head-lbl.locked   { color: #9ca3af; }
.hint-text-unlocked { font-size: 0.86rem; color: #111827; line-height: 1.55; font-weight: 500; }
.hint-text-locked   { font-size: 0.84rem; color: #9ca3af; line-height: 1.5; display: flex; align-items: center; gap: 5px; }

/* Progressive Guidance insight */
.hint-insight { margin-top: 4px; }

/* ═══════════════════════════════════════════════════════════════
   HIDDEN TESTS TAB
══════════════════════════════════════════════════════════════ */
.hidden-outer { padding: 0 16px 16px; display: flex; flex-direction: column; gap: 12px; }
.ht-intro-card {
  background: #fff; border: 1px solid #ede8df; border-radius: 14px;
  padding: 18px 16px; text-align: center;
}
.ht-intro-text { font-size: 0.84rem; color: #6b7280; line-height: 1.6; margin-bottom: 14px; }
.ht-intro-text strong { color: #b45309; }
.ht-gen-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: linear-gradient(160deg, #f59e0b, #d97706);
  color: #fff; border: none; border-radius: 12px;
  padding: 12px 28px; cursor: pointer;
  font-size: 0.9rem; font-weight: 700; font-family: inherit;
  box-shadow: 0 3px 10px rgba(217,119,6,0.3);
  transition: opacity 0.15s, transform 0.1s;
}
.ht-gen-btn:hover { opacity: 0.9; transform: translateY(-1px); }
.ht-gen-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

/* Dark test case card */
.tc-card {
  background: #1a1f2e; border-radius: 14px; overflow: hidden;
  box-shadow: 0 3px 12px rgba(0,0,0,0.2);
}
.tc-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 11px 16px; border-bottom: 1px solid #242938;
}
.tc-head-lbl {
  font-size: 0.68rem; font-weight: 800; color: #d97706;
  text-transform: uppercase; letter-spacing: 0.09em; font-family: 'Courier New', monospace;
}
.tc-copy-btn {
  background: none; border: none; cursor: pointer; color: #6b7280;
  font-size: 0.85rem; padding: 2px; transition: color 0.15s;
}
.tc-copy-btn:hover { color: #e2e8f0; }
.tc-body {
  padding: 12px 16px; font-family: 'Courier New', monospace; font-size: 0.82rem; line-height: 1.8;
}
.tc-in  { color: #60b3f8; font-weight: 700; }
.tc-out { color: #4ade80; font-weight: 700; }
.tc-val { color: #e2e8f0; }

/* ═══════════════════════════════════════════════════════════════
   CHAT TAB
══════════════════════════════════════════════════════════════ */
#tab-chat { height: 100%; min-height: 450px; }
.chat-wrap { display: flex; flex-direction: column; height: 100%; background: #fff; }
.chat-hero {
  padding: 16px 20px 12px; border-bottom: 1px solid #f3f4f6; flex-shrink: 0;
}
.chat-hero-row { display: flex; align-items: center; gap: 10px; margin-bottom: 3px; }
.chat-hero-logo-img {
  width: 32px; height: 32px; object-fit: contain; border-radius: 6px; flex-shrink: 0;
}
.chat-hero-name  { font-size: 1rem; font-weight: 800; color: #111827; }
.chat-hero-title { font-size: 0.84rem; font-weight: 600; color: #374151; }
.chat-hero-sub   { font-size: 0.75rem; color: #9ca3af; }
.chat-actions {
  display: flex; gap: 8px; padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6; flex-shrink: 0;
  background: #faf9f7;
}
.cab {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 5px;
  background: linear-gradient(160deg, #f59e0b, #d97706);
  border: none; border-radius: 12px; padding: 12px 6px;
  cursor: pointer; font-family: inherit;
  box-shadow: 0 2px 8px rgba(217,119,6,0.25);
  transition: transform 0.12s, box-shadow 0.12s;
}
.cab:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(217,119,6,0.35); }
.cab:active { transform: translateY(0); }
.cab-icon  { font-size: 1.1rem; }
.cab-label { font-size: 0.67rem; font-weight: 700; color: #fff; text-align: center; line-height: 1.2; }
.chat-messages {
  flex: 1; overflow-y: auto; display: flex; flex-direction: column;
  gap: 12px; padding: 14px 16px; background: #faf9f7;
}
.chat-bubble { display: flex; gap: 9px; align-items: flex-start; animation: cqfade 0.18s ease; }
@keyframes cqfade { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:none} }
.chat-av {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #60b3f8, #1d7eef);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 800; color: #fff;
}
.chat-text {
  background: #fff; border: 1px solid #e5e7eb;
  border-radius: 4px 14px 14px 14px;
  padding: 10px 13px; font-size: 0.84rem; color: #374151;
  line-height: 1.55; max-width: 82%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); white-space: pre-wrap; overflow-wrap: anywhere;
}
.chat-col { display: flex; flex-direction: column; gap: 4px; max-width: 86%; min-width: 0; }
.chat-col .chat-text { max-width: 100%; }
/* rendered Markdown (assistant replies) */
.chat-text.md { white-space: normal; }
.md > :first-child { margin-top: 0; } .md > :last-child { margin-bottom: 0; }
.md p { margin: 0 0 9px; }
.md strong { font-weight: 700; color: #111827; } .md em { font-style: italic; } .md del { opacity: .65; }
.md ul, .md ol { margin: 4px 0 9px; padding-left: 20px; } .md li { margin: 3px 0; } .md li > ul, .md li > ol { margin: 3px 0; }
.md h3, .md h4, .md h5 { margin: 12px 0 5px; font-weight: 700; color: #111827; line-height: 1.3; }
.md h3 { font-size: 1.02rem; } .md h4 { font-size: .93rem; } .md h5 { font-size: .86rem; text-transform: none; }
.md code { background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 4px; padding: 1px 5px; font: .78rem/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; color: #b45309; }
.md .cq-code { margin: 9px 0; border-radius: 9px; overflow: hidden; border: 1px solid #1e293b; background: #0f172a; }
.md .cq-code-head { display: flex; align-items: center; justify-content: space-between; padding: 4px 10px; background: #1e293b; color: #94a3b8; font-size: .68rem; text-transform: lowercase; }
.md .cq-copy { background: transparent; color: #cbd5e1; border: 1px solid #475569; border-radius: 5px; padding: 1px 8px; font-size: .66rem; cursor: pointer; }
.md .cq-copy:hover { background: #334155; }
.md .cq-code pre { margin: 0; padding: 10px 12px; overflow-x: auto; white-space: pre; }
.md .cq-code pre code { background: none; border: 0; padding: 0; color: #e2e8f0; font-size: .77rem; }
.md blockquote { margin: 7px 0; padding: 5px 11px; border-left: 3px solid #d97706; background: #fffbeb; color: #92400e; border-radius: 0 6px 6px 0; }
.md blockquote > :last-child { margin-bottom: 0; }
.md .cq-table { overflow-x: auto; margin: 7px 0; }
.md table { border-collapse: collapse; font-size: .78rem; } .md th, .md td { border: 1px solid #e5e7eb; padding: 4px 9px; text-align: left; } .md th { background: #f9fafb; font-weight: 700; }
.md hr { border: 0; border-top: 1px solid #e5e7eb; margin: 11px 0; }
.md a { color: #1d7eef; text-decoration: underline; }
.chat-chips { display: flex; gap: 5px; flex-wrap: wrap; padding-left: 2px; }
.chat-chip { font-size: .64rem; font-weight: 600; color: #6b7280; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 999px; padding: 1px 8px; }
.chat-chip.good { color: #047857; background: #ecfdf5; border-color: #a7f3d0; }
.chat-chip.warn { color: #92400e; background: #fffbeb; border-color: #fde68a; }
.chat-tools { display: flex; gap: 6px; padding-left: 2px; opacity: 0; transition: opacity .15s; }
.chat-col:hover .chat-tools, .chat-col:focus-within .chat-tools { opacity: 1; }
.chat-tool { background: none; border: 0; color: #9ca3af; font-size: .68rem; cursor: pointer; padding: 0 2px; }
.chat-tool:hover { color: #374151; }
.cq-caret::after { content: "▍"; margin-left: 1px; color: #d97706; animation: cqblink 1s steps(2) infinite; }
@keyframes cqblink { 50% { opacity: 0; } }
.chat-bubble.user { flex-direction: row-reverse; }
.chat-bubble.user .chat-av { background: linear-gradient(135deg, #374151, #1f2937); }
.chat-bubble.user .chat-text {
  background: #1f2937; border-color: #374151;
  border-radius: 14px 4px 14px 14px; color: #f9fafb;
}
.tdots { display: flex; gap: 4px; align-items: center; padding: 3px 0; }
.tdots span {
  width: 7px; height: 7px; border-radius: 50%; background: #d97706;
  animation: cqdot 1.2s infinite;
}
.tdots span:nth-child(2) { animation-delay: 0.18s; }
.tdots span:nth-child(3) { animation-delay: 0.36s; }
@keyframes cqdot { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }
.chat-input-row {
  display: flex; align-items: center; gap: 8px;
  padding: 11px 14px; border-top: 1px solid #f3f4f6;
  flex-shrink: 0; background: #fff;
}
.chat-input {
  flex: 1; background: #f9fafb; border: 1.5px solid #e5e7eb;
  border-radius: 22px; padding: 9px 16px;
  color: #111827; font-size: 0.82rem; font-family: inherit; outline: none;
  transition: border-color 0.15s;
}
.chat-input:focus { border-color: #d97706; background: #fff; }
.chat-input::placeholder { color: #9ca3af; }
.chat-send {
  width: 36px; height: 36px; flex-shrink: 0;
  background: linear-gradient(135deg, #d97706, #b45309);
  color: #fff; border: none; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 0.9rem;
  transition: opacity 0.15s, transform 0.1s;
  box-shadow: 0 2px 6px rgba(217,119,6,0.3);
}
.chat-send:hover { opacity: 0.88; transform: scale(1.07); }

/* ── Shared ──────────────────────────────────────────────────────────────── */
.cq-warn {
  background: #fffbeb; border-bottom: 1px solid #fde68a;
  padding: 8px 20px; font-size: 0.73rem; color: #92400e;
  flex-shrink: 0; line-height: 1.4;
}
.cq-loading {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 12px; height: 200px;
  color: #9ca3af; font-size: 0.85rem;
}
.cq-spinner {
  width: 30px; height: 30px;
  border: 3px solid #ede8df; border-top-color: #d97706;
  border-radius: 50%; animation: cqspin 0.8s linear infinite;
}
@keyframes cqspin { to { transform: rotate(360deg); } }
.cq-error {
  margin: 16px; background: #fef2f2; border: 1px solid #fecaca;
  border-radius: 12px; padding: 14px; color: #dc2626; font-size: 0.84rem; line-height: 1.5;
}
.cq-empty {
  margin: 16px; background: #fff; border: 1px solid #e5e7eb;
  border-radius: 12px; padding: 18px; color: #9ca3af;
  font-size: 0.84rem; text-align: center; line-height: 1.5;
}
`;

// ── Helpers ───────────────────────────────────────────────────────────────────

function icoClass(o: string) { return o === "passed" ? "p" : o === "wrong_output" ? "f" : "e"; }
function icoChar(o: string)  { return o === "passed" ? "✓" : o === "wrong_output" ? "✕" : "!"; }
function vcls(o: string)     { return o === "passed" ? "vp" : o === "wrong_output" ? "vf" : "ve"; }
function kindLabel(k: string) {
  return k === "example" ? "Example Test Case" : k === "run_capture" ? "Your Run" : "Fuzz Test Case";
}
function mistakeLabel(cls: string | null | undefined) {
  if (!cls) return "Unknown Issue";
  return cls.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
function esc(t: unknown): string {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c] as string));
}

/** AI crew call through the service worker; null when the backend / FEATURE_CREW is unavailable. */
async function crew<T>(agent: "explain" | "tests" | "debug" | "trace", body: Record<string, unknown>): Promise<CrewEnvelope<T> | null> {
  try {
    const r = await chrome.runtime.sendMessage({ type: "CREW", agent, body }) as (CrewEnvelope<T> & { error?: string }) | null;
    return r && !r.error && r.result ? r : null;
  } catch { return null; }
}

export function playText(text: string) {
  if (!text) return;
  chrome.runtime.sendMessage({ type: "PLAY_TTS", text, lang: "en" }).catch(() => {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text); u.rate = 0.92; speechSynthesis.speak(u);
  });
}
function stopTTS() {
  speechSynthesis.cancel();
  chrome.runtime.sendMessage({ type: "STOP_TTS" }).catch(() => {});
}

// ── Panel class ───────────────────────────────────────────────────────────────

export class ResultCard {
  private host: HTMLDivElement;
  private shadow: ShadowRoot;
  private panel: HTMLDivElement;
  private activeTab = "verdict";
  private response: AnalyzeResponse | null = null;
  private attemptId: number | null = null;
  private slug = "";
  private unsupportedLang: string | null = null;
  private explanationOnly: string | null = null;
  private reviewCode = "";
  private reviewLang = "";
  private reviewSent = false;
  private traceIter = 1;
  private traceTotalIter = 3; // simulated steps; Phase 3: from real tracer
  private chatSend: ((text: string) => void) | null = null;
  private hiddenList: CrewTestCase[] | null = null;   // AI-generated (and sandbox-run) test cases; null = not loaded
  private hiddenInfo = "";
  private hiddenBusy = false;
  private explainBusy = false;
  private traceLoaded = false;
  private explainText = "";

  constructor() {
    this.host = document.createElement("div");
    this.host.id = "codequest-result-host";
    this.host.style.cssText = "position:fixed;top:0;right:0;z-index:2147483646;pointer-events:none;";
    document.documentElement.appendChild(this.host);
    this.shadow = this.host.attachShadow({ mode: "open" });
    const s = document.createElement("style"); s.textContent = CARD_CSS;
    this.shadow.appendChild(s);
    this.panel = document.createElement("div"); this.panel.id = "cq-panel";
    this.shadow.appendChild(this.panel);
  }

  // ── Public API ──────────────────────────────────────────────────────────────

  showLoading(msg = "Analyzing your code…"): void {
    this.panel.classList.add("open"); this.host.style.pointerEvents = "all";
    this.panel.innerHTML = `${this.hdr(null)}<div class="cq-loading"><div class="cq-spinner"></div><span>${msg}</span></div>`;
    this.shadow.getElementById("cq-close-btn")?.addEventListener("click", () => this.close());
  }

  showError(title: string, detail?: string): void {
    this.panel.classList.add("open"); this.host.style.pointerEvents = "all";
    this.panel.innerHTML = `${this.hdr(null)}<div class="cq-error"><strong>${title}</strong>${detail ? `<br><br><small>${detail}</small>` : ""}</div>`;
    this.shadow.getElementById("cq-close-btn")?.addEventListener("click", () => this.close());
  }

  /** The learner's code + editor language, used for the AI review when the code cannot be executed. */
  setReviewCode(code: string, language: string): void { this.reviewCode = code; this.reviewLang = language; this.reviewSent = false; }

  showResults(res: AnalyzeResponse, slug: string, unsupportedLang?: string, explanationOnly?: string, startTab?: string): void {
    this.response = res; this.attemptId = res.attempt_id;
    this.slug = slug; this.unsupportedLang = unsupportedLang ?? null;
    this.explanationOnly = explanationOnly ?? null;
    this.hiddenList = null; this.hiddenInfo = ""; this.traceLoaded = false;
    this.activeTab = startTab ?? (explanationOnly ? "chat" : "verdict"); this.traceIter = 1; // nothing ran: open the chat directly
    // estimate trace steps from iteration field
    if (res.diagnosis?.divergence?.iteration) this.traceTotalIter = Math.max(3, res.diagnosis.divergence.iteration + 1);
    this.panel.classList.add("open"); this.host.style.pointerEvents = "all";
    this.render();
  }

  /** True when the panel already holds results for this problem (so a toolbar action can just switch tabs). */
  hasResultsFor(slug: string): boolean { return !!this.response && this.slug === slug; }

  /** Switch the visible tab (no re-render). */
  switchTab(id: string): void {
    this.activeTab = id;
    this.panel.classList.add("open"); this.host.style.pointerEvents = "all";
    this.shadow.querySelectorAll(".cq-tab").forEach((b) => b.classList.toggle("active", (b as HTMLElement).dataset.tab === id));
    this.shadow.querySelectorAll(".cq-tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${id}`));
    if (id === "explain") void this.prefillExplain();
    if (id === "trace") void this.loadCrewTrace();
    if (id === "hiddentests" && !this.hiddenInfo) void this.loadHidden();
  }

  /**
   * Toolbar entry point for Explain / Concept / Chat: open the Chat tab without running code analysis.
   * `send` asks the question right away; otherwise `text` is only placed in the input box.
   */
  openChat(slug: string, text?: string, send = false): void {
    if (!this.hasResultsFor(slug)) {
      const idle: AnalyzeResponse = { attempt_id: 0, verified: "unverified", results: [], diagnosis: null, explanation: null, flags: [], allowed_hint_level: 1 };
      this.showResults(idle, slug, undefined, undefined, "chat");
    } else this.switchTab("chat");
    if (!text) return;
    if (send && this.chatSend) this.chatSend(text);
    else {
      const input = this.shadow.getElementById("cq-chat-input") as HTMLInputElement | null;
      if (input) { input.value = text; input.focus(); }
    }
  }

  close(): void { this.panel.classList.remove("open"); this.host.style.pointerEvents = "none"; stopTTS(); }
  isOpen(): boolean { return this.panel.classList.contains("open"); }

  // ── Header ──────────────────────────────────────────────────────────────────

  private hdr(verified: "oracle-verified" | "unverified" | null): string {
    const badge = verified === "oracle-verified"
      ? `<span class="cq-badge-oracle">Oracle Verified</span>`
      : verified === "unverified"
      ? `<span class="cq-badge-unverified">Unverified</span>` : "";
    return `<div class="cq-header">
      <img class="cq-logo-img" src="${LOGO_DATA_URL}" alt="CodeQuest" />
      <span class="cq-title">CodeQuest AI</span>
      ${badge}
      <button class="cq-close" id="cq-close-btn">×</button>
    </div>`;
  }

  private tabs(): string {
    const t = [
      { id: "verdict", lbl: "Debug" }, { id: "explain", lbl: "Explain" }, { id: "trace", lbl: "Trace" },
      { id: "hints",   lbl: "Hints" }, { id: "hiddentests", lbl: "Hidden" },
      { id: "chat",    lbl: "Chat"  },
    ];
    return `<div class="cq-tabs">${t.map((x) =>
      `<button class="cq-tab${this.activeTab === x.id ? " active" : ""}" data-tab="${x.id}">${x.lbl}</button>`
    ).join("")}</div>`;
  }

  // ── Debug tab ───────────────────────────────────────────────────────────────

  private debugTab(res: AnalyzeResponse): string {
    const rows = (res.results ?? [] as TestResult[]).map((r) => {
      const det: string[] = [];
      if (r.input) det.push(`<div class="res-detail"><b>Input:</b> ${r.input}</div>`);
      if (r.outcome !== "passed" && r.actual != null)
        det.push(`<div class="res-detail"><b>Output: ${r.actual}</b>&nbsp;|&nbsp;Expected: ${r.expected ?? "?"}</div>`);
      if (r.error) det.push(`<div class="res-detail">${r.error}</div>`);
      return `<div class="res-card">
        <div class="res-ico ${icoClass(r.outcome)}">${icoChar(r.outcome)}</div>
        <div class="res-body">
          <div class="res-kind">${kindLabel(r.kind)}</div>
          <div class="res-verdict ${vcls(r.outcome)}">${r.outcome.replace(/_/g, " ")}</div>
          ${det.join("")}
        </div>
      </div>`;
    }).join("") || `<div class="cq-empty">No test results yet.</div>`;

    const diagHtml = res.diagnosis ? `
      <div class="diag-card">
        <div class="diag-card-head">
          <div class="diag-ico-box">🔬</div>
          <span class="diag-head-lbl">Diagnosis</span>
        </div>
        <div class="diag-card-body">
          <div class="diag-name">${mistakeLabel(res.diagnosis.mistake_class)}</div>
          ${res.diagnosis.failure_class ? `<div class="diag-sub">Failure class: ${res.diagnosis.failure_class}</div>` : ""}
          <div class="conf-bar"><div class="conf-fill" style="width:${Math.round(res.diagnosis.confidence * 100)}%"></div></div>
          <div class="conf-lbl">Confidence: ${Math.round(res.diagnosis.confidence * 100)}%</div>
          ${res.diagnosis.divergence?.variable ? `<div class="div-chip">
            <span class="dline">📍 Line ${res.diagnosis.divergence.line ?? "?"}: </span>
            <span class="dvar">${res.diagnosis.divergence.variable}</span><br>
            = <span class="dval">${JSON.stringify(res.diagnosis.divergence.actual)}</span>
            &nbsp;(expected <span class="dexp">${JSON.stringify(res.diagnosis.divergence.expected)}</span>)
          </div>` : ""}
        </div>
      </div>` : "";

    const flags = (res.flags ?? []).filter(Boolean);
    const flagsHtml = flags.length
      ? `<div style="display:flex;flex-wrap:wrap;gap:5px;">
           ${flags.map((f) => `<span style="font-size:0.65rem;padding:2px 8px;border-radius:5px;background:#f3f4f6;color:#9ca3af;">${f}</span>`).join("")}
         </div>` : "";

    return `<div class="cq-tab-panel${this.activeTab === "verdict" ? " active" : ""}" id="tab-verdict">
      <div class="sec-head">
        <span class="sec-title">Test Results</span>
        <button class="listen-btn" id="cq-speak-debug">🔊 Listen</button>
      </div>
      <div class="debug-body">
        ${rows}
        ${diagHtml}
        ${flagsHtml}
        <div class="expl-card">
          <div class="expl-head">
            <div class="diag-ico-box">🤖</div>
            <span class="diag-head-lbl">AI Debug Report</span>
          </div>
          <div class="expl-body" id="cq-ai-debug">
            <button class="ht-gen-btn" id="cq-ai-debug-btn">Run AI analysis</button>
            <span style="font-size:.7rem;color:#9ca3af;margin-left:6px;">Root cause and fix steps in words. No full solution.</span>
          </div>
        </div>
        <div class="expl-card">
          <div class="expl-head">
            <div class="diag-ico-box">📝</div>
            <span class="diag-head-lbl">Explanation</span>
          </div>
          <div class="expl-body" id="cq-explanation-text">
            ${res.explanation ?? "<span style='color:#9ca3af'>Loading explanation…</span>"}
          </div>
        </div>
      </div>
    </div>`;
  }

  // ── Trace tab ───────────────────────────────────────────────────────────────

  private traceTab(res: AnalyzeResponse): string {
    const d = res.divergence ?? res.diagnosis?.divergence;
    const iter = this.traceIter;
    const total = this.traceTotalIter;

    const darkCard = d && (d.variable || d.line) ? `
      <div class="trace-dark-card">
        <div class="trace-timeline">
          ${this.trow("pin", "Line",      `<span class="tlv-green">${d.line ?? "?"}</span>`)}
          ${this.trow("o",   "Variable",  `<span class="tlv-green">${d.variable ?? "?"}</span>`)}
          ${this.trow("o",   "Expected",  `<span class="tlv-amber">${JSON.stringify(d.expected)}</span>`)}
          ${this.trow("o",   "Actual",    `<span class="tlv-amber">${JSON.stringify(d.actual)}</span>`)}
          ${d.iteration != null ? this.trow("o", "Iteration", `<span class="tlv-amber">${d.iteration}</span>`) : ""}
        </div>
        <div class="trace-nav">
          <button class="trace-nav-btn" id="cq-trace-prev" ${iter <= 1 ? "disabled" : ""}>‹ Previous</button>
          <div class="trace-nav-center">
            <div class="trace-nav-label">Iteration ${iter} of ${total}</div>
            <div class="trace-dots">
              ${Array.from({ length: total }, (_, i) =>
                `<div class="trace-dot${i + 1 === iter ? " active" : ""}"></div>`
              ).join("")}
            </div>
          </div>
          <button class="trace-nav-btn next" id="cq-trace-next" ${iter >= total ? "disabled" : ""}>Next ›</button>
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-ico">💡</div>
        <div class="insight-body">
          <div class="insight-label">Trace Insight</div>
          <div class="insight-text">
            At line <span class="code-chip">${d.line ?? "?"}</span>, the variable
            <span class="code-chip">${d.variable ?? "?"}</span> is
            <span class="code-chip">${JSON.stringify(d.actual)}</span>, but the
            expected state contains ${d.expected && Object.keys(d.expected as object).length
              ? `key <span class="code-chip">${Object.keys(d.expected as object)[0]}</span> with value <span class="code-chip">${Object.values(d.expected as object)[0]}</span>`
              : "different values"}.
          </div>
        </div>
      </div>` : `<div class="cq-empty">No trace data yet.<br>Trace appears when a fuzz test reveals a divergence.</div>`;

    return `<div class="cq-tab-panel${this.activeTab === "trace" ? " active" : ""}" id="tab-trace">
      <div class="sec-head">
        <span class="sec-title">Variable Trace</span>
        <button class="listen-btn" id="cq-speak-trace">🔊 Listen</button>
      </div>
      <div class="trace-outer">${darkCard}
        <div id="cq-crew-trace" class="expl-card" style="margin-top:10px;"><div class="expl-body" style="color:#9ca3af">Open this tab to record a real step-by-step execution trace…</div></div>
      </div>
    </div>`;
  }

  private trow(iconType: "pin" | "o", label: string, valueHtml: string): string {
    const icon = iconType === "pin"
      ? `<div class="tl-icon"><span class="tl-pin">📍</span></div>`
      : `<div class="tl-icon"><div class="tl-circle"></div></div>`;
    return `<div class="trace-tl-row">
      ${icon}
      <span class="tl-label">${label}</span>
      <div class="tl-value-box">${valueHtml}</div>
    </div>`;
  }

  // ── Hints tab ───────────────────────────────────────────────────────────────

  private hintsTab(res: AnalyzeResponse): string {
    const maxLevel = res.allowed_hint_level ?? 1;
    const unlockMsg: Record<number, string> = {
      2: "Hint 2 — unlocks after 2+ attempts or 3 min",
      3: "Hint 3 — unlocks after 3+ attempts or 6 min",
      4: "Hint 4 — unlocks after 4+ attempts or 10 min",
    };
    const rows = [1, 2, 3, 4].map((lv) => {
      if (lv <= maxLevel) {
        return `<div class="hint-row">
          <div class="hint-tl"><div class="hint-num-circle">${lv}</div></div>
          <div class="hint-card-unlocked">
            <div class="hint-card-head-lbl unlocked">Hint ${lv}</div>
            <div class="hint-text-unlocked" id="cq-hint-text-${lv}">Loading…</div>
          </div>
        </div>`;
      }
      return `<div class="hint-row">
        <div class="hint-tl"><div class="hint-lock-circle">🔒</div></div>
        <div class="hint-card-locked">
          <div class="hint-card-head-lbl locked">Hint ${lv}</div>
          <div class="hint-text-locked">🔒 ${unlockMsg[lv] ?? `Hint ${lv} — unlocks later`}</div>
        </div>
      </div>`;
    }).join("");

    return `<div class="cq-tab-panel${this.activeTab === "hints" ? " active" : ""}" id="tab-hints">
      <div class="sec-head">
        <span class="sec-title">Tiered Hints</span>
        <button class="listen-btn" id="cq-speak-hints">🔊 Listen</button>
      </div>
      <div class="sec-subtitle">Hints unlock as you attempt more solutions.</div>
      <div class="hints-outer">
        <div class="hint-ladder">${rows}</div>
        <div class="insight-card hint-insight">
          <div class="insight-ico">💡</div>
          <div class="insight-body">
            <div class="insight-label">Progressive Guidance</div>
            <div class="insight-text">Each hint reveals one more step — without giving away the full solution.</div>
          </div>
        </div>
      </div>
    </div>`;
  }

  // ── Explain tab: problem URL + LeetCode username -> the backend fetches the problem and explains it ──────

  private explainTab(): string {
    return `<div class="cq-tab-panel${this.activeTab === "explain" ? " active" : ""}" id="tab-explain">
      <div class="sec-head">
        <span class="sec-title">Explain Problem</span>
        <button class="listen-btn" id="cq-speak-explain">🔊 Listen</button>
      </div>
      <div class="hidden-outer">
        <div class="ht-intro-card" style="flex-direction:column;align-items:stretch;gap:6px;">
          <label style="font-size:.7rem;font-weight:600;color:#6b7280">Problem link</label>
          <input class="chat-input" id="cq-ex-url" type="text" placeholder="https://leetcode.com/problems/two-sum/" style="width:100%;box-sizing:border-box" />
          <label style="font-size:.7rem;font-weight:600;color:#6b7280">LeetCode username (optional, personalises the explanation)</label>
          <input class="chat-input" id="cq-ex-user" type="text" placeholder="your public LeetCode username" style="width:100%;box-sizing:border-box" />
          <div style="font-size:.66rem;color:#9ca3af">Entering a username lets CodeQuest read your PUBLIC LeetCode profile (solved counts, languages). Leave it empty to skip. You can withdraw this from Chat → Profile access.</div>
          <button class="ht-gen-btn" id="cq-ex-run">📖 Explain this problem</button>
        </div>
        <div id="cq-ex-out"><div class="cq-empty">Paste a problem link (the current page is filled in) and press Explain.</div></div>
      </div>
    </div>`;
  }

  private problemUrl(): string {
    const m = location.pathname.match(/\/problems\/([^/?#]+)/);
    return m ? `https://leetcode.com/problems/${m[1]}/` : "";
  }

  /** Fill the inputs once: current page URL and the username already authorised (if any). */
  private async prefillExplain(): Promise<void> {
    const url = this.shadow.getElementById("cq-ex-url") as HTMLInputElement | null;
    const user = this.shadow.getElementById("cq-ex-user") as HTMLInputElement | null;
    if (url && !url.value) url.value = this.problemUrl();
    if (user && !user.value) {
      try {
        const st = await chrome.runtime.sendMessage({ type: "CHAT_STATUS" }) as { granted?: boolean; leetcode_username?: string | null } | null;
        if (st?.granted && st.leetcode_username) user.value = st.leetcode_username;
      } catch { /* offline: leave empty */ }
    }
  }

  /** Run the explanation. `selected` = text the learner highlighted on the page (explained first). */
  private async runExplain(selected?: string): Promise<void> {
    const out = this.shadow.getElementById("cq-ex-out");
    const btn = this.shadow.getElementById("cq-ex-run") as HTMLButtonElement | null;
    const url = (this.shadow.getElementById("cq-ex-url") as HTMLInputElement | null)?.value.trim() ?? "";
    const username = (this.shadow.getElementById("cq-ex-user") as HTMLInputElement | null)?.value.trim() ?? "";
    if (!out || this.explainBusy) return;
    if (!url) { out.innerHTML = `<div class="cq-error">Enter a LeetCode problem link first.</div>`; return; }
    this.explainBusy = true;
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Fetching the problem…"; }
    out.innerHTML = `<div class="cq-loading" style="height:140px"><div class="cq-spinner"></div><span>Fetching the problem and preparing the explanation…</span></div>`;
    let r: (ExplainProblemResponse & { error?: string }) | null = null;
    try { r = await chrome.runtime.sendMessage({ type: "EXPLAIN_PROBLEM", body: { url, username: username || undefined, selected_text: selected || undefined, code: this.reviewCode || undefined, language: this.reviewLang || undefined } }); } catch { r = null; }
    this.explainBusy = false;
    if (btn) { btn.disabled = false; btn.textContent = "📖 Explain this problem"; }
    if (!r || r.error || !r.explanation) {
      const why = r?.error ? esc(r.error.replace(/^\d+ [^:]*:\s*/, "").slice(0, 220)) : "backend unreachable";
      out.innerHTML = `<div class="cq-error"><strong>Could not explain the problem</strong><br><small>${why}</small></div>`;
      return;
    }
    const e = r.explanation, p = r.problem;
    const list = (a: string[]) => a.length ? `<ul style="margin:4px 0 0 16px;padding:0">${a.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
    const sec = (title: string, body: string) => body.trim() ? `<div style="margin-top:8px"><b>${title}</b><div>${body}</div></div>` : "";
    this.explainText = [e.what_is_asked, e.input_meaning, e.output_meaning, ...e.constraints_and_conditions].filter(Boolean).join(". ");
    out.innerHTML = `<div class="expl-card">
      <div class="expl-head"><div class="diag-ico-box">📖</div><span class="diag-head-lbl">${esc(p.title)} · ${esc(p.difficulty)}</span></div>
      <div class="expl-body">
        <div style="font-size:.7rem;color:#6b7280">${p.tags.map(esc).join(" · ")}</div>
        ${selected ? `<div style="margin-top:6px;font-size:.72rem;background:#fffbeb;border-radius:6px;padding:6px">You highlighted: “${esc(selected.slice(0, 200))}”</div>` : ""}
        ${sec("What it asks", esc(e.what_is_asked))}
        ${sec("Input", esc(e.input_meaning))}
        ${sec("Output", esc(e.output_meaning))}
        ${sec("Constraints", list(e.constraints_and_conditions))}
        ${sec("Examples", list(e.examples_walkthrough))}
        ${sec("Your code", e.code_relation ? esc(e.code_relation) + (e.code_solves_problem !== "unclear" ? ` <i>(solves it: ${e.code_solves_problem})</i>` : "") : "")}
        ${sec("Mismatches", list(e.mismatches))}
        <div style="font-size:.66rem;color:#9ca3af;margin-top:10px">${r.source === "fetched" ? "Problem fetched from LeetCode." : "Using the copy captured earlier (LeetCode unreachable)."}
          ${r.personalised ? ` Personalised for ${esc(r.username ?? "you")}.` : ""}${r.llm_used ? "" : " AI model unavailable: showing the problem's own text."}
          ${r.notes.map((n) => " " + esc(n)).join("")}</div>
      </div></div>`;
  }

  /** Toolbar "Explain": open this tab, fill in the page URL and run immediately. */
  openExplain(selected?: string): void {
    const slug = location.pathname.match(/\/problems\/([^/?#]+)/)?.[1] ?? "";
    if (!this.response) {
      const idle: AnalyzeResponse = { attempt_id: 0, verified: "unverified", results: [], diagnosis: null, explanation: null, flags: [], allowed_hint_level: 1 };
      this.showResults(idle, slug, undefined, undefined, "explain");
    } else this.switchTab("explain");
    void this.prefillExplain().then(() => this.runExplain(selected));
  }

  // ── Hidden Tests tab ─────────────────────────────────────────────────────────

  private hiddenTab(): string {
    return `<div class="cq-tab-panel${this.activeTab === "hiddentests" ? " active" : ""}" id="tab-hiddentests">
      <div class="sec-head">
        <span class="sec-title">Generated Test Cases</span>
        <button class="listen-btn" id="cq-speak-hidden">🔊 Listen</button>
      </div>
      <div class="hidden-outer">
        <div class="ht-intro-card">
          <div class="ht-intro-text" id="cq-hidden-info">AI-generated edge cases and boundaries, run against <strong>your code</strong> in the secure sandbox. These are generated tests, not LeetCode's official hidden tests.</div>
          <button class="ht-gen-btn" id="cq-gen-hidden">⚡ Regenerate</button>
        </div>
        <div id="cq-hidden-results">
          <div class="cq-empty">Open this tab to generate test cases…</div>
        </div>
      </div>
    </div>`;
  }

  /** The cases currently shown (AI-generated if loaded, else the static fallback set). */
  private shownCases(): { input: string; expected: string; status?: string; actual?: string; reason?: string }[] {
    return this.hiddenList
      ? this.hiddenList.map((c) => ({ input: c.input, expected: c.expected_output, status: c.status, actual: c.actual_output, reason: c.reason }))
      : this.hiddenCases(this.slug);
  }

  private buildTestCards(): string {
    return this.shownCases().map((tc, i) => `
      <div class="tc-card">
        <div class="tc-head">
          <span class="tc-head-lbl">Test Case ${i + 1}${tc.status ? ` · <span style="color:${tc.status === "PASS" ? "#16a34a" : tc.status === "FAIL" ? "#dc2626" : "#9ca3af"}">${tc.status === "NOT_RUN" ? "NOT RUN" : tc.status}</span>` : ""}</span>
          <button class="tc-copy-btn" data-copy="${esc(tc.input)}" title="Copy input">⧉</button>
        </div>
        <div class="tc-body">
          <div><span class="tc-in">Input: </span><span class="tc-val">${esc(tc.input)}</span></div>
          <div><span class="tc-out">Expected: </span><span class="tc-val">${esc(tc.expected)}</span></div>
          ${tc.actual ? `<div><span class="tc-out">Your output: </span><span class="tc-val">${esc(tc.actual)}</span></div>` : ""}
          ${tc.reason ? `<div style="font-size:.7rem;color:#9ca3af">${esc(tc.reason)}</div>` : ""}
        </div>
      </div>`).join("");
  }

  private wireCopyButtons(): void {
    this.shadow.querySelectorAll(".tc-copy-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        navigator.clipboard.writeText((btn as HTMLElement).dataset.copy ?? "").catch(() => {});
        (btn as HTMLElement).textContent = "✓";
        setTimeout(() => { (btn as HTMLElement).textContent = "⧉"; }, 1200);
      });
    });
  }

  /** Test Case Generator agent: model-written cases, executed in the backend sandbox. Falls back to the static set. */
  private async loadHidden(): Promise<void> {
    const out = this.shadow.getElementById("cq-hidden-results");
    const info = this.shadow.getElementById("cq-hidden-info");
    const btn = this.shadow.getElementById("cq-gen-hidden") as HTMLButtonElement | null;
    if (!out || this.hiddenBusy) return;
    this.hiddenBusy = true;
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Generating…"; }
    out.innerHTML = `<div class="cq-loading" style="height:120px"><div class="cq-spinner"></div><span>Generating and running test cases…</span></div>`;
    const r = await crew<CrewTestReport>("tests", { problem_slug: this.slug, code: this.reviewCode || undefined, language: this.reviewLang || undefined });
    this.hiddenBusy = false;
    if (btn) { btn.disabled = false; btn.textContent = "⚡ Regenerate"; }
    if (r && r.result.test_cases.length) {
      this.hiddenList = r.result.test_cases;
      const rep = r.result;
      const extra = [...rep.failure_analysis.map((t) => `• ${esc(t)}`), ...rep.required_fixes.map((t) => `→ ${esc(t)}`)].join("<br>");
      this.hiddenInfo = `${esc(rep.disclaimer)}${r.executed ? " Run in the secure sandbox against your code." : " Not executed" + (r.notes[0] ? `: ${esc(r.notes[0])}` : ".")}${r.llm_used ? "" : " (AI model unavailable: using the problem's examples.)"}${extra ? `<div style="margin-top:6px">${extra}</div>` : ""}`;
    } else {
      this.hiddenList = null;
      this.hiddenInfo = "Could not reach the AI test generator (is FEATURE_CREW=1 set on the backend?). Showing a basic edge-case set.";
    }
    if (info) info.innerHTML = this.hiddenInfo;
    out.innerHTML = this.buildTestCards();
    this.wireCopyButtons();
    if (!this.hiddenList) this.hiddenList = null; // static fallback stays re-generatable
  }

  /** Trace Analyst agent: real execution steps from the sandbox + the model's explanation of where it goes wrong. */
  private async loadCrewTrace(): Promise<void> {
    const box = this.shadow.getElementById("cq-crew-trace");
    if (!box || this.traceLoaded || !this.slug) return;
    this.traceLoaded = true;
    box.innerHTML = `<div class="expl-body" style="color:#9ca3af">Recording execution trace…</div>`;
    const r = await crew<CrewTraceReport>("trace", { problem_slug: this.slug, code: this.reviewCode || undefined, language: this.reviewLang || undefined });
    if (!r) { this.traceLoaded = false; box.innerHTML = `<div class="expl-body" style="color:#9ca3af">Execution trace is unavailable (backend FEATURE_CREW off or offline).</div>`; return; }
    const t = r.result;
    const rows = t.steps.slice(0, 60).map((s) => `<tr${t.divergence_step === s.step ? ' style="background:#fef3c7"' : ""}><td>${s.step}</td><td><code>${esc(s.statement)}</code></td><td style="font-size:.7rem">${esc(s.variables)}</td></tr>`).join("");
    box.innerHTML = `<div class="expl-head"><div class="diag-ico-box">🧭</div><span class="diag-head-lbl">Execution Trace · ${t.trace_source === "actual_runtime" ? "real run" : "AI simulation"}</span></div>
      <div class="expl-body">
        <div style="font-size:.72rem;color:#6b7280;margin-bottom:6px">${esc(t.note)}</div>
        ${t.failure_explanation ? `<div style="margin-bottom:8px">${esc(t.failure_explanation)}</div>` : ""}
        ${rows ? `<div style="overflow-x:auto"><table style="border-collapse:collapse;font-size:.74rem;width:100%"><tr><th>#</th><th>Statement</th><th>Variables</th></tr>${rows}</table></div>` : ""}
        ${t.steps.length > 60 ? `<div style="font-size:.7rem;color:#9ca3af">Showing 60 of ${t.steps.length} steps.</div>` : ""}
      </div>`;
  }

  /** Debugger agent: root cause and fix steps in words (the corrected full solution is withheld by the backend). */
  private async runAiDebug(): Promise<void> {
    const box = this.shadow.getElementById("cq-ai-debug");
    if (!box) return;
    box.innerHTML = `<span style="color:#9ca3af">Analysing your code…</span>`;
    const r = await crew<CrewDebugReport>("debug", { problem_slug: this.slug, code: this.reviewCode || undefined, language: this.reviewLang || undefined, attempt_id: this.attemptId || undefined });
    if (!r) { box.innerHTML = `<span style="color:#9ca3af">AI analysis is unavailable (backend FEATURE_CREW off or offline).</span>`; return; }
    const d = r.result;
    const li = (arr: string[]) => arr.length ? `<ul style="margin:4px 0 0 16px;padding:0">${arr.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
    box.innerHTML = `<div style="font-weight:700">${esc(d.diagnosis)}</div>
      ${d.bug_types.length ? `<div style="font-size:.7rem;color:#92400e">${d.bug_types.map(esc).join(" · ")}</div>` : ""}
      ${d.root_cause ? `<div style="margin-top:6px"><b>Root cause:</b> ${esc(d.root_cause)}</div>` : ""}
      ${d.expected_vs_actual ? `<div style="margin-top:4px"><b>Expected vs actual:</b> ${esc(d.expected_vs_actual)}</div>` : ""}
      ${d.variable_trace_of_bug ? `<div style="margin-top:4px"><b>Where it goes wrong:</b> ${esc(d.variable_trace_of_bug)}</div>` : ""}
      ${d.changes_and_reasons.length ? `<div style="margin-top:6px"><b>What to change:</b>${li(d.changes_and_reasons)}</div>` : ""}
      ${d.corrected_code ? `<pre style="white-space:pre-wrap;font-size:.72rem;background:#f9fafb;padding:8px;border-radius:8px;margin-top:6px">${esc(d.corrected_code)}</pre>` : ""}
      <div style="font-size:.68rem;color:#9ca3af;margin-top:6px">${r.llm_used ? "" : "AI model unavailable: showing the stored diagnosis. "}${r.executed ? "Checked against the examples in the sandbox." : "Code was not executed."}${r.fix_code_withheld ? " Full solution intentionally not shown." : ""}</div>`;
  }

  private hiddenCases(slug: string): { input: string; expected: string }[] {
    if (slug.includes("two-sum")) return [
      { input: "nums = [], target = 0",                              expected: "[]" },
      { input: "nums = [3], target = 3",                             expected: "based on constraints" },
      { input: "nums = [1,1,1,1], target = 2",                       expected: "based on constraints" },
      { input: "nums = [-1,-2,-3,-4,-5], target = -8",               expected: "[2,4]" },
      { input: "nums = [1000000000,1000000000], target = 2000000000", expected: "[0,1]" },
    ];
    if (slug.includes("binary-search")) return [
      { input: "nums = [-1,0,3,5,9,12], target = 9",  expected: "4"  },
      { input: "nums = [5], target = 5",               expected: "0"  },
      { input: "nums = [5], target = -5",              expected: "-1" },
      { input: "nums = [1,3,5,7,9], target = 6",       expected: "-1" },
    ];
    if (slug.includes("maximum-subarray")) return [
      { input: "nums = [-2,1,-3,4,-1,2,1,-5,4]", expected: "6"  },
      { input: "nums = [-1]",                     expected: "-1" },
      { input: "nums = [-2,-1]",                  expected: "-1" },
      { input: "nums = [5,4,-1,7,8]",             expected: "23" },
    ];
    return [
      { input: "edge: empty input",        expected: "check constraints" },
      { input: "edge: single element",     expected: "check constraints" },
      { input: "edge: all same elements",  expected: "check constraints" },
      { input: "edge: max constraints",    expected: "check constraints" },
    ];
  }

  // ── Chat tab ─────────────────────────────────────────────────────────────────

  private chatTab(): string {
    const slug = this.slug || "this problem";
    return `<div class="cq-tab-panel${this.activeTab === "chat" ? " active" : ""}" id="tab-chat" style="padding:0;height:100%;min-height:420px;">
      <div class="chat-wrap">
        <div class="chat-hero">
          <div class="chat-hero-row">
            <img class="chat-hero-logo-img" src="${LOGO_DATA_URL}" alt="CodeQuest" />
            <span class="chat-hero-name">CodeQuest</span>
          </div>
          <div class="chat-hero-title">Your AI Coding Co-Pilot.</div>
          <div class="chat-hero-sub">Ask about "${slug}" or debug your code.</div>
        </div>
        <div class="chat-actions">
          <button class="cab" id="cq-cab-explain"><span class="cab-icon">📖</span><span class="cab-label">Explain Problem</span></button>
          <button class="cab" id="cq-cab-debug"><span class="cab-icon">⚙️</span><span class="cab-label">Debug Code</span></button>
          <button class="cab" id="cq-cab-tests"><span class="cab-icon">↗</span><span class="cab-label">Generate Tests</span></button>
          <button class="cab" id="cq-cab-profile"><span class="cab-icon">🔒</span><span class="cab-label">Profile access</span></button>
        </div>
        <div class="chat-messages" id="cq-chat-messages">
          <div class="chat-bubble">
            <div class="chat-av">AI</div>
            <div class="chat-text">Hi! I can explain this problem, help you find why your code fails, or give you hints. I will not hand over the full solution.</div>
          </div>
        </div>
        <div class="chat-input-row">
          <input class="chat-input" id="cq-chat-input" type="text" placeholder="Ask CodeQuest… (e.g., 'Explain this constraint')" />
          <button class="chat-send" id="cq-chat-send">➤</button>
        </div>
      </div>
    </div>`;
  }

  // ── Main render ──────────────────────────────────────────────────────────────

  private render(): void {
    if (!this.response) return;
    const res = this.response;
    const warn = this.explanationOnly
      ? `<div class="cq-warn">ℹ️ ${this.explanationOnly.replace(/[<>&]/g, "")}</div>` : "";

    this.panel.innerHTML = `
      ${this.hdr(res.verified as "oracle-verified" | "unverified" | null)}
      ${warn}
      ${this.tabs()}
      <div class="cq-body">
        ${this.debugTab(res)}
        ${this.explainTab()}
        ${this.traceTab(res)}
        ${this.hintsTab(res)}
        ${this.hiddenTab()}
        ${this.chatTab()}
      </div>`;

    this.attachAll(res);
  }

  // ── Attach all listeners ─────────────────────────────────────────────────────

  private attachAll(res: AnalyzeResponse): void {
    // Close
    this.shadow.getElementById("cq-close-btn")?.addEventListener("click", () => this.close());

    // Tabs
    this.shadow.querySelectorAll(".cq-tab").forEach((btn) => {
      btn.addEventListener("click", () => this.switchTab((btn as HTMLElement).dataset.tab ?? "verdict"));
    });

    // 🔊 Listen buttons
    const diagTxt = res.diagnosis?.mistake_class
      ? `Diagnosis: ${mistakeLabel(res.diagnosis.mistake_class)}, ${Math.round(res.diagnosis.confidence * 100)} percent confidence.` : "";
    this.shadow.getElementById("cq-speak-debug")?.addEventListener("click", () =>
      playText([res.explanation, diagTxt].filter(Boolean).join(" "))
    );
    this.shadow.getElementById("cq-speak-trace")?.addEventListener("click", () => {
      const d = res.divergence ?? res.diagnosis?.divergence;
      if (!d) return;
      playText(`Line ${d.line ?? "?"}, variable ${d.variable ?? "?"} was ${JSON.stringify(d.actual)} expected ${JSON.stringify(d.expected)}.`);
    });
    this.shadow.getElementById("cq-speak-hints")?.addEventListener("click", () => {
      const txts: string[] = [];
      for (let i = 1; i <= (res.allowed_hint_level ?? 1); i++) {
        const el = this.shadow.getElementById(`cq-hint-text-${i}`);
        if (el?.textContent) txts.push(`Hint ${i}: ${el.textContent}`);
      }
      if (txts.length) playText(txts.join(". "));
    });
    this.shadow.getElementById("cq-speak-hidden")?.addEventListener("click", () => {
      const cases = this.shownCases();
      playText(cases.map((c, i) => `Test ${i + 1}: Input ${c.input}. Expected ${c.expected}.`).join(" "));
    });
    this.shadow.getElementById("cq-ex-run")?.addEventListener("click", () => { void this.runExplain(); });
    this.shadow.getElementById("cq-speak-explain")?.addEventListener("click", () => playText(this.explainText));
    this.shadow.getElementById("cq-ai-debug-btn")?.addEventListener("click", () => { void this.runAiDebug(); });

    // Trace nav
    this.shadow.getElementById("cq-trace-prev")?.addEventListener("click", () => {
      if (this.traceIter > 1) { this.traceIter--; this.reRenderTrace(res); }
    });
    this.shadow.getElementById("cq-trace-next")?.addEventListener("click", () => {
      if (this.traceIter < this.traceTotalIter) { this.traceIter++; this.reRenderTrace(res); }
    });

    // Hints fetch
    const { slug, attemptId } = this;
    for (let lv = 1; lv <= (res.allowed_hint_level ?? 1); lv++) {
      const el = this.shadow.getElementById(`cq-hint-text-${lv}`);
      if (el && !attemptId) { el.textContent = "Hints need an analysed attempt: run Debug on Python 3 code."; continue; }
      if (!el || !slug || !attemptId) continue;
      const lvCopy = lv;
      chrome.runtime.sendMessage({ type: "GET_HINT", slug, attemptId, level: lvCopy })
        .then((h: { text?: string; hint_text?: string } | null) => {
          el.textContent = h?.text ?? h?.hint_text ?? "Hint not available yet.";
        })
        .catch(() => { el.textContent = "Could not load hint."; });
    }

    // Generated tests: copy buttons are wired after each (re)render of the list
    this.shadow.getElementById("cq-gen-hidden")?.addEventListener("click", () => { this.hiddenList = null; void this.loadHidden(); });
    if (this.activeTab === "hiddentests") void this.loadHidden();
    if (this.activeTab === "trace") void this.loadCrewTrace();

    // Chat
    this.attachChat(res);

    // Explanation fetch
    this.fetchExplanation(res);
  }

  private reRenderTrace(res: AnalyzeResponse): void {
    const panel = this.shadow.getElementById("tab-trace");
    if (!panel) return;
    const d = res.divergence ?? res.diagnosis?.divergence;
    if (!d) return;
    const iter = this.traceIter; const total = this.traceTotalIter;
    // Update dots
    this.shadow.querySelectorAll(".trace-dot").forEach((dot, i) => {
      dot.classList.toggle("active", i + 1 === iter);
    });
    // Update label
    const lbl = this.shadow.querySelector(".trace-nav-label");
    if (lbl) lbl.textContent = `Iteration ${iter} of ${total}`;
    // Update buttons
    const prev = this.shadow.getElementById("cq-trace-prev") as HTMLButtonElement | null;
    const next = this.shadow.getElementById("cq-trace-next") as HTMLButtonElement | null;
    if (prev) prev.disabled = iter <= 1;
    if (next) next.disabled = iter >= total;
    // Update iteration value in trace
    const iterBox = this.shadow.querySelector(".trace-tl-row:last-child .tl-value-box .tlv-amber");
    if (iterBox) iterBox.textContent = String(iter);
  }

  private attachChat(res: AnalyzeResponse): void {
    const input = this.shadow.getElementById("cq-chat-input") as HTMLInputElement | null;
    const sendBtn = this.shadow.getElementById("cq-chat-send");
    const msgs = this.shadow.getElementById("cq-chat-messages");
    if (!input || !sendBtn || !msgs) return;

    // Assistant bubbles render Markdown (bold, lists, code, tables…) safely; user bubbles stay plain text.
    const addBubble = (text: string, isUser: boolean): HTMLElement => {
      const w = document.createElement("div"); w.className = `chat-bubble${isUser ? " user" : ""}`;
      const av = document.createElement("div"); av.className = "chat-av"; av.textContent = isUser ? "U" : "AI";
      const col = document.createElement("div"); col.className = "chat-col";
      const b = document.createElement("div"); b.className = isUser ? "chat-text" : "chat-text md";
      if (isUser) b.textContent = text; else b.appendChild(renderMarkdown(text));
      col.appendChild(b);
      if (!isUser) {
        const tools = document.createElement("div"); tools.className = "chat-tools";
        const copy = document.createElement("button"); copy.className = "chat-tool"; copy.textContent = "⧉ Copy";
        copy.addEventListener("click", () => {
          navigator.clipboard.writeText(b.dataset.raw ?? b.textContent ?? "").catch(() => {});
          copy.textContent = "✓ Copied"; setTimeout(() => { copy.textContent = "⧉ Copy"; }, 1200);
        });
        const speak = document.createElement("button"); speak.className = "chat-tool"; speak.textContent = "🔊 Listen";
        speak.addEventListener("click", () => playText(stripMarkdown(b.dataset.raw ?? b.textContent ?? "")));
        tools.append(copy, speak); col.appendChild(tools);
      }
      w.appendChild(av); w.appendChild(col); msgs.appendChild(w); msgs.scrollTop = msgs.scrollHeight;
      return b;
    };
    const chips = (target: HTMLElement, items: Array<[string, "good" | "warn" | ""]>) => {
      if (!items.length) return;
      const row = document.createElement("div"); row.className = "chat-chips";
      items.forEach(([t, k]) => { const c = document.createElement("span"); c.className = `chat-chip ${k}`.trim(); c.textContent = t; row.appendChild(c); });
      target.closest(".chat-col")?.appendChild(row);
    };

    const showTyping = () => {
      const w = document.createElement("div"); w.className = "chat-bubble"; w.id = "cq-typing";
      w.innerHTML = `<div class="chat-av">AI</div><div class="chat-text"><div class="tdots"><span></span><span></span><span></span></div></div>`;
      msgs.appendChild(w); msgs.scrollTop = msgs.scrollHeight;
    };
    const hideTyping = () => { this.shadow.getElementById("cq-typing")?.remove(); };

    // ── Backend chat (FEATURE_CHAT) with a local canned fallback when the backend/chat is unavailable ──
    const addNote = (text: string) => {
      const n = document.createElement("div");
      n.style.cssText = "font-size:11px;color:#6b7280;text-align:center;margin:4px 12px;";
      n.textContent = text; msgs.appendChild(n); msgs.scrollTop = msgs.scrollHeight;
    };
    const call = <T>(m: object): Promise<(T & { error?: string }) | null> =>
      (chrome.runtime.sendMessage(m) as Promise<(T & { error?: string }) | null>).catch(() => null);

    /** Stream one reply through the service worker; resolves when the stream ends. Text is revealed progressively. */
    const streamReply = (text: string, code?: string) => new Promise<{ ok: boolean; content: string; meta?: Extract<ChatStreamEvent, { event: "meta" }>["data"]; done?: Extract<ChatStreamEvent, { event: "done" }>["data"]; bubble?: HTMLElement }>((resolve) => {
      let port: chrome.runtime.Port;
      try { port = chrome.runtime.connect({ name: "cq-chat" }); } catch { resolve({ ok: false, content: "" }); return; }
      let content = "", shown = 0, ended = false, failed = false, settled = false;
      let meta: Extract<ChatStreamEvent, { event: "meta" }>["data"] | undefined;
      let done: Extract<ChatStreamEvent, { event: "done" }>["data"] | undefined;
      let bubble: HTMLElement | undefined;
      let timer: ReturnType<typeof setInterval> | undefined;
      const finish = () => {
        if (settled) return; settled = true; if (timer) clearInterval(timer);
        bubble?.classList.remove("cq-caret");
        if (bubble) { bubble.dataset.raw = content; bubble.replaceChildren(renderMarkdown(content)); }
        try { port.disconnect(); } catch { /* already closed */ }
        resolve({ ok: content.length > 0, content, meta, done, bubble });
      };
      const step = () => {
        if (bubble && shown < content.length) {
          shown = Math.min(content.length, shown + Math.max(4, Math.ceil((content.length - shown) / 10)));
          bubble.replaceChildren(renderMarkdown(content.slice(0, shown)));
          msgs.scrollTop = msgs.scrollHeight;
        }
        if (ended && shown >= content.length) finish();
      };
      port.onMessage.addListener((e: ChatStreamEvent) => {
        if (e.event === "meta") meta = e.data;
        else if (e.event === "token") {
          if (!bubble) { hideTyping(); bubble = addBubble("", false); bubble.classList.add("cq-caret"); }
          content += e.data.text;
        } else if (e.event === "done") done = e.data;
        else if (e.event === "error") failed = true;
        else if (e.event === "end") ended = true;
        if (!timer) timer = setInterval(step, 24);
        if (failed && !content) finish();
      });
      port.onDisconnect.addListener(() => { ended = true; if (!content) finish(); });
      port.postMessage({ slug: this.slug, text, code, codeLanguage: code ? this.reviewLang : undefined });
    });

    const send = async (text: string, fromUser = true, code?: string) => {
      if (fromUser) addBubble(text, true);
      showTyping();
      let r = await streamReply(text, code);
      if (!r.ok) {
        // streaming unavailable: try the plain JSON endpoint once, then the local canned reply
        const j = await call<ChatSendResponse>({ type: "CHAT_SEND", slug: this.slug, text, code, codeLanguage: code ? this.reviewLang : undefined });
        hideTyping();
        if (j && !j.error && j.reply) {
          const b = addBubble(j.reply.content, false); b.dataset.raw = j.reply.content;
          r = { ok: true, content: j.reply.content, bubble: b,
                meta: { thread_id: j.thread_id, language: j.reply.language, mode: j.reply.mode, tools_used: j.reply.tools_used, personalized: j.reply.personalized } };
        } else {
          const local = this.chatReply(text);
          const b = addBubble(local, false); b.dataset.raw = local;
          addNote("Offline mode: could not reach the CodeQuest chat service.");
          playText(local);
          return;
        }
      }
      hideTyping();
      const m = r.meta;
      const tags: Array<[string, "good" | "warn" | ""]> = [];
      if (m?.personalized) tags.push(["🔒 Personalised", "good"]);
      if (m?.mode === "refusal") tags.push(["Solution withheld", "warn"]);
      if (m?.mode === "guard_fallback") tags.push(["Filtered for safety", "warn"]);
      if (m?.mode === "fallback") tags.push(["Basic mode (AI model unavailable)", ""]);
      if (r.done?.sources?.length) tags.push([`Sources: ${r.done.sources.slice(0, 3).join(", ")}`, ""]);
      if (r.bubble) chips(r.bubble, tags);
      playText(stripMarkdown(r.content));
    };

    this.chatSend = (t: string) => { void send(t); };
    const submit = () => { const t = input.value.trim(); if (!t) return; input.value = ""; send(t); };
    sendBtn.addEventListener("click", submit);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });

    // ── Profile consent: asked when the chat opens (until the learner decides) ──
    const consentCard = async () => {
      const info = await call<ConsentInfo>({ type: "CHAT_CONSENT_INFO" });
      if (!info || info.error) { addNote("Profile access is not available right now."); return; }
      const w = document.createElement("div"); w.className = "chat-bubble";
      const av = document.createElement("div"); av.className = "chat-av"; av.textContent = "🔒";
      const b = document.createElement("div"); b.className = "chat-text";
      const title = document.createElement("div"); title.style.fontWeight = "700"; title.textContent = info.title;
      const body = document.createElement("div"); body.style.cssText = "margin:4px 0 8px;font-size:12px;"; body.textContent = info.text;
      const user = document.createElement("input"); user.className = "chat-input"; user.placeholder = "Your public LeetCode username";
      user.style.cssText = "width:100%;box-sizing:border-box;margin-bottom:6px;";
      const row = document.createElement("div"); row.style.cssText = "display:flex;gap:6px;flex-wrap:wrap;";
      const allow = document.createElement("button"); allow.className = "cab"; allow.textContent = "Allow & fetch my profile";
      const skip = document.createElement("button"); skip.className = "cab"; skip.textContent = "Not now";
      const state = document.createElement("div"); state.style.cssText = "font-size:11px;margin-top:6px;color:#6b7280;";
      row.append(allow, skip); b.append(title, body, user, row, state); w.append(av, b);
      msgs.appendChild(w); msgs.scrollTop = msgs.scrollHeight;
      skip.addEventListener("click", () => {
        chrome.storage.local.set({ cqConsentAsked: true });
        w.remove(); addNote("OK — chat works without personalisation. Use 🔒 Profile access to change this.");
      });
      allow.addEventListener("click", async () => {
        const name = user.value.trim(); if (!name) { state.textContent = "Enter your LeetCode username first."; return; }
        allow.disabled = skip.disabled = true; state.textContent = "Fetching your public profile… (this can take ~30 s)";
        const st = await call<ConsentStatus>({ type: "CHAT_GRANT", username: name });
        allow.disabled = skip.disabled = false;
        if (!st || st.error) { state.textContent = "Could not save permission: " + (st?.error ?? "backend unreachable"); return; }
        chrome.storage.local.set({ cqConsentAsked: true });
        w.remove();
        if (st.profile_synced) {
          const solved = st.summary?.solved?.All;
          addNote(`🔒 Profile loaded for ${st.leetcode_username}${solved != null ? ` — ${solved} solved` : ""}. Answers are now personalised.`);
        } else addNote("Permission saved, but the profile could not be fetched yet" + (st.sync_error?.message ? ` (${st.sync_error.message})` : "") + ". Chat continues without it.");
      });
    };
    call<ConsentStatus>({ type: "CHAT_STATUS" }).then(async (st) => {
      if (!st || st.error) return; // chat disabled or backend offline: keep local replies
      if (st.granted) { addNote(`🔒 Personalised with ${st.leetcode_username}'s public LeetCode profile.`); return; }
      const asked = (await chrome.storage.local.get("cqConsentAsked")).cqConsentAsked;
      if (!asked) consentCard();
    });
    this.shadow.getElementById("cq-cab-profile")?.addEventListener("click", async () => {
      const st = await call<ConsentStatus>({ type: "CHAT_STATUS" });
      if (!st || st.error) { addNote("Profile access is not available right now."); return; }
      if (st.granted) {
        const r = await call<ConsentStatus>({ type: "CHAT_REVOKE" });
        chrome.storage.local.set({ cqConsentAsked: true });
        addNote(r && !r.error ? "Permission withdrawn — your stored LeetCode profile data was deleted." : "Could not withdraw permission right now.");
      } else consentCard();
    });

    this.shadow.getElementById("cq-cab-explain")?.addEventListener("click", async () => {
      addBubble("Explain this problem to me in simple words.", true); showTyping();
      const r = await crew<CrewExplanation>("explain", { problem_slug: this.slug, code: this.reviewCode || undefined, language: this.reviewLang || undefined });
      hideTyping();
      if (!r || !r.llm_used) { await send("Explain this problem to me in simple words.", false); return; } // chat service answers instead
      const e = r.result;
      const md = [`**What it asks:** ${e.what_is_asked}`, e.input_meaning && `**Input:** ${e.input_meaning}`, e.output_meaning && `**Output:** ${e.output_meaning}`,
        e.constraints_and_conditions.length && `**Constraints:**\n${e.constraints_and_conditions.map((c) => `- ${c}`).join("\n")}`,
        e.examples_walkthrough.length && `**Examples:**\n${e.examples_walkthrough.map((c) => `- ${c}`).join("\n")}`,
        e.code_relation && `**Your code:** ${e.code_relation}${e.code_solves_problem !== "unclear" ? ` (solves the problem: ${e.code_solves_problem})` : ""}`,
        e.mismatches.length && `**Mismatches:**\n${e.mismatches.map((c) => `- ${c}`).join("\n")}`].filter(Boolean).join("\n\n");
      const b = addBubble(md, false); b.dataset.raw = md;
    });

    const reviewNow = () => {
      if (!this.reviewCode.trim()) { addNote("No code found in the editor to review."); return; }
      send(`Review my ${this.reviewLang} code for this problem: what might be wrong, and what should I think about?`, true, this.reviewCode);
    };
    // Nothing could be executed (e.g. Java): review the code with the AI right away, once per Debug click.
    if (this.explanationOnly && this.reviewCode.trim() && !this.reviewSent) { this.reviewSent = true; setTimeout(reviewNow, 400); }

    this.shadow.getElementById("cq-cab-debug")?.addEventListener("click", () => {
      if (this.explanationOnly) { reviewNow(); return; }
      this.activeTab = "verdict";
      this.shadow.querySelectorAll(".cq-tab").forEach((b) => b.classList.remove("active"));
      this.shadow.querySelectorAll(".cq-tab-panel").forEach((p) => p.classList.remove("active"));
      this.shadow.querySelector("[data-tab='verdict']")?.classList.add("active");
      this.shadow.getElementById("tab-verdict")?.classList.add("active");
    });

    this.shadow.getElementById("cq-cab-tests")?.addEventListener("click", async () => {
      addBubble("Generate test cases for this problem", true); showTyping();
      if (!this.hiddenList) await this.loadHidden();
      hideTyping();
      const cases = this.shownCases();
      const reply = `Here are ${cases.length} test cases (open the Hidden tab for details):\n` +
        cases.map((c, i) => `${i + 1}. ${c.input} → ${c.expected}${c.status ? ` (${c.status})` : ""}`).join("\n");
      addBubble(reply, false);
    });
  }

  private chatReply(t: string): string {
    const tl = t.toLowerCase();
    if (tl.includes("hint")) return "Check the Hints tab — I have tiered hints ready!";
    if (tl.includes("trace") || tl.includes("variable")) return "Visit the Trace tab to see where the divergence happened.";
    if (tl.includes("explain") || tl.includes("problem")) {
      const el = this.shadow.getElementById("cq-explanation-text");
      return el?.textContent?.trim()?.replace("Loading explanation…", "") || this.response?.explanation || "Check the Debug tab for the full explanation.";
    }
    if (tl.includes("test") || tl.includes("case")) return "Use 'Generate Tests' above or visit the Hidden tab.";
    return "I'm here to help! Use the action buttons above or ask anything about this problem.";
  }

  private fetchExplanation(res: AnalyzeResponse): void {
    if (res.explanation) return;
    const { attemptId } = this; if (!attemptId) return;
    chrome.runtime.sendMessage({ type: "GET_EXPLANATION", attemptId, lang: "en" })
      .then((r: { text?: string } | null) => {
        const el = this.shadow.getElementById("cq-explanation-text");
        if (el && r?.text) el.textContent = r.text;
        else if (el) el.textContent = "No explanation available.";
      })
      .catch(() => {
        const el = this.shadow.getElementById("cq-explanation-text");
        if (el) el.textContent = res.explanation ?? "Explanation not available.";
      });
  }
}

// ── Singleton ─────────────────────────────────────────────────────────────────
let _card: ResultCard | null = null;
export function getResultCard(): ResultCard {
  if (!_card) _card = new ResultCard();
  return _card;
}
