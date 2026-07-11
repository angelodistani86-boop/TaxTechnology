# Piano News Banche · rilascio graduale a 6 mesi

Progetto: dashboard settimanale sulle banche italiane monitorate, con arricchimento progressivo delle anagrafiche e ampliamento delle fonti regionali. Automazione via GitHub Actions cron + Claude Sonnet 4.6 con prompt caching aggressivo per contenere i token.

Origine di questa versione: la richiesta del 25 giugno 2026 ("prima pagina di valore in news banche, aggiornamento settimanale, ricerca approfondita su 3-4 banche nuove ogni settimana, senza consumare tantissimi token, ordine cronologico decrescente, card banca solo su click sul nome, arricchimento progressivo con dipendenti/attivo/utile").

---

## Vincoli e principi guida

- **Budget token**: obiettivo < $2/mese di Claude API. Ottenuto con: prompt caching ephemeral sul template (–75% input), max 150 articoli grezzi per run, `max_tokens` output = 4000, chiamata singola settimanale invece che bisettimanale.
- **Rotazione**: ogni settimana l'agente approfondisce 3-4 banche fra quelle **meno recentemente coperte**, non tutte insieme.
- **Onestà editoriale**: se un dato non è verificabile, resta `null`. Nessun campo inventato.
- **Fonti**: RSS + Google News + progressivamente siti regionali locali. Niente scraping aggressivo, niente API a pagamento.
- **Layout**: mobile-first, ordine cronologico decrescente, anagrafica banca lazy-loaded al click.

---

## Fase 1 — Fondamenta (Settimane 1–4)

**Obiettivo**: infrastruttura stabile, prima erogazione settimanale funzionante, pagina pubblicata in area riservata.

