import os
from typing import List

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("TRAVEL_AGENT_BACKEND_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/api/agent"

st.set_page_config(page_title="Travel Agent", page_icon="🧭", layout="wide")
st.title("🧭 Travel Agent")

with st.sidebar:
    st.header("Session Settings")
    default_lat = st.number_input("Latitude", value=29.37, format="%.6f")
    default_lng = st.number_input("Longitude", value=47.97, format="%.6f")
    enable_debug = st.checkbox("Show debug info", value=False)
    st.markdown("---")
    st.markdown(
        """Backend URL: `%(url)s`

To change it, set the `TRAVEL_AGENT_BACKEND_URL` environment variable or edit `streamlit_app.py`."""
        % {"url": BACKEND_URL}
    )

if "chat_history" not in st.session_state:
    st.session_state.chat_history: List[dict[str, str]] = []

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    """
    Welcome! Ask for places, events, or travel tips. The agent will use the backend
    FastAPI service to fetch real data, enriched with Google Places, Tavily, and
    translation tools.
    """
)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Where should we explore today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "input": prompt,
        "messages": st.session_state.messages[:-1],
        "location": {"lat": default_lat, "lng": default_lng},
        "debug": enable_debug,
    }

    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=90)
        response.raise_for_status()
    except requests.RequestException as exc:
        error_message = f"Failed to contact backend: {exc}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        with st.chat_message("assistant"):
            st.error(error_message)
    else:
        data = response.json()
        assistant_message = data.get("message", {}).get("content", "(No response)")
        debug_payload = data.get("debug")

        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        with st.chat_message("assistant"):
            st.markdown(assistant_message)
            if enable_debug and debug_payload:
                with st.expander("Debug info"):
                    st.json(debug_payload)

st.caption(
    "Powered by Travel Agent backend. Set `TRAVEL_AGENT_BACKEND_URL` to point to the API if it's running elsewhere."
)
