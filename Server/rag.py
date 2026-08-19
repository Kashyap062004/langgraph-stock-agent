import uuid
from pathlib import Path
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

PERSIST_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "user_documents"
_EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings: Optional[HuggingFaceEmbeddings] = None
_vectorstore: Optional[Chroma] = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=_EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=_get_embeddings(),
            persist_directory=str(PERSIST_DIR),
        )
    return _vectorstore


def _load_and_split(file_path: str, filename: str) -> list:
    """Loads a PDF or plain-text file and splits it into overlapping chunks.
    150-token overlap keeps a sentence that straddles a chunk boundary from
    losing context in both halves — a standard RAG chunking practice."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(file_path)
    elif suffix in (".txt", ".md"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .pdf, .txt, or .md.")

    raw_docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    return splitter.split_documents(raw_docs)


def ingest_document(
    file_path: str,
    filename: str,
    user_id: str,
    ticker: Optional[str] = None,
) -> dict:
    chunks = _load_and_split(file_path, filename)
    if not chunks:
        raise ValueError("No extractable text found in this file.")

    doc_id = str(uuid.uuid4())
    ticker_normalized = ticker.upper().strip() if ticker else None

    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    for chunk in chunks:
        chunk.metadata.update(
            {
                "doc_id": doc_id,
                "user_id": user_id,
                "filename": filename,
                "ticker": ticker_normalized or "",
            }
        )

    vectorstore = _get_vectorstore()
    vectorstore.add_documents(documents=chunks, ids=ids)

    return {"doc_id": doc_id, "chunk_count": len(chunks)}


def delete_document_chunks(doc_id: str, user_id: str) -> None:
    vectorstore = _get_vectorstore()
    vectorstore._collection.delete(
        where={"$and": [{"doc_id": doc_id}, {"user_id": user_id}]}
    )


def search_documents(
    query: str,
    user_id: str,
    ticker: Optional[str] = None,
    k: int = 4,
) -> str:
    if not user_id:
        return "No user context available for document search."

    where: dict = {"user_id": user_id}
    if ticker:
        where = {"$and": [{"user_id": user_id}, {"ticker": ticker.upper().strip()}]}

    vectorstore = _get_vectorstore()
    results = vectorstore.similarity_search(query, k=k, filter=where)

    if not results:
        scope = f" for ticker {ticker.upper()}" if ticker else ""
        return f"No relevant content found in your uploaded documents{scope}."

    formatted = []
    for i, doc in enumerate(results, start=1):
        source = doc.metadata.get("filename", "unknown document")
        formatted.append(f"[{i}] (source: {source})\n{doc.page_content}")

    return "\n\n".join(formatted)