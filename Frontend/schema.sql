-- Konektya's database tables(SQLite)
DROP TABLE IF EXISTS emergency_contacts;

--  Emergency Contacts
CREATE TABLE emergency_contacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    number        TEXT NOT NULL,
    purpose       TEXT NOT NULL,
    availability  TEXT,
    source_name   TEXT NOT NULL,
    source_url    TEXT,
    verified_on   TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 100
);

DROP TABLE IF EXISTS health_articles;
DROP TABLE IF EXISTS health_categories;

CREATE TABLE health_categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    slug        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE health_articles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER NOT NULL REFERENCES health_categories(id) ON DELETE RESTRICT,
    title         TEXT NOT NULL,
    slug          TEXT NOT NULL UNIQUE,
    summary       TEXT NOT NULL,
    body          TEXT NOT NULL,
    source_name   TEXT,
    source_url    TEXT,
    status        TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    last_reviewed TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);