from app.nodes.intent_classifier import CUSTOMER_SYSTEM_PROMPT, llm_customer
from langchain_core.messages import HumanMessage, SystemMessage


async def main():
    messages = [
        SystemMessage(content=CUSTOMER_SYSTEM_PROMPT),
        HumanMessage(content="how are you"),
    ]

    async for chunk in llm_customer.astream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)

    print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
