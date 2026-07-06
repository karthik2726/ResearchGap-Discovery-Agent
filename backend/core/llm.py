import os
from langchain_core.language_models import BaseChatModel

def get_llm() -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            temperature=0.2, 
            model_name="llama-3.1-8b-instant", 
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3:8b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.2
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="meta-llama/llama-3.3-70b-instruct:free",
            temperature=0.2,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
