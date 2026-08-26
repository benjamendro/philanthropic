#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ייבוא חד-פעמי של מיפוי ארגוני הצעירים אל מבנה הנתונים המשותף.

    python3 tools/import_young.py [--force]

הקלט:  young-organizations-dashboard/src/processed_data.json
הפלט:  data/young-organizations.json

שני הכללים של המזמין מוחלים כאן במלואם:

1. אין מפרסמים נתונים אישיים. העמודות "איש קשר" ו"טלפון" — 60 שמות ו-56
   מספרי טלפון נייד פרטיים — אינן מיובאות כלל.
2. תוכן לא נמחק בגלל ניסוח. הטקסטים מיובאים כלשונם, למעט תיקוני רווחים.

מרגע שעורכים דרך young/editor.html, קובץ ה-JSON הוא מקור האמת, ולכן
הסקריפט מסרב לדרוס אותו בלי --force.
"""
import argparse
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "young-organizations-dashboard", "src", "processed_data.json")
OUT = os.path.join(ROOT, "data", "young-organizations.json")

# ---------------------------------------------------------------------------
# מקומות. הרשימה מכסה את הגליל המזרחי והמערבי, שכן המיפוי הזה משתרע על שניהם.
# ערך שאינו מקום (משפט חופשי כמו "משתנה, כרגע יש בנהריה חצור טבריה ועוד")
# אינו הופך לאפשרות סינון.
# ---------------------------------------------------------------------------
CANONICAL = {
    "קרית שמונה": "קריית שמונה",
    "מעלות": "מעלות תרשיחא",
    "מעלות-תרשיחא": "מעלות תרשיחא",
    "גליל עליון- עמק החולה": "גליל עליון",
    "הגליל העליון": "גליל עליון",
    "טובא זנגריה": "טובא-זנגריה",
    "גליל מזרחי וגליל מערבי": "גליל מזרחי ומערבי",
    'אשכול גלמ"ז': "גליל מזרחי",
    "כל רשויות אשכול גליל מערבי וגליל מזרחי": "גליל מזרחי ומערבי",
    "ג'וליס,": "ג'וליס",
    "תל חי": "קריית שמונה",
}

# ערכים שהם טקסט חופשי ולא מקום – יורדים מרשימת המקומות ונשמרים בטקסט
NOT_A_PLACE = {
    "בצפון כולו- גולן, גליל עליון, קרית שמונה, גליל מערבי לאורכו",
    "גולן, מבואות חרמון, מעלה יוסף, מרום גליל, מטה אשר, הגליל העליון, "
    "עכו, נהריה, קרית שמונה...",
    "כל הגליל", "רחבי הגליל", "עבודה מול האשכולות בצפון",
    "משתנה, כרגע יש בנהריה חצור טבריה ועוד",
    "משאבים נמצאת בקרית שמונה, מרכזי החוסן שאותם הם מפעילים פרוסים בצפון",
    "גליל מזרחי ומערבי", "אצבע הגליל",
}

EAST = {"קריית שמונה", "צפת", "חצור הגלילית", "מטולה", "יסוד המעלה", "ראש פינה",
        "קצרין", "גולן", "גליל עליון", "טובא-זנגריה", "גוש חלב", "מנרה",
        "מלכיה", "משמר הירדן", "כפר הנשיא", "משגב עם", "להבות הבשן",
        "מבואות חרמון", "גינוסר"}
WEST = {"עכו", "נהריה", "שלומי", "מעלות תרשיחא", "כפר יאסיף", "אבו סנאן",
        "ירכא", "חורפיש", "בית ג'אן", "מטה אשר", "ג'וליס", "מעלה יוסף"}


def clean(text):
    """מנקה רווחים כפולים ורווחים תלויים, בלי לגעת בתוכן."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def slugify(name):
    s = unicodedata.normalize("NFKD", name)
    return re.sub(r"[^\w֐-׿]+", "-", s).strip("-")[:60]


def normalize_places(raw):
    places = []
    for value in raw or []:
        value = clean(value)
        if not value or value in NOT_A_PLACE:
            continue
        for part in (value.split(",") if value == "גינוסר, עכו" else [value]):
            part = CANONICAL.get(clean(part), clean(part))
            if part and part not in places:
                places.append(part)
    return places


def scope_of(places, area_text):
    east = any(p in EAST for p in places)
    west = any(p in WEST for p in places)
    if east and not west:
        return "גליל מזרחי"
    if west and not east:
        return "גליל מערבי"
    if east or west or area_text:
        return "כלל הגליל והצפון"
    return "כלל הגליל והצפון"


