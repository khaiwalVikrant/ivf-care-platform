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
    "🌸 **Welcome to IVF Care Platform!**\n\n"
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
    min-height: 100vh;
    gap: 0;
}

/* ── Left sidebar ── */
.left-sidebar {
    background: #f9fafb !important;
    border-right: 1px solid #e5e7eb !important;
    padding: 16px 14px !important;
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow-y: auto;
}
.sidebar-logo {
    font-size: 1.1rem;
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
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 14px 0 6px 0;
}

/* ── Agent status — prominent banner ── */
.agent-status-wrap {
    background: #f5f3ff;
    border-left: 3px solid #7c3aed;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.82rem;
    color: #7c3aed;
    font-weight: 500;
    min-height: 36px;
    margin-bottom: 4px;
}
.agent-status-wrap p { margin: 0 !important; color: #7c3aed !important; font-size: 0.82rem !important; }

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
    margin-bottom: 6px !important;
    display: block !important;
    width: 100% !important;
}
.quick-btn button {
    width: 100% !important;
    text-align: left !important;
    border-radius: 10px !important;
    font-size: 0.81rem !important;
    padding: 9px 13px 9px 14px !important;
    border: 1px solid #e5e7eb !important;
    background: #ffffff !important;
    color: #374151 !important;
    font-weight: 500 !important;
    transition: all 0.18s ease !important;
    height: auto !important;
    min-height: 38px !important;
    justify-content: flex-start !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    position: relative !important;
    overflow: hidden !important;
}
/* Coloured left accent bar */
.quick-btn button::before {
    content: '' !important;
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    bottom: 0 !important;
    width: 3px !important;
    border-radius: 10px 0 0 10px !important;
    background: linear-gradient(180deg, #7c3aed, #db2777) !important;
    opacity: 0.7 !important;
    transition: opacity 0.18s ease !important;
}
.quick-btn button:hover {
    background: linear-gradient(135deg, #f5f3ff 0%, #fdf2f8 100%) !important;
    border-color: #c4b5fd !important;
    color: #6d28d9 !important;
    box-shadow: 0 3px 12px rgba(124,58,237,0.18) !important;
    transform: translateX(3px) !important;
}
.quick-btn button:hover::before {
    opacity: 1 !important;
    width: 4px !important;
}

/* Per-button accent colours via elem_id */
#qbtn-0 button::before { background: linear-gradient(180deg, #7c3aed, #a78bfa) !important; }
#qbtn-1 button::before { background: linear-gradient(180deg, #0ea5e9, #38bdf8) !important; }
#qbtn-2 button::before { background: linear-gradient(180deg, #059669, #34d399) !important; }
#qbtn-3 button::before { background: linear-gradient(180deg, #f59e0b, #fbbf24) !important; }
#qbtn-4 button::before { background: linear-gradient(180deg, #ec4899, #f472b6) !important; }
#qbtn-5 button::before { background: linear-gradient(180deg, #db2777, #f43f5e) !important; }

/* ── Support communities — flat list, no box ── */
.communities-block {
    font-size: 0.82rem;
    line-height: 2;
    padding: 0;
}
.communities-block a {
    color: #7c3aed;
    text-decoration: none;
    font-weight: 500;
}
.communities-block a:hover { text-decoration: underline; }

/* ── Language selector ── */
.lang-selector .wrap { gap: 6px !important; }
.lang-selector label { font-size: 0.80rem !important; color: #7c3aed !important; font-weight: 500 !important; }

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

/* ── Sidebar action buttons ── */
.sidebar-action-btn button {
    border-radius: 8px !important;
    font-size: 0.80rem !important;
    padding: 7px 12px !important;
    border: 1px solid #7c3aed !important;
    background: #ffffff !important;
    color: #7c3aed !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}
.sidebar-action-btn button:hover {
    background: #7c3aed !important;
    color: #ffffff !important;
}
.save-btn button {
    border-radius: 8px !important;
    background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0.80rem !important;
    width: 100% !important;
    padding: 7px 12px !important;
}

/* ── Central chat column ── */
.center-col {
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 0 !important;
    overflow: hidden;
}
.chat-header-wrap { padding: 16px 24px 8px 24px; }
.chat-header-title {
    font-size: 1.25rem;
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

/* ── Chatbot bubbles ── */
.chat-wrap {
    border-radius: 16px !important;
    border: 1px solid #e5e7eb !important;
    background: #ffffff !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.07) !important;
    overflow: hidden !important;
    flex-grow: 1 !important;
    overflow-y: auto !important;
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
    padding: 12px 14px 10px 14px;
    box-shadow: 0 2px 8px rgba(124,58,237,0.06);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.input-area:focus-within {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
}
.input-area textarea {
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
    padding: 10px 14px !important;
    font-size: 0.93rem !important;
    background: #f9fafb !important;
    resize: none !important;
    color: #1A1A2E !important;
}
.input-area textarea:focus {
    border-color: #7c3aed !important;
    background: #ffffff !important;
    outline: none !important;
}

/* ── Send button ── */
.send-btn button {
    border-radius: 10px !important;
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 10px 20px !important;
    box-shadow: 0 2px 10px rgba(124,58,237,0.3) !important;
    transition: opacity 0.15s, transform 0.1s !important;
    height: 42px !important;
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

/* ── Right sidebar ── */
.right-sidebar {
    background: #ffffff !important;
    border-left: 1px solid #e5e7eb !important;
    padding: 20px 16px !important;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
}

/* ── Sources panel ── */
.sources-panel {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px;
    box-shadow: 0 2px 8px rgba(124,58,237,0.05);
}
.sources-panel h4 {
    color: #7c3aed;
    font-size: 0.85rem;
    font-weight: 700;
    margin: 0 0 10px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #e5e7eb;
}
.source-item {
    background: #f5f3ff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 7px 10px;
    margin-bottom: 5px;
    font-size: 0.76rem;
    color: #374151;
    line-height: 1.4;
}
.sources-list { display: flex; flex-direction: column; gap: 4px; }

/* ── Bento cards ── */
.bento-btn {
    margin-bottom: 8px !important;
    display: block !important;
    width: 100% !important;
}
.bento-btn button {
    width: 100% !important;
    text-align: left !important;
    border-radius: 12px !important;
    border: 1px solid #e5e7eb !important;
    background: #ffffff !important;
    padding: 14px !important;
    height: auto !important;
    min-height: unset !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    cursor: pointer !important;
    white-space: normal !important;
    line-height: 1.4 !important;
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s, transform 0.2s !important;
    box-shadow: none !important;
    /* reset Gradio secondary button styles */
    color: #1A1A2E !important;
    font-weight: 400 !important;
    font-size: 0.82rem !important;
}
.bento-btn button:hover {
    background: #fdf2f8 !important;
    border-color: #db2777 !important;
    box-shadow: 0 4px 16px rgba(219,39,119,0.15) !important;
    transform: translateY(-3px) !important;
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
    """Streaming chat — yields (history, session_id, state_badge, save_btn_update, agent_status, sources_html)."""
    if not user_message.strip():
        yield history, session_id, "", gr.update(), gr.update(visible=False), gr.update()
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
    yield new_history, session_id, "🟢 Active session", gr.update(), gr.update(value="⏳ Processing your request...", visible=True), gr.update()

    response = ""
    last_sources_html = _build_sources_html([])  # default empty
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
                yield new_history, session_id, "🟢 Active session", gr.update(), gr.update(value=status_html, visible=True, elem_classes=["agent-status-wrap", "agent-active-pulse"]), last_sources_html
            else:
                response = chunk
                new_history[-1] = _msg("assistant", response)
                citations = _extract_citations(response)
                if citations:
                    last_sources_html = _build_sources_html(citations)
                state_str = _state_badge(session.state) if session else "🟢 Active session"
                yield new_history, session_id, state_str, gr.update(visible=True), gr.update(visible=False), last_sources_html
    except Exception as e:
        new_session_obj = orch.create_session()
        session_id = new_session_obj.session_id
        new_history = [_msg("assistant", "Your session expired. Starting a new session.")]
        yield new_history, session_id, "🟢 Active session", gr.update(visible=True), gr.update(visible=False), gr.update()


def save_profile(history: list[dict], session_id: str):
    """Trigger profile save via chat."""
    yield from chat("I would like to save my profile", history, session_id)


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


# ── UI layout ──────────────────────────────────────────────────────────────

_all_quick: list[tuple[gr.Button, str]] = []  # populated during layout

with gr.Blocks(
    title="IVF Advisor Command Center",
    theme=gr.themes.Base(
        primary_hue=gr.themes.colors.purple,
        secondary_hue=gr.themes.colors.pink,
        neutral_hue=gr.themes.colors.gray,
        font=gr.themes.GoogleFont("Inter"),
    ),
    css=CSS,
) as demo:

    session_id_state = gr.State("")

    with gr.Row(equal_height=False):

        # ══════════════════════════════════════════════════════════════════
        # COLUMN 1 — Left Navigation Sidebar
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(scale=1, elem_classes=["left-sidebar"]):

            # Logo
            gr.HTML('<div class="sidebar-logo">🌸 IVF Care</div>')

            # Current activity section — patient-friendly label
            gr.HTML('<div class="sidebar-section-title">💬 Current Activity</div>')
            agent_status = gr.Markdown(
                value="Ready to help you",
                visible=True,
                elem_classes=["agent-status-wrap"],
            )

            # Quick Access section — renamed to "Start a Conversation"
            gr.HTML('<div class="sidebar-section-title">💬 Start a Conversation</div>')
            gr.HTML('<p style="font-size:0.75rem;color:#9ca3af;margin:0 0 8px 0">Tap to send a question instantly</p>')

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

            # Support Communities — verified working links
            gr.HTML('<div class="sidebar-section-title">🌐 Support Communities</div>')
            gr.HTML("""
            <div class="communities-block">
                <div>🇮🇳 <a href="https://www.ivfbabble.com/india" target="_blank">IVF Babble India</a></div>
                <div>🇮🇳 <a href="https://www.practo.com/ivf" target="_blank">Practo IVF Forum</a></div>
                <div>🇬🇧 <a href="https://fertilitynetworkuk.org" target="_blank">Fertility Network UK</a></div>
                <div>� <a href="https://resolve.org" target="_blank">RESOLVE (US)</a></div>
            </div>
            """)

            # Language selector
            language_selector = gr.Radio(
                choices=["English", "Hindi"],
                value="English",
                label="🌐 Language",
                interactive=True,
                elem_classes=["lang-selector"],
            )

            # Session status badge
            state_display = gr.Textbox(
                label="Session",
                interactive=False,
                value="🟢 Active session",
                elem_classes=["status-badge"],
                show_label=True,
            )

            # New chat + Save profile buttons — always visible
            new_btn = gr.Button("🔄 New Chat", variant="secondary", size="sm", elem_classes=["sidebar-action-btn"])
            save_profile_btn = gr.Button(
                "💾 Save Profile",
                variant="secondary",
                size="sm",
                visible=True,
                elem_classes=["save-btn"],
            )

        # ══════════════════════════════════════════════════════════════════
        # COLUMN 2 — Central Chat
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(scale=3, elem_classes=["center-col"]):

            # Header
            gr.HTML("""
            <div>
                <p class="chat-header-title">IVF Advisor Command Center</p>
                <p class="chat-header-sub">Your compassionate AI companion — evidence-based, always supportive</p>
            </div>
            """)

            # Chatbot
            chatbot = gr.Chatbot(
                label="",
                height=520,
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
                        scale=8,
                        show_label=False,
                        lines=1,
                        max_lines=4,
                    )
                    send_btn = gr.Button(
                        "Send ➤",
                        scale=1,
                        variant="primary",
                        elem_classes=["send-btn"],
                    )
                with gr.Row():
                    audio_input = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="🎤 Speak (Hindi or English)",
                        show_label=True,
                        scale=1,
                        elem_classes=["audio-compact"],
                    )

            # Example chips — custom styled buttons replacing gr.Examples
            _example_prompts = [
                ("🧬 Lab results", "What are the success rates for women over 38?"),
                ("💊 Injections", "How do I self-administer Gonal-F injections?"),
                ("💰 Delhi costs", "What does IVF cost in Delhi?"),
                ("❤️ Feeling anxious", "I'm feeling anxious about my upcoming egg retrieval"),
            ]
            _example_btns = []
            with gr.Row(elem_classes=["custom-chips-row"]):
                for _chip_label, _chip_prompt in _example_prompts:
                    _eb = gr.Button(_chip_label, size="sm", elem_classes=["example-chip"])
                    _example_btns.append((_eb, _chip_prompt))

            # Disclaimer
            gr.HTML("""
            <div class="disclaimer-banner">
                <p>
                    ⚠️ <strong>Medical Disclaimer:</strong> This platform provides general educational
                    information about IVF and fertility treatments. It is not a substitute for professional
                    medical advice, diagnosis, or treatment. Always seek the guidance of your doctor or
                    qualified fertility specialist with any questions you may have.
                </p>
            </div>
            """)

        # ══════════════════════════════════════════════════════════════════
        # COLUMN 3 — Right Bento Sidebar
        # ══════════════════════════════════════════════════════════════════
        with gr.Column(scale=1, elem_classes=["right-sidebar"]):

            # Evidence & Sources panel
            gr.HTML('<div class="sources-panel"><h4>📚 Evidence &amp; Sources</h4>')
            sources_box = gr.HTML(
                value='<p style="color:#6b7280;font-size:0.82rem;margin:0">Sources will appear here after evidence search responses.</p>',
            )
            gr.HTML('</div>')

            # Bento feature cards — renamed to "Tools & Capabilities"
            gr.HTML('<div class="sidebar-section-title" style="margin-top:8px">🛠️ Tools &amp; Capabilities</div>')
            gr.HTML('<p style="font-size:0.75rem;color:#9ca3af;margin:0 0 8px 0">Specialist tools — click a card to explore</p>')

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
            for _icon, _title, _desc, _prompt in _bento_defs:
                _bbtn = gr.Button(
                    value=(
                        f'<span style="font-size:1.4rem;margin-bottom:6px;display:block">{_icon}</span>'
                        f'<span style="font-weight:700;color:#7c3aed;font-size:0.85rem;margin-bottom:4px;display:block">{_title}</span>'
                        f'<span style="color:#6b7280;font-size:0.76rem;line-height:1.5;display:block">{_desc}</span>'
                    ),
                    variant="secondary",
                    elem_classes=["bento-btn"],
                )
                _bento_btns.append((_bbtn, _prompt))
                _all_quick.append((_bbtn, _prompt))

    # ── Event wiring ──────────────────────────────────────────────────────
    send_btn.click(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, agent_status, sources_box],
    ).then(lambda: "", outputs=msg_input)

    msg_input.submit(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, agent_status, sources_box],
    ).then(lambda: "", outputs=msg_input)

    # Audio: transcribe when recording stops, fill text box then auto-send
    audio_input.stop_recording(
        fn=handle_audio,
        inputs=[audio_input, language_selector],
        outputs=[msg_input],
    ).then(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, agent_status, sources_box],
    ).then(lambda: "", outputs=msg_input)

    new_btn.click(fn=new_session, outputs=[chatbot, session_id_state, state_display])

    save_profile_btn.click(
        fn=save_profile,
        inputs=[chatbot, session_id_state],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn, agent_status, sources_box],
    )

    for _btn, _prompt in _all_quick:
        _btn.click(
            fn=_make_quick_handler(_prompt),
            inputs=[chatbot, session_id_state],
            outputs=[chatbot, session_id_state, state_display, save_profile_btn, agent_status, sources_box],
        )

    demo.load(fn=new_session, outputs=[chatbot, session_id_state, state_display])

    # Wire example chips — fill input box on click
    for _eb, _ep in _example_btns:
        _eb.click(fn=set_example, inputs=gr.State(_ep), outputs=msg_input)


port = int(os.environ.get("PORT", 7860))
demo.launch(
    server_name="0.0.0.0",
    server_port=port,
    share=False,
    show_error=True,
    show_api=False,
)
