from flask import Blueprint, Flask, render_template
bp = Blueprint("public", __name__)
@bp.route("/")
def home():
    return render_template("public/home.html")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)