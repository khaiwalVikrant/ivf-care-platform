"""Gradio chat UI for the IVF Treatment Advisor Agent — Command Center layout."""

from __future__ import annotations

import os

# Apply gradio patch before importing gradio
import ivf_advisor.patch_gradio  # noqa: F401

import gradio as gr  # type: ignore

from ivf_advisor.models import ConversationState
from ivf_advisor.agent import create_agent
from ivf_advisor.orchestrator import ConversationOrchestrator
from ivf_advisor.tools.speech_to_text import transcribe_audio

_orchestrator = ConversationOrchestrator(agent=create_agent())


def _get_orchestrator():
    return _orchestrator


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


def _state_badge(state: ConversationState) -> str:
    labels = {
        ConversationState.ONBOARDING: "🟣 Setting up your profile",
        ConversationState.PROFILE_COLLECTION: "🟣 Collecting profile",
        ConversationState.MAIN_LOOP: "🟢 Active session",
    }
    return labels.get(state, state.value)


WELCOME_MESSAGE = (
    "**Welcome to IVF Care Platform!**\n\n"
    "I'm your compassionate AI companion for the IVF journey. I can help you:\n\n"
    "- 🧬 Interpret your lab results (AMH, FSH, AFC)\n"
    "- 📅 Build a personalised treatment timeline\n"
    "- 💊 Guide you through injections and medications\n"
    "- 💰 Break down IVF costs in your city\n"
    "- 🔬 Answer clinical questions with evidence\n"
    "- ❤️ Provide emotional support when you need it\n\n"
    "Use the quick action chips above, or just tell me what you need.\n\n"
    "_Note: I provide educational information only — always consult your fertility specialist._"
)

# ── Quick action chips ─────────────────────────────────────────────────────
QUICK_CHIPS: list[tuple[str, str]] = [
    ("🧬 Lab results",       "I want to understand my AMH/FSH results"),
    ("📅 Timeline",          "Can you create a treatment timeline starting next Monday?"),
    ("💊 Injections",        "How do I self-administer subcutaneous injections?"),
    ("💰 Mumbai costs",      "What does IVF cost in Mumbai?"),
    ("📊 Success rates",     "What are the success rates for someone my age?"),
    ("🥗 Wellness",          "What should I eat during stimulation?"),
    ("🚩 Check clinic",      "My clinic says they have 80% success rate for women over 40"),
    ("❤️ Support",           "I'm feeling overwhelmed and anxious about IVF"),
    ("🔬 Evidence",          "Give me research references about IVF success rates"),
    ("📅 Book appointment",  "Book a consultation appointment for next week"),
]


