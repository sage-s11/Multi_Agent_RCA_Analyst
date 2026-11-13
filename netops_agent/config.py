import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def get_llm(temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.environ["LLM_MODEL"]

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=temperature)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")