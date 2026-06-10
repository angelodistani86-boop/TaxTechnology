# Aggiornamento Banking — gestione via Excel

Manuale operativo del foglio `banking-news.xlsx` e dei due flussi di pubblicazione:
**(A) generazione di una pagina HTML statica con la stessa UX del mockup B v3**
e **(B) caricamento del foglio in un sito terzo** (Google Sites, Notion, Webflow, WordPress, SharePoint).

---

## 1. Contenuto del file `banking-news.xlsx`

Tre fogli, ognuno una tabella piatta. Tutte le celle sono testo (per stabilità nei vari parser); le date sono in formato ISO `YYYY-MM-DD`.

### Foglio 1 — `News`

Una riga per ogni notizia. Chiave primaria `id` (numerico, incrementale).

| Colonna | Tipo | Obbl. | Esempio | Note |
|---|---|---|---|---|
| `id` | int | sì | `1` | Univoco. Usa `MAX+1` quando aggiungi una riga. |
| `cliente_slug` | str | sì | `intesa` | Deve corrispondere ad uno `slug` del foglio Clienti. |
| `cliente_nome` | str | sì | `Intesa Sanpaolo` | Si può popolare con `=VLOOKUP(B2,Clienti.A:B,2,FALSE)`. |
| `fascia` | str | sì | `top10` | Uno tra `top10` / `media` / `piccola`. Anche questa via VLOOKUP. |
| `data` | str ISO | sì | `2026-05-08` | `YYYY-MM-DD`. Niente data Excel nativa per evitare ambiguità. |
| `titolo` | str | sì | `Messina: «Distribuiremo 10 mld»` | Max ~95 caratteri. |
| `sintesi` | str | sì | `Q1 2026 utile 2,8 mld...` | 2 righe, max ~200 caratteri. |
| `dettaglio` | str | no | `Annunciata nuova ondata di buyback...` | Opzionale, max ~250 caratteri. |
| `tipo` | str | sì | `intervista-ceo` | Uno tra `risultati` / `comunicato` / `intervista-ceo` / `operazione-straordinaria` / `fisco` / `altro`. |
| `emittente_slug` | str | sì | `bloomberg` | Slug normalizzato (vedi foglio Vocabolari). |
| `emittente_label` | str | sì | `Bloomberg` | Etichetta visualizzata. |
| `url` | str | sì | `https://www.bloomberg.com/...` | Link alla fonte originale. |
| `audit_alert` | str | sì | `FALSE` | `TRUE` o `FALSE`. Mettilo a `TRUE` se la notizia segnala un cambio del revisore. |

### Foglio 2 — `Clienti`

Anagrafica delle 42 banche monitorate. Aggiorna a mano una volta l'anno dopo i bilanci.

| Colonna | Esempio | Note |
|---|---|---|
| `slug` | `intesa` | Stabile, lowercase, no spazi. |
| `nome` | `Intesa Sanpaolo` | Etichetta visualizzata. |
| `fascia` | `top10` | `top10` / `media` / `piccola`. |
| `revisore` | `EY S.p.A.` | Lascia vuoto se non noto. |
| `ultimo_esercizio_revisionato` | `2025` | Anno (int). |
| `incarico_fino_al` | `2029` | Anno (int) o vuoto. |
| `ad` | `Carlo Messina` | AD/CEO attuale. |
| `presidente` | `Gian Maria Gros-Pietro` | |

### Foglio 3 — `Vocabolari`

Tabella di lookup con i valori validi per le colonne categoriche. Una riga = `(dimensione, slug, label_estesa)`. Serve per:
- ricordare quali valori sono ammessi (`tipo`, `fascia`, `emittente`),
- alimentare la **Data Validation** delle colonne in `News` (vedi §2),
- rendere coerenti le label visualizzate.

---

## 2. Come aggiornare l'Excel

### Aggiungere una notizia

1. Apri `banking-news.xlsx`, vai al foglio `News`.
2. Sotto l'ultima riga, scrivi `id = MAX+1`.
3. Compila `cliente_slug` con uno slug del foglio `Clienti`.
4. Popola `cliente_nome` e `fascia` (a mano o con `VLOOKUP`).
5. Inserisci `data` in formato `YYYY-MM-DD` (es. `2026-05-24`).
6. Compila `titolo`, `sintesi`, `dettaglio` (opzionale).
7. Scegli `tipo` da: `risultati` / `comunicato` / `intervista-ceo` / `operazione-straordinaria` / `fisco` / `altro`.
8. Imposta `emittente_slug` e `emittente_label` da `Vocabolari`.
9. Incolla l'URL fonte.
10. Lascia `audit_alert = FALSE` (o `TRUE` se è un cambio revisore).

### Aggiungere una nuova banca cliente

1. Vai al foglio `Clienti`.
2. Aggiungi la riga con `slug` univoco (lowercase, senza spazi: es. `nuova-cassa`).
3. Compila almeno `nome`, `fascia`. Gli altri campi audit possono essere completati in seguito.

