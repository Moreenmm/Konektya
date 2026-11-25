"""General user functions: FR 1-5, FR 8."""


def text(resp):
    return resp.get_data(as_text=True)


# ---- FR 8: navigation ----
def test_main_navigation_on_every_page(client):
    for url in ["/", "/health", "/facilities", "/services", "/emergency", "/search"]:
        html = text(client.get(url))
        for href in ['href="/health"', 'href="/facilities"', 'href="/services"',
                     'href="/emergency"', 'href="/"']:
            assert href in html, (url, href)


def test_home_has_search_and_purpose(client):
    html = text(client.get("/"))
    assert 'action="/search"' in html
    assert "does not diagnose" in html


# ---- FR 1: browse health information ----
def test_categories_listed(client):
    html = text(client.get("/health"))
    assert "Infectious diseases" in html and "Mental health" in html


def test_article_shows_source_and_disclaimer(client):
    html = text(client.get("/health/infectious-diseases/malaria-signs-prevention-and-testing"))
    assert "Malaria" in html
    assert "General information, not medical advice" in html
    assert "who.int" in html
    assert "Back to Infectious diseases" in html  # FR 8.5


def test_empty_category_message(client, admin):
    admin.post("/admin/categories/health/new", data={"name": "Eye health"})
    html = text(client.get("/health/eye-health"))
    assert "no published information in this category" in html


def test_missing_article_is_friendly_404(client):
    r = client.get("/health/infectious-diseases/does-not-exist")
    assert r.status_code == 404 and "Page not found" in text(r)


def test_draft_articles_are_hidden(client, query):
    query("UPDATE health_articles SET status='draft' WHERE slug LIKE 'malaria%'")
    assert client.get("/health/infectious-diseases/malaria-signs-prevention-and-testing").status_code == 404
    assert "Malaria" not in text(client.get("/search?q=malaria"))


# ---- FR 2: search ----
def test_search_finds_health_and_facilities(client):
    html = text(client.get("/search?q=emergency"))
    assert "Found" in html  # FR 8.6 feedback
    assert "Kenyatta National Hospital" in html


def test_search_multiword_and_case_insensitive(client):
    html = text(client.get("/search?q=BLOOD pressure"))
    assert "High blood pressure" in html


def test_search_no_results_message(client):
    html = text(client.get("/search?q=zzzznotathing"))
    assert "No results found" in html


def test_empty_search_prompts_for_keyword(client):
    r = client.get("/search?q=+++")
    assert r.status_code == 200
    assert "Please enter a search keyword." in text(r)


def test_search_has_clear_option(client):
    html = text(client.get("/search?q=malaria"))
    assert "Clear search" in html


def test_search_handles_wildcards_safely(client):
    r = client.get("/search?q=%25_%5C'%22;--")
    assert r.status_code == 200
    assert "No results found" in text(r)


def test_search_scope(client):
    html = text(client.get("/search?q=kisumu&scope=health"))
    assert "Jaramogi" not in html


# ---- FR 3: facility directory ----
def test_directory_lists_facilities(client):
    html = text(client.get("/facilities"))
    assert html.count("/facilities/") >= 5


def test_facility_search_by_service_and_county(client):
    assert "Jaramogi" in text(client.get("/facilities?q=dialysis")) or \
           "Jaramogi" in text(client.get("/facilities?q=kidney"))
    assert "Moi Teaching" in text(client.get("/facilities?q=uasin"))


def test_facility_search_no_match(client):
    assert "No facilities match" in text(client.get("/facilities?q=atlantis"))


def test_facility_empty_or_long_search_no_error(client):
    assert client.get("/facilities?q=").status_code == 200
    assert client.get("/facilities?q=" + "a" * 500).status_code == 200
    assert client.get("/facilities?page=abc").status_code == 200


# ---- FR 4: facility details ----
def test_facility_detail_fields(client, query):
    fid = query("SELECT id FROM facilities WHERE name LIKE 'Kenyatta National%'")[0][0]
    html = text(client.get(f"/facilities/{fid}"))
    assert "Hospital Road" in html
    assert 'href="tel:0202726300"' in html  # FR 4.7
    assert "Emergency care" in html
    assert "Last reviewed" in html


def test_missing_details_marked_not_available(client, query):
    fid = query("SELECT id FROM facilities WHERE name LIKE 'Jaramogi%'")[0][0]
    html = text(client.get(f"/facilities/{fid}"))
    assert html.count("Not available") >= 3


# ---- Services ----
def test_services_link_to_facilities(client, query):
    sid = query("SELECT id FROM service_categories WHERE name='Emergency care'")[0][0]
    html = text(client.get(f"/services/{sid}"))
    assert "Kenyatta National Hospital" in html and "Coast General" in html
    assert "Kidney care" in text(client.get("/services?q=kidney"))


# ---- FR 5: emergency contacts ----
def test_emergency_contacts_labelled_and_callable(client):
    html = text(client.get("/emergency"))
    for number in ("999", "112", "1199", "1195", "116"):
        assert f'href="tel:{number}"' in html
    assert "Verified" in html and "Kenya Red Cross" in html


# ---- NFR 13 / security ----
def test_unexpected_error_hides_details(app, client):
    @app.route("/boom")
    def boom():
        raise RuntimeError("secret database path /var/db")
    r = client.get("/boom")
    assert r.status_code == 500
    assert "secret" not in text(r) and "Traceback" not in text(r)


def test_security_headers(client):
    r = client.get("/")
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]


def test_no_cookies_set_for_general_users(client):
    """NFR 17: browsing does not create a session or track users."""
    r = client.get("/search?q=malaria")
    assert "Set-Cookie" not in r.headers
