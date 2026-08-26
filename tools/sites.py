# -*- coding: utf-8 -*-
"""
הגדרות האתרים שנבנים מהמאגר.

כל אתר מצביע על קובץ נתונים אחד ומגדיר מה מוצג ולפי מה מסננים. התבניות
(template.html ו-editor_template.html) משותפות לכל האתרים וקוראות את
ההגדרה הזאת, כך שאפשר להוסיף מיפוי נוסף בלי לגעת בקוד התצוגה.

שדות ההגדרה
-----------
facets   מסננים. כל אחד: key (שדה ברשומה), label, all (טקסט "הכול").
         multi=True כשהשדה הוא רשימה. order מקבע סדר תצוגה.
kpis     מדדים בראש הדף. kind אחד מ:
             count    מספר הרשומות המוצגות
             equals   כמה מהן עם value בשדה key
             actions  סכום הפעולות
             distinct כמה ערכים שונים יש בשדה key (רשימה או מחרוזת)
meta     שורות מידע נוספות בכרטיס, מעבר ל"מרחב פעילות" ולאתר.
fields   שדות שכלי העריכה מציג, בסדר הזה.
"""

# שדות שהם מטא על תהליך הבנייה ולא מידע על הארגון. נשמרים בקובץ הנתונים
# ואינם נכללים בדף הפומבי — גם לא בקוד המקור שלו.
BUILD_ONLY = ("internalNote", "sources", "isAddition", "tagsDerived")

# שדות עריכה שמופיעים כמעט בכל מיפוי
COMMON_FIELDS = ["name", "areaText", "places", "tags", "intro", "actions",
                 "note", "website", "internalNote"]

SITES = [
    {
        "key": "galilee",
        "data": "data/organizations.json",
        "out": "index.html",
        "editorOut": "editor.html",
        "title": "ארגונים העוסקים בפיתוח כלכלי בגליל המזרחי",
        "subtitle": "קרנות, ארגונים מפעילים ומיזמים הפועלים באזור",
        "description": "מיפוי הארגונים העוסקים בפיתוח כלכלי בגליל המזרחי "
                       "— מרכז הידע האזורי גליל מזרחי־מערבי.",
        "sources": "מבוסס על מיפוי FronTech, מיפוי מרכז הידע גליל מזרחי ומערבי, "
                   "גיידסטאר, מרשם העמותות ומקורות פתוחים",
        "tagsTitle": "תגיות נפוצות",
        "facets": [
            {"key": "relevance", "label": "רלוונטיות", "all": "הכול"},
            {"key": "typeGroup", "label": "סוג הגוף", "all": "כל הסוגים"},
            {"key": "scope", "label": "היקף הפעילות", "all": "כל ההיקפים",
             "order": ["גליל מזרחי", "צפון והגליל", "ארצי"]},
            {"key": "places", "label": "יישוב או אזור", "all": "כל המקומות",
             "multi": True},
        ],
        "kpis": [
            {"label": "ארגונים", "kind": "count"},
            {"label": "ליבה", "kind": "equals", "key": "relevance", "value": "ליבה"},
            {"label": "בגליל המזרחי", "kind": "equals", "key": "scope",
             "value": "גליל מזרחי"},
            {"label": "פעולות ותוכניות", "kind": "actions"},
        ],
        "meta": [],
        "fields": ["name", "relevance", "typeGroup", "type", "scope", "areaText",
                   "places", "tags", "intro", "actions", "note", "website",
                   "internalNote"],
    },
    {
        "key": "young",
        "data": "data/young-organizations.json",
        "out": "young/index.html",
        "editorOut": "young/editor.html",
        "title": "ארגונים הפועלים עם צעירים בגליל",
        "subtitle": "מיפוי השחקנים בתחום הצעירים בגליל ובצפון",
        "description": "מיפוי הארגונים הפועלים עם צעירים בגליל ובצפון "
                       "— מרכז הידע האזורי גליל מזרחי־מערבי.",
        "sources": 'מבוסס על מסד הנתונים "שחקנים בתחום צעירים" ועל קבצי מיפוי '
                   'של קרן רש"י',
        "tagsTitle": "תחומי פעילות",
        "facets": [
            {"key": "scope", "label": "היקף הפעילות", "all": "כל ההיקפים",
             "order": ["גליל מזרחי", "גליל מערבי", "כלל הגליל והצפון"]},
            {"key": "places", "label": "יישוב או אזור", "all": "כל המקומות",
             "multi": True},
        ],
        "kpis": [
            {"label": "ארגונים", "kind": "count"},
            {"label": "תחומי פעילות", "kind": "distinct", "key": "tags"},
            {"label": "יישובים ואזורים", "kind": "distinct", "key": "places"},
        ],
        "meta": [{"key": "audience", "label": "אוכלוסיית יעד"}],
        "fields": ["name", "scope", "areaText", "places", "tags", "audience",
                   "intro", "actions", "note", "website", "internalNote"],
    },
]


def site(key):
    for s in SITES:
        if s["key"] == key:
            return s
    raise KeyError(key)
