import openai
import google.generativeai as genai

class ChatModel:
    """A class to encapsulate chat model interactions with different APIs.
    """

    def __init__(self, openai_api: str | None = None, gemini_api: str | None = None) -> None:
        """
        Initialize the chatmodel class with api keys
        """
        self.openai_api = openai_api
        self.gemini_api = gemini_api

        if self.openai_api is None:
            print("Warning: OpenAI API key was not provided.")
        if self.gemini_api is None:
            print("Warning: Gemini API key was not provided.")
    
    def openai_chat_models(self, prompt: str) -> str:
        """Sends a prompt to the OpenAI chat model (GPT-4) and returns the response."""
        if self.openai_api is None:
            return "Error: OpenAI API key was not provided."
        try:
            client = openai.OpenAI(api_key=self.openai_api)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful and concise assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            # Corrected: Check if content is None before calling .strip()
            content = response.choices[0].message.content
            return content.strip() if content is not None else ""
            
        except Exception as e:
            return f"An error occurred with the OpenAI API: {e}"
    
    def gemini_chat_models(self, prompt: str) -> str:
        """sends a prompt to the Gemini chat model and returns the response."""
        
        if self.gemini_api is None:
            return "Error: Gemini API key was not provided."
        try:
            genai.configure(api_key=self.gemini_api)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            # Corrected: Check if response.text is None before calling .strip()
            content = response.text
            return content.strip() if content is not None else ""
            
        except Exception as e:
            return f"An error occurred with the Gemini API: {e}"