def build_record(row):
    name = clean(row.get("שם הארגון"))
    places = normalize_places(row.get("locations"))

    # הערכים שאינם מקום נשמרים כטקסט חופשי, כדי שלא ילך מידע לאיבוד
    free_text = [clean(v) for v in (row.get("locations") or [])
                 if clean(v) in NOT_A_PLACE]
    area_text = ", ".join(places + [t for t in free_text if t not in places])

    description = clean(row.get("תיאור/פרויקטים"))
    actions = ([{"title": "פעילות ופרויקטים", "body": description, "partners": []}]
               if description else [])

    return {
        "id": slugify(name),
        "name": name,
        "aliases": [],
        "areaText": area_text,
        "scope": scope_of(places, area_text),
        "places": places,
        "tags": [clean(t) for t in row.get("parsed_categories", []) if clean(t)],
        "audience": clean(row.get("אוכלוסיית יעד")),
        "intro": clean(row.get("תחום פעילות")),
        "actions": actions,
        "partners": [],
        "note": "",
        "internalNote": "",
        "website": "",
        "sources": [clean(row.get("מקור נתונים"))] if clean(row.get("מקור נתונים")) else [],
    }


def merge(a, b):
    """מאחד שתי רשומות של אותו ארגון: מעדיף ערך מלא על ריק, ומאחד רשימות."""
    for key, value in b.items():
        if isinstance(value, list):
            for item in value:
                if item not in a[key]:
                    a[key].append(item)
        elif value and not a.get(key):
            a[key] = value
    return a


def dedupe(records):
    """מאחד רשומות בעלות אותו שם ומוודא שכל מזהה ייחודי."""
    by_name = {}
    for rec in records:
        if rec["name"] in by_name:
            merge(by_name[rec["name"]], rec)
        else:
            by_name[rec["name"]] = rec

    merged = list(by_name.values())
    seen = set()
    for rec in merged:
        base = rec["id"] or "org"
        candidate, n = base, 2
        while candidate in seen:
            candidate, n = f"{base}-{n}", n + 1
        rec["id"] = candidate
        seen.add(candidate)
    return merged


def main():
    parser = argparse.ArgumentParser(description="ייבוא מיפוי ארגוני הצעירים")
    parser.add_argument("--force", action="store_true",
                        help="דריסת קובץ נתונים קיים")
    args = parser.parse_args()

    if os.path.exists(OUT) and not args.force:
        print(f"{os.path.relpath(OUT, ROOT)} כבר קיים ולא נדרס.")
        print("אם ערכתם דרך young/editor.html, ההרצה הזאת תמחק את העריכות.")
        print("להרצה בכל זאת:  python3 tools/import_young.py --force")
        raise SystemExit(1)

    with open(SRC, encoding="utf-8") as f:
        rows = json.load(f)

    raw_records = [build_record(r) for r in rows if clean(r.get("שם הארגון"))]
    records = dedupe(raw_records)
    records.sort(key=lambda r: r["name"])

    payload = {
        "organizations": records,
        "legend": [
            {"topic": "מטרת הקובץ",
             "text": "מיפוי הארגונים הפועלים עם צעירים בגליל ובצפון: מנהיגות "
                     "צעירה, חינוך והשכלה, תעסוקה ויזמות, קהילה וחברה, "
                     "התיישבות וציונות וחירום וחוסן."},
            {"topic": "פרטי קשר",
             "text": "הדף אינו מציג שמות של אנשי קשר או מספרי טלפון. פנייה "
                     "לארגון נעשית דרך הערוצים הפומביים שלו."},
            {"topic": "מרחב פעילות",
             "text": "המיפוי משתרע על הגליל המזרחי והמערבי. מסנן היישובים כולל "
                     "רק ערכים שנרשמו כמקום; תיאורי פעילות חופשיים נשמרו "
                     "כטקסט ואינם ניתנים לסינון."},
            {"topic": "סייג",
             "text": "המיפוי משקף את המקורות שסופקו. אין זו רשימה ממצה של כלל "
                     "הארגונים הפועלים במרחב."},
        ],
        "tagOrder": ["מנהיגות צעירה", "חינוך והשכלה", "תעסוקה ויזמות",
                     "קהילה וחברה", "התיישבות וציונות", "חירום וחוסן", "כללי"],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    dropped_contacts = sum(1 for r in rows if clean(r.get("איש קשר")))
    dropped_phones = sum(1 for r in rows if clean(r.get("טלפון")))
    print(f"נכתבו {len(records)} ארגונים אל {os.path.relpath(OUT, ROOT)}")
    print(f"  לא יובאו: {dropped_contacts} שמות אנשי קשר, {dropped_phones} מספרי טלפון")
    print(f"  ערכי סינון למקומות: {len({p for r in records for p in r['places']})}")
    if len(raw_records) != len(records):
        print(f"  אוחדו {len(raw_records) - len(records)} רשומות כפולות")


if __name__ == "__main__":
    main()
