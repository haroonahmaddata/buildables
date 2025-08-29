import streamlit as st
import os
import sys
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# --- Imports from your project ---
# Import ChatModel from utils.chat_models
from utils.chat_models import ChatModel
# Import core chat functions from utils.chat_core
from chat_core import load_system_prompt_content, get_ai_response_for_chat
import config # Your config.py

# --- Configuration & Path Setup ---
# PROMPTS_BASE_DIR for loading persona files
_PROMPTS_ABS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

# Ensure the prompts directory exists for user feedback
if not os.path.exists(_PROMPTS_ABS_DIR):
    os.makedirs(_PROMPTS_ABS_DIR)
    st.warning(f"Created missing prompts directory: {_PROMPTS_ABS_DIR}")

# --- Helper Functions ---
def get_available_personas() -> list[str]:
    """
    Scans the PROMPTS_BASE_DIR for .txt files and returns their base names (display format).
    """
    if not os.path.exists(_PROMPTS_ABS_DIR):
        return []
    
    persona_files = [f for f in os.listdir(_PROMPTS_ABS_DIR) if f.endswith(".txt")]
    return [os.path.splitext(f)[0].replace('_', ' ').title() for f in persona_files]

def export_chat_history_as_text():
    """Formats the chat history into a downloadable text string."""
    export_string = ""
    for message in st.session_state.chat_history:
        if isinstance(message, SystemMessage):
            export_string += f"SYSTEM: {message.content}\n\n"
        elif isinstance(message, HumanMessage):
            export_string += f"USER: {message.content}\n\n"
        elif isinstance(message, AIMessage):
            export_string += f"ASSISTANT: {message.content}\n\n"
    return export_string

# --- Streamlit App Setup ---
st.set_page_config(page_title="🦜MittuChat", layout="centered")
st.title(" 🦜MittuChat Multirole AI Chatbot")
st.markdown("### AI interactions with customizable personas and models.")
st.markdown("---")

# --- Initialize Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "system_prompt_content" not in st.session_state:
    st.session_state.system_prompt_content = "" # Will be set by selector
if "selected_llm" not in st.session_state:
    st.session_state.selected_llm = "OpenAI" # Default LLM

# Initialize ChatModel only once and store in session state
if "model" not in st.session_state:
    try:
        st.session_state.model = ChatModel(config.OPENAI_API_KEY, config.GEMINI_API_KEY)
    except AttributeError:
        st.warning("Could not get API keys from config.py. Falling back to environment variables.")
        openai_api = os.getenv("OPENAI_API_KEY")
        gemini_api = os.getenv("GEMINI_API_KEY")
        st.session_state.model = ChatModel(openai_api, gemini_api)
    
    # Check if any API keys are available
    if st.session_state.model.openai_api is None and st.session_state.model.gemini_api is None:
        st.error("No API keys found for OpenAI or Gemini. Please set them in config.py or environment variables.")
        st.stop()


# --- Sidebar for Chat Settings ---
st.sidebar.header("Chat Settings")

# 1. LLM Selector
selected_llm_option = st.sidebar.selectbox(
    "Choose AI Model:",
    options=["OpenAI", "Gemini"],
    index=0 if st.session_state.selected_llm == "OpenAI" else 1, # Set initial index based on session state
    key="llm_selector"
)
# Update session state if LLM selection changes
if selected_llm_option != st.session_state.selected_llm:
    st.session_state.selected_llm = selected_llm_option
    st.session_state.chat_history = [] # Clear history on LLM change
    # Force rerun to re-initialize system message with potentially new LLM context
    st.experimental_rerun() 

st.sidebar.markdown("---")

# 2. Persona Selector
available_personas = get_available_personas()
default_persona_index = available_personas.index("Professional Assistant") if "Professional Assistant" in available_personas else (0 if available_personas else -1)

if default_persona_index == -1:
    st.sidebar.warning("No persona prompt files found in the 'prompts' directory. Using default assistant.")
    selected_persona_display_name = "Default Assistant"
else:
    selected_persona_display_name = st.sidebar.selectbox(
        "Choose AI Persona:", 
        options=available_personas, 
        index=default_persona_index,
        key="persona_selector"
    )

# Convert display name back to file name format
selected_persona_file_name = selected_persona_display_name.lower().replace(' ', '_') + ".txt" if selected_persona_display_name != "Default Assistant" else ""

# Load the system prompt based on selection
new_system_prompt_content = load_system_prompt_content(selected_persona_file_name) if selected_persona_file_name else "You are a helpful assistant."

# Reset chat history if persona changes
if st.session_state.system_prompt_content != new_system_prompt_content:
    st.session_state.system_prompt_content = new_system_prompt_content
    st.session_state.chat_history = [] # Clear history on persona change
    st.experimental_rerun() # Rerun to apply new system message and clear history

# Add system message to history if it's empty or needs updating (e.g., first load or after clear)
if not st.session_state.chat_history or not isinstance(st.session_state.chat_history[0], SystemMessage) or st.session_state.chat_history[0].content != st.session_state.system_prompt_content:
    # Ensure system message is always the first in history and reflects current persona
    st.session_state.chat_history = [SystemMessage(content=st.session_state.system_prompt_content)] + \
                                      [msg for msg in st.session_state.chat_history if not isinstance(msg, SystemMessage)]


st.sidebar.markdown("---")
if st.sidebar.button("Clear Chat History", key="clear_chat_button"):
    st.session_state.chat_history = [SystemMessage(content=st.session_state.system_prompt_content)] # Only keep the system message
    st.experimental_rerun()

st.sidebar.download_button(
    label="Export Chat (.txt)",
    data=export_chat_history_as_text(),
    file_name="chat_history.txt",
    mime="text/plain",
    key="export_chat_button"
)
st.sidebar.markdown("---")
st.sidebar.info("Select your preferences and start chatting!")


# --- Display Chat Messages ---
# Display only Human and AI messages for a cleaner UI
for message in st.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.write(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.write(message.content)


# --- Chat Input & AI Response Generation ---
if user_query := st.chat_input("Type your message here...", key="chat_input"):
    # Append user message to history
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    # Display user message immediately
    with st.chat_message("user"):
        st.write(user_query)

    with st.spinner(f"Thinking with {st.session_state.selected_llm} as {selected_persona_display_name}..."):
        try:
            # Prepare prompt for the model (including the current system message)
            # Ensure all contents are strings for the model
            formatted_prompt = " ".join(
                str(msg.content) for msg in st.session_state.chat_history
            )
            
            # --- CONDITIONAL MODEL CALLING ---
            if st.session_state.selected_llm == "OpenAI":
                if st.session_state.model.openai_api is None:
                    ai_response_text = "Error: OpenAI API key is not set. Please check your config.py or environment variables."
                else:
                    ai_response_text = st.session_state.model.openai_chat_models(formatted_prompt)
            elif st.session_state.selected_llm == "Gemini":
                if st.session_state.model.gemini_api is None:
                    ai_response_text = "Error: Gemini API key is not set. Please check your config.py or environment variables."
                else:
                    ai_response_text = st.session_state.model.gemini_chat_models(formatted_prompt)
            else:
                ai_response_text = "Error: Unknown LLM selected."
            
            st.session_state.chat_history.append(AIMessage(content=ai_response_text))
            with st.chat_message("assistant"):
                st.write(ai_response_text)
        except Exception as e:
            st.error(f"Error from AI model: {e}")
            # Optionally remove the last message if needed
            if len(st.session_state.chat_history) > 1: # Don't remove system message
                st.session_state.chat_history.pop()

