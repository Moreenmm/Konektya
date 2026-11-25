"""Basic audit trail of important administrator actions (NFR 8)."""
from flask import g

from db import get_db


def record(action, entity_type, entity_id=None, entity_label=None, commit=True):
    admin = g.get("admin")
    db = get_db()
    db.execute(
        "INSERT INTO audit_log (admin_id, admin_username, action, entity_type, "
        "entity_id, entity_label) VALUES (?, ?, ?, ?, ?, ?)",
        (admin["id"] if admin else None,
         admin["username"] if admin else "system",
         action, entity_type, entity_id, (entity_label or "")[:200]),
    )
    if commit:
        db.commit()
