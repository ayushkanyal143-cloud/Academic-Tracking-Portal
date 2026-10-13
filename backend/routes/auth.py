"""
Session authentication backed by data/students.csv (see auth_service).

/login and /logout are public. HTML pages use login_required.
/share APIs stay open for tooling and the optional legacy form flow.
"""

from __future__ import annotations

from functools import wraps

from flask import Blueprint, redirect, render_template, request, session, url_for

from backend.services.auth_service import verify_login
from backend.utils.helpers import safe_redirect_path

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    """Redirect unauthenticated users to /login with a safe return path."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            next_url = request.path
            if request.query_string:
                next_url = next_url + "?" + request.query_string.decode()
            return redirect(url_for("auth.login", next=next_url))
        return view(*args, **kwargs)

    return wrapped


def _next_from_request() -> str | None:
    return request.args.get("next") or request.form.get("next")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and session.get("user"):
        return redirect(safe_redirect_path(request.args.get("next"), url_for("pages.index")))

    if request.method == "POST":
        username_input = request.form.get("username") or ""
        password_input = request.form.get("password") or ""
        username = username_input.strip()
        password = password_input.strip()

        # Basic input validation for the authentication layer.
        if len(username) < 3 or len(username) > 50:
            return render_template(
                "login.html",
                error="Username must be 3 to 50 characters.",
                next_url=_next_from_request(),
            )
        if len(password) < 3 or len(password) > 128:
            return render_template(
                "login.html",
                error="Password must be 3 to 128 characters.",
                next_url=_next_from_request(),
            )

        row = verify_login(username, password)
        if row:
            session["user"] = (row.get("username") or "").strip()
            session["student_id"] = (row.get("id") or "").strip()
            return redirect(safe_redirect_path(_next_from_request(), url_for("pages.index")))
        return render_template(
            "login.html",
            error="Invalid username or password.",
            next_url=_next_from_request(),
        )

    return render_template("login.html", next_url=request.args.get("next"))


@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("student_id", None)
    return redirect(url_for("auth.login"))
