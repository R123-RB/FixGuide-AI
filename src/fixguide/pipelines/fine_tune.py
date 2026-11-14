"""Fine-tuning pipeline for product classifier."""

from __future__ import annotations

import json
from pathlib import Path

import typer

app = typer.Typer()


def _load_training_data(data_dir: str) -> list[dict]:
    """Load labeled training data from JSONL files."""
    path = Path(data_dir)
    if not path.exists():
        return []
    samples = []
    for f in sorted(path.glob("*.jsonl")):
        with f.open() as fh:
            for line in fh:
                if line.strip():
                    samples.append(json.loads(line))
    return samples


def _build_dataset(samples: list[dict]) -> tuple[list[str], list[int]]:
    """Build text/label pairs from samples."""
    from fixguide.models.domain import ProductCategory

    cat_to_id = {c.value: i for i, c in enumerate(ProductCategory)}
    texts, labels = [], []
    for s in samples:
        text = s.get("text", "")
        cat = s.get("category", "")
        if text and cat in cat_to_id:
            texts.append(text)
            labels.append(cat_to_id[cat])
    return texts, labels


@app.command()
def train(
    data_dir: str = "data/processed/classifier",
    model_name: str = "microsoft/resnet-50",
    output_dir: str = "models/product_classifier",
    epochs: int = 10,
    batch_size: int = 32,
) -> None:
    """Fine-tune product classifier on labeled data."""
    samples = _load_training_data(data_dir)
    if not samples:
        return

    texts, labels = _build_dataset(samples)

    try:
        from sentence_transformers import InputExample, SentenceTransformer
        from sentence_transformers.loss import SoftmaxLoss  # type: ignore[import-not-found]
        from torch.utils.data import DataLoader
    except ImportError:
        return

    model = SentenceTransformer(model_name)
    train_examples = [InputExample(texts=[t], label=label) for t, label in zip(texts, labels)]
    train_dataloader: DataLoader[InputExample] = DataLoader(
        train_examples,  # type: ignore[arg-type]
        batch_size=batch_size,
    )
    train_loss = SoftmaxLoss(model, num_labels=len(set(labels)))

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=100,
        output_path=output_dir,
    )


@app.command()
def evaluate(model_dir: str = "models/product_classifier") -> None:
    """Evaluate fine-tuned classifier on test set."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_dir)
    samples = _load_training_data("data/eval/classifier_test")
    if not samples:
        return

    texts, labels = _build_dataset(samples)
    embeddings = model.encode(texts, show_progress_bar=True)

    # Simple nearest-neighbor classification
    from sklearn.metrics import accuracy_score  # type: ignore[import-untyped]
    from sklearn.neighbors import KNeighborsClassifier  # type: ignore[import-untyped]

    # Split train/test
    split = int(len(embeddings) * 0.8)
    knn = KNeighborsClassifier(n_neighbors=3)
    knn.fit(embeddings[:split], labels[:split])
    preds = knn.predict(embeddings[split:])

    accuracy_score(labels[split:], preds)


if __name__ == "__main__":
    app()
