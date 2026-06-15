"""RSS feed fetcher (RSS 2.0 e Atom via feedparser)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict

import feedparser


def fetch_rss(url: str, source_label: str) -> List[Dict]:
    feed = feedparser.parse(url)
    items: List[Dict] = []
    for entry in feed.entries:
        published = None
        for attr in ('published_parsed', 'updated_parsed'):
            t = getattr(entry, attr, None)
            if t:
                published = datetime(*t[:6], tzinfo=timezone.utc)
                break
        items.append({
            'titolo': (entry.get('title') or '').strip(),
            'url': (entry.get('link') or '').strip(),
            'snippet': (entry.get('summary') or '')[:600].strip(),
            'data': published.isoformat() if published else None,
            'source_label': source_label,
        })
    return items
