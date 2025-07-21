from .card_data import get_card_data
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


vectorstore = Chroma.from_documents(
    documents=get_card_data(),
    embedding=OllamaEmbeddings(model="dengcao/Qwen3-Embedding-8B:Q5_K_M"),
    persist_directory="chroma_db",
)
