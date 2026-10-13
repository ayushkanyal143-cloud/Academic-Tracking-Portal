"""
scikit-learn performance classifier trained on data/students.csv at startup.

Features: attendance (%), marks (0–10 scale, same space as CGPA for this project).
Labels: Poor, Average, Good (from the dataset's performance column).

Inference runs after metrics are derived from the enrolled record or from the FE share pipeline.
"""

from __future__ import annotations

import csv
import logging
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.utils.helpers import get_students_dataset_path

logger = logging.getLogger(__name__)

_LABEL_ORDER = ("Poor", "Average", "Good")

# Dataset labels can vary in case/whitespace and may include synonyms.
# Keys MUST be lowercase to match normalization in training.
_LABEL_TO_INDEX: dict[str, int] = {
    "poor": 0,
    "average": 1,
    "good": 2,
    # Common synonym that appears in some datasets; map to "Good" to keep
    # the original 3-class pipeline intact.
    "excellent": 2,
}
_pipeline: Pipeline | None = None


def _normalize_label(value: Any) -> str:
    return ("" if value is None else str(value)).strip().lower()


def _build_training_arrays() -> tuple[np.ndarray, np.ndarray]:
    path = get_students_dataset_path()
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 3:
        raise ValueError("students.csv needs at least a few rows to train the demo model.")

    X_list: list[list[float]] = []
    y_list: list[int] = []

    for r in rows:
        label = _normalize_label(r.get("performance"))
        idx = _LABEL_TO_INDEX.get(label)
        if idx is None:
            logger.warning("Unknown performance label %r in dataset row id=%r; skipping.", label, r.get("id"))
            continue

        X_list.append([float(r["attendance"]), float(r["marks"])])
        y_list.append(int(idx))

    if len(y_list) < 3:
        raise ValueError(
            "Not enough labeled rows to train the model. "
            "Check the 'performance' column values and supported labels: "
            f"{sorted(_LABEL_TO_INDEX.keys())}"
        )

    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.int64)
    return X, y


def init_model() -> None:
    """
    Train once per process. Called from app factory so failures surface at startup.
    """
    global _pipeline
    if _pipeline is not None:
        return
    X, y = _build_training_arrays()
    _pipeline = Pipeline(
        [
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=42)),
        ]
    )
    _pipeline.fit(X, y)
    logger.info("ML model trained on dataset (%d samples).", len(y))


def predict_performance(attendance_percentage: float, marks: float) -> str:
    """Return Poor / Average / Good for viva-friendly wording."""
    init_model()
    assert _pipeline is not None
    pred = _pipeline.predict([[float(attendance_percentage), float(marks)]])[0]
    return _LABEL_ORDER[int(pred)]


def classify_performance(attendance_percentage: float, cgpa: float) -> str:
    """
    Used by the share-based API path: CGPA is already on the same 0–10 scale as marks
    in the CSV, so we feed it as the second feature.
    """
    return predict_performance(attendance_percentage, cgpa)
