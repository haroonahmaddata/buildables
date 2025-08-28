from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from utils.chat_models import ChatModel
import config
import os

PROMPTS_BASE_DIR = os.path.join(os.path.dirname(__file__), "prompts")
SYSTEM_PROMPT_FILE = "creative_companion.txt"

def load_system_prompt_content(persona_file_name: str) -> str:
    """
    Loads the system prompt content from a specified file in the PROMPTS_BASE_DIR.
    If the file is not found or an error occurs, returns a generic fallback message.
    """
    file_path = os.path.join(PROMPTS_BASE_DIR, persona_file_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading prompt '{persona_file_name}' from {file_path}: {e}. Using a default helpful assistant message.")
        return "You are a helpful assistant."  # Fallback system prompt

try:
    model = ChatModel(config.OPENAI_API_KEY, config.GEMINI_API_KEY)
except AttributeError:
    print("Warning: Could not get API keys.")
    openai_api = os.getenv("OPENAI_API_KEY")
    gemini_api = os.getenv("GEMINI_API_KEY")
    model = ChatModel(openai_api, gemini_api)

chat_history = []

# ✅ FIX 3: Use plain string content for SystemMessage
system_prompt_content = load_system_prompt_content(SYSTEM_PROMPT_FILE)
system_message = SystemMessage(content=system_prompt_content)

chat_history.append(system_message)

print("\n--------------*TERMINAL CHATBOT*--------------\n")
while True:
    try:
        query = input("User: ").strip()
        
        # ✅ FIX 1: Correct exit condition
        if query.lower() in ("exit", "good bye", "goodbye", "quit"):
            for i in chat_history:
                print(f"Chat History: {i}")
            print("Goodbye...")
            break

        chat_history.append(HumanMessage(content=query))
        
        # ✅ FIX 2: Ensure all contents are strings
        formatted_prompt = " ".join(
            str(msg.content) for msg in chat_history
        )

        response = model.openai_chat_models(formatted_prompt)
        
        chat_history.append(AIMessage(content=response))
        print(f"Assistant: {response}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        # Optionally remove the last message if needed
        # chat_history.pop()
