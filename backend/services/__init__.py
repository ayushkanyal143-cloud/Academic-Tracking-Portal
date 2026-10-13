"""Services: auth (CSV), metrics + FE storage, MPC keys."""

from .auth_service import get_student_by_username, load_students, public_record, verify_login
from .compute import compute_metrics, compute_results_from_shares, store_protected_data
from .key_sharing import get_student_token_from_parts, init_key_parts

__all__ = [
    "compute_metrics",
    "compute_results_from_shares",
    "get_student_by_username",
    "get_student_token_from_parts",
    "init_key_parts",
    "load_students",
    "public_record",
    "store_protected_data",
    "verify_login",
]
