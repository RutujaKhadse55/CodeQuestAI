// ─── Result Card — Shadow DOM panel ──────────────────────────────────────────
// Fully matches the CodeQuest reference screenshots.

import type { AnalyzeResponse, TestResult, Diagnosis, Verified, ChatSendResponse, ConsentInfo, ConsentStatus } from "../api/types";
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
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); white-space: pre-wrap;
}
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
function playText(text: string) {
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
  private traceIter = 1;
  private traceTotalIter = 3; // simulated steps; Phase 3: from real tracer

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

  showResults(res: AnalyzeResponse, slug: string, unsupportedLang?: string): void {
    this.response = res; this.attemptId = res.attempt_id;
    this.slug = slug; this.unsupportedLang = unsupportedLang ?? null;
    this.activeTab = "verdict"; this.traceIter = 1;
    // estimate trace steps from iteration field
    if (res.diagnosis?.divergence?.iteration) this.traceTotalIter = Math.max(3, res.diagnosis.divergence.iteration + 1);
    this.panel.classList.add("open"); this.host.style.pointerEvents = "all";
    this.render();
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
      { id: "verdict", lbl: "Debug" }, { id: "trace", lbl: "Trace" },
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
      <div class="trace-outer">${darkCard}</div>
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

  // ── Hidden Tests tab ─────────────────────────────────────────────────────────

  private hiddenTab(): string {
    return `<div class="cq-tab-panel${this.activeTab === "hiddentests" ? " active" : ""}" id="tab-hiddentests">
      <div class="sec-head">
        <span class="sec-title">Hidden Test Cases</span>
        <button class="listen-btn" id="cq-speak-hidden">🔊 Listen</button>
      </div>
      <div class="hidden-outer">
        <div class="ht-intro-card">
          <div class="ht-intro-text">These test cases go beyond the examples — they test your code against <strong>rigorous edge conditions and constraint boundaries</strong> that a naive solution will fail. Your implementation must handle all of them correctly.</div>
          <button class="ht-gen-btn" id="cq-gen-hidden">⚡ Regenerate</button>
        </div>
        <div id="cq-hidden-results">
          ${this.buildTestCards(this.slug)}
        </div>
      </div>
    </div>`;
  }

  private buildTestCards(slug: string): string {
    const cases = this.hiddenCases(slug);
    return cases.map((tc, i) => `
      <div class="tc-card">
        <div class="tc-head">
          <span class="tc-head-lbl">Test Case ${i + 1}</span>
          <button class="tc-copy-btn" data-copy="${tc.input}" title="Copy input">⧉</button>
        </div>
        <div class="tc-body">
          <div><span class="tc-in">Input: </span><span class="tc-val">${tc.input}</span></div>
          <div><span class="tc-out">Expected: </span><span class="tc-val">${tc.expected}</span></div>
        </div>
      </div>`).join("");
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
            <div class="chat-text">The problem asks for ${slug.includes("two-sum") ? "indices of two numbers that sum to target. Have you considered edge cases?" : "a solution. How can I help you today?"}</div>
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
    const warn = this.unsupportedLang && this.unsupportedLang !== "python3"
      ? `<div class="cq-warn">⚠️ Mock mode — language <strong>${this.unsupportedLang}</strong> is not yet executed.</div>` : "";

    this.panel.innerHTML = `
      ${this.hdr(res.verified as "oracle-verified" | "unverified" | null)}
      ${warn}
      ${this.tabs()}
      <div class="cq-body">
        ${this.debugTab(res)}
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
      btn.addEventListener("click", () => {
        const id = (btn as HTMLElement).dataset.tab ?? "verdict";
        this.activeTab = id;
        this.shadow.querySelectorAll(".cq-tab").forEach((b) => b.classList.remove("active"));
        this.shadow.querySelectorAll(".cq-tab-panel").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        this.shadow.getElementById(`tab-${id}`)?.classList.add("active");
      });
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
      const cases = this.hiddenCases(this.slug);
      playText(cases.map((c, i) => `Test ${i + 1}: Input ${c.input}. Expected ${c.expected}.`).join(" "));
    });

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
      if (!el || !slug || !attemptId) continue;
      const lvCopy = lv;
      chrome.runtime.sendMessage({ type: "GET_HINT", slug, attemptId, level: lvCopy })
        .then((h: { text?: string; hint_text?: string } | null) => {
          el.textContent = h?.text ?? h?.hint_text ?? "Hint not available yet.";
        })
        .catch(() => { el.textContent = "Could not load hint."; });
    }

    // Hidden test copy buttons
    this.shadow.querySelectorAll(".tc-copy-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const text = (btn as HTMLElement).dataset.copy ?? "";
        navigator.clipboard.writeText(text).catch(() => {});
        (btn as HTMLElement).textContent = "✓";
        setTimeout(() => { (btn as HTMLElement).textContent = "⧉"; }, 1200);
      });
    });

    // Hidden regenerate
    const genBtn = this.shadow.getElementById("cq-gen-hidden") as HTMLButtonElement | null;
    const hiddenResults = this.shadow.getElementById("cq-hidden-results");
    genBtn?.addEventListener("click", () => {
      if (!genBtn || !hiddenResults) return;
      genBtn.disabled = true; genBtn.textContent = "⏳ Generating…";
      setTimeout(() => {
        hiddenResults.innerHTML = this.buildTestCards(this.slug);
        // Re-attach copy buttons
        this.shadow.querySelectorAll(".tc-copy-btn").forEach((btn) => {
          btn.addEventListener("click", () => {
            const text = (btn as HTMLElement).dataset.copy ?? "";
            navigator.clipboard.writeText(text).catch(() => {});
            (btn as HTMLElement).textContent = "✓";
            setTimeout(() => { (btn as HTMLElement).textContent = "⧉"; }, 1200);
          });
        });
        genBtn.textContent = "⚡ Regenerate"; genBtn.disabled = false;
      }, 900);
    });

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

    const addBubble = (text: string, isUser: boolean) => {
      const w = document.createElement("div"); w.className = `chat-bubble${isUser ? " user" : ""}`;
      const av = document.createElement("div"); av.className = "chat-av"; av.textContent = isUser ? "U" : "AI";
      const b = document.createElement("div"); b.className = "chat-text"; b.textContent = text;
      w.appendChild(av); w.appendChild(b); msgs.appendChild(w); msgs.scrollTop = msgs.scrollHeight;
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

    const send = async (text: string, fromUser = true) => {
      if (fromUser) addBubble(text, true);
      showTyping();
      const r = await call<ChatSendResponse>({ type: "CHAT_SEND", slug: this.slug, text });
      hideTyping();
      if (!r || r.error || !r.reply) {
        const local = this.chatReply(text);
        addBubble(local, false); playText(local);
        addNote("Offline mode: could not reach the CodeQuest chat service.");
        return;
      }
      addBubble(r.reply.content, false);
      const bits = [r.reply.personalized ? "🔒 personalised" : "", r.reply.mode === "refusal" ? "solution withheld" : "",
        r.reply.mode === "guard_fallback" ? "answer filtered" : ""].filter(Boolean);
      if (bits.length) addNote(bits.join(" · "));
      playText(r.reply.content);
    };

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

    const submit = () => { const t = input.value.trim(); if (!t) return; input.value = ""; send(t); };
    sendBtn.addEventListener("click", submit);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });

    this.shadow.getElementById("cq-cab-explain")?.addEventListener("click", () => {
      send("Explain this problem to me in simple words.");
    });

    this.shadow.getElementById("cq-cab-debug")?.addEventListener("click", () => {
      this.activeTab = "verdict";
      this.shadow.querySelectorAll(".cq-tab").forEach((b) => b.classList.remove("active"));
      this.shadow.querySelectorAll(".cq-tab-panel").forEach((p) => p.classList.remove("active"));
      this.shadow.querySelector("[data-tab='verdict']")?.classList.add("active");
      this.shadow.getElementById("tab-verdict")?.classList.add("active");
    });

    this.shadow.getElementById("cq-cab-tests")?.addEventListener("click", () => {
      addBubble("Generate test cases for this problem", true); showTyping();
      setTimeout(() => {
        hideTyping();
        const cases = this.hiddenCases(this.slug);
        const reply = `Here are ${cases.length} test cases:\n` +
          cases.map((c, i) => `${i + 1}. ${c.input} → ${c.expected}`).join("\n");
        addBubble(reply, false);
        playText(`I generated ${cases.length} test cases. Check the Hidden tab for the full formatted list.`);
      }, 800);
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