### Attivare la Data Validation (consigliato, una tantum)

In Excel: **Dati → Convalida dati → Elenco → Origine** =
- per `fascia`:    `=Vocabolari!B2:B4`
- per `tipo`:      `=Vocabolari!B5:B10`
- per `emittente_slug`: `=Vocabolari!B11:B25`

Così quando aggiungi una news non puoi sbagliare il valore della categoria.

### Convenzioni da rispettare per non rompere il render

- `data` sempre in `YYYY-MM-DD`. Niente formato italiano `DD/MM/YYYY` o data Excel formattata.
- `slug` sempre lowercase, senza spazi, niente accenti (usa trattini).
- `url` deve iniziare con `http://` o `https://`.
- `audit_alert` deve essere la stringa `TRUE` o `FALSE` (case-sensitive).
- Niente celle unite (merge), niente intestazioni multilivello: una tabella piatta.

---

## 3. Visualizzare le notizie come nella dashboard HTML

L'obiettivo è ottenere una pagina con la stessa UX del [mockup B v3](https://raw.githack.com/angelodistani86-boop/TaxTechnology/claude/site-index-public-pages-kjgsk/mockup/banking-mockup-b.html): filtri multipli (tipologia, fascia, cliente, emittente, periodo), tag cliente su ogni card, drawer mobile.

### Opzione A — Script Python (consigliata, design coerente)

Lo script `excel_to_html.py` qui sotto legge l'`xlsx` e produce un HTML statico identico al mockup. Lo puoi eseguire ad ogni update dell'Excel.

**Prerequisiti**
```bash
pip install openpyxl jinja2
```

**Uso**
```bash
# 1. Genera la pagina
python excel_to_html.py banking-news.xlsx banking-news.html

# 2. Apri in locale per controllare
open banking-news.html      # macOS
xdg-open banking-news.html  # linux
start banking-news.html     # windows

# 3. Carica sul tuo "altro sito" via FTP/dashboard hosting
```

**Script `excel_to_html.py`** (autonomo, ~80 righe; il template HTML è quello già nel repo `agent/templates/page.html.j2` — copiacelo accanto allo script):

```python
#!/usr/bin/env python3
"""Converte banking-news.xlsx in HTML usando il template del mockup B v3."""
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import load_workbook
from jinja2 import Environment, FileSystemLoader, select_autoescape

# --- date helpers (italiano) ---
MM_SHORT = ['gen','feb','mar','apr','mag','giu','lug','ago','set','ott','nov','dic']
DAY_SHORT = ['Lun','Mar','Mer','Gio','Ven','Sab','Dom']
def fmt_date_short(v):
    d = v if isinstance(v, datetime) else datetime.fromisoformat(str(v))
    return f"{d.day:02d} {MM_SHORT[d.month-1]} {d.year}"
def fmt_date_long(v):
    d = v if isinstance(v, datetime) else datetime.fromisoformat(str(v))
    return f"{DAY_SHORT[d.weekday()]} {d.day} {MM_SHORT[d.month-1].capitalize()} {d.year}"

def read_table(ws):
    """Worksheet → list[dict] usando la riga 1 come header."""
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = [str(c).strip() if c is not None else '' for c in rows[0]]
    out = []
    for r in rows[1:]:
        if all(c is None or str(c).strip() == '' for c in r):
            continue
        out.append({header[i]: (r[i] if r[i] is not None else '') for i in range(len(header))})
    return out

def main(xlsx_path, out_path, template_dir='.'):
    wb = load_workbook(xlsx_path, data_only=True)
    news_raw = read_table(wb['News'])
    clienti = read_table(wb['Clienti'])

    # normalizza tipi
    items = []
    for n in news_raw:
        items.append({
            'cliente_slug': str(n['cliente_slug']),
            'fascia': str(n['fascia']),
            'data': str(n['data']),
            'titolo': str(n['titolo']),
            'sintesi': str(n['sintesi']),
            'dettaglio': str(n.get('dettaglio') or ''),
            'tipo': str(n['tipo']),
            'emittente_slug': str(n['emittente_slug']),
            'emittente_label': str(n['emittente_label']),
            'url': str(n['url']),
            'audit_alert': str(n.get('audit_alert', 'FALSE')).upper() == 'TRUE',
        })

    # converte i campi numerici sui clienti
    for c in clienti:
        for k in ('ultimo_esercizio_revisionato','incarico_fino_al'):
            c[k] = int(c[k]) if c.get(k) not in ('', None) else None
        for k in ('revisore','ad','presidente'):
            c[k] = c.get(k) or None

    # sezioni: clienti che hanno news, ordinati come nel foglio Clienti
    by_cli = {}
    for it in items:
        by_cli.setdefault(it['cliente_slug'], []).append(it)
    sections = []
    for c in clienti:
        news = by_cli.get(c['slug'], [])
        if news:
            news.sort(key=lambda x: x['data'], reverse=True)
            sections.append({**c, 'news': news})

    # gruppi per fascia (per il filtro)
    by_fascia = {'top10': [], 'media': [], 'piccola': []}
    for c in clienti:
        by_fascia.setdefault(c['fascia'], []).append(c)

    # counter dinamici
    counters = {
        'tipo': dict(Counter(i['tipo'] for i in items)),
        'fascia': dict(Counter(i['fascia'] for i in items)),
        'cliente': dict(Counter(i['cliente_slug'] for i in items)),
        'emittente': dict(Counter(i['emittente_slug'] for i in items)),
    }

    # render
    env = Environment(loader=FileSystemLoader(template_dir),
                      autoescape=select_autoescape(['html', 'xml']),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters['fmt_date_short'] = fmt_date_short
    env.filters['fmt_date_long'] = fmt_date_long
    tpl = env.get_template('page.html.j2')

    now = datetime.now()
    html = tpl.render(
        generated_at=now,
        next_update=now + timedelta(days=3),
        sections=sections,
        all_targets=clienti,
        by_fascia=by_fascia,
        counters=counters,
        n_items=len(items),
        n_fonti=len({i['emittente_slug'] for i in items}),
        n_banche_monitorate=len(clienti),
        n_clienti_con_news=len(sections),
    )
    Path(out_path).write_text(html, encoding='utf-8')
    print(f'OK: {out_path} ({len(html):,} bytes) — {len(sections)} sezioni, {len(items)} news')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Uso: python excel_to_html.py banking-news.xlsx output.html [template_dir]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '.')
```

