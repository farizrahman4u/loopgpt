from streamlit_chat import message
from loopgpt.agent import Agent
from loopgpt.constants import PROCEED_INPUT
import streamlit as st

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent()

if "history" not in st.session_state:
    st.session_state["history"] = []

if "last_user_input" not in st.session_state:
    st.session_state["last_user_input"] = ""

if "last_response" not in st.session_state:
    st.session_state["last_response"] = ""

if "wait_for_yn" not in st.session_state:
    st.session_state["wait_for_yn"] = False


def process_response(resp, voice_only=True):
    if resp:
        msgs = []
        if isinstance(resp, str):
            msgs.append(resp)
        else:
            if "thoughts" in resp:
                thoughts = resp["thoughts"]
                if not voice_only:
                    if "text" in thoughts:
                        msgs.append(thoughts["text"])
                    if "reasoning" in thoughts:
                        msgs.append(f"Reasoning: {thoughts['reasoning']}")
                    if "plan" in thoughts:
                        msgs += thoughts["plan"].split("\n")
                    if "criticism" in thoughts:
                        msgs.append(f"Criticism: {thoughts['criticism']}")
                if "speak" in thoughts:
                    if voice_only:
                        msgs.append(f"{thoughts['speak']}")
                    else:
                        msgs.append(f"(voice) {thoughts['speak']}")
            if "command" in resp and resp["command"]:
                msgs.append(
                    f"Agent wants to execute the following command :\n{resp['command']}. Type 'y' to execute or 'n' to cancel."
                )
                st.session_state.wait_for_yn = True
        for msg in msgs:
            st.session_state.history.append(("loopGPT", msg))
        return msgs


def submit():
    inp = st.session_state.input
    agent = st.session_state.agent
    resp = ""
    if inp:
        if st.session_state.wait_for_yn:
            yn = inp.lower().strip()
            if yn in ("y", "n"):
                st.session_state.history.append(("user", yn))
                st.session_state.wait_for_yn = False
                if yn == "y":
                    resp = agent.chat(PROCEED_INPUT, True)
                elif yn == "n":
                    feedback = "Enter feedback (Why not execute the command?): "
                    st.session_state.history.append(("loopGPT", feedback))
        else:
            resp = agent.chat(inp, run_tool=False)
            st.session_state.history.append(("user", inp))

        st.session_state.last_user_input = inp
        st.session_state.input = ""
        process_response(resp)


if __name__ == "__main__":
    st.title("LoopGPT")

    if st.session_state.history:
        for i, msg in enumerate(st.session_state.history):
            message(msg[1], is_user=msg[0] == "user", key=str(i))

    st.text_input("Chat with LoopGPT", key="input", on_change=submit)
