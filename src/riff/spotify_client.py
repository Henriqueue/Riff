"""Wrapper sobre o Spotipy com as operações que o Riff usa.

Mantém toda a superfície de contato com a Spotify Web API num só lugar,
para facilitar troca/mocks em testes futuros e manter o app.py focado
só na interface.
"""

from __future__ import annotations

from typing import Any

import spotipy

from .auth import get_auth_manager


class SpotifyClient:
    def __init__(self) -> None:
        self._sp = spotipy.Spotify(auth_manager=get_auth_manager())

    def current_playback(self) -> dict[str, Any] | None:
        """Estado atual de reprodução (faixa, progresso, volume, dispositivo)."""
        return self._sp.current_playback()

    def play(self) -> None:
        self._sp.start_playback()

    def pause(self) -> None:
        self._sp.pause_playback()

    def toggle_play_pause(self, is_playing: bool) -> None:
        if is_playing:
            self.pause()
        else:
            self.play()

    def next_track(self) -> None:
        self._sp.next_track()

    def previous_track(self) -> None:
        self._sp.previous_track()

    def set_volume(self, percent: int) -> None:
        percent = max(0, min(100, percent))
        self._sp.volume(percent)
