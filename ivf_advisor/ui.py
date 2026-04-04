"""Gradio chat UI for the IVF Treatment Advisor Agent."""

from __future__ import annotations

import os

import gradio as gr  # type: ignore

from ivf_advisor.models import ConversationState
from ivf_advisor.agent import create_agent
from ivf_advisor.orchestrator import ConversationOrchestrator

_orchestrator = ConversationOrchestrator(agent=create_agent())


def _get_orchestrator():
    return _orchestrator


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


def _state_badge(state: ConversationState) -> str:
    labels = {
        ConversationState.PROFILE_COLLECTION: "📋 Profile collection",
        ConversationState.MAIN_LOOP: "✅ Active session",
    }
    return labels.get(state, state.value)


def new_session() -> tuple[list[dict], str, str]:
    orch = _get_orchestrator()
    session = orch.create_session()
    session_id = session.session_id
    response = orch.turn(session_id, "")
    return [_msg("assistant", response)], session_id, _state_badge(session.state)


def chat(user_message: str, history: list[dict], session_id: str) -> tuple[list[dict], str, str]:
    if not user_message.strip():
        return history, session_id, ""

    orch = _get_orchestrator()

    if not session_id or orch.get_session(session_id) is None:
        session = orch.create_session()
        session_id = session.session_id
        disclaimer = orch.turn(session_id, "")
        history = [_msg("assistant", disclaimer)]

    try:
        response = orch.turn(session_id, user_message)
    except Exception:
        session = orch.create_session()
        session_id = session.session_id
        orch.turn(session_id, "")
        history = [_msg("assistant", "Your session expired. Starting a new session.")]
        return history, session_id, _state_badge(orch.get_session(session_id).state)

    new_history = list(history) + [
        _msg("user", user_message),
        _msg("assistant", response),
    ]
    session = orch.get_session(session_id)
    return new_history, session_id, _state_badge(session.state) if session else ""


def quick_action(prompt: str, history: list[dict], session_id: str):
    return chat(prompt, history, session_id)


CSS = """
/* ── Global ── */
body, .gradio-container {
    font-family: 'Inter', sans-serif !important;
    background: #fdf6ff !important;
}
footer { display: none !important; }

/* ── Header ── */
.header-box {
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 8px;
    color: white;
}
.header-box h1 { color: white !important; margin: 0 0 4px 0; font-size: 1.8rem; }
.header-box p  { color: rgba(255,255,255,0.85) !important; margin: 0; font-size: 0.95rem; }

/* ── Chatbot ── */
.chatbot-wrap .wrap { border-radius: 16px !important; border: 1px solid #e9d5ff !important; }
.chatbot-wrap { background: white; border-radius: 16px; }

/* ── Quick action buttons ── */
.quick-btn { border-radius: 20px !important; font-size: 0.82rem !important; }

/* ── Input row ── */
.input-row textarea {
    border-radius: 24px !important;
    border: 2px solid #e9d5ff !important;
    padding: 12px 20px !important;
    font-size: 0.95rem !important;
}
.input-row textarea:focus { border-color: #7c3aed !important; }
.send-btn { border-radius: 24px !important; }

/* ── Status badge ── */
.status-box textarea {
    border-radius: 8px !important;
    background: #f5f3ff !important;
    border: 1px solid #ddd6fe !important;
    color: #5b21b6 !important;
    font-size: 0.82rem !important;
}

/* ── Sidebar ── */
.sidebar-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #e9d5ff;
    padding: 16px;
}
.sidebar-heading h3 {
    color: #4c1d95 !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
}
.sidebar-card p, .sidebar-card span, .sidebar-card label {
    color: #374151 !important;
    font-size: 0.85rem !important;
}
.small-text p {
    color: #4b5563 !important;
    font-size: 0.82rem !important;
    line-height: 1.5 !important;
}
"""

