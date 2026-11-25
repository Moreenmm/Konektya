"""Administrator dashboard: manage content, view audit log, back up/restore (FR 7, NFR 8, NFR 16)."""
import math
import sqlite3
from datetime import datetime, timezone

from flask import (Blueprint, Response, abort, current_app, flash, g, redirect,
                   render_template, request, url_for)

import queries
from audit import record
from auth import login_required
from backup import BackupError, backup_to_bytes, restore_from_upload
from db import get_db
from validation import (slugify, validate_article, validate_category,
                         validate_contact, validate_facility)

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@login_required
def require_login():
    """Every route in this blueprint needs an authenticated admin (NFR 1)."""
    return None


def _unique_slug(table, base, exclude_id=None):
    db = get_db()
    slug, n = base, 2
    while True:
        row = db.execute(f"SELECT id FROM {table} WHERE slug = ?", (slug,)).fetchone()
        if row is None or row["id"] == exclude_id:
            return slug
        slug, n = f"{base}-{n}", n + 1


def _save(action, entity, label, fn):
    """Run a write, log it, and report success or failure to the admin."""
    db = get_db()
    try:
        entity_id = fn(db)
        record(action, entity, entity_id, label, commit=False)
        db.commit()
    except sqlite3.Error:
        db.rollback()
        current_app.logger.exception("Database write failed")
        flash(f"The {entity.replace('_', ' ')} could not be {action}d because of a "
              "database problem. No changes were saved. Please try again.", "error")
        return False
    verb = {"create": "added", "update": "updated", "delete": "deleted",
            "publish": "published", "unpublish": "moved back to draft"}[action]
    flash(f"“{label}” was {verb} successfully.", "success")
    return True


def _get_or_404(table, item_id):
    row = get_db().execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        abort(404)
    return row


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ---------------- Dashboard ----------------

@bp.route("/")
def dashboard():
    db = get_db()
    count = lambda sql: db.execute(sql).fetchone()[0]  # noqa: E731
    stats = {
        "published": count("SELECT COUNT(*) FROM health_articles WHERE status='published'"),
        "drafts": count("SELECT COUNT(*) FROM health_articles WHERE status='draft'"),
        "facilities": count("SELECT COUNT(*) FROM facilities"),
        "contacts": count("SELECT COUNT(*) FROM emergency_contacts"),
        "services": count("SELECT COUNT(*) FROM service_categories"),
        "categories": count("SELECT COUNT(*) FROM health_categories"),
    }
    recent = db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 8").fetchall()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


# ---------------- Health information ----------------

@bp.route("/articles")
def articles():
    rows = get_db().execute(
        """SELECT a.id, a.title, a.status, a.updated_at, a.source_name, c.name AS category
           FROM health_articles a JOIN health_categories c ON c.id = a.category_id
           ORDER BY a.updated_at DESC"""
    ).fetchall()
    return render_template("admin/articles.html", articles=rows)


def _category_choices():
    return get_db().execute("SELECT id, name FROM health_categories ORDER BY name").fetchall()


@bp.route("/articles/new", methods=("GET", "POST"))
@bp.route("/articles/<int:article_id>/edit", methods=("GET", "POST"))
def article_form(article_id=None):
    article = _get_or_404("health_articles", article_id) if article_id else None
    categories = _category_choices()
    if not categories:
        flash("Add a health category before adding health information.", "error")
        return redirect(url_for("admin.health_categories"))

    form, errors = (dict(article) if article else {"status": "draft"}), []
    if request.method == "POST":
        data, errors = validate_article(request.form, {c["id"] for c in categories})
        form = dict(request.form)
        if not errors:
            slug = _unique_slug("health_articles", slugify(data["title"]), article_id)
            fields = ("category_id", "title", "summary", "body", "source_name",
                      "source_url", "status", "last_reviewed")
            values = [data[f] for f in fields]

            def write(db):
                if article:
                    db.execute(
                        f"UPDATE health_articles SET {', '.join(f + '=?' for f in fields)}, "
                        "slug=?, updated_at=? WHERE id=?",
                        values + [slug, _now(), article_id])
                    return article_id
                cur = db.execute(
                    f"INSERT INTO health_articles ({', '.join(fields)}, slug) "
                    f"VALUES ({', '.join('?' * (len(fields) + 1))})", values + [slug])
                return cur.lastrowid

            if _save("update" if article else "create", "health_information",
                     data["title"], write):
                if data["status"] == "draft":
                    # Send drafts straight to preview so they can be reviewed (FR 7.11).
                    new_id = article_id or get_db().execute(
                        "SELECT id FROM health_articles WHERE slug = ?", (slug,)).fetchone()["id"]
                    return redirect(url_for("admin.article_preview", article_id=new_id))
                return redirect(url_for("admin.articles"))
    status = 422 if errors else 200
    return render_template("admin/article_form.html", article=article, form=form,
                           errors=errors, categories=categories), status


