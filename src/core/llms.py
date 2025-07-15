from langchain_community.chat_models import ChatOllama
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser

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
    else:
        raise ValueError(f"Unsupported model type: {PRIMARY_MODEL_TYPE}")

def get_structured_llm():
    base_llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=LLMResponse)
    return base_llm, parser

llm, output_parser = get_structured_llm()