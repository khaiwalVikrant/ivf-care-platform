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
    "Use the quick action buttons on the left, or just tell me what you need.\n\n"
    "_Note: I provide educational information only — always consult your fertility specialist._"
)

# ── Categorised quick actions ──────────────────────────────────────────────
QUICK_PROMPTS: dict[str, list[tuple[str, str]]] = {
    "🔬 Clinical": [
        ("🧬 My lab results",     "I want to understand my AMH/FSH results"),
        ("📊 Success rates",      "What are the success rates for someone my age?"),
        ("🚩 Check clinic claim", "My clinic says they have 80% success rate for women over 40"),
        ("🔬 Research evidence",  "Give me research references about IVF success rates"),
    ],
    "📅 Planning": [
        ("📅 Treatment timeline", "Can you create a treatment timeline starting next Monday?"),
        ("🏥 Book appointment",   "Book a consultation appointment for next week"),
        ("💉 Book nurse visit",   "I need a nurse to come home for my injection tomorrow at 9am"),
        ("⏰ My schedule",        "Tell me all my upcoming schedule and reminders"),
    ],
    "💊 Medications": [
        ("💊 Injection guide",    "How do I self-administer subcutaneous injections?"),
        ("⏰ Set reminder",       "Set a daily reminder for my Gonal-F injection at 9pm"),
    ],
    "💰 Costs": [
        ("💰 India IVF costs",   "What does IVF cost in Mumbai?"),
        ("📈 Cost summary",      "Show me my IVF cycle cost summary"),
    ],
    "🌿 Wellness & Support": [
        ("🥗 Wellness tips",     "What should I eat during stimulation?"),
        ("❤️ Emotional support", "I'm feeling overwhelmed and anxious about IVF"),
    ],
}

