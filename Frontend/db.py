""" SQLite connection handling and the seed-db command"""
import sqlite3

import click
from flask import current_app, g


def get_db():
    """Return a connection for the current request, opening one if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(_exc=None):
    """Close the connection when the request ends."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables from schema.sql (drops existing ones)."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.commit()


@click.command("seed-db")
def seed_db_command():
    """Create a fresh database and load the test data."""
    from seed import seed

    init_db()
    seed(get_db())
    click.echo("Database created and loaded with the test dataset.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(seed_db_command)