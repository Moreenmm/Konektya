# Konektya

Konektya is a web platform that connects people living in Kenya with reliable health information and healthcare services. Users can read categorised health information, search for information and facilities, browse facilities and services, view full facility details, and reach verified emergency contacts.

Konektya **does not** diagnose conditions, prescribe medicine or replace doctors, pharmacists or other health workers.

**Stack:** HTML, CSS and JavaScript on the front end; Python with Flask on the back end; SQLite for storage. There are no external hospital systems, patient records, payment gateways or third-party clinical systems, and no CDN or external font dependencies.

---

## Quick start

Requires Python 3.10 or newer.

Run these in PowerShell from the `Frontend` folder:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python -m flask --app app seed-db        # create the database and load the test dataset
python -m flask --app app create-admin   # prompts for username, email and password
python app.py                            # http://127.0.0.1:5000
```

Use `python -m flask --app app init-db` instead of `seed-db` for an empty database.

The administrator login is at `/admin/login`. The **System** button on the home page also leads there.

## Running the tests

```bash
python -m pytest
```

The suite has 55 tests. It covers search, administrator login, content management, validation, the audit log, backup and restore, error handling, the 3-second page-response target and 10 simultaneous users. Each function can be tested on its own (NFR 14).

## Deployment

Run the app behind any WSGI server, for example:

```bash
pip install gunicorn
gunicorn -w 3 -b 0.0.0.0:8000 wsgi:app
```

Recommended environment variables:

| Variable | Purpose |
|---|---|
| `KONEKTYA_SECRET_KEY` | Session signing key. If it is not set, a random key is generated and saved to `instance/secret_key`. |
| `KONEKTYA_DATABASE` | Path to the SQLite file. The default is `instance/konektya.sqlite3`. |
| `KONEKTYA_SECURE_COOKIES=1` | Send session cookies only over HTTPS. Set this in production. |

Serve the site over HTTPS in production.

## Command-line tools

| Command | What it does |
|---|---|
| `python -m flask --app app init-db` | Creates an empty database. This deletes existing data. |
| `python -m flask --app app seed-db` | Creates the database and loads the sourced test dataset. |
| `python -m flask --app app create-admin` | Adds an administrator account. The password is stored as a salted hash. |
| `python -m flask --app app backup-db FILE` | Writes a consistent backup of the live database. |
| `python -m flask --app app restore-db FILE` | Validates a backup and restores it. |

Administrators can also download a backup and restore one from **Dashboard → Backup and restore**.

## Project structure

```
Frontend/
  app.py           app factory, config, friendly error pages; `python app.py` starts the site
  db.py            SQLite connection and CLI commands
  schema.sql       database tables
  auth.py          admin login/logout, session, login throttling
  accounts.py      the System page: shared sign-in for administrators and users, and public sign-up
  public.py        public pages: home, health info, search, facilities, services, emergency
  admin.py         dashboard and all add/edit/delete actions, audit log, backup/restore
  queries.py       shared read queries (search, listings)
  validation.py    server-side validation of every input
  security.py      CSRF protection and security headers
  audit.py         audit trail writer
  backup.py        backup and restore using SQLite's online backup API
  content.py       safe rendering of article text
  seed.py          sourced test dataset
  templates/       Jinja templates (public/, admin/, errors/, base.html, macros.html)
  static/          style.css, script.js, Logo.png
  index.html       the original static home page (not used by Flask)
  tests/           pytest suite
  pytest.ini       lets the tests import the modules in this folder
  wsgi.py          production entry point
```

## Writing health information

Article text is plain text with a small set of safe formatting rules:

- Leave a blank line between paragraphs.
- Start a line with `## ` to make a sub-heading.
- Start a line with `- ` to make a bullet point.

All text is HTML-escaped, so raw HTML cannot be injected. New pages are saved as drafts and open in a preview first. A page can only be published once it has a source.

## About the test dataset

All records were checked against the listed sources on **24 November 2026**.

- **Emergency contacts.** Each contact cites its verifying source:
  - 999 and 112: Communications Authority of Kenya numbering plan.
  - 1199: Kenya Red Cross.
  - 1195: State Department for Gender.
  - 116 and 1190: UNHCR Kenya.
- **Facilities.** There are five public referral hospitals. Details come from each hospital's official website or from government sources. Any field that could not be confirmed from such a source has been left empty, so the site shows it as "Not available".
- **Health information.** There are six pages written in plain language. Each summarises a linked World Health Organization source.

