from langchain_ollama import ChatOllama
from pydantic import BaseModel

from src.config import(
    PRIMARY_MODEL_NAME,
    PRIMARY_MODEL_TEMPERATURE,
    PRIMARY_MODEL_TYPE,
)

class LLMResponse(BaseModel):
    think: str
    command: str

def get_llm():
    if PRIMARY_MODEL_TYPE == 'local':
        return ChatOllama(
            model=PRIMARY_MODEL_NAME,
            temperature=PRIMARY_MODEL_TEMPERATURE,
            request_timeout=120.0
        )
    else:
        raise ValueError(f"Unsupported model type: {PRIMARY_MODEL_TYPE}")

def get_structured_llm():
    base_llm = get_llm()
    return base_llm.with_structured_output(LLMResponse)

llm = get_structured_llm()
