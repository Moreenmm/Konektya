"""NFR 2 (pages within 3 s) and NFR 3 (10 simultaneous users) on the test dataset."""
import threading
import time
import urllib.request

from werkzeug.serving import make_server

PAGES = ["/", "/health", "/search?q=malaria", "/facilities?q=nairobi", "/facilities/1",
         "/services", "/emergency"]


def test_pages_respond_within_three_seconds(client):
    for url in PAGES:
        start = time.perf_counter()
        assert client.get(url).status_code == 200
        assert time.perf_counter() - start < 3, url


def test_ten_simultaneous_users(app):
    server = make_server("127.0.0.1", 0, app, threaded=True)
    port = server.server_port
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    results, errors = [], []

    def user():
        try:
            for url in PAGES:
                start = time.perf_counter()
                with urllib.request.urlopen(f"http://127.0.0.1:{port}{url}", timeout=10) as r:
                    assert r.status == 200
                results.append(time.perf_counter() - start)
        except Exception as e:  # pragma: no cover
            errors.append(e)

    users = [threading.Thread(target=user) for _ in range(10)]
    for u in users:
        u.start()
    for u in users:
        u.join()
    server.shutdown()
    assert not errors
    assert len(results) == 10 * len(PAGES)
    assert max(results) < 3