@bp.route("/articles/<int:article_id>/preview")
def article_preview(article_id):
    article = get_db().execute(
        """SELECT a.*, c.name AS category, c.slug AS category_slug
           FROM health_articles a JOIN health_categories c ON c.id = a.category_id
           WHERE a.id = ?""", (article_id,)).fetchone()
    if article is None:
        abort(404)
    return render_template("public/health_article.html", article=article, preview=True)


@bp.route("/articles/<int:article_id>/status", methods=("POST",))
def article_status(article_id):
    article = _get_or_404("health_articles", article_id)
    new_status = request.form.get("status")
    if new_status not in ("draft", "published"):
        abort(400, description="Unknown status.")
    if new_status == "published" and not (article["source_name"] or "").strip():
        flash("This health information cannot be published until a source is added.", "error")
        return redirect(url_for("admin.article_form", article_id=article_id))

    def write(db):
        db.execute("UPDATE health_articles SET status=?, updated_at=? WHERE id=?",
                   (new_status, _now(), article_id))
        return article_id

    _save("publish" if new_status == "published" else "unpublish",
          "health_information", article["title"], write)
    return redirect(url_for("admin.articles"))


@bp.route("/articles/<int:article_id>/delete", methods=("POST",))
def article_delete(article_id):
    article = _get_or_404("health_articles", article_id)
    _save("delete", "health_information", article["title"],
          lambda db: db.execute("DELETE FROM health_articles WHERE id=?",
                                (article_id,)) and article_id)
    return redirect(url_for("admin.articles"))


# ---------------- Facilities ----------------

FACILITY_FIELDS = ("name", "facility_type", "county", "town", "address", "phone",
                   "email", "website", "summary", "source_name", "source_url",
                   "last_reviewed")


@bp.route("/facilities")
def facilities():
    q = " ".join(request.args.get("q", "").split())[:100]
    rows, _ = queries.search_facilities(q)
    return render_template("admin/facilities.html", facilities=rows, query=q)


def _service_choices():
    return get_db().execute("SELECT id, name FROM service_categories ORDER BY name").fetchall()


@bp.route("/facilities/new", methods=("GET", "POST"))
@bp.route("/facilities/<int:facility_id>/edit", methods=("GET", "POST"))
def facility_form(facility_id=None):
    facility = _get_or_404("facilities", facility_id) if facility_id else None
    services = _service_choices()
    selected = {s["id"] for s in queries.facility_services(facility_id)} if facility else set()
    form, errors = (dict(facility) if facility else {}), []

    if request.method == "POST":
        data, errors = validate_facility(request.form, {s["id"] for s in services})
        form, selected = dict(request.form), set(data["service_ids"])
        if not errors:
            values = [data[f] for f in FACILITY_FIELDS]

            def write(db):
                if facility:
                    db.execute(
                        f"UPDATE facilities SET {', '.join(f + '=?' for f in FACILITY_FIELDS)}, "
                        "updated_at=? WHERE id=?", values + [_now(), facility_id])
                    fid = facility_id
                else:
                    fid = db.execute(
                        f"INSERT INTO facilities ({', '.join(FACILITY_FIELDS)}) "
                        f"VALUES ({', '.join('?' * len(FACILITY_FIELDS))})", values).lastrowid
                db.execute("DELETE FROM facility_services WHERE facility_id=?", (fid,))
                db.executemany(
                    "INSERT INTO facility_services (facility_id, service_id) VALUES (?, ?)",
                    [(fid, sid) for sid in data["service_ids"]])
                return fid

            if _save("update" if facility else "create", "facility", data["name"], write):
                return redirect(url_for("admin.facilities"))
    return render_template("admin/facility_form.html", facility=facility, form=form,
                           errors=errors, services=services, selected=selected), \
        (422 if errors else 200)