# ── CSS ────────────────────────────────────────────────────────────────────
CSS = """
/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }
body, .gradio-container {
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    background: #ffffff !important;
    color: #1A1A2E !important;
    font-size: 14px !important;
}
footer, .footer { display: none !important; }
.gradio-container { max-width: 100% !important; margin: 0 !important; padding: 0 !important; }
.contain { max-width: 100% !important; padding: 0 !important; }
.gap { gap: 0 !important; }

/* ── Three-column layout ── */
.cmd-layout {
    display: flex;
    flex-direction: row;
    width: 100%;
    gap: 0;
}

/* ── Left sidebar ── */
.left-sidebar {
    background: #ffffff !important;
    border-right: 1px solid #e5e7eb !important;
    padding: 16px 14px !important;
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow-y: auto;
    position: sticky;
    top: 0;
    max-height: 100vh;
    min-width: 200px;
}
.sidebar-logo {
    font-size: 1.3rem;
    font-weight: 800;
    color: #7c3aed;
    letter-spacing: -0.3px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 14px;
}
.sidebar-section-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: #7c3aed;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 14px 0 6px 0;
}

@keyframes pulse-glow {
    0%   { box-shadow: 0 0 0 0px rgba(124, 58, 237, 0.4); }
    70%  { box-shadow: 0 0 0 10px rgba(124, 58, 237, 0); }
    100% { box-shadow: 0 0 0 0px rgba(124, 58, 237, 0); }
}
.agent-active-pulse {
    animation: pulse-glow 2s infinite;
    border-color: #db2777 !important;
}

/* ── Quick access buttons ── */
.quick-btn {
    margin-bottom: 5px !important;
    display: block !important;
    width: 100% !important;
}
.quick-btn button {
    width: 100% !important;
    text-align: left !important;
    border-radius: 12px !important;
    font-size: 0.82rem !important;
    padding: 10px 12px 10px 12px !important;
    border: 1.5px solid transparent !important;
    background: #f5f3ff !important;
    color: #4c1d95 !important;
    font-weight: 600 !important;
    transition: all 0.18s ease !important;
    height: auto !important;
    min-height: 40px !important;
    justify-content: flex-start !important;
    display: flex !important;
    align-items: center !important;
    gap: 9px !important;
    box-shadow: 0 1px 4px rgba(124,58,237,0.08), inset 0 1px 0 rgba(255,255,255,0.8) !important;
    position: relative !important;
    overflow: hidden !important;
    letter-spacing: 0.01em !important;
}
/* Shimmer sweep on hover */
.quick-btn button::after {
    content: '' !important;
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.45) 50%, transparent 60%) !important;
    transform: translateX(-100%) !important;
    transition: transform 0.4s ease !important;
}
.quick-btn button:hover::after {
    transform: translateX(100%) !important;
}
.quick-btn button:hover {
    transform: translateX(4px) scale(1.01) !important;
    box-shadow: 0 4px 14px rgba(124,58,237,0.22) !important;
    border-color: rgba(124,58,237,0.3) !important;
}
.quick-btn button:active {
    transform: translateX(2px) scale(0.99) !important;
}

/* Per-button tinted backgrounds + accent borders */
#qbtn-0 button { background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%) !important; color: #5b21b6 !important; border-color: #c4b5fd !important; }
#qbtn-0 button:hover { background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%) !important; border-color: #a78bfa !important; }

#qbtn-1 button { background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important; color: #1e40af !important; border-color: #93c5fd !important; }
#qbtn-1 button:hover { background: linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%) !important; border-color: #60a5fa !important; }

#qbtn-2 button { background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%) !important; color: #14532d !important; border-color: #86efac !important; }
#qbtn-2 button:hover { background: linear-gradient(135deg, #bbf7d0 0%, #86efac 100%) !important; border-color: #4ade80 !important; }

#qbtn-3 button { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important; color: #78350f !important; border-color: #fcd34d !important; }
#qbtn-3 button:hover { background: linear-gradient(135deg, #fde68a 0%, #fcd34d 100%) !important; border-color: #fbbf24 !important; }

#qbtn-4 button { background: linear-gradient(135deg, #fae8ff 0%, #f5d0fe 100%) !important; color: #701a75 !important; border-color: #e879f9 !important; }
#qbtn-4 button:hover { background: linear-gradient(135deg, #f5d0fe 0%, #f0abfc 100%) !important; border-color: #d946ef !important; }

#qbtn-5 button { background: linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%) !important; color: #881337 !important; border-color: #fda4af !important; }
#qbtn-5 button:hover { background: linear-gradient(135deg, #fecdd3 0%, #fda4af 100%) !important; border-color: #fb7185 !important; }

/* ── Language selector ── */
.lang-selector {
    background: #f5f3ff;
    border-radius: 10px;
    padding: 8px 10px !important;
    margin-bottom: 4px !important;
    border: 1px solid #ede9fe;
}
.lang-selector .wrap { gap: 12px !important; }
.lang-selector label { font-size: 0.80rem !important; color: #7c3aed !important; font-weight: 600 !important; }
.lang-selector span { font-size: 0.79rem !important; color: #374151 !important; }

/* ── Agent activity — bottom of sidebar, subtle ── */
.agent-status-wrap {
    background: #f9fafb;
    border-left: 3px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.78rem;
    color: #9ca3af;
    font-weight: 400;
    min-height: 32px;
    margin-top: 4px;
}
.agent-status-wrap p { margin: 0 !important; color: #9ca3af !important; font-size: 0.78rem !important; }
.agent-active-pulse .agent-status-wrap,
.agent-status-wrap.agent-active-pulse {
    background: #f5f3ff;
    border-left-color: #7c3aed;
    color: #7c3aed;
}
.agent-status-wrap.agent-active-pulse p { color: #7c3aed !important; }

/* ── Session badge ── */
.status-badge textarea, .status-badge input {
    border-radius: 999px !important;
    background: #f5f3ff !important;
    border: 1px solid rgba(124,58,237,0.3) !important;
    color: #7c3aed !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 4px 14px !important;
    text-align: center !important;
}

/* ── New Conversation button — top of sidebar ── */
.new-convo-btn {
    margin-bottom: 12px !important;
    width: 100% !important;
}
.new-convo-btn button {
    width: 100% !important;
    border-radius: 10px !important;
    border: 1.5px dashed #c4b5fd !important;
    background: #faf5ff !important;
    color: #7c3aed !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 9px 12px !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.01em !important;
}
.new-convo-btn button:hover {
    background: #7c3aed !important;
    color: #ffffff !important;
    border-color: #7c3aed !important;
    border-style: solid !important;
}

/* ── Save Profile — inline below chat, contextual ── */
.save-profile-inline-btn {
    width: 100% !important;
    margin: 6px 0 4px 0 !important;
}
.save-profile-inline-btn button {
    width: 100% !important;
    border-radius: 10px !important;
    background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
    color: #ffffff !important;
    border: none !important;
    font-size: 0.80rem !important;
    font-weight: 600 !important;
    padding: 9px 16px !important;
    box-shadow: 0 2px 8px rgba(5,150,105,0.25) !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
.save-profile-inline-btn button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

/* ── Download Report — inline below chat ── */
.download-report-btn {
    width: 100% !important;
    margin: 6px 0 4px 0 !important;
}
.download-report-btn button {
    width: 100% !important;
    border-radius: 10px !important;
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
    color: #ffffff !important;
    border: none !important;
    font-size: 0.80rem !important;
    font-weight: 600 !important;
    padding: 9px 16px !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.25) !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
.download-report-btn button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}


/* ── Central chat column ── */
.center-col {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 0 !important;
    overflow: hidden;
}
.chat-header-wrap { padding: 16px 24px 8px 24px; }
.chat-header-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #7c3aed;
    margin: 0 0 2px 0;
}
.chat-header-sub {
    font-size: 0.82rem;
    color: #6b7280;
    margin: 0;
}
.chat-scroll-area {
    flex: 1;
    overflow-y: auto;
    padding: 0 24px;
}
.input-area-container {
    padding: 12px 24px 16px 24px;
    background: #ffffff;
    border-top: 1px solid #e5e7eb;
}

/* ── Right sidebar ── */
.right-sidebar {
    background: #ffffff !important;
    border-left: 1px solid #e5e7eb !important;
    padding: 12px 10px 12px 10px !important;
    display: flex;
    flex-direction: column;
    gap: 8px;
    overflow-y: auto;
    overflow-x: hidden;
    position: sticky;
    top: 0;
    height: 100vh;
    max-height: 100vh;
    min-width: 200px;
    scrollbar-width: thin;
    scrollbar-color: #7c3aed #f5f3ff;
}
.right-sidebar::-webkit-scrollbar {
    width: 12px;
}
.right-sidebar::-webkit-scrollbar-track {
    background: #f5f3ff;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
}
.right-sidebar::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #7c3aed 0%, #db2777 100%);
    border-radius: 6px;
    border: 2px solid #f5f3ff;
    box-shadow: 0 2px 8px rgba(124,58,237,0.3);
}
.right-sidebar::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #6d28d9 0%, #be185d 100%);
    box-shadow: 0 3px 12px rgba(124,58,237,0.5);
}
/* Prevent any child from overflowing horizontally */
.right-sidebar > * {
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

/* ── Chatbot bubbles ── */
.chat-wrap {
    border-radius: 16px !important;
    border: 1px solid #e5e7eb !important;
    background: #ffffff !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.07) !important;
    overflow: hidden !important;
    flex-grow: 1 !important;
    overflow-y: auto !important;
    height: calc(100vh - 320px) !important;
    min-height: 400px !important;
    max-height: calc(100vh - 320px) !important;
}
/* User bubble */
.chat-wrap .message.user > div,
.chat-wrap [data-testid="user"] .bubble-wrap {
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
    color: white !important;
    border-radius: 18px 18px 4px 18px !important;
    box-shadow: 0 2px 10px rgba(124,58,237,0.25) !important;
}
/* Bot bubble */
.chat-wrap .message.bot > div,
.chat-wrap [data-testid="bot"] .bubble-wrap {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-left: 3px solid #7c3aed !important;
    border-radius: 18px 18px 18px 4px !important;
    color: #1A1A2E !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}

/* ── Input area ── */
.input-area {
    background: #ffffff;
    border-radius: 16px;
    border: 1.5px solid #e5e7eb;
    padding: 8px 10px 8px 14px;
    box-shadow: 0 2px 8px rgba(124,58,237,0.06);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.input-area:focus-within {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
}
/* Remove Gradio's own border/bg on the row inside the group */
.input-area > .gap,
.input-area .gr-row {
    gap: 8px !important;
    align-items: flex-end !important;
}
.input-area textarea {
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 4px !important;
    font-size: 0.93rem !important;
    background: transparent !important;
    resize: none !important;
    color: #1A1A2E !important;
    box-shadow: none !important;
}
.input-area textarea:focus {
    border-color: transparent !important;
    background: transparent !important;
    outline: none !important;
    box-shadow: none !important;
}

/* ── Send button ── */
.send-btn {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: unset !important;
}
.send-btn button {
    border-radius: 12px !important;
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    border: none !important;
    padding: 0 !important;
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    min-height: 44px !important;
    box-shadow: 0 2px 10px rgba(124,58,237,0.3) !important;
    transition: opacity 0.15s, transform 0.1s !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}
.send-btn button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important; }

/* ── Disclaimer banner ── */
.disclaimer-banner {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 10px;
    padding: 10px 14px;
}
.disclaimer-banner p {
    color: #92400e !important;
    font-size: 0.76rem !important;
    margin: 0 !important;
    line-height: 1.5 !important;
}

/* ── Compact top disclaimer banner ── */
.disclaimer-top-banner {
    background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
    border-bottom: 1px solid #e9d5ff;
    padding: 8px 20px;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.08);
}
.disclaimer-top-banner p {
    color: #6b21a8 !important;
    font-size: 0.75rem !important;
    margin: 0 !important;
    line-height: 1.4 !important;
    font-weight: 500 !important;
}
.disclaimer-top-banner strong {
    font-weight: 700 !important;
    color: #581c87 !important;
}

/* ── Example chips row ── */
.custom-chips-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin: 6px 0 4px 0;
}
.example-chip button {
    border-radius: 20px !important;
    border: 1px solid #e5e7eb !important;
    background: #ffffff !important;
    color: #6b7280 !important;
    font-size: 0.78rem !important;
    padding: 4px 12px !important;
    height: auto !important;
    white-space: nowrap !important;
    transition: all 0.2s ease !important;
    font-weight: 400 !important;
}
.example-chip button:hover {
    border-color: #7c3aed !important;
    color: #7c3aed !important;
    background: #f5f3ff !important;
}

/* ── Journey progress bar ── */
.journey-panel,
.sources-panel,
.docs-panel {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 8px 10px;
    box-shadow: 0 2px 8px rgba(124,58,237,0.05);
    margin-left: 0 !important;
    margin-right: 0 !important;
}
.journey-panel h4 {
    color: #7c3aed;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #e5e7eb;
}
.journey-steps {
    display: flex;
    flex-direction: column;
    gap: 0;
    position: relative;
}
.journey-steps::before {
    content: '';
    position: absolute;
    left: 9px;
    top: 14px;
    bottom: 14px;
    width: 2px;
    background: linear-gradient(to bottom, #e5e7eb 0%, #e5e7eb 100%);
    z-index: 0;
}
.journey-step {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    padding: 2px 0;
    position: relative;
    z-index: 1;
}
.journey-dot {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    font-weight: 700;
    flex-shrink: 0;
    border: 2px solid #e5e7eb;
    background: #ffffff;
    color: #9ca3af;
    transition: all 0.2s;
}
.journey-dot.done {
    background: linear-gradient(135deg, #7c3aed, #db2777);
    border-color: transparent;
    color: #ffffff;
}
.journey-dot.active {
    background: #ffffff;
    border-color: #7c3aed;
    color: #7c3aed;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.15);
}
.journey-step-info { padding-top: 1px; }
.journey-step-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #374151;
    line-height: 1.2;
}
.journey-step-label.active { color: #7c3aed; }
.journey-step-label.done { color: #6b7280; }
.journey-step-sub {
    font-size: 0.64rem;
    color: #9ca3af;
    margin-top: 0px;
}

/* ── Documents & Support panel ── */
.docs-panel h4 {
    color: #7c3aed;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #e5e7eb;
}
.docs-section-label {
    font-size: 0.64rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 6px 0 3px 0;
}
.doc-item {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 4px 5px;
    border-radius: 5px;
    text-decoration: none;
    color: #374151;
    font-size: 0.70rem;
    font-weight: 500;
    transition: background 0.15s, color 0.15s;
    margin-bottom: 2px;
}
.doc-item:hover {
    background: #f5f3ff;
    color: #7c3aed;
}
.doc-icon {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    flex-shrink: 0;
}
.doc-icon.purple { background: #f5f3ff; }
.doc-icon.blue   { background: #eff6ff; }
.doc-icon.green  { background: #f0fdf4; }
.doc-icon.pink   { background: #fdf2f8; }
.support-pill {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 2px 6px;
    border-radius: 14px;
    font-size: 0.70rem;
    font-weight: 500;
    text-decoration: none;
    margin: 2px 2px 0 0;
    transition: opacity 0.15s;
    border: 1px solid transparent;
}
.support-pill:hover { opacity: 0.8; }
.support-pill.india  { background: #fdf2f8; color: #db2777; border-color: #fbcfe8; }
.support-pill.uk     { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
.support-pill.global { background: #f0fdf4; color: #059669; border-color: #bbf7d0; }

/* ── Sources panel ── */
.sources-panel h4 {
    color: #7c3aed;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #e5e7eb;
}
.source-item {
    background: #f5f3ff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 6px 8px;
    margin-bottom: 4px;
    font-size: 0.72rem;
    color: #374151;
    line-height: 1.3;
}
.sources-list { display: flex; flex-direction: column; gap: 3px; }

/* ── Bento cards ── */
.bento-card-wrap {
    position: relative !important;
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 0 !important;
    margin-bottom: 5px !important;
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s, transform 0.2s !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.05) !important;
    overflow: hidden !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
}
.bento-card-wrap:hover {
    background: #fdf2f8 !important;
    border-color: #db2777 !important;
    box-shadow: 0 4px 16px rgba(219,39,119,0.15) !important;
    transform: translateY(-2px) !important;
}
.bento-card-visual {
    padding: 8px 10px;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.bento-card-icon { font-size: 1.1rem; display: block; }
.bento-card-title { font-weight: 700; color: #7c3aed; font-size: 0.76rem; display: block; }
.bento-card-desc { color: #6b7280; font-size: 0.72rem; line-height: 1.3; display: block; }

/* Transparent full-cover button overlay */
.bento-card-overlay-btn {
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    z-index: 2 !important;
}
.bento-card-overlay-btn button {
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}

/* ── Audio trigger button ── */
.audio-trigger-btn {
    margin-top: 6px !important;
    width: 100% !important;
}
.audio-trigger-btn button {
    width: 100% !important;
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
    background: #ffffff !important;
    color: #7c3aed !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 6px 12px !important;
    transition: all 0.15s !important;
}
.audio-trigger-btn button:hover {
    background: #f5f3ff !important;
    border-color: #7c3aed !important;
}


/* ── Responsive Design ── */

/* Large tablets and small laptops (768px - 1100px) */
@media (max-width: 1100px) {
    .right-sidebar { 
        display: none !important; 
    }
    .center-col {
        padding: 0 12px !important;
    }
    .chat-header-wrap {
        padding: 12px 16px 6px 16px !important;
    }
    .chat-scroll-area {
        padding: 0 16px !important;
    }
    .input-area-container {
        padding: 10px 16px 12px 16px !important;
    }
}

/* Small tablets and large phones (481px - 767px) */
@media (max-width: 767px) {
    .left-sidebar {
        display: none !important;
    }
    .right-sidebar {
        display: none !important;
    }
    .center-col {
        min-height: 100svh !important;
        padding: 0 !important;
    }
    .chat-header-wrap {
        padding: 12px 12px 6px 12px !important;
    }
    .chat-header-title {
        font-size: 1.1rem !important;
    }
    .chat-header-sub {
        font-size: 0.76rem !important;
    }
    .chat-scroll-area {
        padding: 0 12px !important;
    }
    .chat-wrap {
        border-radius: 12px !important;
    }
    .chatbot {
        height: 350px !important;
    }
    .input-area-container {
        padding: 8px 12px 12px 12px !important;
    }
    .input-area {
        padding: 6px 8px 6px 10px !important;
    }
    .input-area textarea {
        font-size: 0.88rem !important;
        padding: 8px 4px !important;
    }
    .send-btn button {
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        min-height: 40px !important;
        font-size: 1rem !important;
    }
    .custom-chips-row {
        gap: 4px !important;
        margin: 4px 0 !important;
    }
    .example-chip button {
        font-size: 0.72rem !important;
        padding: 3px 10px !important;
    }
    .disclaimer-banner {
        padding: 8px 10px !important;
        margin-top: 8px !important;
    }
    .disclaimer-banner p {
        font-size: 0.70rem !important;
    }
    .save-profile-inline-btn button,
    .download-report-btn button {
        font-size: 0.76rem !important;
        padding: 8px 14px !important;
    }
}

/* Mobile phones (320px - 480px) */
@media (max-width: 480px) {
    body, .gradio-container {
        font-size: 13px !important;
    }
    .left-sidebar {
        display: none !important;
    }
    .right-sidebar {
        display: none !important;
    }
    .center-col {
        min-height: 100svh !important;
        padding: 0 !important;
    }
    .chat-header-wrap {
        padding: 10px 10px 5px 10px !important;
    }
    .chat-header-title {
        font-size: 1rem !important;
    }
    .chat-header-sub {
        font-size: 0.72rem !important;
    }
    .chat-scroll-area {
        padding: 0 10px !important;
    }
    .chat-wrap {
        border-radius: 10px !important;
        height: 300px !important;
    }
    .chatbot {
        height: 300px !important;
    }
    .input-area-container {
        padding: 6px 10px 10px 10px !important;
    }
    .input-area {
        padding: 5px 6px 5px 8px !important;
        border-radius: 12px !important;
    }
    .input-area textarea {
        font-size: 0.85rem !important;
        padding: 7px 3px !important;
    }
    .send-btn button {
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
        font-size: 0.95rem !important;
        border-radius: 10px !important;
    }
    .custom-chips-row {
        gap: 3px !important;
        margin: 3px 0 !important;
        flex-wrap: wrap !important;
    }
    .example-chip button {
        font-size: 0.68rem !important;
        padding: 2px 8px !important;
        border-radius: 16px !important;
    }
    .disclaimer-banner {
        padding: 6px 8px !important;
        margin-top: 6px !important;
        border-radius: 8px !important;
    }
    .disclaimer-banner p {
        font-size: 0.66rem !important;
        line-height: 1.4 !important;
    }
    .save-profile-inline-btn,
    .download-report-btn {
        margin: 4px 0 3px 0 !important;
    }
    .save-profile-inline-btn button,
    .download-report-btn button {
        font-size: 0.72rem !important;
        padding: 7px 12px !important;
        border-radius: 8px !important;
    }
    .audio-compact .record-button-container button {
        font-size: 0.72rem !important;
        padding: 4px 10px !important;
        min-height: 28px !important;
    }
    /* Chat bubbles */
    .chat-wrap .message.user > div,
    .chat-wrap [data-testid="user"] .bubble-wrap {
        border-radius: 14px 14px 3px 14px !important;
        font-size: 0.88rem !important;
    }
    .chat-wrap .message.bot > div,
    .chat-wrap [data-testid="bot"] .bubble-wrap {
        border-radius: 14px 14px 14px 3px !important;
        font-size: 0.88rem !important;
    }
}

/* 14-inch laptop screens (1366x768 common resolution) */
@media (min-width: 1101px) and (max-width: 1440px) {
    .left-sidebar {
        min-width: 180px !important;
        padding: 14px 12px !important;
    }
    .right-sidebar {
        min-width: 180px !important;
        padding: 14px 12px !important;
    }
    .sidebar-logo {
        font-size: 1rem !important;
    }
    .quick-btn button {
        font-size: 0.78rem !important;
        padding: 9px 10px !important;
    }
    .chat-header-title {
        font-size: 1.15rem !important;
    }
    .chat-header-sub {
        font-size: 0.78rem !important;
    }
    .chatbot {
        height: 380px !important;
    }
    .bento-card-icon {
        font-size: 1.1rem !important;
    }
    .bento-card-title {
        font-size: 0.76rem !important;
    }
    .bento-card-desc {
        font-size: 0.70rem !important;
    }
    .journey-panel h4,
    .sources-panel h4,
    .docs-panel h4 {
        font-size: 0.78rem !important;
    }
}

/* Very small mobile devices (< 360px) */
@media (max-width: 359px) {
    .chat-header-title {
        font-size: 0.95rem !important;
    }
    .chat-header-sub {
        font-size: 0.68rem !important;
    }
    .chat-wrap {
        height: 280px !important;
    }
    .chatbot {
        height: 280px !important;
    }
    .input-area textarea {
        font-size: 0.82rem !important;
    }
    .send-btn button {
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
    }
    .example-chip button {
        font-size: 0.65rem !important;
        padding: 2px 6px !important;
    }
}

/* Screens with limited vertical height (Mac mini, small monitors) */
@media (max-height: 900px) {
    .right-sidebar {
        padding: 8px 8px 8px 8px !important;
        gap: 6px !important;
    }
    .journey-panel {
        padding: 6px 8px !important;
    }
    .journey-panel h4 {
        font-size: 0.74rem !important;
        margin: 0 0 4px 0 !important;
        padding-bottom: 3px !important;
    }
    .journey-step {
        padding: 1px 0 !important;
        gap: 5px !important;
    }
    .journey-dot {
        width: 18px !important;
        height: 18px !important;
        font-size: 0.62rem !important;
    }
    .journey-steps::before {
        left: 8px !important;
        top: 12px !important;
        bottom: 12px !important;
    }
    .journey-step-label {
        font-size: 0.68rem !important;
    }
    .journey-step-sub {
        font-size: 0.60rem !important;
    }
    .sources-panel {
        padding: 6px 8px !important;
    }
    .sources-panel h4 {
        font-size: 0.74rem !important;
        margin: 0 0 4px 0 !important;
        padding-bottom: 3px !important;
    }
    .source-item {
        padding: 5px 7px !important;
        font-size: 0.68rem !important;
        margin-bottom: 3px !important;
    }
    .bento-card-wrap {
        margin-bottom: 4px !important;
    }
    .bento-card-visual {
        padding: 6px 8px !important;
    }
    .bento-card-icon {
        font-size: 1rem !important;
    }
    .bento-card-title {
        font-size: 0.72rem !important;
    }
    .bento-card-desc {
        font-size: 0.64rem !important;
        line-height: 1.2 !important;
    }
    .docs-panel {
        padding: 6px 8px !important;
    }
    .docs-panel h4 {
        font-size: 0.74rem !important;
        margin: 0 0 4px 0 !important;
        padding-bottom: 3px !important;
    }
    .docs-section-label {
        font-size: 0.60rem !important;
        margin: 4px 0 2px 0 !important;
    }
    .doc-item {
        padding: 3px 4px !important;
        font-size: 0.66rem !important;
        gap: 4px !important;
    }
    .doc-icon {
        width: 18px !important;
        height: 18px !important;
        font-size: 0.70rem !important;
    }
    .support-pill {
        padding: 2px 5px !important;
        font-size: 0.62rem !important;
        margin: 1px 1px 0 0 !important;
    }
    .sidebar-section-title {
        font-size: 0.64rem !important;
        margin: 4px 0 3px 0 !important;
    }
}

/* Extra compact for very short screens (768px height or less) */
@media (max-height: 768px) {
    .right-sidebar {
        padding: 6px 6px 6px 6px !important;
        gap: 4px !important;
    }
    .journey-panel,
    .sources-panel,
    .docs-panel {
        padding: 5px 6px !important;
        border-radius: 6px !important;
    }
    .journey-panel h4,
    .sources-panel h4,
    .docs-panel h4 {
        font-size: 0.70rem !important;
        margin: 0 0 3px 0 !important;
        padding-bottom: 2px !important;
    }
    .journey-step {
        padding: 0 !important;
    }
    .journey-dot {
        width: 16px !important;
        height: 16px !important;
        font-size: 0.58rem !important;
    }
    .journey-steps::before {
        left: 7px !important;
        top: 10px !important;
        bottom: 10px !important;
    }
    .journey-step-label {
        font-size: 0.64rem !important;
        line-height: 1.1 !important;
    }
    .journey-step-sub {
        display: none !important;
    }
    .bento-card-wrap {
        margin-bottom: 3px !important;
    }
    .bento-card-visual {
        padding: 5px 6px !important;
        gap: 1px !important;
    }
    .bento-card-icon {
        font-size: 0.95rem !important;
    }
    .bento-card-title {
        font-size: 0.68rem !important;
    }
    .bento-card-desc {
        font-size: 0.60rem !important;
        line-height: 1.15 !important;
    }
    .doc-item {
        padding: 2px 3px !important;
        font-size: 0.62rem !important;
        margin-bottom: 1px !important;
    }
    .doc-icon {
        width: 16px !important;
        height: 16px !important;
        font-size: 0.65rem !important;
    }
    .support-pill {
        padding: 1px 4px !important;
        font-size: 0.58rem !important;
    }
    .source-item {
        padding: 4px 6px !important;
        font-size: 0.64rem !important;
        margin-bottom: 2px !important;
    }
}
"""


