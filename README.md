# Bot UBS — WhatsApp Business

> Bot informativo para pacientes da Unidade Básica de Saúde via WhatsApp Business.
> **ESF Sebastião Lima da Costa** — Capelinha do Barreiro / Distrito da Baixa — Uberaba/MG

---

## Sobre o projeto

Bot desenvolvido para facilitar o acesso da comunidade às informações do posto de saúde, sem precisar ligar ou ir pessoalmente. Os pacientes podem consultar horários, programas de saúde, equipe médica, vacinas, exames e muito mais diretamente pelo WhatsApp.

**Tecnologias:** Python · FastAPI · WhatsApp Cloud API (Meta) · SQLite · Docker

---

## Funcionalidades

### Informações gerais
- Quem atende hoje (com lógica automática para sextas alternadas)
- Endereços das duas unidades com link para o Google Maps
- Equipe completa com dias de atendimento por unidade
- Farmácia (dias de entrega, carro da prefeitura)
- Documentos necessários para cadastro
- FAQ com as 8 dúvidas mais frequentes
- Emergência (UPA, SAMU, hospitais para gestantes)

### Programas de saúde
- HiperDia, Pré-Natal, Puericultura, Vacinação
- Saúde da Mulher (cálculo automático de datas)
- Saúde Bucal, Mental, do Idoso e Fisioterapia
- Grupos terapêuticos (Gestantes, HiperDia, Tabagismo)

### Inteligência e métricas
- Pesquisa de satisfação com nota e comentário (salvo em SQLite)
- Avisos de campanha enviados pelo admin
- Métricas de uso: rotas mais acessadas, mensagens por dia

### Segurança
- Verificação HMAC dos webhooks da Meta
- Rate limiting (10 mensagens/min por número)
- Retry com backoff exponencial
- Validação do `config.json` com Pydantic

---

## Estrutura do projeto

```
bot_ubs/
├── main.py                  # FastAPI + webhook + roteamento
├── config.json              # Dados da UBS (editável sem alterar código)
├── admin.py                 # Painel admin no terminal
├── chat.py                  # Simulador de conversa no terminal
├── Dockerfile               # Deploy com Docker (Render/Railway)
├── Procfile                 # Deploy sem Docker
├── requirements.txt
├── runtime.txt
├── handlers/
│   ├── menu.py              # Menu principal e submenus
│   ├── info.py              # Quem atende hoje, unidades, equipe
│   ├── programas.py         # HiperDia, pré-natal, vacinação...
│   ├── exames.py            # Coleta de sangue e farmácia
│   ├── saude.py             # Bucal, mental, idoso, fisioterapia
│   ├── grupos.py            # Grupos da UBS
│   ├── emergencia.py        # UPA, SAMU, FAQ
│   ├── nivel3.py            # Pesquisa de satisfação
│   └── media.py             # Resposta para áudio/foto/sticker
├── services/
│   └── whatsapp.py          # Cliente WhatsApp API (pooling + retry)
├── utils/
│   ├── session.py           # Sessões por número de telefone
│   ├── security.py          # HMAC e rate limiting
│   ├── database.py          # SQLite (avaliações, métricas, avisos)
│   └── config_validator.py  # Validação do config.json
└── tests/
    └── test_bot.py          # 29 testes automatizados
```

---

## Configuração local

```bash
# Clone o repositório
git clone https://github.com/NoodleLDS/ubs-bot.git
cd ubs-bot

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env            # Edite com seus tokens

# Rode o servidor
uvicorn main:app --reload

# Simule uma conversa no terminal
python chat.py

# Acesse o painel admin
python admin.py

# Execute os testes
python -m pytest tests/ -v
```

---

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

| Variável | Descrição |
|---|---|
| `WHATSAPP_TOKEN` | Token da WhatsApp Cloud API (Meta) |
| `WHATSAPP_PHONE_ID` | ID do número de telefone (Meta) |
| `WEBHOOK_VERIFY_TOKEN` | Token de verificação do webhook (você define) |
| `WHATSAPP_APP_SECRET` | App Secret para validação HMAC |
| `ADMIN_TOKEN` | Senha dos endpoints `/admin/*` |
| `DB_PATH` | Caminho do banco SQLite (padrão: `./bot_ubs.db`) |

---

## Deploy no Render

1. Suba o projeto no GitHub
2. No [Render](https://render.com), crie um novo **Web Service** apontando para este repositório
3. Configure um **Disk** persistente montado em `/data`
4. Adicione as variáveis de ambiente + `DB_PATH=/data/bot_ubs.db`
5. O Render detecta o `Dockerfile` automaticamente
6. Após o deploy, registre a URL do Render como webhook na [Meta for Developers](https://developers.facebook.com)

---

## Endpoints admin

Com o servidor rodando, você pode gerenciar o bot via API:

```bash
# Criar aviso de campanha
curl -X POST https://sua-url.onrender.com/admin/aviso \
  -H "Content-Type: application/json" \
  -d '{"token": "SEU_ADMIN_TOKEN", "mensagem": "Vacinação contra gripe dia 25!"}'

# Remover aviso
curl -X POST https://sua-url.onrender.com/admin/aviso \
  -H "Content-Type: application/json" \
  -d '{"token": "SEU_ADMIN_TOKEN"}'

# Ver avaliações dos pacientes
curl "https://sua-url.onrender.com/admin/avaliacoes?token=SEU_ADMIN_TOKEN"

# Ver métricas de uso (últimos 30 dias)
curl "https://sua-url.onrender.com/admin/metricas?token=SEU_ADMIN_TOKEN&dias=30"

# Health check
curl "https://sua-url.onrender.com/health"
```

---

## Personalização

Toda a configuração da UBS (equipe, horários, endereços, programas) fica no arquivo `config.json`. Você pode editar esse arquivo sem precisar mexer no código.

---

Desenvolvido por **Lucas Daniel** — Enfermeiro ESF, Uberaba/MG
