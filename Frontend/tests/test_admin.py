"""FR 5.4, FR 7, NFR 8, NFR 16: content administration."""
import io
import sqlite3

ARTICLE = {
    "title": "Typhoid fever basics", "category_id": "1",
    "summary": "What typhoid is.", "body": "Typhoid spreads through contaminated food.\n\n- Wash hands",
    "source_name": "", "source_url": "", "last_reviewed": "", "status": "draft",
}


def text(r):
    return r.get_data(as_text=True)


def test_dashboard_shows_counts(admin, client):
    html = text(client.get("/admin/"))
    assert "Published health pages" in html and "Recent activity" in html


# ---- Health information ----
def test_add_draft_preview_then_publish(admin, client, query):
    r = admin.post("/admin/articles/new", data=ARTICLE, follow_redirects=True)
    html = text(r)
    assert "was added successfully" in html  # FR 7.8
    assert "Preview." in html                # FR 7.11
    aid = query("SELECT id FROM health_articles WHERE title='Typhoid fever basics'")[0][0]
    # Not public while draft
    assert "Typhoid" not in text(client.get("/search?q=typhoid"))
    # Cannot publish without a source (FR 7.10)
    r = admin.post(f"/admin/articles/{aid}/status", data={"status": "published"}, follow_redirects=True)
    assert "cannot be published until a source is added" in text(r)
    # Add source, then publish
    data = dict(ARTICLE, source_name="WHO typhoid fact sheet",
                source_url="https://www.who.int/news-room/fact-sheets/detail/typhoid")
    admin.post(f"/admin/articles/{aid}/edit", data=data)
    r = admin.post(f"/admin/articles/{aid}/status", data={"status": "published"}, follow_redirects=True)
    assert "was published successfully" in text(r)
    assert "Typhoid fever basics" in text(client.get("/search?q=typhoid"))


def test_publish_directly_requires_source(admin):
    r = admin.post("/admin/articles/new", data=dict(ARTICLE, status="published"))
    assert r.status_code == 422
    assert "A source is required" in text(r)


def test_required_fields_validated(admin):
    r = admin.post("/admin/articles/new", data={"status": "draft"})
    html = text(r)
    assert r.status_code == 422
    for msg in ("Title is required.", "Summary is required.", "Content is required.",
                "Please choose a valid category."):
        assert msg in html


def test_invalid_values_rejected(admin):
    r = admin.post("/admin/articles/new", data=dict(
        ARTICLE, source_url="javascript:alert(1)", last_reviewed="2999-01-01"))
    html = text(r)
    assert "must be a full web address" in html and "cannot be in the future" in html


def test_article_content_is_escaped(admin, client, query):
    data = dict(ARTICLE, body="<script>alert(1)</script>", source_name="Test", status="published")
    admin.post("/admin/articles/new", data=data)
    html = text(client.get("/health/infectious-diseases/typhoid-fever-basics"))
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


def test_edit_and_delete_article(admin, query):
    aid = query("SELECT id FROM health_articles LIMIT 1")[0][0]
    row = dict(query("SELECT * FROM health_articles WHERE id=?", (aid,))[0])
    row.update(title="Edited title", status="published", category_id=str(row["category_id"]))
    row = {k: ("" if v is None else str(v)) for k, v in row.items()}
    r = admin.post(f"/admin/articles/{aid}/edit", data=row, follow_redirects=True)
    assert "was updated successfully" in text(r)
    r = admin.post(f"/admin/articles/{aid}/delete", follow_redirects=True)
    assert "was deleted successfully" in text(r)
    assert not query("SELECT id FROM health_articles WHERE id=?", (aid,))


# ---- Facilities ----
def test_facility_crud_with_services(admin, client, query):
    sid = query("SELECT id FROM service_categories WHERE name='Eye care'")[0][0]
    r = admin.post("/admin/facilities/new", data={
        "name": "Test Eye Clinic", "county": "Nakuru", "town": "Nakuru",
        "phone": "+254 700 000000", "service_ids": [str(sid)]}, follow_redirects=True)
    assert "was added successfully" in text(r)
    fid = query("SELECT id FROM facilities WHERE name='Test Eye Clinic'")[0][0]
    html = text(client.get(f"/facilities/{fid}"))
    assert "Eye care" in html and "Nakuru County" in html
    r = admin.post(f"/admin/facilities/{fid}/edit", data={"name": "Test Eye Clinic Renamed"},
                   follow_redirects=True)
    assert "was updated successfully" in text(r)
    assert not query("SELECT * FROM facility_services WHERE facility_id=?", (fid,))
    r = admin.post(f"/admin/facilities/{fid}/delete", follow_redirects=True)
    assert "was deleted successfully" in text(r)


