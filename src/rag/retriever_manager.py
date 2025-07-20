from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_ollama import ChatOllama
from .vector_store import VectorStoreManager
from .metadata_field_info import document_content_description, metadata_field_info


class RetrieverManager:
    def __init__(self, llm_model="qwen3:8b", temperature=0.5, request_timeout=120.0):
        self.llm = ChatOllama(
            model=llm_model, temperature=temperature, request_timeout=request_timeout
        )
        self.vector_store_manager = VectorStoreManager()
        self.retriever = None

    def create_retriever(self):
        vectorstore = self.vector_store_manager.get_vectorstore()
        self.retriever = SelfQueryRetriever.from_llm(
            self.llm,
            vectorstore,
            document_content_description,
            metadata_field_info,
            enable_limit=True,
        )
        return self.retriever

    def get_retriever(self):
        if self.retriever is None:
            self.retriever = self.create_retriever()
        return self.retriever

    def query(self, query_text):
        retriever = self.get_retriever()
        return retriever.invoke(query_text)
