"""Safe rendering of health article text.

Admins write plain text with a tiny, safe markup:
  * a blank line starts a new paragraph
  * a line starting with "## " is a sub-heading
  * lines starting with "- " form a bullet list
Everything is HTML-escaped first, so no raw HTML can reach the page.
"""
from datetime import date

from markupsafe import Markup, escape


def render_body(text):
    if not text:
        return Markup("")
    out = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        lines = [ln.rstrip() for ln in block.strip().split("\n") if ln.strip()]
        if not lines:
            continue
        para, items = [], []

        def flush_para():
            if para:
                out.append("<p>" + "<br>".join(str(escape(p)) for p in para) + "</p>")
                para.clear()

        def flush_list():
            if items:
                out.append("<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>")
                items.clear()

        for ln in lines:
            if ln.startswith("## "):
                flush_para(); flush_list()
                out.append(f"<h3>{escape(ln[3:].strip())}</h3>")
            elif ln.lstrip().startswith("- "):
                flush_para()
                items.append(ln.lstrip()[2:].strip())
            else:
                flush_list()
                para.append(ln)
        flush_para(); flush_list()
    return Markup("\n".join(out))


def format_date(value):
    """Turn 2026-11-24 into 24 November 2026; leave anything else unchanged."""
    if not value:
        return ""
    try:
        d = date.fromisoformat(str(value)[:10])
    except ValueError:
        return value
    return f"{d.day} {d.strftime('%B %Y')}"
