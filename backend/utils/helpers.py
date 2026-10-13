"""
Shared helpers: project paths, payload hashing (integrity simulation), URL safety.

Functional encryption / MPC are implemented in services (see compute.py, key_sharing.py);
this module holds cross-cutting utilities for routes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

# Project root (parent of backend/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STUDENTS_CSV = ROOT_DIR / "data" / "students.csv"
STUDENTS_CSV_PLAIN_MIRROR = ROOT_DIR / "data" / "students_login.csv"


def _password_looks_like_sha256_hex(value: str) -> bool:
    s = value.strip()
    if len(s) != 64:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in s)


def get_students_dataset_path() -> Path:
    """
    Use data/students.csv by default.

    If that file still has legacy password hashes (64-char hex) and
    data/students_login.csv exists with plain-text passwords, read the mirror
    instead so login and ML stay consistent (e.g. when students.csv is locked
    by sync tools — replace it with plain text when you can).
    """
    if STUDENTS_CSV_PLAIN_MIRROR.exists():
        if not STUDENTS_CSV.exists():
            return STUDENTS_CSV_PLAIN_MIRROR
        try:
            with STUDENTS_CSV.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            if rows and _password_looks_like_sha256_hex(rows[0].get("password") or ""):
                return STUDENTS_CSV_PLAIN_MIRROR
        except OSError:
            return STUDENTS_CSV_PLAIN_MIRROR
    return STUDENTS_CSV


def hash_submission_payload(student_id: str, share1: dict, share2: dict, share3: dict) -> str:
    """SHA-256 over canonical JSON before MPC/storage (simulated cloud integrity gate)."""
    payload: dict[str, Any] = {
        "student_id": (student_id or "").strip(),
        "share1": share1,
        "share2": share2,
        "share3": share3,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def safe_redirect_path(candidate: str | None, fallback: str) -> str:
    """Prevent open redirects: only same-site relative paths."""
    if candidate and candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return fallback
