from __future__ import annotations

import base64
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.utils.helpers import ROOT_DIR


ACADEMIC_MARKS_CSV = ROOT_DIR / "data" / "academic_marks.csv"


@dataclass(frozen=True)
class SubjectMark:
    subject: str
    credits: float
    marks: float
    grade_point: float


def _grade_point_from_marks(marks: float) -> float:
    """
    Map marks (0-100) -> grade point (0-10).
    Simple, commonly used bands; adjust bands if your institute differs.
    """
    m = float(marks)
    if m >= 90:
        return 10.0
    if m >= 80:
        return 9.0
    if m >= 70:
        return 8.0
    if m >= 60:
        return 7.0
    if m >= 50:
        return 6.0
    if m >= 45:
        return 5.0
    if m >= 40:
        return 4.0
    return 0.0


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_academic_marks_rows(path: Path = ACADEMIC_MARKS_CSV) -> list[dict[str, str]]:
    """
    Load marks from CSV on demand (no caching) so file edits are reflected immediately.
    """
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_academic_summary(username: str, *, path: Path = ACADEMIC_MARKS_CSV) -> dict[str, Any]:
    """
    Returns:
      - semesters: [{semester, sgpa, total_credits, subjects:[...]}]
      - cgpa
      - comparison: [{from_semester, to_semester, sgpa_delta}]
    """
    user = (username or "").strip()
    rows = [r for r in load_academic_marks_rows(path) if (r.get("username") or "").strip() == user]

    # semester -> subjects
    sem_map: dict[int, list[SubjectMark]] = {}
    for r in rows:
        sem = int(_safe_float(r.get("semester"), default=0))
        if sem <= 0:
            continue
        subject = (r.get("subject") or "").strip() or "Subject"
        credits = max(0.0, _safe_float(r.get("credits"), default=0.0))
        marks = max(0.0, min(100.0, _safe_float(r.get("marks"), default=0.0)))
        gp = _grade_point_from_marks(marks)
        sem_map.setdefault(sem, []).append(SubjectMark(subject=subject, credits=credits, marks=marks, grade_point=gp))

    semesters_out: list[dict[str, Any]] = []
    total_qp = 0.0
    total_credits_all = 0.0

    for sem in sorted(sem_map.keys()):
        subjects = sem_map[sem]
        sem_credits = sum(s.credits for s in subjects) or 0.0
        sem_qp = sum(s.grade_point * s.credits for s in subjects) or 0.0
        sgpa = 0.0 if sem_credits <= 0 else round(sem_qp / sem_credits, 2)

        total_qp += sem_qp
        total_credits_all += sem_credits

        semesters_out.append(
            {
                "semester": sem,
                "sgpa": sgpa,
                "total_credits": round(sem_credits, 2),
                "subjects": [
                    {
                        "subject": s.subject,
                        "credits": round(s.credits, 2),
                        "marks": round(s.marks, 2),
                        "grade_point": round(s.grade_point, 2),
                    }
                    for s in subjects
                ],
            }
        )

    # Existing CGPA logic is intentionally preserved as-is.
    cgpa = 0.0 if total_credits_all <= 0 else round(total_qp / total_credits_all, 2)

    comparison: list[dict[str, Any]] = []
    for i in range(1, len(semesters_out)):
        prev = semesters_out[i - 1]
        cur = semesters_out[i]
        comparison.append(
            {
                "from_semester": prev["semester"],
                "to_semester": cur["semester"],
                "sgpa_delta": round(float(cur["sgpa"]) - float(prev["sgpa"]), 2),
            }
        )

    # ML inference simulation: predict next SGPA with recency-weighted average.
    # This is intentionally simple and viva-friendly.
    semester_sgpas = [float(s["sgpa"]) for s in semesters_out]
    predicted_next_sgpa = 0.0
    if semester_sgpas:
        total_weight = 0.0
        weighted_sum = 0.0
        for idx, sgpa in enumerate(semester_sgpas, start=1):
            weighted_sum += idx * sgpa
            total_weight += idx
        predicted_next_sgpa = round(weighted_sum / total_weight, 2) if total_weight > 0 else round(semester_sgpas[-1], 2)

    # Data encryption simulation for cloud storage/transport:
    # encode semester summary as Base64; decode only when needed.
    encoded_semester_payload = base64.b64encode(
        json.dumps(semesters_out, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).decode("ascii")

    decoded_semesters_count = 0
    try:
        decoded_raw = base64.b64decode(encoded_semester_payload.encode("ascii")).decode("utf-8")
        decoded_semesters = json.loads(decoded_raw)
        decoded_semesters_count = len(decoded_semesters) if isinstance(decoded_semesters, list) else 0
    except (ValueError, TypeError):
        decoded_semesters_count = 0

    # MPC simulation: split CGPA accumulation into two semester groups and combine.
    # This simulates distributed partial computation without changing existing CGPA formula.
    mid = len(semesters_out) // 2
    group_a = semesters_out[:mid]
    group_b = semesters_out[mid:]

    part_a_qp = sum(
        sum(float(sub["grade_point"]) * float(sub["credits"]) for sub in sem["subjects"])
        for sem in group_a
    )
    part_a_credits = sum(sum(float(sub["credits"]) for sub in sem["subjects"]) for sem in group_a)
    part_b_qp = sum(
        sum(float(sub["grade_point"]) * float(sub["credits"]) for sub in sem["subjects"])
        for sem in group_b
    )
    part_b_credits = sum(sum(float(sub["credits"]) for sub in sem["subjects"]) for sem in group_b)
    combined_credits = part_a_credits + part_b_credits
    mpc_simulated_cgpa = 0.0 if combined_credits <= 0 else round((part_a_qp + part_b_qp) / combined_credits, 2)

    return {
        "username": user,
        "semesters": semesters_out,
        "cgpa": cgpa,
        "comparison": comparison,
        "predicted_next_sgpa": predicted_next_sgpa,
        "security_simulation": {
            "encoding": "base64",
            "encoded_semester_payload": encoded_semester_payload,
            "decoded_semesters_count": decoded_semesters_count,
        },
        "mpc_simulation": {
            "part_a": {"semesters": [s["semester"] for s in group_a], "quality_points": round(part_a_qp, 2), "credits": round(part_a_credits, 2)},
            "part_b": {"semesters": [s["semester"] for s in group_b], "quality_points": round(part_b_qp, 2), "credits": round(part_b_credits, 2)},
            "combined_cgpa": mpc_simulated_cgpa,
        },
        "cloud_simulation_note": "Frontend fetches summary from backend API, simulating cloud-hosted inference and secure processing.",
        "data_source": str(path),
    }

