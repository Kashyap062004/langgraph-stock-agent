from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from state import AgentState
from llm import llm_with_tools, SYSTEM_PROMPT
from tools import TOOLS
import rag
import watchlist as watchlist_store
import yfinance as yf


TOOLS_BY_NAME = {t.name: t for t in TOOLS}

USER_SCOPED_TOOLS = {"search_uploaded_documents", "get_my_watchlist_prices"}


def agent_node(state: AgentState) -> dict:
    """
    The "router/brain" node. Sends the full conversation (with a system prompt
    prepended) to the tool-bound LLM and gets back either:
      (a) a plain-text AIMessage (final answer), or
      (b) an AIMessage with a populated `tool_calls` field (wants to use a tool).
    """
    messages = state["messages"]
    full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # WORKAROUND for a known Groq/llama-3.3-70b-versatile issue: the model
    # occasionally emits its own "<function=name{...}></function>" text
    # instead of a properly structured tool call, which Groq's API rejects
    # with a 400 "tool_use_failed" error rather than passing through
    # gracefully. This is a well-documented, non-deterministic model-level
    # quirk (confirmed across many unrelated projects using this same
    # model+provider combo) — not something fixable in our prompt or code.
    # It usually succeeds on a second attempt, so we retry once before
    # giving up and returning a clean error message instead of letting the
    # raw Groq error surface all the way to the user.
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = llm_with_tools.invoke(full_messages)
            return {"messages": [response]}
        except Exception as e:
            last_error = e
            if "tool_use_failed" not in str(e) and "Failed to call a function" not in str(e):
                raise  # a different kind of error — don't swallow it, let it surface normally

    fallback = AIMessage(
        content=(
            "I had trouble formatting that request internally — could you "
            "try rephrasing your question, or ask again in a moment?"
        )
    )
    return {"messages": [fallback]}


def _run_user_scoped_tool(tool_name: str, args: dict, user_id: str | None) -> str:
    if not user_id:
        return "You must be signed in to use this feature."

    if tool_name == "search_uploaded_documents":
        query = args.get("query", "")
        ticker = args.get("ticker") or None
        return rag.search_documents(query=query, user_id=user_id, ticker=ticker)

    if tool_name == "get_my_watchlist_prices":
        tickers = watchlist_store.list_tickers(user_id)
        if not tickers:
            return "The user's watchlist is empty."
        lines = []
        for t in tickers:
            try:
                fast = yf.Ticker(t).fast_info
                price = getattr(fast, "last_price", None)
                lines.append(f"{t}: ${price:.2f}" if price is not None else f"{t}: price unavailable")
            except Exception as e:
                lines.append(f"{t}: error fetching price ({e})")
        return "Watchlist:\n" + "\n".join(lines)

    return f"Error: '{tool_name}' is not a recognized user-scoped tool."


def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    tool_messages = []
    tool_results = dict(state.get("tool_results") or {})
    user_id = state.get("user_id")

    for call in last_message.tool_calls:
        if call["name"] in USER_SCOPED_TOOLS:
            try:
                result = _run_user_scoped_tool(call["name"], call["args"], user_id)
            except Exception as e:
                result = f"Error executing tool '{call['name']}': {str(e)}"
        else:
            tool_fn = TOOLS_BY_NAME.get(call["name"])
            if tool_fn is None:
                result = f"Error: unknown tool '{call['name']}' requested."
            else:
                try:
                    result = tool_fn.invoke(call["args"])
                except Exception as e:
                    result = f"Error executing tool '{call['name']}': {str(e)}"

        tool_results[call["name"]] = result
        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=call["id"])
        )

    return {"messages": tool_messages, "tool_results": tool_results}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
        return "tools"
    return "end"