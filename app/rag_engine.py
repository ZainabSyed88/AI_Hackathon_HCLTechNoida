"""
RAG Engine — ChromaDB vector store for Sanket.AI intelligence data.
Handles ingestion of agriculture, disaster, and health data + semantic retrieval.
"""
import chromadb
from chromadb.utils import embedding_functions
from app.config import CHROMA_DB_PATH, EMBEDDING_MODEL, RAG_TOP_K


_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        _collection = _client.get_or_create_collection(
            name="public_intelligence",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def ingest_documents(documents: list[dict]):
    """
    Ingest documents into the vector store.
    Each doc: { "id": str, "text": str, "metadata": dict }
    metadata should include: sector (agriculture/disaster/health), region, date, source
    """
    collection = _get_collection()
    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [doc.get("metadata", {}) for doc in documents]

    collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
    return len(ids)


def query(text: str, top_k: int = RAG_TOP_K, sector: str = None) -> list[dict]:
    """
    Retrieve relevant documents for a query.
    Optionally filter by sector: agriculture, disaster, health
    """
    collection = _get_collection()
    where_filter = {"sector": sector} if sector else None

    results = collection.query(
        query_texts=[text],
        n_results=top_k,
        where=where_filter,
    )

    docs = []
    for i in range(len(results["ids"][0])):
        docs.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "distance": results["distances"][0][i] if results["distances"] else None,
        })
    return docs


def get_context_string(query_text: str, sector: str = None) -> str:
    """
    Get a formatted context string from RAG for injection into LLM prompt.
    """
    docs = query(query_text, sector=sector)
    if not docs:
        return "No relevant data found in the knowledge base."

    context_parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc["metadata"]
        source = meta.get("source", "Unknown")
        region = meta.get("region", "Unknown")
        date = meta.get("date", "Unknown")
        context_parts.append(
            f"[Source {i}] ({source}, {region}, {date}):\n{doc['text']}"
        )
    return "\n\n".join(context_parts)


def get_all_sectors_context(query_text: str) -> dict[str, str]:
    """
    Get context from all sectors for cross-domain analysis.
    """
    sectors = ["agriculture", "disaster", "health", "security"]
    result = {}
    for sector in sectors:
        ctx = get_context_string(query_text, sector=sector)
        result[sector] = ctx
    return result


def get_stats() -> dict:
    """Get collection statistics."""
    collection = _get_collection()
    return {"total_documents": collection.count()}
