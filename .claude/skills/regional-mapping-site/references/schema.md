# Record shape and site config

## The data file

```jsonc
{
  "organizations": [ /* records, see below */ ],
  "legend": [ { "topic": "…", "text": "…" } ],   // shown in the page's מקרא section
  "tagOrder": [ "…" ]                            // domain tags first, rest alphabetical
}
```

## A record

Only `id`, `name`, `tags` and `actions` are required by the templates. Every
other field is optional and simply does not render when absent, which is what
lets two mappings with different fields share one template.

| field | type | notes |
|---|---|---|
| `id` | string | slug of the name, **unique** — used for `#deep-links` and for the editor's change tracking |
| `name` | string | |
| `aliases` | string[] | hidden search keys; not displayed (a visible "also known as" line reads like filler) |
| `relevance` | string | e.g. `ליבה` / `משיק`. Drives the card's edge stripe and badge colour |
| `type` | string | free text as written in the source |
| `typeGroup` | string | the consolidated family, six to eight values, the one worth filtering by |
| `areaText` | string | the activity area exactly as it should read on the card |
| `scope` | string | coarse level, e.g. `גליל מזרחי` / `צפון והגליל` / `ארצי` |
| `places` | string[] | filterable place tokens, **only ones that literally appear** in the source location field |
| `tags` | string[] | one unified vocabulary |
| `audience` | string | example of a mapping-specific field; declare it in `meta` and `fields` |
| `intro` | string | opening paragraph. `\n` renders as a line break |
| `actions` | object[] | `{ title, body, partners: string[] }` — one per programme or activity |
| `partners` | string[] | flattened union of the action partners; the editor re-derives this on export |
| `note` | string | shown on the card, italic |
| `website` | string | rendered as "אתר הארגון" |

### Build-only fields

Kept in the JSON, stripped from the published page — including from its source:

| field | why it exists |
|---|---|
| `internalNote` | judgements about a third party; never publish |
| `sources` | per-entry provenance; the page names sources once instead |
| `isAddition` | this entry was researched rather than supplied |
| `tagsDerived` | its tags were inferred from the description |

`actions[].partnersNote` is also stripped: some survey answers put a sentence
where a partner list belongs (`אין שותפים רוחביים. סביב פעולות ספציפיות אנו
רותמים שותפים`), which reads wrong under a "בשיתוף" label.

The editor must be seeded with these fields present, or every export drops them.

## Site config (`tools/sites.py`)

```python
{
  "key": "young",                       # also the localStorage key for its editor
  "data": "data/young-organizations.json",
  "out": "young/index.html",
  "editorOut": "young/editor.html",
  "title": "…", "subtitle": "…", "description": "…",
  "sources": "מבוסס על …",              # the one source statement
  "tagsTitle": "תחומי פעילות",           # heading over the tag distribution panel

  "facets": [                           # each becomes a select, built from the data
    {"key": "scope", "label": "היקף הפעילות", "all": "כל ההיקפים",
     "order": ["גליל מזרחי", "גליל מערבי", "כלל הגליל והצפון"]},
    {"key": "places", "label": "יישוב או אזור", "all": "כל המקומות", "multi": True},
  ],

  "kpis": [                             # kind: count | equals | actions | distinct
    {"label": "ארגונים", "kind": "count"},
    {"label": "תחומי פעילות", "kind": "distinct", "key": "tags"},
  ],

  "meta":   [{"key": "audience", "label": "אוכלוסיית יעד"}],   # extra card lines
  "fields": ["name", "scope", "areaText", "places", "tags",    # editor form, in order
             "audience", "intro", "actions", "note", "website", "internalNote"],
}
```

`order` pins a facet's option order where alphabetical would be meaningless —
a scope running local → regional → national reads correctly, sorted does not.

Facet values are read straight from the data, so a value only appears as an
option if some record has it. That is deliberate: it makes an empty filter
impossible, and it means fixing the data fixes the filter.

## Layout notes that cost a debugging round

- The KPI band is flex, not grid. A grid with a fixed column count leaves a
  visibly empty cell whenever the mapping has fewer KPIs, and the divider trick
  (`gap: 1px` over a coloured container) paints that cell grey.
- A `<span>` with `height` and `width` is inline and ignores both. The
  distribution bars need `display: block` to render at all.
- Hebrew labels do not want `letter-spacing`; it just loosens the script.
- A count following a Latin-script tag needs `unicode-bidi: isolate`, or
  `STEM` and `3` collide into `STEM3`.
- Do not make a tall filter panel sticky — it eats a third of the viewport.
