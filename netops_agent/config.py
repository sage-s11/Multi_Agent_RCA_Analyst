import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RUNBOOKS_DIR = BASE_DIR / "runbooks"

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