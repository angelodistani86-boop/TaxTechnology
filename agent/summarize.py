"""Sintesi/classificazione via Claude Sonnet 4.6 con prompt caching."""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

_CLIENT = None


def _client() -> 'Anthropic':
    global _CLIENT
    if _CLIENT is None:
        if Anthropic is None:
            raise SystemExit('Modulo anthropic non installato. `pip install -r agent/requirements.txt`.')
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise SystemExit(
                'ANTHROPIC_API_KEY non impostata. Per test in locale usa --mock; '
                'in GitHub Actions configura il secret ANTHROPIC_API_KEY.'
            )
        _CLIENT = Anthropic(api_key=api_key)
    return _CLIENT


def summarize(prompt_text: str, raw_articles: List[Dict], targets: Dict) -> Dict:
    """Chiama Claude e ritorna il JSON parsato dello schema atteso dal prompt."""
    targets_compact = [
        {
            'slug': c['slug'],
            'nome': c['nome'],
            'fascia': c['fascia'],
            'query_alias': c.get('query_alias', []),
        }
        for c in targets.get('clienti', [])
    ]
    user_msg = (
        '[CLIENTI MONITORATI]\n'
        + json.dumps(targets_compact, ensure_ascii=False)
        + '\n\n[ARTICOLI GREZZI]\n'
        + json.dumps(raw_articles, ensure_ascii=False)
    )

    response = _client().messages.create(
        model='claude-sonnet-4-6',
        max_tokens=8000,
        system=[
            {
                'type': 'text',
                'text': prompt_text,
                'cache_control': {'type': 'ephemeral'},
            }
        ],
        messages=[{'role': 'user', 'content': user_msg}],
    )

    text = response.content[0].text.strip()
    # Strip eventuali code-fence se il modello li include nonostante l'istruzione
    if text.startswith('```'):
        first_nl = text.find('\n')
        text = text[first_nl + 1:] if first_nl > 0 else text
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f'JSON parse error: {e}', file=sys.stderr)
        print(f'Output ricevuto (primi 500 char):\n{text[:500]}', file=sys.stderr)
        raise