# ── Business logic ─────────────────────────────────────────────────────────

def new_session() -> tuple[list[dict], str, str]:
    orch = _get_orchestrator()
    session = orch.create_session()
    return [_msg("assistant", WELCOME_MESSAGE)], session.session_id, "🟢 Active session"


def chat(
    user_message: str,
    history: list[dict],
    session_id: str,
    language: str = "English",
):
    """Streaming chat — yields (history, session_id, state_badge, save_btn_update, download_btn_update, agent_status, sources_html, journey_bar)."""
    if not user_message.strip():
        yield history, session_id, "", gr.update(), gr.update(), gr.update(visible=False), gr.update(), gr.update()
        return

    orch = _get_orchestrator()

    if not session_id or orch.get_session(session_id) is None:
        session = orch.create_session()
        session_id = session.session_id
        history = [_msg("assistant", WELCOME_MESSAGE)]

    message_to_send = user_message
    if language == "Hindi":
        message_to_send = f"Please respond in Hindi (Devanagari script).\n\n{user_message}"

    new_history = list(history) + [
        _msg("user", user_message),
        _msg("assistant", "🤔 Thinking..."),
    ]
    yield new_history, session_id, "🟢 Active session", gr.update(), gr.update(), gr.update(value="⏳ Processing your request...", visible=True), gr.update(), gr.update()

    response = ""
    last_sources_html = _build_sources_html([])  # default empty
    last_journey_html = gr.update()
    try:
        for chunk, session in orch.turn_stream(session_id, message_to_send):
            if chunk.startswith("_thinking:"):
                tool = chunk.replace("_thinking:", "").replace("_", " ").strip()
                tool_labels = {
                    "lab result": ("🧬 Lab Result Agent", "Analysing your test values..."),
                    "evidence search": ("🔬 Evidence Agent", "Searching clinical guidelines..."),
                    "cost breakdown": ("💰 Cost Agent", "Calculating costs for your region..."),
                    "injection guide": ("💊 Medication Agent", "Preparing injection guidance..."),
                    "timeline": ("📅 Timeline Agent", "Building your treatment schedule..."),
                    "success rate": ("📊 Statistics Agent", "Computing personalised success rates..."),
                    "wellness guide": ("🥗 Wellness Agent", "Preparing lifestyle recommendations..."),
                    "emotional support": ("❤️ Support Agent", "Preparing empathetic response..."),
                    "red flag": ("🚩 Safety Agent", "Checking clinic claims..."),
                    "journey guide": ("🗺️ Journey Agent", "Mapping your IVF journey..."),
                    "scope guard": ("🛡️ Safety Check", "Verifying query scope..."),
                }
                agent_name, agent_action = tool_labels.get(tool.lower(), ("🔍 AI Agent", f"{tool.title()}..."))
                status_html = f"**{agent_name}** — {agent_action}"
                new_history[-1] = _msg("assistant", f"_{agent_name} is working..._")
                yield new_history, session_id, "🟢 Active session", gr.update(), gr.update(), gr.update(value=status_html, visible=True, elem_classes=["agent-status-wrap", "agent-active-pulse"]), last_sources_html, last_journey_html
            else:
                response = chunk
                new_history[-1] = _msg("assistant", response)
                citations = _extract_citations(response)
                if citations:
                    last_sources_html = _build_sources_html(citations)
                stage = _detect_journey_stage(response)
                last_journey_html = _build_journey_html(stage)
                state_str = _state_badge(session.state) if session else "🟢 Active session"
                yield new_history, session_id, state_str, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), last_sources_html, last_journey_html
    except Exception as e:
        new_session_obj = orch.create_session()
        session_id = new_session_obj.session_id
        new_history = [_msg("assistant", "Your session expired. Starting a new session.")]
        yield new_history, session_id, "🟢 Active session", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(), gr.update()


