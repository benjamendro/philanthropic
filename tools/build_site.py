#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה שני קבצים מתוך data/organizations.json:

    index.html    הדף המפורסם – תצוגה בלבד, מוכן ל-GitHub Pages ולהטמעה
                  כ-iframe בפלטפורמת Experience.
    editor.html   כלי עריכה מקומי. פותחים אותו בדפדפן, עורכים, ומייצאים
                  organizations.json מעודכן. אינו משנה דבר בשרת.

    python3 tools/build_site.py
"""
import base64
import copy
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "organizations.json")
TEMPLATE = os.path.join(ROOT, "tools", "template.html")
EDITOR_TEMPLATE = os.path.join(ROOT, "tools", "editor_template.html")
LOGO = os.path.join(ROOT, "לוגו מרכז הידע חדש עם גליל מערבי רקע לבן.jpg")
OUT = os.path.join(ROOT, "index.html")
EDITOR_OUT = os.path.join(ROOT, "editor.html")

HEBREW_MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
                 "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]

# שדות שהם מטא על תהליך הבנייה ולא מידע על הארגון. הם נשמרים ב-JSON
# לצורך מעקב, ואינם נכללים בדף הפומבי — גם לא בקוד המקור שלו.
BUILD_ONLY = ("internalNote", "sources", "isAddition", "tagsDerived")

LOGO_WIDTH = 760  # מוצג בגובה 46px; רוחב זה מספיק גם למסכי Retina


def shrink_logo():
    """מקטין את הלוגו לפני ההטמעה – הקובץ המקורי גדול פי עשרה מהנדרש."""
    try:
        from PIL import Image
    except ImportError:
        with open(LOGO, "rb") as f:
            return f.read()
    import io
    with Image.open(LOGO) as im:
        height = round(LOGO_WIDTH * im.size[1] / im.size[0])
        small = im.convert("RGB").resize((LOGO_WIDTH, height), Image.LANCZOS)
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
    return buf.getvalue()


def embed(template_path, payload, **tokens):
    with open(template_path, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("/*__DATA__*/{}",
                        json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    for key, value in tokens.items():
        html = html.replace(f"__{key}__", value)
    return html


def main():
    with open(DATA, encoding="utf-8") as f:
        payload = json.load(f)

    # כלי העריכה מקבל את הנתונים המלאים, כדי שייצוא ממנו לא ישמיט שדות
    editor = embed(EDITOR_TEMPLATE, payload)
    with open(EDITOR_OUT, "w", encoding="utf-8") as f:
        f.write(editor)

    # הדף הפומבי מקבל עותק מופשט
    payload = copy.deepcopy(payload)
    for org in payload["organizations"]:
        for field in BUILD_ONLY:
            org.pop(field, None)
        # חלק מתשובות "בשיתוף" בקובץ המקור הן משפט ולא רשימת שותפים
        for action in org["actions"]:
            action.pop("partnersNote", None)

    today = datetime.date.today()
    site = embed(
        TEMPLATE, payload,
        LOGO="data:image/jpeg;base64," + base64.b64encode(shrink_logo()).decode(),
        UPDATED=f"{HEBREW_MONTHS[today.month - 1]} {today.year}",
        COUNT=str(len(payload["organizations"])),
    )
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(site)

    print(f"נכתב {os.path.relpath(OUT, ROOT)}    — {len(site):,} תווים, "
          f"{len(payload['organizations'])} ארגונים")
    print(f"נכתב {os.path.relpath(EDITOR_OUT, ROOT)}   — {len(editor):,} תווים")


if __name__ == "__main__":
    main()