def test_facility_validation(admin):
    r = admin.post("/admin/facilities/new", data={
        "name": "", "email": "not-an-email", "phone": "call me", "website": "www.x.com",
        "service_ids": ["99999"]})
    html = text(r)
    assert r.status_code == 422
    assert "Facility name is required." in html
    assert "valid email" in html and "Phone number may only contain" in html
    assert "does not exist" in html


# ---- Emergency contacts (FR 5.4) ----
def test_contact_crud(admin, client, query):
    r = admin.post("/admin/contacts/new", data={
        "name": "Test line", "number": "0800 000 000", "purpose": "Testing",
        "source_name": "Test source", "verified_on": "2026-01-01", "display_order": "5"},
        follow_redirects=True)
    assert "was added successfully" in text(r)
    assert "Test line" in text(client.get("/emergency"))
    cid = query("SELECT id FROM emergency_contacts WHERE name='Test line'")[0][0]
    admin.post(f"/admin/contacts/{cid}/delete", follow_redirects=True)
    assert "Test line" not in text(client.get("/emergency"))


def test_contact_requires_verification(admin):
    r = admin.post("/admin/contacts/new", data={"name": "X", "number": "123", "purpose": "Y"})
    html = text(r)
    assert "Source name is required." in html and "Date verified is required." in html


# ---- Categories and services ----
def test_category_with_pages_cannot_be_deleted(admin, query):
    cid = query("SELECT id FROM health_categories WHERE slug='mental-health'")[0][0]
    r = admin.post(f"/admin/categories/health/{cid}/delete", follow_redirects=True)
    assert "still has" in text(r)
    assert query("SELECT id FROM health_categories WHERE id=?", (cid,))


def test_duplicate_service_rejected(admin):
    r = admin.post("/admin/categories/service/new", data={"name": "emergency care"})
    assert "already exists" in text(r)


# ---- FR 7.9: failed operations reported ----
def test_database_failure_reported(admin, app, monkeypatch):
    import admin as admin_mod

    def broken(*a, **k):
        raise sqlite3.OperationalError("disk I/O error")
    monkeypatch.setattr(admin_mod, "record", broken)
    r = admin.post("/admin/categories/service/new", data={"name": "Physiotherapy"},
                   follow_redirects=True)
    html = text(r)
    assert "could not be created" in html and "disk I/O" not in html


# ---- NFR 8: audit trail ----
def test_changes_are_logged(admin, client, query):
    admin.post("/admin/categories/service/new", data={"name": "Dental care"})
    rows = query("SELECT admin_username, action, entity_type, entity_label FROM audit_log "
                 "ORDER BY id DESC LIMIT 1")
    assert tuple(rows[0]) == ("tester", "create", "service", "Dental care")
    assert "Dental care" in text(client.get("/admin/audit"))


# ---- NFR 16: backup and restore ----
def test_backup_and_restore(admin, client, query, tmp_path):
    r = admin.post("/admin/backup/download")
    assert r.status_code == 200 and r.data.startswith(b"SQLite format 3")
    backup = r.data
    admin.post("/admin/categories/service/new", data={"name": "Added after backup"})
    assert query("SELECT 1 FROM service_categories WHERE name='Added after backup'")
    r = admin.post("/admin/backup/restore", data={
        "confirm": "yes", "backup_file": (io.BytesIO(backup), "backup.sqlite3")},
        content_type="multipart/form-data", follow_redirects=True)
    assert "was restored" in text(r)
    assert not query("SELECT 1 FROM service_categories WHERE name='Added after backup'")


def test_restore_rejects_invalid_file(admin, query):
    before = query("SELECT COUNT(*) FROM facilities")[0][0]
    r = admin.post("/admin/backup/restore", data={
        "confirm": "yes", "backup_file": (io.BytesIO(b"not a database"), "x.sqlite3")},
        content_type="multipart/form-data", follow_redirects=True)
    assert "Restore failed" in text(r)
    assert query("SELECT COUNT(*) FROM facilities")[0][0] == before


def test_restore_requires_confirmation(admin):
    r = admin.post("/admin/backup/restore", data={
        "backup_file": (io.BytesIO(b"x"), "x.sqlite3")},
        content_type="multipart/form-data", follow_redirects=True)
    assert "tick the box" in text(r)