# ── CSS ────────────────────────────────────────────────────────────────────
CSS = """
/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }
body, .gradio-container {
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    background: #f8f4ff !important;
}
footer, .footer { display: none !important; }
.gradio-container { max-width: 1280px !important; margin: 0 auto !important; }

/* ── Gradient header ── */
.ivf-header {
    background: linear-gradient(135deg, #6d28d9 0%, #be185d 100%);
    border-radius: 20px;
    padding: 28px 36px;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(109,40,217,0.25);
}
.ivf-header h1 {
    color: white !important;
    margin: 0 0 6px 0;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
}
.ivf-header .tagline {
    color: rgba(255,255,255,0.88) !important;
    margin: 0;
    font-size: 1rem;
}

/* ── Sidebar card ── */
.sidebar-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #ede9fe;
    padding: 14px 12px;
    margin-bottom: 10px;
    box-shadow: 0 2px 12px rgba(109,40,217,0.07);
}
.sidebar-section-title {
    color: #5b21b6 !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #ede9fe;
}

/* ── Quick action pill buttons ── */
.quick-pill button {
    border-radius: 999px !important;
    font-size: 0.80rem !important;
    padding: 5px 12px !important;
    border: 1px solid #ddd6fe !important;
    background: #faf5ff !important;
    color: #4c1d95 !important;
    font-weight: 500 !important;
    width: 100% !important;
    text-align: left !important;
    margin-bottom: 4px !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}
.quick-pill button:hover {
    background: linear-gradient(135deg, #6d28d9 0%, #be185d 100%) !important;
    color: white !important;
    border-color: transparent !important;
    box-shadow: 0 2px 8px rgba(109,40,217,0.3) !important;
}

/* ── Chatbot ── */
.chat-wrap {
    border-radius: 20px !important;
    border: 1px solid #ede9fe !important;
    background: white !important;
    box-shadow: 0 4px 24px rgba(109,40,217,0.08) !important;
    overflow: hidden !important;
}
.chat-wrap .message.user {
    background: linear-gradient(135deg, #6d28d9 0%, #be185d 100%) !important;
    color: white !important;
    border-radius: 18px 18px 4px 18px !important;
}
.chat-wrap .message.bot {
    background: #faf5ff !important;
    border: 1px solid #ede9fe !important;
    border-radius: 18px 18px 18px 4px !important;
    color: #1f2937 !important;
}

/* ── Input area ── */
.input-area {
    background: white;
    border-radius: 16px;
    border: 1px solid #ede9fe;
    padding: 12px 16px;
    margin-top: 8px;
    box-shadow: 0 2px 12px rgba(109,40,217,0.06);
}
.input-area textarea {
    border-radius: 24px !important;
    border: 2px solid #ede9fe !important;
    padding: 12px 20px !important;
    font-size: 0.95rem !important;
    background: #faf5ff !important;
    resize: none !important;
    transition: border-color 0.2s !important;
}
.input-area textarea:focus {
    border-color: #7c3aed !important;
    background: white !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}

/* ── Send button ── */
.send-btn button {
    border-radius: 24px !important;
    background: linear-gradient(135deg, #6d28d9 0%, #be185d 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 10px 22px !important;
    box-shadow: 0 2px 10px rgba(109,40,217,0.3) !important;
    transition: opacity 0.15s !important;
}
.send-btn button:hover { opacity: 0.88 !important; }

/* ── Status badge ── */
.status-badge textarea, .status-badge input {
    border-radius: 999px !important;
    background: #f5f3ff !important;
    border: 1px solid #ddd6fe !important;
    color: #5b21b6 !important;
    font-size: 0.80rem !important;
    font-weight: 600 !important;
    padding: 4px 14px !important;
    text-align: center !important;
}

/* ── Action row ── */
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
}

/* ── Language selector ── */
.lang-selector .wrap { gap: 8px !important; }
.lang-selector label { font-size: 0.82rem !important; color: #4c1d95 !important; }

/* ── Help accordion ── */
.help-accordion {
    border-radius: 16px !important;
    border: 1px solid #ede9fe !important;
    background: white !important;
    margin-top: 8px !important;
    overflow: hidden !important;
}
.help-accordion .label-wrap {
    background: linear-gradient(135deg, #6d28d9 0%, #be185d 100%) !important;
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
    padding: 4px;
}
.help-card {
    background: #faf5ff;
    border: 1px solid #ede9fe;
    border-radius: 12px;
    padding: 12px 14px;
}
.help-card .icon { font-size: 1.4rem; margin-bottom: 4px; }
.help-card .title { font-weight: 700; color: #4c1d95; font-size: 0.85rem; margin-bottom: 4px; }
.help-card .desc { color: #374151; font-size: 0.78rem; line-height: 1.5; margin: 0; }

/* ── Disclaimer banner ── */
.disclaimer-banner {
    background: #fff7ed;
    border: 1px solid #fed7aa;
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

/* ── About card ── */
.about-card {
    background: linear-gradient(135deg, #faf5ff 0%, #fdf2f8 100%);
    border-radius: 16px;
    border: 1px solid #ede9fe;
    padding: 14px;
    box-shadow: 0 2px 12px rgba(109,40,217,0.05);
}
.about-card p {
    color: #374151 !important;
    font-size: 0.80rem !important;
    line-height: 1.6 !important;
    margin: 0 !important;
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
) -> tuple[list[dict], str, str, gr.update]:
    if not user_message.strip():
        return history, session_id, "", gr.update()

    orch = _get_orchestrator()

    if not session_id or orch.get_session(session_id) is None:
        session = orch.create_session()
        session_id = session.session_id
        history = [_msg("assistant", WELCOME_MESSAGE)]

    message_to_send = user_message
    if language == "Hindi":
        message_to_send = f"Please respond in Hindi (Devanagari script).\n\n{user_message}"

    try:
        response = orch.turn(session_id, message_to_send)
    except Exception:
        session = orch.create_session()
        session_id = session.session_id
        history = [_msg("assistant", "Your session expired. Starting a new session.")]
        return history, session_id, _state_badge(orch.get_session(session_id).state), gr.update(visible=True)

    new_history = list(history) + [
        _msg("user", user_message),
        _msg("assistant", response),
    ]
    session = orch.get_session(session_id)
    show_save = gr.update(visible=True) if len(new_history) >= 2 else gr.update()
    return new_history, session_id, _state_badge(session.state) if session else "", show_save


def save_profile(history: list[dict], session_id: str) -> tuple[list[dict], str, str, gr.update]:
    return chat("I would like to save my profile", history, session_id)


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


def transcribe_and_fill(audio_data: tuple | None, language: str = "English") -> str:
    """Transcribe recorded audio and return text for the input box."""
    if audio_data is None:
        return ""
    try:
        import numpy as np
        import wave
        import io

        sample_rate, audio_array = audio_data
        # Convert to 16-bit PCM WAV bytes
        audio_int16 = (audio_array * 32767).astype(np.int16) if audio_array.dtype != np.int16 else audio_array
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        audio_bytes = buf.getvalue()

        lang_code = "hi-IN" if language == "Hindi" else "en-IN"
        transcript = transcribe_audio_bytes(audio_bytes, language_code=lang_code)
        return transcript or ""
    except Exception:
        return ""


def _make_quick_handler(prompt: str):
    """Return a handler that fires a quick-action prompt."""
    def _handler(history: list[dict], session_id: str):
        return chat(prompt, history, session_id)[:3]
    return _handler


# ── UI layout ──────────────────────────────────────────────────────────────

_all_quick: list[tuple[gr.Button, str]] = []  # populated during layout

with gr.Blocks(
    title="IVF Care Platform",
    theme=gr.themes.Soft(
        primary_hue=gr.themes.colors.purple,
        secondary_hue=gr.themes.colors.pink,
        neutral_hue=gr.themes.colors.slate,
        font=gr.themes.GoogleFont("Inter"),
    ),
    css=CSS,
) as demo:

    # ── Gradient header ──
    gr.HTML("""
    <div class="ivf-header">
        <h1>🌸 IVF Care Platform</h1>
        <p class="tagline">Your compassionate AI companion — ask questions, plan your journey, and feel supported every step of the way.</p>
    </div>
    """)

    with gr.Row(equal_height=False):

        # ── Left sidebar ──
        with gr.Column(scale=1, min_width=230):
            for _section_title, _prompts in QUICK_PROMPTS.items():
                gr.HTML(
                    f'<div class="sidebar-card">'
                    f'<p class="sidebar-section-title">{_section_title}</p>'
                )
                for _label, _prompt in _prompts:
                    _btn = gr.Button(_label, variant="secondary", elem_classes=["quick-pill"])
                    _all_quick.append((_btn, _prompt))
                gr.HTML('</div>')

            gr.HTML("""
            <div class="about-card">
                <p>
                    <strong style="color:#4c1d95">Educational use only.</strong><br>
                    This assistant does not provide medical advice.
                    Always consult your fertility specialist before making treatment decisions.
                </p>
            </div>
            """)

        # ── Main chat column ──
        with gr.Column(scale=3):

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

            chatbot = gr.Chatbot(
                label="",
                height=500,
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
            outputs=[chatbot, session_id_state, state_display],
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
