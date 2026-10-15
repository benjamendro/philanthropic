#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מכין את התוכן של ריפו השיתוף – החלק של המאגר שמותר למסור לגורמים חיצוניים.

    python3 tools/export_share.py <תיקיית-יעד>

נכתבים ליעד:

    <out>                 הדפים המפורסמים, כפי שבנה build_site.py
    data/<שם>.json        הנתונים של כל מיפוי, באותה הפשטה שבדף:
                          בלי internalNote, sources וכל שדה ב-BUILD_ONLY
    README.md             הסבר לגורם המקבל ולסוכן שלו (tools/share_README.md)

כלי העריכה אינם נכללים – הם מכילים את הנתונים המלאים, כולל ההערות הפנימיות.

לפני הכתיבה התוכן נסרק למספרי טלפון ולכתובות דוא"ל. אם נמצא משהו, הסקריפט
נכשל ולא נכתב דבר, כך שה-Action לא דוחף מידע אישי לריפו הציבורי.
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import ROOT, public_payload  # noqa: E402
from sites import SITES  # noqa: E402

SHARE_README = os.path.join(ROOT, "tools", "share_README.md")

PHONE = re.compile(r"(?<![\w/+=])0(?:5\d|[2-489]|7\d)-?\d{3}-?\d{4}(?![\w/+=])")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
DATA_URI = re.compile(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+")


def personal_data(text):
    text = DATA_URI.sub("", text)  # הלוגו המוטמע אינו טקסט
    return PHONE.findall(text) + EMAIL.findall(text)


def collect():
    """{נתיב ביעד: תוכן} לכל מה שעובר לריפו השיתוף."""
    files = {}
    for cfg in SITES:
        with open(os.path.join(ROOT, cfg["out"]), encoding="utf-8") as f:
            files[cfg["out"]] = f.read()
        with open(os.path.join(ROOT, cfg["data"]), encoding="utf-8") as f:
            payload = json.load(f)
        name = os.path.basename(cfg["data"])
        files[f"data/{name}"] = json.dumps(
            public_payload(payload), ensure_ascii=False, indent=2) + "\n"
    with open(SHARE_README, encoding="utf-8") as f:
        files["README.md"] = f.read()
    files[".nojekyll"] = ""
    return files


def main():
    if len(sys.argv) != 2:
        raise SystemExit("שימוש: python3 tools/export_share.py <תיקיית-יעד>")
    dest = sys.argv[1]
    files = collect()

    found = {path: hits for path, text in files.items()
             if (hits := personal_data(text))}
    if found:
        for path, hits in found.items():
            print(f"{path}: {sorted(set(hits))}", file=sys.stderr)
        raise SystemExit("נמצא מה שנראה כמו מידע אישי. לא נכתב דבר.")

    # היעד משקף בדיוק את מה שנאסף: מה שהוסר מהמאגר מוסר גם ממנו
    os.makedirs(dest, exist_ok=True)
    for entry in os.listdir(dest):
        if entry == ".git":
            continue
        full = os.path.join(dest, entry)
        shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
    for path, text in files.items():
        full = os.path.join(dest, path)
        os.makedirs(os.path.dirname(full) or dest, exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  {path}")


if __name__ == "__main__":
    main()