Il file `page.html.j2` è disponibile nel repo, in `agent/templates/page.html.j2`. Copialo nella stessa cartella dello script.

### Opzione B — Google Sheets pubblicato

1. Importa `banking-news.xlsx` in Google Sheets (File → Importa).
2. File → Condividi → Pubblica sul web → Foglio "News" → Formato `Pagina web`.
3. Ottieni un URL pubblico tipo `https://docs.google.com/spreadsheets/d/.../pubhtml`.
4. Embed via `<iframe src="…" width="100%" height="800">` in qualsiasi sito.

Pro: rapidità. Contro: layout Google, nessun filtro custom.

### Opzione C — Notion database

1. In Notion: pagina nuova → `/database` → Tabella.
2. Vai sull'Excel: salva il foglio `News` come CSV (UTF-8).
3. In Notion: `…` → Import → CSV → carica il file.
4. Configura proprietà come Select (tipo, fascia, emittente, cliente).
5. Crea viste filtrate ("Solo Risultati ultimi 30 giorni", "Cherry Bank", ecc.).
6. Pubblica con "Share to web" se vuoi esposizione esterna.

Pro: filtri nativi senza codice. Contro: estetica Notion.

### Opzione D — WordPress + plugin tabella

1. Plugin tipo *TablePress*, *wpDataTables*, *Ninja Tables*.
2. Importa CSV/xlsx direttamente da admin.
3. Abilita filtri sulle colonne `tipo` / `fascia` / `cliente_nome`.
4. Inserisci shortcode in una pagina.

Pro: integrazione nativa WP. Contro: design del tema, JS non personalizzabile facilmente.

### Opzione E — SharePoint/OneDrive embed

1. Carica `banking-news.xlsx` su SharePoint/OneDrive.
2. Apri online → File → Condividi → Embed → copia il codice `<iframe>`.
3. Incolla l'iframe nella pagina del tuo sito.

Pro: zero conversioni. Contro: richiede account Microsoft per i visitatori in alcuni casi.

---

## 4. Workflow editoriale consigliato

```
1. Apri banking-news.xlsx (settimanalmente)
2. Aggiungi nuove news nel foglio "News" (~10-20 minuti)
3. Salva
4a. (Opzione A) python excel_to_html.py banking-news.xlsx out.html
   → carica out.html sul sito via FTP/CMS
4b. (Opzione B/C/D/E) re-importi su Google Sheets/Notion/WP/SharePoint
5. Verifica nel browser che i filtri funzionino
```

Per restare allineato con lo stile editoriale del progetto: tieni il `sintesi` sotto 200 caratteri, `dettaglio` sotto 250, e segnala con `audit_alert=TRUE` ogni cambio di revisore — è uno dei segnali che lo studio vuole tracciare.

---

## 5. Estensione a Tax Tech / Studi fiscali

Per replicare lo stesso schema su altri topic (V2/V3 del progetto): duplica `banking-news.xlsx` in `taxtech-news.xlsx` e `studi-news.xlsx`, mantieni le stesse 13 colonne nel foglio News e gli stessi vocabolari (eventualmente aggiungendo nuove `tipo`). Lo script Python è già pronto per altri topic: basta passare l'xlsx giusto.
