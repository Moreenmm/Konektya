"""FR 6 and NFR 1: administrator authentication."""
from conftest import ADMIN_PASS, ADMIN_USER, AdminActions, csrf_from


def test_login_form_displayed(client):
    html = client.get("/admin/login").get_data(as_text=True)
    assert 'name="identifier"' in html and 'type="password"' in html


def test_invalid_credentials_rejected(client):
    r = AdminActions(client).login(password="wrong-password")
    assert r.status_code == 401
    assert "Incorrect username/email or password." in r.get_data(as_text=True)


def test_empty_credentials_rejected(client):
    r = AdminActions(client).login(identifier="", password="")
    assert r.status_code == 401
    assert "Please enter both" in r.get_data(as_text=True)


def test_login_with_username_or_email(client):
    assert AdminActions(client).login().headers["Location"].endswith("/admin/")
    client.get("/")  # new client state below
    c2 = client.application.test_client()
    assert AdminActions(c2).login(identifier="TESTER@konektya.test").status_code == 302


def test_admin_pages_require_login(client):
    for url in ["/admin/", "/admin/articles", "/admin/facilities/new", "/admin/contacts",
                "/admin/audit", "/admin/backup", "/admin/categories/service/new"]:
        r = client.get(url)
        assert r.status_code == 302 and "/admin/login" in r.headers["Location"], url


def test_logout_ends_session(admin, client):
    admin.post("/admin/logout")
    assert client.get("/admin/").status_code == 302


def test_password_not_stored_in_plain_text(query):
    stored = query("SELECT password_hash FROM admins WHERE username=?", (ADMIN_USER,))[0][0]
    assert ADMIN_PASS not in stored
    assert stored.startswith(("scrypt:", "pbkdf2:"))


def test_post_without_csrf_token_rejected(admin, client):
    r = client.post("/admin/facilities/new", data={"name": "No token clinic"})
    assert r.status_code == 400


def test_repeated_failures_locked_out(client):
    actions = AdminActions(client)
    for _ in range(5):
        actions.login(password="nope")
    r = actions.login()  # correct password, but locked
    assert "Too many failed login attempts" in r.get_data(as_text=True)


def test_open_redirect_blocked(client):
    token = csrf_from(client, "/admin/login")
    r = client.post("/admin/login?next=https://evil.example", data={
        "identifier": ADMIN_USER, "password": ADMIN_PASS, "csrf_token": token})
    assert r.headers["Location"].endswith("/admin/")
