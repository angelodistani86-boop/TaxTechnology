"""Orchestratore dell'agente Banking (e futuri topic)."""
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
    """Mar+Ven: prossimo giorno utile alle 08:00 Europe/Rome (approx UTC+2)."""
    days_ahead = (1 - now.weekday()) % 7 if now.weekday() != 1 else 3  # next Tue or Fri
    candidates = [1, 4]  # Mar, Ven
    deltas = [((d - now.weekday()) % 7) or 7 for d in candidates]
    return (now + timedelta(days=min(deltas))).replace(hour=8, minute=0, second=0, microsecond=0)


def _do_fetch(sources: dict) -> list:
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
    for q in sources.get('gnews_queries', []) or []:
        try:
            items = fetch_gnews(q['query'], q['label'])
            _log(f'GNews [{q["label"]}]: {len(items)} items')
            raw.extend(items)
        except Exception as e:
            _log(f'GNews [{q["label"]}]: ERRORE {type(e).__name__}: {e}')
    return raw


def main() -> int:
    ap = argparse.ArgumentParser(description='Generatore pagine auto-update (Banking, …).')
    ap.add_argument('topic', help='Topic (es. banking)')
    ap.add_argument('--dry-run', action='store_true', help='Non aprire PR, lascia il file in working tree')
    ap.add_argument('--mock', action='store_true',
                    help='Usa dati mock invece di fetch+LLM (richiede agent/mock-<topic>.json)')
    ap.add_argument('--output', default=None,
                    help='Percorso HTML di output (default: <topic>-daily.html nella root del repo)')
    args = ap.parse_args()

    output_path = Path(args.output) if args.output else (REPO_ROOT / f'{args.topic}-daily.html')

    _log(f'=== Run topic={args.topic} dry_run={args.dry_run} mock={args.mock} output={output_path} ===')

    sources = _load_yaml(f'sources/{args.topic}.yaml')
    targets = _load_yaml(f'targets/{args.topic}.yaml')

    if args.mock:
        mock_path = ROOT / f'mock-{args.topic}.json'
        if not mock_path.exists():
            _log(f'Mock file mancante: {mock_path}')
            return 1
        result = json.loads(mock_path.read_text(encoding='utf-8'))
        _log(f'Mock caricato: {len(result.get("items", []))} items')
    else:
        from agent.summarize import summarize  # import lazy: evita import di anthropic in mock mode
        prompt_text = (ROOT / f'prompts/{args.topic}.txt').read_text(encoding='utf-8')
        state = _load_state()

        raw = _do_fetch(sources)
        _log(f'Totale articoli raccolti: {len(raw)}')

        before = len(raw)
        seen = set(state.get('seen_hashes', []))
        raw = [r for r in raw if _hash_url(r.get('url', '')) not in seen]
        _log(f'Anti-duplicato cross-run: {before} → {len(raw)}')

        raw.sort(key=lambda r: r.get('data') or '', reverse=True)
        raw = raw[:200]
        _log(f'Articoli inviati a Claude: {len(raw)}')

        result = summarize(prompt_text, raw, targets)
        _log(f'Items selezionati da Claude: {len(result.get("items", []))}')

        # Aggiorna stato seen
        state['seen_hashes'] = (state.get('seen_hashes', []) + [_hash_url(r['url']) for r in raw if r.get('url')])[-3000:]
        _save_state(state)

    now = datetime.now(timezone.utc) + timedelta(hours=2)  # CEST approssimato
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

    from agent.open_pr import open_pr  # import lazy
    branch = open_pr(output_file=str(output_path.relative_to(REPO_ROOT)) if output_path.is_absolute() else str(output_path))
    _log(f'PR flow: branch={branch}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
