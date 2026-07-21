# Architecture Decision Records — Riff
Este documento registra as decisões arquiteturais tomadas durante o planejamento do projeto: um cliente de terminal (TUI) para controlar o Spotify, inspirado no player em Haskell [`meloid`](https://github.com/DexerMatters/meloid) de um conhecido.

---

## ADR-001: Controle remoto via Spotify Web API, em vez de reprodução própria de áudio

**Status:** Aceita

**Contexto**

O projeto original que inspirou esta ideia (`meloid`) é um player de música *local*: ele mesmo decodifica e reproduz arquivos de áudio, integrando-se ao MPD (Music Player Daemon) no Linux. A proposta aqui é diferente: reproduzir conteúdo do Spotify, um serviço de streaming com DRM, a partir de um app de terminal no Windows.

Existem, em tese, dois caminhos técnicos:

1. **Controle remoto**: o app de terminal envia comandos (play, pause, next, seek, volume, fila) via API oficial do Spotify para um dispositivo que já está autenticado e reproduzindo — o app oficial do Spotify (desktop/mobile) ou um dispositivo Spotify Connect. O áudio em si é decodificado e emitido pelo cliente oficial.
2. **Reprodução própria**: o app de terminal decodificaria e emitiria o áudio ele mesmo, sem depender do cliente oficial rodando.

O caminho 2 esbarra em limitações reais: o SDK oficial de reprodução da Spotify (Web Playback SDK) funciona apenas dentro de navegador (JavaScript), exige aprovação prévia da Spotify para uso comercial, e os termos de desenvolvedor proíbem explicitamente alterar o conteúdo da Spotify ou construir integrações de streaming não autorizadas. Implementações não-oficiais que contornam isso (como as usadas por alguns players do tipo `ncspot`) dependem de engenharia reversa do protocolo Spotify Connect, o que está fora do que este projeto quer fazer — o requisito explícito do autor é permanecer dentro da legalidade e dos Termos de Uso da Spotify.

**Decisão**

Adotar o **caminho 1**: o Riff é um cliente/controle remoto que fala com a **Spotify Web API (Player API)**. Ele não decodifica nem transmite áudio — apenas orquestra a reprodução em um dispositivo já autenticado (o app oficial do Spotify aberto no PC, celular, ou um alto-falante Connect).

**Consequências**

- ✅ 100% dentro dos Termos de Uso da Spotify.
- ✅ Histórico de reprodução, atividade de amigos e computação para o Spotify Wrapped continuam funcionando normalmente, porque é o cliente oficial quem de fato reproduz e reporta a escuta aos servidores da Spotify — o Riff não interfere nisso, apenas emite comandos.
- ✅ Sem necessidade de lidar com decodificação de áudio, buffers, ou dispositivos de saída de som.
- ⚠️ Requer que **algum** cliente oficial da Spotify esteja aberto e logado (pode ficar minimizado) para existir um "dispositivo ativo" a ser controlado.
- ⚠️ Requer conta **Spotify Premium** (exigência da própria Web API para os endpoints de reprodução).

---

## ADR-002: Stack tecnológica — Python + Textual + Spotipy

**Status:** Aceita

**Contexto**

O autor tem experiência prévia em Java, Python, TypeScript, Node e JavaScript, mas não em Haskell ou Rust — linguagens comuns em projetos similares (o `meloid` do conhecido, em Haskell; o `spotify-tui`, em Rust). É preciso escolher uma stack que:

- Aproveite conhecimento já existente do autor;
- Tenha bibliotecas maduras para TUI (interface de terminal) e para a Spotify Web API;
- Rode bem no Windows.

**Alternativas consideradas**

| Stack | Prós | Contras |
|---|---|---|
| **Python + Textual + Spotipy** | Framework de TUI moderno e muito ativo; `spotipy` é a lib de facto para Spotify em Python, já resolve OAuth/refresh; grande comunidade | — |
| Node/TypeScript + Ink + spotify-web-api-node | Componentes estilo React, familiar para mim quem venho do front-end | Ecossistema de TUI em Node é menos maduro que o de Python/Rust; Ink foi pensado mais para CLIs curtas do que para apps full-screen complexos |
| Java + Lanterna | Reaproveita experiência do autor em Java | Bibliotecas de TUI em Java (Lanterna) e de integração com Spotify são bem menos maduras/mantidas; comunidade pequena | 

**Decisão**

Usar **Python** como linguagem, **[Textual](https://textual.textualize.io/)** como framework de TUI e **[Spotipy](https://spotipy.readthedocs.io/)** como wrapper da Web API.

**Consequências**

- ✅ Curva de aprendizado baixa (o autor já sabe Python).
- ✅ Textual oferece widgets prontos (tabelas, listas, barras de progresso, painéis) que mapeiam bem para a estética de "múltiplos painéis" da referência visual.
- ✅ Spotipy já implementa o fluxo de autenticação e os principais endpoints do Player API, reduzindo boilerplate.
- ⚠️ Performance de uma TUI em Python é adequada para este caso de uso (não há processamento pesado de áudio, só chamadas de API e renderização de texto), então não é uma preocupação real aqui.

---

## ADR-003: Autenticação via OAuth 2.0 Authorization Code + PKCE

**Status:** Aceita

**Contexto**

A Spotify Web API exige OAuth 2.0 para autenticar o usuário e obter escopos de permissão (ler reprodução atual, controlar playback, ler playlists, etc.). Para aplicações desktop/nativas (que não conseguem guardar um *client secret* com segurança), a própria Spotify recomenda o fluxo **Authorization Code with PKCE**, em vez do fluxo implícito (deprecado) ou do fluxo padrão com client secret embutido no app.

**Decisão**

Implementar o fluxo **Authorization Code + PKCE**: o Riff abre o navegador padrão do usuário para a tela de login/consentimento da Spotify, recebe o `authorization code` via um servidor HTTP local temporário (`localhost:PORTA/callback`), troca o código por um `access_token` + `refresh_token`, e usa o `refresh_token` para renovar a sessão automaticamente sem pedir login toda vez.

**Escopos necessários (mínimo viável):**
- `user-read-playback-state` — ver o que está tocando, dispositivo ativo, fila.
- `user-modify-playback-state` — play/pause/next/previous/seek/volume/fila.
- `user-read-currently-playing` — faixa atual em detalhe.
- `playlist-read-private` — listar playlists do usuário para navegação.
- `user-read-recently-played` (opcional) — exibir histórico recente dentro do próprio TUI.

**Consequências**

- ✅ Seguro para um app nativo (nenhum segredo fica embutido no binário/código-fonte distribuído).
- ✅ Sessão persistente entre execuções, sem exigir novo login a cada abertura.
- ⚠️ Exige subir um pequeno servidor HTTP local (mesmo que efêmero) só para capturar o *redirect* do OAuth — implementação padrão e bem documentada pelo Spotipy.

---

## ADR-004: Registro de app no modo "Development Mode" da Spotify

**Status:** Aceita — reavaliar se o projeto crescer além do uso pessoal

**Contexto**

Em fevereiro de 2026, a Spotify anunciou mudanças no acesso de desenvolvedores à Web API, reduzindo o escopo do "Development Mode" e reforçando controles de segurança e uso — mas mantendo suporte explícito a aprendizado, experimentação e **projetos pessoais sem fins comerciais** de desenvolvedores individuais.

**Decisão**

Registrar o app no Spotify for Developers Dashboard em **Development Mode**, para uso estritamente pessoal (conta própria, sem distribuição pública nem comercialização). Não solicitar extensão de cota (*Extended Quota Mode*), já que isso é destinado a aplicações com base de usuários significativa ou fins comerciais — o que não é o caso aqui.

**Consequências**

- ✅ Acesso total aos endpoints necessários para uso pessoal, sem burocracia adicional.
- ⚠️ Se no futuro o projeto for compartilhado publicamente para outras pessoas usarem com suas próprias contas (não só o autor), será necessário revisitar os termos atuais no dashboard da Spotify antes de distribuir, pois as regras de acesso têm mudado com frequência.

---

## ADR-005: Acento de cor dinâmico extraído da capa do álbum

**Status:** Aceita

**Decisão**

Usar Pillow + quantização de cor pra extrair a cor dominante de cada capa, com verificação de contraste/saturação e paleta de fallback para capas monocromáticas ou de baixo contraste. A cor dinâmica é aplicada apenas em elementos de acento (bordas, badges, barra de progresso) — nunca no texto corrido, para preservar a legibilidade do estilo brutalista.

---

## ADR-006: Armazenamento do token

**Status:** Aceita — reavaliar se o projeto desejar opções mais seguras como keyring do Windows (Credential Manager)

**Decisão**

Cache local do Spotipy (arquivo em texto na pasta do projeto/usuário). Simples e é o padrão da própria biblioteca — (só vale lembrar de colocar esse arquivo no .gitignore, já que ele contém tokens de acesso, não posso esquecer hehe.)

---

## ADR-007: Gerenciamento de dependências

**Status:** Aceita 

**Decisão**

Poetry. Cuida de venv, lockfile (poetry.lock) e empacotamento num só lugar — bom também pra quando for hora de gerar um executável ou publicar.

---

## ADR-008: Estratégia de polling

**Status:** Aceita 

**Decisão**

 Adaptativo. Ideia geral: ao detectar troca de faixa ou pause/play, aumenta a frequência de consulta por alguns segundos pra pegar o estado "fresco" rápido; em repouso (mesma faixa tocando, nada mudou), relaxa o intervalo pra não estourar rate limit da API.

---

ADR-009: Repaginação visual — de neo-brutalismo para "terminal discreto"
Reverter a direção neo-brutalista (ADR original de identidade visual) após teste prático mostrar que bordas grossas e blocos de cor saturada cansavam na leitura contínua. Nova direção: paleta escura arroxeada de baixa saturação, hierarquia por peso tipográfico (não por cor/borda), líderes pontilhados no estilo terminal clássico, e pílulas de rótulo como único elemento de cor saturada na tela.
## Projetos relacionados (prior art)

---

- **[meloid](https://github.com/DexerMatters/meloid)** — player de música em Haskell, foco em arquivos locais via MPD, com renderização de capa de álbum em terminais compatíveis (Kitty, Ghostty, iTerm). Fonte de inspiração visual/estética direta deste projeto.
- **[spotify-tui](https://github.com/Rigellute/spotify-tui)** — cliente de terminal em Rust que controla o Spotify via Web API, mesmo modelo arquitetural adotado aqui (controle remoto, não reprodução própria).
- **[ncspot](https://github.com/hrkfdn/ncspot)** — cliente de terminal em Rust que efetivamente reproduz áudio via protocolo Connect não-oficial (`librespot`); mencionado aqui apenas como referência de mercado, **não** como abordagem adotada, por estar fora do escopo de legalidade definido neste projeto (ADR-001).
