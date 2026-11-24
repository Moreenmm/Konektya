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
