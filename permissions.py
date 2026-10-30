"""Shared role/permission helpers for classic routes and /api/v2.
"""
from functools import wraps

from flask import jsonify
from flask_login import current_user, login_required


def role_required(*roles):
    """Allow a view only to logged-in users holding one of the given roles.

    Unauthenticated users fall through to the login flow (same as plain
    ``login_required``); authenticated users without one of the roles get a
    JSON 403.
    """
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if getattr(current_user, 'role', None) not in roles:
                return jsonify({'error': 'دسترسی غیرمجاز'}), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator
