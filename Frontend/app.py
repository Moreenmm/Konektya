import os
from datetime import date
from flask import Blueprint, Flask, render_template
import db

bp = Blueprint("public", __name__)
@bp.route("/")
def home():
    return render_template("public/home.html")

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