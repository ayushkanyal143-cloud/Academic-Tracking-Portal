"""Flask blueprints."""

from .api import api_bp
from .auth import auth_bp
from .pages import pages_bp

__all__ = ["api_bp", "auth_bp", "pages_bp"]
