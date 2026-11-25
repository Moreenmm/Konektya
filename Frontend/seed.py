""" Test data for Konektya 
Every record names where it came from. The emergency contacts were checked against the listed sources."""
import re

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

HEALTH_CATEGORIES = [
    ("Infectious diseases", "infectious-diseases",
     "Illnesses caused by germs such as parasites, bacteria and viruses, and how to prevent them."),
    ("Long-term conditions", "long-term-conditions",
     "Conditions such as high blood pressure that develop over time and need ongoing care."),
    ("Maternal and child health", "maternal-and-child-health",
     "Information for pregnancy, birth and the early years of a child's life."),
    ("Mental health", "mental-health",
     "Emotional wellbeing, common mental health conditions and where to find support."),
    ("Sexual and reproductive health", "sexual-and-reproductive-health",
     "HIV, sexually transmitted infections, family planning and testing services."),
]

ARTICLES = [
    {
        "category": "infectious-diseases",
        "title": "Malaria: signs, prevention and testing",
        "summary": "Malaria is spread by mosquito bites and can become serious quickly. "
                   "Learn the common signs and how to lower your risk.",
        "body": """Malaria is an illness caused by a parasite that is passed to people through the bites of infected female Anopheles mosquitoes. It cannot spread directly from one person to another.

## Common signs
- Fever, chills and sweating
- Headache and body aches
- Tiredness, nausea or vomiting

Signs usually start 10 to 15 days after an infected bite. Young children and pregnant women are more likely to become seriously ill.

## Lowering your risk
- Sleep under an insecticide-treated mosquito net every night
- Remove standing water around your home where mosquitoes breed
- Cover arms and legs in the evening and use repellent where available

## Getting tested
Malaria can only be confirmed with a test, such as a rapid diagnostic test at a health facility. If you or your child has a fever, especially in an area where malaria is common, visit a health facility promptly so a health worker can test and advise you.""",
        "source_name": "World Health Organization - Malaria fact sheet",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/malaria",
    },
    {
        "category": "infectious-diseases",
        "title": "Cholera: how it spreads and how to stay safe",
        "summary": "Cholera spreads through contaminated water and food. Safe water, "
                   "hand washing and quick care save lives.",
        "body": """Cholera is an infection of the gut caused by eating food or drinking water contaminated with the cholera bacterium. It often spreads where clean water and sanitation are limited.

## Common signs
- Sudden, watery diarrhoea, sometimes described as "rice-water" stools
- Vomiting
- Signs of dehydration such as thirst, a dry mouth and passing little urine

Many people have mild illness, but severe cholera can cause dangerous dehydration within hours.

## Staying safe
- Drink water that has been boiled, chlorinated or comes from a safe source
- Wash hands with soap and clean water after using the toilet and before handling food
- Eat food that is cooked well and served hot
- Use a toilet or latrine and keep it clean

## When to seek care
Anyone with severe watery diarrhoea should go to a health facility straight away. Oral rehydration solution (ORS) can be started on the way.""",
        "source_name": "World Health Organization - Cholera fact sheet",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/cholera",
    },
    {
        "category": "long-term-conditions",
        "title": "High blood pressure (hypertension)",
        "summary": "High blood pressure often has no symptoms. A quick check at a health "
                   "facility is the only way to know your numbers.",
        "body": """Blood pressure is the force of blood pushing against the walls of your blood vessels. When it stays too high over time, it is called hypertension. It raises the risk of heart attack, stroke and kidney disease.

## Why checking matters
Most people with high blood pressure feel well and do not know they have it. Having your blood pressure measured at a health facility or pharmacy is quick and painless.

## Things that raise the risk
- Eating a lot of salt
- Low levels of physical activity
- Tobacco use and drinking alcohol
- Being overweight
- A family history of high blood pressure, and getting older

## Healthy habits
- Use less salt and eat more vegetables and fruit
- Stay physically active
- Avoid tobacco and limit alcohol

If you have been told you have high blood pressure, follow the plan agreed with your health worker and keep your follow-up appointments.""",
        "source_name": "World Health Organization - Hypertension fact sheet",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/hypertension",
    },
    {
        "category": "maternal-and-child-health",
        "title": "Antenatal care during pregnancy",
        "summary": "Regular check-ups during pregnancy help protect the health of both "
                   "mother and baby.",
        "body": """Antenatal care is the care a woman receives from health workers during pregnancy. It helps find and manage problems early and prepares the family for a safe birth.

## What happens at a visit
- Checking blood pressure, weight and the baby's growth
- Tests such as blood, urine and HIV tests
- Advice on nutrition and supplements recommended by the health worker
- Planning where and with whom the birth will take place

## How often
The World Health Organization recommends at least eight antenatal contacts during pregnancy, starting in the first three months. Your health worker will guide you on your own schedule.

## Danger signs
Go to a health facility immediately if you have vaginal bleeding, severe headache or blurred vision, fits, severe abdominal pain, fever, or if the baby stops moving.""",
        "source_name": "World Health Organization - Recommendations on antenatal care for a positive pregnancy experience",
        "source_url": "https://www.who.int/publications/i/item/9789241549912",
    },
    {
        "category": "mental-health",
        "title": "Looking after your mental health",
        "summary": "Mental health is part of overall health. Knowing the signs and where "
                   "to find support can make a difference.",
        "body": """Mental health is about how we think, feel and cope with everyday life. Everyone goes through hard times, and feeling low or anxious now and then is common.

## Signs that you may need support
- Feeling sad, hopeless or worried most of the time for two weeks or more
- Changes in sleep or appetite
- Losing interest in things you usually enjoy
- Finding it hard to cope at school, work or home

## Things that can help
- Talking to someone you trust
- Keeping a regular routine for sleep, meals and activity
- Avoiding alcohol and drugs as a way to cope

## Getting help
Mental health conditions can be treated. A health worker at a facility can assess you and refer you to counselling or other care. The Kenya Red Cross toll-free line 1199 offers psychosocial support. If you are in danger, call 999 or 112.""",
        "source_name": "World Health Organization - Mental disorders fact sheet",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/mental-disorders",
    },
    {
        "category": "sexual-and-reproductive-health",
        "title": "HIV testing: why and where",
        "summary": "Testing is the only way to know your HIV status. Treatment lets people "
                   "with HIV live long, healthy lives.",
        "body": """HIV is a virus that weakens the body's defence against infection. It is passed through certain body fluids, for example during unprotected sex, by sharing needles, or from a mother to her baby during pregnancy, birth or breastfeeding.

## Why get tested
- Many people with HIV feel well and do not know they have it
- Starting treatment early protects your health
- People on effective treatment who keep the virus suppressed do not pass HIV to sexual partners

## Where to test
HIV testing is offered at many public health facilities, including comprehensive care centres. Self-test kits are also available in some places; a reactive self-test must be confirmed at a health facility.

## Prevention
- Use condoms correctly every time
- Ask a health worker whether prevention medicine (PrEP) is right for you
- Pregnant women should test as part of antenatal care to protect their babies""",
        "source_name": "World Health Organization - HIV and AIDS fact sheet",
        "source_url": "https://www.who.int/news-room/fact-sheets/detail/hiv-aids",
    },
]

def slugify(text):
    """Turn a title into a web-address name: "Malaria: the basics" -> "malaria-the-basics"."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80] or "item"


def seed(db):
    cat_ids = {}
    for name, slug, desc in HEALTH_CATEGORIES:
        cat_ids[slug] = db.execute(
            "INSERT INTO health_categories (name, slug, description) VALUES (?, ?, ?)",
            (name, slug, desc)).lastrowid

    for a in ARTICLES:
        db.execute(
            """INSERT INTO health_articles (category_id, title, slug, summary, body,
               source_name, source_url, status, last_reviewed)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'published', ?)""",
            (cat_ids[a["category"]], a["title"], slugify(a["title"]), a["summary"],
             a["body"], a["source_name"], a["source_url"], REVIEWED))

    db.executemany(
        """INSERT INTO emergency_contacts (name, number, purpose, availability,
           source_name, source_url, display_order, verified_on)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [c + (REVIEWED,) for c in EMERGENCY_CONTACTS])
    db.commit()