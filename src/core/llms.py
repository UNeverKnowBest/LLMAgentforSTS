from langchain_community.chat_models import ChatOllama

from src.config import(
    PRIMARY_MODEL_NAME,
    PRIMARY_MODEL_TEMPERATURE,
    PRIMARY_MODEL_TYPE
)

def get_llm():
    if PRIMARY_MODEL_TYPE == 'local':
        return ChatOllama(
            model=PRIMARY_MODEL_NAME,
            temperature=PRIMARY_MODEL_TEMPERATURE
        )

    else:
        raise ValueError(f"Unsupported model type: {PRIMARY_MODEL_TYPE}")