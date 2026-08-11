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
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id  TEXT PRIMARY KEY,
                user_id    TEXT NOT NULL,
                title      TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                sub        TEXT PRIMARY KEY,
                email      TEXT NOT NULL,
                name       TEXT NOT NULL,
                picture    TEXT,
                first_login TEXT NOT NULL,
                last_login  TEXT NOT NULL
            )
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Users ---------------------------------------------------------------

def upsert_user(sub: str, email: str, name: str, picture: Optional[str]) -> dict:
    """Called on every successful Google login. Creates the user row on
    first login, otherwise just bumps last_login and refreshes profile
    fields (name/picture can change on Google's side over time)."""
    now = _now()
    with _connect() as conn:
        existing = conn.execute("SELECT * FROM users WHERE sub = ?", (sub,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET email=?, name=?, picture=?, last_login=? WHERE sub=?",
                (email, name, picture, now, sub),
            )
        else:
            conn.execute(
                "INSERT INTO users (sub, email, name, picture, first_login, last_login) VALUES (?, ?, ?, ?, ?, ?)",
                (sub, email, name, picture, now, now),
            )
    return {"sub": sub, "email": email, "name": name, "picture": picture}


# --- Conversations (all scoped by user_id) --------------------------------

def create_conversation(thread_id: str, user_id: str, title: str = "New conversation") -> dict:
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO conversations (thread_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (thread_id, user_id, title, now, now),
        )
    return {"thread_id": thread_id, "title": title, "created_at": now, "updated_at": now}


def get_conversation(thread_id: str, user_id: str) -> Optional[dict]:
    """Returns None both when the thread_id doesn't exist AND when it exists
    but belongs to a different user — callers can't distinguish "not found"
    from "not yours" from the return value alone, which is intentional: it
    means api.py always responds 404 rather than leaking "this thread_id
    exists, it's just not yours" to an unauthorized caller."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE thread_id = ? AND user_id = ?",
            (thread_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def list_conversations(user_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def touch_conversation(thread_id: str, user_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE thread_id = ? AND user_id = ?",
            (_now(), thread_id, user_id),
        )


def rename_conversation(thread_id: str, user_id: str, title: str) -> Optional[dict]:
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE thread_id = ? AND user_id = ?",
            (title, _now(), thread_id, user_id),
        )
    return get_conversation(thread_id, user_id)


def delete_conversation(thread_id: str, user_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE thread_id = ? AND user_id = ?",
            (thread_id, user_id),
        )
        return cursor.rowcount > 0


def make_title_from_message(message: str, max_len: int = 48) -> str:
    cleaned = " ".join(message.strip().split())
    if len(cleaned) <= max_len:
        return cleaned or "New conversation"
    truncated = cleaned[:max_len].rsplit(" ", 1)[0]
    return (truncated or cleaned[:max_len]) + "…"