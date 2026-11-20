import asyncio
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.nodes.intent_classifier import INTENT_SYSTEM_PROMPT, classifier_llm

CASES_PATH = Path(__file__).with_name("intent_cases.json")
MIN_INTENT_ACCURACY = 0.8
MIN_EXPLICIT_SLOT_ACCURACY = 0.8


async def evaluate() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    intent_correct = 0
    slot_correct = 0

    for case in cases:
        result = await classifier_llm.ainvoke(
            [
                SystemMessage(content=INTENT_SYSTEM_PROMPT),
                HumanMessage(content=case["message"]),
            ]
        )
        intent_matches = result.intent == case["expected_intent"]
        intent_correct += intent_matches

        expected_slots = (case["expected_product_query"], case["expected_quantity"])
        actual_slots = (result.product_query, result.quantity)
        slot_correct += actual_slots == expected_slots

        status = "PASS" if intent_matches else "FAIL"
        print(
            f"{status} {case['id']}: "
            f"expected={case['expected_intent']}, got={result.intent}"
        )

    intent_accuracy = intent_correct / len(cases)
    slot_accuracy = slot_correct / len(cases)
    print(f"intent accuracy: {intent_accuracy:.1%} ({intent_correct}/{len(cases)})")
    print(f"slot exact match: {slot_accuracy:.1%} ({slot_correct}/{len(cases)})")

    return int(
        intent_accuracy < MIN_INTENT_ACCURACY
        or slot_accuracy < MIN_EXPLICIT_SLOT_ACCURACY
    )


if __name__ == "__main__":
    raise SystemExit(asyncio.run(evaluate()))
