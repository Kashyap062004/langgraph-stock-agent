from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

load_dotenv()  # must run before auth.py reads GOOGLE_CLIENT_ID/JWT_SECRET
                # and before `from graph import graph` constructs the LLM client

from graph import graph  # noqa: E402
import conversations as conv_store  # noqa: E402
import Reports  # noqa: E402
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


# --- Schemas -----------------------------------------------------------

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
    credential: str  # the raw Google ID token from the frontend button


class UserOut(BaseModel):
    sub: str
    email: str
    name: str
    picture: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    user: UserOut


class ReportRequest(BaseModel):
    content: str   # the assistant message's raw markdown content
    title: str = "Stock Report"


class ReportRequest(BaseModel):
    content: str   # the assistant message's raw markdown content
    title: str = "Stock Report"
# --- Helpers -----------------------------------------------------------

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


def _safe_filename(title: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip()
    return cleaned or "report"


# --- Auth endpoints --------------------------------------------------------

@app.post("/auth/google", response_model=TokenResponse)
def login_with_google(req: GoogleLoginRequest):
    """
    Called once, right after Google's button hands the frontend a signed ID
    token. We verify that token against Google, upsert a local user record
    (so /conversations queries have a stable owner id to filter by), and
    hand back OUR OWN session token — see auth.py's module docstring for why
    this is a different token from the one Google issued.
    """
    profile = verify_google_credential(req.credential)
    conv_store.upsert_user(profile.sub, profile.email, profile.name, profile.picture)
    token = create_session_token(profile)
    return TokenResponse(
        access_token=token,
        user=UserOut(sub=profile.sub, email=profile.email, name=profile.name, picture=profile.picture),
    )


@app.get("/auth/me", response_model=UserOut)
def get_me(user: dict = Depends(get_current_user)):
    """Lets the frontend validate a stored session token on page load
    without re-running the whole Google login flow."""
    return UserOut(sub=user["sub"], email=user["email"], name=user["name"], picture=user.get("picture"))


# --- Conversation registry endpoints (all scoped to the authenticated user) -

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


# --- Report endpoints (PDF download / email) -------------------------------

@app.post("/reports/pdf")
def download_report_pdf(req: ReportRequest, user: dict = Depends(get_current_user)):
    """
    Renders the given markdown content as a PDF and returns it directly as
    the response body with a Content-Disposition header — that header is
    what makes the browser trigger a native "Save As" download instead of
    just showing raw bytes (see frontend's downloadReportPdf()).
    """
    try:
        pdf_bytes = Reports.markdown_to_pdf(req.content, title=req.title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")

    filename = _safe_filename(req.title)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )


@app.post("/reports/email")
def email_report(req: ReportRequest, user: dict = Depends(get_current_user)):
    """
    Same PDF as above, emailed to the AUTHENTICATED USER'S OWN address
    (user["email"], from their verified Google profile) — never an address
    supplied in the request body. Letting the request specify an arbitrary
    recipient would turn this into an open mail relay anyone with a valid
    session could point at any address — a real abuse vector worth avoiding.
    """
    try:
        pdf_bytes = Reports.markdown_to_pdf(req.content, title=req.title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")

    filename = _safe_filename(req.title)
    try:
        Reports.send_report_email(
            to_email=user["email"],
            subject=req.title,
            pdf_bytes=pdf_bytes,
            pdf_filename=f"{filename}.pdf",
        )
    except RuntimeError as e:
        # SMTP not configured — a setup problem, not a user error
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    return {"sent": True, "to": user["email"]}


# --- Chat endpoint (also scoped to the authenticated user) -----------------

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    thread_id = req.thread_id
    owns_existing_thread = thread_id is not None and conv_store.get_conversation(thread_id, user["sub"]) is not None

    if thread_id and not owns_existing_thread:
        # Either a brand-new client-generated id, or someone else's
        # thread_id — either way, we do not silently write into a thread
        # this user doesn't own. Reject explicitly rather than guessing.
        raise HTTPException(status_code=403, detail="You do not have access to this conversation")

    is_new_conversation = thread_id is None
    if is_new_conversation:
        thread_id = str(uuid.uuid4())
        title = conv_store.make_title_from_message(req.message)
        conv_store.create_conversation(thread_id, user["sub"], title=title)

    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = graph.invoke(
            {"messages": [HumanMessage(content=req.message)]},
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

# Run with: uvicorn api:app --reload --port 8000