import os
import time
import openai
import google.generativeai as genai
from google.api_core import exceptions
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

class Summarizer:
    def __init__(self, model_name: str):
        """
        Initialize summarizer with a provider.
        Supported providers: "gemini-2.5-pro", "gpt-5"
        """
        self.model_name = model_name
        if "gpt" in model_name.lower():
            self.openai_client = OpenAI()  # initialize OpenAI client only if needed
        elif "gemini" in model_name.lower():
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    def summarize(self, text: str) -> str:
        """
        Generates a concise summary of the provided text
        using the selected LLM provider.
        """
        time.sleep(1)  # simple rate limiting

        if self.model_name == "gemini-2.5-pro":
            return self._summarize_with_gemini(text)
        elif self.model_name == "gpt-5":
            return self._summarize_with_openai(text)
        else:
            raise ValueError("Invalid provider. Use 'gemini-2.5-pro' or 'gpt-5'.")

    def _summarize_with_gemini(self, text: str) -> str:
        try:
            model = genai.GenerativeModel(self.model_name)
            prompt = f"Summarize the following text concisely:\n\n{text}"
            response = model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted:
            return "Error: API rate limit exceeded. Please try again later."
        except exceptions.GoogleAPIError as e:
            return f"Error: Google API error occurred. Details: {e}"
        except Exception as e:
            return f"Error: An unexpected error occurred. Details: {e}"

    def _summarize_with_openai(self, text: str) -> str:
        try:
            prompt_messages = [
                {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
                {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
            ]
            completion = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=prompt_messages
            )
            return completion.choices[0].message.content
        except OpenAIError as e:
            return f"Error: OpenAI API error. Details: {e}"
        except Exception as e:
            return f"Error: An unexpected error occurred with OpenAI. Details: {e}"
