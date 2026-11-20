import asyncio
import json
import math
from pathlib import Path

CASES_PATH = Path(__file__).with_name("embedding_cases.json")
MIN_HIT_RATE_AT_3 = 0.8


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors have different dimensions")

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        raise ValueError("Embedding vector has zero magnitude")

    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


async def evaluate() -> int:
    from app.services.embedding_model import encode_text

    dataset = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    documents = dataset["documents"]
    document_vectors = await encode_text([document["text"] for document in documents])

    if len(document_vectors) != len(documents):
        raise ValueError("Embedding model returned an unexpected document count")

    hits_at_3 = 0
    reciprocal_ranks = []

    for case in dataset["queries"]:
        query_vector = (await encode_text(case["text"]))[0]
        ranked = sorted(
            zip(
                documents,
                document_vectors,
                strict=True,
            ),
            key=lambda item: _cosine_similarity(query_vector, item[1]),
            reverse=True,
        )
        ranked_ids = [document["id"] for document, _ in ranked]
        rank = ranked_ids.index(case["relevant_document_id"]) + 1
        hits_at_3 += rank <= 3
        reciprocal_ranks.append(1 / rank)
        print(
            f"{'PASS' if rank <= 3 else 'FAIL'} {case['id']}: "
            f"relevant rank={rank}, top-3={ranked_ids[:3]}"
        )

    hit_rate_at_3 = hits_at_3 / len(dataset["queries"])
    mean_reciprocal_rank = sum(reciprocal_ranks) / len(reciprocal_ranks)
    print(f"vector hit rate@3: {hit_rate_at_3:.1%}")
    print(f"vector mean reciprocal rank: {mean_reciprocal_rank:.3f}")

    return int(hit_rate_at_3 < MIN_HIT_RATE_AT_3)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(evaluate()))
