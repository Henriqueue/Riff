# Termify 🎧
Um cliente de terminal (TUI) para controlar sua conta Spotify, com uma interface inspirada em players de música de linha de comando clássicos.

Este projeto nasceu de uma conversa sobre o [`meloid`](https://github.com/DexerMatters/meloid), um player de música em Haskell feito por um conhecido, para arquivos locais no Linux. O Riff pega essa mesma estética — painéis de álbuns, faixas, fila de reprodução, barras de progresso em modo texto — e aplica ao controle da sua conta do Spotify no Windows.

## O que é e para que serve

O Riff **não é** um player de áudio propriamente dito. Ele é um **controle remoto em modo texto** para o Spotify: uma interface de terminal bonita e rápida para ver o que está tocando, navegar por álbuns e playlists, gerenciar a fila e controlar a reprodução (play/pause/skip/volume/seek), sem precisar abrir a janela pesada do app oficial ou do navegador.

Quem de fato reproduz o áudio continua sendo o **app oficial da Spotify** (ou qualquer dispositivo Spotify Connect logado na sua conta) — o Riff só envia comandos pra ele através da API oficial. Isso significa que:

- ✅ Seu histórico de reprodução continua sendo registrado normalmente;
- ✅ Seus amigos continuam vendo sua atividade recente (Friend Activity);
- ✅ Os minutos escutados continuam contando para o seu Spotify Wrapped e para a "cápsula do tempo" de fim de ano;
- ✅ Tudo dentro dos Termos de Uso da Spotify — nenhuma engenharia reversa, nenhuma decodificação de áudio por fora do app oficial.

## Como funciona (visão geral)

```
┌──────────── ──┐        comandos (play/pause/next/seek/volume)      ┌────────────────────┐
│   Riff        │ ───────────────────────────────────────────────►   │  Spotify Web API   │
│  (TUI local) │                                                     │   (Player API)     │
└──────────────┘ ◄─────────────────────────────────────────────────  └────────┬───────────┘
                     estado atual (faixa, fila, progresso, volume)             │
                                                                                ▼
                                                                  ┌────────────────────────┐
                                                                  │ App oficial do Spotify │
                                                                  │  (ou dispositivo       │
                                                                  │   Spotify Connect)     │
                                                                  │  → decodifica e toca   │
                                                                  │    o áudio de fato     │
                                                                  └────────────────────────┘
```

1. O Riff autentica o usuário via OAuth 2.0 (Authorization Code + PKCE) contra a Spotify.
2. A cada ação do usuário (apertar espaço, seta, etc.), o Riff chama o endpoint correspondente da Web API (`/me/player/play`, `/me/player/next`, `/me/player/volume`, ...).
3. Em paralelo, o Riff consulta periodicamente o estado atual de reprodução (`/me/player/currently-playing`, `/me/player/queue`) e atualiza a tela.
4. Quem decodifica e reproduz o som é sempre um dispositivo já autenticado na conta (o app oficial aberto, minimizado, ou um alto-falante Connect) — nunca o próprio Riff.

## Tecnologias e por que foram escolhidas

| Tecnologia | Papel | Por quê |
|---|---|---|
| **Python 3** | Linguagem principal | Já é dominada pelo autor; ecossistema maduro para HTTP, OAuth e TUI |
| **[Textual](https://textual.textualize.io/)** | Framework de interface de terminal | Framework moderno de TUI, com widgets prontos (tabelas, listas, barras de progresso, painéis dockados) que mapeiam bem para a estética de múltiplos painéis buscada aqui; ativamente mantido |
| **[Spotipy](https://spotipy.readthedocs.io/)** | Cliente da Spotify Web API | Biblioteca de facto da comunidade Python para a Web API; já resolve o fluxo OAuth (incluindo PKCE) e expõe os endpoints do Player API de forma tipada e simples |
| **Spotify Web API (Player API)** | Backend real de reprodução | Único caminho **legal e oficial** para controlar playback programaticamente sem reimplementar decodificação de áudio (ver ADR-001) |

Detalhes de cada decisão e alternativas descartadas estão documentados em [`ADR.md`](./ADR.md).✌( ͡❛ ෴ ͡❛)✌

## Requisitos

- Windows 10/11
- Python 3.11+
- Conta **Spotify Premium** (obrigatória para os endpoints de controle de reprodução da Web API)
- App oficial do Spotify (desktop ou mobile) instalado e logado — é ele quem reproduz o áudio
- Um app registrado no [Spotify for Developers Dashboard](https://developer.spotify.com/dashboard) (gratuito, em Development Mode, uso pessoal)

## Instalação

```bash
git clone https://github.com/HenriqueUE/Riff.git
cd Riff
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Configure suas credenciais da Spotify (obtidas no Developer Dashboard) em um arquivo `.env`:

```
SPOTIFY_CLIENT_ID=seu_client_id
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

E rode:

```bash
python -m termify
```

Na primeira execução, o navegador vai abrir pedindo login/consentimento na Spotify. Depois disso, a sessão fica salva localmente e não é necessário logar de novo.

## Funcionalidades

- [ ] Autenticação OAuth 2.0 (Authorization Code + PKCE)
- [ ] Painel "tocando agora" (capa, faixa, artista, álbum, progresso)
- [ ] Fila de reprodução (visualizar e reordenar)
- [ ] Navegação por playlists e álbuns salvos
- [ ] Controles de reprodução (play/pause/next/previous/seek/volume)
- [ ] Atalhos de teclado estilo player de terminal (setas, espaço, `q` para sair, etc.)
- [ ] Histórico recente dentro do próprio TUI
- [ ] Troca de dispositivo ativo (transferir playback entre PC/celular/alto-falante)

## Projetos relacionados

- [**meloid**](https://github.com/DexerMatters/meloid) — player de música local em Haskell, inspiração visual direta deste projeto.
- [**spotify-tui**](https://github.com/Rigellute/spotify-tui) — cliente de terminal em Rust com a mesma abordagem de controle remoto via Web API.
- [**ncspot**](https://github.com/hrkfdn/ncspot) — cliente de terminal em Rust; citado apenas como referência de mercado (usa protocolo não-oficial para reproduzir áudio diretamente, fora do escopo deste projeto).

## Licença

MIT.

## Aviso

Este projeto usa a Spotify Web API sob os [Termos de Uso para Desenvolvedores da Spotify](https://developer.spotify.com/policy). Não é afiliado, endossado ou patrocinado pela Spotify AB.

## Extras

Designs descartados ou de inspiração. Talvez sejam utilizados para uma função de novos temas, mas quem sabe? Bleh ( ͡❛ ෴ ͡❛)
[alt text](image.png)
![alt text](image-1.png)