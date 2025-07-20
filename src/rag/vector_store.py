from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from .card_data import get_card_data


class VectorStoreManager:
    def __init__(
        self, model_name="dengcao/Qwen3-Embedding-8B:Q5_K_M", persist_directory="./db/"
    ):
        self.model_name = model_name
        self.persist_directory = persist_directory
        self.embeddings = OllamaEmbeddings(model=model_name)
        self.vectorstore = None

    def create_vectorstore(self):
        card_data = get_card_data()
        self.vectorstore = Chroma.from_documents(
            card_data, self.embeddings, persist_directory=self.persist_directory
        )
        return self.vectorstore

    def load_vectorstore(self):
        if self.vectorstore is None:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
        return self.vectorstore

    def get_vectorstore(self):
        if self.vectorstore is None:
            try:
                return self.load_vectorstore()
            except:
                return self.create_vectorstore()
        return self.vectorstore