@bp.route("/facilities/<int:facility_id>/delete", methods=("POST",))
def facility_delete(facility_id):
    facility = _get_or_404("facilities", facility_id)
    _save("delete", "facility", facility["name"],
          lambda db: db.execute("DELETE FROM facilities WHERE id=?",
                                (facility_id,)) and facility_id)
    return redirect(url_for("admin.facilities"))


# ---------------- Emergency contacts ----------------

CONTACT_FIELDS = ("name", "number", "purpose", "availability", "source_name",
                  "source_url", "verified_on", "display_order")


@bp.route("/contacts")
def contacts():
    return render_template("admin/contacts.html", contacts=queries.emergency_contacts())


@bp.route("/contacts/new", methods=("GET", "POST"))
@bp.route("/contacts/<int:contact_id>/edit", methods=("GET", "POST"))
def contact_form(contact_id=None):
    contact = _get_or_404("emergency_contacts", contact_id) if contact_id else None
    form, errors = (dict(contact) if contact else {"display_order": 100}), []
    if request.method == "POST":
        data, errors = validate_contact(request.form)
        form = dict(request.form)
        if not errors:
            values = [data[f] for f in CONTACT_FIELDS]

            def write(db):
                if contact:
                    db.execute(
                        f"UPDATE emergency_contacts SET "
                        f"{', '.join(f + '=?' for f in CONTACT_FIELDS)} WHERE id=?",
                        values + [contact_id])
                    return contact_id
                return db.execute(
                    f"INSERT INTO emergency_contacts ({', '.join(CONTACT_FIELDS)}) "
                    f"VALUES ({', '.join('?' * len(CONTACT_FIELDS))})", values).lastrowid

            if _save("update" if contact else "create", "emergency_contact",
                     data["name"], write):
                return redirect(url_for("admin.contacts"))
    return render_template("admin/contact_form.html", contact=contact, form=form,
                           errors=errors), (422 if errors else 200)


@bp.route("/contacts/<int:contact_id>/delete", methods=("POST",))
def contact_delete(contact_id):
    contact = _get_or_404("emergency_contacts", contact_id)
    _save("delete", "emergency_contact", contact["name"],
          lambda db: db.execute("DELETE FROM emergency_contacts WHERE id=?",
                                (contact_id,)) and contact_id)
    return redirect(url_for("admin.contacts"))


# ---------------- Categories (health) and services ----------------

def _category_views(kind):
    """Shared list/form/delete logic for health categories and service categories."""
    table = "health_categories" if kind == "health" else "service_categories"
    entity = "health_category" if kind == "health" else "service"
    label = "Health category" if kind == "health" else "Service"
    return table, entity, label


@bp.route("/categories", methods=("GET",))
def health_categories():
    return render_template("admin/categories.html", kind="health",
                           items=queries.categories_with_counts(published_only=False))


@bp.route("/services", methods=("GET",))
def services():
    return render_template("admin/categories.html", kind="service",
                           items=queries.services_with_counts())


