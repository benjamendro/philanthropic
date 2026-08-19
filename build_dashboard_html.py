import json
import sys
import base64

# Location normalization map - consolidate duplicates and clean messy values
LOCATION_NORMALIZE = {
    'קריית שמונה': 'קריית שמונה',
    'קרית שמונה': 'קריית שמונה',
    'גליל מזרחי וגליל מערבי': 'גליל מזרחי ומערבי',
    'גליל מזרחי ומערבי': 'גליל מזרחי ומערבי',
    'גליל עליון- עמק החולה': 'גליל עליון',
    'גינוסר, עכו': None,          # multi-value, expand below
    "ג'וליס,": "ג'וליס",
    # Free-text descriptions that are not real locations → drop
    'בצפון כולו- גולן, גליל עליון, קרית שמונה, גליל מערבי לאורכו': None,
    'גולן, מבואות חרמון, מעלה יוסף, מרום גליל, מטה אשר, הגליל העליון, עכו, נהריה, קרית שמונה...': None,
    'כל הגליל': None,
    'כל רשויות אשכול גליל מערבי וגליל מזרחי': None,
    'רחבי הגליל': None,
    'משאבים נמצאת בקרית שמונה, מרכזי החוסן שאותם הם מפעילים פרוסים בצפון': None,
    'עבודה מול האשכולות בצפון': None,
    'משתנה, כרגע יש בנהריה חצור טבריה ועוד': None,
    'אשכול גלמ"ז': 'גליל מזרחי',
}

# Multi-value expansions
EXPAND_LOCATIONS = {
    'גינוסר, עכו': ['גינוסר', 'עכו'],
}

def normalize_location(loc):
    """Return None to drop, or normalized string."""
    loc = loc.strip()
    if loc in EXPAND_LOCATIONS:
        return EXPAND_LOCATIONS[loc]  # returns list
    mapped = LOCATION_NORMALIZE.get(loc, loc)
    return mapped  # None means drop

def normalize_org_locations(locations):
    result = []
    for loc in (locations or []):
        out = normalize_location(loc.strip())
        if out is None:
            continue
        elif isinstance(out, list):
            result.extend(out)
        else:
            result.append(out)
    # deduplicate preserving order
    seen = set()
    unique = []
    for l in result:
        if l and l not in seen:
            seen.add(l)
            unique.append(l)
    return unique

