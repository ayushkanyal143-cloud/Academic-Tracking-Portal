"""
MPC-based key sharing simulation (educational).

The secret material is split into three parts; no single routine reassembles the
full key. Tokens are derived from per-part hashes only. Real deployments would
use protocols such as Shamir secret sharing across separate trust domains.
"""

import hashlib
import json
import secrets
from pathlib import Path

# MPC simulation: three separate in-memory maps — analogous to three parties.
_KEY_PART_1: dict[str, str] = {}
_KEY_PART_2: dict[str, str] = {}
_KEY_PART_3: dict[str, str] = {}

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DATA_DIR.mkdir(exist_ok=True)


def init_key_parts(student_id: str) -> tuple[str, str, str]:
    """
    Generate split key material; persist each share to its own file so no single
    file holds the combined secret (simulation of multi-party storage).
    """
    raw_secret = secrets.token_hex(32)
    part1 = secrets.token_hex(16)
    part2 = secrets.token_hex(16)
    part3 = hashlib.sha256((raw_secret + part1 + part2).encode()).hexdigest()[:32]

    _KEY_PART_1[student_id] = part1
    _KEY_PART_2[student_id] = part2
    _KEY_PART_3[student_id] = part3

    _save_key_part(1, student_id, part1)
    _save_key_part(2, student_id, part2)
    _save_key_part(3, student_id, part3)

    return (part1, part2, part3)


def _save_key_part(part_num: int, student_id: str, value: str) -> None:
    f = _DATA_DIR / f"key_part_{part_num}.json"
    data: dict = {}
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data[student_id] = value
    f.write_text(json.dumps(data), encoding="utf-8")


def _load_key_part(part_num: int, student_id: str) -> str | None:
    f = _DATA_DIR / f"key_part_{part_num}.json"
    if not f.exists():
        if part_num == 1:
            return _KEY_PART_1.get(student_id)
        if part_num == 2:
            return _KEY_PART_2.get(student_id)
        return _KEY_PART_3.get(student_id)
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data.get(student_id)


def get_student_token_from_parts(student_id: str) -> str | None:
    """
    Derive lookup token from H(part1)||H(part2)||H(part3) → SHA-256.
    Raw parts are never concatenated into one “master key” variable.
    """
    p1 = _load_key_part(1, student_id)
    p2 = _load_key_part(2, student_id)
    p3 = _load_key_part(3, student_id)
    if not (p1 and p2 and p3):
        return None
    h1 = hashlib.sha256(p1.encode()).hexdigest()
    h2 = hashlib.sha256(p2.encode()).hexdigest()
    h3 = hashlib.sha256(p3.encode()).hexdigest()
    combined = h1 + h2 + h3
    return hashlib.sha256(combined.encode()).hexdigest()
