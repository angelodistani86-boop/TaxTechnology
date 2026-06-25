# AGENTS.md — istruzioni per agenti AI che lavorano su questo repo

Questo file istruisce un agente AI (Claude Code, Cursor, GitHub Copilot Workspace, Aider, Continue, qualsiasi cosa legga `AGENTS.md`) su come lavorare in questo repository nello stesso modo in cui ci ha lavorato il primo agente. Leggilo prima di proporre qualsiasi modifica.

---

## 1. Cos'è questo repo

Sito personale di **Angelo Di Stani** — Tax Technology & AI — servito da **GitHub Pages** sotto il dominio custom **angelodistani.com**.

- Repo: `angelodistani86-boop/taxtechnology`
- Branch di pubblicazione: **`main`** (push diretto = live in ~1 minuto)
- Hosting: GitHub Pages (file statici, niente backend)
- CNAME: `angelodistani.com`

Il sito è un **hub personale** con tre tipi di contenuto:
- **Strumenti fiscali** (calcolatori, dashboard) — sezione *Progetti & pagine condivise*
- **News banche** — dashboard + Excel
- **Ritratti editoriali** (omaggi a persone/istituzioni) — sezione *For fun* o area riservata

---

## 2. Struttura del repo

```
/
├── index.html                  ← homepage, menu accordion + gate password JS
├── Index.html                  ← DUPLICATO con I maiuscola, da tenere sincronizzato
├── CNAME                       ← angelodistani.com
├── AGENTS.md                   ← questo file
├── .gitignore
│
├── <slug>.html                 ← pagine pubbliche nella root (una per voce di menu)
│   es. acconto-imposte-dirette-2026.html
│       ravvedimento-operoso.html
│       cnm-dashboard.html
│       smart-tax-suite.html
│       banca-csr.html
│       sparkasse-bolzano.html
│       vito-pennetta.html
│       francesco-trivisano.html
│
├── mockup/                     ← mockup HTML interattivi (Banking dashboard)
│   └── banking-mockup-b.html   ← variante scelta dall'utente
│
├── excel/                      ← dati operativi
│   ├── banking-news.xlsx       ← foglio News + Clienti + Vocabolari
│   └── banking-news.md         ← guida operativa + script Python xlsx→HTML
│
├── agent/                      ← pipeline Python per generazione Banking page
│   ├── run.py, fetchers/, summarize.py, render.py, open_pr.py
│   ├── sources/banking.yaml, targets/banking.yaml, prompts/banking.txt
│   ├── templates/page.html.j2  ← template Jinja2 = mockup B v3
│   └── requirements.txt
│
└── .github/workflows/
    └── banking-update.yml      ← cron Mar/Ven 06:00 UTC, dispatch manuale
```

**Regola importante:** ogni volta che modifichi `index.html`, ricordati di copiarlo su `Index.html` (alcune URL casing-sensitive lo richiedono):

```bash
cp index.html Index.html
```

---

## 3. Convenzioni HTML / CSS

### Stack
- **HTML + CSS + JS vanilla** — niente framework, niente build step
- Google Fonts da CDN: `Fraunces` (serif editoriale), `Inter` (sans-serif UI), `JetBrains Mono` (mono)
- Tutto il CSS è **inline nel `<style>` della pagina** — nessun foglio condiviso (ogni pagina è autonoma)
- Stesso vale per JS: inline nello `<script>` della pagina

### Palette di base (terracotta — usata in tutto il sito)

```css
:root{
  --bg:#faf9f5;
  --paper:#ffffff;
  --ink:#1f1e1c;
  --ink-soft:#3d3a35;
  --muted:#6b675e;
  --line:#e8e4d8;
  --line-soft:#f1ede1;
  --accent:#cc785c;          /* terracotta */
  --accent-deep:#a85a40;
  --accent-soft:#f4e4dc;
  --warm:#f5f1e6;
  --warm-deeper:#ede6d3;
  --gold:#c8a951;
  --gold-soft:#fbf4dc;
  --green:#5a8f6b;
  --green-soft:#e4ede2;
  --blue:#5a7a9f;
  --blue-soft:#e1e8ef;
  --shadow-sm:0 1px 2px rgba(31,30,28,.04);
  --shadow-md:0 4px 16px -4px rgba(31,30,28,.08), 0 1px 3px rgba(31,30,28,.04);
  --shadow-lg:0 24px 60px -20px rgba(31,30,28,.18), 0 6px 14px rgba(31,30,28,.05);
}
```

