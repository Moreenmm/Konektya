import re

import pytest

from app import create_app
from auth import _failures, create_admin
from db import get_db, init_db
from seed import seed

ADMIN_USER = "tester"
ADMIN_EMAIL = "tester@konektya.test"
ADMIN_PASS = "correct-horse-battery"


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE": str(tmp_path / "test.sqlite3"),
    })
    with app.app_context():
        init_db()
        seed(get_db())
        create_admin(get_db(), ADMIN_USER, ADMIN_EMAIL, ADMIN_PASS)
    _failures.clear()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_from(client, url):
    html = client.get(url).get_data(as_text=True)
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert m, f"no CSRF token on {url}"
    return m.group(1)


class AdminActions:
    def __init__(self, client):
        self.client = client

    def login(self, identifier=ADMIN_USER, password=ADMIN_PASS):
        token = csrf_from(self.client, "/admin/login")
        return self.client.post("/admin/login", data={
            "identifier": identifier, "password": password, "csrf_token": token})

    def token(self):
        return csrf_from(self.client, "/admin/")

    def post(self, url, data=None, **kw):
        data = dict(data or {})
        data["csrf_token"] = self.token()
        return self.client.post(url, data=data, **kw)


@pytest.fixture
def admin(client):
    actions = AdminActions(client)
    assert actions.login().status_code == 302
    return actions


@pytest.fixture
def query(app):
    def run(sql, params=()):
        with app.app_context():
            db = get_db()
            rows = db.execute(sql, params).fetchall()
            db.commit()
            return rows
    return run
