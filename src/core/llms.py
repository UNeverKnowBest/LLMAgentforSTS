from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import os

from src.config import(
    PRIMARY_MODEL_NAME,
    PRIMARY_MODEL_TEMPERATURE,
    PRIMARY_MODEL_TYPE
)

class LLMResponse(BaseModel):
    think: str
    command: str

def get_llm():
    if PRIMARY_MODEL_TYPE == 'local':
        return ChatOllama(
            model=PRIMARY_MODEL_NAME,
            temperature=PRIMARY_MODEL_TEMPERATURE
        )
    elif PRIMARY_MODEL_TYPE == 'gemini':
        return ChatGoogleGenerativeAI(
            model=PRIMARY_MODEL_NAME,
            temperature=PRIMARY_MODEL_TEMPERATURE,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        raise ValueError(f"Unsupported model type: {PRIMARY_MODEL_TYPE}")

def get_structured_llm():
    base_llm = get_llm()
    return base_llm.with_structured_output(LLMResponse)

llm = get_structured_llm()