Per pagine "tematiche" (Sparkasse, Vito@Zambon, Francesco@Deloitte) **deroga sull'accent**: rosso tirolese, verde farmaceutico, verde Deloitte. Resta tutto il sistema (ink, line, warm, shadow). Mai cambiare il `--bg`: deve essere sempre `#faf9f5` per coerenza visiva fra le pagine.

### Struttura ricorrente di una "pagina ritratto"

```
<nav.top>                  ← sticky, brand sx + ul ancore dx
<header.hero>              ← grid 1.15fr .85fr (testo + emblem-wrap)
  <eyebrow>                ← pillola accent uppercase
  <h1>                     ← Fraunces 40-68px, em italic colorato
  <role>                   ← Inter 17px ink-soft
  <firm>                   ← 14px muted con .mark colorato
  <lead>                   ← 17.5px ink-soft max-width 58ch
  <cta-row>                ← btn-primary + btn-ghost
  <emblem-wrap>            ← box 4/5 con SVG sfondo + monogramma + ribbon
<main>                     ← grid 1.4fr .9fr (content + aside)
  sezioni.card             ← bianche, border line, radius 20px, shadow-sm
    <kicker>               ← 11px uppercase letterspaced colorato
    <h2>                   ← Fraunces 28px con em italic
    facts / virtues / timeline / tags / blockquote
  aside
    .card.ode-box          ← card scura accent (verde scuro / rosso scuro / nero)
    altre cards
<footer>                   ← border-top, 2 colonne
```

Per **strumenti di calcolo** (ravvedimento-operoso, acconto-imposte-dirette) layout più verticale single-column max-width 780-820px, sezioni numerate con `badge` rotondo (α β γ δ).

### Responsive

- Breakpoint principali: `880px` (sidebar→stack), `680px` (nav menu→hide), `560px` (font/padding ridotti)
- Mobile-first nei filtri/drawer: se la pagina ha filtri laterali, su mobile diventano drawer + FAB sticky in basso (vedi `mockup/banking-mockup-b.html`)

### Accessibilità minima

- `lang="it"` sempre
- `<meta viewport>` con `viewport-fit=cover`
- `<meta name="description">` significativo
- `aria-label` su emblem e icone
- `target="_blank" rel="noopener"` su link esterni

---

## 4. Tipi di pagina

### A) Strumenti di calcolo (in *Progetti & pagine condivise*)

Esempi: `ravvedimento-operoso.html`, `acconto-imposte-dirette-2026.html`

Schema:
1. Header sticky con eyebrow + h1 + lead + nav inline
2. Sezione "Cos'è" — citazione normativa in `.blk` warm con border-left accent
3. Sezione "Tabella scaglioni" — `table.scag` con codici e percentuali tabular-nums
4. Sezione "Calcolatore" — form 2 colonne + result panel `linear-gradient(warm, warm-deeper)`
5. Sezione "Esempi pratici" — 3 card affiancate
6. Disclaimer in `.footer-note` gold-soft

JS: vanilla, IIFE, listener `input` e `change`, formattazione `toLocaleString('it-IT')` per euro.

### B) Dashboard (in *Progetti & pagine condivise* o *News banche*)

Esempi: `cnm-dashboard.html`, `smart-tax-suite.html`, `mockup/banking-mockup-b.html`

Layout con sidebar filtri sticky + grid card. Filtri client-side `data-*` su `article.card` + checkbox toggle. Su mobile: drawer + FAB.

### C) Ritratti editoriali (in *For fun* o area riservata)

Esempi: `banca-csr.html`, `sparkasse-bolzano.html`, `vito-pennetta.html`, `francesco-trivisano.html`

Schema fisso: hero con emblem 4/5 + sezioni "Perché"/"Virtù"/"Storia"/"Numeri" + aside con ode-box scura.

**Regole irrinunciabili per i ritratti di persona:**
- Tono editoriale, omaggio leggero, **mai** dati personali inventati
- Solo info da fonti pubbliche verificabili (LinkedIn, sito aziendale, stampa)
- Sempre link al LinkedIn pubblico se trovato, con disclaimer "ruolo reso pubblico dall'interessato"
- Sempre clausola di chiusura: *"se domani [Nome] preferisce rimuoverla basta un messaggio: viene giù in cinque minuti"*

