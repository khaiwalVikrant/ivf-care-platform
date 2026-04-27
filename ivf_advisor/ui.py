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
.gradio-container { max-width: 1100px !important; margin: 0 auto !important; padding: 0 !important; }

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
.main-content { padding: 0 20px 80px 20px; }
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
    """Streaming chat — yields (history, session_id, state_badge, save_btn_update)."""
    if not user_message.strip():
        yield history, session_id, "", gr.update()
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
    yield new_history, session_id, "🟢 Active session", gr.update()

    response = ""
    try:
        for chunk, session in orch.turn_stream(session_id, message_to_send):
            if chunk.startswith("_thinking:"):
                tool = chunk.replace("_thinking:", "").replace("_", " ").strip()
                tool_labels = {
                    "lab result": "🧬 Analysing lab results...",
                    "evidence search": "🔬 Searching evidence...",
                    "cost breakdown": "💰 Calculating costs...",
                    "injection guide": "💊 Checking medications...",
                    "timeline": "📅 Building timeline...",
                    "success rate": "📊 Computing success rates...",
                    "wellness guide": "🥗 Preparing wellness tips...",
                    "emotional support": "❤️ Preparing support...",
                    "red flag": "🚩 Checking clinic claims...",
                    "journey guide": "🗺️ Mapping your journey...",
                    "scope guard": "🛡️ Checking scope...",
                }
                display = tool_labels.get(tool.lower(), f"🔍 {tool.title()}...")
                new_history[-1] = _msg("assistant", display)
            else:
                response = chunk
                new_history[-1] = _msg("assistant", response)
            state_str = _state_badge(session.state) if session else "🟢 Active session"
            yield new_history, session_id, state_str, gr.update(visible=True)
    except Exception as e:
        new_session_obj = orch.create_session()
        session_id = new_session_obj.session_id
        new_history = [_msg("assistant", "Your session expired. Starting a new session.")]
        yield new_history, session_id, "🟢 Active session", gr.update(visible=True)


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
        <div class="top-bar-right" id="top-bar-right-slot"></div>
    </div>
    """)

    with gr.Column(elem_classes=["main-content"]):

        # ── Top controls row (language + session badge + buttons) ──
        with gr.Row(elem_classes=["action-row"]):
            state_display = gr.Textbox(
                label="",
                interactive=False,
                value="🟢 Active session",
                elem_classes=["status-badge"],
                scale=2,
                show_label=False,
            )
            language_selector = gr.Radio(
                choices=["English", "Hindi"],
                value="English",
                label="🌐 Language",
                interactive=True,
                elem_classes=["lang-selector"],
                scale=2,
            )
            new_btn = gr.Button("🔄 New chat", variant="secondary", size="sm", scale=1)
            save_profile_btn = gr.Button(
                "💾 Save my profile",
                variant="secondary",
                size="sm",
                visible=False,
                elem_classes=["save-btn"],
                scale=1,
            )

        # ── Welcome feature cards (shown before first message) ──
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

        # ── Help accordion ──
        with gr.Accordion("❓ What can I help you with?", open=False, elem_classes=["help-accordion"]):
            gr.HTML("""
            <div class="help-grid">
                <div class="help-card">
                    <div class="icon">🧬</div>
                    <div class="title">Lab Result Interpreter</div>
                    <p class="desc">Share your AMH, FSH, or AFC values and I'll explain what they mean for your IVF journey in plain language.</p>
                </div>
                <div class="help-card">
                    <div class="icon">📅</div>
                    <div class="title">Treatment Timeline</div>
                    <p class="desc">Tell me your start date and protocol — I'll generate a personalised week-by-week IVF schedule.</p>
                </div>
                <div class="help-card">
                    <div class="icon">💊</div>
                    <div class="title">Injection Training</div>
                    <p class="desc">Step-by-step guidance for subcutaneous and intramuscular injections, including site rotation and missed dose advice.</p>
                </div>
                <div class="help-card">
                    <div class="icon">💰</div>
                    <div class="title">Cost Breakdown</div>
                    <p class="desc">Get detailed IVF cost estimates in your city — including INR ranges for Indian cities like Mumbai, Delhi, Bangalore.</p>
                </div>
                <div class="help-card">
                    <div class="icon">📊</div>
                    <div class="title">Success Rate Calculator</div>
                    <p class="desc">Enter your age and diagnosis to get personalised IVF success rate estimates based on SART/HFEA data.</p>
                </div>
                <div class="help-card">
                    <div class="icon">🥗</div>
                    <div class="title">Wellness Guide</div>
                    <p class="desc">Stage-specific diet, exercise, sleep, and supplement advice for stimulation, egg retrieval, two-week wait, and transfer.</p>
                </div>
                <div class="help-card">
                    <div class="icon">🚩</div>
                    <div class="title">Clinic Red Flag Checker</div>
                    <p class="desc">Describe what a clinic told you — I'll flag unrealistic claims like guaranteed pregnancy or inflated success rates.</p>
                </div>
                <div class="help-card">
                    <div class="icon">❤️</div>
                    <div class="title">Emotional Support</div>
                    <p class="desc">IVF is emotionally hard. I'm here to listen, offer coping strategies, and connect you with support resources when you need them.</p>
                </div>
                <div class="help-card">
                    <div class="icon">🔬</div>
                    <div class="title">Evidence Search</div>
                    <p class="desc">Ask clinical questions and get answers grounded in ESHRE, ASRM, and NICE guidelines from the knowledge base.</p>
                </div>
                <div class="help-card">
                    <div class="icon">🌐</div>
                    <div class="title">Hindi Support</div>
                    <p class="desc">Switch to Hindi using the language selector above — I'll respond in Devanagari script with medical terms in English.</p>
                </div>
            </div>
            """)

    # ── Event wiring ──
    send_btn.click(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn],
    ).then(lambda: "", outputs=msg_input)

    msg_input.submit(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn],
    ).then(lambda: "", outputs=msg_input)

    # Audio: transcribe when recording stops, fill text box then auto-send
    audio_input.stop_recording(
        fn=handle_audio,
        inputs=[audio_input, language_selector],
        outputs=[msg_input],
    ).then(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state, language_selector],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn],
    ).then(lambda: "", outputs=msg_input)

    new_btn.click(fn=new_session, outputs=[chatbot, session_id_state, state_display])

    save_profile_btn.click(
        fn=save_profile,
        inputs=[chatbot, session_id_state],
        outputs=[chatbot, session_id_state, state_display, save_profile_btn],
    )

    for _btn, _prompt in _all_quick:
        _btn.click(
            fn=_make_quick_handler(_prompt),
            inputs=[chatbot, session_id_state],
            outputs=[chatbot, session_id_state, state_display, save_profile_btn],
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
