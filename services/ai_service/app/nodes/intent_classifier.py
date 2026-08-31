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
llm_admin = llm.bind_tools(CUSTOMER_TOOLS + ADMIN_TOOLS)

CUSTOMER_SYSTEM_PROMPT = (
    "You are Cartord's shopping assistant. Help the customer place and manage "
    "their own orders using the tools available to you. Never claim to have "
    "admin access, and never invent order, product, or account data you have "
    "not fetched with a tool."
)

ADMIN_SYSTEM_PROMPT = (
    "You are Cartord's assistant for an admin user. Alongside the customer "
    "tools, you may pull store-wide analytics (users, orders, customers, "
    "inventory) with the admin tools available to you. Never invent numbers; "
    "always call the relevant tool."
)

async def Agent(state: AgentState) -> AgentState:
    is_admin = state.get("is_admin", False)
    llm_with_tools = llm_admin if is_admin else llm_customer
    system_prompt = ADMIN_SYSTEM_PROMPT if is_admin else CUSTOMER_SYSTEM_PROMPT

    messages = [SystemMessage(content=system_prompt), *state["messages"]]
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}