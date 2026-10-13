"""
Academic metrics + FE/MPC simulation storage.

- Dataset flow: compute_metrics(attendance, marks) uses enrollment data + ML model.
- Legacy API flow: additive shares stored as in a functional-encryption-style simulation;
  MPC key parts live in key_sharing.py (hashes combined into token, never full raw key).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.ml.model import predict_performance

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SHARES_FILE = _DATA_DIR / "student_shares.json"


def _load_shares() -> dict:
    _DATA_DIR.mkdir(exist_ok=True)
    if not _SHARES_FILE.exists():
        return {}
    try:
        return json.loads(_SHARES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_shares(data: dict) -> None:
    _DATA_DIR.mkdir(exist_ok=True)
    _SHARES_FILE.write_text(json.dumps(data), encoding="utf-8")


def store_protected_data(student_token: str, share1: dict, share2: dict, share3: dict) -> None:
    """FE simulation: persist only share payloads keyed by opaque token."""
    all_shares = _load_shares()
    all_shares[student_token] = {"share1": share1, "share2": share2, "share3": share3}
    _save_shares(all_shares)
    logger.debug("Stored protected shares (token not logged).")


def compute_results_from_shares(student_token: str) -> dict | None:
    """Recombine shares in memory; emit policy outputs + ML on aggregates only."""
    all_shares = _load_shares()
    student_data = all_shares.get(student_token)
    if not student_data:
        return None

    s1, s2, s3 = student_data["share1"], student_data["share2"], student_data["share3"]
    att_num = s1["attendance_present"] + s2["attendance_present"] + s3["attendance_present"]
    att_den = s1["attendance_total"] + s2["attendance_total"] + s3["attendance_total"]
    attendance_pct = 0.0 if att_den <= 0 else round(100.0 * att_num / att_den, 2)

    grade_sum_scaled = s1["grade_sum"] + s2["grade_sum"] + s3["grade_sum"]
    count = s1["grade_count"] + s2["grade_count"] + s3["grade_count"]
    cgpa = 0.0 if count <= 0 else round((grade_sum_scaled / 100.0) / count, 2)

    return _finalize_metrics(attendance_pct, cgpa, ml_feature_marks=cgpa)


def compute_metrics(attendance_pct: float, marks: float) -> dict:
    """
    Dataset-driven dashboard: attendance is already a percentage in CSV;
    marks are on a 0–10 scale and define CGPA for display.
    """
    return _finalize_metrics(float(attendance_pct), float(marks), ml_feature_marks=float(marks))


def _finalize_metrics(attendance_pct: float, cgpa: float, ml_feature_marks: float) -> dict:
    MIN_ATTENDANCE_PCT = 75.0
    MIN_CGPA = 5.0
    eligibility = "Allowed" if attendance_pct >= MIN_ATTENDANCE_PCT and cgpa >= MIN_CGPA else "Not Allowed"

    ai_label = predict_performance(attendance_pct, ml_feature_marks)

    return {
        "attendance_percentage": round(attendance_pct, 2),
        "cgpa": round(cgpa, 2),
        "eligibility": eligibility,
        "performance_category": ai_label,
        "ai_predicted_performance": ai_label,
    }
