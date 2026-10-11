// ─── Result Card — Shadow DOM panel ──────────────────────────────────────────
// Fully matches the CodeQuest reference screenshots.

import type { AnalyzeResponse, TestResult, Diagnosis, Verified } from "../api/types";
import { LOGO_DATA_URL } from "../assets/logo";

// ── Styles ────────────────────────────────────────────────────────────────────

const CARD_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:host { all: initial; font-family: 'Inter', system-ui, sans-serif; }
* { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Panel shell ─────────────────────────────────────────────────────────── */
#cq-panel {
  position: fixed;
  top: 0; right: -462px;
  width: 462px; height: 100vh;
  background: #f5efe0;
  border-left: 1px solid #ddd4c0;
  display: flex; flex-direction: column;
  z-index: 2147483646;
  transition: right 0.35s cubic-bezier(0.4,0,0.2,1),
              bottom 0.35s cubic-bezier(0.4,0,0.2,1),
              width 0.35s cubic-bezier(0.4,0,0.2,1),
              height 0.35s cubic-bezier(0.4,0,0.2,1),
              border-radius 0.35s cubic-bezier(0.4,0,0.2,1),
              box-shadow 0.35s;
  box-shadow: -6px 0 28px rgba(0,0,0,0.13);
  color: #111827; overflow: hidden;
  font-family: 'Inter', system-ui, sans-serif;
}
#cq-panel.open { right: 0; }

