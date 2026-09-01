from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from uuid import UUID

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: UUID
    access_token: str
    is_admin: bool
    users_name: str