def save_profile(history: list[dict], session_id: str):
    """Trigger profile save via chat."""
    yield from chat("I would like to save my profile", history, session_id)


def download_report(history: list[dict], session_id: str):
    """Trigger PDF report generation via chat."""
    yield from chat(
        "Please generate a personalized IVF plan PDF report for me with all the information we've discussed",
        history,
        session_id
    )


def handle_audio(audio_path: str | None, language: str = "English") -> str:
    """Transcribe recorded audio and return text for the input box."""
    if not audio_path:
        return "🎤 No audio recorded — please try again"
    try:
        lang_code = "hi-IN" if language == "Hindi" else "en-IN"
        transcript = transcribe_audio(audio_path, language_code=lang_code)
        if transcript:
            return transcript
        return "🎤 Could not transcribe audio — please type your question"
    except Exception as e:
        return f"🎤 Transcription error: {e}"


def set_example(text: str) -> str:
    """Fill the input box with an example prompt."""
    return text


def _make_quick_handler(prompt: str):
    """Return a streaming handler that fires a quick-action prompt."""
    def _handler(history: list[dict], session_id: str):
        yield from chat(prompt, history, session_id)
    return _handler


def _extract_citations(text: str) -> list[str]:
    """Extract citation lines from evidence search responses."""
    citations = []
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        # Look for lines that look like citations (numbered, bulleted, or contain URLs/guideline names)
        if any(kw in line.lower() for kw in ["eshre", "asrm", "nice", "hfea", "icmr", "sart", "pubmed", "doi", "guideline", "journal"]):
            if len(line) > 10:
                citations.append(line.lstrip("•-*123456789. "))
    return citations[:5]  # max 5 citations


