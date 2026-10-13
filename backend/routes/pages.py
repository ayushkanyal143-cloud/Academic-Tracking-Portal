"""Server-rendered pages (session-protected)."""

from flask import Blueprint, render_template, session

from backend.routes.auth import login_required
from backend.services.auth_service import get_student_by_username, public_record

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
@login_required
def index():
    row = get_student_by_username(session["user"])
    student = public_record(row) if row else None
    return render_template("index.html", student=student)


@pages_bp.route("/result")
@login_required
def result_page():
    return render_template("result.html")
