"""Entry point for production WSGI servers, e.g. `gunicorn wsgi:app`."""
from app import create_app

app = create_app()
