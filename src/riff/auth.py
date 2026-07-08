"""Autenticação com a Spotify Web API.

Implementa o fluxo OAuth 2.0 Authorization Code + PKCE (ADR-003), recomendado
pela própria Spotify para aplicações nativas/desktop que não conseguem
guardar um client secret com segurança.

O token e o refresh token ficam salvos em um arquivo de cache local
(ADR-006) — simples e é o comportamento padrão do Spotipy. Esse arquivo
contém credenciais de sessão e por isso está no .gitignore.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyPKCE

load_dotenv()

# Escopos mínimos necessários para ler e controlar a reprodução (ADR-003).
SCOPES = " ".join(
    [
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing",
        "playlist-read-private",
        "user-read-recently-played",
    ]
)

CACHE_PATH = os.path.join(os.path.expanduser("~"), ".riff_cache")


def get_auth_manager() -> SpotifyPKCE:
    """Cria o gerenciador de autenticação PKCE a partir do .env."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID não definido. Copie .env.example para .env "
            "e preencha com o Client ID do seu app no Spotify Dashboard."
        )

    return SpotifyPKCE(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        cache_path=CACHE_PATH,
        open_browser=True,
    )
