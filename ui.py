"""Gradio chat UI for the IVF Treatment Advisor Agent."""

from __future__ import annotations

import os

import gradio as gr  # type: ignore

from ivf_advisor.models import ConversationState

_orchestrator = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from ivf_advisor.agent import create_agent
        from ivf_advisor.orchestrator import ConversationOrchestrator
        _orchestrator = ConversationOrchestrator(agent=create_agent())
    return _orchestrator


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


def _state_badge(state: ConversationState) -> str:
    labels = {
        ConversationState.DISCLAIMER_PENDING: "⚠️ Disclaimer pending",
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

    # Ensure we have a valid session
    if not session_id:
        session = orch.create_session()
        session_id = session.session_id
        disclaimer = orch.turn(session_id, "")
        history = [_msg("assistant", disclaimer)]

    response = orch.turn(session_id, user_message)

    # Always build a fresh clean list to avoid any format contamination
    new_history = list(history) + [
        _msg("user", user_message),
        _msg("assistant", response),
    ]

    session = orch.get_session(session_id)
    state_label = _state_badge(session.state) if session else ""
    return new_history, session_id, state_label


with gr.Blocks(title="IVF Treatment Advisor") as demo:
    gr.Markdown("# IVF Treatment Advisor\nAn informational companion for your IVF journey.")

    state_display = gr.Textbox(
        label="Session status", interactive=False, value="⚠️ Disclaimer pending"
    )
    chatbot = gr.Chatbot(
        label="Conversation",
        height=500,
        type="messages",
        value=[],
    )
    session_id_state = gr.State("")

    with gr.Row():
        msg_input = gr.Textbox(
            placeholder="Type your message here…",
            label="Your message",
            scale=8,
        )
        send_btn = gr.Button("Send", scale=1, variant="primary")

    new_btn = gr.Button("New session", variant="secondary")

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

    demo.load(fn=new_session, outputs=[chatbot, session_id_state, state_display])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
