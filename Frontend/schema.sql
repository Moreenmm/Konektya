-- Konektya database schema (SQLite)
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS facility_services;
DROP TABLE IF EXISTS facilities;
DROP TABLE IF EXISTS service_categories;
DROP TABLE IF EXISTS health_articles;
DROP TABLE IF EXISTS health_categories;
DROP TABLE IF EXISTS emergency_contacts;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE admins (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,            -- salted hash, never plain text (NFR 1)
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

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
    source_name   TEXT,                     -- required before publishing (FR 7.10)
    source_url    TEXT,
    status        TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    last_reviewed TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE service_categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE facilities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    facility_type TEXT,
    county        TEXT,
    town          TEXT,
    address       TEXT,
    phone         TEXT,
    email         TEXT,
    website       TEXT,
    summary       TEXT,
    source_name   TEXT,
    source_url    TEXT,
    last_reviewed TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE facility_services (
    facility_id INTEGER NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    service_id  INTEGER NOT NULL REFERENCES service_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (facility_id, service_id)
);

CREATE TABLE emergency_contacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    number        TEXT NOT NULL,
    purpose       TEXT NOT NULL,            -- label for what the number is for (FR 5.2)
    availability  TEXT,
    source_name   TEXT NOT NULL,            -- verified before publication (NFR 10)
    source_url    TEXT,
    verified_on   TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 100
);

-- Basic record of important admin actions (NFR 8)
CREATE TABLE audit_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id       INTEGER,
    admin_username TEXT NOT NULL,
    action         TEXT NOT NULL,
    entity_type    TEXT NOT NULL,
    entity_id      INTEGER,
    entity_label   TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_articles_category ON health_articles(category_id);
CREATE INDEX idx_articles_status ON health_articles(status);
CREATE INDEX idx_facilities_name ON facilities(name);
CREATE INDEX idx_audit_created ON audit_log(created_at);
