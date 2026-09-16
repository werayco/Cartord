from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from app.core.config import settings
from app.services.agent_state import AgentState
from app.services.agent_tools import CUSTOMER_TOOLS

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=settings.LLM_API_KEY,
    temperature=settings.TEMPERATURE,
    streaming=True,
)

llm_customer = llm.bind_tools(CUSTOMER_TOOLS)

CUSTOMER_SYSTEM_PROMPT = (
    "You are Cartord's shopping assistant. Help the customer manage their existing "
    "orders and answer questions using the tools available to you. Never invent order, "
    "product, or account data you have not fetched with a tool. Placing new orders is "
    "handled by a separate flow, not by you."
)


async def Agent(state: AgentState, config: RunnableConfig) -> AgentState:
    messages = [
        SystemMessage(content=CUSTOMER_SYSTEM_PROMPT),
        *state["messages"]]

    response = await llm_customer.ainvoke(messages, config)

    return {"messages": [response]}