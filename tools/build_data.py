#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את data/organizations.json מתוך קובץ האקסל של המיפוי + שכבת העריכה.

    python3 tools/build_data.py

הקלט:
    מיפוי מאוחד - גופים לפיתוח כלכלי בגליל המזרחי.xlsx
    tools/curation.py   – תיקוני טקסט, איחוד תגיות, השלמות
    tools/additions.py  – ארגונים שנוספו ממקורות פתוחים

הפלט:
    data/organizations.json

שימו לב: מרגע שעורכים את הנתונים דרך editor.html, הקובץ data/organizations.json
הוא מקור האמת. הרצה חוזרת של הסקריפט הזה תדרוס עריכות כאלה, ולכן היא דורשת
--force כשהקובץ כבר קיים.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curation import (  # noqa: E402
    AREA_TEXT_REWRITES, DOMAIN_TAGS, ENRICHMENTS, INTERNAL_NOTE_MARKERS,
    PERSONAL_REDACTIONS, PLACE_TOKENS, PROCESS_NOTES, SCOPE_RULES, SOURCE_MAP,
    TAG_COMPLETIONS, TAG_MAP, TEXT_FIXES, TONE_EDITS, TYPE_GROUPS,
)
from additions import ADDITIONS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(ROOT, "מיפוי מאוחד - גופים לפיתוח כלכלי בגליל המזרחי.xlsx")
OUT = os.path.join(ROOT, "data", "organizations.json")

TYPE_OF_GROUP = {t: g for g, types in TYPE_GROUPS.items() for t in types}


def apply_text_fixes(text):
    if not text:
        return ""
    for pattern, repl in TEXT_FIXES + PERSONAL_REDACTIONS:
        text = re.sub(pattern, repl, text)
    return text.strip()


def apply_tone_edits(name, text):
    for old, new in TONE_EDITS.get(name, []):
        fixed = apply_text_fixes(old)
        if old in text:
            text = text.replace(old, new)
        elif fixed in text:
            text = text.replace(fixed, new)
        else:
            print(f"  אזהרה: עריכת סגנון לא נמצאה ב{name!r}: {old[:45]}…")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_description(text):
    """מפריד את התיאור לפסקת פתיחה ולרשימת פעולות (בולטים)."""
    intro_lines, actions = [], []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("•"):
            body = line.lstrip("•").strip()
            partners = []
            partners_note = ""
            m = re.search(r"בשיתוף:\s*(.+?)\s*$", body)
            if m:
                partners, partners_note = split_partners(m.group(1))
                body = body[: m.start()].strip().rstrip(".").strip()
            title, _, rest = body.partition("—")
            if not rest.strip():
                title, rest = "", body
            actions.append({"title": title.strip().rstrip(".").strip(),
                            "body": rest.strip(),
                            "partners": partners,
                            "partnersNote": partners_note})
        elif actions:
            actions[-1]["body"] += " " + line
        else:
            intro_lines.append(line)
    return "\n".join(intro_lines).strip(), actions


MAX_PARTNER_CHIP = 34


def split_partners(text):
    """מפריד את רשימת השותפים לתגיות קצרות ולטקסט חופשי שנשאר כפי שנכתב.

    בחלק מהתשובות בקובץ המקור "בשיתוף" הוא משפט שלם ולא רשימת שמות, ולכן כל
    מקטע ארוך מוצג כטקסט ולא כתגית.
    """
    text = re.sub(r"\s*\.\s*$", "", text).strip()
    chips, leftover = [], []
    for part in re.split(r"[,;]", text):
        part = part.strip(" .־-")
        if len(part) < 2:
            continue
        (chips if len(part) <= MAX_PARTNER_CHIP else leftover).append(part)
    return chips, ", ".join(leftover)


def normalize_tags(raw, name):
    if not raw or not raw.strip():
        derived = TAG_COMPLETIONS.get(name, [])
        return sorted(set(derived), key=tag_sort_key), bool(derived)
    tags = []
    for t in raw.split(","):
        t = t.strip()
        if not t:
            continue
        mapped = TAG_MAP.get(t, t)
        if mapped:
            tags.append(mapped)
    return sorted(set(tags), key=tag_sort_key), False


def tag_sort_key(tag):
    return (0, DOMAIN_TAGS.index(tag)) if tag in DOMAIN_TAGS else (1, tag)


def clean_area(text):
    """מנקה שאריות עיבוד מעמודת מרחב פעילות."""
    text = (text or "").strip()
    if "|" in text:
        left, right = (p.strip() for p in text.split("|", 1))
        # "X | מיקום שצוין במקור: X" – החלק השני מיותר כשהוא כלול בראשון
        inner = right.replace("מיקום שצוין במקור:", "").strip()
        if inner and inner in left:
            text = left
        else:
            text = left
    return AREA_TEXT_REWRITES.get(text, text)


def places_in(area_text, description):
    """מחזיר רק מקומות שנכתבו בפועל בעמודת מרחב הפעילות."""
    found = [p for p in PLACE_TOKENS if p in area_text]
    # "18 רשויות" מתייחס לכל האשכול ולא ליישוב מסוים
    return found


