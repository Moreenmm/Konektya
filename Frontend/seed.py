""" Test data for Konektya 
Every record names where it came from. The emergency contacts were checked against the listed sources."""

REVIEWED = "2026-11-24"

CA_PLAN = ("https://www.ca.go.ke/sites/default/files/2026-04/"
           "Numbering%20Plan%20Kenya%20April%202026.pdf")

# (name, number, purpose, availability, source_name, source_url, display_order)
EMERGENCY_CONTACTS = [
    ("National emergency line", "999",
     "Police, fire and ambulance emergencies anywhere in Kenya. Free to call.",
     "24 hours", "Communications Authority of Kenya - National Numbering Plan", 
CA_PLAN, 10),
    ("National emergency line (alternative)", "112",
     "Alternative national emergency number for police, fire and ambulance. Free to call.",
     "24 hours", "Communications Authority of Kenya - National Numbering Plan", 
CA_PLAN, 20),
    ("Kenya Red Cross", "1199",
     "Ambulance and emergency response, and psychosocial support. Toll-free.",
     "24 hours", "Kenya Red Cross Society - Contact us", "https://www.redcross.or.ke/?p=56", 30),
    ("National GBV helpline", "1195",
     "Tele-counselling and referral for survivors of gender-based violence. Toll-free.",
     "24 hours", "State Department for Gender and Affirmative Action - GBV Prevention and Response",
     "https://migecah.go.ke/gbv-prevention-and-response", 40),
    ("Childline Kenya", "116",
     "Report child abuse or get help for a child at risk. Toll-free.",
     "24 hours", "UNHCR Kenya - Child Protection Services", "https://help.unhcr.org/kenya/?p=280", 50),
    ("Counselling hotline", "1190",
     "General counselling support. Toll-free.",
     None, "UNHCR Kenya - Gender-Based Violence", "https://help.unhcr.org/kenya/?p=275", 60),
]


def seed(db):
    db.executemany(
        """INSERT INTO emergency_contacts (name, number, purpose, availability,
           source_name, source_url, display_order, verified_on)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [c + (REVIEWED,) for c in EMERGENCY_CONTACTS])
    db.commit()