---

## 5. La homepage `index.html`

Menu a fisarmonica con 4 sezioni (in quest'ordine):

1. **Progetti & pagine condivise** (pubblico) — strumenti fiscali
2. **News banche** (pubblico) — dashboard + Excel + guida
3. **For fun** (pubblico) — ritratti editoriali leggeri
4. **Area riservata** (gate password client-side)
   - `listShared` — visibile con password `jointhetaxrevolution`
   - `listOwner` — visibile con password `angelo44` (solo per il proprietario)

**Attenzione:** il gate password è **solo visivo** (JS client-side). I file HTML sono comunque accessibili a chiunque conosca l'URL diretto. Per vera privacy serve un altro hosting (Cloudflare Access). Documentalo se metti qualcosa di "riservato".

Quando aggiungi una pagina:
1. Crea il `.html` nella root
2. Aggiungi una `<li><a>` nella sezione corretta dell'`index.html`
3. **Copia** `index.html` su `Index.html`
4. Commit + push

---

## 6. Workflow di lavoro

Lo stile dell'utente è **veloce, diretto, decisionale**. Non chiedere conferma per cose ovvie. Procedi e mostra il risultato.

### Sequenza standard per una nuova pagina

```
1. Capisci la richiesta (1 sec)
2. Se servono dati esterni reali: WebSearch (e/o WebFetch su URL noti)
   - NIENTE dati inventati su persone, aziende, normative
   - Se non trovi: di' chiaramente "non ho trovato X" e proponi alternativa
3. Per ricerche ampie (>3 query): delega ad Agent subagent_type=Explore
4. Costruisci il file HTML autonomo (CSS+JS inline)
5. Aggiorna index.html nella sezione giusta
6. cp index.html Index.html (sync)
7. git add <file> index.html Index.html
8. git commit con messaggio dettagliato italiano + footer session
9. git push origin main
10. Risposta utente: link githack preview + link live + breve riassunto
```

### Git

- Lavora **direttamente su `main`** per le aggiunte normali (è un sito personale, niente review formale richiesta)
- Branch separati solo se l'utente lo chiede esplicitamente
- **Mai** `--force` su `main`
- **Mai** skip hooks o disabilitare GPG senza che l'utente lo chieda
- Push retry: se network fail, esponenziale (2s, 4s, 8s, 16s) max 4 tentativi

### Formato commit

```
Titolo conciso (50-72 char) in italiano, imperativo gentile

Paragrafo che spiega COSA e PERCHÉ. Multi-riga ok.
Elenco puntato se servono molti dettagli:
- file aggiunto X
- modifica Y a index
- nota Z

URL di sessione opzionale a fondo (se in Claude Code):
https://claude.ai/code/session_xxx
```

Esempio:
```
Aggiunge pagina 'Ravvedimento operoso' con calcolatore interattivo

Strumento di calcolo aggiornato alla riforma D.Lgs. 87/2024:
- tabella degli 8 scaglioni di ritardo con riduzioni
- calcolatore: importo + scadenza + data versamento -> sanzione, interessi, totale
- 3 esempi pratici
- codici tributo F24 (8901/8904 sanzioni, 1989/1991 interessi)

Voce aggiunta in 'Progetti & pagine condivise'. Index sync.
```

### Risposte all'utente

- **Brevi e dirette** — l'utente lavora veloce, vuole link e conferma
- Dai sempre:
  - URL **live**: `https://angelodistani.com/<file>.html`
  - URL **preview immediata**: `https://raw.githack.com/angelodistani86-boop/TaxTechnology/main/<file>.html`
- Riepiloga in 3-5 righe cosa hai fatto
- Sources citate come bullet list di link Markdown alla fine se hai usato WebSearch

---

## 7. Strumenti / MCP / Skills

### Strumenti che usi spesso

- **WebSearch / WebFetch** — caricabili via ToolSearch (`select:WebSearch,WebFetch`)
- **GitHub MCP** — caricabili via ToolSearch (`mcp__github__*`) per PR/issue/branch checks
- **Agent Explore** — per ricerche multi-step su dati esterni
- **Bash** — per `git`, `cp`, `mkdir`, `ls`

### Strumenti che NON ci sono

- `gh` CLI: usa GitHub MCP via `mcp__github__*`
- `openpyxl` / `xlsxwriter` non disponibili via pip in questo ambiente: per generare xlsx usa zip+XML stdlib (vedi `excel/banking-news.md` per il pattern)
- LibreOffice headless presente ma può non avviarsi: non affidarcisi per validation

### Skills disponibili (Claude Code)

- `/verify` — verifica una PR runnando l'app
- `/code-review` — review del diff
- `/init` — inizializza CLAUDE.md
- `/run` — lancia l'app per screenshot

---

## 8. Scelte già fatte (NON discutere a meno di richiesta esplicita)

- ✅ Sito = HTML statico su GitHub Pages, **no framework**
- ✅ Inline CSS+JS per pagina autonoma (nessuna dipendenza fra file)
- ✅ Push diretto su `main` (no PR review formale)
- ✅ Dashboard Banking = mockup B v3 (3 colonne filtri + drawer mobile)
- ✅ Agent Python con Claude Sonnet 4.6 (`claude-sonnet-4-6`) per il flusso Banking automatico
- ✅ Cron Mar/Ven 06:00 UTC (Mar+Ven 08:00 Europe/Rome)
- ✅ Lingua: tutto in italiano (testi, commit, commenti)
- ✅ Tono editoriale serio per gli strumenti, leggero/affettuoso per i ritratti
- ✅ Niente emoji nei file di output (CSS, HTML, JS, MD) salvo richiesta esplicita

---

## 9. Pattern di scrittura per i contenuti editoriali

- **Periodi corti**, ma con un ritmo curato (Fraunces aiuta la cadenza visiva)
- Italianismo elegante, niente anglicismi inutili (preferisci "consulenza" a "consulting" se il senso non cambia)
- Citazioni in `<blockquote>` con `<cite>` per la fonte
- Date: formato lungo italiano (`6 novembre 1854`, `marzo 2026`)
- Numeri/cifre: separatore migliaia con punto, decimali con virgola (`12,5 mld`, `1.300 dipendenti`)
- Codici/normative in `<code>` o `<b>` (es. `art. 13 D.Lgs. 472/1997`)

---

## 10. Cosa NON fare

- ❌ NON inventare dati personali su persone reali (anche amici dell'utente)
- ❌ NON dare numeri/dati di bilancio non verificati
- ❌ NON aggiungere framework, build step, package.json al repo
- ❌ NON modificare `CNAME`
- ❌ NON force-pushare su `main`
- ❌ NON committare il file `banking-daily.html` dopo un test locale: viene generato dall'agente via PR
- ❌ NON committare `agent/state/last-run.log` (già in `.gitignore`)
- ❌ NON aggiungere emoji nei file output
- ❌ NON aggiungere commenti di codice "ovvi" che spiegano cosa il codice già dice

---

## 11. Cosa CHIEDERE all'utente

Solo se davvero serve. Esempi legittimi:
- Soggetto ambiguo ("crea una pagina su X" se X ha più interpretazioni)
- Scelta visiva critica (palette quando ci sono 2-3 candidati credibili)
- Pubblicazione di contenuto sensibile (es. dati di un amico che vanno oltre LinkedIn pubblico)

Altrimenti: **fai, mostra, chiedi solo dopo se non funziona**.

---

## 12. Quick reference: voci di menu attuali

```
Progetti & pagine condivise           ← pubblica
├── Acconto imposte dirette 2026
├── Ravvedimento operoso
├── Smart Tax Suite
└── Dashboard Dichiarazione CNM

News banche                            ← pubblica
├── Dashboard Aggiornamento Banking   (mockup/banking-mockup-b.html)
├── Foglio Excel news banche          (excel/banking-news.xlsx)
└── Guida operativa Excel → HTML      (excel/banking-news.md)

For fun                                ← pubblica
├── Quanto è stupenda la Banca CSR
└── Cassa di Risparmio di Bolzano — Sparkasse

Area riservata · gate password
├── listShared (pwd: jointhetaxrevolution)  — vuoto al momento
└── listOwner  (pwd: angelo44)
    ├── Vito Pennetta — un amico in Zambon
    └── Francesco Trivisano — un amico in Deloitte
```

Aggiornare questa sezione quando si aggiunge/sposta una pagina.
