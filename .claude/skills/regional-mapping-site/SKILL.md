---
name: regional-mapping-site
description: >
  Build or update a regional organisation mapping — a filterable Hebrew RTL
  page published to GitHub Pages and embedded in ArcGIS Experience, plus a
  local editor the owner uses to maintain it. Use this whenever someone brings
  a spreadsheet, GuideStar export, registry dump or survey of organisations and
  wants it turned into a browsable page or directory; when they ask to add,
  remove or edit organisations in an existing mapping; when they want to add a
  whole new mapping alongside the existing ones; or when they hand over an
  exported organizations.json to apply. Also use it before publishing any
  directory of real organisations, because it carries the data policies —
  especially the rule against publishing personal contact details — that this
  project has already been burned by.
---

# Regional mapping sites

A mapping starts as somebody's spreadsheet: a survey with free-text answers, a
registry export, a couple of merged files. It ends as a page a resident or a
funder can scan in thirty seconds. Most of the work is in between, and most of
the mistakes are made by treating the spreadsheet as if it were already clean.

## The pipeline

```
source file (xlsx / json)
      │   one-time import script + auditable curation layer
      ▼
data/<name>.json          ← source of truth once importing is done
      │   tools/build_site.py, driven by tools/sites.py
      ├─► <out>.html        the published page, view-only
      └─► <editor>.html     a local editing tool that exports data/<name>.json
```

`data/*.json` is the source of truth. The import scripts refuse to overwrite an
existing one without `--force`, because once the owner has edited through the
editor, re-running an import would silently destroy that work.

Adding a mapping means adding a data file and an entry in `tools/sites.py` —
titles, facets, KPIs, editor fields. The templates are shared and need no
changes. Read `references/schema.md` for the record shape and the config
fields.

## Start by reading the data, not by building

Before writing any page, load the source and answer these, then report what you
found. Every one of these has bitten this project at least once:

- **How many records have each field?** A field that is empty in 55% of rows
  cannot be a filter.
- **How many distinct values does each categorical field have?** 42 free-text
  "organisation type" values across 53 rows is not a facet; it needs
  consolidating into six to eight families first.
- **Is there a controlled vocabulary, or two of them merged?** Look for near
  duplicates: `תעסוקה` next to `תעסוקה והשמות`, `צעירים` next to
  `צעירים וסטודנטים`. Merged sources produce these.
- **Does anything break when split on a comma?**
  `STEM (מדע, טכנולוגיה, הנדסה, מתמטיקה)` became four tags this way.
- **Are there duplicate names or colliding ids?** Two rows named the same thing
  break both the editor's change tracking and `#id` deep links. Merge by name,
  preferring the non-empty value, and guarantee unique ids.
- **Is there personal data?** See below. Check every field, not just the ones
  named "contact".
- **Does the legend describe columns that are not in the file?** A trimmed
  export can leave the documentation describing data nobody has.

Report the gaps as a list with counts and say which ones block the work. Do not
quietly paper over them.

## Data policies

These came from the owner and are not negotiable defaults you can reason past.

**Never publish personal data.** No phone numbers, no email addresses, no named
contacts, no staff first names. This is the one that has actually gone wrong: a
previously published dashboard in this repo carried 51 private mobile numbers
and 60 personal names for months. Personal data hides in places the column
names do not advertise — inside a partners list (`בשיתוף: ... (סיוון, קרן)`),
inside a description (`קרן בלומברג (בתכנון, השתתפות של רונית)`). Before you
publish, grep the built output for phone patterns, `@`, and `מנכ"ל/יו"ר +
name`, and read what you find. Names that are part of an organisation's public
identity are different — a fund named after its founder, a historical figure —
and those stay.

**Do not delete content because the writing is inflated.** Some entries read
like marketing copy or like a machine wrote them. That is not a reason to cut
them: extra information does not detract. Fix outright errors — typos, a stray
`:;`, an unreadable fragment — and leave the rest as written. If you think an
entry reads badly, list it for the owner rather than trimming it.

**Keep the build log off the page.** Anything that describes how the mapping was
assembled belongs in the data, not in front of a reader: `מטרות רשומות:` as a
prefix (a registry-extraction label), notes like "row X was merged here" or
"mentioned in the source file as a partner", provenance badges saying an entry
was added from open sources, markers showing which tags were inferred. A person
compiling a directory by hand would not annotate their own process. Keep the
fields in the JSON, strip them at build time.

**Sources are one statement, not a line on every card.** Per-entry source values
confuse readers and expose internal file names. Name the sources once under the
masthead and once in the footer. Keep the per-entry values in the data.

**Judgements about third parties stay internal.** "No valid management
approval", "should verify it is still active" — legitimate in a working file,
not something to publish about a named organisation. `internalNote` carries
these and never reaches the page.

**Geography is only what the source says.** Do not infer a location. Build the
place filter from tokens that literally appear in the location field, and limit
it to the region the mapping is about — a fund that also works in Jerusalem
stays in the mapping, but Jerusalem is not a filter option and need not be
named. "Countrywide" is fine as a description.

## Text repairs worth making

Source text from a hand-filled form carries real typos. Fix them in the
curation layer, not in the source file, so a re-import does not lose them.
Watch for transposed letters (`הטשכנולוגיה`), doubled words
(`אשר חוו אשר למדו`), truncation (`משרד החקלאו,`), a Latin letter standing in
for a Hebrew one (`רש"י uפועלת`), and spelling variants worth unifying
(`שרות`→`שירות`, `איזור`→`אזור`). Use negative lookbehind so `שרות` does not
match inside `משרות`.

Keep every intervention in one reviewable place. `tools/curation.py` holds the
regex fixes, the redactions, the tag vocabulary map, the type families and the
per-entry overrides for one mapping; a new mapping gets its own equivalent.
When you are done, diff the output against the source at word level and account
for every difference — structural labels and intended fixes only, no silent
content loss.

## The editor

The owner maintains the mapping through a local page, not by editing JSON and
not by sending changes through chat. It loads the data, offers real controls
per field, tracks what changed, and exports a replacement data file.

Two things that matter more than they look:

- **Seed the editor with the complete record.** If you hand it a payload that
  has already had build-only fields stripped, every export silently drops those
  fields. Strip for the published page only.
- **Label the buttons by what the file is for.** An export and a change summary
  look interchangeable until someone sends you the summary and asks what to do
  next. Say inside each dialog which one updates the page and how.

Work is kept in `localStorage` keyed per mapping so a session survives a
refresh, and the export re-derives any denormalised field (like the flattened
partner list) so it cannot drift.

## Publishing

One self-contained HTML file per page: data and logo embedded, no CDN except
Google Fonts, white background so the iframe merges with the host Experience,
no horizontal scroll at 380px. The page reads URL parameters (`q`, the facet
keys, `tag`) so it can open pre-filtered, and `#id` opens one card.

`.github/workflows/publish.yml` rebuilds and pushes whenever a data file or a
template changes, so the owner publishes by dropping the exported JSON into
`data/` — no round trip through anyone else.

## Verify in a browser before saying it works

Run the pages in Chromium and check: no console errors, no horizontal overflow
at 1280px and 560px, every facet populated, filters and tag chips actually
narrow the list, the reset button clears everything, and the editor survives a
full round trip — edit, reload, export, and confirm the export parses and still
carries the internal fields. Screenshot the result and look at it; layout bugs
like an orphaned grid cell only show up visually.
