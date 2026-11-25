import os
from datetime import date
from flask import Blueprint, Flask, render_template
from flask import Blueprint, Flask, abort, render_template
import db

bp = Blueprint("public", __name__)
@bp.route("/")
def home():
    return render_template("public/home.html", categories=categories_with_counts())


def categories_with_counts():
    """Every health category, with how many published pages it has."""
    return db.get_db().execute(
        """SELECT c.*, COUNT(a.id) AS article_count
           FROM health_categories c
           LEFT JOIN health_articles a ON a.category_id = c.id AND a.status = 'published'
           GROUP BY c.id ORDER BY c.name""").fetchall()


@bp.route("/health")
def health_index():
    """FR 1.1: list the health categories."""
    return render_template("public/health_index.html", categories=categories_with_counts())


@bp.route("/health/<slug>")
def health_category(slug):
    """One category and its published pages. Unknown category -> 404 page (FR 1.4)."""
    category = db.get_db().execute(
        "SELECT * FROM health_categories WHERE slug = ?", (slug,)).fetchone()
    if category is None:
        abort(404)
    articles = db.get_db().execute(
        """SELECT id, title, slug, summary FROM health_articles
           WHERE category_id = ? AND status = 'published' ORDER BY title""",
        (category["id"],)).fetchall()
    return render_template("public/health_category.html", category=category, articles=articles)

@bp.route("/emergency")
def emergency():
    contacts = db.get_db().execute(
         "SELECT * FROM emergency_contacts ORDER BY display_order, name").fetchall()
    return render_template("public/emergency.html", contacts=contacts)

def nice_date(value):
    """Turn 2026-11-24 into 24 November 2026. Used in templates as {{ value|nice_date }}."""
    if not value:
        return ""
    try:
        d = date.fromisoformat(str(value)[:10])
    except ValueError:
        return value
    return f"{d.day} {d.strftime('%B %Y')}"

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "konektya.sqlite3")
    db.init_app(app)
    app.register_blueprint(bp)
    app.jinja_env.filters["nice_date"] = nice_date
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)