def scope_of(area_text):
    for keyword, scope in SCOPE_RULES:
        if keyword in area_text:
            return scope
    if "צפון" in area_text or "גליל" in area_text:
        return "צפון והגליל"
    return "ארצי"


DOMAIN_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-zA-Z]{2,}$")


def normalize_sources(raw):
    """מתרגם את ערכי המקור לשמות המוצגים.

    ארבעת קבצי המיפוי מקובצים לשמות ציבוריים לפי SOURCE_MAP, ומהמקורות
    הפתוחים נשמרות כתובות אתרים בלבד — לא עיתונות, ויקיפדיה או שמות קבצים.
    """
    out = []
    for token in re.split(r"\s\+\s|,", raw or ""):
        token = token.replace("מקורות פתוחים –", "").strip(" .–-")
        if not token:
            continue
        value = SOURCE_MAP.get(token)
        if value is None and DOMAIN_RE.match(token):
            value = token
        if value and value not in out:
            out.append(value)
    return out


def slugify(name):
    s = unicodedata.normalize("NFKD", name)
    s = re.sub(r"[^\w֐-׿]+", "-", s).strip("-")
    return s[:60]


def split_note(note):
    """מפריד הערות פומביות מהערות פנימיות על כשירות של צד שלישי."""
    note = (note or "").strip()
    if not note:
        return "", ""
    public, internal = [], []
    for sentence in re.split(r"(?<=[.;])\s+", note):
        if not sentence.strip():
            continue
        target = internal if any(m in sentence for m in INTERNAL_NOTE_MARKERS) else public
        target.append(sentence.strip())
    return " ".join(public), " ".join(internal)


def build_record(row, is_addition=False):
    name = (row["שם הגוף"] or "").strip()
    enrich = ENRICHMENTS.get(name, {})

    description = apply_tone_edits(name, apply_text_fixes(row["תיאור"]))
    intro, actions = split_description(description)

    area_text = clean_area(row["מרחב פעילות"])
    tags, tags_derived = normalize_tags(row["קטגוריות ותגיות"], name)

    note_raw = apply_text_fixes(row.get("הערות") or "")
    if name in PROCESS_NOTES:
        public_note, internal_note = "", note_raw
    else:
        public_note, internal_note = split_note(note_raw)
    if enrich.get("note"):
        public_note = (public_note + " " + enrich["note"]).strip()

    org_type = (row["סוג הגוף"] or "").strip()
    sources = normalize_sources(row["מקורות המידע"])

    return {
        "id": slugify(name),
        "name": name,
        "aliases": row.get("aliases", []) or enrich.get("aliases", []),
        "type": org_type,
        "typeGroup": TYPE_OF_GROUP.get(org_type, "אחר"),
        "relevance": (row["רלוונטיות לפיתוח כלכלי"] or "").strip(),
        "areaText": area_text,
        "scope": scope_of(area_text),
        "places": places_in(area_text, description),
        "tags": tags,
        "tagsDerived": tags_derived,
        "intro": intro,
        "actions": actions,
        "partners": sorted({p for a in actions for p in a["partners"]}),
        "sources": sources,
        "note": public_note,
        "internalNote": internal_note,
        "website": row.get("website") or enrich.get("website", ""),
        "isAddition": is_addition,
    }


def main():
    parser = argparse.ArgumentParser(description="ייבוא המיפוי מקובץ האקסל")
    parser.add_argument("--force", action="store_true",
                        help="דריסת data/organizations.json קיים")
    args = parser.parse_args()

    if os.path.exists(OUT) and not args.force:
        print(f"{os.path.relpath(OUT, ROOT)} כבר קיים ולא נדרס.")
        print("אם ערכתם דרך editor.html, ההרצה הזאת תמחק את העריכות.")
        print("להרצה בכל זאת:  python3 tools/build_data.py --force")
        raise SystemExit(1)

    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb["מיפוי מאוחד"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]

    records = [build_record(dict(zip(header, r))) for r in rows[1:] if r[0]]
    records += [build_record(a, is_addition=True) for a in ADDITIONS]
    records.sort(key=lambda r: (r["relevance"] != "ליבה", r["name"]))

    legend = [
        {"topic": r[0], "text": r[1]}
        for r in wb["מקרא והסברים"].iter_rows(min_row=2, values_only=True)
        if r[0]
    ]

    payload = {
        "organizations": records,
        "legend": legend,
        "tagOrder": DOMAIN_TAGS,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    untagged = [r["name"] for r in records if not r["tags"]]
    print(f"נכתבו {len(records)} ארגונים אל {os.path.relpath(OUT, ROOT)}")
    print(f"  מתוכם {sum(r['isAddition'] for r in records)} חדשים, "
          f"{sum(r['tagsDerived'] for r in records)} עם תגיות שהושלמו")
    if untagged:
        print(f"  ללא תגיות: {untagged}")


if __name__ == "__main__":
    main()
