from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid
import shutil
import tempfile
from pathlib import Path

load_dotenv()  

from graph import graph  # noqa: E402
import conversations as conv_store  # noqa: E402
import documents as doc_store  # noqa: E402
import watchlist as watchlist_store  # noqa: E402
import rag  # noqa: E402
from auth import (  # noqa: E402
    get_current_user,
    verify_google_credential,
    create_session_token,
)

app = FastAPI(title="Stock Market Expert Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    conv_store.init_db()
    doc_store.init_db()
    watchlist_store.init_db()




class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


class ConversationOut(BaseModel):
    thread_id: str
    title: str
    created_at: str
    updated_at: str


class RenameRequest(BaseModel):
    title: str


class MessageOut(BaseModel):
    role: str
    content: str


class MessagesResponse(BaseModel):
    thread_id: str
    messages: list[MessageOut]


class GoogleLoginRequest(BaseModel):
    credential: str  


class UserOut(BaseModel):
    sub: str
    email: str
    name: str
    picture: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    user: UserOut


class DocumentOut(BaseModel):
    doc_id: str
    filename: str
    ticker: Optional[str] = None
    chunk_count: int
    uploaded_at: str


class WatchlistOut(BaseModel):
    tickers: list[str]


class AddTickerRequest(BaseModel):
    ticker: str




def _reconstruct_visible_messages(raw_messages) -> list[MessageOut]:
    visible = []
    for m in raw_messages:
        if isinstance(m, HumanMessage):
            visible.append(MessageOut(role="user", content=m.content))
        elif isinstance(m, AIMessage) and m.content:
            visible.append(MessageOut(role="assistant", content=m.content))
        elif isinstance(m, ToolMessage):
            continue
    return visible




@app.post("/auth/google", response_model=TokenResponse)
def login_with_google(req: GoogleLoginRequest):
    profile = verify_google_credential(req.credential)
    conv_store.upsert_user(profile.sub, profile.email, profile.name, profile.picture)
    token = create_session_token(profile)
    return TokenResponse(
        access_token=token,
        user=UserOut(sub=profile.sub, email=profile.email, name=profile.name, picture=profile.picture),
    )


@app.get("/auth/me", response_model=UserOut)
def get_me(user: dict = Depends(get_current_user)):
    return UserOut(sub=user["sub"], email=user["email"], name=user["name"], picture=user.get("picture"))



@app.post("/conversations", response_model=ConversationOut)
def create_conversation(user: dict = Depends(get_current_user)):
    thread_id = str(uuid.uuid4())
    record = conv_store.create_conversation(thread_id, user["sub"])
    return ConversationOut(**record)


@app.get("/conversations", response_model=list[ConversationOut])
def get_conversations(user: dict = Depends(get_current_user)):
    return [ConversationOut(**c) for c in conv_store.list_conversations(user["sub"])]


@app.get("/conversations/{thread_id}/messages", response_model=MessagesResponse)
def get_conversation_messages(thread_id: str, user: dict = Depends(get_current_user)):
    if conv_store.get_conversation(thread_id, user["sub"]) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    raw_messages = state.values.get("messages", []) if state.values else []
    return MessagesResponse(
        thread_id=thread_id,
        messages=_reconstruct_visible_messages(raw_messages),
    )


@app.patch("/conversations/{thread_id}", response_model=ConversationOut)
def rename_conversation(thread_id: str, req: RenameRequest, user: dict = Depends(get_current_user)):
    if conv_store.get_conversation(thread_id, user["sub"]) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    title = req.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title cannot be empty")
    record = conv_store.rename_conversation(thread_id, user["sub"], title)
    return ConversationOut(**record)


@app.delete("/conversations/{thread_id}")
def delete_conversation(thread_id: str, user: dict = Depends(get_current_user)):
    deleted = conv_store.delete_conversation(thread_id, user["sub"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"thread_id": thread_id, "deleted": True}




ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_DOCUMENT_SIZE_BYTES = 20 * 1024 * 1024  # 20MB


@app.post("/documents/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    ticker: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))}",
        )

    # Stream to a temp file rather than reading the whole upload into memory
    # at once — matters once you're accepting 20MB PDFs from multiple users.
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        size = 0
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_DOCUMENT_SIZE_BYTES:
                tmp.close()
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="File exceeds 20MB limit")
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        result = rag.ingest_document(
            file_path=tmp_path,
            filename=file.filename or "document",
            user_id=user["sub"],
            ticker=ticker,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    record = doc_store.record_document(
        doc_id=result["doc_id"],
        user_id=user["sub"],
        filename=file.filename or "document",
        ticker=ticker.upper().strip() if ticker else None,
        chunk_count=result["chunk_count"],
    )
    return DocumentOut(**record)


@app.get("/documents", response_model=list[DocumentOut])
def list_documents(user: dict = Depends(get_current_user)):
    return [DocumentOut(**d) for d in doc_store.list_documents(user["sub"])]


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    if doc_store.get_document(doc_id, user["sub"]) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    rag.delete_document_chunks(doc_id, user["sub"])
    doc_store.delete_document_record(doc_id, user["sub"])
    return {"doc_id": doc_id, "deleted": True}


# --- Watchlist endpoints -----------------------------------------------

@app.get("/watchlist", response_model=WatchlistOut)
def get_watchlist(user: dict = Depends(get_current_user)):
    return WatchlistOut(tickers=watchlist_store.list_tickers(user["sub"]))


@app.post("/watchlist", response_model=WatchlistOut)
def add_to_watchlist(req: AddTickerRequest, user: dict = Depends(get_current_user)):
    if not req.ticker.strip():
        raise HTTPException(status_code=400, detail="ticker cannot be empty")
    watchlist_store.add_ticker(user["sub"], req.ticker)
    return WatchlistOut(tickers=watchlist_store.list_tickers(user["sub"]))


@app.delete("/watchlist/{ticker}", response_model=WatchlistOut)
def remove_from_watchlist(ticker: str, user: dict = Depends(get_current_user)):
    watchlist_store.remove_ticker(user["sub"], ticker)
    return WatchlistOut(tickers=watchlist_store.list_tickers(user["sub"]))


# --- Chat endpoint (also scoped to the authenticated user) -----------------

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    thread_id = req.thread_id
    owns_existing_thread = thread_id is not None and conv_store.get_conversation(thread_id, user["sub"]) is not None

    if thread_id and not owns_existing_thread:
        raise HTTPException(status_code=403, detail="You do not have access to this conversation")

    is_new_conversation = thread_id is None
    if is_new_conversation:
        thread_id = str(uuid.uuid4())
        title = conv_store.make_title_from_message(req.message)
        conv_store.create_conversation(thread_id, user["sub"], title=title)

    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=req.message)], "user_id": user["sub"]},
            config=config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    conv_store.touch_conversation(thread_id, user["sub"])

    final_message = result["messages"][-1]
    return ChatResponse(reply=final_message.content, thread_id=thread_id)


@app.get("/health")
def health():
    return {"status": "ok"}