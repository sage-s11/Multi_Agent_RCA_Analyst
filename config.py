import os
from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model = os.environ["LLM_MODEL"]

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")