import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your environment variables file.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your environment variables file.")


class ModelCosts:
    """
    Holds cost constants for different models.
    Cost is per 1M tokens.
    """
    GM_I_COST = 1.25   # Gemini input cost
    GM_O_COST = 10.00  # Gemini output cost
    GPT_I_COST = 1.25  # GPT input cost
    GPT_O_COST = 10.00  # GPT output cost
