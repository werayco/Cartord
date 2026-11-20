import asyncio
from threading import Lock
from typing import Any

from app.core.config import settings

MODEL_ID = "meta-llama/Llama-Prompt-Guard-2-22M"
INJECTION_LABELS = {"INJECTION", "JAILBREAK"}
INJECTION_SCORE_THRESHOLD = 0.5

_classifier: Any | None = None
_classifier_lock = Lock()


def _get_classifier() -> Any:
    global _classifier

    with _classifier_lock:
        if _classifier is None:
            from transformers import pipeline

            _classifier = pipeline(
                "text-classification",
                model=MODEL_ID,
                token=settings.HF_TOKEN or None,
                device=-1,
            )
        return _classifier


def _classify(text: str) -> bool:
    predictions = _get_classifier()(text, top_k=None, truncation=True)
    if predictions and isinstance(predictions[0], list):
        predictions = predictions[0]

    for prediction in predictions:
        label = prediction["label"].upper()
        if label not in INJECTION_LABELS and label != "BENIGN":
            raise RuntimeError(f"Unexpected prompt guard label: {label}")
        if (
            label in INJECTION_LABELS
            and float(prediction["score"]) >= INJECTION_SCORE_THRESHOLD
        ):
            return True

    return False


async def detect_prompt_injection(text: str) -> bool:
    if not settings.PROMPT_INJECTION_GUARD_ENABLED:
        return False

    return await asyncio.to_thread(_classify, text)
