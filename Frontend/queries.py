"""Read queries shared by the public site and the admin dashboard."""
from db import get_db


def _like(term):
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _terms_clause(terms, fields):
    """Every term must appear in at least one of the fields (case-insensitive)."""
    clauses, params = [], []
    for term in terms:
        ors = " OR ".join(f"{f} LIKE ? ESCAPE '\\'" for f in fields)
        clauses.append(f"({ors})")
        params.extend([_like(term)] * len(fields))
    return " AND ".join(clauses) or "1=1", params


def search_articles(query, limit=50):
    terms = query.split()[:8]
    where, params = _terms_clause(
        terms, ["a.title", "a.summary", "a.body", "c.name"])
    return get_db().execute(
        f"""SELECT a.id, a.title, a.slug, a.summary, c.name AS category, c.slug AS category_slug
            FROM health_articles a JOIN health_categories c ON c.id = a.category_id
            WHERE a.status = 'published' AND {where}
            ORDER BY (a.title LIKE ? ESCAPE '\\') DESC, a.title
            LIMIT ?""",
        params + [_like(query), limit],
    ).fetchall()


FACILITY_SERVICE_NAMES = (
    "(SELECT group_concat(s.name, ', ') FROM facility_services fs "
    "JOIN service_categories s ON s.id = fs.service_id WHERE fs.facility_id = f.id)"
)


def search_facilities(query, limit=None, offset=0):
    terms = query.split()[:8] if query else []
    where, params = _terms_clause(
        terms, ["f.name", "f.facility_type", "f.county", "f.town", "f.address",
                "f.summary", FACILITY_SERVICE_NAMES])
    sql = f"""SELECT f.*, {FACILITY_SERVICE_NAMES} AS service_names
              FROM facilities f WHERE {where} ORDER BY f.name"""
    count = get_db().execute(
        f"SELECT COUNT(*) FROM facilities f WHERE {where}", params).fetchone()[0]
    if limit:
        sql += " LIMIT ? OFFSET ?"
        params = params + [limit, offset]
    return get_db().execute(sql, params).fetchall(), count


def facility_services(facility_id):
    return get_db().execute(
        """SELECT s.id, s.name FROM service_categories s
           JOIN facility_services fs ON fs.service_id = s.id
           WHERE fs.facility_id = ? ORDER BY s.name""",
        (facility_id,),
    ).fetchall()


def services_with_counts(query=""):
    terms = query.split()[:8] if query else []
    where, params = _terms_clause(terms, ["s.name", "s.description"])
    return get_db().execute(
        f"""SELECT s.*, COUNT(fs.facility_id) AS facility_count
            FROM service_categories s
            LEFT JOIN facility_services fs ON fs.service_id = s.id
            WHERE {where} GROUP BY s.id ORDER BY s.name""",
        params,
    ).fetchall()


def categories_with_counts(published_only=True):
    status = "AND a.status = 'published'" if published_only else ""
    return get_db().execute(
        f"""SELECT c.*, COUNT(a.id) AS article_count
            FROM health_categories c
            LEFT JOIN health_articles a ON a.category_id = c.id {status}
            GROUP BY c.id ORDER BY c.name"""
    ).fetchall()


def emergency_contacts():
    return get_db().execute(
        "SELECT * FROM emergency_contacts ORDER BY display_order, name").fetchall()
