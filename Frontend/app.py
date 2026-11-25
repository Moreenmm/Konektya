"""Konektya: connecting people in Kenya with reliable health information and services.

Start the website:
    python -m flask --app app seed-db       first time only: create the database with test data
    python -m flask --app app create-admin  add an administrator account
    python app.py                           then open http://127.0.0.1:5000
"""
import logging
import os
import secrets
from datetime import timedelta

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException


def _load_secret_key(instance_path):
    key = os.environ.get("KONEKTYA_SECRET_KEY")
    if key:
        return key
    key_file = os.path.join(instance_path, "secret_key")
    if os.path.exists(key_file):
        with open(key_file) as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(key_file, "w") as f:
        f.write(key)
    os.chmod(key_file, 0o600)
    return key


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        DATABASE=os.environ.get("KONEKTYA_DATABASE",
                                os.path.join(app.instance_path, "konektya.sqlite3")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("KONEKTYA_SECURE_COOKIES", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,  # limit for backup uploads
        PER_PAGE=20,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = _load_secret_key(app.instance_path)

    import accounts, admin, auth, db, public, security
    from content import format_date, render_body

    db.init_app(app)
    security.init_app(app)
    app.register_blueprint(public.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(accounts.bp)
    app.jinja_env.filters["render_body"] = render_body
    app.jinja_env.filters["nice_date"] = format_date

    # Friendly error pages that never expose technical details (NFR 13).
    messages = {
        400: ("Request could not be completed", None),
        403: ("Access denied", "You do not have permission to view this page."),
        404: ("Page not found", "The page you are looking for does not exist or has been removed."),
        405: ("Action not allowed", "That action is not available on this page."),
        413: ("File too large", "The uploaded file is larger than the 25 MB limit."),
    }

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        title, default_msg = messages.get(e.code, ("Something went wrong", None))
        msg = default_msg or (e.description if e.code == 400 else
                              "The request could not be completed.")
        return render_template("errors/error.html", code=e.code, title=title,
                               message=msg), e.code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception("Unhandled error")  # details go to the server log only
        return render_template(
            "errors/error.html", code=500, title="Something went wrong",
            message="An unexpected error occurred. Please try again later.",
        ), 500

    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
