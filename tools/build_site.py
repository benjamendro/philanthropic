#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את הדפים של כל המיפויים המוגדרים ב-tools/sites.py.

לכל מיפוי נוצרים שני קבצים:

    <out>        הדף המפורסם – תצוגה בלבד, מוכן ל-GitHub Pages ולהטמעה
                 כ-iframe בפלטפורמת Experience.
    <editorOut>  כלי עריכה מקומי. פותחים אותו בדפדפן, עורכים, ומייצאים
                 קובץ נתונים מעודכן. אינו משנה דבר בשרת.

    python3 tools/build_site.py            כל המיפויים
    python3 tools/build_site.py galilee    מיפוי אחד
"""
import base64
import copy
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sites import BUILD_ONLY, SITES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "tools", "template.html")
EDITOR_TEMPLATE = os.path.join(ROOT, "tools", "editor_template.html")
LOGO = os.path.join(ROOT, "לוגו מרכז הידע חדש עם גליל מערבי רקע לבן.jpg")

HEBREW_MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
                 "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]

LOGO_WIDTH = 760  # מוצג בגובה 46px; רוחב זה מספיק גם למסכי Retina
_logo_cache = None


def logo_data_uri():
    """מקטין את הלוגו פעם אחת – הקובץ המקורי גדול פי עשרה מהנדרש."""
    global _logo_cache
    if _logo_cache:
        return _logo_cache
    try:
        from PIL import Image
        import io
        with Image.open(LOGO) as im:
            height = round(LOGO_WIDTH * im.size[1] / im.size[0])
            small = im.convert("RGB").resize((LOGO_WIDTH, height), Image.LANCZOS)
        buf = io.BytesIO()
        small.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
        raw = buf.getvalue()
    except ImportError:
        with open(LOGO, "rb") as f:
            raw = f.read()
    _logo_cache = "data:image/jpeg;base64," + base64.b64encode(raw).decode()
    return _logo_cache


def embed(template_path, payload, config, **tokens):
    with open(template_path, encoding="utf-8") as f:
        html = f.read()
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*__DATA__*/{}", dump(payload))
    html = html.replace("/*__CONFIG__*/{}", dump(config))
    for key, value in tokens.items():
        html = html.replace(f"__{key}__", value)
    return html


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    return len(text)


def build(cfg):
    with open(os.path.join(ROOT, cfg["data"]), encoding="utf-8") as f:
        payload = json.load(f)

    # ההגדרה שנשלחת לדפדפן – בלי הנתיבים, שאין בהם צורך שם
    client_cfg = {k: v for k, v in cfg.items()
                  if k not in ("data", "out", "editorOut")}

    # כלי העריכה מקבל את הנתונים המלאים, כדי שייצוא ממנו לא ישמיט שדות
    editor_size = write(cfg["editorOut"], embed(
        EDITOR_TEMPLATE, payload, client_cfg, TITLE=cfg["title"]))

    # הדף הפומבי מקבל עותק מופשט
    public = copy.deepcopy(payload)
    for org in public["organizations"]:
        for field in BUILD_ONLY:
            org.pop(field, None)
        # חלק מתשובות "בשיתוף" בקובץ המקור הן משפט ולא רשימת שותפים
        for action in org["actions"]:
            action.pop("partnersNote", None)

    today = datetime.date.today()
    site_size = write(cfg["out"], embed(
        TEMPLATE, public, client_cfg,
        LOGO=logo_data_uri(),
        TITLE=cfg["title"],
        SUBTITLE=cfg["subtitle"],
        DESCRIPTION=cfg["description"],
        SOURCES=cfg["sources"],
        TAGS_TITLE=cfg["tagsTitle"],
        UPDATED=f"{HEBREW_MONTHS[today.month - 1]} {today.year}",
        COUNT=str(len(public["organizations"])),
    ))

    print(f"{cfg['key']:>8}  {cfg['out']:<18} {site_size:>7,} תווים, "
          f"{len(public['organizations'])} ארגונים")
    print(f"{'':>8}  {cfg['editorOut']:<18} {editor_size:>7,} תווים")


def main():
    wanted = sys.argv[1:]
    targets = [s for s in SITES if not wanted or s["key"] in wanted]
    if not targets:
        raise SystemExit(f"אין מיפוי בשם {wanted}. קיימים: {[s['key'] for s in SITES]}")
    for cfg in targets:
        build(cfg)


if __name__ == "__main__":
    main()
