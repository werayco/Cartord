import asyncio
from uuid import UUID
from langchain_core.messages import HumanMessage
from app.nodes.entry_point import node_registry

async def main():
    print("Building graph...", flush=True)
    graph = await node_registry()

    inputs = {
        "messages": [HumanMessage(content="how are you")],
        "user_id": UUID("01a09686-1198-72d2-a215-b1cfa244a4e5"),
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMWEwOTY4Ni0xMTk4LTcyZDItYTIxNS1iMWNmYTI0NGE0ZTUiLCJlbWFpbCI6ImJ1eWVyLnRlc3RAZXhhbXBsZS5jb20iLCJyb2xlIjoiYnV5ZXIiLCJpYXQiOjE3ODkzMjE1ODIsImV4cCI6MTc4OTMzMzU4MiwidHlwZSI6ImFjY2VzcyJ9.N_WdErQXq9IZaIoOj2i25Y-DrPVvd9chgfGRCsnJS1A",
        "users_name": "test_buyer_001",
    }

    config = {
        "configurable": {
            "thread_id": "67a0e31e-f29f-4a22-a9e7-d4ba7edf6ef3",
        }
    }

    print("Streaming...", flush=True)
    async for chunk in graph.astream(
        inputs,
        config=config,
        stream_mode="messages",
    ):
        message, metadata = chunk

        print("TYPE:", type(message))
        print("CONTENT:", repr(message.content))
        print("METADATA:", metadata)

    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(main())