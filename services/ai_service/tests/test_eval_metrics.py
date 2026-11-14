import asyncio
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from app.evals import evaluate_embeddings

CASES_PATH = Path(__file__).parents[1] / "app" / "evals" / "embedding_cases.json"


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ([1.0, 0.0], [1.0, 0.0], 1.0),
        ([1.0, 0.0], [0.0, 1.0], 0.0),
        ([1.0, 0.0], [-1.0, 0.0], -1.0),
    ],
)
def test_cosine_similarity(left, right, expected):
    assert evaluate_embeddings._cosine_similarity(left, right) == pytest.approx(
        expected
    )


def test_cosine_similarity_rejects_mismatched_dimensions():
    with pytest.raises(ValueError, match="different dimensions"):
        evaluate_embeddings._cosine_similarity([1.0], [1.0, 0.0])


def test_cosine_similarity_rejects_zero_vectors():
    with pytest.raises(ValueError, match="zero magnitude"):
        evaluate_embeddings._cosine_similarity([0.0, 0.0], [1.0, 0.0])


def test_embedding_eval_passes_when_relevant_docs_rank_first(monkeypatch, capsys):
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    documents = cases["documents"]
    queries = cases["queries"]
    document_indexes = {doc["id"]: i for i, doc in enumerate(documents)}

    async def fake_encode(text):
        if isinstance(text, list):
            return [
                [float(i == j) for j in range(len(documents))]
                for i, _ in enumerate(text)
            ]
        relevant_index = document_indexes[
            next(
                case["relevant_document_id"]
                for case in queries
                if case["text"] == text
            )
        ]
        return [
            [float(i == relevant_index) for i in range(len(documents))]
        ]

    fake_embedding_model = ModuleType("app.services.embedding_model")
    fake_embedding_model.encode_text = fake_encode
    monkeypatch.setitem(
        sys.modules, "app.services.embedding_model", fake_embedding_model
    )

    assert asyncio.run(evaluate_embeddings.evaluate()) == 0
    assert "vector hit rate@3: 100.0%" in capsys.readouterr().out


def test_embedding_eval_fails_below_hit_rate_threshold(monkeypatch):
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    documents = cases["documents"]

    async def fake_encode(text):
        if isinstance(text, list):
            return [[1.0, 0.0] for _ in text]
        return [[1.0, 0.0]]

    fake_embedding_model = ModuleType("app.services.embedding_model")
    fake_embedding_model.encode_text = fake_encode
    monkeypatch.setitem(
        sys.modules, "app.services.embedding_model", fake_embedding_model
    )

    assert len(documents) == 8
    assert asyncio.run(evaluate_embeddings.evaluate()) == 1