Review this data before any real-world use, and re-check it periodically (NFR 15).

---

## Requirements traceability

### Functional requirements

| ID | Requirement | Where it is implemented |
|---|---|---|
| FR 1.1 | Display health categories | `/health` (`public.health_index`) |
| FR 1.2 | View health information | `/health/<category>/<article>` |
| FR 1.3 | Display information sources | Source line on each article (`macros.source_line`) |
| FR 1.4 | Handle missing information | Empty-category message; friendly 404 page |
| FR 2.1–2.5 | Search: enter, process, display, no results, open result | `/search` with scope options, result counts and links |
| FR 2.6 | Prompt on empty search | Checked in the browser (`main.js`) and on the server (`clean_search`) |
| FR 2.7 | Clear search | "Clear search" button on every search form |
| FR 3.1, 3.3–3.5 | Facility directory, matches, no match, select | `/facilities` |
| FR 3.2 | Search facilities* | Keyword search by name, type, town, county, address or service |
| FR 3.6 | Handle empty or invalid facility search | Blank, overlong and malformed input is handled without errors (tested) |
| FR 4.1–4.4 | Facility name, location, services, contact | `/facilities/<id>` |
| FR 4.5 | Indicate missing details | "Not available" shown in italics |
| FR 4.6 | Source and last-reviewed date | Source line on the details page |
| FR 4.7 | Contact links | `tel:`, `mailto:` and website links |
| FR 5.1–5.3 | Emergency contacts with labels | `/emergency`, linked in the main navigation and the red bar on every page |
| FR 5.4 | Admin manages contacts | Admin → Emergency contacts |
| FR 6.1–6.5 | Login form, credential check, access, rejection, logout | `auth.py` |
| FR 7.1–7.6 | Add, edit and delete health information and facilities | `admin.py` |
| FR 7.7 | Validate required fields | `validation.py`, with an error summary on each form |
| FR 7.8 / 7.9 | Confirm success; report failure | Flash messages; database errors are caught and reported without technical detail |
| FR 7.10 | Source required before publishing | Enforced on save and on publish |
| FR 7.11 | Preview before publishing | Drafts open in a preview page with a Publish button |
| FR 8.1–8.6 | Navigation, mobile layout, error messages, return links, feedback | `base.html`, breadcrumbs, back links, result counts, flash messages |

\*FR 3.2 reads "Allow the user to complete a Slip" in the source document. This was taken to be a typo for "allow the user to search for facilities". Please confirm this reading.

### Non-functional requirements

| ID | How it is met |
|---|---|
| NFR 1 Security | Every `/admin` route requires login. Passwords are stored as salted hashes. Forms have CSRF tokens. Repeated failed logins are throttled. Session cookies are HttpOnly and SameSite. |
| NFR 2 Performance | Pages render on the server, use one CSS file and one small JS file, and load no external assets. Response time under 3 s is tested. |
| NFR 3 Scalability | A test runs 10 simultaneous users against a threaded server. |
| NFR 4 Usability | Plain labels, a single clear search box, and the same navigation on every page. |
| NFR 5 Reliability / maintainability | Friendly error pages. Code is organised into modules by responsibility. |
| NFR 6 Cross-browser | Standards-based HTML and CSS with no browser-specific features; every feature works without JavaScript. |
| NFR 7 Devices | Responsive layout from 320 px phones to desktops. No app install needed. |
| NFR 8 Auditability | `audit_log` table records logins, creates, updates, deletes, publishes, backups and restores. Admins can view it under Activity log. |
| NFR 9 Accessibility | Semantic headings and landmarks, a skip link, a high-visibility keyboard focus style, colour contrast at or above WCAG AA, labelled controls, and reduced-motion support. |
| NFR 10 Accuracy | Health pages need a source to publish. Emergency contacts need a source and a verification date. A separate not-medical-advice notice appears on every article. |
| NFR 11 Availability | Standard WSGI deployment. Availability depends only on the host. |
| NFR 12 Language | English interface and content. |
| NFR 13 Error handling | A global handler logs details on the server only and shows users a generic message (tested). |
| NFR 14 Testability | An app factory and isolated test database. Each function has its own tests. |
| NFR 15 Freshness | Last-reviewed and verified dates are stored and shown for every record. |
| NFR 16 Backup / recovery | Backup download, validated restore with confirmation, and CLI equivalents. |
| NFR 17 Privacy | No user accounts, cookies or tracking for general users. Search terms are never saved to the database. |