QUICK_PROMPTS = [
    ("💉 Book nurse visit", "I need a nurse to come home for my injection tomorrow at 9am"),
    ("📅 My schedule", "Tell me all my upcoming schedule and reminders"),
    ("💊 Set medication reminder", "Set a daily reminder for my Gonal-F injection at 9pm"),
    ("🏥 Book appointment", "Book a consultation appointment for next week"),
    ("💰 Cost summary", "Show me my IVF cycle cost summary"),
    ("🔬 Research evidence", "Give me research references about IVF success rates"),
]

with gr.Blocks(
    title="IVF Care Platform",
    theme=gr.themes.Soft(
        primary_hue=gr.themes.colors.purple,
        secondary_hue=gr.themes.colors.pink,
        neutral_hue=gr.themes.colors.slate,
    ),
    css=CSS,
) as demo:

    # ── Header ──
    gr.HTML("""
    <div class="header-box">
        <h1>🌸 IVF Care Platform</h1>
        <p>Your compassionate AI companion for the IVF journey — ask questions, book appointments, set reminders, and more.</p>
    </div>
    """)

    with gr.Row(equal_height=True):
        # ── Left sidebar ──
        with gr.Column(scale=1, min_width=220):
            gr.HTML('<div class="sidebar-card">')
            gr.HTML('<p style="color:#4c1d95;font-weight:700;font-size:0.95rem;margin:0 0 10px 0">⚡ Quick Actions</p>')
            quick_btns = []
            for label, _ in QUICK_PROMPTS:
                btn = gr.Button(label, variant="secondary", elem_classes=["quick-btn"])
                quick_btns.append(btn)
            gr.HTML('</div>')

            gr.HTML('<div class="sidebar-card" style="margin-top:12px">')
            gr.HTML('<p style="color:#4c1d95;font-weight:700;font-size:0.95rem;margin:0 0 8px 0">ℹ️ About</p>')
            gr.HTML(
                '<p style="color:#4b5563;font-size:0.82rem;line-height:1.5;margin:0">'
                'This assistant provides <strong>educational information only</strong> '
                'and does not constitute medical advice. Always consult your fertility specialist.'
                '</p>'
            )
            gr.HTML('</div>')

        # ── Main chat area ──
        with gr.Column(scale=3):
            state_display = gr.Textbox(
                label="Session status",
                interactive=False,
                value="✅ Active session",
                elem_classes=["status-box"],
            )
            chatbot = gr.Chatbot(
                label="",
                height=480,
                type="messages",
                value=[],
                avatar_images=(None, "https://em-content.zobj.net/source/google/387/seedling_1f331.png"),
                elem_classes=["chatbot-wrap"],
                show_label=False,
            )
            session_id_state = gr.State("")

            with gr.Row(elem_classes=["input-row"]):
                msg_input = gr.Textbox(
                    placeholder="Ask me anything about IVF, or request an action…",
                    label="",
                    scale=8,
                    show_label=False,
                    lines=1,
                )
                send_btn = gr.Button("Send ➤", scale=1, variant="primary", elem_classes=["send-btn"])

            new_btn = gr.Button("🔄 New conversation", variant="secondary", size="sm")

    # ── Event wiring ──
    send_btn.click(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state],
        outputs=[chatbot, session_id_state, state_display],
    ).then(lambda: "", outputs=msg_input)

    msg_input.submit(
        fn=chat,
        inputs=[msg_input, chatbot, session_id_state],
        outputs=[chatbot, session_id_state, state_display],
    ).then(lambda: "", outputs=msg_input)

    new_btn.click(
        fn=new_session,
        outputs=[chatbot, session_id_state, state_display],
    )

    # Wire quick action buttons
    for btn, (_, prompt) in zip(quick_btns, QUICK_PROMPTS):
        btn.click(
            fn=quick_action,
            inputs=[gr.State(prompt), chatbot, session_id_state],
            outputs=[chatbot, session_id_state, state_display],
        )

    demo.load(fn=new_session, outputs=[chatbot, session_id_state, state_display])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
