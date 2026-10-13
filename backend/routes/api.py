"""
REST API: /submit-data, /get-result (legacy share flow), /api/my-summary (dataset + session).

Security simulation order for submit-data:
  1) Parse JSON
  2) SHA-256 over canonical payload (hash_submission_payload)
  3) MPC key split + token derivation (key_sharing)
  4) FE-style storage of shares only (compute.store_protected_data)
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request, session

from backend.services import (
    compute_metrics,
    compute_results_from_shares,
    get_student_token_from_parts,
    init_key_parts,
    public_record,
    store_protected_data,
)
from backend.services.auth_service import get_student_by_username
from backend.services.academic import build_academic_summary
from backend.utils.helpers import hash_submission_payload

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

REQUIRED_SHARE_KEYS = frozenset({"attendance_present", "attendance_total", "grade_sum", "grade_count"})


def _validate_shares(data: dict) -> tuple[dict, dict, dict] | tuple[None, str]:
    if "share1" not in data or "share2" not in data or "share3" not in data:
        return None, "share1, share2, share3 required"
    share1, share2, share3 = data["share1"], data["share2"], data["share3"]
    for name, share in (("share1", share1), ("share2", share2), ("share3", share3)):
        if not isinstance(share, dict) or REQUIRED_SHARE_KEYS - set(share.keys()):
            return None, f"{name} must contain attendance_present, attendance_total, grade_sum, grade_count"
        for k in REQUIRED_SHARE_KEYS:
            try:
                share[k] = int(share[k])
            except (TypeError, ValueError):
                return None, f"{name}.{k} must be a valid integer"
    return (share1, share2, share3), ""


@api_bp.route("/submit-data", methods=["POST"])
def submit_data():
    data = request.get_json(silent=True)
    if not data:
        logger.warning("submit-data: missing JSON body")
        return jsonify({"ok": False, "error": "JSON body required"}), 400

    student_id = (data.get("student_id") or "").strip() or "anonymous"
    validated = _validate_shares(data)
    if validated[0] is None:
        return jsonify({"ok": False, "error": validated[1]}), 400
    share1, share2, share3 = validated[0]

    payload_digest = hash_submission_payload(student_id, share1, share2, share3)
    logger.debug("Submission digest (SHA-256): %s...", payload_digest[:16])

    init_key_parts(student_id)
    student_token = get_student_token_from_parts(student_id)
    if not student_token:
        logger.error("Token derivation failed for session")
        return jsonify({"ok": False, "error": "Could not derive token"}), 500

    store_protected_data(student_token, share1, share2, share3)

    return jsonify(
        {
            "ok": True,
            "student_token": student_token,
            "secure_processing": True,
        }
    )


@api_bp.route("/get-result", methods=["GET"])
def get_result():
    student_token = request.args.get("student_token")
    if not student_token:
        return jsonify({"ok": False, "error": "student_token query parameter required"}), 400

    result = compute_results_from_shares(student_token)
    if result is None:
        return jsonify({"ok": False, "error": "No data found for this token"}), 404

    ai = result["ai_predicted_performance"]
    return jsonify(
        {
            "ok": True,
            "attendance_percentage": result["attendance_percentage"],
            "cgpa": result["cgpa"],
            "eligibility": result["eligibility"],
            "performance_category": result["performance_category"],
            "ai_prediction": ai,
            "ai_predicted_performance": ai,
            "secure_processing": True,
        }
    )


@api_bp.route("/api/my-summary", methods=["GET"])
def my_summary():
    """
    Dataset-driven dashboard payload for the logged-in student.
    Session cookie required; does not replace the token-based /get-result API.
    """
    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    row = get_student_by_username(username)
    if not row:
        return jsonify({"ok": False, "error": "Student not found in dataset"}), 404

    metrics = compute_metrics(float(row["attendance"]), float(row["marks"]))
    profile = public_record(row)
    ai = metrics["ai_predicted_performance"]

    return jsonify(
        {
            "ok": True,
            "profile": profile,
            "attendance_percentage": metrics["attendance_percentage"],
            "cgpa": metrics["cgpa"],
            "eligibility": metrics["eligibility"],
            "performance_category": metrics["performance_category"],
            "ai_prediction": ai,
            "ai_predicted_performance": ai,
            "secure_processing": True,
            "source": "dataset",
        }
    )


@api_bp.route("/api/academic-summary", methods=["GET"])
def academic_summary():
    """
    Semester-wise marks + SGPA/CGPA.
    Loads CSV on each request so edits reflect instantly.
    """
    username = session.get("user")
    if not username:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    summary = build_academic_summary(username)
    if not summary["semesters"]:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "No semester marks found for this user in data/academic_marks.csv",
                }
            ),
            404,
        )

    return jsonify({"ok": True, "summary": summary})
