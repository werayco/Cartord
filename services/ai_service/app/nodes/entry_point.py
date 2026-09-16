from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from app.services.agent_state import AgentState
from app.services.agent_checkpointer import get_checkpointer
from app.nodes.intent_classifier import classify_intent
from app.nodes.customer_agent import Agent
from app.nodes.order_flow import (collect_order_details, validate_item, check_wallet, confirm_order, place_order_node, wallet_balance_node)
from app.nodes.tool_node import tool_node

async def node_registry():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("classify_intent", classify_intent)
    graph_builder.add_node("collect_order_details", collect_order_details)
    graph_builder.add_node("validate_item", validate_item)
    graph_builder.add_node("check_wallet", check_wallet)
    graph_builder.add_node("confirm_order", confirm_order)
    graph_builder.add_node("place_order", place_order_node)
    graph_builder.add_node("wallet_balance", wallet_balance_node)
    graph_builder.add_node("general_agent", Agent)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_edge(START, "classify_intent")
    graph_builder.add_conditional_edges("general_agent",
        tools_condition,
        {"tools": "tools", END: END},
    )
    graph_builder.add_edge("tools", "general_agent")

    checkpointer = await get_checkpointer()
    return graph_builder.compile(checkpointer=checkpointer)