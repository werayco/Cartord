import asyncio
import importlib
import json
from pathlib import Path
from uuid import UUID

import pytest
from langchain_core.messages import HumanMessage

from app.core.schemas import IntentClassification
from app.services.agent_state import AgentState

CASES_PATH = Path(__file__).parents[1] / "app" / "evals" / "intent_cases.json"
INTENT_TARGETS = {
    "place_order": "collect_order_details",
    "check_balance": "wallet_balance",
    "general": "general_agent",
}


def load_cases():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    for case in cases:
        IntentClassification(
            intent=case["expected_intent"],
            product_query=case["expected_product_query"],
            quantity=case["expected_quantity"],
        )
    return cases


@pytest.mark.parametrize("case", load_cases(), ids=lambda case: case["id"])
def test_eval_case_routes_intent_and_preserves_explicit_slots(case, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "eval-test-key")
    intent_classifier = importlib.import_module("app.nodes.intent_classifier")
    prediction = IntentClassification(
        intent=case["expected_intent"],
        product_query=case["expected_product_query"],
        quantity=case["expected_quantity"],
    )

    class FakeClassifier:
        async def ainvoke(self, messages, config):
            assert messages[-1].content == case["message"]
            assert config == {}
            return prediction

    monkeypatch.setattr(intent_classifier, "classifier_llm", FakeClassifier())
    state: AgentState = {
        "messages": [HumanMessage(content=case["message"])],
        "user_id": UUID(int=0),
        "users_name": "eval",
    }

    command = asyncio.run(intent_classifier.classify_intent(state, {}))

    assert command.goto == INTENT_TARGETS[case["expected_intent"]]
    assert command.update["intent"] == case["expected_intent"]
    if case["expected_intent"] == "place_order":
        expected_draft = {}
        if case["expected_product_query"]:
            expected_draft["product_query"] = case["expected_product_query"]
        if case["expected_quantity"]:
            expected_draft["quantity"] = case["expected_quantity"]
        assert command.update["order_draft"] == expected_draft
