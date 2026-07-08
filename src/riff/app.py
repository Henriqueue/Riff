"""Riff — cliente de terminal para controlar o Spotify.

Versão base (v0.1): autenticação + tela única "tocando agora" com
play/pause/next/previous e polling adaptativo (ADR-008).

O áudio em si é reproduzido pelo app oficial do Spotify (ou um dispositivo
Spotify Connect) já autenticado na conta — este app apenas envia comandos
e lê o estado via Web API (ver ADR-001).
"""

from __future__ import annotations

import time

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, ProgressBar, Static

from .spotify_client import SpotifyClient

# Polling adaptativo (ADR-008): rápido logo após uma mudança detectada,
# relaxado quando o estado está parado, para não estourar rate limit da API.
FAST_INTERVAL = 1.0
SLOW_INTERVAL = 3.0
FAST_BURST_SECONDS = 8.0


class RiffApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "riff"

    BINDINGS = [
        ("space", "toggle_play", "Play/Pause"),
        ("n", "next_track", "Próxima"),
        ("p", "previous_track", "Anterior"),
        ("q", "quit", "Sair"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.client = SpotifyClient()
        self._last_track_id: str | None = None
        self._last_is_playing: bool | None = None
        self._fast_until: float = 0.0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="now-playing"):
            yield Static("▶ TOCANDO AGORA", id="status-bar")
            yield Static("Carregando...", id="track-title")
            yield Static("", id="track-meta")
            yield ProgressBar(total=100, show_eta=False, id="progress")
        yield Footer()

    def on_mount(self) -> None:
        self._poll()

    @work(exclusive=True, thread=True)
    def _poll(self) -> None:
        """Consulta o estado atual (chamada de rede, roda em thread) e agenda
        a próxima consulta com o intervalo adaptativo."""
        try:
            state = self.client.current_playback()
            error: Exception | None = None
        except Exception as exc:  # noqa: BLE001 - queremos mostrar qualquer erro na tela
            state = None
            error = exc

        # Atualizações de UI a partir de uma worker thread precisam
        # passar por call_from_thread.
        self.call_from_thread(self._handle_poll_result, state, error)

    def _handle_poll_result(self, state: dict | None, error: Exception | None) -> None:
        if error is not None:
            self.query_one("#track-title", Static).update(f"Erro ao consultar Spotify: {error}")
            self.query_one("#track-meta", Static).update("")
            self.set_timer(SLOW_INTERVAL, self._poll)
            return

        self._render_state(state)

        changed = False
        if state and state.get("item"):
            track_id = state["item"].get("id")
            is_playing = state.get("is_playing")
            if track_id != self._last_track_id or is_playing != self._last_is_playing:
                changed = True
            self._last_track_id = track_id
            self._last_is_playing = is_playing

        if changed:
            self._fast_until = time.monotonic() + FAST_BURST_SECONDS

        next_interval = FAST_INTERVAL if time.monotonic() < self._fast_until else SLOW_INTERVAL
        self.set_timer(next_interval, self._poll)

    def _render_state(self, state: dict | None) -> None:
        title_widget = self.query_one("#track-title", Static)
        meta_widget = self.query_one("#track-meta", Static)
        progress = self.query_one("#progress", ProgressBar)

        if not state or not state.get("item"):
            title_widget.update("Nenhum dispositivo ativo.")
            meta_widget.update(
                "Abra o Spotify em algum dispositivo (PC, celular, alto-falante) e volte aqui."
            )
            progress.update(progress=0)
            return

        item = state["item"]
        artists = ", ".join(a["name"] for a in item.get("artists", []))
        album = item.get("album", {}).get("name", "")

        title_widget.update(item.get("name", "?"))
        meta_widget.update(f"{artists} — {album}")

        duration_ms = item.get("duration_ms") or 1
        position_ms = state.get("progress_ms") or 0
        percent = min(100, int(position_ms / duration_ms * 100))
        progress.update(progress=percent)

    # --- Ações de teclado -------------------------------------------------

# --- Ações de teclado -------------------------------------------------

    def _run_action(self, fn) -> None:
        """Executa uma ação de player protegendo contra erros da API
        (ex: 'Restriction violated'), sem derrubar o app."""
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            self.query_one("#track-meta", Static).update(f"⚠ comando recusado pela API: {exc}")
        self._fast_until = time.monotonic() + FAST_BURST_SECONDS

    def action_toggle_play(self) -> None:
        self._run_action(lambda: self.client.toggle_play_pause(bool(self._last_is_playing)))

    def action_next_track(self) -> None:
        self._run_action(self.client.next_track)

    def action_previous_track(self) -> None:
        self._run_action(self.client.previous_track)


def main() -> None:
    RiffApp().run()


if __name__ == "__main__":
    main()
