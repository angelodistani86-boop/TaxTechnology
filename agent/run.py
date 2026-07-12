"""Orchestratore dell'agente News Banche.

Ogni venerdì:
- Fetch RSS + Google News (query base)
- Rotazione settimanale: 4 banche da approfondire (deep dive) + query dedicate
- Chiamata Claude Sonnet con prompt caching, budget 4000 token output
- Render HTML + PR verso main
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent

from agent.render import render_page

STATE_DIR = ROOT / 'state'
SEEN_FILE = STATE_DIR / 'seen.json'
LOG_FILE = STATE_DIR / 'last-run.log'


def _log(msg: str) -> None:
    print(msg)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(f'[{datetime.utcnow().isoformat()}] {msg}\n')


def _load_yaml(rel: str):
    return yaml.safe_load((ROOT / rel).read_text(encoding='utf-8'))


def _load_state():
    if SEEN_FILE.exists():
        try:
            return json.loads(SEEN_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'seen_hashes': []}


def _save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def _hash_url(url: str) -> str:
    return hashlib.sha1(url.encode('utf-8')).hexdigest()[:16]


def _next_update(now: datetime) -> datetime:
    """Domattina alle 08:00 Europe/Rome (aggiornamento giornaliero)."""
    return (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)


def _select_deep_banks(sources: dict, targets: dict, override: str = '') -> list:
    """Seleziona N banche da approfondire questa settimana.

    - Se override != '', usa la lista di slug forniti (via workflow_dispatch input).
    - Altrimenti: settimana ISO -> offset deterministico nella rotation list.
    Ritorna lista di dict target completi.
    """
    rotation_cfg = sources.get('deep_dive_rotation', {})
    n = int(rotation_cfg.get('banks_per_week', 4))
    order = rotation_cfg.get('order', []) or []
    clienti = {c['slug']: c for c in targets.get('clienti', [])}

    if override:
        slugs = [s.strip() for s in override.split(',') if s.strip()]
    elif order:
        iso_week = datetime.utcnow().isocalendar()[1]
        offset = (iso_week * n) % len(order)
        slugs = [order[(offset + i) % len(order)] for i in range(n)]
    else:
        slugs = []

    return [clienti[s] for s in slugs if s in clienti]


def _deep_dive_query(banca: dict) -> dict:
    """Query GNews mirata all'anagrafica di una singola banca."""
    aliases = banca.get('query_alias') or [banca['nome']]
    quoted = ' OR '.join(f'"{a}"' for a in aliases[:3])
    q = f'({quoted}) (bilancio OR dipendenti OR "totale attivo" OR utile OR "amministratore delegato") when:180d'
    return {'label': f'deep-{banca["slug"]}', 'query': q}


def _do_fetch(sources: dict, extra_gnews: list = None) -> list:
    from agent.fetchers.rss import fetch_rss
    from agent.fetchers.gnews import fetch_gnews
    raw: list = []
    for f in sources.get('rss', []):
        if not f.get('enabled', True):
            continue
        try:
            items = fetch_rss(f['url'], f['name'])
            _log(f'RSS [{f["name"]}]: {len(items)} items')
            raw.extend(items)
        except Exception as e:
            _log(f'RSS [{f["name"]}]: ERRORE {type(e).__name__}: {e}')
    all_q = list(sources.get('gnews_queries', []) or []) + list(extra_gnews or [])
    for q in all_q:
        try:
            items = fetch_gnews(q['query'], q['label'])
            _log(f'GNews [{q["label"]}]: {len(items)} items')
            raw.extend(items)
        except Exception as e:
            _log(f'GNews [{q["label"]}]: ERRORE {type(e).__name__}: {e}')
    return raw