@bp.route("/categories/<kind>/new", methods=("GET", "POST"))
@bp.route("/categories/<kind>/<int:item_id>/edit", methods=("GET", "POST"))
def category_form(kind, item_id=None):
    if kind not in ("health", "service"):
        abort(404)
    table, entity, label = _category_views(kind)
    item = _get_or_404(table, item_id) if item_id else None
    form, errors = (dict(item) if item else {}), []
    back = url_for("admin.health_categories" if kind == "health" else "admin.services")
    if request.method == "POST":
        data, errors = validate_category(request.form, label)
        form = dict(request.form)
        dup = get_db().execute(f"SELECT id FROM {table} WHERE lower(name) = lower(?)",
                               (data["name"] or "",)).fetchone()
        if dup and dup["id"] != item_id:
            errors.append(f"A {label.lower()} with that name already exists.")
        if not errors:
            def write(db):
                if kind == "health":
                    slug = _unique_slug(table, slugify(data["name"]), item_id)
                    if item:
                        db.execute(f"UPDATE {table} SET name=?, description=?, slug=? WHERE id=?",
                                   (data["name"], data["description"], slug, item_id))
                        return item_id
                    return db.execute(
                        f"INSERT INTO {table} (name, description, slug) VALUES (?, ?, ?)",
                        (data["name"], data["description"], slug)).lastrowid
                if item:
                    db.execute(f"UPDATE {table} SET name=?, description=? WHERE id=?",
                               (data["name"], data["description"], item_id))
                    return item_id
                return db.execute(f"INSERT INTO {table} (name, description) VALUES (?, ?)",
                                  (data["name"], data["description"])).lastrowid

            if _save("update" if item else "create", entity, data["name"], write):
                return redirect(back)
    return render_template("admin/category_form.html", kind=kind, label=label, item=item,
                           form=form, errors=errors, back=back), (422 if errors else 200)


@bp.route("/categories/<kind>/<int:item_id>/delete", methods=("POST",))
def category_delete(kind, item_id):
    if kind not in ("health", "service"):
        abort(404)
    table, entity, label = _category_views(kind)
    item = _get_or_404(table, item_id)
    back = url_for("admin.health_categories" if kind == "health" else "admin.services")
    if kind == "health":
        in_use = get_db().execute(
            "SELECT COUNT(*) FROM health_articles WHERE category_id=?", (item_id,)).fetchone()[0]
        if in_use:
            flash(f"“{item['name']}” still has {in_use} health information page(s). "
                  "Move or delete them before deleting this category.", "error")
            return redirect(back)
    _save("delete", entity, item["name"],
          lambda db: db.execute(f"DELETE FROM {table} WHERE id=?", (item_id,)) and item_id)
    return redirect(back)


# ---------------- Audit log ----------------

@bp.route("/audit")
def audit():
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = 50
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    rows = db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?",
                      (per_page, (page - 1) * per_page)).fetchall()
    return render_template("admin/audit.html", entries=rows, page=page,
                           pages=max(math.ceil(total / per_page), 1))


@bp.route("/guide")
def guide():
    return render_template("admin/guide.html")


# ---------------- Backup and restore ----------------

@bp.route("/backup")
def backup():
    return render_template("admin/backup.html")


@bp.route("/backup/download", methods=("POST",))
def backup_download():
    data = backup_to_bytes(current_app.config["DATABASE"])
    record("backup", "database", None, "Database backup downloaded")
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    return Response(data, mimetype="application/vnd.sqlite3", headers={
        "Content-Disposition": f'attachment; filename="konektya-backup-{stamp}.sqlite3"'})


@bp.route("/backup/restore", methods=("POST",))
def backup_restore():
    upload = request.files.get("backup_file")
    if not upload or not upload.filename:
        flash("Please choose a backup file to restore.", "error")
        return redirect(url_for("admin.backup"))
    if request.form.get("confirm") != "yes":
        flash("Please tick the box to confirm you want to replace the current data.", "error")
        return redirect(url_for("admin.backup"))
    username = g.admin["username"]
    # Close this request's connection before overwriting the file.
    from db import close_db
    close_db()
    try:
        restore_from_upload(upload, current_app.config["DATABASE"])
    except BackupError as e:
        flash(f"Restore failed: {e} The current data has not been changed.", "error")
        return redirect(url_for("admin.backup"))
    get_db().execute(
        "INSERT INTO audit_log (admin_id, admin_username, action, entity_type, entity_label) "
        "VALUES (NULL, ?, 'restore', 'database', ?)",
        (username, f"Restored from {upload.filename[:100]}"))
    get_db().commit()
    flash("The database was restored from the backup. If your account is not in the "
          "backup, you will need to log in with an account that is.", "success")
    return redirect(url_for("admin.dashboard"))