def _build_sources_html(citations: list[str]) -> str:
    if not citations:
        return '<p style="color:#6b7280;font-size:0.82rem;margin:0">No sources cited for this response.</p>'
    items = "".join(
        f'<div class="source-item" style="border-left: 2px solid #7c3aed;">{c}</div>'
        for c in citations
    )
    return f'<div class="sources-list" style="max-height: 300px; overflow-y: auto;">{items}</div>'


# IVF journey stages definition
_JOURNEY_STAGES = [
    ("1", "Initial Consultation", "Assessment & planning"),
    ("2", "Stimulation", "Hormone injections phase"),
    ("3", "Egg Retrieval", "Follicle aspiration"),
    ("4", "Embryo Transfer", "Implantation step"),
    ("5", "Result", "Pregnancy test"),
]


def _build_journey_html(active_stage: int = 1) -> str:
    """Build the journey progress bar HTML. active_stage is 1-indexed."""
    steps_html = ""
    for i, (num, label, sub) in enumerate(_JOURNEY_STAGES, start=1):
        if i < active_stage:
            dot_cls = "done"
            label_cls = "done"
            icon = "✓"
        elif i == active_stage:
            dot_cls = "active"
            label_cls = "active"
            icon = num
        else:
            dot_cls = ""
            label_cls = ""
            icon = num
        steps_html += f"""
        <div class="journey-step">
            <div class="journey-dot {dot_cls}">{icon}</div>
            <div class="journey-step-info">
                <div class="journey-step-label {label_cls}">{label}</div>
                <div class="journey-step-sub">{sub}</div>
            </div>
        </div>"""
    return f'<div class="journey-steps">{steps_html}</div>'


