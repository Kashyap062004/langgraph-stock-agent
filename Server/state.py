from typing import TypedDict, Annotated, Optional, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):

    messages: Annotated[List[BaseMessage], add_messages]

    ticker_symbol: Optional[str]

    tool_results: Optional[dict]
    
    next_step: Optional[str]