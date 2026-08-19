#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את index.html – קובץ HTML יחיד ועצמאי, מוכן לפרסום ב-GitHub Pages
ולהטמעה כ-iframe בפלטפורמת Experience.

    python3 tools/build_site.py

הקלט:  data/organizations.json, tools/template.html, קובץ הלוגו
הפלט:  index.html
"""
import base64
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "organizations.json")
TEMPLATE = os.path.join(ROOT, "tools", "template.html")
LOGO = os.path.join(ROOT, "לוגו מרכז הידע חדש עם גליל מערבי רקע לבן.jpg")
OUT = os.path.join(ROOT, "index.html")

HEBREW_MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
                 "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]


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


def main():
    with open(DATA, encoding="utf-8") as f:
        payload = json.load(f)

    # ההערות הפנימיות (אמירות על כשירות של צד שלישי) אינן נכללות בדף הפומבי
    for org in payload["organizations"]:
        org.pop("internalNote", None)

    logo = "data:image/jpeg;base64," + base64.b64encode(shrink_logo()).decode()

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    today = datetime.date.today()
    html = (html
            .replace("/*__DATA__*/{}", json.dumps(payload, ensure_ascii=False,
                                                  separators=(",", ":")))
            .replace("__LOGO__", logo)
            .replace("__UPDATED__", f"{HEBREW_MONTHS[today.month - 1]} {today.year}")
            .replace("__COUNT__", str(len(payload["organizations"]))))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"נכתב {os.path.relpath(OUT, ROOT)} — {len(html):,} תווים, "
          f"{len(payload['organizations'])} ארגונים")


if __name__ == "__main__":
    main()