def generate_dashboard():
    # Load logo as embedded base64
    logo_path = 'לוגו מרכז הידע חדש עם גליל מערבי רקע לבן.jpg'
    with open(logo_path, 'rb') as f:
        logo_b64 = 'data:image/jpeg;base64,' + base64.b64encode(f.read()).decode()

    with open('young-organizations-dashboard/src/processed_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Clean data
    clean_data = []
    for item in data:
        name = (item.get('שם הארגון') or '').strip()
        if not name:
            continue
        item['locations'] = normalize_org_locations(item.get('locations', []))
        clean_data.append(item)

    # All unique locations (clean)
    all_locs = set()
    for item in clean_data:
        for loc in item['locations']:
            if loc:
                all_locs.add(loc)
    all_locs_sorted = sorted(all_locs)

    # Categories sorted by count (descending)
    ALL_CATS_ORDERED = ['חינוך והשכלה','תעסוקה ויזמות','כללי','מנהיגות צעירה',
                        'קהילה וחברה','התיישבות וציונות','חירום וחוסן']

    data_json = json.dumps(clean_data, ensure_ascii=False)
    locs_json = json.dumps(all_locs_sorted, ensure_ascii=False)
    cats_json = json.dumps(ALL_CATS_ORDERED, ensure_ascii=False)

    html = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ארגוני צעירים — מרכז ידע</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --c-bg:        #f7f8fa;
    --c-surface:   #ffffff;
    --c-border:    #dde2e8;
    --c-text:      #333333;
    --c-text-sub:  #4A4A4A;
    --c-navy:      #003B6F;
    --c-navy-lt:   #e8eef5;
    --c-tag-bg:    #f1f4f8;
    --c-tag-txt:   #4A4A4A;
    --radius-sm:   6px;
    --radius-md:   10px;
    --radius-lg:   14px;
    --shadow-sm:   0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.05);
    --shadow-md:   0 4px 12px rgba(0,0,0,.08);
    font-family: 'Avenir Next', 'Avenir', 'Nunito Sans', 'Segoe UI', Arial, sans-serif;
  }

  body { background: var(--c-bg); color: var(--c-text); min-height: 100vh; }

  /* ── Layout ── */
  .page { max-width: 1140px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }

  /* ── Top bar ── */
  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 1rem;
    border-bottom: 2px solid var(--c-border);
    padding-bottom: 1.25rem; margin-bottom: 2rem;
  }
  .topbar-left { display: flex; align-items: center; gap: 1rem; }
  .topbar-brand h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.3px; color: var(--c-navy); }
  .topbar-brand p  { font-size: 0.86rem; color: var(--c-text-sub); margin-top: 2px; }
  .topbar-stats { display: flex; gap: 1.5rem; }
  .kpi { text-align: center; }
  .kpi-val { font-size: 1.5rem; font-weight: 700; color: var(--c-navy); line-height: 1; }
  .kpi-lbl { font-size: 0.75rem; color: var(--c-text-sub); margin-top: 2px; }

  /* ── Cards ── */
  .card {
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: 1.4rem 1.5rem;
    margin-bottom: 1.25rem;
  }
  .card-title {
    font-size: 0.78rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.07em; color: var(--c-navy);
    border-bottom: 1px solid var(--c-border);
    padding-bottom: 0.6rem; margin-bottom: 1rem;
  }

  /* ── Filters ── */
  .filter-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media(max-width:560px) { .filter-row { grid-template-columns: 1fr; } }
  .field label { display: block; font-size: 0.8rem; font-weight: 500;
    color: var(--c-text-sub); margin-bottom: 0.35rem; }
  input[type=text], select {
    width: 100%; padding: 0.55rem 0.85rem;
    border: 1px solid var(--c-border); border-radius: var(--radius-sm);
    background: var(--c-bg); color: var(--c-text);
    font-size: 0.92rem; font-family: inherit;
    transition: border-color .15s, box-shadow .15s;
    appearance: none; outline: none;
  }
  input[type=text]:focus, select:focus {
    border-color: var(--c-navy);
    box-shadow: 0 0 0 3px rgba(0,59,111,.12);
  }

  /* ── Chart ── */
  .chart-wrap { height: 300px; position: relative; }

  /* ── Category accordion ── */
  .section-head {
    display: flex; align-items: center; justify-content: space-between;
    margin: 1.75rem 0 0.85rem;
  }
  .section-head h2 { font-size: 1.05rem; font-weight: 700; color: var(--c-navy); }
  .result-meta { font-size: 0.82rem; color: var(--c-text-sub); }

  .accordion { display: flex; flex-direction: column; gap: 0.6rem; }

  .acc-item {
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
  }
  .acc-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.85rem 1.1rem;
    cursor: pointer; user-select: none;
    background: var(--c-navy);
    transition: background .12s;
  }
  .acc-header:hover { background: #004d8f; }
  .acc-left { display: flex; align-items: center; gap: 0.65rem; }
  .acc-stripe {
    width: 4px; height: 20px;
    border-radius: 2px; flex-shrink: 0;
    background: rgba(255,255,255,0.5);
  }
  .acc-name { font-size: 0.97rem; font-weight: 600; color: #ffffff; }
  .acc-right { display: flex; align-items: center; gap: 0.75rem; }
  .acc-count {
    font-size: 0.78rem; font-weight: 600;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    background: rgba(255,255,255,0.2); color: #ffffff;
    border: 1px solid rgba(255,255,255,0.35);
  }
  .acc-chevron { font-size: 0.75rem; color: rgba(255,255,255,0.8); transition: transform .25s; }
  .acc-chevron.open { transform: rotate(180deg); }

  .acc-body { display: none; padding: 0 1.1rem 1.1rem; }
  .acc-body.open { display: block; }

  /* ── Org list ── */
  .org-list { display: flex; flex-direction: column; gap: 0.6rem; margin-top: 0.4rem; }
  .org-row {
    padding: 0.85rem 1rem;
    border: 1px solid var(--c-border);
    border-radius: var(--radius-sm);
    background: var(--c-bg);
  }
  .org-row-head { display: flex; align-items: baseline; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.35rem; }
  .org-name { font-size: 0.95rem; font-weight: 600; color: var(--c-navy); }
  .org-contact { font-size: 0.8rem; color: var(--c-text-sub); }
  .org-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.4rem; }
  .tag {
    font-size: 0.72rem; font-weight: 500;
    padding: 0.18rem 0.55rem; border-radius: 20px;
    background: var(--c-navy-lt); color: var(--c-navy);
    border: 1px solid rgba(0,59,111,0.15);
  }
  .org-desc { font-size: 0.83rem; color: var(--c-text-sub); line-height: 1.6; }

  .empty { padding: 1.5rem; text-align: center; font-size: 0.88rem; color: var(--c-text-sub); }

  /* ── Footer ── */
  footer { text-align: center; font-size: 0.78rem; color: var(--c-text-sub); margin-top: 3rem; }
</style>
</head>
<body>
<div class="page">

  <!-- Top bar -->
  <div class="topbar">
    <div class="topbar-left">
      <img src="''' + logo_b64 + '''" alt="לוגו מרכז הידע" style="height:56px;width:auto;object-fit:contain;">
      <div class="topbar-brand">
        <h1>ארגוני הצעירים — מרכז ידע</h1>
        <p>מיפוי שחקנים בתחום הצעירים בגליל ובצפון</p>
      </div>
    </div>
    <div class="topbar-stats">
      <div class="kpi"><div class="kpi-val" id="kpiTotal">—</div><div class="kpi-lbl">ארגונים</div></div>
      <div class="kpi"><div class="kpi-val" id="kpiCats">7</div><div class="kpi-lbl">תחומים</div></div>
      <div class="kpi"><div class="kpi-val" id="kpiLocs">—</div><div class="kpi-lbl">אזורי פעילות</div></div>
    </div>
  </div>

  <!-- Filters -->
  <div class="card">
    <div class="card-title">סינון לפי אזור</div>
    <div class="field">
      <label for="locFilter">אזור גיאוגרפי</label>
      <select id="locFilter">
        <option value="">כל האזורים</option>
      </select>
    </div>
  </div>

  <!-- Chart -->
  <div class="card">
    <div class="card-title">התפלגות לפי תחום פעילות (ממוין)</div>
    <div class="chart-wrap"><canvas id="chart"></canvas></div>
  </div>

  <!-- Accordion -->
  <div class="section-head">
    <h2>פירוט לפי תחום</h2>
    <span class="result-meta" id="resultMeta"></span>
  </div>
  <div class="accordion" id="accordion"></div>

</div>
<footer>עודכן לאחרונה: אפריל 2025 &nbsp;|&nbsp; נתונים: מרכז ידע ארגוני צעירים</footer>

<script>
const DATA  = ''' + data_json + ''';
const LOCS  = ''' + locs_json + ''';
const CATS  = ''' + cats_json + ''';

// ── Populate location dropdown ──
const locSel = document.getElementById('locFilter');
LOCS.forEach(l => {
  const o = document.createElement('option');
  o.value = l; o.textContent = l;
  locSel.appendChild(o);
});

// ── Accent colours (professional, low-saturation) ──
const CAT_COLOR = {
  'חינוך והשכלה':    '#1d4ed8',
  'תעסוקה ויזמות':   '#0e7490',
  'כללי':             '#475569',
  'מנהיגות צעירה':   '#7c3aed',
  'קהילה וחברה':     '#065f46',
  'התיישבות וציונות':'#b45309',
  'חירום וחוסן':     '#991b1b',
};

// ── State ──
const expanded = new Set();
let chartInst = null;

// ── Filter ──
function getFiltered() {
  const loc = document.getElementById('locFilter').value;
  return DATA.filter(d => {
    if (!(d['שם הארגון']||'').trim()) return false;
    if (loc && !(d.locations||[]).includes(loc)) return false;
    return true;
  });
}

// ── KPIs ──
function updateKPIs(filtered) {
  const locSet = new Set();
  filtered.forEach(d => (d.locations||[]).forEach(l => locSet.add(l)));
  document.getElementById('kpiTotal').textContent = filtered.length;
  document.getElementById('kpiLocs').textContent  = locSet.size;
}

// ── Chart (sorted descending) ──
function renderChart(filtered) {
  const counts = CATS.map(c => filtered.filter(d => (d.parsed_categories||[]).includes(c)).length);
  // sort descending for display
  const pairs = CATS.map((c,i) => [c, counts[i]]).sort((a,b) => b[1]-a[1]);
  const labels = pairs.map(p => p[0]);
  const vals   = pairs.map(p => p[1]);
  const colors = labels.map(l => CAT_COLOR[l] || '#475569');

  if (chartInst) chartInst.destroy();
  const ctx = document.getElementById('chart').getContext('2d');
  chartInst = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: vals,
        backgroundColor: colors.map(c => c + '22'),
        borderColor: colors,
        borderWidth: 1.5,
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          rtl: true, textDirection: 'rtl',
          callbacks: { label: ctx => ` ${ctx.parsed.x} ארגונים` }
        }
      },
      scales: {
        x: {
          ticks: { precision: 0, font: { family: 'Heebo', size: 12 }, color: '#5a6478' },
          grid: { color: '#e2e6ea' },
          border: { color: '#e2e6ea' }
        },
        y: {
          ticks: { font: { family: 'Heebo', size: 13 }, color: '#1a202c' },
          grid: { display: false },
          border: { display: false }
        }
      }
    }
  });
}

