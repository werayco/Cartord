from typing import Literal, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.types import Command
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.schemas import IntentClassification
from app.services.agent_state import AgentState

classifier_llm = ChatGroq(model="openai/gpt-oss-120b",api_key=settings.LLM_API_KEY,temperature=0).with_structured_output(IntentClassification)

INTENT_SYSTEM_PROMPT = (
    "Classify the customer's latest message into exactly one intent. Only fill in "
    "product_query or quantity if the customer stated them explicitly in this message."
)

async def classify_intent(state: AgentState, config: RunnableConfig) -> Command[Literal["collect_order_details", "wallet_balance", "general_agent"]]:
    messages = [SystemMessage(content=INTENT_SYSTEM_PROMPT), *state["messages"]]
    result: IntentClassification = await classifier_llm.ainvoke(messages, config)

    update = {"intent": result.intent}

    if result.intent == "place_order":
        draft = {}
        if result.product_query:
            draft["product_query"] = result.product_query

        if result.quantity:
            draft["quantity"] = result.quantity

        update["order_draft"] = draft
        return Command(goto="collect_order_details", update=update)

    if result.intent == "check_balance":
        return Command(goto="wallet_balance", update=update)

    return Command(goto="general_agent", update=update)