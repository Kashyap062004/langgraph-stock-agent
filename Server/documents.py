import sqlite3
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

DB_PATH = Path(__file__).parent / "conversations.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id      TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                filename    TEXT NOT NULL,
                ticker      TEXT,
                chunk_count INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id)"
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_document(
    doc_id: str, user_id: str, filename: str, ticker: Optional[str], chunk_count: int
) -> dict:
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO documents (doc_id, user_id, filename, ticker, chunk_count, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, user_id, filename, ticker, chunk_count, now),
        )
    return {
        "doc_id": doc_id,
        "filename": filename,
        "ticker": ticker,
        "chunk_count": chunk_count,
        "uploaded_at": now,
    }


def list_documents(user_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_document(doc_id: str, user_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE doc_id = ? AND user_id = ?",
            (doc_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def delete_document_record(doc_id: str, user_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE doc_id = ? AND user_id = ?",
            (doc_id, user_id),
        )
        return cursor.rowcount > 0