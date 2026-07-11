"""Render della pagina Banking via Jinja2."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

MM_IT_SHORT = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']
DAY_IT_SHORT = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']


def fmt_date_short(value) -> str:
    """Es. '02 feb 2026' da ISO string o datetime."""
    d = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return f"{d.day:02d} {MM_IT_SHORT[d.month - 1]} {d.year}"


def fmt_date_long(value) -> str:
    """Es. 'Mar 24 Mag 2026' da datetime."""
    d = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return f"{DAY_IT_SHORT[d.weekday()]} {d.day} {MM_IT_SHORT[d.month - 1].capitalize()} {d.year}"


_TEMPLATE_DIR = Path(__file__).parent / 'templates'


def render_page(items: List[Dict], targets: Dict, generated_at: datetime, next_update: datetime) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters['fmt_date_short'] = fmt_date_short
    env.filters['fmt_date_long'] = fmt_date_long

    clienti_list = targets.get('clienti', targets) if isinstance(targets, dict) else targets

    # Raggruppa news per cliente
    by_cliente: Dict[str, List[Dict]] = {}
    for it in items:
        by_cliente.setdefault(it['cliente_slug'], []).append(it)

    # Costruisci sezioni nell'ordine dei targets, solo per clienti con news
    sections: List[Dict] = []
    for c in clienti_list:
        news = by_cliente.get(c['slug'], [])
        if not news:
            continue
        news.sort(key=lambda x: x.get('data') or '', reverse=True)
        sections.append({**c, 'news': news})

    # Counters dinamici per i filtri
    counters = {
        'tipo': dict(Counter(it.get('tipo') for it in items if it.get('tipo'))),
        'fascia': dict(Counter(it.get('fascia') for it in items if it.get('fascia'))),
        'cliente': dict(Counter(it.get('cliente_slug') for it in items if it.get('cliente_slug'))),
        'emittente': dict(Counter(it.get('emittente_slug') for it in items if it.get('emittente_slug'))),
    }

    # Lista clienti raggruppata per fascia (per il filtro)
    by_fascia: Dict[str, List[Dict]] = {'top10': [], 'media': [], 'piccola': []}
    for c in clienti_list:
        by_fascia.setdefault(c['fascia'], []).append(c)

    # Flusso unico ordinato per data desc (nuovo layout)
    items_sorted = sorted(items, key=lambda x: x.get('data') or '', reverse=True)

    # Dict banche accessibile al JS del modal (per anagrafica al click)
    banche_dict = {c['slug']: c for c in clienti_list}

    template = env.get_template('page.html.j2')
    return template.render(
        generated_at=generated_at,
        next_update=next_update,
        sections=sections,
        items_sorted=items_sorted,
        banche_dict=banche_dict,
        all_targets=clienti_list,
        by_fascia=by_fascia,
        counters=counters,
        n_items=len(items),
        n_fonti=len({it.get('emittente_slug') for it in items if it.get('emittente_slug')}),
        n_banche_monitorate=len(clienti_list),
        n_clienti_con_news=len(sections),
    )
