import chromadb
from chromadb.config import Settings
from typing import List, Optional
from app.core.config import get_settings

settings = get_settings()

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False)
)


class VectorStore:
    """ChromaDB-based vector store for code embeddings."""
    
    def __init__(self, collection_name: Optional[str] = None):
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.collection = chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str]
    ) -> None:
        """Add documents to the vector store."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[dict] = None
    ) -> dict:
        """Query the vector store for similar documents."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        chroma_client.delete_collection(self.collection_name)
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()


def get_vector_store(repo_id: Optional[int] = None) -> VectorStore:
    """Get a vector store instance, optionally scoped to a repository."""
    collection_name = f"{settings.CHROMA_COLLECTION_NAME}_repo_{repo_id}" if repo_id else settings.CHROMA_COLLECTION_NAME
    return VectorStore(collection_name)
