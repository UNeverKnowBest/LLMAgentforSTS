from langchain_core.tools import tool
from rag.retriever import retriever
from typing import List, Dict, Optional
from src.rag.card_data import get_card_data


@tool
def lookup_card_info(query: str) -> str:
    docs = retriever.get_relevant_documents(query)
    return "\n".join([f"{doc.metadata['name']}: {doc.page_content}" for doc in docs])
