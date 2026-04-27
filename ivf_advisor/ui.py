"""Gradio chat UI for the IVF Treatment Advisor Agent — premium redesign."""

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
    background: #FAFAF8 !important;
    color: #1A1A2E !important;
}
footer, .footer { display: none !important; }
.gradio-container { max-width: 100% !important; margin: 0 !important; padding: 0 !important; }
.contain { max-width: 100% !important; padding: 0 !important; }
.gap { gap: 0 !important; }

/* ── Sticky top bar ── */
.top-bar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(250,250,248,0.95);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(13,115,119,0.12);
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0;
}
.top-bar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
}
.top-bar-logo .logo-icon { font-size: 1.6rem; }
.top-bar-logo .logo-text {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0D7377;
    letter-spacing: -0.3px;
}
.top-bar-logo .logo-sub {
    font-size: 0.72rem;
    color: #6b7280;
    font-weight: 400;
    display: block;
    margin-top: -2px;
}
.top-bar-right {
    display: flex;
    align-items: center;
    gap: 12px;
}

/* ── Status badge ── */
.status-badge textarea, .status-badge input {
    border-radius: 999px !important;
    background: #f0fafa !important;
    border: 1px solid rgba(13,115,119,0.25) !important;
    color: #0D7377 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 4px 14px !important;
    text-align: center !important;
    min-width: 160px !important;
}

