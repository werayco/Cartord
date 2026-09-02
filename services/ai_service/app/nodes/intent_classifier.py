from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from app.core.config import settings
from app.services.agent_state import AgentState
from app.services.agent_tools import CUSTOMER_TOOLS, ADMIN_TOOLS

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.LLM_API_KEY,
    temperature=settings.TEMPERATURE,
    streaming=True,
)

llm_customer = llm.bind_tools(CUSTOMER_TOOLS)

CUSTOMER_SYSTEM_PROMPT = (
    "You are Cartord's shopping assistant. Help the customer place and manage "
    "their own orders using the tools available to you. Never claim to have "
    "admin access, and never invent order, product, or account data you have "
    "not fetched with a tool."
)


async def Agent(state: AgentState) -> AgentState:
    messages = [SystemMessage(content=CUSTOMER_SYSTEM_PROMPT), *state["messages"]]
    response = await llm_customer.ainvoke(messages)
    return {"messages": [response]}