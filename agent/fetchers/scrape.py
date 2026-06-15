"""Plain HTML fetcher + text extraction via trafilatura (per pagine corporate senza RSS)."""
import httpx
import trafilatura


def fetch_url(url: str, timeout: float = 10.0) -> str | None:
    try:
        r = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; TaxTechBot/1.0; +https://angelodistani.com)'},
        )
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def extract_text(html: str | None) -> str | None:
    if not html:
        return None
    return trafilatura.extract(html, include_comments=False, include_tables=False)
