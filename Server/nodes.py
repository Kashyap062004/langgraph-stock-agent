from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from state import AgentState
from llm import llm_with_tools, SYSTEM_PROMPT
from tools import TOOLS
from Formatting import normalize_markdown_tables

#  name/tool->function mapping 

TOOLS_BY_NAME = {t.name: t for t in TOOLS}


def agent_node(state: AgentState) -> dict:
    """
    The "router/brain" node. Sends the full conversation (with a system prompt
    prepended) to the tool-bound LLM and gets back either:
      (a) a plain-text AIMessage (final answer), or
      (b) an AIMessage with a populated `tool_calls` field (wants to use a tool).

    This single node handles BOTH "just chat" and "needs data" cases — the
    routing decision (chat vs tool) is made by the LLM itself via tool_calls,
    not by a separate hand-written classifier. That's the LangGraph idiom:
    let the model decide, then branch on what it decided (Step 6).
    """
    messages = state["messages"]
    # Prepend the system prompt fresh each call rather than storing it in state,
    # so it's never accidentally duplicated as conversation history grows.
    full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(full_messages)
    if isinstance(response, AIMessage):
        response.content = normalize_markdown_tables(response.content)
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    tool_messages = []
    tool_results = dict(state.get("tool_results") or {})

    for call in last_message.tool_calls:
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