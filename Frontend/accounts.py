"""Shared login for administrators and public users, plus public signup."""
import sqlite3
import time

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from audit import record
from auth import _failures, _is_locked, _throttle_key
from db import get_db
from validation import validate_admin

bp = Blueprint("accounts", __name__)

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


def _db():
    db = get_db()
    db.execute(USERS_TABLE)
    return db


def _find(db, table, identifier):
    return db.execute(
        f"SELECT * FROM {table} WHERE username = ? OR email = ?",
        (identifier, identifier.lower()),
    ).fetchone()


def _render(status=200, **ctx):
    ctx.setdefault("login_error", None)
    ctx.setdefault("signup_errors", [])
    ctx.setdefault("identifier", "")
    ctx.setdefault("signup", {})
    return render_template("public/system.html", **ctx), status


@bp.before_app_request
def load_logged_in_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id is not None:
        g.user = _db().execute(
            "SELECT id, username, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if g.user is None:
            session.pop("user_id", None)


@bp.route("/system")
def system():
    if g.admin:
        return redirect(url_for("admin.dashboard"))
    if g.user:
        return redirect(url_for("public.home"))
    return _render()


@bp.route("/system/login", methods=("POST",))
def login():
    identifier = request.form.get("identifier", "").strip()
    password = request.form.get("password", "")
    key = _throttle_key(identifier)

    if not identifier or not password:
        return _render(401, identifier=identifier,
                       login_error="Please enter both your username or email and your password.")
    if _is_locked(key):
        return _render(401, identifier=identifier,
                       login_error="Too many failed login attempts. Please wait 15 minutes and try again.")

    db = _db()
    admin = _find(db, "admins", identifier)
    if admin and check_password_hash(admin["password_hash"], password):
        _failures.pop(key, None)
        session.clear()
        session["admin_id"] = admin["id"]
        session.permanent = True
        g.admin = admin
        record("login", "admin", admin["id"], admin["username"])
        flash(f"Welcome back, {admin['username']}.", "success")
        return redirect(url_for("admin.dashboard"))

    user = _find(db, "users", identifier)
    if user and check_password_hash(user["password_hash"], password):
        _failures.pop(key, None)
        session.clear()
        session["user_id"] = user["id"]
        session.permanent = True
        flash(f"Welcome back, {user['username']}.", "success")
        return redirect(url_for("public.home"))

    _failures.setdefault(key, []).append(time.time())
    return _render(401, identifier=identifier,
                   login_error="Incorrect username/email or password.")


@bp.route("/system/signup", methods=("POST",))
def signup():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    errors = validate_admin(username, email, password)
    if password != confirm:
        errors.append("Passwords do not match.")

    db = _db()
    if not errors:
        for table in ("admins", "users"):
            taken = db.execute(
                f"SELECT 1 FROM {table} WHERE username = ? OR email = ?", (username, email)
            ).fetchone()
            if taken:
                errors.append("That username or email is already in use.")
                break

    if not errors:
        try:
            cur = db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            errors.append("That username or email is already in use.")

    if errors:
        return _render(400, signup_errors=errors,
                       signup={"username": username, "email": email})

    session.clear()
    session["user_id"] = cur.lastrowid
    session.permanent = True
    flash(f"Welcome to Konektya, {username}.", "success")
    return redirect(url_for("public.home"))