_DOCS_HTML = """
<div class="docs-section-label">📄 Patient Guides</div>
<a class="doc-item" href="https://www.eshre.eu/Guidelines-and-Legal/Guidelines/Ovarian-stimulation-in-IVF" target="_blank">
    <span class="doc-icon purple">📋</span>ESHRE Stimulation Guide
</a>
<a class="doc-item" href="https://www.hfea.gov.uk/treatments/explore-all-treatments/in-vitro-fertilisation-ivf/" target="_blank">
    <span class="doc-icon blue">📘</span>HFEA IVF Patient Guide
</a>
<a class="doc-item" href="https://www.icmr.gov.in/cder/dir/ART%20GUIDELINES-%20FINAL.pdf" target="_blank">
    <span class="doc-icon green">📗</span>ICMR ART Guidelines (India)
</a>
<a class="doc-item" href="https://www.asrm.org/topics/topics-index/in-vitro-fertilization-ivf/" target="_blank">
    <span class="doc-icon pink">📙</span>ASRM IVF Patient Resources
</a>

<div class="docs-section-label" style="margin-top:12px">🤝 Support Groups</div>
<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">
    <a class="support-pill india" href="https://www.ivfbabble.com/india" target="_blank">🇮🇳 IVF Babble India</a>
    <a class="support-pill india" href="https://www.practo.com/ivf" target="_blank">🇮🇳 Practo Forum</a>
    <a class="support-pill uk" href="https://fertilitynetworkuk.org" target="_blank">🇬🇧 Fertility Network UK</a>
    <a class="support-pill global" href="https://resolve.org" target="_blank">🌍 RESOLVE (US)</a>
    <a class="support-pill global" href="https://www.ifmh.org" target="_blank">🌍 IFMH Global</a>
</div>
"""


