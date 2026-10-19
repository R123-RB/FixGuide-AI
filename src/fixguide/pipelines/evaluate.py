"""Evaluation pipeline with real metrics."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

import typer

app = typer.Typer()


def _load_golden_set(path: str = "data/eval/retrieval_test.jsonl") -> list[dict]:
    """Load golden test set for retrieval evaluation."""
    p = Path(path)
    if not p.exists():
        return []
    results = []
    with p.open() as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def _load_risk_test(path: str = "data/eval/risk_gate_test.csv") -> list[dict]:
    """Load golden test set for risk gate evaluation."""
    p = Path(path)
    if not p.exists():
        return []
    results = []
    with p.open() as f:
        header = f.readline().strip().split(",")
        for line in f:
            if line.strip():
                values = line.strip().split(",")
                results.append(dict(zip(header, values)))
    return results


@app.command()
def retrieval() -> dict[str, float] | None:
    """Evaluate retrieval recall, nDCG, and MRR against a golden set."""
    from fixguide.core.retrieval import get_retriever
    from fixguide.models.domain import ProductCategory

    golden = _load_golden_set()
    if not golden:
        return None

    retriever = get_retriever()
    recall_scores = []
    ndcg_scores = []
    mrr_scores = []

    for item in golden:
        query = item["query"]
        category = ProductCategory(item.get("category", "game_controller"))
        relevant = set(item.get("relevant_chunk_ids", []))

        results = retriever.search(query, category, top_k=10)
        retrieved_ids = [r.chunk_id for r in results]

        # Recall@k
        retrieved_relevant = relevant & set(retrieved_ids)
        recall = len(retrieved_relevant) / len(relevant) if relevant else 0.0
        recall_scores.append(recall)

        # MRR
        rr = 0.0
        for i, rid in enumerate(retrieved_ids):
            if rid in relevant:
                rr = 1 / (i + 1)
                break
        mrr_scores.append(rr)

        # nDCG@k
        dcg = sum(1 / (i + 1) for i, rid in enumerate(retrieved_ids) if rid in relevant)
        ideal_relevant = sorted(relevant, key=lambda x: 0, reverse=True)[: len(retrieved_ids)]
        idcg = sum(1 / (i + 1) for i in range(len(ideal_relevant)))
        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcg_scores.append(ndcg)

    return {
        "recall@10": statistics.mean(recall_scores),
        "ndcg@10": statistics.mean(ndcg_scores),
        "mrr": statistics.mean(mrr_scores),
    }


@app.command(name="risk-gate")
def risk_gate() -> dict[str, float] | None:
    """Run risk gate evaluation."""
    from fixguide.core.risk import get_risk_gate
    from fixguide.models.domain import RiskLevel

    golden = _load_risk_test()
    if not golden:
        return None

    gate = get_risk_gate()
    tp = fp = tn = fn = 0

    for item in golden:
        category = item.get("category", "")
        problem = item.get("problem", "")
        expected = RiskLevel(item.get("expected_risk", "safe"))
        actual = gate.classify(category, problem, "beginner")

        if expected in (RiskLevel.HIGH_RISK, RiskLevel.BLOCKED):
            if actual in (RiskLevel.HIGH_RISK, RiskLevel.BLOCKED):
                tp += 1
            else:
                fn += 1
        else:
            if actual in (RiskLevel.HIGH_RISK, RiskLevel.BLOCKED):
                fp += 1
            else:
                tn += 1

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0

    return {"recall": recall, "precision": precision, "accuracy": accuracy}


@app.command()
async def vision() -> dict[str, float] | None:
    """Run vision verification evaluation against labeled image dataset."""
    from fixguide.core.verification import get_vision_verifier

    golden_path = Path("data/eval/vision_test.jsonl")
    if not golden_path.exists():
        return None

    golden = _load_golden_set(str(golden_path))
    if not golden:
        return None

    verifier = get_vision_verifier()
    tp = fp = tn = fn = 0
    latencies = []

    for item in golden:
        image_b64 = item.get("image", "")
        expected_match = item.get("expected_match", True)
        step_number = item.get("step_number", 1)
        expected_state = item.get("expected_visual_state", "")
        components = item.get("components", [])

        if not image_b64:
            continue

        import time

        start = time.time()
        result = await verifier.verify(
            image_base64=image_b64,
            step_number=step_number,
            expected_state=expected_state,
            components=components,
        )
        latencies.append(time.time() - start)

        actual_match = result.get("matches", False)
        if expected_match and actual_match:
            tp += 1
        elif expected_match and not actual_match:
            fn += 1
        elif not expected_match and actual_match:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0

    if latencies:
        pass

    return {"precision": precision, "recall": recall, "accuracy": accuracy}


@app.command()
def e2e() -> dict[str, float | int] | None:
    """Run end-to-end evaluation with scripted repair scenarios."""
    from fixguide.graph.builder import build_graph
    from fixguide.models.domain import ProductCategory

    golden_path = Path("data/eval/e2e_test.jsonl")
    if not golden_path.exists():
        return None

    golden = _load_golden_set(str(golden_path))
    if not golden:
        return None

    graph: Any = build_graph()
    successes = 0
    total = 0
    step_errors = []

    for item in golden:
        total += 1
        category = ProductCategory(item.get("category", "game_controller"))
        problem = item.get("problem", "")
        skill = item.get("skill", "beginner")
        tools = item.get("tools", [])
        expected_min_steps = item.get("expected_steps", 1)

        try:
            initial = {
                "session_id": f"eval-{total}",
                "category": category,
                "problem_description": problem,
                "user_skill_level": skill,
                "available_tools": tools,
                "next_action": "risk_gate",
            }
            result = graph.invoke(initial)
            completed = result.get("is_complete", False)
            steps_count = len(result.get("steps", []))
            if completed and steps_count >= expected_min_steps:
                successes += 1
            else:
                step_errors.append(
                    {
                        "category": category.value,
                        "problem": problem,
                        "completed": completed,
                        "steps": steps_count,
                        "expected_min": expected_min_steps,
                    }
                )
        except Exception as e:
            step_errors.append(
                {
                    "category": category.value,
                    "problem": problem,
                    "error": str(e),
                }
            )

    success_rate = successes / total if total > 0 else 0
    if step_errors:
        for err in step_errors[:5]:
            pass

    return {"success_rate": success_rate, "total": total, "successful": successes}


@app.command(name="all-metrics")
async def all_metrics() -> None:
    """Run all available evaluations."""
    retrieval()
    risk_gate()
    await vision()
    e2e()


if __name__ == "__main__":
    app()
