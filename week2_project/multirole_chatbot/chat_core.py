from langchain_core.messages import HumanMessage
import os
# Assume ChatModel and config are imported from utils and config module
# Or passed as arguments

PROMPTS_BASE_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def load_system_prompt_content(persona_file_name: str) -> str:
    # ... (Your existing function remains the same) ...
    file_path = os.path.join(PROMPTS_BASE_DIR, persona_file_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading prompt '{persona_file_name}' from {file_path}: {e}. Using a default helpful assistant message.")
        return "You are a helpful assistant."

def get_ai_response_for_chat(
    current_chat_history: list,
    model_instance, # Your ChatModel instance
    user_query: str
) -> str:
    """
    Processes a single user query and gets an AI response.
    This replaces the core logic inside your old `while True` loop.
    """
    # Create a temporary history including the new user message
    # Streamlit will manage the main chat_history in session_state
    temp_chat_history = list(current_chat_history) # Make a copy to not modify the original
    temp_chat_history.append(HumanMessage(content=user_query))

    # Format the entire chat history into a single string for the model
    formatted_prompt = " ".join(
        str(msg.content) for msg in temp_chat_history
    )

    try:
        # Use the ChatModel instance to get the response
        response = model_instance.openai_chat_models(formatted_prompt) # Or gemini_chat_models
        return response
    except Exception as e:
        return f"An error occurred during AI generation: {e}"

# If you still want a CLI, you could put a small main function here:
if __name__ == "__main__":
    # This part would only run if chat_core.py is executed directly
    # and would use the get_ai_response_for_chat function
    print("This is the core chat logic module. Run streamlit_app.py for the web UI.")