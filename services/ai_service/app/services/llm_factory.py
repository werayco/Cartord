from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

_GROQ_MODELS = {
    "customer": "openai/gpt-oss-120b",
    "classifier": "llama-3.3-70b-versatile",
    "slot": "llama-3.3-70b-versatile",
}

_GEMINI_MODELS = {
    "customer": "gemini-3.1-pro-preview",   # stronger reasoning, needed for open-ended tool selection
    "classifier": "gemini-3.1-flash-lite",  # cheap, stable, plenty for simple classification
    "slot": "gemini-3.1-flash-lite",
}

def get_chat_model(role: str, *, temperature: float = 0, streaming: bool = False) -> BaseChatModel:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=_GEMINI_MODELS[role],
            api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )

    if provider == "groq":
        return ChatGroq(
            model=_GROQ_MODELS[role],
            api_key=settings.LLM_API_KEY,
            temperature=temperature,
            streaming=streaming,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")