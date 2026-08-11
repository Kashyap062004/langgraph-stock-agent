from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from nodes import agent_node, tool_node, should_continue
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.set_entry_point("agent")
 
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END,
    },
)
builder.add_edge("tools", "agent")
 
platform_graph = builder.compile()
 
_DB_PATH = Path(__file__).parent / "checkpoints.db"
_conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
checkpointer = SqliteSaver(_conn)
checkpointer.setup()  
 
graph = builder.compile(checkpointer=checkpointer)