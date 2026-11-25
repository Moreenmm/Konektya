"""Server-side checks on every record before it is written (FR 7.7, FR 7.10)."""
import re
from datetime import date

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+()\s/,.\-]+$")
URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.IGNORECASE)
SEARCH_MAX = 100


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80] or "item"


def _text(form, field, label, errors, required=False, max_len=200):
    value = (form.get(field) or "").strip()
    if required and not value:
        errors.append(f"{label} is required.")
    elif len(value) > max_len:
        errors.append(f"{label} must be {max_len} characters or fewer.")
    return value or None


def _url(form, field, label, errors):
    value = _text(form, field, label, errors, max_len=500)
    if value and not URL_RE.match(value):
        errors.append(f"{label} must be a full web address starting with http:// or https://.")
    return value


def _date(form, field, label, errors, required=False):
    value = _text(form, field, label, errors, required=required, max_len=10)
    if value:
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            errors.append(f"{label} must be a valid date (YYYY-MM-DD).")
            return value
        if parsed > date.today():
            errors.append(f"{label} cannot be in the future.")
    return value


def _phone(form, field, label, errors, required=False):
    value = _text(form, field, label, errors, required=required, max_len=100)
    if value and not PHONE_RE.match(value):
        errors.append(f"{label} may only contain digits, spaces and + ( ) - / , characters.")
    return value


def clean_search(raw):
    """Normalise a search query. Returns (query, error)."""
    q = " ".join((raw or "").split())
    if not q:
        return "", "Please enter a search keyword."
    if len(q) > SEARCH_MAX:
        return q[:SEARCH_MAX], f"Search terms can be at most {SEARCH_MAX} characters."
    return q, None


def validate_article(form, valid_category_ids):
    errors = []
    data = {
        "title": _text(form, "title", "Title", errors, required=True, max_len=150),
        "summary": _text(form, "summary", "Summary", errors, required=True, max_len=300),
        "body": _text(form, "body", "Content", errors, required=True, max_len=20000),
        "source_name": _text(form, "source_name", "Source name", errors, max_len=200),
        "source_url": _url(form, "source_url", "Source link", errors),
        "last_reviewed": _date(form, "last_reviewed", "Last reviewed date", errors),
        "status": (form.get("status") or "draft").strip(),
    }
    try:
        data["category_id"] = int(form.get("category_id", ""))
        if data["category_id"] not in valid_category_ids:
            raise ValueError
    except ValueError:
        data["category_id"] = None
        errors.append("Please choose a valid category.")
    if data["status"] not in ("draft", "published"):
        errors.append("Status must be Draft or Published.")
        data["status"] = "draft"
    if data["status"] == "published" and not data["source_name"]:
        errors.append("A source is required before health information can be published.")
    return data, errors


def validate_facility(form, valid_service_ids):
    errors = []
    data = {
        "name": _text(form, "name", "Facility name", errors, required=True, max_len=150),
        "facility_type": _text(form, "facility_type", "Facility type", errors, max_len=80),
        "county": _text(form, "county", "County", errors, max_len=60),
        "town": _text(form, "town", "Town", errors, max_len=80),
        "address": _text(form, "address", "Address", errors, max_len=250),
        "phone": _phone(form, "phone", "Phone number", errors),
        "email": _text(form, "email", "Email", errors, max_len=150),
        "website": _url(form, "website", "Website", errors),
        "summary": _text(form, "summary", "Summary", errors, max_len=500),
        "source_name": _text(form, "source_name", "Source name", errors, max_len=200),
        "source_url": _url(form, "source_url", "Source link", errors),
        "last_reviewed": _date(form, "last_reviewed", "Last reviewed date", errors),
    }
    if data["email"] and not EMAIL_RE.match(data["email"]):
        errors.append("Email must be a valid email address.")
    services = []
    for raw in form.getlist("service_ids"):
        try:
            sid = int(raw)
        except ValueError:
            continue
        if sid in valid_service_ids:
            services.append(sid)
        else:
            errors.append("One of the selected services does not exist.")
    data["service_ids"] = sorted(set(services))
    return data, errors


def validate_contact(form):
    errors = []
    data = {
        "name": _text(form, "name", "Name", errors, required=True, max_len=120),
        "number": _phone(form, "number", "Number", errors, required=True),
        "purpose": _text(form, "purpose", "Purpose", errors, required=True, max_len=300),
        "availability": _text(form, "availability", "Availability", errors, max_len=100),
        "source_name": _text(form, "source_name", "Source name", errors, required=True, max_len=200),
        "source_url": _url(form, "source_url", "Source link", errors),
        "verified_on": _date(form, "verified_on", "Date verified", errors, required=True),
    }
    try:
        data["display_order"] = int(form.get("display_order") or 100)
        if not 0 <= data["display_order"] <= 9999:
            raise ValueError
    except ValueError:
        data["display_order"] = 100
        errors.append("Display order must be a whole number between 0 and 9999.")
    return data, errors


def validate_category(form, label="Category"):
    errors = []
    data = {
        "name": _text(form, "name", f"{label} name", errors, required=True, max_len=80),
        "description": _text(form, "description", "Description", errors, max_len=300),
    }
    return data, errors


def validate_admin(username, email, password):
    errors = []
    if not username or not re.fullmatch(r"[A-Za-z0-9_.-]{3,40}", username):
        errors.append("Username must be 3-40 letters, numbers, dots, dashes or underscores.")
    if not email or not EMAIL_RE.match(email):
        errors.append("Email must be a valid email address.")
    if not password or len(password) < 10:
        errors.append("Password must be at least 10 characters long.")
    return errors
