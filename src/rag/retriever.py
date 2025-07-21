from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_ollama import ChatOllama
from .vector_store import vectorstore
from .metadata_field_info import document_content_description, metadata_field_info
from core.llms import llm

retriever = SelfQueryRetriever.from_llm(
    llm,
    vectorstore,
    document_content_description,
    metadata_field_info,
    enable_limit=True,
)