/* ── Minimized FAB bubble ───────────────────────────────────────── */
#cq-panel.minimized {
  right: 20px !important;
  top: auto !important;
  bottom: 20px;
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: #1a1f2e;
  border: none;
  border-left: none;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4), 0 0 0 4px rgba(217,119,6,0.3);
  cursor: pointer;
}
#cq-panel.minimized .cq-panel-inner {
  opacity: 0; pointer-events: none; transform: scale(0.85);
}
#cq-panel.minimized .cq-min-logo {
  opacity: 1; pointer-events: all; transform: scale(1);
}
/* Wrapper around all panel content */
.cq-panel-inner {
  display: flex; flex-direction: column; height: 100%;
  transition: opacity 0.25s ease, transform 0.2s ease;
  opacity: 1; transform: scale(1);
}
/* Logo shown when minimized */
.cq-min-logo {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transform: scale(0.5);
  transition: opacity 0.25s ease 0.1s, transform 0.25s ease 0.1s;
}
.cq-min-logo img {
  width: 40px; height: 40px; border-radius: 50%;
  object-fit: contain; filter: drop-shadow(0 1px 3px rgba(0,0,0,0.3));
}

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
.cq-minimize {
  background: none; border: none; cursor: pointer;
  color: #6b7280; font-size: 1.1rem; padding: 2px 6px;
  transition: color 0.15s, background 0.15s; font-weight: 400; line-height: 1;
  border-radius: 5px; display: flex; align-items: center; justify-content: center;
}
.cq-minimize:hover { color: #111827; background: #f3f4f6; }

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.cq-tabs {
  display: flex;
  background: #fff;
  border-bottom: 1.5px solid #ede8df;
  flex-shrink: 0; padding: 0 4px;
  overflow-x: auto; scrollbar-width: none;
}
.cq-tabs::-webkit-scrollbar { display: none; }
.cq-tab {
  flex: 1; padding: 12px 2px 10px;
  background: none; border: none;
  border-bottom: 2.5px solid transparent;
  margin-bottom: -1.5px;
  cursor: pointer; font-size: 0.71rem; font-weight: 500;
  color: #9ca3af; font-family: inherit; transition: all 0.15s;
  white-space: nowrap;
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

/* ═══════════════════════════════════════════════════════════════
   EXPLAIN / VISUAL EXPLANATION TAB
═══════════════════════════════════════════════════════════════ */
.explain-outer { padding: 0 16px 20px; display: flex; flex-direction: column; gap: 0; }
.explain-hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 0 14px;
}
.explain-hero-left { display: flex; align-items: center; gap: 14px; }
.explain-hero-icon {
  width: 52px; height: 52px; border-radius: 14px; flex-shrink: 0;
  background: #fef3c7; display: flex; align-items: center; justify-content: center;
  font-size: 1.55rem;
}
.explain-hero-title { font-size: 1.05rem; font-weight: 800; color: #111827; }
.explain-hero-sub   { font-size: 0.78rem; color: #6b7280; margin-top: 3px; font-weight: 400; }
.explain-listen-row {
  display: flex; justify-content: flex-end; margin-bottom: 12px;
}
/* Feature description card (title + subtitle, rounded border) */
.tab-desc-card {
  background: #fff; border: 1.5px solid #e5dece; border-radius: 14px;
  padding: 13px 16px; margin-bottom: 14px;
}
.tab-desc-card-title {
  font-size: 0.88rem; font-weight: 700; color: #111827; margin-bottom: 4px;
}
.tab-desc-card-sub {
  font-size: 0.78rem; color: #6b7280; line-height: 1.6; font-weight: 400;
}
/* Numbered step card */
.vstep-card {
  background: #fff; border: 1px solid #ebe5d9; border-radius: 16px;
  margin-bottom: 14px; overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.vstep-body { display: flex; gap: 0; }
.vstep-left { flex: 1; padding: 16px 14px 16px 16px; }
.vstep-right {
  flex: 0 0 175px; padding: 14px 12px;
  background: #faf8f4;
  border-left: 1px solid #ebe5d9;
  display: flex; flex-direction: column; gap: 7px; justify-content: center; align-items: center;
}
.vstep-num-row { display: flex; align-items: center; gap: 11px; margin-bottom: 8px; }
.vstep-num {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  background: #d97706; color: #fff; font-size: 0.95rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.vstep-title { font-size: 0.92rem; font-weight: 700; color: #d97706; }
.vstep-desc { font-size: 0.83rem; color: #374151; line-height: 1.7; font-weight: 400; }
/* Inline code chip inside desc text */
.ic { display: inline-block; background: #fde68a; color: #92400e; border-radius: 4px;
  padding: 1px 6px; font-family: 'Courier New', monospace; font-size: 0.76rem; font-weight: 600; }
/* Full-width step (no right col) */
.vstep-full { padding: 16px; }
/* Array visualization */
.arr-viz { display: flex; flex-direction: column; gap: 5px; width: 100%; }
.arr-header-row { font-size: 0.67rem; color: #9ca3af; margin-bottom: 2px; }
.arr-cells-row { display: flex; align-items: center; gap: 3px; }
.arr-brk { font-size: 1.1rem; font-weight: 600; color: #6b7280; }
.arr-sep { font-size: 0.72rem; color: #9ca3af; }
.arr-cell {
  width: 30px; height: 30px; border: 1.5px solid #d1d5db; border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.82rem; font-weight: 600; color: #374151; background: #fff;
  flex-shrink: 0;
}
.arr-cell.hl  { background: #dcfce7; border-color: #4ade80; color: #15803d; }
.arr-cell.hl2 { background: #fef3c7; border-color: #f59e0b; color: #b45309; }
.arr-idx-row { display: flex; align-items: center; gap: 3px; padding-left: 18px; }
.arr-idx { width: 30px; text-align: center; font-size: 0.6rem; color: #9ca3af; }
.target-pill {
  background: #fff; border: 1.5px solid #d1d5db; border-radius: 20px;
  padding: 5px 14px; font-size: 0.78rem; font-weight: 700; color: #374151;
  font-family: 'Courier New', monospace; align-self: center; margin-top: 4px;
}
.sum-pill {
  background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px;
  padding: 6px 10px; font-size: 0.8rem; font-weight: 700; color: #92400e;
  text-align: center; font-family: 'Courier New', monospace; width: 100%;
}
.output-pill {
  background: #dcfce7; border: 1px solid #86efac; border-radius: 8px;
  padding: 6px 10px; font-size: 0.8rem; font-weight: 700; color: #16a34a;
  display: flex; align-items: center; gap: 5px; width: 100%; justify-content: center;
}
/* Rules bullet list */
.rules-ul { margin: 8px 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 4px; }
.rules-ul li { display: flex; gap: 7px; font-size: 0.81rem; color: #374151; line-height: 1.5; align-items: flex-start; }
.rules-ul li::before { content: "\u25cf"; color: #d97706; flex-shrink: 0; margin-top: 2px; font-size: 0.6rem; }
/* Key Insight mini card */
.key-insight {
  background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
  padding: 10px 12px; display: flex; gap: 8px; align-items: flex-start; margin-top: 10px;
}
.ki-icon { font-size: 0.9rem; flex-shrink: 0; margin-top: 1px; }
.ki-title { font-size: 0.66rem; font-weight: 800; color: #b45309; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 3px; }
.ki-text  { font-size: 0.8rem; color: #374151; line-height: 1.5; }
/* Final understanding card */
.final-inner {
  display: flex; gap: 10px; align-items: flex-start;
  background: #dcfce7; border: 1px solid #86efac; border-radius: 10px;
  padding: 12px; margin-top: 8px;
}
.final-check { font-size: 1.2rem; flex-shrink: 0; }
.final-text { font-size: 0.82rem; color: #374151; line-height: 1.65; }
/* AI-gen image placeholder */
.viz-img-slot {
  width: 100%; min-height: 70px; border-radius: 8px; border: 1px dashed #e5e7eb;
  background: #f9fafb; display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; color: #9ca3af; text-align: center; padding: 8px;
}
.viz-img-slot img { width: 100%; height: auto; border-radius: 8px; }
/* Shimmer loading */
.vstep-loading {
  height: 60px; border-radius: 8px;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%; animation: vshimmer 1.5s infinite;
}
@keyframes vshimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ═══════════════════════════════════════════════════════════════
   CODE EXPLAIN TAB (step-by-step code walkthrough)
═══════════════════════════════════════════════════════════════ */
.cexp-outer { padding: 0 16px 20px; display: flex; flex-direction: column; gap: 0; }
.cexp-hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 0 10px;
}
.cexp-hero-left { display: flex; align-items: center; gap: 14px; }
.cexp-hero-icon {
  width: 50px; height: 50px; border-radius: 14px; flex-shrink: 0;
  background: #fef3c7; display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem;
}
.cexp-hero-title { font-size: 1.05rem; font-weight: 900; color: #111827; text-transform: uppercase; letter-spacing: 0.04em; }
.cexp-hero-sub   { font-size: 0.78rem; color: #6b7280; margin-top: 2px; }
/* Numbered step card (same vstep-* classes re-used) */
/* Code block */
.cexp-code-wrap {
  background: #1e2233; border-radius: 10px; overflow: hidden;
  margin-top: 10px; border: 1px solid #2d3347;
}
.cexp-code-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; background: #252b3b; border-bottom: 1px solid #2d3347;
}
.cexp-code-lang { font-size: 0.7rem; color: #94a3b8; font-family: 'Courier New', monospace; }
.cexp-copy-btn {
  background: none; border: none; cursor: pointer; color: #94a3b8;
  font-size: 0.7rem; display: flex; align-items: center; gap: 4px;
  padding: 2px 6px; border-radius: 5px; transition: color 0.15s;
}
.cexp-copy-btn:hover { color: #f1f5f9; }
.cexp-code-body {
  padding: 12px 14px; overflow-x: auto;
  font-family: 'Courier New', monospace; font-size: 0.78rem;
  line-height: 1.7; color: #e2e8f0; white-space: pre;
}
/* Syntax colour tokens */
.ck { color: #7dd3fc; font-weight: 600; }   /* keyword: def for if return in */
.cf { color: #a78bfa; }                      /* function name */
.cs { color: #6ee7b7; }                      /* string */
.cn { color: #fde68a; }                      /* number/builtin */
.cc { color: #6b7280; font-style: italic; }  /* comment */
/* Complexity pill */
.cplx-pill {
  display: inline-block; background: #fef3c7; border: 1px solid #fde68a;
  border-radius: 6px; padding: 2px 8px;
  font-family: 'Courier New', monospace; font-size: 0.76rem; font-weight: 700; color: #92400e;
}
.cplx-desc { font-size: 0.82rem; color: #374151; line-height: 1.6; display: inline; margin-left: 6px; }

/* ═══════════════════════════════════════════════════════════════
   APPROACH TAB
═══════════════════════════════════════════════════════════════ */
/* Re-uses .cexp-outer, .vstep-card, .vstep-full, .vstep-num, .vstep-title,
   .vstep-desc, .ic, .rules-ul, .key-insight, .listen-btn from other tabs   */
.apr-hero {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 16px 0 4px;
}
.apr-hero-left { display: flex; align-items: center; gap: 14px; }
.apr-hero-icon {
  width: 50px; height: 50px; border-radius: 14px; flex-shrink: 0;
  background: #fef3c7; display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem;
}
.apr-hero-title { font-size: 1.0rem; font-weight: 800; color: #111827; text-transform: uppercase; letter-spacing: 0.03em; }
.apr-hero-sub   { font-size: 0.76rem; color: #6b7280; margin-top: 2px; }
/* Profile section - inside a vstep-card */
.apr-profile-name { font-size: 0.96rem; font-weight: 700; color: #111827; margin-bottom: 3px; }
.apr-badges { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 5px; }
.apr-badge { font-size: 0.62rem; font-weight: 600; padding: 2px 7px; border-radius: 5px; }
.apr-badge.inter { background: #dbeafe; color: #1d4ed8; }
.apr-badge.lang  { background: #dbeafe; color: #1d4ed8; }
.apr-solved { font-size: 0.78rem; color: #374151; display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.apr-solved strong { font-weight: 700; color: #111827; }
.apr-easy  { color: #16a34a; } .apr-med { color: #d97706; } .apr-hard { color: #dc2626; }
.apr-sync  { font-size: 0.65rem; color: #9ca3af; margin-left: auto; display: flex; align-items: center; gap: 3px; }
.apr-topics-row { display: flex; gap: 14px; margin-top: 4px; flex-wrap: wrap; }
.apr-topics-col { flex: 1; }
.apr-topics-label { font-size: 0.62rem; color: #9ca3af; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px; }
.apr-chip {
  display: inline-flex; font-size: 0.68rem; font-weight: 600;
  padding: 2px 8px; border-radius: 20px; margin: 2px 3px 2px 0;
}
.apr-chip.strong { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
.apr-chip.growth { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
/* Pattern insights - 2 equal cards side by side */
.apr-patterns { display: flex; gap: 10px; margin-top: 4px; }
.apr-pattern-card { flex: 1; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px; }
.apr-pattern-row  { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
.apr-pattern-name { font-size: 0.82rem; font-weight: 700; color: #111827; flex: 1; }
.apr-pat-badge {
  font-size: 0.58rem; font-weight: 700; letter-spacing: 0.04em;
  padding: 2px 6px; border-radius: 5px; text-transform: uppercase;
}
.apr-pat-badge.strong { background: #d1fae5; color: #065f46; }
.apr-pat-badge.growth { background: #fef3c7; color: #92400e; }
.apr-pat-icon { width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; }
.apr-pat-check { color: #16a34a; font-size: 0.9rem; }
.apr-pat-dot   { width: 8px; height: 8px; border-radius: 50%; background: #d97706; }
.apr-pattern-sub { font-size: 0.72rem; color: #6b7280; }
/* Section header row inside a step card */
.apr-sec-head { display: flex; align-items: center; gap: 9px; margin-bottom: 6px; }
.apr-sec-icon {
  width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
  background: #fef3c7; display: flex; align-items: center; justify-content: center; font-size: 0.85rem;
}
.apr-sec-title { font-size: 0.88rem; font-weight: 700; color: #111827; flex: 1; }
.apr-sec-sub   { font-size: 0.72rem; color: #6b7280; }
/* Approach cards */
.approach-card {
  border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 10px 12px; margin-bottom: 7px; background: #fff;
  display: flex; gap: 10px; align-items: flex-start;
}
.approach-card.best { border-color: #d97706; background: #fffbeb; box-shadow: 0 0 0 2px rgba(217,119,6,0.12); }
.approach-num {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.82rem; font-weight: 700; color: #fff; background: #d1d5db; margin-top: 2px;
}
.approach-num.best { background: #d97706; }
.approach-body { flex: 1; }
.approach-name-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 3px; }
.approach-name { font-size: 0.86rem; font-weight: 700; color: #111827; }
.apr-diff-badge { font-size: 0.58rem; font-weight: 700; padding: 2px 6px; border-radius: 5px; text-transform: uppercase; letter-spacing: 0.04em; }
.apr-diff-badge.beg { background: #d1fae5; color: #065f46; }
.apr-diff-badge.int { background: #dbeafe; color: #1d4ed8; }
.apr-diff-badge.adv { background: #ede9fe; color: #6d28d9; }
.apr-best-badge {
  background: #d97706; color: #fff; font-size: 0.58rem; font-weight: 700;
  padding: 2px 7px; border-radius: 5px; display: flex; align-items: center; gap: 3px;
}
.apr-baseline-badge { background: #f3f4f6; color: #6b7280; font-size: 0.58rem; font-weight: 600; padding: 2px 6px; border-radius: 5px; }
.approach-meta { font-size: 0.72rem; color: #6b7280; margin-bottom: 2px; }
.approach-idea { font-size: 0.78rem; color: #374151; }
.approach-why  { font-size: 0.72rem; color: #92400e; margin-top: 3px; }
.approach-steps-btn {
  flex-shrink: 0; font-size: 0.7rem; font-weight: 600;
  padding: 5px 11px; border-radius: 8px; cursor: pointer; align-self: center;
  transition: opacity 0.15s; white-space: nowrap;
}
.approach-steps-btn.normal { background: #fff; border: 1.5px solid #d1d5db; color: #374151; }
.approach-steps-btn.best   { background: #d97706; border: none; color: #fff; box-shadow: 0 2px 5px rgba(217,119,6,0.3); }
.approach-steps-btn:hover  { opacity: 0.8; }
/* Thinking guide */
.think-steps { margin-top: 6px; display: flex; flex-direction: column; gap: 7px; }
.think-step { display: flex; gap: 9px; align-items: flex-start; }
.think-num {
  width: 20px; height: 20px; border-radius: 50%; background: #d97706; flex-shrink: 0;
  color: #fff; font-size: 0.68rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; margin-top: 1px;
}
.think-text { font-size: 0.79rem; color: #374151; line-height: 1.5; }
.think-text strong { color: #111827; font-weight: 700; }
/* Bottom complexity + confidence row */
.apr-bottom { display: flex; gap: 10px; }
.apr-complexity-card, .apr-confidence-card {
  flex: 1; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px;
}
.apr-complexity-label { font-size: 0.62rem; color: #9ca3af; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px; }
.apr-complexity-sub   { font-size: 0.66rem; color: #6b7280; margin-bottom: 8px; }
.apr-cmplx-row { display: flex; gap: 14px; }
.apr-cmplx-col { text-align: center; }
.apr-cmplx-name { font-size: 0.62rem; color: #6b7280; margin-bottom: 2px; }
.apr-cmplx-val { font-size: 1.15rem; font-weight: 800; font-family: 'Courier New', monospace; }
.apr-cmplx-val.time  { color: #16a34a; }
.apr-cmplx-val.space { color: #6d28d9; }
.apr-cmplx-why { font-size: 0.66rem; color: #6b7280; margin-top: 7px; border-top: 1px solid #f3f4f6; padding-top: 6px; }
.apr-cmplx-why strong { color: #374151; font-weight: 600; }
.apr-confidence-card { display: flex; gap: 9px; align-items: flex-start; }
.apr-conf-check {
  width: 24px; height: 24px; border-radius: 50%; background: #16a34a; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 0.85rem;
}
.apr-conf-title { font-size: 0.66rem; font-weight: 700; color: #111827; margin-bottom: 3px; }
.apr-conf-text  { font-size: 0.74rem; color: #374151; line-height: 1.5; }
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
  private submittedCode = "";
  private submittedLang = "python";
  private traceIter = 1;
  private traceTotalIter = 3;
  private panelClickAttached = false; // guard against listener stacking

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

  showResults(res: AnalyzeResponse, slug: string, unsupportedLang?: string, code?: string, lang?: string): void {
    this.response = res; this.attemptId = res.attempt_id;
    this.slug = slug; this.unsupportedLang = unsupportedLang ?? null;
    this.submittedCode = code ?? "";
    this.submittedLang = lang ?? "python";
    this.activeTab = "codeexplain"; this.traceIter = 1;
    // estimate trace steps from iteration field
    if (res.diagnosis?.divergence?.iteration) this.traceTotalIter = Math.max(3, res.diagnosis.divergence.iteration + 1);
    this.panel.classList.add("open"); this.host.style.pointerEvents = "all";
    this.render();
  }

  close(): void    { this.panel.classList.remove("open"); this.host.style.pointerEvents = "none"; stopTTS(); }
  isOpen(): boolean { return this.panel.classList.contains("open"); }
  minimize(): void  { this.panel.classList.add("minimized"); }
  maximize(): void  { this.panel.classList.remove("minimized"); }

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
      <button class="cq-minimize" id="cq-minimize-btn" title="Minimize">&#8211;</button>
      <button class="cq-close" id="cq-close-btn">&#215;</button>
    </div>`;
  }

  private tabs(): string {
    const t = [
      { id: "codeexplain",  lbl: "Explain"   },
      { id: "approach",     lbl: "Approach"   },
      { id: "visualize",    lbl: "Visualize"  },
      { id: "verdict",      lbl: "Debug"      },
      { id: "trace",        lbl: "Trace"      },
      { id: "hints",        lbl: "Hints"      },
      { id: "hiddentests",  lbl: "Hidden"     },
      { id: "chat",         lbl: "Chat"       },
    ];
    return `<div class="cq-tabs">${t.map((x) =>
      `<button class="cq-tab${this.activeTab === x.id ? " active" : ""}" data-tab="${x.id}">${x.lbl}</button>`
    ).join("")}</div>`;
  }

  // ── Code Explain tab (step-by-step code walkthrough) ────────────────────────

  private codeExplainTab(res: AnalyzeResponse): string {
    const slug = this.slug;
    const isTS  = slug.includes("two-sum");
    const isBin = slug.includes("binary-search");
    const lang  = this.submittedLang || "python";
    const langLabel = lang === "python3" ? "Python" : lang === "java" ? "Java" : lang === "cpp" ? "C++" : lang;

    // ── Step content based on problem ──────────────────────────────────────────
    const overview = isTS
      ? `This code solves the <strong>Two Sum</strong> problem. The goal is to find two different indices <span class="ic">i</span> and <span class="ic">j</span> in the array <span class="ic">nums</span> such that <span class="ic">nums[i] + nums[j]</span> equals the <span class="ic">target</span>, and return the indices.`
      : isBin
      ? `This code solves the <strong>Binary Search</strong> problem. We are given a sorted array <span class="ic">nums</span> and a <span class="ic">target</span> value. The goal is to return the index of <span class="ic">target</span> in <span class="ic">O(log n)</span> time, or <span class="ic">-1</span> if not found.`
      : (res.explanation?.substring(0, 220) ?? "This code provides a solution to the problem. Read through the steps below to understand the approach.");

    const howItWorks = isTS
      ? `<ul class="rules-ul">
          <li>We use a <strong>hash map</strong> to store each number and its <span class="ic">index</span> as we iterate through the array.</li>
          <li>For each number <span class="ic">nums[i]</span>, we compute the complement:<br><span class="ic">complement = target - nums[i]</span>.</li>
          <li>If the complement already exists in the map, we have found the answer. We return the current index <span class="ic">i</span> and the index stored in the map.</li>
          <li>Otherwise, we store <span class="ic">nums[i]</span> and its index in the map and continue.</li>
        </ul>`
      : isBin
      ? `<ul class="rules-ul">
          <li>Set two pointers <span class="ic">lo = 0</span> and <span class="ic">hi = len(nums) - 1</span>.</li>
          <li>While <span class="ic">lo <= hi</span>, compute <span class="ic">mid = (lo + hi) // 2</span>.</li>
          <li>If <span class="ic">nums[mid] == target</span>, return <span class="ic">mid</span>.</li>
          <li>If <span class="ic">nums[mid] < target</span>, move <span class="ic">lo = mid + 1</span>; otherwise <span class="ic">hi = mid - 1</span>.</li>
        </ul>`
      : `<ul class="rules-ul">
          <li>Read through each line carefully and map the logic to the problem statement.</li>
          <li>Identify the core data structure(s) being used.</li>
          <li>Trace through with the first example input to verify correctness.</li>
        </ul>`;

    // ── Code block ────────────────────────────────────────────────────────────
    const codeRaw = this.submittedCode
      || (isTS
        ? `def twoSum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i`
        : isBin
        ? `def search(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1`
        : `# Your submitted code will appear here.`);

    const codeHl = this.highlightPython(codeRaw);

    // ── Complexity ────────────────────────────────────────────────────────────
    const timeText = isTS
      ? `<span class="cplx-pill">O(n)</span><span class="cplx-desc">— We iterate through the array once, and each hash map operation (insert and lookup) takes <span class="cplx-pill">O(1)</span> on average.</span>`
      : isBin
      ? `<span class="cplx-pill">O(log n)</span><span class="cplx-desc">— Each iteration halves the search space, giving logarithmic time.</span>`
      : `<span class="cplx-pill">O(?)</span><span class="cplx-desc">— Complexity depends on your approach. Analyze nested loops and recursive depth.</span>`;

    const spaceText = isTS
      ? `<span class="cplx-pill">O(n)</span><span class="cplx-desc">— In the worst case, we store all numbers in the hash map.</span>`
      : isBin
      ? `<span class="cplx-pill">O(1)</span><span class="cplx-desc">— We use only two pointer variables; no extra space proportional to input.</span>`
      : `<span class="cplx-pill">O(?)</span><span class="cplx-desc">— Consider any auxiliary data structures you allocate.</span>`;

    const isActive = this.activeTab === "codeexplain";
    return `<div class="cq-tab-panel${isActive ? " active" : ""}" id="tab-codeexplain">
      <div class="cexp-outer">
        <div class="cexp-hero">
          <div class="cexp-hero-left">
            <div class="cexp-hero-icon">📖</div>
            <div>
              <div class="cexp-hero-title">Explain</div>
              <div class="cexp-hero-sub">Understand the selected code and its logic.</div>
            </div>
          </div>
          <button class="listen-btn" id="cq-speak-codeexplain">🔊 Listen</button>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row"><div class="vstep-num">1</div><div class="vstep-title">Overview</div></div>
            <div class="vstep-desc">${overview}</div>
          </div>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row"><div class="vstep-num">2</div><div class="vstep-title">How it works</div></div>
            <div class="vstep-desc">${howItWorks}</div>
            <div class="cexp-code-wrap">
              <div class="cexp-code-header">
                <span class="cexp-code-lang">${langLabel} (Example)</span>
                <button class="cexp-copy-btn" id="cq-copy-code">&#8944; Copy</button>
              </div>
              <div class="cexp-code-body" id="cq-code-body">${codeHl}</div>
            </div>
          </div>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row"><div class="vstep-num">3</div><div class="vstep-title">Time Complexity</div></div>
            <div class="vstep-desc">${timeText}</div>
          </div>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row"><div class="vstep-num">4</div><div class="vstep-title">Space Complexity</div></div>
            <div class="vstep-desc">${spaceText}</div>
          </div>
        </div>
      </div>
    </div>`;
  }

  /** Very-light Python syntax highlighter for the code block */
  private highlightPython(code: string): string {
    const kws = ["def","for","if","elif","else","return","in","while","class","import","from","and","or","not","None","True","False","lambda","pass","break","continue"];
    // Escape HTML first
    let h = code.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    // Comments
    h = h.replace(/(#[^\n]*)/g, `<span class="cc">$1</span>`);
    // Strings
    h = h.replace(/('[^']*'|"[^"]*")/g, `<span class="cs">$1</span>`);
    // Keywords (whole-word only)
    kws.forEach((kw) => {
      h = h.replace(new RegExp(`\\b(${kw})\\b(?![^<]*>)`, "g"), `<span class="ck">$1</span>`);
    });
    // Numbers
    h = h.replace(/\b(\d+)\b(?![^<]*>)/g, `<span class="cn">$1</span>`);
    // Function names after def
    h = h.replace(/(<span class="ck">def<\/span>\s+)(\w+)/g, `$1<span class="cf">$2</span>`);
    return h;
  }

  // ── Approach tab ──────────────────────────────────────────────────────────────

  private approachTab(res: AnalyzeResponse): string {
    const slug  = this.slug;
    const isTS  = slug.includes("two-sum");
    const isBin = slug.includes("binary-search");

    const approaches = isTS ? [
      { num: 1, name: "Brute Force",         diff: "beg", diffLbl: "Beginner",     baseline: true,  best: false,
        time: "O(n\xB2)", space: "O(1)", idea: "Check every pair of elements and see if they sum to the target.", why: "" },
      { num: 2, name: "Hash Map Lookup",     diff: "int", diffLbl: "Intermediate", baseline: false, best: true,
        time: "O(n)",   space: "O(n)", idea: "Use a hash map to store each number's index. For each element, check if its complement exists.",
        why: "Builds on your Hash Table strength while solving Two Sum optimally." },
      { num: 3, name: "Sort + Two Pointers", diff: "adv", diffLbl: "Advanced",     baseline: false, best: false,
        time: "O(n log n)", space: "O(1)", idea: "Sort the array and use two pointers converging from both ends.", why: "" },
    ] : isBin ? [
      { num: 1, name: "Linear Search",          diff: "beg", diffLbl: "Beginner",     baseline: true,  best: false,
        time: "O(n)",      space: "O(1)", idea: "Iterate through the array and return the index when element equals target.", why: "" },
      { num: 2, name: "Binary Search",           diff: "int", diffLbl: "Intermediate", baseline: false, best: true,
        time: "O(log n)",  space: "O(1)", idea: "Use two pointers lo/hi. Compute mid, compare with target, and narrow search range.",
        why: "Optimal for sorted arrays — halves search space each iteration." },
      { num: 3, name: "Recursive Binary Search", diff: "adv", diffLbl: "Advanced",     baseline: false, best: false,
        time: "O(log n)",  space: "O(log n)", idea: "Same logic as iterative, but implemented recursively with call stack overhead.", why: "" },
    ] : [
      { num: 1, name: "Brute Force",            diff: "beg", diffLbl: "Beginner",     baseline: true,  best: false,
        time: "O(n\xB2)", space: "O(n)", idea: "Try all combinations. Usually too slow but a good starting baseline.", why: "" },
      { num: 2, name: "Optimized (Hashing)",    diff: "int", diffLbl: "Intermediate", baseline: false, best: true,
        time: "O(n)",   space: "O(n)", idea: "Use a hash map or sort the input to reduce redundant comparisons.",
        why: "Usually the expected approach for interview problems at this difficulty." },
      { num: 3, name: "Space-Optimized",        diff: "adv", diffLbl: "Advanced",     baseline: false, best: false,
        time: "O(n)",   space: "O(1)", idea: "Reduce auxiliary space by mutating the input or using bit manipulation.", why: "" },
    ];

    const bestApp = approaches.find((a) => a.best)!;

    const thinkSteps = isTS ? [
      { label: "Identify the goal",       hint: "What two values are we searching for in the array?" },
      { label: "Choose a data structure", hint: "What structure lets us check if a value exists in O(1)?" },
      { label: "Handle the complement",   hint: "For each element, what value do we need to have seen before?" },
    ] : isBin ? [
      { label: "Define the window",    hint: "What should the lo and hi pointers represent?" },
      { label: "Compute the midpoint", hint: "How do you avoid integer overflow when computing mid?" },
      { label: "Narrow the search",    hint: "When should you move lo vs hi?" },
    ] : [
      { label: "Understand the constraints", hint: "What are the input size limits? Does that rule out O(n^2)?" },
      { label: "Pick your structure",        hint: "Would a hash map, stack, or two-pointer approach help?" },
      { label: "Handle edge cases",          hint: "What happens with empty input, duplicates, or boundary values?" },
    ];

    const approachHtml = approaches.map((a) =>
      `<div class="approach-card${a.best ? " best" : ""}">
        <div class="approach-num${a.best ? " best" : ""}">${a.num}</div>
        <div class="approach-body">
          <div class="approach-name-row">
            <span class="approach-name">${a.name}</span>
            <span class="apr-diff-badge ${a.diff}">${a.diffLbl}</span>
            ${a.baseline ? `<span class="apr-baseline-badge">Baseline</span>` : ""}
            ${a.best     ? `<span class="apr-best-badge">&#9733; Best for you</span>` : ""}
          </div>
          <div class="approach-meta">Time: ${a.time} &nbsp;&bull;&nbsp; Space: ${a.space}</div>
          <div class="approach-idea"><strong>Idea:</strong> ${a.idea}</div>
          ${a.why ? `<div class="approach-why"><strong>Why recommended:</strong> ${a.why}</div>` : ""}
        </div>
        <button class="approach-steps-btn ${a.best ? "best" : "normal"}">View steps</button>
      </div>`
    ).join("");

    const thinkHtml = thinkSteps.map((s, i) =>
      `<div class="think-step">
        <div class="think-num">${i + 1}</div>
        <div class="think-text"><strong>${s.label}</strong> &mdash; ${s.hint}</div>
      </div>`
    ).join("");

    const whyItWorks = isTS
      ? "Each number is visited once and looked up in O(1) via the hash map."
      : isBin ? "Search space halves each iteration, at most log2(n) steps needed."
      : "The optimal approach avoids redundant work by leveraging structure in the input.";

    const confBooster = isTS
      ? `You've solved "Contains Duplicate" recently — this uses a similar Hash Map idea, extended to track indices.`
      : isBin ? `You've used two pointers before — Binary Search is the same idea applied to a sorted array.`
      : `This problem pattern appears in many of your recent solves. You already have the building blocks.`;

    const profileName = slug.split("-").map((w: string) => (w[0] ?? "").toUpperCase() + w.slice(1)).join("");
    const isActive = this.activeTab === "approach";
    return `<div class="cq-tab-panel${isActive ? " active" : ""}" id="tab-approach">
      <div class="cexp-outer">
        <div class="apr-hero">
          <div class="apr-hero-left">
            <div class="apr-hero-icon">&#128214;</div>
            <div>
              <div class="apr-hero-title">Personalized Approach</div>
              <div class="apr-hero-sub">Choose the strategy that fits your problem-solving habits.</div>
            </div>
          </div>
          <button class="listen-btn" id="cq-speak-approach">&#128266; Listen</button>
        </div>

        <div class="tab-desc-card">
          <div class="tab-desc-card-title">Personalized Strategy Guide</div>
          <div class="tab-desc-card-sub">Recommends the best algorithmic approach based on your LeetCode profile, difficulty level, and known strengths. Includes a thinking guide and complexity summary.</div>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row">
              <div class="apr-sec-icon">&#128100;</div>
              <div class="apr-sec-title">Your LeetCode Profile</div>
              <span class="apr-sync">&#8635; Last synced: just now</span>
            </div>
            <div class="apr-profile-name">${profileName}</div>
            <div class="apr-badges">
              <span class="apr-badge inter">Intermediate</span>
              <span class="apr-badge lang">Python3</span>
            </div>
            <div class="apr-solved"><strong>142</strong> Solved <span class="apr-easy">Easy: 90</span><span class="apr-med">Medium: 50</span><span class="apr-hard">Hard: 2</span></div>
            <div class="apr-topics-row">
              <div class="apr-topics-col">
                <div class="apr-topics-label">Strong Topics</div>
                <div>
                  <span class="apr-chip strong">Array</span><span class="apr-chip strong">Hash Table</span>
                  <span class="apr-chip strong">String</span><span class="apr-chip strong">Two Pointers</span>
                </div>
              </div>
              <div class="apr-topics-col">
                <div class="apr-topics-label">Growth Areas</div>
                <div>
                  <span class="apr-chip growth">Dynamic Programming</span>
                  <span class="apr-chip growth">Sliding Window</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row">
              <div class="apr-sec-icon">&#128202;</div>
              <div>
                <div class="apr-sec-title">Pattern Insights</div>
                <div class="apr-sec-sub">Analysis based on your solved problems and recent activity.</div>
              </div>
            </div>
            <div class="apr-patterns">
              <div class="apr-pattern-card">
                <div class="apr-pattern-row">
                  <div class="apr-pat-icon"><span class="apr-pat-check">&#10003;</span></div>
                  <span class="apr-pattern-name">${isTS ? "Hash Set lookup" : isBin ? "Binary Search" : "Core Pattern"}</span>
                  <span class="apr-pat-badge strong">Strong</span>
                </div>
                <div class="apr-pattern-sub">You have 41 Hash Table solves.</div>
              </div>
              <div class="apr-pattern-card">
                <div class="apr-pattern-row">
                  <div class="apr-pat-icon"><div class="apr-pat-dot"></div></div>
                  <span class="apr-pattern-name">${isTS ? "Sliding Window" : isBin ? "Two Pointers" : "Growth Pattern"}</span>
                  <span class="apr-pat-badge growth">Growth Area</span>
                </div>
                <div class="apr-pattern-sub">You have 3 solves in this pattern.</div>
              </div>
            </div>
          </div>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row">
              <div class="apr-sec-icon">&#128196;</div>
              <div>
                <div class="apr-sec-title">Available Approaches</div>
                <div class="apr-sec-sub">Main approaches with recommendations for you.</div>
              </div>
            </div>
            ${approachHtml}
          </div>
        </div>

        <div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row">
              <div class="apr-sec-icon">&#128161;</div>
              <div>
                <div class="apr-sec-title">Step-by-Step Thinking Guide</div>
                <div class="apr-sec-sub">Try to answer these before looking at the full solution.</div>
              </div>
            </div>
            <div class="think-steps">${thinkHtml}</div>
          </div>
        </div>

        <div class="apr-bottom">
          <div class="apr-complexity-card">
            <div class="apr-complexity-label">&#9203; Complexity Summary</div>
            <div class="apr-complexity-sub">For the recommended approach (${bestApp.name}).</div>
            <div class="apr-cmplx-row">
              <div class="apr-cmplx-col">
                <div class="apr-cmplx-name">Time Complexity</div>
                <div class="apr-cmplx-val time">${bestApp.time}</div>
              </div>
              <div class="apr-cmplx-col">
                <div class="apr-cmplx-name">Space Complexity</div>
                <div class="apr-cmplx-val space">${bestApp.space}</div>
              </div>
            </div>
            <div class="apr-cmplx-why"><strong>Why it works:</strong> ${whyItWorks}</div>
          </div>
          <div class="apr-confidence-card">
            <div class="apr-conf-check">&#10003;</div>
            <div>
              <div class="apr-conf-title">Confidence Booster</div>
              <div class="apr-conf-text">${confBooster}</div>
            </div>
          </div>
        </div>
      </div>
    </div>`;
  }

  // ── Visualize / Visual Explanation tab ───────────────────────────────────────

  // ── Visualize / Visual Explanation tab ───────────────────────────────────────

  private visualizeTab(res: AnalyzeResponse): string {
    // Parse first example input for array visualization
    const exInput = (res.results ?? []).find((r: TestResult) => r.kind === "example")?.input ?? "";
    const { arr, target, highlight } = this.parseArrayInput(exInput, res);
    const hasArr = arr.length > 0;
    const slug = this.slug;
    const isTS = slug.includes("two-sum");
    const isBin = slug.includes("binary-search");
    const explanation = res.explanation ?? "";

    const arrVizBase = hasArr ? this.renderArr(arr, []) : "";
    const arrVizHL  = hasArr ? this.renderArr(arr, highlight) : "";
    const arrVizOut = hasArr ? this.renderArr(arr, [0, 1]) : "";

    // Steps
    const steps = [
      {
        num: 1, title: "Input and Goal",
        desc: isTS
          ? `We are given an array <span class="ic">nums</span> and a target sum.<br>We need to find two indices <span class="ic">i</span> and <span class="ic">j</span> such that<br><span class="ic">nums[i] + nums[j] = target</span>.`
          : isBin
          ? `We are given a <strong>sorted</strong> array <span class="ic">nums</span> and a <span class="ic">target</span>.<br>We need to return the index of <span class="ic">target</span>, or <span class="ic">-1</span> if not found.`
          : explanation.length > 40
          ? explanation.substring(0, 160) + "…"
          : `Understand the inputs and what the problem is asking you to return.`,
        viz: hasArr ? `${arrVizBase}<div class="target-pill" style="margin-top:6px">target = ${target ?? "?"}</div>` : this.vizPlaceholder(),
      },
      {
        num: 2, title: isTS ? "Find a valid pair" : isBin ? "Narrow the search" : "Core approach",
        desc: isTS
          ? `Look for two numbers whose sum is equal to the <span class="ic">target (${target ?? "?"})</span>. Here, <span class="ic">${arr[highlight[0]] ?? "?"}</span> and <span class="ic">${arr[highlight[1]] ?? "?"}</span> add up to ${target ?? "?"}.`
          : isBin
          ? `Use two pointers <span class="ic">lo</span> and <span class="ic">hi</span>. Check the middle element — if it equals target, return; otherwise narrow the range.`
          : `Think about the most efficient strategy. Avoid nested loops where possible — consider hashing, sorting, or a two-pointer approach.`,
        viz: hasArr
          ? `${arrVizHL}<div class="sum-pill" style="margin-top:6px">${arr[highlight[0]] ?? "?"} + ${arr[highlight[1]] ?? "?"} = ${target ?? "?"}<br>= target</div>`
          : this.vizPlaceholder(),
      },
      {
        num: 3, title: "Return the result",
        desc: isTS
          ? `The indices of <span class="ic">${arr[highlight[0]] ?? "?"}</span> and <span class="ic">${arr[highlight[1]] ?? "?"}</span> are <span class="ic">0</span> and <span class="ic">1</span>.<br>So the answer is <span class="ic">[${highlight.join(", ")}]</span>.`
          : isBin
          ? `When <span class="ic">nums[mid] === target</span>, return <span class="ic">mid</span>. If the loop ends without a match, return <span class="ic">-1</span>.`
          : `Make sure you return the correct type and format as specified in the problem output section.`,
        viz: hasArr
          ? `${arrVizOut}<div class="output-pill" style="margin-top:6px">✓ Output: [${highlight.join(", ")}]</div>`
          : this.vizPlaceholder(),
      },
      {
        num: 4, title: "Key rules to remember",
        desc: isTS
          ? `<ul class="rules-ul">
              <li>Each input will have exactly one solution.</li>
              <li>You may not use the same element twice.</li>
              <li>You can return the indices in any order.</li>
              <li>The array can contain positive, negative, or zero values.</li>
            </ul>
            <div class="key-insight">
              <div class="ki-icon">💡</div>
              <div><div class="ki-title">Key Insight</div>
              <div class="ki-text">We return the <em>indices</em> (positions) of the two numbers, not the numbers themselves.</div></div>
            </div>`
          : `<ul class="rules-ul">
              <li>Read the constraints carefully — they define edge cases.</li>
              <li>Consider empty arrays, single elements, and boundary values.</li>
              <li>Check whether indices or values should be returned.</li>
            </ul>
            <div class="key-insight">
              <div class="ki-icon">💡</div>
              <div><div class="ki-title">Key Insight</div>
              <div class="ki-text">Edge cases are where most solutions fail. Test explicitly for empty input and min/max values.</div></div>
            </div>`,
        viz: null,
      },
      {
        num: 5, title: "Final understanding",
        desc: isTS
          ? `<div class="final-inner"><span class="final-check">✅</span><div class="final-text">In short, you need to find two <strong>different indices</strong> <span class="ic">i</span> and <span class="ic">j</span> such that<br><span class="ic">nums[i] + nums[j] = target</span> and return <span class="ic">[i, j]</span>.</div></div>`
          : `<div class="final-inner"><span class="final-check">✅</span><div class="final-text">${explanation.length > 40 ? explanation : "Make sure your solution handles all edge cases and returns the correct output format as specified."}</div></div>`,
        viz: null,
      },
    ];

    const stepsHtml = steps.map((step) => {
      if (step.viz === null) {
        return `<div class="vstep-card">
          <div class="vstep-full">
            <div class="vstep-num-row">
              <div class="vstep-num">${step.num}</div>
              <div class="vstep-title">${step.title}</div>
            </div>
            <div class="vstep-desc">${step.desc}</div>
          </div>
        </div>`;
      }
      return `<div class="vstep-card">
        <div class="vstep-body">
          <div class="vstep-left">
            <div class="vstep-num-row">
              <div class="vstep-num">${step.num}</div>
              <div class="vstep-title">${step.title}</div>
            </div>
            <div class="vstep-desc">${step.desc}</div>
          </div>
          <div class="vstep-right">${step.viz}</div>
        </div>
      </div>`;
    }).join("");

    const isActive = this.activeTab === "visualize";
    return `<div class="cq-tab-panel${isActive ? " active" : ""}" id="tab-visualize">
      <div class="explain-outer">
        <div class="explain-hero">
          <div class="explain-hero-left">
            <div class="explain-hero-icon">&#128301;</div>
            <div>
              <div class="explain-hero-title">Visual Explanation</div>
              <div class="explain-hero-sub">Let&#39;s understand this problem step by step with visuals.</div>
            </div>
          </div>
          <button class="listen-btn" id="cq-speak-visualize">&#128266; Listen</button>
        </div>

        <div class="tab-desc-card">
          <div class="tab-desc-card-title">Step-by-Step Visual Walkthrough</div>
          <div class="tab-desc-card-sub">Breaks the problem into clear visual steps — input setup, core approach with highlighted array elements, expected output, key rules, and a final summary.</div>
        </div>

        ${stepsHtml}
        <div id="cq-visualize-img-slot" style="display:none">
          <div class="viz-img-slot" id="cq-visualize-ai-img">&#9203; AI visual loading&#8230;</div>
        </div>
      </div>
    </div>`;
  }

  // ── Array parsing + rendering helpers ─────────────────────────────────────────

  private parseArrayInput(input: string, res: AnalyzeResponse): { arr: number[]; target: number | null; highlight: number[] } {
    try {
      // Try to parse "nums = [2,7,11,15], target = 9"
      const arrMatch = input.match(/\[([\d,\s-]+)\]/);
      const tgtMatch = input.match(/target\s*=\s*([\d-]+)/);
      if (arrMatch) {
        const arr = arrMatch[1].split(",").map((x) => parseInt(x.trim(), 10)).filter((n) => !isNaN(n));
        const target = tgtMatch ? parseInt(tgtMatch[1], 10) : null;
        // Find pair that sums to target
        const highlight: number[] = [];
        if (target !== null) {
          outer: for (let i = 0; i < arr.length; i++) {
            for (let j = i + 1; j < arr.length; j++) {
              if (arr[i] + arr[j] === target) { highlight.push(i, j); break outer; }
            }
          }
        }
        if (!highlight.length && arr.length >= 2) highlight.push(0, 1);
        return { arr, target, highlight };
      }
    } catch { /* ignore */ }
    // Fall back to checking expected output
    const exp = (res.results ?? []).find((r: TestResult) => r.kind === "example")?.expected;
    if (typeof exp === "string") {
      const m = exp.match(/\[([\d,\s]+)\]/);
      if (m) {
        const idxs = m[1].split(",").map(Number);
        return { arr: [], target: null, highlight: idxs };
      }
    }
    return { arr: [], target: null, highlight: [0, 1] };
  }

  private renderArr(arr: number[], highlight: number[]): string {
    if (!arr.length) return "";
    const cells = arr.map((v, i) => {
      const cls = highlight.includes(i) ? (highlight.indexOf(i) === 0 ? " hl" : " hl2") : "";
      return `<span class="arr-cell${cls}">${v}</span>`;
    }).join(`<span class="arr-sep">,</span>`);
    const idxs = arr.map((_, i) => `<span class="arr-idx">${i}</span>`).join("");
    return `<div class="arr-viz">
      <div class="arr-header-row">nums =</div>
      <div class="arr-cells-row"><span class="arr-brk">[</span>${cells}<span class="arr-brk">]</span></div>
      <div class="arr-idx-row">${idxs}</div>
    </div>`;
  }

  private vizPlaceholder(): string {
    return `<div class="viz-img-slot">📊<br>Visual<br>Diagram</div>`;
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
      <div class="cq-min-logo"><img src="${LOGO_DATA_URL}" alt="CQ" /></div>
      <div class="cq-panel-inner">
        ${this.hdr(res.verified as "oracle-verified" | "unverified" | null)}
        ${warn}
        ${this.tabs()}
        <div class="cq-body">
          ${this.codeExplainTab(res)}
          ${this.visualizeTab(res)}
          ${this.approachTab(res)}
          ${this.debugTab(res)}
          ${this.traceTab(res)}
          ${this.hintsTab(res)}
          ${this.hiddenTab()}
          ${this.chatTab()}
        </div>
      </div>`;

    this.attachAll(res);
  }

  // ── Attach all listeners ─────────────────────────────────────────────────────

  private attachAll(res: AnalyzeResponse): void {
    // Close
    this.shadow.getElementById("cq-close-btn")?.addEventListener("click", () => this.close());

    // Minimize – stopPropagation so click doesn't bubble to panel restore handler
    this.shadow.getElementById("cq-minimize-btn")?.addEventListener("click", (e) => {
      e.stopPropagation();
      this.minimize();
    });

    // Clicking the FAB bubble while minimized restores – attach only once
    if (!this.panelClickAttached) {
      this.panelClickAttached = true;
      this.panel.addEventListener("click", () => {
        if (this.panel.classList.contains("minimized")) this.maximize();
      });
    }

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

    // Code Explain tab listen
    this.shadow.getElementById("cq-speak-codeexplain")?.addEventListener("click", () => {
      const panel = this.shadow.getElementById("tab-codeexplain");
      if (panel) playText(panel.innerText.replace(/\n+/g, " ").replace(/Listen/g, "").replace(/Copy/g, ""));
    });

    // Approach tab listen
    this.shadow.getElementById("cq-speak-approach")?.addEventListener("click", () => {
      const panel = this.shadow.getElementById("tab-approach");
      if (panel) playText(panel.innerText.replace(/\n+/g, " ").replace(/Listen|View steps/g, ""));
    });

    // Visualize tab listen
    this.shadow.getElementById("cq-speak-visualize")?.addEventListener("click", () => {
      const panel = this.shadow.getElementById("tab-visualize");
      if (panel) playText(panel.innerText.replace(/\n+/g, " ").replace(/Listen/g, ""));
    });

    // Copy code button
    this.shadow.getElementById("cq-copy-code")?.addEventListener("click", (e) => {
      const btn = e.currentTarget as HTMLButtonElement;
      navigator.clipboard.writeText(this.submittedCode || "").then(() => {
        btn.textContent = "✓ Copied"; setTimeout(() => { btn.textContent = "⧉ Copy"; }, 1800);
      });
    });

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

    const send = (text: string, fromUser = true) => {
      if (fromUser) addBubble(text, true);
      showTyping();
      setTimeout(() => { hideTyping(); const r = this.chatReply(text); addBubble(r, false); playText(r); }, 700);
    };

    const submit = () => { const t = input.value.trim(); if (!t) return; input.value = ""; send(t); };
    sendBtn.addEventListener("click", submit);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });

    this.shadow.getElementById("cq-cab-explain")?.addEventListener("click", () => {
      addBubble("Explain this problem to me", true); showTyping();
      setTimeout(() => {
        hideTyping();
        const exEl = this.shadow.getElementById("cq-explanation-text");
        const text = exEl?.textContent?.trim()?.replace("Loading explanation…", "") || res.explanation
          || "Focus on the constraints and edge cases. Think about what the function needs to return for special inputs.";
        addBubble(text, false); playText(text);
      }, 600);
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
