"""Google News RSS query fetcher."""
from urllib.parse import quote

from .rss import fetch_rss


def fetch_gnews(query: str, label: str):
    url = f'https://news.google.com/rss/search?q={quote(query)}&hl=it&gl=IT&ceid=IT:it'
    return fetch_rss(url, f'gnews:{label}')
