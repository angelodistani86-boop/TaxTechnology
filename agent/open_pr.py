"""Apre una Pull Request con il nuovo banking-daily.html per la revisione manuale."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone

import httpx


def _run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print('> ' + ' '.join(cmd))
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def open_pr(output_file: str = 'banking-daily.html', base: str = 'main') -> str | None:
    """Crea branch auto/banking-YYYY-MM-DD, committa, push, apre PR via GitHub API.

    Ritorna il nome del branch creato, o None se non c'erano modifiche.
    Richiede env: GH_TOKEN (o GITHUB_TOKEN), GITHUB_REPOSITORY.
    """
    diff = _run(['git', 'diff', '--quiet', '--', output_file], check=False)
    untracked = _run(['git', 'ls-files', '--others', '--exclude-standard', '--', output_file],
                     check=False, capture=True)
    if diff.returncode == 0 and not untracked.stdout.strip():
        print(f'Nessuna modifica a {output_file}, niente da committare.')
        return None

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    branch = f'auto/banking-{today}'

    _run(['git', 'config', 'user.email', 'banking-agent@users.noreply.github.com'])
    _run(['git', 'config', 'user.name', 'Banking Update Agent'])

    # Reset to main first to make a clean branch
    _run(['git', 'checkout', '-B', branch])
    _run(['git', 'add', output_file])
    _run(['git', 'commit', '-m', f'Banking update {today}'])
    _run(['git', 'push', '-u', 'origin', branch, '--force'])

    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not token or not repo:
        print('GH_TOKEN o GITHUB_REPOSITORY mancante: PR non aperta automaticamente.', file=sys.stderr)
        return branch

    title = f'Banking update {today}'
    body = (
        f'Aggiornamento automatico della pagina Banking generato dall\'agente.\n\n'
        f'**Per pubblicare**: rivedi i diff in *Files changed*, eventualmente edita '
        f'`{output_file}` direttamente da qui (matita), poi **Merge pull request**.\n\n'
        f'**Per scartare**: chiudi la PR senza merge — l\'agente riproverà al prossimo run schedulato.'
    )

    # Try to find an existing open PR for this branch (idempotent)
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    existing = httpx.get(
        f'https://api.github.com/repos/{repo}/pulls',
        params={'head': f'{repo.split("/")[0]}:{branch}', 'state': 'open'},
        headers=headers,
        timeout=15,
    )
    if existing.status_code == 200 and existing.json():
        url = existing.json()[0].get('html_url')
        print(f'PR già esistente per {branch}: {url}')
        return branch

    r = httpx.post(
        f'https://api.github.com/repos/{repo}/pulls',
        headers=headers,
        json={'title': title, 'body': body, 'head': branch, 'base': base},
        timeout=15,
    )
    if r.status_code in (200, 201):
        print(f'PR aperta: {r.json().get("html_url")}')
    else:
        print(f'Errore apertura PR ({r.status_code}): {r.text}', file=sys.stderr)
    return branch