// ── Accordion ──
function renderAccordion(filtered) {
  const meta = document.getElementById('resultMeta');
  meta.textContent = `${filtered.length} ארגונים מוצגים`;

  const container = document.getElementById('accordion');
  // Sort cats by count desc in current filter
  const sorted = [...CATS].sort((a,b) => {
    const ca = filtered.filter(d => (d.parsed_categories||[]).includes(a)).length;
    const cb = filtered.filter(d => (d.parsed_categories||[]).includes(b)).length;
    return cb - ca;
  });

  container.innerHTML = sorted.map(cat => {
    const orgs = filtered.filter(d => (d.parsed_categories||[]).includes(cat));
    const isOpen = expanded.has(cat);
    const color  = CAT_COLOR[cat] || '#475569';
    const bodyHtml = orgs.length === 0
      ? `<div class="empty">אין ארגונים התואמים את הסינון בתחום זה</div>`
      : `<div class="org-list">${orgs.map(org => {
          const contact = [org['איש קשר'], org['טלפון']].filter(Boolean).join(' · ');
          const locs = (org.locations||[]).map(l => `<span class="tag">📍 ${l}</span>`).join('');
          const desc = org['תיאור/פרויקטים'] || org['תחום פעילות'] || '';
          const descTrunc = desc.length > 300 ? desc.slice(0,300)+'…' : desc;
          return `<div class="org-row">
            <div class="org-row-head">
              <span class="org-name">${org['שם הארגון']}</span>
              ${contact ? `<span class="org-contact">${contact}</span>` : ''}
            </div>
            ${locs ? `<div class="org-tags">${locs}</div>` : ''}
            ${descTrunc ? `<div class="org-desc">${descTrunc}</div>` : ''}
          </div>`;
        }).join('')}</div>`;

    return `<div class="acc-item">
      <div class="acc-header" onclick="toggle('${cat.replace(/'/g,"\\'")}')">
        <div class="acc-left">
          <div class="acc-stripe" style="background:${color}"></div>
          <span class="acc-name">${cat}</span>
        </div>
        <div class="acc-right">
          <span class="acc-count">${orgs.length}</span>
          <span class="acc-chevron ${isOpen ? 'open' : ''}">▾</span>
        </div>
      </div>
      <div class="acc-body ${isOpen ? 'open' : ''}">${bodyHtml}</div>
    </div>`;
  }).join('');
}

function toggle(cat) {
  if (expanded.has(cat)) expanded.delete(cat); else expanded.add(cat);
  renderAccordion(getFiltered());
}

function render() {
  const f = getFiltered();
  updateKPIs(f);
  renderChart(f);
  renderAccordion(f);
}

document.getElementById('locFilter').addEventListener('change', render);
render();
</script>
</body>
</html>'''

    with open('young-organizations-dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Done — {len(html):,} bytes written.")

generate_dashboard()
