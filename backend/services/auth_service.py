"""
Dataset-backed authentication.

Reads users from data/students.csv.
Supports secure password checking with SHA-256 hashes while remaining backward
compatible with plain-text rows for existing demo datasets.
"""

from __future__ import annotations

import csv
import hashlib
import logging
from typing import Any

from backend.utils.helpers import get_students_dataset_path

logger = logging.getLogger(__name__)

_rows: list[dict[str, Any]] | None = None


def load_students() -> list[dict[str, Any]]:
    """Load and cache CSV rows (reload process picks up file edits)."""
    global _rows
    if _rows is None:
        path = get_students_dataset_path()
        print("[auth debug] loading students from:", path)
        with path.open(newline="", encoding="utf-8") as f:
            _rows = list(csv.DictReader(f))
        logger.info("Loaded %d student records from dataset.", len(_rows))
    return _rows


def reload_students() -> None:
    """Testing / admin: force re-read CSV."""
    global _rows
    _rows = None
    load_students()


def _is_sha256_hex(value: str) -> bool:
    s = (value or "").strip()
    if len(s) != 64:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in s)


def _sha256_text(raw: str) -> str:
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


def _password_matches(input_password: str, stored_password: str) -> bool:
    """
    Security layer:
    - If stored password is SHA-256 hex, compare against hash(input_password).
    - Else keep legacy plain-text compare so existing records still work.
    """
    entered = (input_password or "").strip()
    saved = (stored_password or "").strip()
    if _is_sha256_hex(saved):
        return _sha256_text(entered).lower() == saved.lower()
    return entered == saved


def verify_login(username: str, password: str) -> dict[str, Any] | None:
    """Return full row if username and password match CSV."""
    username = (username or "").strip()
    password = (password or "").strip()

    if not username:
        return None

    for row in load_students():
        row_user = (row.get("username") or "").strip()
        row_pass = row.get("password") or ""

        if row_user == username and _password_matches(password, row_pass):
            return row

    return None


def get_student_by_username(username: str) -> dict[str, Any] | None:
    key = (username or "").strip()
    for row in load_students():
        if (row.get("username") or "").strip() == key:
            return row
    return None


def public_record(row: dict[str, Any]) -> dict[str, Any]:
    """Expose safe fields for templates / JSON (no password)."""
    return {
        "id": row["id"],
        "username": row["username"],
        "attendance": row["attendance"],
        "marks": row["marks"],
        "performance": row.get("performance", ""),
    }
