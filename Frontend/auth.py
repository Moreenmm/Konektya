"""Administrator authentication (FR 6, NFR 1)."""
import functools
import time

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from audit import record
from db import get_db

bp = Blueprint("auth", __name__, url_prefix="/admin")

# Simple in-memory throttle against password guessing.
MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
_failures = {}


def _throttle_key(identifier):
    return f"{request.remote_addr}|{identifier.lower()}"


def _is_locked(key):
    attempts = [t for t in _failures.get(key, []) if time.time() - t < WINDOW_SECONDS]
    _failures[key] = attempts
    return len(attempts) >= MAX_FAILURES


def create_admin(db, username, email, password):
    db.execute(
        "INSERT INTO admins (username, email, password_hash) VALUES (?, ?, ?)",
        (username.strip(), email.strip().lower(), generate_password_hash(password)),
    )
    db.commit()


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.get("admin") is None:
            flash("Please log in to access the administrator area.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)
    return wrapped


@bp.before_app_request
def load_logged_in_admin():
    admin_id = session.get("admin_id")
    g.admin = None
    if admin_id is not None:
        g.admin = get_db().execute(
            "SELECT id, username, email FROM admins WHERE id = ?", (admin_id,)
        ).fetchone()
        if g.admin is None:
            session.pop("admin_id", None)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.admin:
        return redirect(url_for("admin.dashboard"))

    identifier = ""
    error = None
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        key = _throttle_key(identifier)

        if not identifier or not password:
            error = "Please enter both your username or email and your password."
        elif _is_locked(key):
            error = ("Too many failed login attempts. "
                     "Please wait 15 minutes and try again.")
        else:
            admin = get_db().execute(
                "SELECT * FROM admins WHERE username = ? OR email = ?",
                (identifier, identifier.lower()),
            ).fetchone()
            if admin is None or not check_password_hash(admin["password_hash"], password):
                _failures.setdefault(key, []).append(time.time())
                error = "Incorrect username/email or password."
            else:
                _failures.pop(key, None)
                session.clear()
                session["admin_id"] = admin["id"]
                session.permanent = True
                g.admin = admin
                record("login", "admin", admin["id"], admin["username"])
                flash(f"Welcome back, {admin['username']}.", "success")
                nxt = request.args.get("next", "")
                if not nxt.startswith("/admin") or nxt.startswith("//"):
                    nxt = url_for("admin.dashboard")
                return redirect(nxt)

    return render_template("admin/login.html", error=error, identifier=identifier), \
        (401 if error else 200)


@bp.route("/logout", methods=("POST",))
def logout():
    if g.admin:
        record("logout", "admin", g.admin["id"], g.admin["username"])
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("public.home"))