/* ── Language selector ── */
.lang-selector .wrap { gap: 6px !important; }
.lang-selector label { font-size: 0.80rem !important; color: #0D7377 !important; font-weight: 500 !important; }
.lang-selector .gr-radio-row { gap: 6px !important; }

/* ── Welcome feature cards ── */
.welcome-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 24px 0 8px 0;
}
.welcome-card {
    background: white;
    border: 1px solid rgba(13,115,119,0.15);
    border-radius: 16px;
    padding: 20px 18px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 2px 12px rgba(13,115,119,0.06);
}
.welcome-card:hover {
    border-color: #0D7377;
    box-shadow: 0 6px 24px rgba(13,115,119,0.15);
    transform: translateY(-2px);
}
.welcome-card .wc-icon { font-size: 2rem; margin-bottom: 10px; }
.welcome-card .wc-title { font-weight: 700; color: #0D7377; font-size: 0.95rem; margin-bottom: 6px; }
.welcome-card .wc-desc { color: #4b5563; font-size: 0.80rem; line-height: 1.55; margin: 0; }

/* ── Chatbot bubbles ── */
.chat-wrap {
    border-radius: 20px !important;
    border: 1px solid rgba(13,115,119,0.12) !important;
    background: #FAFAF8 !important;
    box-shadow: 0 4px 24px rgba(13,115,119,0.07) !important;
    overflow: hidden !important;
}
/* User bubble */
.chat-wrap .message.user > div,
.chat-wrap [data-testid="user"] .bubble-wrap {
    background: linear-gradient(135deg, #0D7377 0%, #14A085 100%) !important;
    color: white !important;
    border-radius: 18px 18px 4px 18px !important;
    box-shadow: 0 2px 10px rgba(13,115,119,0.25) !important;
}
/* Bot bubble */
.chat-wrap .message.bot > div,
.chat-wrap [data-testid="bot"] .bubble-wrap {
    background: rgba(255,255,255,0.92) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(13,115,119,0.12) !important;
    border-left: 3px solid #0D7377 !important;
    border-radius: 18px 18px 18px 4px !important;
    color: #1A1A2E !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06) !important;
}

/* ── Quick action chips row ── */
.chips-row {
    display: flex;
    flex-direction: row;
    gap: 8px;
    overflow-x: auto;
    padding: 10px 0 6px 0;
    scrollbar-width: none;
    -ms-overflow-style: none;
}
.chips-row::-webkit-scrollbar { display: none; }
.chip-btn button {
    border-radius: 999px !important;
    font-size: 0.80rem !important;
    padding: 6px 14px !important;
    border: 1.5px solid rgba(13,115,119,0.3) !important;
    background: white !important;
    color: #0D7377 !important;
    font-weight: 500 !important;
    white-space: nowrap !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
    height: auto !important;
    min-width: unset !important;
}
.chip-btn button:hover {
    background: #0D7377 !important;
    color: white !important;
    border-color: #0D7377 !important;
    box-shadow: 0 2px 8px rgba(13,115,119,0.3) !important;
}

/* ── Input area ── */
.input-area {
    background: white;
    border-radius: 20px;
    border: 1.5px solid rgba(13,115,119,0.2);
    padding: 14px 16px 10px 16px;
    margin-top: 6px;
    box-shadow: 0 2px 16px rgba(13,115,119,0.06);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.input-area:focus-within {
    border-color: #0D7377 !important;
    box-shadow: 0 0 0 3px rgba(13,115,119,0.12), 0 2px 16px rgba(13,115,119,0.1) !important;
}
.input-area textarea {
    border-radius: 12px !important;
    border: 1.5px solid rgba(13,115,119,0.15) !important;
    padding: 10px 16px !important;
    font-size: 0.95rem !important;
    background: #FAFAF8 !important;
    resize: none !important;
    color: #1A1A2E !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.input-area textarea:focus {
    border-color: #0D7377 !important;
    background: white !important;
    outline: none !important;
    box-shadow: none !important;
}

/* ── Glowing input animation while waiting ── */
@keyframes glow-pulse {
    0%   { box-shadow: 0 0 0 3px rgba(13,115,119,0.15); border-color: #0D7377; }
    50%  { box-shadow: 0 0 0 5px rgba(244,132,95,0.2);  border-color: #F4845F; }
    100% { box-shadow: 0 0 0 3px rgba(13,115,119,0.15); border-color: #0D7377; }
}
.input-waiting {
    animation: glow-pulse 1.6s ease-in-out infinite !important;
}

/* ── Send button ── */
.send-btn button {
    border-radius: 12px !important;
    background: linear-gradient(135deg, #0D7377 0%, #14A085 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 10px 22px !important;
    box-shadow: 0 2px 10px rgba(13,115,119,0.3) !important;
    transition: opacity 0.15s, transform 0.1s !important;
    height: 42px !important;
}
.send-btn button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important; }
.send-btn button:active { transform: translateY(0) !important; }

/* ── Action row ── */
.action-row { align-items: center !important; gap: 8px !important; }
.action-row button {
    border-radius: 999px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

/* ── Save profile button ── */
.save-btn button {
    border-radius: 999px !important;
    background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(5,150,105,0.3) !important;
    font-size: 0.82rem !important;
}

/* ── Floating mic button ── */
.floating-mic {
    position: fixed !important;
    bottom: 28px !important;
    right: 28px !important;
    z-index: 200 !important;
    width: 56px !important;
    height: 56px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #F4845F 0%, #e8623a 100%) !important;
    box-shadow: 0 4px 20px rgba(244,132,95,0.45) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    border: none !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.floating-mic:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 6px 28px rgba(244,132,95,0.55) !important;
}
/* Hide the default audio widget label/border, keep it minimal */
.audio-hidden {
    opacity: 0;
    position: absolute;
    pointer-events: none;
    width: 1px;
    height: 1px;
    overflow: hidden;
}

/* ── Help accordion ── */
.help-accordion {
    border-radius: 16px !important;
    border: 1px solid rgba(13,115,119,0.15) !important;
    background: white !important;
    margin-top: 8px !important;
    overflow: hidden !important;
}
.help-accordion .label-wrap {
    background: linear-gradient(135deg, #0D7377 0%, #14A085 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 10px 16px !important;
}
.help-accordion .label-wrap span { color: white !important; }
.help-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    padding: 14px;
}
.help-card {
    background: #f0fafa;
    border: 1px solid rgba(13,115,119,0.12);
    border-radius: 12px;
    padding: 12px 14px;
}
.help-card .icon { font-size: 1.4rem; margin-bottom: 4px; }
.help-card .title { font-weight: 700; color: #0D7377; font-size: 0.85rem; margin-bottom: 4px; }
.help-card .desc { color: #374151; font-size: 0.78rem; line-height: 1.5; margin: 0; }

/* ── Disclaimer banner ── */
.disclaimer-banner {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 12px;
    padding: 10px 16px;
    margin-top: 8px;
}
.disclaimer-banner p {
    color: #92400e !important;
    font-size: 0.78rem !important;
    margin: 0 !important;
    line-height: 1.5 !important;
}

/* ── Main content padding ── */
.main-content { padding: 0 32px 80px 32px; max-width: 960px; margin: 0 auto; }

/* ── Agent status indicator ── */
.agent-status {
    background: linear-gradient(135deg, #f0fafa 0%, #fdf2f8 100%);
    border: 1px solid rgba(13,115,119,0.2);
    border-left: 4px solid #0D7377;
    border-radius: 10px;
    padding: 10px 16px;
    margin-bottom: 8px;
    font-size: 0.85rem;
    color: #0D7377;
    font-weight: 500;
}

/* ── Sources sidebar ── */
.sources-panel {
    background: white;
    border: 1px solid rgba(13,115,119,0.15);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 2px 12px rgba(13,115,119,0.06);
    min-height: 200px;
}
.sources-panel h4 {
    color: #0D7377;
    font-size: 0.85rem;
    font-weight: 700;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(13,115,119,0.12);
}
.source-item {
    background: #f0fafa;
    border: 1px solid rgba(13,115,119,0.1);
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 0.78rem;
    color: #374151;
    line-height: 1.4;
}
.sources-list { display: flex; flex-direction: column; gap: 4px; }

/* ── Two-column layout ── */
.chat-col { flex: 3 !important; }
.sidebar-col { flex: 1 !important; min-width: 220px !important; max-width: 280px !important; }
.feature-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 0 4px 0;
}
.feature-pill {
    background: white;
    border: 1px solid rgba(13,115,119,0.2);
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #0D7377;
    white-space: nowrap;
    box-shadow: 0 1px 4px rgba(13,115,119,0.08);
}

/* ── Top bar controls (Gradio components inside top bar area) ── */
.top-controls {
    background: rgba(250,250,248,0.95);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(13,115,119,0.1);
    padding: 8px 32px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.top-controls .status-badge textarea {
    min-width: 130px !important;
    max-width: 160px !important;
}
.top-controls .lang-selector { flex-shrink: 0; }
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
                yield new_history, session_id, "🟢 Active session", gr.update(), gr.update(value=status_html, visible=True), gr.update()
            else:
                response = chunk
                new_history[-1] = _msg("assistant", response)
                citations = _extract_citations(response)
                sources_html = _build_sources_html(citations)
                state_str = _state_badge(session.state) if session else "🟢 Active session"
                yield new_history, session_id, state_str, gr.update(visible=True), gr.update(visible=False), sources_html
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
        return '<p style="color:#6b7280;font-size:0.82rem;margin:0">Sources will appear here after evidence search responses.</p>'
    items = "".join(
        f'<div class="source-item">📄 {c}</div>'
        for c in citations
    )
    return f'<div class="sources-list">{items}</div>'


# ── UI layout ──────────────────────────────────────────────────────────────

_all_quick: list[tuple[gr.Button, str]] = []  # populated during layout

with gr.Blocks(
    title="IVF Care Platform",
    theme=gr.themes.Base(
        primary_hue=gr.themes.colors.teal,
        secondary_hue=gr.themes.colors.orange,
        neutral_hue=gr.themes.colors.gray,
        font=gr.themes.GoogleFont("Inter"),
    ),
    css=CSS,
) as demo:

    # ── Sticky top bar ──
    gr.HTML("""
    <div class="top-bar">
        <div class="top-bar-logo">
            <span class="logo-icon">🌸</span>
            <div>
                <span class="logo-text">IVF Care Platform</span>
                <span class="logo-sub">Your compassionate AI companion</span>
            </div>
        </div>
    </div>
    """)

    # ── Top controls row — clean, compact ──
    with gr.Row(elem_classes=["top-controls"]):
        state_display = gr.Textbox(
            label="",
            interactive=False,
            value="🟢 Active session",
            elem_classes=["status-badge"],
            scale=1,
            show_label=False,
        )
        language_selector = gr.Radio(
            choices=["English", "Hindi"],
            value="English",
            label="🌐",
            interactive=True,
            elem_classes=["lang-selector"],
            scale=1,
        )
        new_btn = gr.Button("🔄 New", variant="secondary", size="sm", scale=0)
        save_profile_btn = gr.Button(
            "💾 Save profile",
            variant="secondary",
            size="sm",
            visible=False,
            elem_classes=["save-btn"],
            scale=0,
        )

    with gr.Column(elem_classes=["main-content"]):

        # ── Feature pills — always visible, shows all capabilities ──
        gr.HTML("""
        <div class="feature-pills">
            <span class="feature-pill">🧬 Lab Results</span>
            <span class="feature-pill">📅 Treatment Timeline</span>
            <span class="feature-pill">💊 Injection Training</span>
            <span class="feature-pill">💰 Cost Breakdown (INR)</span>
            <span class="feature-pill">📊 Success Rates</span>
            <span class="feature-pill">🥗 Wellness Guide</span>
            <span class="feature-pill">🚩 Clinic Red Flags</span>
            <span class="feature-pill">❤️ Emotional Support</span>
            <span class="feature-pill">🔬 Evidence Search</span>
            <span class="feature-pill">🌐 Hindi Support</span>
            <span class="feature-pill">📅 Book Appointments</span>
            <span class="feature-pill">⏰ Medication Reminders</span>
        </div>
        """)

        # ── Welcome feature cards ──
        gr.HTML("""
        <div class="welcome-cards">
            <div class="welcome-card">
                <div class="wc-icon">🧬</div>
                <div class="wc-title">Lab Results</div>
                <p class="wc-desc">Share your AMH, FSH, AFC values for plain-language interpretation tailored to your situation.</p>
            </div>
            <div class="welcome-card">
                <div class="wc-icon">💰</div>
                <div class="wc-title">Cost Planning</div>
                <p class="wc-desc">Get IVF cost estimates in your city including detailed INR ranges for Indian clinics.</p>
            </div>
            <div class="welcome-card">
                <div class="wc-icon">❤️</div>
                <div class="wc-title">Support &amp; Guidance</div>
                <p class="wc-desc">Evidence-based answers, emotional support, and step-by-step injection training.</p>
            </div>
        </div>
        """)

        # ── Two-column layout: chat + sources sidebar ──
        with gr.Row():
            with gr.Column(scale=3, elem_classes=["chat-col"]):

                # ── Agent status indicator ──
                agent_status = gr.Markdown(
                    value="",
                    visible=False,
                    elem_classes=["agent-status"],
                )

                # ── Chatbot ──
                chatbot = gr.Chatbot(
                    label="",
                    height=480,
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

                session_id_state = gr.State("")

                # ── Quick action chips row ──
                with gr.Row(elem_classes=["chips-row"]):
                    for _label, _prompt in QUICK_CHIPS:
                        _btn = gr.Button(_label, variant="secondary", size="sm", elem_classes=["chip-btn"])
                        _all_quick.append((_btn, _prompt))

                # ── Input area ──
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
                            label="🎤 Speak your question (Hindi or English)",
                            show_label=True,
                            scale=1,
                        )

                # ── Disclaimer ──
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

            # ── Sources sidebar ──
            with gr.Column(scale=1, elem_classes=["sidebar-col"]):
                gr.HTML('<div class="sources-panel"><h4>📚 Evidence &amp; Sources</h4>')
                sources_box = gr.HTML(
                    value='<p style="color:#6b7280;font-size:0.82rem;margin:0">Sources will appear here after evidence search responses.</p>',
                )
                gr.HTML('</div>')

                gr.HTML("""
                <div class="sources-panel" style="margin-top:12px">
                    <h4>⚡ Quick Actions</h4>
                    <p style="color:#6b7280;font-size:0.78rem;margin:0 0 8px 0">Use the chips above the input to quickly access all features.</p>
                    <div style="font-size:0.78rem;color:#374151;line-height:2">
                        🧬 Lab Results<br>
                        📅 Treatment Timeline<br>
                        💊 Injection Training<br>
                        💰 Cost Breakdown<br>
                        📊 Success Rates<br>
                        🥗 Wellness Guide<br>
                        🚩 Clinic Red Flags<br>
                        ❤️ Emotional Support<br>
                        🔬 Evidence Search<br>
                        🌐 Hindi Support
                    </div>
                </div>
                """)

    # ── Event wiring ──
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


port = int(os.environ.get("PORT", 7860))
demo.launch(
    server_name="0.0.0.0",
    server_port=port,
    share=False,
    show_error=True,
    show_api=False,
)