Milestone tecniche:
- [x] Nuovo template `page.html.j2` con flusso unico cronologico decrescente
- [x] Modal anagrafica banca al click sul nome (lazy, chiuso di default)
- [x] Layout responsive: card fluide, filtri drawer FAB su mobile
- [x] Cron settimanale (venerdì 06:00 UTC = 08:00 Europe/Rome) + `workflow_dispatch`
- [x] Schema `targets/banking.yaml` esteso con campi `dipendenti`, `totale_attivo_mln_eur`, `utile_ultimo_esercizio_mln_eur`, `esercizio_riferimento`
- [x] Rotazione settimanale: `sources/banking.yaml.deep_dive_rotation` + logica in `run.py`
- [x] Fonti regionali baseline aggiunte (Il Cittadino MB, Corriere Brescia, Il Giornale di Vicenza, La Provincia di Cremona, L'Eco di Bergamo, Il Gazzettino, MilanoToday economia)
- [x] Prompt aggiornato con sezione `[DEEP DIVE SETTIMANALE]`
- [x] Pagina finale `news-banche.html` disponibile in area riservata sotto "Aggiornamento Banking"

Deliverable: pagina online, agente pronto a girare al prossimo venerdì appena configurato il secret `ANTHROPIC_API_KEY`.

---

## Fase 2 — Prima ondata di deep dive (Settimane 5–8)

**Obiettivo**: coprire in profondità 12-16 banche (mai analizzate finora), con foto anagrafica completa.

Rotazione automatica:
- Sett. 5: UniCredit, Banco BPM, MPS, Mediobanca
- Sett. 6: BPER, Mediolanum, Banca Generali, FinecoBank
- Sett. 7: Credem, Banca Popolare di Sondrio, Banca Sella, Banca Ifis
- Sett. 8: illimity, BFF, Banca Sistema, Banca Profilo

Per ogni banca, l'agente cerca (via GNews query mirate):
- Ultimo bilancio depositato / relazione finanziaria
- N. dipendenti totali dichiarato
- Totale attivo (mln €)
- Utile netto ultimo esercizio (mln €)
- Composizione governance corrente

Se un dato non è reperibile da fonti pubbliche gratuite, l'agente lo lascia `null`. Angelo può integrare manualmente il campo in `targets/banking.yaml` in qualsiasi momento — il file è editabile da UI GitHub.

Al termine della Fase 2, atteso ~50% dei clienti con anagrafica finanziaria completa.

---

## Fase 3 — Deep dive banche piccole/fintech (Settimane 9–13)

Rotazione:
- Sett. 9: Cherry Bank (aggiornamento), Banca AideXa, Banca CF+, Banca Valsabbina
- Sett. 10: Banca del Fucino, Banca Passadore, Banca Investis, Banca Patrimoni Sella
- Sett. 11: Volksbank, CiviBank, Sparkasse Bolzano (aggiornamento), Banco di Sardegna
- Sett. 12: Banca Popolare Pugliese, Banca Popolare di Bari, Iccrea, Banca del Piemonte
- Sett. 13: Banca Akros, Banca Finint, Banca Galileo, Banca Reale

Focus editoriale: banche territoriali. Le fonti regionali diventano cruciali. Espansione blogroll RSS.

---

## Fase 4 — Espansione fonti regionali (Settimane 14–17)

**Obiettivo**: aggiungere 15-20 fonti locali con feed RSS attivi, mirate a intercettare notizie di banche di prossimità che i grandi giornali non coprono.

Piano fonti da valutare (ognuna testata prima dell'inserimento — se feed rotto o irrilevante, saltata):

| Regione | Testata | Priorità |
|---|---|---|
| Lombardia | Il Cittadino di Monza, PrimaMonza, Il Giorno Milano, MilanoToday, BresciaToday, BergamoNews | alta |
| Veneto | Il Gazzettino, La Nuova Venezia, Il Mattino di Padova, Verona Sera | media |
| Piemonte | La Stampa Torino, AtNews (Asti), La Provincia di Cuneo | alta (Banca di Asti) |
| Emilia | Gazzetta di Modena, Il Resto del Carlino, Piacenza Sera | media (Credem) |
| Alto Adige | Alto Adige, Corriere Alto Adige, Salto | alta (Sparkasse) |
| Nazionale | BeBeez (già inclusa), Credit Village, Idealista News, We Wealth | mantenimento |

Ampliamento query Google News: per ogni comune sede di banca cliente, aggiungere query localizzata.

---

## Fase 5 — Arricchimento anagrafica completo (Settimane 18–21)

**Obiettivo**: 100% dei 42 clienti con anagrafica finanziaria compilata + fonte di ogni dato.

Aggiunta schema `targets/banking.yaml`:
```yaml
dipendenti:
  valore: int
  esercizio: int
  fonte: url

totale_attivo_mln_eur:
  valore: float
  esercizio: int
  fonte: url

utile_ultimo_esercizio_mln_eur:
  valore: float
  esercizio: int
  fonte: url
```

Il modal anagrafica del sito viene aggiornato per mostrare esercizio di riferimento e link "vedi fonte" per ogni cifra.

L'agente in questa fase esegue un audit settimanale: per ogni cliente cerca se sono usciti nuovi bilanci/comunicati IR e propone aggiornamento del campo (via PR, l'utente conferma).

---

## Fase 6 — Consolidamento e KPI dell'agente (Settimane 22–26)

**Obiettivo**: monitoraggio della qualità dell'agente stesso.

Nuova sezione dashboard "Salute agente":
- Numero fonti attive/totali per settimana
- Notizie scartate per età / duplicato / non pertinenza (dallo `stats` del JSON LLM)
- Percentuale clienti con anagrafica finanziaria completa
- Storico costi API stimati per run
- Top 5 banche più coperte / meno coperte negli ultimi 3 mesi

Ottimizzazioni possibili in questa fase:
- Auto-detection e disabilitazione fonti RSS morte (per 3 run consecutivi 0 items → disable)
- Adaptive rotation: se una banca non ha novità reali per 4 settimane consecutive, salta un giro
- Alert su cambio revisore o cambio governance importante (già implementato flag `audit_alert`, aggiungere `governance_alert` esplicito)

---

## Cosa fa l'agente da solo (senza intervento umano)

Ogni venerdì mattina, in ordine:
1. Leggi `targets/banking.yaml` e `sources/banking.yaml`
2. Determina 3-4 banche da approfondire questa settimana (rotazione via numero settimana ISO)
3. Fetch RSS + Google News (query base + query deep dive per le banche selezionate)
4. Dedup vs `state/seen.json`
5. Chiamata Claude Sonnet 4.6 con prompt caching, budget max 4000 token output
6. Genera `news-banche.html` con nuovo template
7. Crea branch `auto/banking-YYYY-MM-DD`, apre PR verso `main`
8. Notifica email a angelodistani86@gmail.com
9. Log settimanale in `agent/state/last-run.log`

Costo atteso per run: **$0.05-0.12**. Sui 26 run del periodo totale, ~$2-4.

---

## Cosa fa Angelo (opzionale)

- Approva/scarta la PR settimanale (default: approvazione automatica se non intervieni entro 24h — feature opzionale in Fase 4)
- Aggiunge/corregge dati in `targets/banking.yaml` via UI GitHub quando trova numeri più aggiornati
- Aggiunge/rimuove fonti in `sources/banking.yaml` via UI GitHub
- Modifica regole editoriali in `prompts/banking.txt` via UI GitHub

Tutti i file sono editabili senza toccare il codice Python.

---

## Deliverable Fase 1 (già in questo commit)

- `PIANO-BANKING-6M.md` (questo file)
- `agent/templates/page.html.j2` (riscritto)
- `agent/targets/banking.yaml` (schema esteso)
- `agent/sources/banking.yaml` (fonti regionali + rotazione)
- `agent/prompts/banking.txt` (rotazione + deep dive)
- `agent/run.py` (logica rotazione)
- `.github/workflows/banking-update.yml` (cron settimanale)
- `news-banche.html` (prima pagina generata da mock)
- `index.html` (link in area riservata)

---

## Rischi noti

- **Feed RSS fragili**: alcuni feed regionali vanno offline senza preavviso. Mitigazione: log per fonte, opzione `enabled: false`, in Fase 6 auto-disable.
- **Duplicati mascherati**: notizie ripubblicate con titoli leggermente diversi possono sfuggire al dedup URL. Mitigazione: dedup basato su hash titolo normalizzato in Fase 3.
- **Dati finanziari non pubblici**: alcune banche piccole non pubblicano bilanci consolidati facilmente reperibili online. Mitigazione: accettare `null`, arricchimento manuale se necessario.
- **Claude API price change**: se il pricing cambia in modo significativo, rivalutare frequenza (settimanale → quindicinale) o modello (Sonnet → Haiku per la maggior parte, Sonnet solo per deep dive).
