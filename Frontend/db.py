"""SQLite connection handling and command-line database tools."""
import os
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
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables (drops existing ones)."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.commit()


@click.command("init-db")
def init_db_command():
    """Create a fresh, empty database."""
    init_db()
    click.echo("Initialised an empty Konektya database.")


@click.command("seed-db")
def seed_db_command():
    """Create a fresh database and load the sourced test dataset."""
    from seed import seed

    init_db()
    seed(get_db())
    click.echo("Database created and loaded with the test dataset.")


@click.command("create-admin")
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.password_option()
def create_admin_command(username, email, password):
    """Create an administrator account (password is stored hashed)."""
    from auth import create_admin
    from validation import validate_admin

    errors = validate_admin(username, email, password)
    if errors:
        for e in errors:
            click.echo(f"Error: {e}")
        raise SystemExit(1)
    try:
        create_admin(get_db(), username, email, password)
    except sqlite3.IntegrityError:
        click.echo("Error: that username or email is already in use.")
        raise SystemExit(1)
    click.echo(f"Administrator '{username}' created.")


@click.command("backup-db")
@click.argument("destination")
def backup_db_command(destination):
    """Write a consistent copy of the database to DESTINATION."""
    from backup import write_backup

    write_backup(current_app.config["DATABASE"], destination)
    click.echo(f"Backup written to {os.path.abspath(destination)}")


@click.command("restore-db")
@click.argument("source")
def restore_db_command(source):
    """Replace the database with the backup file at SOURCE."""
    from backup import BackupError, restore_backup

    try:
        restore_backup(source, current_app.config["DATABASE"])
    except BackupError as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
    click.echo("Database restored from backup.")


def init_app(app):
    app.teardown_appcontext(close_db)
    for cmd in (init_db_command, seed_db_command, create_admin_command,
                backup_db_command, restore_db_command):
        app.cli.add_command(cmd)