def _build_deep_prompt_section(banche: list) -> str:
    if not banche:
        return "(nessuna deep dive questa settimana)"
    lines = []
    for b in banche:
        aliases = ', '.join(b.get('query_alias', []) or [b['nome']])
        current = []
        if b.get('dipendenti') is not None:
            current.append(f"dipendenti: {b['dipendenti']}")
        if b.get('totale_attivo_mln_eur') is not None:
            current.append(f"attivo: {b['totale_attivo_mln_eur']} mln€")
        if b.get('utile_ultimo_esercizio_mln_eur') is not None:
            current.append(f"utile: {b['utile_ultimo_esercizio_mln_eur']} mln€")
        cur_str = ' · attualmente noti: ' + ', '.join(current) if current else ' · anagrafica finanziaria non ancora popolata'
        lines.append(f"- **{b['nome']}** (slug: `{b['slug']}`, alias: {aliases}){cur_str}")
    return '\n'.join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description='Generatore News Banche (settimanale).')
    ap.add_argument('topic', help='Topic (es. banking)')
    ap.add_argument('--dry-run', action='store_true', help='Non aprire PR, lascia il file in working tree')
    ap.add_argument('--mock', action='store_true', help='Usa dati mock invece di fetch+LLM')
    ap.add_argument('--output', default=None, help='Percorso HTML di output')
    args = ap.parse_args()

    output_path = Path(args.output) if args.output else (REPO_ROOT / f'{args.topic}-daily.html')
    _log(f'=== Run topic={args.topic} dry_run={args.dry_run} mock={args.mock} output={output_path} ===')

    sources = _load_yaml(f'sources/{args.topic}.yaml')
    targets = _load_yaml(f'targets/{args.topic}.yaml')

    # Rotazione deep dive settimanale
    force_banks = os.environ.get('FORCE_DEEP_BANKS', '')
    deep_banks = _select_deep_banks(sources, targets, override=force_banks)
    deep_slugs = [b['slug'] for b in deep_banks]
    _log(f'Deep dive settimana ISO {datetime.utcnow().isocalendar()[1]}: {deep_slugs}')

    if args.mock:
        mock_path = ROOT / f'mock-{args.topic}.json'
        if not mock_path.exists():
            _log(f'Mock file mancante: {mock_path}')
            return 1
        result = json.loads(mock_path.read_text(encoding='utf-8'))
        _log(f'Mock caricato: {len(result.get("items", []))} items')
    else:
        from agent.summarize import summarize  # import lazy
        prompt_text = (ROOT / f'prompts/{args.topic}.txt').read_text(encoding='utf-8')
        deep_section = _build_deep_prompt_section(deep_banks)
        prompt_text = prompt_text.replace('__DEEP_BANKS_SECTION__', deep_section)

        state = _load_state()

        # Fetch: baseline + query deep dive dinamiche
        extra_gnews = [_deep_dive_query(b) for b in deep_banks]
        raw = _do_fetch(sources, extra_gnews=extra_gnews)
        _log(f'Totale articoli raccolti: {len(raw)} (di cui deep dive: {sum(1 for r in raw if r.get("source_label", "").startswith("gnews:deep-"))})')

        before = len(raw)
        seen = set(state.get('seen_hashes', []))
        raw = [r for r in raw if _hash_url(r.get('url', '')) not in seen]
        _log(f'Anti-duplicato cross-run: {before} → {len(raw)}')

        raw.sort(key=lambda r: r.get('data') or '', reverse=True)
        raw = raw[:150]  # ridotto da 200 per contenere token
        _log(f'Articoli inviati a Claude: {len(raw)}')

        result = summarize(prompt_text, raw, targets)
        _log(f'Items selezionati da Claude: {len(result.get("items", []))}')

        state['seen_hashes'] = (state.get('seen_hashes', []) + [_hash_url(r['url']) for r in raw if r.get('url')])[-3000:]
        _save_state(state)

    now = datetime.now(timezone.utc) + timedelta(hours=2)  # CEST
    next_up = _next_update(now)
    html = render_page(
        items=result.get('items', []),
        targets=targets,
        generated_at=now,
        next_update=next_up,
    )
    output_path.write_text(html, encoding='utf-8')
    _log(f'Pagina scritta: {output_path} ({len(html)} bytes)')

    if args.dry_run:
        _log('Dry-run: nessun commit / nessuna PR.')
        return 0

    from agent.open_pr import open_pr
    branch = open_pr(output_file=str(output_path.relative_to(REPO_ROOT)) if output_path.is_absolute() else str(output_path))
    _log(f'PR flow: branch={branch}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
