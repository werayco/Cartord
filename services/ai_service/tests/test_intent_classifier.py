import asyncio

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.schemas import IntentClassification
from app.nodes import intent_classifier


def test_classifier_only_sends_latest_user_message(monkeypatch):
    previous_message = HumanMessage(content="Earlier question")
    latest_message = HumanMessage(content="How much do I have in my wallet?")
    captured_messages = []

    class FakeClassifier:
        async def ainvoke(self, messages, _config):
            assert _config == {}
            captured_messages.extend(messages)
            return IntentClassification(intent="check_balance")

    monkeypatch.setattr(intent_classifier, "classifier_llm", FakeClassifier())

    result = asyncio.run(
        intent_classifier.classify_intent(
            {
                "messages": [
                    previous_message,
                    AIMessage(content="Earlier answer"),
                    latest_message,
                ]
            },
            {},
        )
    )

    assert captured_messages == [
        SystemMessage(content=intent_classifier.INTENT_SYSTEM_PROMPT),
        latest_message,
    ]
    assert result.goto == "wallet_balance"