def _detect_journey_stage(response: str) -> int:
    """Infer IVF journey stage (1-5) from the assistant response text."""
    text = response.lower()
    if any(k in text for k in ["pregnancy test", "beta hcg", "positive test", "implantation success", "congratulations"]):
        return 5
    if any(k in text for k in ["embryo transfer", "transfer day", "blastocyst transfer", "fet", "frozen embryo transfer"]):
        return 4
    if any(k in text for k in ["egg retrieval", "egg collection", "follicle aspiration", "oocyte retrieval", "fertilisation result"]):
        return 3
    if any(k in text for k in ["stimulation", "gonal-f", "menopur", "follicle monitoring", "trigger injection", "self-administer"]):
        return 2
    return 1


# ── UI layout ──────────────────────────────────────────────────────────────

_all_quick: list[tuple[gr.Button, str]] = []  # populated during layout

with gr.Blocks(
    title="IVF Care — Your Compassionate Companion",
    theme=gr.themes.Base(
        primary_hue=gr.themes.colors.purple,
        secondary_hue=gr.themes.colors.pink,
        neutral_hue=gr.themes.colors.gray,
        font=gr.themes.GoogleFont("Inter"),
    ),
    css=CSS,
) as demo:

    session_id_state = gr.State("")

    # ══════════════════════════════════════════════════════════════════════
    # TOP DISCLAIMER BANNER — Professional, always visible
    # ══════════════════════════════════════════════════════════════════════
    gr.HTML("""
    <div class="disclaimer-top-banner">
        <p>
            ⚠️ <strong>Medical Disclaimer:</strong> This platform provides educational information only. 
            It is not a substitute for professional medical advice. Always consult your fertility specialist.
        </p>
    </div>
    """)

    with gr.Row(equal_height=False):

        # ══════════════════════════════════════════════════════════════════
        # COLUMN 1 — Left Navigation Sidebar
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(scale=1, elem_classes=["left-sidebar"]):

            # Logo + New Conversation button side by side
            gr.HTML('<div class="sidebar-logo">🌸 IVF Care</div>')
            new_btn = gr.Button("✦ New Conversation", variant="secondary", size="sm", elem_classes=["new-convo-btn"])

            # Language selector — top priority, affects all responses
            language_selector = gr.Radio(
                choices=["English", "Hindi"],
                value="English",
                label="🌐 Language / भाषा",
                interactive=True,
                elem_classes=["lang-selector"],
            )

            # Quick Access — Start a Conversation
            gr.HTML('<div class="sidebar-section-title" style="padding-left:0;margin-left:0">💬 Start a Conversation</div>')
            gr.HTML('<p style="font-size:0.75rem;color:#9ca3af;margin:0 0 8px 0;padding-left:0">Tap to send a question instantly</p>')

            _quick_sidebar: list[tuple[gr.Button, str]] = []
            _sidebar_quick_defs = [
                ("🧬 Lab Results",   "I want to understand my AMH/FSH results"),
                ("📅 My Timeline",   "Can you create a treatment timeline starting next Monday?"),
                ("💰 Cost Estimate", "What does IVF cost in Mumbai?"),
                ("📊 Success Rates", "What are the success rates for someone my age?"),
                ("💊 Injections",    "How do I self-administer subcutaneous injections?"),
                ("❤️ Support",       "I'm feeling overwhelmed and anxious about IVF"),
            ]
            for _i, (_label, _prompt) in enumerate(_sidebar_quick_defs):
                _btn = gr.Button(_label, variant="secondary", size="sm", elem_classes=["quick-btn"], elem_id=f"qbtn-{_i}")
                _quick_sidebar.append((_btn, _prompt))
                _all_quick.append((_btn, _prompt))

            # Support Communities removed — covered by Documents & Support in right sidebar

            # Evidence & Sources panel — moved from right sidebar to save space
            gr.HTML('<div class="sidebar-section-title" style="margin-top:14px;padding-left:0;margin-left:0">📚 Evidence &amp; Sources</div>')
            gr.HTML('<div class="sources-panel" style="margin-top:6px">')
            sources_box = gr.HTML(
                value='<p style="color:#6b7280;font-size:0.82rem;margin:0">Sources will appear here after evidence search responses.</p>',
            )
            gr.HTML('</div>')

            # Current Activity — bottom, subtle, for context only
            gr.HTML('<div class="sidebar-section-title" style="margin-top:auto;padding-top:16px;padding-left:0;margin-left:0">⚡ Agent Activity</div>')
            agent_status = gr.Markdown(
                value="Ready to help you",
                visible=True,
                elem_classes=["agent-status-wrap"],
            )

            # Hidden session state — needed for wiring but not shown to patient
            state_display = gr.Textbox(
                label="",
                interactive=False,
                value="🟢 Active session",
                elem_classes=["status-badge"],
                show_label=False,
                visible=False,
            )

        # ══════════════════════════════════════════════════════════════════
        # COLUMN 2 — Central Chat
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(scale=3, elem_classes=["center-col"]):

            # Header
            gr.HTML("""
            <div>
                <p class="chat-header-title">Your IVF Care Companion</p>
                <p class="chat-header-sub">Compassionate, evidence-based support — every step of your journey</p>
            </div>
            """)

            # Chatbot
            chatbot = gr.Chatbot(
                label="",
                type="messages",
                value=[],
                avatar_images=(
                    None,
                    "https://em-content.zobj.net/source/google/387/seedling_1f331.png",
                ),
                elem_classes=["chat-wrap"],
                show_label=False,
                bubble_full_width=False,
            )

            # Input area
            with gr.Group(elem_classes=["input-area"]):
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask me anything about IVF, or request an action…",
                        label="",
                        scale=10,
                        show_label=False,
                        lines=1,
                        max_lines=4,
                    )
                    send_btn = gr.Button(
                        "➤",
                        scale=0,
                        variant="primary",
                        elem_classes=["send-btn"],
                    )
            
            # Audio recorder - hidden, only for functionality
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="",
                show_label=False,
                visible=False,
            )
            
            # Audio button - visible trigger
            audio_btn = gr.Button(
                "🎤 Voice Input",
                variant="secondary",
                size="sm",
                elem_classes=["audio-trigger-btn"],
            )

            # Save Profile — appears after first turn, contextual to conversation
            save_profile_btn = gr.Button(
                "💾 Remember me for future visits",
                variant="secondary",
                size="sm",
                visible=False,
                elem_classes=["save-profile-inline-btn"],
            )
            
            # Download Report — appears after first turn
            download_report_btn = gr.Button(
                "📥 Download My IVF Plan (PDF)",
                variant="primary",
                size="sm",
                visible=False,
                elem_classes=["download-report-btn"],
            )

        # ══════════════════════════════════════════════════════════════════
        # COLUMN 3 — Right Bento Sidebar
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(scale=1, elem_classes=["right-sidebar"]):

            # ── Patient Journey Progress Bar ──────────────────────────────
            gr.HTML('<div class="journey-panel"><h4>🗺️ Your IVF Journey</h4>')
            journey_bar = gr.HTML(value=_build_journey_html(1))
            gr.HTML('</div>')

            # Bento feature cards — renamed to "Tools & Capabilities"
            gr.HTML('<div class="sidebar-section-title" style="margin-top:12px;padding-left:0;margin-left:0">🛠️ Tools &amp; Capabilities</div>')

            _bento_defs = [
                ("📈", "Success Predictor",  "Personalised success rates by age & diagnosis",
                 "What are the success rates for someone my age?"),
                ("🥗", "Wellness Guide",     "Stage-specific diet, sleep & exercise tips",
                 "What should I eat during stimulation?"),
                ("🚩", "Clinic Checker",     "Detect misleading clinic claims",
                 "My clinic says they have 80% success rate for women over 40"),
                ("🔬", "Evidence Search",    "ESHRE/ASRM/NICE guidelines",
                 "Give me research references about IVF success rates"),
            ]

            _bento_btns: list[tuple[gr.Button, str]] = []
            for _i, (_icon, _title, _desc, _prompt) in enumerate(_bento_defs):
                with gr.Group(elem_classes=["bento-card-wrap"]):
                    gr.HTML(f"""
                    <div class="bento-card-visual" aria-hidden="true">
                        <span class="bento-card-icon">{_icon}</span>
                        <span class="bento-card-title">{_title}</span>
                        <span class="bento-card-desc">{_desc}</span>
                    </div>
                    """)
                    _bbtn = gr.Button(
                        value="",
                        variant="secondary",
                        elem_classes=["bento-card-overlay-btn"],
                        size="sm",
                    )
                _bento_btns.append((_bbtn, _prompt))
                _all_quick.append((_bbtn, _prompt))

            # ── Documents & Support Group ─────────────────────────────────
            gr.HTML('<div class="docs-panel"><h4>📁 Documents &amp; Support</h4>')
            gr.HTML(_DOCS_HTML)
            gr.HTML('</div>')

    # ── Event wiring ──────────────────────────────────────────────────────
    send_btn.click(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, download_report_btn, agent_status, sources_box, journey_bar],
    ).then(lambda: "", outputs=msg_input)

    msg_input.submit(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, download_report_btn, agent_status, sources_box, journey_bar],
    ).then(lambda: "", outputs=msg_input)

    # Audio button: show audio recorder when clicked
    audio_btn.click(
        fn=lambda: gr.update(visible=True),
        outputs=[audio_input],
    )
    
    # Audio: transcribe when recording stops, fill text box then auto-send
    audio_input.stop_recording(
        fn=handle_audio,
        inputs=[audio_input, language_selector],
        outputs=[msg_input],
    ).then(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, download_report_btn, agent_status, sources_box, journey_bar],
    ).then(lambda: "", outputs=msg_input).then(
        fn=lambda: gr.update(visible=False),
        outputs=[audio_input],
    )

    new_btn.click(fn=new_session, outputs=[chatbot, session_id_state, state_display])

    save_profile_btn.click(
        fn=save_profile,
        inputs=[chatbot, session_id_state],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, download_report_btn, agent_status, sources_box, journey_bar],
    )
    
    download_report_btn.click(
        fn=download_report,
        inputs=[chatbot, session_id_state],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, download_report_btn, agent_status, sources_box, journey_bar],
    )

    for _btn, _prompt in _all_quick:
        _btn.click(
            fn=_make_quick_handler(_prompt),
            inputs=[chatbot, session_id_state],
            outputs=[chatbot, session_id_state, state_display, save_profile_btn, download_report_btn, agent_status, sources_box, journey_bar],
        )

    demo.load(fn=new_session, outputs=[chatbot, session_id_state, state_display])


port = int(os.environ.get("PORT", 7860))
demo.launch(
    server_name="0.0.0.0",
    server_port=port,
    share=False,
    show_error=True,
    show_api=False,
)
