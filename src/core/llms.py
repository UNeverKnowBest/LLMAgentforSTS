from langchain_community.chat_models import ChatOllama

from src.config import(
    PRIMARY_MODEL_NAME,
    PRIMARY_MODEL_TEMPERATURE,
    PRIMARY_MODEL_TYPE
)

local_llm = ChatOllama(
    model=PRIMARY_MODEL_NAME,
    temperature=PRIMARY_MODEL_TEMPERATURE
)

if PRIMARY_MODEL_TYPE == 'local':
    llm = local_llm