"""Public pages for general users (no login, no personal data collected - NFR 17)."""
import math

from flask import Blueprint, abort, current_app, render_template, request

import queries
from db import get_db
from validation import clean_search

bp = Blueprint("public", __name__)


@bp.route("/")
def home():
    db = get_db()
    return render_template(
        "public/home.html",
        categories=queries.categories_with_counts(),
        top_contacts=db.execute(
            "SELECT * FROM emergency_contacts ORDER BY display_order, name LIMIT 3"
        ).fetchall(),
        counts={
            "articles": db.execute(
                "SELECT COUNT(*) FROM health_articles WHERE status='published'").fetchone()[0],
            "facilities": db.execute("SELECT COUNT(*) FROM facilities").fetchone()[0],
            "services": db.execute("SELECT COUNT(*) FROM service_categories").fetchone()[0],
            "contacts": db.execute("SELECT COUNT(*) FROM emergency_contacts").fetchone()[0],
        },
    )


@bp.route("/about")
def about():
    return render_template("public/about.html")


# ---------- Health information (FR 1) ----------

@bp.route("/health")
def health_index():
    return render_template("public/health_index.html",
                           categories=queries.categories_with_counts())


@bp.route("/health/<slug>")
def health_category(slug):
    db = get_db()
    category = db.execute(
        "SELECT * FROM health_categories WHERE slug = ?", (slug,)).fetchone()
    if category is None:
        abort(404)
    articles = db.execute(
        """SELECT id, title, slug, summary, last_reviewed FROM health_articles
           WHERE category_id = ? AND status = 'published' ORDER BY title""",
        (category["id"],),
    ).fetchall()
    return render_template("public/health_category.html",
                           category=category, articles=articles)


@bp.route("/health/<cat_slug>/<slug>")
def health_article(cat_slug, slug):
    article = get_db().execute(
        """SELECT a.*, c.name AS category, c.slug AS category_slug
           FROM health_articles a JOIN health_categories c ON c.id = a.category_id
           WHERE a.slug = ? AND c.slug = ? AND a.status = 'published'""",
        (slug, cat_slug),
    ).fetchone()
    if article is None:
        abort(404)
    return render_template("public/health_article.html", article=article, preview=False)


# ---------- Search (FR 2) ----------

@bp.route("/search")
def search():
    submitted = "q" in request.args
    scope = request.args.get("scope", "all")
    if scope not in ("all", "health", "facilities"):
        scope = "all"
    query, error = clean_search(request.args.get("q"))
    articles, facilities = [], []
    if submitted and query:
        if scope in ("all", "health"):
            articles = queries.search_articles(query)
        if scope in ("all", "facilities"):
            facilities, _ = queries.search_facilities(query, limit=50)
    return render_template(
        "public/search.html", query=query, scope=scope, submitted=submitted,
        error=error if submitted else None, articles=articles, facilities=facilities,
    )


# ---------- Facilities (FR 3, FR 4) ----------

@bp.route("/facilities")
def facilities():
    submitted = "q" in request.args
    query, error = clean_search(request.args.get("q"))
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = current_app.config["PER_PAGE"]
    rows, total = queries.search_facilities(query, limit=per_page,
                                            offset=(page - 1) * per_page)
    return render_template(
        "public/facilities.html", facilities=rows, total=total, query=query,
        submitted=submitted, error=error if submitted else None,
        page=page, pages=max(math.ceil(total / per_page), 1),
    )


@bp.route("/facilities/<int:facility_id>")
def facility_detail(facility_id):
    facility = get_db().execute(
        "SELECT * FROM facilities WHERE id = ?", (facility_id,)).fetchone()
    if facility is None:
        abort(404)
    return render_template("public/facility_detail.html", facility=facility,
                           services=queries.facility_services(facility_id))


# ---------- Healthcare services ----------

@bp.route("/services")
def services():
    submitted = "q" in request.args
    query, error = clean_search(request.args.get("q"))
    return render_template(
        "public/services.html", services=queries.services_with_counts(query),
        query=query, submitted=submitted, error=error if submitted else None,
    )


@bp.route("/services/<int:service_id>")
def service_detail(service_id):
    db = get_db()
    service = db.execute(
        "SELECT * FROM service_categories WHERE id = ?", (service_id,)).fetchone()
    if service is None:
        abort(404)
    facilities = db.execute(
        """SELECT f.* FROM facilities f
           JOIN facility_services fs ON fs.facility_id = f.id
           WHERE fs.service_id = ? ORDER BY f.name""",
        (service_id,),
    ).fetchall()
    return render_template("public/service_detail.html",
                           service=service, facilities=facilities)


# ---------- Emergency contacts (FR 5) ----------

@bp.route("/emergency")
def emergency():
    return render_template("public/emergency.html",
                           contacts=queries.emergency_contacts())
