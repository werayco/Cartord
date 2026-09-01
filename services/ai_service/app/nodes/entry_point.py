## registers the nodes and compiles the graph
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from app.services.agent_state import AgentState
from app.services.agent_checkpointer import get_checkpointer
from app.nodes.intent_classifier import Agent
from app.nodes.tool_node import tool_node

async def node_registry():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("agent", Agent)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END},
    )
    graph_builder.add_edge("tools", "agent")

    checkpointer = await get_checkpointer()
    return graph_builder.compile(checkpointer=checkpointer)