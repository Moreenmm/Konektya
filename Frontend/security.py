"""CSRF protection and HTTP security headers."""
import hmac
import secrets

from flask import abort, request, session

CSRF_FIELD = "csrf_token"


def get_csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


def check_csrf():
    """Reject state-changing requests that lack the session's CSRF token."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    expected = session.get("_csrf")
    sent = request.form.get(CSRF_FIELD) or request.headers.get("X-CSRF-Token")
    if not expected or not sent or not hmac.compare_digest(expected, sent):
        abort(400, description="Your session expired or the form was invalid. "
                               "Please reload the page and try again.")


def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self'; "
        "script-src 'self'; form-action 'self'; frame-ancestors 'none'",
    )
    return response


def init_app(app):
    app.before_request(check_csrf)
    app.after_request(add_security_headers)
    app.jinja_env.globals["csrf_token"] = get_csrf_token
